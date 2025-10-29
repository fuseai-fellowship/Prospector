import streamlit as st
import json
from pathlib import Path
from configs.config import settings
from configs.config import logger
import traceback

# Get the path from settings
INTERVIEW_RESULT_PATH = settings.get("interview_result", "data/interviews")


@st.cache_data(ttl=60)
def load_all_results(path: str) -> list:
    """Loads all interview JSON files from the specified path."""
    results = []
    interview_dir = Path(path)

    # Add a log to see what path is being checked
    logger.info(f"Attempting to load results from: {interview_dir.resolve()}")

    if not interview_dir.exists():
        # This error will display in the Streamlit app
        st.error(f"Interview results directory not found: {interview_dir.resolve()}")
        logger.error(
            f"Interview results directory not found: {interview_dir.resolve()}"
        )
        return []

    for file in interview_dir.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_filepath"] = str(file)  # Store filepath to write back
                results.append(data)
        except json.JSONDecodeError:
            logger.warning(f"Could not decode JSON from file: {file.name}")
        except Exception as e:
            logger.error(f"Error loading file {file.name}: {e}")

    return results


def update_result_status(filepath: str, status: str):
    """Reads a JSON file, updates its status, and writes it back."""
    try:
        data = {}
        # Read the existing data
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Update the status
        data["status"] = status

        # Write the updated data back
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Clear the cache to force a re-read
        st.cache_data.clear()

    except Exception as e:
        logger.error(f"Failed to update status for {filepath}: {e}", exc_info=True)
        st.error(f"Failed to update status: {e}")


def get_status_color(status: str) -> str:
    """Returns a color for the status."""
    if status == "Accepted":
        return "green"
    if status == "Rejected":
        return "red"
    return "gray"


# --- MODIFICATION 2: Set width to "large" ---
@st.dialog("Candidate Details", width="large")
def show_details_dialog(result: dict):
    """
    This function is now decorated, so it will automatically
    render as a dialog when called.
    """
    candidate_info = result.get("candidate_info", {})
    name = candidate_info.get("name", "Unknown")

    st.title(f"Details for {name}")
    st.markdown("---")

    st.markdown(f"**Email:** {candidate_info.get('email', 'N/A')}")
    st.markdown(f"**Phone:** {candidate_info.get('phone', 'N/A')}")

    st.subheader("AI Overall Summary")
    summary = result.get("overall_evaluation_summary", "No summary generated.")
    st.text_area(
        "Summary",
        value=summary,
        height=150,
        disabled=True,
        key=f"summary_dialog_{name}",
    )

    st.subheader("Question-by-Question Breakdown")

    questions = result.get("questions_and_answers", [])
    evaluations = result.get("evaluations", [])

    if not questions:
        st.info("No questions or answers were recorded for this interview.")

    # Pair questions with evaluations. Assumes they are in the same order.
    for i, q_data in enumerate(questions):
        eval_data = evaluations[i] if i < len(evaluations) else {}
        scores = eval_data.get("scores", {})

        with st.container(border=True):
            st.markdown(f"**Question {i + 1}:** {q_data.get('question', 'N/A')}")
            st.info(f"**Answer:** {q_data.get('answer', 'N/A')}")

            st.markdown("**Evaluation Scores:**")
            score_cols = st.columns(5)
            score_cols[0].metric("Relevance", f"{scores.get('relevance', 0)}/10")
            score_cols[1].metric("Clarity", f"{scores.get('clarity', 0)}/10")
            score_cols[2].metric("Depth", f"{scores.get('depth', 0)}/10")
            score_cols[3].metric("Accuracy", f"{scores.get('accuracy', 0)}/10")
            score_cols[4].metric("Completeness", f"{scores.get('completeness', 0)}/10")

            assessment = eval_data.get("overall_assessment", "N/A")
            st.caption(f"**AI Assessment:** *{assessment}*")

    st.markdown("---")
    if st.button("Close", use_container_width=True, key=f"close_dialog_{name}"):
        pass


def render_view_results_tab():
    """Main render function for the View Results tab."""
    st.title("Interview Results Dashboard")

    results = load_all_results(INTERVIEW_RESULT_PATH)

    if not results:
        st.info("No interview results found.")
        return

    # Sort results by score (final_percentage)
    try:
        sorted_results = sorted(
            results, key=lambda x: x.get("final_percentage", 0), reverse=True
        )
    except Exception as e:
        st.error(f"Error sorting results: {e}")
        sorted_results = results

    # --- Filters ---
    st.markdown("---")
    status_options = ["Pending", "Accepted", "Rejected"]
    selected_statuses = st.multiselect(
        "Filter by Status", options=status_options, default=status_options
    )

    # Add a count of results found *before* filtering
    st.markdown(f"**Found {len(results)} total interview records.**")

    # Filtered results
    filtered_results = []
    for r in sorted_results:
        if r.get("status", "Pending") in selected_statuses:
            filtered_results.append(r)

    if not filtered_results:
        st.info("No results match the current filter.")
        return

    # --- Results List ---
    for result in filtered_results:
        filepath = result.get("_filepath")
        if not filepath:
            continue

        candidate_info = result.get("candidate_info", {})
        name = candidate_info.get("name", "Unknown")
        job = candidate_info.get("job_applied", "Unknown")
        score = result.get("final_percentage", 0)
        status = result.get("status", "Pending")

        # --- MODIFICATION 1: Get AI summary for card ---
        summary = result.get("overall_evaluation_summary", "No summary generated.")
        # Truncate summary for display on card
        summary_preview = (summary[:120] + "...") if len(summary) > 120 else summary

        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 2])

            with col1:
                st.subheader(name)
                st.caption(f"Applied for: **{job}**")

                # --- MODIFICATION 1 (Continued): Display summary preview ---
                st.markdown(f"**AI Summary:** *{summary_preview}*")

                # --- "View Details" button ---
                if st.button(
                    "View Details", key=f"details_{filepath}", use_container_width=True
                ):
                    show_details_dialog(result)

            with col2:
                st.metric("Final Score", f"{score:.1f}%")

            with col3:
                st.markdown(
                    f"**Status:** <span style='color:{get_status_color(status)};'>{status}</span>",
                    unsafe_allow_html=True,
                )

                # Action buttons
                btn_cols = st.columns(2)
                with btn_cols[0]:
                    if st.button(
                        "Accept",
                        key=f"accept_{filepath}",
                        use_container_width=True,
                        type="primary",
                        disabled=(status == "Accepted"),
                    ):
                        update_result_status(filepath, "Accepted")
                        st.rerun()

                with btn_cols[1]:
                    if st.button(
                        "Reject",
                        key=f"reject_{filepath}",
                        use_container_width=True,
                        disabled=(status == "Rejected"),
                    ):
                        update_result_status(filepath, "Rejected")
                        st.rerun()
