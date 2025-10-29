import streamlit as st
import time
import json
from datetime import datetime
from configs.config import logger
from ..controller.application_controller import ApplicationController
from .interview_session import InterviewSession


def _clear_question_flow_state(question_id):
    """Clears all session state for a given question ID."""
    keys_to_delete = []
    for key in st.session_state.keys():
        if str(question_id) in key:
            keys_to_delete.append(key)
        # Also clean up refresh keys if they exist
        if (
            key == f"record_refresher_{question_id}"
            or key == f"review_refresher_{question_id}"
        ):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        if key in st.session_state:  # Check existence before deleting
            del st.session_state[key]


# ---------------- Main Render Function ----------------
def render():
    """Main render function for interview page"""

    if not st.session_state.get("interview_started"):
        st.warning(
            "Interview has not been started. Please go back to the application page."
        )
        if st.button("Go Home"):
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
    if "interview_results_saved" not in st.session_state:
        st.session_state.interview_results_saved = False

    st.title("AI-Powered Interview")
    st.markdown("*Please answer each question clearly and professionally.*")

    controller = ApplicationController()
    active_jd = st.session_state.get("active_jd")
    active_jd_name = st.session_state.get("active_jd_name")
    final_application_info = st.session_state.get("final_application_info")

    if not active_jd or not final_application_info:
        st.error("Missing required information. Please complete the application first.")
        if st.button("Go Back"):
            st.session_state.interview_started = False
            st.session_state.current_page = "interview"
            st.rerun()
        return

    # Prepare interview questions (only once)
    if not st.session_state.interview_questions_prepared:
        with st.spinner("Preparing your interview..."):
            try:
                resume_json = final_application_info.model_dump_json()
                interview_questions = controller.prepeare_interview_questions(
                    resume_json=resume_json, jd_json=active_jd
                )

                st.session_state.interview_questions = interview_questions
                st.session_state.interview_questions_prepared = True
                st.session_state.interview_session = InterviewSession(controller)

                st.success("Interview ready! First question will play automatically...")
                time.sleep(2)
                st.rerun()

            except Exception as e:
                st.error(f"Error preparing interview questions: {e}")
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
            "Interview session or SpeechService failed to initialize. Please reload."
        )
        if st.button("Reload"):
            # Clear state to force re-initialization
            if "interview_session" in st.session_state:
                del st.session_state.interview_session
            st.rerun()
        return

    categories = [
        ("resume_questions", "Resume-Based Questions"),
        ("jd_questions", "Job Description Questions"),
        ("mixed_questions", "Mixed Questions"),
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
        st.success(f"{category_name} completed! Moving to next section...")
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
            st.info("Follow-up question based on your answer...")
            question_list.insert(current_q_index + 1, follow_up)
            setattr(interview_questions, category_key, question_list)
            st.session_state.interview_questions = interview_questions

        # Clean up state for the question we just finished
        _clear_question_flow_state(current_question.id)

        # Advance to the next question
        st.session_state.current_question_in_category += 1
        st.session_state.interview_session = interview_session  # Save session

        # The 1s sleep in _handle_evaluation provides a brief pause.
        st.rerun()


def display_completion_page():
    """Display interview completion summary"""
    st.success("Interview Completed!")
    st.markdown(
        """
        Thank you for completing the interview.

        - **Great work:** We appreciate the time and effort you've put into your responses.
        - **Next Steps:** Our team will now review your interview.
        - **Contact:** We will be in touch soon with your results and information on the next steps.

        You may now return home.
        """
    )

    # --- Auto-save results on page load ---
    if not st.session_state.get("interview_results_saved", False):
        try:
            # 1. Get all required data from session_state
            interview_session = st.session_state.get("interview_session")
            final_application_info = st.session_state.get("final_application_info")
            active_jd_name = st.session_state.get("active_jd_name")
            controller = ApplicationController()

            if not all([interview_session, final_application_info, active_jd_name]):
                st.error("Session data missing, cannot save results automatically.")
                return

            # 2. Get params for controller method
            applicant_number = final_application_info.personal_details.phone
            active_jd = active_jd_name

            if not applicant_number:
                st.error("Candidate phone number not found, cannot save results.")
                return

            # 3. Build the results JSON
            candidate_info = {
                "name": final_application_info.personal_details.name,
                "email": final_application_info.personal_details.email,
                "phone": applicant_number,
                "job_applied": active_jd,
            }

            results = {
                "candidate_info": candidate_info,
                "session_id": f"{applicant_number}_{active_jd}",
                "timestamp": datetime.now().isoformat(),
                "total_questions": len(interview_session.all_questions_asked),
                "questions_and_answers": [
                    q.model_dump() for q in interview_session.all_questions_asked
                ],
                "evaluations": [],
                "total_score": 0,
            }

            total_score = 0
            for eval_item, q in zip(
                interview_session.all_evaluations,
                interview_session.all_questions_asked,
            ):
                if not eval_item:
                    continue
                scores = getattr(eval_item, "scores", eval_item)
                if not scores:
                    continue

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
                        else (scores.__dict__ if hasattr(scores, "__dict__") else {}),
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
            max_possible = len(interview_session.all_evaluations) * 50
            results["max_possible_score"] = max_possible
            results["final_percentage"] = (
                (total_score / max_possible) * 100 if max_possible > 0 else 0
            )

            # 4. Generate the overall summary
            # Pass the results so far (as a string) to the evaluation method
            logger.info("Generating overall evaluation summary...")
            summary_input_text = json.dumps(results)
            overall_summary_text = ""
            with st.spinner("Generating overall summary..."):
                overall_summary_text = controller.get_overall_evaluation(
                    evaluation_text=summary_input_text
                )

            # 5. Add the summary to the results dictionary
            results["overall_evaluation_summary"] = overall_summary_text
            logger.info("Overall summary generated and added to results.")

            # 6. Convert *final* dict (with summary) to JSON string for saving
            final_interview_jsons = json.dumps(results, indent=2, ensure_ascii=False)

            # 7. Call the controller method to save
            with st.spinner("Saving your interview results..."):
                controller.interview_result_saver(
                    applicant_number=applicant_number,
                    active_jd=active_jd,
                    interview_jsons=final_interview_jsons,
                )

            # 8. Set the flag
            st.session_state.interview_results_saved = True
            logger.info(
                f"Interview results saved for {applicant_number} for {active_jd}"
            )

        except Exception as e:
            logger.error(f"Failed to auto-save interview results: {e}", exc_info=True)
            # Display a more user-friendly error
            st.error(
                "An error occurred while saving your results. Please contact support."
            )

    # This check was already here, ensures session exists
    interview_session = st.session_state.get("interview_session")
    if not interview_session:
        st.error("Session not found.")
        return

    st.markdown("---")
    if st.button("Return Home"):
        # Clean up all session state
        keys_to_clear = [
            "interview_session",
            "interview_questions_prepared",
            "current_category_index",
            "current_question_in_category",
            "interview_completed",
            "interview_questions",
            "final_application_info",
            "interview_started",
            "interview_results_saved",  # Add flag to cleanup
        ]

        for key in list(st.session_state.keys()):
            # Check for main keys or any dynamic question-specific keys
            if (
                key in keys_to_clear
                or "audio_" in key
                or "answer_" in key
                or "recorded_" in key
                or "evaluated_" in key
                or "submitted_" in key
                or "_start_time_" in key
                or "user_is_recording_" in key
                or "refresher_" in key  # Clean up autorefresh keys
            ):
                if key in st.session_state:
                    del st.session_state[key]

        st.session_state.current_page = "home"
        st.rerun()
