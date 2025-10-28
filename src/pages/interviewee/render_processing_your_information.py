import streamlit as st
import time


def render_interview_processing(application_controller):
    if "is_qualified" not in st.session_state:
        with st.spinner("🔍 Checking your resume... Please wait."):
            time.sleep(2)  # simulate processing
            st.session_state["is_qualified"] = (
                application_controller.check_qualification()
            )

    # Use it
    is_qualified = st.session_state["is_qualified"]

    # Layout
    col1, col2 = st.columns([1, 1])

    if is_qualified:
        st.subheader("🎯 You’re Qualified!")
        st.success("Congratulations! You’ve been selected for the AI Interview.")

        with st.expander("📘 Interview Instructions", expanded=True):
            st.markdown("""
                **Welcome to your AI-powered Interview!**
                Before you begin, please review the following instructions carefully:
                
                - 🗣️ You’ll be asked **several questions** based on your resume and the job description.
                - ⏱️ You have a **maximum of 2 minutes** to speak your answer.
                - ✍️ After speaking, you’ll get **1 minute to edit** or refine your response.
                - 🌐 Please answer in **English** and maintain **professional integrity** — this simulates a real interview.
                - 🎧 Ensure your **microphone and internet** are working properly before you begin.
                """)

        st.info("Click below when you’re ready to start your AI Interview.")
        if st.button("🚀 Start Interview"):
            st.success("Interview Started!")
            st.session_state["interview_started"] = True
            st.session_state.current_page = "interview_page"
            st.rerun()

    else:
        with col1:
            st.error("❌ Unfortunately, you did not qualify for the interview.")
            st.write(
                "We encourage you to improve your resume and try again for the next new open position!"
            )

            if st.button("🏠 Go Home"):
                # Clear all session states except 'active_jd_name'
                active_jd_name = st.session_state.get("active_jd_name")
                active_jd = st.session_state.get("active_jd")
                st.session_state.clear()
                if active_jd:
                    st.session_state["active_jd_name"] = active_jd_name
                    st.session_state["active_jd"] = active_jd

                # Switch to home page in the main app
                st.session_state.current_page = "home"

                st.success("Returning to Home Page...")
                st.rerun()
        with col2:
            st.image(
                "https://cdn-icons-png.flaticon.com/512/4076/4076549.png",
                width=220,
                caption="Keep Improving!",
            )
