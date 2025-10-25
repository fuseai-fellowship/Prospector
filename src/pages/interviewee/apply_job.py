import os

from ...utils.validator import Validator
from .render_application_info import render_application_info


def apply_job(st, application_controller):
    submitted_cv = None
    info = None
    active_jd = st.session_state.get("active_jd")
    active_jd_name = st.session_state.get("active_jd_name")
    validator = Validator()

    st.header(f"📌 Applying for: {active_jd_name}")

    with st.expander("🔎 Job Description", expanded=False):
        st.markdown(active_jd)

    st.markdown("---")

    # APPLICATION FORM
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
                    submitted_cv = True
                else:
                    st.error("Please upload a resume file.")
                    submitted_cv = False
            else:
                st.error(f"❌ {validation_msg}")
                submitted_cv = False

    if submitted_cv:
        info = render_application_info(
            resume_path=resume_file.name,
            application_controller=application_controller,
            # st=st,
        )

    if info:
        st.write(info)  # <-- shows in Streamlit UI
        print(info)
