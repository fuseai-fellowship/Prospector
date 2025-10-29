# AI-Powered Interview Platform

This is a comprehensive, voice-based interview application built with Streamlit. It allows admins to upload job descriptions, candidates to take AI-powered audio interviews, and interviewers to review, evaluate, and manage the results.

## Key Features

* **Admin Dashboard**: Upload, manage, and set active Job Descriptions (JDs).
* **Voice-Based Interview Flow**: Candidates interact via voice. The app uses Text-to-Speech (TTS) to ask questions and Speech-to-Recognition (ASR) to transcribe answers.
* **Real-time AI Evaluation**: Candidate answers are evaluated in real-time by an AI agent based on relevance, clarity, depth, and accuracy.
* **Dynamic Follow-ups**: The system can generate follow-up questions on the fly if a candidate's answer is incomplete or needs more detail (limited to one follow-up per question).
* **Results Dashboard**: A private admin tab to view all completed interviews, sorted by score and filterable by status (Pending, Accepted, Rejected).
* **Accept/Reject Workflow**: Admins can directly accept or reject candidates from the dashboard, which updates the interview result file.
* **Detailed Reporting**: A "pop-out" dialog shows a full breakdown of the interview, including the AI's overall summary, each question, the candidate's answer, and the detailed evaluation scores.

## How to Run

### Prerequisites

* **uv**: This project uses `uv` for package management and running. See the [uv installation guide](https://github.com/astral-sh/uv).
* **PortAudio**: The `sounddevice` library requires the PortAudio C library.
    * **macOS (Homebrew):** `brew install portaudio`
    * **Windows:** `uv` *should* bundle this, but if not, you may need to install it manually.
    * **Linux (APT):** `sudo apt-get install portaudio19-dev`
* **API Keys**: You will need API keys from your AI providers (Google -> For LLM Request, Groq -> For Speech Related LLM)

### Setup & Running

1.  **Clone the Repository**
    ```sh
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Set Up Environment**
    Rename or copy the `.env_example` file to `.env` and add your API keys.

    ```sh
    # .env  
    GOOGLE_API_KEY="your_google_api_key_here"
    GROQ_API_KEY="your_groq_api_key_here"
    ```

3.  **Install Dependencies**
    `uv sync` will create a virtual environment and install all packages from `requirements.txt`.
    ```sh
    uv sync
    ```

4.  **Run the Application**
    This command will run the Streamlit app using the `uv`-managed environment.
    ```sh
    uv run streamlit run main.py
    ```

5.  **Access the App**
    Open your browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

## How It Works

1.  **Admin (Setup)**: The admin navigates to the "Admin Dashboard" (`/admin`) and uploads a new Job Description.
2.  **Candidate (Interview)**: The candidate opens the main page, selects the active job, and begins the interview. The app plays the first question's audio.
3.  **Candidate (Answering)**: The candidate clicks "Start Recording," provides their verbal answer, and clicks "Stop Recording."
4.  **System (Evaluation)**: The app transcribes the audio, sends the text to the `EvaluationAgent`, and receives scores. If the answer is poor, the agent generates a follow-up question.
5.  **System (Loop)**: The app moves to the next question (or the follow-up) and repeats the process.
6.  **System (Completion)**: After the interview, the app generates an "overall evaluation summary" and saves the complete interview JSON (e.g., `9876543210_AI_Engineer.json`) to the results directory.
7.  **Admin (Review)**: The admin goes to the "View Interview Results" tab, sees the new candidate, reviews their score and the AI summary, and then clicks "View Details" to see the full report. They can then "Accept" or "Reject" the candidate.