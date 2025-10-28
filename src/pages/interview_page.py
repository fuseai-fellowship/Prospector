import streamlit as st
import time
from pathlib import Path
import json
from datetime import datetime
from typing import List, Tuple
import tempfile
import os
import io
import shutil
import logging

# Audio recording library
import sounddevice as sd
import numpy as np  # Still needed for audio data

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
    # This info message will only show when the cache is empty
    st.info("🔄 Loading speech models (will auto-download if missing)...")
    service = SpeechService(cache_dir=cache_dir)
    logger.info("SpeechService initialized.")
    return service


# ----------------------------
# InterviewSession class (now uses SpeechService)
# ----------------------------
class InterviewSession:
    """Manages interview flow using SpeechService for TTS/ASR and Streamlit for UI."""

    def __init__(self, application_controller: ApplicationController):
        self.controller = application_controller
        self.all_questions_asked: List[QuestionItem] = []
        self.all_evaluations: List[EvaluationScores] = []

        # Load the speech service via the cached helper
        try:
            self.speech_service = get_speech_service(cache_dir="speech_models")

            # Display status messages based on service availability
            if self.speech_service.tts_available:
                st.success("✅ Kokoro ONNX loaded (TTS).")
            else:
                st.warning("⚠️ Kokoro ONNX not available. TTS disabled.")

            if self.speech_service.asr_available:
                st.success("✅ Whisper ONNX + processor loaded (ASR).")
            else:
                st.warning("⚠️ Whisper ONNX or processor not available. ASR disabled.")

            if not self.speech_service.librosa_available:
                st.warning(
                    "⚠️ librosa not available. Audio resampling for ASR may fail."
                )

            time.sleep(1)
        except Exception as e:
            logger.error(f"Error loading voice models: {e}", exc_info=True)
            st.error(f"Error loading voice models: {e}")
            self.speech_service = None  # Ensure it's None on failure

    # -----------------------------------
    # TTS: Wrapper around SpeechService
    # -----------------------------------
    def text_to_speech(self, text: str) -> str:
        """Return path to generated WAV file, or None on error."""
        if not self.speech_service or not self.speech_service.tts_available:
            st.error("TTS model not loaded (Kokoro ONNX).")
            return None

        try:
            path = self.speech_service.text_to_speech(text)
            if path is None:
                st.error("TTS error: Failed to generate audio.")
            return path
        except Exception as e:
            logger.error(f"Kokoro ONNX TTS error wrapper: {e}", exc_info=True)
            st.error(f"TTS error: {e}")
            return None

    # -----------------------------------
    # Recording (Stays here as it's UI-dependent)
    # -----------------------------------
    def record_audio(self, sample_rate: int = 16000) -> np.ndarray:
        """Record audio from microphone (returns numpy array)."""
        try:
            duration = 120  # max duration in seconds

            st.info("🎤 Recording... Speak now!")

            # Start non-blocking recording
            audio_data = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
            )

            stop_placeholder = st.empty()
            # If the user clicks stop, stop the recording and return what we have
            if stop_placeholder.button(
                "⏹️ Stop Recording", key=f"stop_recording_{time.time()}"
            ):
                sd.stop()
                stop_placeholder.empty()
                return audio_data.flatten() if audio_data is not None else None

            # Wait for recording to finish (or user interrupt)
            sd.wait()
            stop_placeholder.empty()  # Clear button after recording finishes naturally

            return audio_data.flatten() if audio_data is not None else None

        except Exception as e:
            logger.error(f"Audio recording error: {e}", exc_info=True)
            st.error(f"Recording error: {e}")
            return None

    # -----------------------------------
    # ASR: Wrapper around SpeechService
    # -----------------------------------
    def transcribe_audio(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio to text using Whisper ONNX session if available, else return None."""
        if not self.speech_service or not self.speech_service.asr_available:
            st.error("ASR model not loaded (Whisper ONNX or processor missing).")
            return None

        try:
            text = self.speech_service.transcribe_audio(audio_data, sample_rate)
            if text is None:
                st.error("Transcription error: Failed to transcribe audio.")
            return text
        except Exception as e:
            logger.error(
                f"Transcription error (Whisper ONNX) wrapper: {e}", exc_info=True
            )
            st.error(f"Transcription error: {e}")
            return None

    # -----------------------------------
    # process_question (Updated to check service availability)
    # -----------------------------------
    def process_question(
        self, question: QuestionItem, jd: str, session_id: str
    ) -> Tuple[QuestionItem, any, QuestionItem]:
        """
        Process a single question: generate audio, play, record answer, transcribe, evaluate
        Returns: (question_with_answer, evaluation, follow_up_question_or_False)
        """

        # Check models
        if not self.speech_service:
            st.error("❌ SpeechService failed to initialize. Cannot proceed.")
            return None, None, None

        if not self.speech_service.tts_available:
            st.error("❌ TTS model (Kokoro ONNX) not loaded. Check logs.")
            # We can still proceed without TTS, but ASR is crucial
            # return None, None, None

        if not self.speech_service.asr_available:
            st.warning("⚠️ Whisper ONNX or processor not loaded. ASR may fail.")
            # We can't proceed without ASR
            st.error("❌ ASR model (Whisper ONNX) not loaded. Cannot proceed.")
            return None, None, None

        # Generate audio for question first (before displaying)
        question_audio_path = None
        if self.speech_service.tts_available:  # Only try if TTS is on
            if not st.session_state.get(f"audio_generated_{question.id}"):
                with st.spinner("Preparing your interview..."):
                    question_audio_path = self.text_to_speech(question.question)
                    if question_audio_path:
                        st.session_state[f"audio_path_{question.id}"] = (
                            question_audio_path
                        )
                        st.session_state[f"audio_generated_{question.id}"] = True
            else:
                question_audio_path = st.session_state.get(f"audio_path_{question.id}")

        # Display question
        st.markdown(f"### Question")
        st.markdown(f"**Difficulty:** {question.difficulty}")
        st.markdown(f"**Target Concepts:** {', '.join(question.target_concepts)}")
        st.markdown("---")
        st.markdown(f"**{question.question}**")

        # Play audio
        if question_audio_path:
            try:
                st.audio(question_audio_path)
            except Exception as e:
                logger.warning(f"Could not play audio via st.audio: {e}")

        # Recording phase
        if not st.session_state.get(f"recorded_{question.id}"):
            st.info("🎤 Click the button below to start recording your answer")

            if st.button(
                "🎤 Start Recording", key=f"record_{question.id}", type="primary"
            ):
                # Record audio
                audio_data = self.record_audio()

                if audio_data is not None and len(audio_data) > 0:
                    st.session_state[f"recorded_{question.id}"] = True
                    st.success("✅ Recording complete!")

                    # Transcribe
                    with st.spinner("📝 Transcribing your answer..."):
                        answer_text = self.transcribe_audio(audio_data)

                        if answer_text:
                            st.session_state[f"answer_{question.id}"] = answer_text
                            st.success("✅ Transcription complete!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Transcription failed. Please try again.")
                            st.session_state[f"recorded_{question.id}"] = False
                else:
                    st.error("❌ Recording failed. Please try again.")

            return None, None, None

        # Display answer and allow editing
        answer_text = st.session_state.get(f"answer_{question.id}")

        if answer_text and not st.session_state.get(f"submitted_{question.id}"):
            st.markdown("#### Your Answer:")

            edited_answer = st.text_area(
                "Review and edit if needed:",
                value=answer_text,
                height=150,
                key=f"edit_{question.id}",
            )

            if st.button(
                "✅ Submit Answer", key=f"submit_{question.id}", type="primary"
            ):
                st.session_state[f"submitted_{question.id}"] = True
                st.session_state[f"final_answer_{question.id}"] = edited_answer
                st.rerun()

            return None, None, None

        # Evaluation phase
        if st.session_state.get(
            f"submitted_{question.id}"
        ) and not st.session_state.get(f"evaluated_{question.id}"):
            final_answer = st.session_state[f"final_answer_{question.id}"]

            # Update question with answer
            question.answer = final_answer

            # Evaluate answer
            with st.spinner("🤔 Evaluating your answer..."):
                evaluation, follow_up = self.controller.evaluate_answer(
                    user_answer=question, jd=jd, session_id=session_id
                )

            # Display evaluation
            self.display_evaluation(evaluation)

            st.session_state[f"evaluated_{question.id}"] = True
            st.session_state[f"evaluation_{question.id}"] = evaluation
            st.session_state[f"followup_{question.id}"] = follow_up

            time.sleep(2)
            st.rerun()

        # Return results if evaluation is complete
        if st.session_state.get(f"evaluated_{question.id}"):
            final_answer = st.session_state[f"final_answer_{question.id}"]
            question.answer = final_answer
            evaluation = st.session_state[f"evaluation_{question.id}"]
            follow_up = st.session_state[f"followup_{question.id}"]

            # Clean up audio file
            audio_path = st.session_state.get(f"audio_path_{question.id}")
            if audio_path:
                try:
                    os.unlink(audio_path)
                except Exception:
                    pass

            return question, evaluation, follow_up

        return None, None, None

    # --------------------------
    # Display evaluation (unchanged)
    # --------------------------
    def display_evaluation(self, evaluation):
        """Display evaluation scores in a nice format"""
        st.markdown("#### 📊 Evaluation Results")

        # Handle AnswerEvaluation object (has .scores attribute)
        if hasattr(evaluation, "scores"):
            scores = evaluation.scores
            follow_up_status = evaluation.follow_up_status
        else:
            # If it's already EvaluationScores
            scores = evaluation
            follow_up_status = False

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Relevance", f"{scores.relevance}/10")
        with col2:
            st.metric("Clarity", f"{scores.clarity}/10")
        with col3:
            st.metric("Depth", f"{scores.depth}/10")
        with col4:
            st.metric("Accuracy", f"{scores.accuracy}/10")
        with col5:
            st.metric("Completeness", f"{scores.completeness}/10")

        total_score = (
            scores.relevance
            + scores.clarity
            + scores.depth
            + scores.accuracy
            + scores.completeness
        )
        percentage = (total_score / 50) * 100

        st.progress(percentage / 100)
        st.markdown(f"**Overall Score: {percentage:.1f}%**")

        if follow_up_status:
            st.warning("🔄 A follow-up question will be asked to clarify your answer.")
        else:
            st.success("✅ Answer evaluated successfully!")

    # --------------------------
    # Save interview results (unchanged)
    # --------------------------
    def save_interview_results(self, candidate_info: dict, session_id: str):
        """Save complete interview results to file"""
        try:
            # Prepare results
            results = {
                "candidate_info": candidate_info,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(self.all_questions_asked),
                "questions_and_answers": [
                    {
                        "id": q.id,
                        "question": q.question,
                        "answer": q.answer,
                        "difficulty": q.difficulty,
                        "target_concepts": q.target_concepts,
                    }
                    for q in self.all_questions_asked
                ],
                "evaluations": [
                    {
                        "question_id": eval_item.question_id
                        if hasattr(eval_item, "question_id")
                        else q.id,
                        "scores": {
                            "relevance": eval_item.scores.relevance
                            if hasattr(eval_item, "scores")
                            else eval_item.relevance,
                            "clarity": eval_item.scores.clarity
                            if hasattr(eval_item, "scores")
                            else eval_item.clarity,
                            "depth": eval_item.scores.depth
                            if hasattr(eval_item, "scores")
                            else eval_item.depth,
                            "accuracy": eval_item.scores.accuracy
                            if hasattr(eval_item, "scores")
                            else eval_item.accuracy,
                            "completeness": eval_item.scores.completeness
                            if hasattr(eval_item, "scores")
                            else eval_item.completeness,
                        },
                        "overall_assessment": eval_item.overall_assessment
                        if hasattr(eval_item, "overall_assessment")
                        else "",
                        "follow_up_status": eval_item.follow_up_status
                        if hasattr(eval_item, "follow_up_status")
                        else False,
                    }
                    for eval_item, q in zip(
                        self.all_evaluations, self.all_questions_asked
                    )
                ],
                "total_score": sum(
                    sum(
                        (
                            eval_item.scores
                            if hasattr(eval_item, "scores")
                            else eval_item
                        ).__dict__.values()
                    )
                    for eval_item in self.all_evaluations
                ),
                "max_possible_score": len(self.all_evaluations) * 50,
            }

            # Calculate final percentage
            if results["max_possible_score"] > 0:
                results["final_percentage"] = (
                    results["total_score"] / results["max_possible_score"]
                ) * 100
            else:
                results["final_percentage"] = 0

            # Save to file
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


# ---------------- Render / page-level helpers (unchanged) ----------------
def render():
    """Main render function for interview page"""

    # Check if interview should start
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

    # Page header
    st.title("🎯 AI Interview Session")
    st.markdown("---")

    # Initialize controller
    controller = ApplicationController()

    # Check for required data
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
        with st.spinner("Preparing your interview ..."):
            try:
                # Convert resume to JSON string
                resume_json = final_application_info.model_dump_json()

                # Generate questions
                interview_questions = controller.prepeare_interview_questions(
                    resume_json=resume_json, jd_json=active_jd
                )

                st.session_state.interview_questions = interview_questions
                st.session_state.interview_questions_prepared = True

                # This is where the InterviewSession (and SpeechService) gets initialized
                st.session_state.interview_session = InterviewSession(controller)

                st.success("✅ Interview questions prepared!")
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error preparing interview questions: {e}")
                logger.error(f"Interview preparation error: {e}", exc_info=True)
                return

    # Check if interview is completed
    if st.session_state.interview_completed:
        display_completion_page()
        return

    # Get interview data
    interview_questions = st.session_state.interview_questions
    interview_session = st.session_state.interview_session

    if not interview_session:
        st.error("❌ Interview session failed to initialize. Please reload.")
        return

    # Define question categories
    categories = [
        ("resume_questions", "📝 Resume-Based Questions"),
        ("jd_questions", "💼 Job Description Questions"),
        ("mixed_questions", "🔀 Mixed Questions"),
    ]

    current_cat_index = st.session_state.current_category_index

    if current_cat_index >= len(categories):
        # All categories completed
        st.session_state.interview_completed = True
        st.rerun()
        return

    category_key, category_name = categories[current_cat_index]
    question_list = getattr(interview_questions, category_key, [])  # Added default

    # Display simple progress
    total_questions_so_far = (
        sum(
            len(getattr(interview_questions, cat[0], []))
            for cat in categories[:current_cat_index]
        )
        + st.session_state.current_question_in_category
    )

    total_base_questions = sum(
        len(getattr(interview_questions, cat[0], [])) for cat in categories
    )

    if total_base_questions > 0:
        progress = min(1.0, total_questions_so_far / total_base_questions)
        st.progress(progress)

    current_q_index = st.session_state.current_question_in_category

    if current_q_index >= len(question_list):
        # Move to next category
        st.session_state.current_category_index += 1
        st.session_state.current_question_in_category = 0
        # Clear all question-specific session state for new category
        for key in list(st.session_state.keys()):
            if any(
                x in key
                for x in [
                    "audio_generated_",
                    "audio_path_",
                    "recorded_",
                    "answer_",
                    "submitted_",
                    "evaluated_",
                ]
            ):
                del st.session_state[key]
        st.success(f"✅ Moving to next section...")
        time.sleep(1)
        st.rerun()
        return

    # Get current question
    current_question = question_list[current_q_index]

    st.markdown("---")

    # Process the question
    result = interview_session.process_question(
        question=current_question,
        jd=active_jd,
        session_id=f"interview_{active_jd_name}",
    )

    if result[0] is not None:  # Question was answered and evaluated
        question_with_answer, evaluation, follow_up = result

        # Add to lists
        interview_session.all_questions_asked.append(question_with_answer)
        interview_session.all_evaluations.append(evaluation)

        # Check for follow-up
        if follow_up:
            st.info("🔄 Follow-up question needed based on your answer...")
            time.sleep(2)
            # Add follow-up to the end of current category's question list
            question_list.append(follow_up)
            # Update the interview_questions object with modified list
            setattr(interview_questions, category_key, question_list)
            st.session_state.interview_questions = interview_questions

        # Clear session state for current question
        for key in list(st.session_state.keys()):
            if str(current_question.id) in key:
                del st.session_state[key]

        # Move to next question
        st.session_state.current_question_in_category += 1

        # Update session state
        st.session_state.interview_session = interview_session

        time.sleep(2)
        st.rerun()


def display_completion_page():
    """Display interview completion summary"""
    st.success("🎉 Interview Completed!")
    st.balloons()

    interview_session = st.session_state.interview_session
    if not interview_session:
        st.error("Session not found.")
        return

    # Calculate final score
    total_score = 0
    for eval_item in interview_session.all_evaluations:
        if hasattr(eval_item, "scores"):
            # AnswerEvaluation object
            scores = eval_item.scores
        else:
            # EvaluationScores object
            scores = eval_item

        if scores:  # Ensure scores object is not None
            total_score += sum(scores.__dict__.values())

    max_score = len(interview_session.all_evaluations) * 50
    percentage = (total_score / max_score * 100) if max_score > 0 else 0

    # Display summary
    st.markdown("## 📊 Interview Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Questions", len(interview_session.all_questions_asked))
    with col2:
        st.metric("Total Score", f"{total_score}/{max_score}")
    with col3:
        st.metric("Percentage", f"{percentage:.1f}%")

    # Performance indicator
    if percentage >= 80:
        st.success("🌟 Excellent Performance!")
    elif percentage >= 60:
        st.info("👍 Good Performance!")
    elif percentage >= 40:
        st.warning("⚠️ Average Performance")
    else:
        st.error("📉 Needs Improvement")

    # Save results
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

    # Navigation
    st.markdown("---")
    if st.button("🏠 Return Home"):
        # Clear interview state
        for key in list(st.session_state.keys()):
            if (
                key.startswith("interview_")
                or key.startswith("answer_")
                or key.startswith("audio_")
                or key == "current_page"
                or key == "active_jd"
                or key == "active_jd_name"
                or key == "final_application_info"
            ):
                if key != "current_page":
                    del st.session_state[key]

        st.session_state.current_page = "home"
        st.session_state.interview_started = False
        st.rerun()
