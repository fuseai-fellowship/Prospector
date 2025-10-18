import streamlit as st


def render():
    st.title("🎤 Interview Page")
    name = st.text_input("Enter your name:")
    if st.button("Submit"):
        st.success(f"Hello {name}, good luck with your interview!")
