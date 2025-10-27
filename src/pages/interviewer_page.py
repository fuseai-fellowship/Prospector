"""
Admin/Interviewer Dashboard
Upload job descriptions and view interview results
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from ..controller.interview_controller import JdController
from ..utils.db import db, Job, save_job

session = db.get_session()


def render():
    st.title("🧑‍💼 Admin Dashboard")
    st.markdown("Upload job descriptions and review candidate interview results")

    # Initialize session state
    if "uploaded_jd" not in st.session_state:
        st.session_state.uploaded_jd = None
    if "jd_file_name" not in st.session_state:
        st.session_state.jd_file_name = None
    if "processed_jd" not in st.session_state:
        st.session_state.processed_jd = None
    if "word_count" not in st.session_state:
        st.session_state.word_count = 0
    if "char_count" not in st.session_state:
        st.session_state.char_count = 0
    if "last_jd_text" not in st.session_state:
        st.session_state.last_jd_text = ""

    # Create tabs
    tab1, tab2 = st.tabs(["📋 Upload Job Description", "📊 View Interview Results"])

    # ==================== TAB 1: UPLOAD JD ====================
    with tab1:
        render_upload_jd_tab()

    # ==================== TAB 2: VIEW RESULTS ====================
    with tab2:
        render_view_results_tab()


def render_upload_jd_tab():
    jd_controller = JdController()

    """Render the Upload Job Description tab"""
    st.header("📋 Upload Job Description")
    st.markdown("Paste a job description to make it available for interviews")

    jd_text = st.text_area(
        "Job Description",
        value=st.session_state.get("last_jd_text", ""),
        height=400,
        placeholder="""Job Title: [Insert concise job title, e.g., Software Engineer]

Job Summary:

A brief 2–3 sentence overview describing the main purpose of the role and its impact on the company.

Key Responsibilities:

[Responsibility 1]

[Responsibility 2]

[Responsibility 3]

Requirements:

[Required skill or qualification 1]

[Required skill or qualification 2]

[Years of experience or tools familiarity]

Qualifications (Preferred):

[Preferred degree, certification, or experience]

Location: [City / Remote]
Employment Type: [Full-time / Part-time / Contract]
""",
        help="Paste the complete job description including position, requirements, responsibilities, etc.",
        key="jd_text_area",
    )

    # Process JD on Submit and persist result in session_state
    if st.button("Submit", key="submit_jd"):
        word_count, char_count, processed = jd_controller.process_jd(jd_text=jd_text)
        st.session_state.processed_jd = processed
        st.session_state.word_count = word_count
        st.session_state.char_count = char_count
        st.session_state.last_jd_text = jd_text

        col1, col2, col3 = st.columns(3)
        col1.metric("Words", word_count)
        col2.metric("Characters", char_count)
        col3.metric("Lines", processed.count("\n") + 1 if processed else 0)

        if word_count < 50:
            st.warning(
                "⚠️ Job description seems short. Consider adding more details for better interview questions."
            )
        elif word_count > 1000:
            st.info(
                "ℹ️ Long job description detected. This will generate comprehensive questions."
            )
        else:
            st.success("✅ Good length for job description")

    st.markdown("---")

    # read processed_jd from session_state so it persists across reruns
    processed_jd = st.session_state.get("processed_jd")

    # Save/Update JD (this block will stay visible as long as processed_jd is stored in session_state)
    if processed_jd and processed_jd.strip():
        st.subheader("⚙️ Job Description Settings")

        jd_name = st.text_input(
            "Job Description Name",
            value=st.session_state.get("jd_name", "Dummy Job"),
            key="jd_name_input",
            help="A unique name to identify this job description",
        )

        make_active = st.checkbox(
            "Set as active JD for interviews",
            value=True,
            key="make_active_checkbox",
            help="When checked, this JD will be visible to Interviewee",
        )

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "💾 Save Job Description",
                type="primary",
                key="save_jd_btn",
                use_container_width=True,
            ):
                # optionally update session_state jd_name so it persists
                st.session_state.jd_name = jd_name
                save_job_description(processed_jd, jd_name, make_active)
                st.session_state.processed_jd = None
                st.session_state.last_jd_text = ""

        with col2:
            if st.button(
                "🗑️ Clear",
                key="clear_jd_btn",
                use_container_width=True,
            ):
                # Clear persisted values and rerun to update UI
                st.session_state.processed_jd = None
                st.session_state.last_jd_text = ""
                st.session_state.word_count = 0
                st.session_state.char_count = 0
                st.session_state.jd_name = None
                st.rerun()

        with col3:
            # Download as JSON
            jd_json = {
                "name": jd_name,
                "content": processed_jd,
                "timestamp": datetime.now().isoformat(),
                "word_count": len(processed_jd.split()),
            }
            st.download_button(
                "📥 Download as JSON",
                data=json.dumps(jd_json, indent=2),
                file_name=f"{jd_name}.json",
                mime="application/json",
                use_container_width=True,
                key="download_jd_json",
            )

        st.markdown("---")

    # Show saved job descriptions
    render_saved_jds()


def render_saved_jds():
    """Display all saved job descriptions"""
    st.subheader("📁 Saved Job Descriptions")

    jd_files_path = Path("data/jd_files")

    if not jd_files_path.exists():
        st.info("ℹ️ No saved job descriptions yet")
        return

    # Get all saved JD JSON files
    jd_files = list(jd_files_path.glob("*.json"))

    if not jd_files:
        st.info("ℹ️ No saved job descriptions yet")
        return

    st.markdown(f"**Total Saved:** {len(jd_files)}")

    # Display each JD
    for jd_file in sorted(jd_files, reverse=True):
        try:
            with open(jd_file, "r") as f:
                jd_data = json.load(f)

            is_active = st.session_state.get("active_jd_name") == jd_data.get("name")

            # Create expander with active indicator
            expander_title = (
                f"{'✅ ' if is_active else '📄 '}{jd_data.get('name', jd_file.stem)}"
            )
            if is_active:
                expander_title += " (Active)"

            with st.expander(expander_title):
                col1, col2, col3 = st.columns(3)

                col1.markdown(
                    f"**Created:** {jd_data.get('timestamp', 'Unknown')[:10]}"
                )
                col2.markdown(f"**Words:** {jd_data.get('word_count', 'N/A')}")
                col3.markdown(
                    f"**Status:** {'🟢 Active' if is_active else '⚪ Inactive'}"
                )

                # Content preview
                st.markdown("**Content Preview:**")
                content = jd_data.get("content", "")
                st.text_area(
                    "JD Content",
                    value=content[:500] + "..." if len(content) > 500 else content,
                    height=150,
                    disabled=True,
                    key=f"preview_{jd_file.stem}",
                )

                # Action buttons
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if is_active:
                        # Show "Deactivate" button if JD is active
                        if st.button(
                            "🚫 Deactivate",
                            key=f"deactivate_{jd_file.stem}",
                            use_container_width=True,
                        ):
                            st.session_state.pop("active_jd", None)
                            st.session_state.pop("active_jd_name", None)
                            st.session_state.pop("interview_ready", None)
                            st.success(
                                f"❎ '{jd_data.get('name')}' has been deactivated."
                            )
                            st.rerun()
                    else:
                        # Show "Set Active" button if JD is inactive
                        if st.button(
                            "✅ Set Active",
                            key=f"activate_{jd_file.stem}",
                            use_container_width=True,
                        ):
                            st.session_state.active_jd = jd_data.get("content")
                            st.session_state.active_jd_name = jd_data.get("name")
                            st.session_state.interview_ready = True
                            st.success(f"✅ '{jd_data.get('name')}' is now active!")
                            st.rerun()

                with col2:
                    st.download_button(
                        "📥 Download",
                        data=json.dumps(jd_data, indent=2),
                        file_name=f"{jd_data.get('name')}.json",
                        mime="application/json",
                        key=f"download_{jd_file.stem}",
                        use_container_width=True,
                    )

                with col3:
                    if st.button(
                        "📋 Copy Text",
                        key=f"copy_{jd_file.stem}",
                        use_container_width=True,
                    ):
                        st.code(jd_data.get("content", ""), language=None)

                with col4:
                    if st.button(
                        "🗑️ Delete",
                        key=f"delete_{jd_file.stem}",
                        use_container_width=True,
                    ):
                        jd_file.unlink()
                        st.success(f"Deleted {jd_data.get('name')}")
                        st.rerun()

        except Exception as e:
            st.error(f"Error loading {jd_file.name}: {str(e)}")


def save_job_description(processed_jd, jd_name, make_active):
    """Save job description to file"""
    try:
        save_job(session=session, title=jd_name)

        # Create directory if not exists
        jd_path = Path("data/jd_files")
        jd_path.mkdir(parents=True, exist_ok=True)

        # Prepare data
        jd_data = {
            "name": jd_name,
            "content": processed_jd,
            "timestamp": datetime.now().isoformat(),
            "word_count": len(processed_jd.split()),
            "char_count": len(processed_jd),
        }

        # Save to file
        filename = f"{jd_name.replace(' ', '_')}.json"
        filepath = jd_path / filename

        with open(filepath, "w") as f:
            json.dump(jd_data, f, indent=2)

        st.success(f"✅ Job description saved: {filename}")

        # Set as active if requested
        if make_active:
            st.session_state.active_jd = processed_jd
            st.session_state.active_jd_name = jd_name
            st.session_state.interview_ready = True
            st.info("🟢 This job description is now active for interviews")

        st.balloons()

    except Exception as e:
        st.error(f"❌ Error saving job description: {str(e)}")


def render_view_results_tab():
    """Render the View Results tab"""
    st.header("📊 Interview Results")
    st.markdown("Review completed candidate interviews")

    # Check for completed interviews
    if (
        "completed_interviews" not in st.session_state
        or not st.session_state.completed_interviews
    ):
        st.info("ℹ️ No completed interviews yet")

        with st.expander("📖 What you'll see here"):
            st.markdown("""
            Once candidates complete their interviews, you'll see:
            
            - **Candidate Information**: Name, email, date
            - **Overall Score**: Percentage and performance level
            - **Detailed Breakdown**: Scores for each criterion
            - **Question-by-Question Analysis**: Individual answers and evaluations
            - **Export Options**: Download results as JSON
            
            **Scoring Breakdown:**
            - Each question scored on 5 criteria (0-10 points each)
            - Maximum 50 points per question
            - Overall percentage calculated across all questions
            
            **Performance Levels:**
            - 🌟 80-100%: Excellent
            - 👍 60-79%: Good
            - ⚠️ 40-59%: Average
            - 📉 Below 40%: Needs Improvement
            """)
        return

    # Summary statistics
    total_interviews = len(st.session_state.completed_interviews)
    st.metric("Total Completed Interviews", total_interviews)

    st.markdown("---")

    # Display each interview result
    for idx, result in enumerate(st.session_state.completed_interviews):
        display_interview_result(result, idx)


def display_interview_result(result, idx):
    """Display a single interview result"""

    candidate_name = result.get("candidate_name", "Anonymous")
    session_name = result.get("session_name", "Unknown Session")
    timestamp = result.get("timestamp", "")[:19].replace("T", " ")

    # Calculate overall statistics
    evaluations = result.get("evaluations", [])
    total_score = 0
    max_score = 0

    criteria_totals = {
        "relevance": 0,
        "clarity": 0,
        "depth": 0,
        "accuracy": 0,
        "completeness": 0,
    }

    for eval_item in evaluations:
        scores = eval_item.get("scores", {})
        for criterion in criteria_totals.keys():
            criteria_totals[criterion] += scores.get(criterion, 0)
        total_score += sum(scores.values())
        max_score += 50

    percentage = (total_score / max_score * 100) if max_score > 0 else 0

    # Performance emoji
    if percentage >= 80:
        perf_emoji = "🌟"
        perf_color = "#28a745"
    elif percentage >= 60:
        perf_emoji = "👍"
        perf_color = "#17a2b8"
    elif percentage >= 40:
        perf_emoji = "⚠️"
        perf_color = "#ffc107"
    else:
        perf_emoji = "📉"
        perf_color = "#dc3545"

    # Expander for each interview
    with st.expander(
        f"{perf_emoji} {candidate_name} | {percentage:.1f}% | {session_name} | {timestamp}",
        expanded=(idx == 0),
    ):
        # Header with candidate info
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**👤 Candidate:** {candidate_name}")
        col2.markdown(f"**📅 Date:** {timestamp}")
        col3.markdown(f"**❓ Questions:** {len(evaluations)}")

        if result.get("candidate_email"):
            st.markdown(f"**📧 Email:** {result.get('candidate_email')}")

        st.markdown("---")

        # Overall performance
        st.subheader("📈 Overall Performance")

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            st.markdown(
                f"""
            <div style="text-align: center; padding: 15px; background-color: {perf_color}; color: white; border-radius: 10px;">
                <div style="font-size: 32px; font-weight: bold;">{percentage:.1f}%</div>
                <div style="font-size: 14px;">Overall Score</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        col2.metric(
            "Relevance", f"{criteria_totals['relevance']}/{len(evaluations) * 10}"
        )
        col3.metric("Clarity", f"{criteria_totals['clarity']}/{len(evaluations) * 10}")
        col4.metric("Depth", f"{criteria_totals['depth']}/{len(evaluations) * 10}")
        col5.metric(
            "Accuracy", f"{criteria_totals['accuracy']}/{len(evaluations) * 10}"
        )
        col6.metric(
            "Completeness", f"{criteria_totals['completeness']}/{len(evaluations) * 10}"
        )

        # Performance assessment
        if percentage >= 80:
            st.success(
                "🌟 **Excellent Performance** - Strong candidate with comprehensive knowledge"
            )
        elif percentage >= 60:
            st.info("👍 **Good Performance** - Solid understanding with minor gaps")
        elif percentage >= 40:
            st.warning("⚠️ **Average Performance** - Basic knowledge, needs development")
        else:
            st.error("📉 **Needs Improvement** - Significant gaps in understanding")

        st.markdown("---")

        # Question-by-question breakdown
        st.subheader("📝 Detailed Question Analysis")

        for i, eval_item in enumerate(evaluations, 1):
            with st.container():
                st.markdown(f"**Question {i}**")
                st.markdown(f"*{eval_item.get('question', 'N/A')}*")

                # Answer
                with st.expander("💬 View Answer"):
                    st.markdown(eval_item.get("answer", "No answer provided"))

                # Scores
                col1, col2, col3, col4, col5 = st.columns(5)
                scores = eval_item.get("scores", {})

                col1.metric("Relevance", f"{scores.get('relevance', 0)}/10")
                col2.metric("Clarity", f"{scores.get('clarity', 0)}/10")
                col3.metric("Depth", f"{scores.get('depth', 0)}/10")
                col4.metric("Accuracy", f"{scores.get('accuracy', 0)}/10")
                col5.metric("Completeness", f"{scores.get('completeness', 0)}/10")

                # Assessment
                st.info(
                    f"**💭 Assessment:** {eval_item.get('assessment', 'No assessment')}"
                )

                # Follow-up indicator
                if eval_item.get("follow_up_status"):
                    st.warning("🔄 Follow-up question was asked for this response")

                st.markdown("---")

        # Export options
        col1, col2, col3 = st.columns(3)

        with col1:
            # Download full report
            json_str = json.dumps(result, indent=2)
            st.download_button(
                label="📥 Download Full Report",
                data=json_str,
                file_name=f"interview_{candidate_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key=f"download_report_{idx}",
                use_container_width=True,
            )

        with col2:
            # Download summary
            summary = {
                "candidate": candidate_name,
                "email": result.get("candidate_email", ""),
                "date": timestamp,
                "overall_score": f"{percentage:.1f}%",
                "total_questions": len(evaluations),
                "scores": criteria_totals,
            }
            st.download_button(
                label="📊 Download Summary",
                data=json.dumps(summary, indent=2),
                file_name=f"summary_{candidate_name.replace(' ', '_')}.json",
                mime="application/json",
                key=f"download_summary_{idx}",
                use_container_width=True,
            )

        with col3:
            # Delete result
            if st.button(
                "🗑️ Delete Result", key=f"delete_result_{idx}", use_container_width=True
            ):
                if st.session_state.get(f"confirm_delete_{idx}"):
                    st.session_state.completed_interviews.pop(idx)
                    st.success("✅ Result deleted")
                    st.rerun()
                else:
                    st.session_state[f"confirm_delete_{idx}"] = True
                    st.warning("⚠️ Click again to confirm deletion")
