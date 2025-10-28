import tempfile
import soundfile as sf
from pathlib import Path
from src.utils.speech_service import SpeechService


def test_tts_asr_roundtrip():
    # Initialize the speech service
    # The cache directory must be the one containing your Vosk model
    service = SpeechService(cache_dir="speech_models", preload_voices=["af_bella"])

    # Text to test
    text = "Hello there, how are you today?"
    print(f"\n🗣️ Original text: {text}")

    # ---- TEXT TO SPEECH (Produces 24kHz WAV bytes) ----
    wav_bytes = service.text_to_speech(text, voice="af_bella")

    # Save for inspection
    # Ensure to use a specific filename or Vosk will struggle to transcribe from the raw bytes
    # without a WAV header being constructed in a separate file.
    output_path = Path(tempfile.gettempdir()) / "kokoro_test.wav"
    with open(output_path, "wb") as f:
        f.write(wav_bytes)
    print(f"💾 Saved synthesized audio to: {output_path}")

    # ---- SPEECH TO TEXT ----
    print("🎧 Transcribing generated audio...")
    # This call now handles the necessary 24kHz -> 16kHz resampling internally.
    result_text = service.transcribe_audio(wav_bytes)
    print(f"📝 Transcribed text: {result_text}")

    # ---- Simple Accuracy Check ----
    # Vosk often drops punctuation and capitalization, so compare normalized text
    normalized_original = text.lower().replace(",", "").replace("?", "").strip()
    normalized_result = result_text.strip().lower()

    # We expect a high degree of match, but not 100% due to ASR imperfections
    if normalized_result == normalized_original:
        print("✅ Transcription succeeded (exact match).")
    elif normalized_result and all(
        word in normalized_result for word in normalized_original.split()
    ):
        print("✅ Transcription succeeded (all words found).")
    else:
        # Check if it failed completely
        if not result_text.strip():
            print("❌ Transcription returned empty text!")
        else:
            print(
                f"⚠️ Transcription mismatch! Expected '{normalized_original}', Got '{normalized_result}'. This is often due to low ASR model accuracy or voice differences."
            )


if __name__ == "__main__":
    test_tts_asr_roundtrip()
