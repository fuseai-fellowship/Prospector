from src.pages import home, interviewee_page, interviewer_page
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Prospector - AI Interview Platform",
    page_icon="🎯",
    layout="wide",
)

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# Sidebar navigation
st.sidebar.title("🎯 Prospector")
st.sidebar.markdown("---")

# Navigation buttons
if st.sidebar.button("🏠 Home", use_container_width=True):
    st.session_state.current_page = "home"

if st.sidebar.button("🎤 Interviewee Portal", use_container_width=True):
    st.session_state.current_page = "interview"

if st.sidebar.button("🧑‍💼 Interviewer Dashboard", use_container_width=True):
    st.session_state.current_page = "interviewer"

st.sidebar.markdown("---")
st.sidebar.info("**Current Page:** " + st.session_state.current_page.title())

# Main content area
if st.session_state.current_page == "home":
    home.render()
elif st.session_state.current_page == "interview":
    interviewee_page.render()
elif st.session_state.current_page == "interviewer":
    interviewer_page.render()
