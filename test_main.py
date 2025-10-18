import streamlit as st
from pathlib import Path
import importlib.util

st.set_page_config(page_title="Interview App", page_icon="🎯", layout="centered")


def load_module_from_path(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROOT = Path(__file__).parent
PAGES = {
    "Home": ROOT / "pages" / "home.py",
    "Interview": ROOT / "pages" / "interview_page.py",
    "Admin": ROOT / "pages" / "interviewer_page.py",
}
st.sidebar.title("Navigation")

if "page" not in st.session_state:
    st.session_state.page = "Home"

for page_name in PAGES.keys():
    if st.sidebar.button(page_name, key=page_name):
        st.session_state.page = page_name

st.sidebar.markdown("---")

selected_path = PAGES[st.session_state.page]
page_module = load_module_from_path(
    selected_path, f"{st.session_state.page.lower()}_page"
)
page_module.render()
