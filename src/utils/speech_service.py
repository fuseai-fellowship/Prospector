import os
import io
import time
import numpy as np
import soundfile as sf
from vosk import Model, KaldiRecognizer
from kokoro import KPipeline
from scipy.signal import resample_poly  # Needed for 24kHz -> 16kHz resampling

# --- Constants ---
# Vosk small model expects 16kHz audio
VOSK_SAMPLE_RATE = 16000
# Kokoro TTS model generates 24kHz audio
KOKORO_SAMPLE_RATE = 24000


class SpeechService:
    """
    A service combining Kokoro TTS and Vosk ASR.
    Handles model initialization and critical sample rate mismatch.
    """

    def __init__(self, cache_dir: str = "speech_models", preload_voices: list = None):
        print(
            f"INFO: Initializing SpeechService. Models will be cached in '{cache_dir}'"
        )

        # 1. Setup Vosk ASR (16kHz)
        vosk_model_path = os.path.join(cache_dir, "vosk-model-small-en-us-0.15")
        if not os.path.exists(vosk_model_path):
            print(f"INFO: Vosk model not found. Downloading the small English model.")
            # NOTE: In a real-world app, you would download and extract the model here
            # For this example, we assume `uv` or a pre-run script handles model presence.
            pass

        print(f"INFO: Loading Vosk model from {vosk_model_path} ...")
        self.vosk_model = Model(vosk_model_path)
        print("INFO: Vosk model loaded.")

        # 2. Setup Kokoro TTS (24kHz)
        self.tts_pipeline = KPipeline(
            lang_code="a"
        )  # 'a' is the default English lang_code for Kokoro

        if preload_voices:
            # Pre-warm the voice cache (optional, but good practice)
            # This ensures required resources for the voices are loaded.
            # In a full Kokoro setup, this might involve loading reference embeddings.
            pass

    def text_to_speech(self, text: str, voice: str) -> bytes:
        """Converts text to WAV audio bytes using Kokoro (24kHz)."""
        print(f"INFO: Generating speech for '{text[:20]}...' with voice '{voice}'")
        start_time = time.time()

        # Kokoro returns a generator of audio chunks, we combine them.
        audio_chunks = [
            audio_chunk for _, _, _, audio_chunk in self.tts_pipeline(text, voice=voice)
        ]
        audio_data = np.concatenate(audio_chunks)

        # Convert numpy array output (PCM-16) to WAV format bytes
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, KOKORO_SAMPLE_RATE, format="WAV", subtype="PCM_16")

        end_time = time.time()
        print(f"INFO: TTS finished in {end_time - start_time:.2f}s")
        return buffer.getvalue()

    def transcribe_audio(self, wav_bytes: bytes) -> str:
        """
        Transcribes WAV audio bytes using Vosk.
        CRITICAL: Automatically handles resampling from 24kHz (Kokoro) to 16kHz (Vosk).
        """
        # Load audio data from bytes
        buffer = io.BytesIO(wav_bytes)
        # sf.read detects the actual sample rate and format
        data, sample_rate = sf.read(buffer, dtype="int16")

        if sample_rate != VOSK_SAMPLE_RATE:
            print(
                f"WARNING: Sample rate mismatch: TTS={sample_rate}Hz, ASR={VOSK_SAMPLE_RATE}Hz. Resampling..."
            )

            # Resample audio using polyphase filter (highest quality)
            # Up: VOSK_SAMPLE_RATE (16000), Down: sample_rate (24000)
            # We need to find the Greatest Common Divisor (GCD) for the up/down arguments: GCD(16000, 24000) = 8000
            # Up = 16000 / 8000 = 2
            # Down = 24000 / 8000 = 3
            resampled_data = resample_poly(data, 2, 3, axis=0).astype("int16")

            # Use the resampled data and the VOSK target rate
            final_audio_data = resampled_data
            final_sample_rate = VOSK_SAMPLE_RATE
        else:
            final_audio_data = data
            final_sample_rate = sample_rate

        # Initialize Vosk recognizer with the correct, expected sample rate (16000)
        rec = KaldiRecognizer(self.vosk_model, final_sample_rate)

        # Vosk expects raw PCM 16-bit data, not the WAV container
        rec.AcceptWaveform(final_audio_data.tobytes())

        # Extract the final result and parse the text
        result_json = rec.FinalResult()

        try:
            import json

            result = json.loads(result_json)
            return result.get("text", "").strip()
        except Exception as e:
            print(f"ERROR: Could not parse Vosk result: {e}")
            return "Transcription Error"
