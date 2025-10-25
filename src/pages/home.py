import streamlit as st


def render():
    # Hero section
    st.markdown(
        """
        <style>
        .hero-text {
            text-align: center;
            padding: 2rem 0;
        }
        .hero-title {
            font-size: 3.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 1rem;
        }
        .hero-subtitle {
            font-size: 1.5rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .feature-card {
            padding: 2rem;
            border-radius: 10px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 1rem 0;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .feature-card h3 {
            color: white;
            margin-bottom: 1rem;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Hero
    st.markdown(
        """
        <div class="hero-text">
            <div class="hero-title">🎯 Prospector</div>
            <div class="hero-subtitle">AI-Powered requrictment Platform</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Introduction
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            ### Welcome to Prospector
            
            An intelligent requrictment platform that leverages AI to conduct and evaluate 
            technical interviews. Choose your role below to get started.
        """)

    st.markdown("<br>", unsafe_allow_html=True)

    # Portal selection
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🎤 Interviewee Portal</h3>
                <p>Take your interview with AI-powered questions tailored to your resume and the job description.</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Start Interview", key="start_interview", use_container_width=True
        ):
            st.session_state.current_page = "interview"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="feature-card">
                <h3>🧑‍💼 Interviewer Dashboard</h3>
                <p>Upload job descriptions, review candidate responses, and analyze interview results efficiently.</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Access Dashboard", key="access_dashboard", use_container_width=True
        ):
            st.session_state.current_page = "interviewer"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Features section
    st.markdown("---")
    st.markdown("### ✨ Key Features")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
            #### 🤖 AI-Powered Job Interviews
            Generate contextual questions based on resume and job description
        """)

    with col2:
        st.markdown("""
            #### 📊 Identify Top Candidates
            AI-driven evaluation with detailed scoring, reasoning, and answer-based insights
        """)

    with col3:
        st.markdown("""
            #### 🔄 Dyanic Follow-up Questions
            Dynamic follow-ups based on candidate responses
        """)

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
