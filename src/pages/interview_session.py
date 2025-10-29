import streamlit as st
import time
from pathlib import Path
import json
from datetime import datetime
from typing import List, Tuple
import io
import os
import logging
import threading
import base64

# Audio recording library
import sounddevice as sd
import soundfile as sf
import numpy as np

# Import the autorefresh component
from streamlit_autorefresh import st_autorefresh

# Keep your relative imports as-is
from ..controller.application_controller import ApplicationController
from ..schemas.interview_questions_schema import QuestionItem, InterviewQuestionsSchema
from ..schemas.evaluation_schema import EvaluationScores

# Use the new import path
from configs.config import logger

# Import the new SpeechService
# Adjusted path to be relative like the others
from ..utils.speech_service import SpeechService


# ----------------------------
# Streamlit-specific cache helper
# ----------------------------
@st.cache_resource
def get_speech_service(cache_dir="speech_models"):
    """Loads the SpeechService and caches it in Streamlit."""
    logger.info("Initializing SpeechService...")
    # Using a known good voice for consistency
    service = SpeechService(cache_dir=cache_dir, preload_voices=["af_bella"])
    logger.info("SpeechService initialized.")
    return service


# ---------------- Utilities ----------------
def _clear_question_audio_state(question_id):
    """Clears session state related to a specific question's audio."""
    keys_to_delete = [
        f"audio_bytes_{question_id}",
        f"audio_generated_{question_id}",
        f"audio_played_{question_id}",
        f"audio_data_{question_id}",
        f"answer_{question_id}",
        f"answer_timer_start_{question_id}",
        f"user_is_recording_{question_id}",
        f"audio_initially_played_{question_id}",  # Clear the new flag
        f"recording_active_{question_id}",
        f"record_start_time_{question_id}",
    ]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]


# ----------------------------
# InterviewSession class (Refactored for Modularity & Threading)
# ----------------------------
class InterviewSession:
    """Manages interview flow using SpeechService for TTS/ASR and Streamlit for UI."""

    def __init__(self, application_controller: ApplicationController):
        self.controller = application_controller
        self.all_questions_asked: List[QuestionItem] = []
        self.all_evaluations: List[EvaluationScores] = []

        # --- Timer Constants REMOVED ---
        # self.RECORD_DURATION = 120
        # self.EDIT_DURATION = 30

        # --- State for Threaded Recording ---
        self.recording_thread = None
        self.is_recording = False
        self.recorded_audio_frames: List[np.ndarray] = []
        # --- End State ---

        # Load the speech service via the cached helper
        try:
            with st.spinner("Loading speech models..."):
                self.speech_service = get_speech_service(cache_dir="speech_models")
            logger.info("SpeechService initialized.")
        except Exception as e:
            logger.error(f"Error loading voice models: {e}", exc_info=True)
            st.error(f"Error loading voice models: {e}")
            self.speech_service = None

    # -----------------------------------
    # TTS: Returns bytes, not a file
    # -----------------------------------
    def text_to_speech(self, text: str, voice: str = "af_bella") -> bytes | None:
        """Return path to generated WAV file, or None on error."""
        if not self.speech_service:
            st.error("TTS model not loaded (Kokoro).")
            return None

        try:
            wav_bytes = self.speech_service.text_to_speech(text, voice=voice)

            if wav_bytes is None:
                st.error("TTS error: Failed to generate audio.")
                return None

            return wav_bytes  # Return bytes directly

        except Exception as e:
            logger.error(f"Kokoro TTS error wrapper: {e}", exc_info=True)
            st.error(f"TTS error: {e}")
            return None

    # -----------------------------------
    # Recording (Thread-safe implementation)
    # -----------------------------------
    def record_audio(self, sample_rate: int = 16000):
        """
        Record audio from microphone.
        This function is intended to be run in a separate thread.
        It appends audio frames to self.recorded_audio_frames.
        """
        try:
            self.is_recording = True
            self.recorded_audio_frames = []  # Clear frames at the start

            def callback(indata, frames, time, status):
                if self.is_recording:
                    self.recorded_audio_frames.append(indata.copy())

            # Use sd.InputStream to capture audio
            with sd.InputStream(channels=1, samplerate=sample_rate, callback=callback):
                while self.is_recording:
                    sd.sleep(100)  # Wait while recording

            logger.info("Recording thread finished.")

        except Exception as e:
            # Cannot use st.error from a non-main thread. Use logger.
            logger.error(f"Recording thread error: {e}", exc_info=True)

    def stop_recording(self):
        """Stop the current recording by setting the flag."""
        try:
            self.is_recording = False
            logger.info("Recording stop signal sent.")
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")

    # -----------------------------------
    # ASR: Wrapper around SpeechService
    # -----------------------------------
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio to text using ASR if available, else return None."""
        if not self.speech_service:
            st.error("ASR model not loaded.")
            return None

        try:
            audio_data = audio_data.flatten()

            # Basic silence removal - with lower threshold
            threshold = 0.005  # Lowered threshold
            logger.debug(f"Original audio length: {len(audio_data)} samples")
            non_silent = np.abs(audio_data) > threshold
            if np.any(non_silent):
                first_sound = np.argmax(non_silent)
                last_sound = len(audio_data) - np.argmax(non_silent[::-1])
                trimmed_audio_data = audio_data[first_sound:last_sound]
                logger.debug(
                    f"Trimmed audio length: {len(trimmed_audio_data)} samples (Removed {len(audio_data) - len(trimmed_audio_data)} samples)"
                )
                if len(trimmed_audio_data) == 0:
                    logger.warning(
                        "Audio trimmed to zero length after silence removal."
                    )
                    return ""  # Return empty if trimming removed everything
                audio_data = trimmed_audio_data  # Use the trimmed data
            else:
                logger.warning(
                    "No audio detected above threshold. Returning empty string."
                )
                return ""  # Return empty string if all silent

            # Write to in-memory buffer
            buffer = io.BytesIO()
            sf.write(buffer, audio_data, sample_rate, format="WAV", subtype="PCM_16")
            wav_bytes = buffer.getvalue()

            text = self.speech_service.transcribe_audio(wav_bytes)

            if text is None or text == "Transcription Error":
                st.error("Transcription error: Failed to transcribe audio.")
                return None

            return text

        except Exception as e:
            logger.error(f"Transcription error wrapper: {e}", exc_info=True)
            st.error(f"Transcription error: {e}")
            return None

    # -----------------------------------
    # Auto-play question audio (from bytes)
    # -----------------------------------
    def auto_play_audio(self, audio_bytes: bytes):
        """Auto-play audio using HTML5 audio with autoplay."""
        try:
            audio_base64 = base64.b64encode(audio_bytes).decode()
            audio_html = f"""
                <audio autoplay style="display:none">
                    <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
            logger.info("Audio autoplay element injected.")
        except Exception as e:
            logger.error(f"Error auto-playing audio: {e}")

    # -----------------------------------
    # Question Flow: Main Controller
    # -----------------------------------
    def run_question_flow(
        self, question: QuestionItem, jd: str, session_id: str
    ) -> Tuple[QuestionItem, any, QuestionItem] | Tuple[None, None, None]:
        """
        Manages the state machine for a single question.
        Returns: (question_with_answer, evaluation, follow_up_question) on completion.
        """
        audio_initially_played_key = f"audio_initially_played_{question.id}"  # Flag key

        # 1. Prepare TTS audio
        audio_bytes = self._prepare_question_audio(question)

        # 2. Render UI Columns
        col_question, col_answer = st.columns([1, 1], gap="large")
        with col_question:
            self._render_question_ui(question, audio_bytes)

        with col_answer:
            # --- This is the core state machine ---
            if not st.session_state.get(f"submitted_{question.id}"):
                # State 1: Ready to record
                # This state's button now moves directly to "submitted"
                self._render_answer_recorder(question)
            else:
                # State 3: Submitted, handle evaluation
                return self._handle_evaluation(question, jd, session_id)

        # 3. Auto-play audio *after* UI columns are rendered
        if audio_bytes and not st.session_state.get(f"audio_played_{question.id}"):
            # Check if we haven't already tried playing and set the flag
            if not st.session_state.get(audio_initially_played_key, False):
                self.auto_play_audio(audio_bytes)
                st.session_state[f"audio_played_{question.id}"] = True
                time.sleep(2)  # Keep the 2-second pause for audio to start
                # Set the flag indicating initial playback attempt is done
                st.session_state[audio_initially_played_key] = True
                logger.info(
                    f"Audio playback initiated for Q {question.id}, setting flag."
                )
                # **REMOVED st.rerun() HERE** - Let the next natural/autorefresh rerun occur

        # Default return if question is not yet complete
        return None, None, None

    def _prepare_question_audio(self, question: QuestionItem) -> bytes | None:
        """Generates or retrieves cached TTS audio bytes."""
        audio_bytes_key = f"audio_bytes_{question.id}"

        if audio_bytes_key not in st.session_state:
            with st.spinner("Preparing question..."):
                audio_bytes = self.text_to_speech(question.question, voice="af_bella")
                if audio_bytes:
                    st.session_state[audio_bytes_key] = audio_bytes
                    st.session_state[f"audio_generated_{question.id}"] = True
                    st.session_state[f"audio_played_{question.id}"] = False
                    # Initialize the new flag
                    st.session_state[f"audio_initially_played_{question.id}"] = False
                else:
                    st.session_state[audio_bytes_key] = None  # Cache failure

        return st.session_state.get(audio_bytes_key)

    def _render_question_ui(self, question: QuestionItem, audio_bytes: bytes | None):
        """Renders the left column with the question and audio player."""
        # --- REMOVED AUTOPLAY LOGIC FROM HERE ---

        # Header with question metadata
        st.markdown(
            f"**Question Id : #{question.id}** | *{question.difficulty}* | *{', '.join(question.target_concepts[:2])}...*"
        )
        st.markdown("---")

        with st.container(border=True):
            st.markdown("### Interview Question")

            # Display the audio player, but don't autoplay here
            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
            else:
                st.warning("Audio not available")

            with st.expander("View Question Text (if needed)"):
                st.markdown(question.question)
                st.caption(
                    f"**Target Concepts:** {', '.join(question.target_concepts)}"
                )

    def _stop_and_process_recording(self, question: QuestionItem) -> str:
        """
        Helper to stop recording, process, transcribe audio,
        and return the transcribed text.
        """
        logger.info(f"Stopping recording for question {question.id}")
        # 1. Stop the thread
        self.stop_recording()
        if self.recording_thread:
            self.recording_thread.join()  # Wait for thread to finish

        # 2. Get frames
        audio_frames = self.recorded_audio_frames

        if audio_frames and len(audio_frames) > 0:
            # 3. Process audio
            audio_data = np.concatenate(audio_frames, axis=0)
            st.session_state[f"audio_data_{question.id}"] = audio_data.flatten()
            # st.session_state[f"recorded_{question.id}"] = True # No longer needed

            # 4. Transcribe
            # This spinner is nested inside the button's spinner
            with st.spinner("Transcribing your answer..."):
                answer_text = self.transcribe_audio(audio_data)

            if answer_text is not None:
                st.success("Answer recorded and transcribed.")
                return answer_text
            else:
                st.error("Transcription failed. Submitting empty answer.")
                return ""
        else:
            # Handle case where user stopped without recording, or time ran out
            st.warning("No audio was recorded. Submitting empty answer.")
            return ""

    def _render_answer_recorder(self, question: QuestionItem):
        """Renders the right column for recording (Start/Stop) with no timer."""
        with st.container(border=True):
            st.markdown("### Your Answer")

            is_recording_active = st.session_state.get(
                f"recording_active_{question.id}", False
            )

            if not is_recording_active:
                st.info("Click 'Start Recording' when ready.")
                if st.button(
                    "Start Recording",
                    key=f"record_{question.id}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state[f"recording_active_{question.id}"] = True
                    # Start the recording thread
                    self.recording_thread = threading.Thread(target=self.record_audio)
                    self.recording_thread.start()
                    # Rerun to show the "Stop" button
                    st.rerun()

            else:
                # --- RECORDING IS ACTIVE ---
                st.info("🔴 Recording... Click below to stop.")

                if st.button(
                    "Stop Recording",
                    key=f"stop_recording_{question.id}",
                    use_container_width=True,
                ):
                    # New flow: Process, transcribe, and submit immediately
                    with st.spinner("Processing and submitting answer..."):
                        # 1. Stop, process, and transcribe
                        answer_text = self._stop_and_process_recording(question)

                        # 2. Immediately submit the result
                        self._submit_answer(question, answer_text)

                    # 3. Rerun. This will trigger _handle_evaluation
                    st.rerun()

    # --- REMOVED _render_answer_review FUNCTION ---

    def _submit_answer(self, question: QuestionItem, final_answer_text: str):
        """Helper to submit the final answer."""
        logger.info(f"Submitting answer for question {question.id}")
        st.session_state[f"submitted_{question.id}"] = True
        st.session_state[f"final_answer_{question.id}"] = final_answer_text
        if f"review_start_time_{question.id}" in st.session_state:
            del st.session_state[f"review_start_time_{question.id}"]

    def _handle_evaluation(self, question: QuestionItem, jd: str, session_id: str):
        """Handles the evaluation phase and returns final data."""

        if not st.session_state.get(f"evaluated_{question.id}"):
            final_answer = st.session_state.get(f"final_answer_{question.id}", "")
            question.answer = final_answer

            with st.spinner("Evaluating your answer..."):
                evaluation, follow_up = self.controller.evaluate_answer(
                    user_answer=question, jd=jd, session_id=session_id
                )
            st.session_state[f"evaluated_{question.id}"] = True
            st.session_state[f"evaluation_{question.id}"] = evaluation
            st.session_state[f"followup_{question.id}"] = follow_up

            # We add a small sleep to ensure the "Evaluating..." spinner
            # is visible for a moment, giving feedback that something happened.
            time.sleep(1)
            st.rerun()

        evaluation = st.session_state.get(f"evaluation_{question.id}")
        follow_up = st.session_state.get(f"followup_{question.id}")
        final_answer = st.session_state.get(f"final_answer_{question.id}", "")

        # --- REMOVED display_evaluation call ---
        # if evaluation:
        #     self.display_evaluation(evaluation)

        question.answer = final_answer
        return question, evaluation, follow_up

    # --------------------------
    # Display evaluation (REMOVED)
    # --------------------------
    # def display_evaluation(self, evaluation):
    #     ...

    # --------------------------
    # Save interview results
    # --------------------------
    def save_interview_results(self, candidate_info: dict, session_id: str):
        """Save complete interview results to file"""
        try:
            results = {
                "candidate_info": candidate_info,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(self.all_questions_asked),
                "questions_and_answers": [
                    q.model_dump() for q in self.all_questions_asked
                ],
                "evaluations": [],
                "total_score": 0,
            }

            total_score = 0
            for eval_item, q in zip(self.all_evaluations, self.all_questions_asked):
                if not eval_item:
                    continue

                # Handle cases where eval_item might be the scores dict directly
                if hasattr(eval_item, "scores"):
                    scores = eval_item.scores
                elif isinstance(eval_item, dict) and "scores" in eval_item:
                    scores = eval_item["scores"]
                else:
                    scores = eval_item  # Assume eval_item *is* the scores object/dict

                # Handle scores being a dict or an object
                def get_score(s, name):
                    if isinstance(s, dict):
                        return s.get(name, 0)
                    return getattr(s, name, 0)

                q_score = (
                    get_score(scores, "relevance")
                    + get_score(scores, "clarity")
                    + get_score(scores, "depth")
                    + get_score(scores, "accuracy")
                    + get_score(scores, "completeness")
                )
                total_score += q_score

                # Prepare scores dict for JSON serialization
                scores_dict = {}
                if hasattr(scores, "model_dump"):
                    scores_dict = scores.model_dump()
                elif isinstance(scores, dict):
                    scores_dict = scores
                elif hasattr(scores, "__dict__"):
                    scores_dict = scores.__dict__

                results["evaluations"].append(
                    {
                        "question_id": q.id,
                        "scores": scores_dict,
                        "overall_assessment": getattr(
                            eval_item, "overall_assessment", ""
                        ),
                        "follow_up_status": getattr(
                            eval_item, "follow_up_status", False
                        ),
                        "question_total_score": q_score,
                    }
                )

            results["total_score"] = total_score
            results["max_possible_score"] = len(self.all_evaluations) * 50
            results["final_percentage"] = (
                (total_score / results["max_possible_score"]) * 100
                if results["max_possible_score"] > 0
                else 0
            )

            interview_dir = Path("data/interviews")
            interview_dir.mkdir(parents=True, exist_ok=True)
            filename = f"interview_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = interview_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            logger.info(f"Interview results saved to: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error saving interview results: {e}", exc_info=True)
            return None
