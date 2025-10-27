from src.pages import home, interviewee_page, interviewer_page, interview_page
import streamlit as st
from src.utils.db import db

# Initialize DB session
session = db.get_session()

# Page configuration
st.set_page_config(
    page_title="Prospector - AI Interview Platform",
    page_icon="🎯",
    layout="wide",
)

# ---------------------- Session State Initialization ----------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False  # default: not started

# ---------------------- Sidebar Navigation ----------------------
st.sidebar.title("🎯 Prospector")
st.sidebar.markdown("---")

# If interview has NOT started, allow navigation
if not st.session_state.interview_started:
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state.current_page = "home"

    if st.sidebar.button("🎤 Interviewee Portal", use_container_width=True):
        st.session_state.current_page = "interview"

    if st.sidebar.button("🧑‍💼 Interviewer Dashboard", use_container_width=True):
        st.session_state.current_page = "interviewer"

# Display current page info in sidebar
st.sidebar.info("**Current Page:** " + st.session_state.current_page.title())

# ---------------------- Main Content Area ----------------------
# If interview has started, force the interview page
if st.session_state.interview_started:
    st.session_state.current_page = "interview_page"
    interview_page.render()
else:
    # Render the page based on current_page
    if st.session_state.current_page == "home":
        home.render()
    elif st.session_state.current_page == "interview":
        interviewee_page.render()
    elif st.session_state.current_page == "interviewer":
        interviewer_page.render()
    elif st.session_state.current_page == "interview_page":
        interview_page.render()
