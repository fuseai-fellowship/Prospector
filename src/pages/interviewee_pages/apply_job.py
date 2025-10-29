import os

from ...utils.validator import Validator
from .render_application_info import render_application_info


def apply_job(st, application_controller):
    active_jd = st.session_state.get("active_jd")
    active_jd_name = st.session_state.get("active_jd_name")
    validator = Validator()

    # Initialize session state for application flow
    if "application_submitted" not in st.session_state:
        st.session_state.application_submitted = False
    if "resume_file_name" not in st.session_state:
        st.session_state.resume_file_name = None

    st.header(f"📌 Applying for: {active_jd_name}")

    with st.expander("🔎 Job Description", expanded=False):
        st.markdown(active_jd)

    st.markdown("---")

    # If application already submitted, go directly to the form
    if st.session_state.application_submitted and st.session_state.resume_file_name:
        render_application_info(
            resume_path=st.session_state.resume_file_name,
            application_controller=application_controller,
        )

        return

    # APPLICATION FORM (only show if not yet submitted)
    st.subheader("📝 Application Form")

    with st.form("application_form"):
        resume_file = st.file_uploader(
            "Upload resume (PDF or DOCX)*",
            type=["pdf", "docx", "doc"],
            key="app_resume",
        )

        submit_app = st.form_submit_button("📨 Submit Application")

        if submit_app:
            resume_validation_status, validation_msg = validator.validate_resume(
                resume_file=resume_file
            )
            if resume_validation_status:
                if resume_file is not None:
                    save_path = os.path.join(
                        "data", "applications", "resumes", resume_file.name
                    )
                    with open(save_path, "wb") as f:
                        f.write(resume_file.getbuffer())
                    st.success(
                        f"✅ Resume submitted successfully! Saved as {save_path}"
                    )

                    # Store in session state
                    st.session_state.application_submitted = True
                    st.session_state.resume_file_name = resume_file.name
                    st.rerun()  # Rerun to show the application info form
                else:
                    st.error("Please upload a resume file.")
            else:
                st.error(f"❌ {validation_msg}")
