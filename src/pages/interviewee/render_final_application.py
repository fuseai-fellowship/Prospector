# import streamlit as st
import streamlit as st
from .render_processing_your_information import render_interview_processing


def render_final_application(application_controller, updated_info, resume_file_name):
    if st.session_state.get("interview_step"):
        msg = st.empty()
        msg.success("✅ Application saved successfully!")

        render_interview_processing(application_controller=application_controller)
        msg.empty()

        return st.session_state.get("interview_step")

    active_jd_name = st.session_state.get("active_jd_name")
    st.subheader("Here is you final Extracted Resume")
    st.write(updated_info)

    submit_button = st.button("Submit")
    if submit_button:
        application_controller.save_applicaticant_info(
            updated_info, resume_file_name, active_jd_name
        )

        st.session_state.interview_step = True

        st.rerun()

    # st.write("All session_state items:")
    # for key, value in st.session_state.items():
    #     st.write(f"{key} : {value}")

    return None
