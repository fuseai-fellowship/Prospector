"""
Interviewee Portal for Streamlit

Main entrypoint: render()

Features:
- Shows active job description (pulled from st.session_state.active_jd or data/jd_files if available)
- Application form (name, email, phone, location, cover letter, resume upload)
- Saves application JSON + resume to data/applications/
- Optional interview flow: generates simple interview questions from JD text and lets candidate answer them
- On interview completion, saves interview result to st.session_state.completed_interviews and to data/interviews/

This is intended to pair with the Admin Dashboard you provided.
"""

import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import uuid
import os

from ..utils.validator import Validator
from ..controller.application_controller import ApplicationController
from .interviewee.apply_job import apply_job

application_controller = ApplicationController()


def render():
    st.title("👩‍💻 Interviewee Portal")
    st.markdown("Apply for the active job and complete the interview")

    # Ensure directories
    Path("data/applications").mkdir(parents=True, exist_ok=True)
    Path("data/applications/resumes").mkdir(parents=True, exist_ok=True)
    Path("data/applications/processed_resumes").mkdir(parents=True, exist_ok=True)
    Path("data/interviews").mkdir(parents=True, exist_ok=True)

    active_jd = st.session_state.get("active_jd")

    if not active_jd:
        st.info(
            "ℹ️ No active job is available right now. Check back later or contact the recruiter."
        )
        return

    apply_job(st=st, application_controller=application_controller)

    # INTERVIEW FLOW (if initialized in session_state)
    if st.session_state.get("interview_questions"):
        st.subheader("🎯 Interview")

        questions = st.session_state["interview_questions"]
        idx = st.session_state.get("current_question_index", 0)

        st.markdown(f"**Question {idx + 1} of {len(questions)}**")
        st.write(questions[idx])

        answer = st.text_area(
            "Your answer",
            value=st.session_state.get("current_interview_answers", [""])[idx],
            height=200,
            key=f"answer_{idx}",
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ Previous", key=f"prev_{idx}", disabled=(idx == 0)):
                st.session_state["current_interview_answers"][idx] = answer
                st.session_state["current_question_index"] = max(0, idx - 1)
                st.rerun()
        with col2:
            if st.button(
                "➡️ Next", key=f"next_{idx}", disabled=(idx == len(questions) - 1)
            ):
                st.session_state["current_interview_answers"][idx] = answer
                st.session_state["current_question_index"] = min(
                    len(questions) - 1, idx + 1
                )
                st.rerun()
        with col3:
            if st.button("✅ Submit Interview", key="submit_interview"):
                st.session_state["current_interview_answers"][idx] = answer
                save_interview_result()
                st.success("✅ Interview submitted. Thank you!")
                # clear interview state
                for k in [
                    "interview_questions",
                    "current_question_index",
                    "current_interview_answers",
                    "interview_app_id",
                    "current_candidate",
                ]:
                    st.session_state.pop(k, None)
                st.rerun()


def generate_questions_from_jd(jd_text: str, n: int = 5):
    """Simple heuristic question generator from JD text.
    Picks lines that look like requirements or responsibilities, or falls back to sentences.
    """
    lines = [l.strip() for l in jd_text.splitlines() if l.strip()]
    candidates = []
    keywords = [
        "require",
        "respons",
        "skill",
        "responsibility",
        "experience",
        "qualification",
    ]

    for l in lines:
        low = l.lower()
        if any(k in low for k in keywords):
            candidates.append(l)

    # If not enough, split into sentences
    if len(candidates) < n:
        import re

        sentences = re.split(r"(?<=[.!?])\s+", jd_text)
        for s in sentences:
            s = s.strip()
            if s and s not in candidates:
                candidates.append(s)
            if len(candidates) >= n:
                break

    # Build question prompts
    questions = []
    for i, c in enumerate(candidates[:n], 1):
        if len(c.split()) < 8:
            questions.append(
                f"Explain how you meet the following requirement or responsibility: {c}"
            )
        else:
            questions.append(f"Answer the following: {c}")

    # Fallback simple generic questions
    while len(questions) < n:
        questions.append(
            "Describe a challenging problem you solved that's relevant to this role, and how you approached it."
        )

    return questions


def save_interview_result():
    """Collect info from session_state and save interview result both in session_state.completed_interviews and to disk."""
    candidate = st.session_state.get("current_candidate") or {}
    questions = st.session_state.get("interview_questions", [])
    answers = st.session_state.get("current_interview_answers", [])
    app_id = st.session_state.get("interview_app_id", uuid.uuid4().hex[:8])

    evaluations = []
    for q, a in zip(questions, answers):
        evaluations.append(
            {
                "question": q,
                "answer": a,
                # placeholder scores/assessment empty for Admin to review or for auto-eval later
                "scores": {
                    "relevance": 0,
                    "clarity": 0,
                    "depth": 0,
                    "accuracy": 0,
                    "completeness": 0,
                },
                "assessment": "",
                "follow_up_status": False,
            }
        )

    result = {
        "candidate_name": candidate.get("candidate_name", "Anonymous"),
        "candidate_email": candidate.get("candidate_email", ""),
        "session_name": st.session_state.get("active_jd_name", "Unknown Job"),
        "timestamp": datetime.now().isoformat(),
        "evaluations": evaluations,
        "application_id": app_id,
    }

    # Append to session_state.completed_interviews
    if "completed_interviews" not in st.session_state:
        st.session_state.completed_interviews = []
    st.session_state.completed_interviews.append(result)

    # Save to disk
    try:
        filepath = Path("data/interviews") / f"interview_{app_id}.json"
        with open(filepath, "w") as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        st.error(f"Failed to save interview result: {e}")

    return
