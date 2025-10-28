import streamlit as st
import time

# Initialize session state variables
if "running" not in st.session_state:
    st.session_state.running = False
if "time_up" not in st.session_state:
    st.session_state.time_up = False
if "start_time" not in st.session_state:
    st.session_state.start_time = 0

TIMER_SECONDS = 10  # Set your timer duration


# Function to trigger the main action
def trigger_action():
    st.session_state.running = False
    st.session_state.time_up = False
    st.success("✅ Action triggered!")


# Start button
if st.button("Start Timer"):
    st.session_state.running = True
    st.session_state.start_time = time.time()

# Stop button
if st.button("Stop"):
    st.session_state.running = False
    trigger_action()

# Timer display
placeholder = st.empty()

if st.session_state.running:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = TIMER_SECONDS - elapsed
    if remaining > 0:
        placeholder.text(f"Time remaining: {remaining} seconds")
        time.sleep(1)
        st.rerun()  # rerun to update timer
    else:
        st.session_state.time_up = True
        st.session_state.running = False

# Trigger action automatically if timer is up
if st.session_state.time_up:
    trigger_action()
