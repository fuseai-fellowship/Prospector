import os
import io
import time
import numpy as np
import soundfile as sf
from dotenv import load_dotenv
from groq import Groq  # <-- Import Groq
from kokoro import KPipeline
from scipy.signal import resample_poly  # Needed for 24kHz -> 16kHz resampling

from configs.config import logger

load_dotenv()

# --- Constants ---
# Groq/Whisper model expects 16kHz audio
WHISPER_SAMPLE_RATE = 16000
# Kokoro TTS model generates 24kHz audio
KOKORO_SAMPLE_RATE = 24000


class SpeechService:
    """
    A service combining Kokoro TTS and Groq ASR.
    Handles model initialization and critical sample rate mismatch.
    """

    def __init__(self, cache_dir: str = "speech_models", preload_voices: list = None):
        logger.info(
            f"Initializing SpeechService with Groq ASR. TTS models cached in '{cache_dir}'"
        )

        # 1. Setup Groq ASR (16kHz)
        logger.info("Initializing Groq client...")
        try:
            self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            # You can also pass api_key=os.environ.get("GROQ_API_KEY")

            # Test connection (optional but recommended)
            # self.groq_client.models.list()
            logger.info("Groq client initialized.")
        except Exception as e:
            logger.critical(f"Failed to initialize Groq client: {e}")
            raise

        self.asr_model = "whisper-large-v3"
        self.asr_target_rate = WHISPER_SAMPLE_RATE

        # 2. Setup Kokoro TTS (24kHz)
        self.tts_pipeline = KPipeline(
            lang_code="a"
        )  # 'a' is the default English lang_code for Kokoro

        if preload_voices:
            # (Your pre-warming logic here)
            pass

    def text_to_speech(self, text: str, voice: str) -> bytes:
        """Converts text to WAV audio bytes using Kokoro (24kHz)."""
        logger.info(f"Generating speech for '{text[:20]}...' with voice '{voice}'")
        start_time = time.time()

        # Kokoro returns a generator of audio chunks, we combine them.
        audio_chunks = [chunk[-1] for chunk in self.tts_pipeline(text, voice=voice)]
        audio_data = np.concatenate(audio_chunks)

        # Convert numpy array output (PCM-16) to WAV format bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, KOKORO_SAMPLE_RATE, format="WAV", subtype="PCM_16")

        end_time = time.time()
        logger.info(f"TTS finished in {end_time - start_time:.2f}s")
        return buffer.getvalue()

    def transcribe_audio(self, wav_bytes: bytes) -> str:
        """
        Transcribes WAV audio bytes using Groq.
        CRITICAL: Automatically handles resampling from any rate to 16kHz (Whisper's requirement).
        """
        # Load audio data from bytes
        buffer = io.BytesIO(wav_bytes)
        try:
            data, sample_rate = sf.read(buffer, dtype="int16")
        except Exception as e:
            logger.error(f"Failed to read audio bytes with soundfile: {e}")
            return "Audio Read Error"

        # --- THIS RESAMPLING LOGIC IS PERFECT, KEEP IT ---
        if sample_rate != self.asr_target_rate:
            logger.warning(
                f"Sample rate mismatch: Input={sample_rate}Hz, ASR_Target={self.asr_target_rate}Hz. Resampling..."
            )

            # Calculate resampling factors (e.g., 24kHz -> 16kHz is 2/3)
            # This handles any input rate, not just 24kHz
            try:
                # Using 2 and 3 is specific to 24k -> 16k.
                # A more general approach is needed if sample_rate is not 24k
                # For this specific use case (Kokoro 24k), 2 and 3 is correct.
                if sample_rate == KOKORO_SAMPLE_RATE:
                    up = 2
                    down = 3
                else:
                    # General case (though less efficient than GCD)
                    up = self.asr_target_rate
                    down = sample_rate

                resampled_data = resample_poly(data, up, down, axis=0).astype("int16")

                final_audio_data = resampled_data
                final_sample_rate = self.asr_target_rate
            except Exception as e:
                logger.error(f"Failed to resample audio: {e}")
                return "Audio Resample Error"
        else:
            # No resampling needed
            final_audio_data = data
            final_sample_rate = sample_rate
        # --- END OF RESAMPLING LOGIC ---

        # --- NEW GROQ API CALL ---

        # 1. Groq needs a file, not raw bytes. Re-package the 16kHz
        #    numpy array back into WAV-formatted bytes.
        try:
            resampled_buffer = io.BytesIO()
            sf.write(
                resampled_buffer,
                final_audio_data,
                final_sample_rate,  # This will be 16000
                format="WAV",
                subtype="PCM_16",
            )
            resampled_buffer.seek(0)  # Rewind the buffer to the beginning
        except Exception as e:
            logger.error(f"Failed to write resampled audio to buffer: {e}")
            return "Audio Write Error"

        # 2. Send the 16kHz WAV bytes to Groq
        try:
            start_time = time.time()
            logger.info("Sending audio to Groq for transcription...")

            transcription = self.groq_client.audio.transcriptions.create(
                file=("input.wav", resampled_buffer.read()),
                model=self.asr_model,
                response_format="json",  # "json" for simple text, "verbose_json" for timestamps
            )

            end_time = time.time()
            logger.info(f"Groq transcription finished in {end_time - start_time:.2f}s")

            return transcription.text.strip()

        except Exception as e:
            logger.critical(f"Groq API transcription failed: {e}")
            return "Transcription Error"
