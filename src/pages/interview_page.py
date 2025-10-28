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

# Audio recording library
import sounddevice as sd
import soundfile as sf
import numpy as np

# Keep your relative imports as-is
from ..controller.application_controller import ApplicationController
from ..schemas.interview_questions_schema import QuestionItem, InterviewQuestionsSchema
from ..schemas.evaluation_schema import EvaluationScores
from configs.config import logger

# Import the new SpeechService
from src.utils.speech_service import SpeechService


# ----------------------------
# Streamlit-specific cache helper
# ----------------------------
@st.cache_resource
def get_speech_service(cache_dir="speech_models"):
    """Loads the SpeechService and caches it in Streamlit."""
    logger.info("Initializing SpeechService...")
    service = SpeechService(cache_dir=cache_dir, preload_voices=["af_bella"])
    logger.info("SpeechService initialized.")
    return service


# ----------------------------
# InterviewSession class (Refactored for Modularity & Threading)
# ----------------------------
class InterviewSession:
    """Manages interview flow using SpeechService for TTS/ASR and Streamlit for UI."""

    def __init__(self, application_controller: ApplicationController):
        self.controller = application_controller
        self.all_questions_asked: List[QuestionItem] = []
        self.all_evaluations: List[EvaluationScores] = []

        # --- State for Threaded Recording ---
        self.recording_thread = None
        self.is_recording = False
        self.recorded_audio_frames: List[np.ndarray] = []
        # --- End State ---

        # Load the speech service via the cached helper
        try:
            with st.spinner("🔄 Loading speech models..."):
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
        """Transcribe audio to text using Vosk if available, else return None."""
        if not self.speech_service:
            st.error("ASR model not loaded (Vosk).")
            return None

        try:
            audio_data = audio_data.flatten()

            # Basic silence removal
            threshold = 0.01
            non_silent = np.abs(audio_data) > threshold
            if np.any(non_silent):
                first_sound = np.argmax(non_silent)
                last_sound = len(audio_data) - np.argmax(non_silent[::-1])
                audio_data = audio_data[first_sound:last_sound]
            else:
                logger.warning("No audio detected above threshold.")
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
            logger.error(f"Transcription error (Vosk) wrapper: {e}", exc_info=True)
            st.error(f"Transcription error: {e}")
            return None

    # -----------------------------------
    # Auto-play question audio (from bytes)
    # -----------------------------------
    def auto_play_audio(self, audio_bytes: bytes):
        """Auto-play audio using HTML5 audio with autoplay."""
        try:
            import base64

            audio_base64 = base64.b64encode(audio_bytes).decode()

            # Auto-play audio element
            audio_html = f"""
                <audio autoplay style="display:none">
                    <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                </audio>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
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

        # 1. Prepare TTS audio (get from cache or generate)
        audio_bytes = self._prepare_question_audio(question)

        # 2. Render UI
        col_question, col_answer = st.columns([1, 1], gap="large")
        with col_question:
            self._render_question_ui(question, audio_bytes)

        with col_answer:
            # --- This is the core state machine ---

            if not st.session_state.get(f"submitted_{question.id}"):
                if not st.session_state.get(f"recorded_{question.id}"):
                    # State 1: Ready to record
                    self._render_answer_recorder(question)
                else:
                    # State 2: Ready to review
                    self._render_answer_review(question)
            else:
                # State 3: Submitted, handle evaluation
                return self._handle_evaluation(question, jd, session_id)

        # Default return if question is not yet complete
        return None, None, None

    # -----------------------------------
    # Question Flow: Helper Modules
    # -----------------------------------

    def _prepare_question_audio(self, question: QuestionItem) -> bytes | None:
        """Generates or retrieves cached TTS audio bytes."""
        audio_bytes_key = f"audio_bytes_{question.id}"

        if audio_bytes_key not in st.session_state:
            with st.spinner("⏳ Preparing question..."):
                audio_bytes = self.text_to_speech(question.question, voice="af_bella")
                if audio_bytes:
                    st.session_state[audio_bytes_key] = audio_bytes
                    st.session_state[f"audio_generated_{question.id}"] = True
                    st.session_state[f"audio_played_{question.id}"] = False
                else:
                    st.session_state[audio_bytes_key] = None  # Cache failure

        return st.session_state.get(audio_bytes_key)

    def _render_question_ui(self, question: QuestionItem, audio_bytes: bytes | None):
        """Renders the left column with the question and audio player."""

        # Auto-play audio once
        if audio_bytes and not st.session_state.get(f"audio_played_{question.id}"):
            self.auto_play_audio(audio_bytes)
            st.session_state[f"audio_played_{question.id}"] = True
            time.sleep(1)  # Brief pause

        # Header with question metadata
        st.markdown(
            f"**Question #{question.id}** | 📊 *{question.difficulty}* | 🎯 *{', '.join(question.target_concepts[:2])}...*"
        )
        st.markdown("---")

        with st.container(border=True):
            st.markdown("### Interview Question")

            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
            else:
                st.warning("⚠️ Audio not available")

            with st.expander("📝 View Question Text (if needed)"):
                st.markdown(question.question)
                st.caption(
                    f"**Target Concepts:** {', '.join(question.target_concepts)}"
                )

    def _render_answer_recorder(self, question: QuestionItem):
        """Renders the right column for recording (Start/Stop)."""
        with st.container(border=True):
            st.markdown("### 🎙️ Your Answer")

            is_recording_active = st.session_state.get(
                f"recording_active_{question.id}", False
            )

            if not is_recording_active:
                st.info("Click 'Start Recording' when ready to answer")
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
                    st.rerun()
            else:
                st.spinner("🎙️ Recording in progress...")

                if st.button(
                    "⏹️ Stop Recording",
                    key=f"stop_recording_{question.id}",
                    use_container_width=True,
                ):
                    # 1. Stop the thread
                    self.stop_recording()
                    if self.recording_thread:
                        self.recording_thread.join()  # Wait for thread to finish

                    # 2. Get frames
                    audio_frames = self.recorded_audio_frames

                    if audio_frames and len(audio_frames) > 0:
                        # 3. Process audio
                        audio_data = np.concatenate(audio_frames, axis=0)
                        st.session_state[f"audio_data_{question.id}"] = (
                            audio_data.flatten()
                        )
                        st.session_state[f"recorded_{question.id}"] = True
                        st.success("✅ Recording complete!")

                        # 4. Transcribe
                        with st.spinner("📝 Transcribing your answer..."):
                            answer_text = self.transcribe_audio(
                                st.session_state[f"audio_data_{question.id}"]
                            )

                        if answer_text is not None:
                            st.session_state[f"answer_{question.id}"] = answer_text
                        else:
                            st.error("❌ Transcription failed. Please try again.")
                            st.session_state[f"recorded_{question.id}"] = False

                    else:
                        st.error("❌ Recording failed or was empty. Please try again.")

                    st.session_state[f"recording_active_{question.id}"] = False
                    st.rerun()

    def _render_answer_review(self, question: QuestionItem):
        """Renders the right column for reviewing/submitting the answer."""
        with st.container(border=True):
            st.markdown("### 🎙️ Your Answer")
            st.success("✅ Answer recorded and transcribed")

            answer_text = st.session_state.get(f"answer_{question.id}", "")

            edited_answer = st.text_area(
                "Review and edit your answer if needed:",
                value=answer_text,
                height=200,
                key=f"edit_{question.id}",
            )

            st.markdown("---")
            col_submit1, col_submit2 = st.columns([1, 1])

            with col_submit1:
                if st.button(
                    "✅ Submit Answer",
                    key=f"submit_{question.id}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state[f"submitted_{question.id}"] = True
                    st.session_state[f"final_answer_{question.id}"] = edited_answer
                    st.rerun()

            with col_submit2:
                if st.button(
                    "🔄 Re-record",
                    key=f"rerecord_{question.id}",
                    use_container_width=True,
                ):
                    # Clear only this question's recording state
                    _clear_question_audio_state(question.id)
                    st.rerun()

    def _handle_evaluation(self, question: QuestionItem, jd: str, session_id: str):
        """Handles the evaluation phase and returns final data."""

        # Run evaluation only once
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
            st.rerun()

        # Display cached evaluation
        evaluation = st.session_state.get(f"evaluation_{question.id}")
        follow_up = st.session_state.get(f"followup_{question.id}")
        final_answer = st.session_state.get(f"final_answer_{question.id}", "")

        if evaluation:
            self.display_evaluation(evaluation)

        # This is the terminal state. Return the results.
        question.answer = final_answer
        return question, evaluation, follow_up

    # --------------------------
    # Display evaluation
    # --------------------------
    def display_evaluation(self, evaluation):
        """Display evaluation scores in a professional format"""
        st.markdown("---")
        st.markdown("### 📊 Evaluation Results")

        if not evaluation:
            st.error("Evaluation data not found.")
            return

        scores = getattr(evaluation, "scores", None)
        if scores is None:
            # Handle case where evaluation might be just the scores object
            scores = evaluation

        follow_up_status = getattr(evaluation, "follow_up_status", False)

        col1, col2, col3, col4, col5 = st.columns(5)

        def get_score(score_name):
            return getattr(scores, score_name, 0)

        with col1:
            st.metric("Relevance", f"{get_score('relevance')}/10")
        with col2:
            st.metric("Clarity", f"{get_score('clarity')}/10")
        with col3:
            st.metric("Depth", f"{get_score('depth')}/10")
        with col4:
            st.metric("Accuracy", f"{get_score('accuracy')}/10")
        with col5:
            st.metric("Completeness", f"{get_score('completeness')}/10")

        total_score = (
            get_score("relevance")
            + get_score("clarity")
            + get_score("depth")
            + get_score("accuracy")
            + get_score("completeness")
        )
        percentage = (total_score / 50) * 100

        st.progress(percentage / 100)
        st.markdown(f"**Overall Score: {percentage:.1f}%**")

        if follow_up_status:
            st.warning("🔄 A follow-up question will be asked to clarify your answer.")
        else:
            st.success("✅ Moving to next question...")

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

                scores = getattr(eval_item, "scores", eval_item)

                def get_score(s, name):
                    return getattr(s, name, 0)

                q_score = (
                    get_score(scores, "relevance")
                    + get_score(scores, "clarity")
                    + get_score(scores, "depth")
                    + get_score(scores, "accuracy")
                    + get_score(scores, "completeness")
                )
                total_score += q_score

                results["evaluations"].append(
                    {
                        "question_id": q.id,
                        "scores": scores.model_dump()
                        if hasattr(scores, "model_dump")
                        else scores.__dict__,
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


# ---------------- Utilities ----------------
def _clear_question_audio_state(question_id):
    """Clears session state related to a specific question's audio."""
    keys_to_delete = [
        f"audio_bytes_{question_id}",
        f"audio_generated_{question_id}",
        f"audio_played_{question_id}",
        f"recorded_{question_id}",
        f"audio_data_{question_id}",
        f"answer_{question_id}",
    ]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]


def _clear_question_flow_state(question_id):
    """Clears all session state for a given question ID."""
    keys_to_delete = []
    for key in st.session_state.keys():
        if str(question_id) in key:
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del st.session_state[key]


# ---------------- Main Render Function ----------------
def render():
    """Main render function for interview page"""

    if not st.session_state.get("interview_started"):
        st.warning(
            "⚠️ Interview has not been started. Please go back to the application page."
        )
        if st.button("🏠 Go Home"):
            st.session_state.current_page = "home"
            st.rerun()
        return

    # Initialize session state
    if "interview_session" not in st.session_state:
        st.session_state.interview_session = None
    if "interview_questions_prepared" not in st.session_state:
        st.session_state.interview_questions_prepared = False
    if "current_category_index" not in st.session_state:
        st.session_state.current_category_index = 0
    if "current_question_in_category" not in st.session_state:
        st.session_state.current_question_in_category = 0
    if "interview_completed" not in st.session_state:
        st.session_state.interview_completed = False

    st.title("🎯 AI-Powered Interview")
    st.markdown(
        "*Please answer each question clearly and professionally. Speak slowly and clearly to ensure accurate transcription.*"
    )

    controller = ApplicationController()
    active_jd = st.session_state.get("active_jd")
    active_jd_name = st.session_state.get("active_jd_name")
    final_application_info = st.session_state.get("final_application_info")

    if not active_jd or not final_application_info:
        st.error(
            "❌ Missing required information. Please complete the application first."
        )
        if st.button("🔙 Go Back"):
            st.session_state.interview_started = False
            st.session_state.current_page = "interview"
            st.rerun()
        return

    # Prepare interview questions (only once)
    if not st.session_state.interview_questions_prepared:
        with st.spinner("⏳ Preparing your interview..."):
            try:
                resume_json = final_application_info.model_dump_json()
                interview_questions = controller.prepeare_interview_questions(
                    resume_json=resume_json, jd_json=active_jd
                )

                st.session_state.interview_questions = interview_questions
                st.session_state.interview_questions_prepared = True
                st.session_state.interview_session = InterviewSession(controller)

                st.success(
                    "✅ Interview ready! First question will play automatically..."
                )
                time.sleep(2)
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error preparing interview questions: {e}")
                logger.error(f"Interview preparation error: {e}", exc_info=True)
                return

    # Check for completion
    if st.session_state.interview_completed:
        display_completion_page()
        return

    interview_questions = st.session_state.interview_questions
    interview_session = st.session_state.interview_session

    if not interview_session or not interview_session.speech_service:
        st.error(
            "❌ Interview session or SpeechService failed to initialize. Please reload."
        )
        if st.button("Reload"):
            st.rerun()
        return

    categories = [
        ("resume_questions", "📝 Resume-Based Questions"),
        ("jd_questions", "💼 Job Description Questions"),
        ("mixed_questions", "🔀 Mixed Questions"),
    ]

    current_cat_index = st.session_state.current_category_index

    if current_cat_index >= len(categories):
        st.session_state.interview_completed = True
        st.rerun()
        return

    category_key, category_name = categories[current_cat_index]
    question_list = getattr(interview_questions, category_key, [])

    # Display progress
    total_base_questions = sum(
        len(getattr(interview_questions, cat[0], [])) for cat in categories
    )
    # Note: total_questions_so_far is harder to track with follow-ups,
    # so we'll just track based on base questions.
    progress_val = (current_cat_index / len(categories)) + (
        st.session_state.current_question_in_category
        / (len(question_list) * len(categories))
        if len(question_list) > 0
        else 0
    )

    st.progress(min(progress_val, 1.0))
    st.caption(
        f"Section: {category_name} • Question {st.session_state.current_question_in_category + 1} of {len(question_list)}"
    )

    current_q_index = st.session_state.current_question_in_category

    if current_q_index >= len(question_list):
        # Move to next category
        st.session_state.current_category_index += 1
        st.session_state.current_question_in_category = 0
        st.success(f"✅ {category_name} completed! Moving to next section...")
        time.sleep(2)
        st.rerun()
        return

    # Get current question
    current_question = question_list[current_q_index]

    # Process the question
    result = interview_session.run_question_flow(
        question=current_question,
        jd=active_jd,
        session_id=f"interview_{active_jd_name}",
    )

    # Check if the question flow is complete
    if result[0] is not None:
        question_with_answer, evaluation, follow_up = result

        interview_session.all_questions_asked.append(question_with_answer)
        interview_session.all_evaluations.append(evaluation)

        if follow_up:
            st.info("🔄 Follow-up question based on your answer...")
            # Insert follow-up *after* the current question
            question_list.insert(current_q_index + 1, follow_up)
            setattr(interview_questions, category_key, question_list)
            st.session_state.interview_questions = interview_questions

        # Clean up state for the question we just finished
        _clear_question_flow_state(current_question.id)

        # Advance to the next question
        st.session_state.current_question_in_category += 1
        st.session_state.interview_session = interview_session  # Save session

        time.sleep(2)  # Pause to show evaluation
        st.rerun()


def display_completion_page():
    """Display interview completion summary"""
    st.success("🎉 Interview Completed!")
    st.balloons()

    interview_session = st.session_state.get("interview_session")
    if not interview_session:
        st.error("Session not found.")
        return

    total_score = 0
    max_score = 0
    for eval_item in interview_session.all_evaluations:
        if not eval_item:
            continue

        scores = getattr(eval_item, "scores", eval_item)
        if not scores:
            continue

        total_score += sum(
            val for val in scores.__dict__.values() if isinstance(val, (int, float))
        )
        max_score += 50  # 5 categories, 10 points each

    percentage = (total_score / max_score * 100) if max_score > 0 else 0

    st.markdown("## 📊 Interview Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", len(interview_session.all_questions_asked))
    with col2:
        st.metric("Total Score", f"{total_score}/{max_score}")
    with col3:
        st.metric("Percentage", f"{percentage:.1f}%")

    if percentage >= 80:
        st.success("🌟 Excellent Performance!")
    elif percentage >= 60:
        st.info("👍 Good Performance!")
    elif percentage >= 40:
        st.warning("⚠️ Average Performance")
    else:
        st.error("📉 Needs Improvement")

    if st.button("💾 Save Results", type="primary"):
        if not st.session_state.final_application_info:
            st.error("Final application info not found. Cannot save.")
            return

        candidate_info = {
            "name": st.session_state.final_application_info.personal_details.name,
            "email": st.session_state.final_application_info.personal_details.email,
            "phone": st.session_state.final_application_info.personal_details.phone,
            "job_applied": st.session_state.active_jd_name,
        }

        filepath = interview_session.save_interview_results(
            candidate_info=candidate_info,
            session_id=st.session_state.get("active_jd_name", "unknown"),
        )

        if filepath:
            st.success(f"✅ Results saved successfully to: {filepath}")
        else:
            st.error("❌ Failed to save results")

    st.markdown("---")
    if st.button("🏠 Return Home"):
        # Clean up all session state
        keys_to_clear = [
            "interview_session",
            "interview_questions_prepared",
            "current_category_index",
            "current_question_in_category",
            "interview_completed",
            "interview_questions",
            "active_jd",
            "active_jd_name",
            "final_application_info",
            "interview_started",
        ]

        for key in list(st.session_state.keys()):
            if (
                key in keys_to_clear
                or "audio_" in key
                or "answer_" in key
                or "recorded_" in key
            ):
                del st.session_state[key]

        st.session_state.current_page = "home"
        st.rerun()
