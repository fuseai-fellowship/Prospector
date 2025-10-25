from pathlib import Path

from src.agents.jd_resume_processor_agent import ResumeProcessorAgent
from src.utils.llm_client import LLMClient
from configs.config import settings
from src.tools.question_answer_generator import QuestionGenerator
from src.tools.answer_evaluation_tool import AnswerEvaluationTool
from src.agents.evaluation_agent import EvaluationAgent
from src.schemas.interview_questions_schema import (
    QuestionItem,
    InterviewQuestionsSchema,
)

from src.utils.llm_client import LLMClient

llm = LLMClient()


def main():
    # resume_path = Path("data/resume_data/SandeshShrestha_CV.pdf")
    # result = JdResumeProcessorAgent().run(resume_path=resume_path)

    # qn_gen = QuestionAnswerGenerator()
    jd = """
    #     Job Description (JD)

    #     Position: Software Engineer I, Machine Learning
    #     Company: Smart Data Solutions (SDS)

    #     Responsibilities:

    #     Build, deploy, maintain, troubleshoot, and improve machine learning models.

    #     Design and implement new applications leveraging ML and related technologies.

    #     Develop and enhance ML infrastructure.

    #     Automate and optimize existing processes using ML.

    #     Investigate and resolve issues with ML processes.

    #     Perform business analysis and process improvements.

    #     Prepare process documentation and communicate effectively.

    #     Other duties as assigned.

    #     Why Join SDS?

    #     Authentic, innovative, and collaborative culture.

    #     Strong focus on professional growth and development.

    #     Competitive benefits package (insurance, Social Security Fund contribution, PTO, holidays, floating day, etc.).

    #     Flexible work environment.

    #     Opportunity to work with healthcare automation and interoperability at scale.

    #     Job Requirements (JR)

    #     Education & Experience:

    #     Bachelor’s degree in Computer Science or equivalent.

    #     1+ year experience in machine learning, NLP, or deep learning.

    #     Hands-on experience with LLMs and RAGs.

    #     Technical Skills:

    #     Proficiency in at least one modern OOP language (Python, Java, C#, C++).

    #     Knowledge of ML, NLP, CV, and data science libraries.

    #     Relational database basics (MySQL).

    #     Unix/Linux basics.

    #     Experience with Git/version control.

    #     Strong skills in Microsoft Excel, Word, and Windows.

    #     Soft Skills & Attributes:

    #     Highly organized, disciplined, and responsive communicator.

    #     Strong analytical, problem-solving, and process improvement mindset.

    #     Effective writing/documentation skills.

    #     Ability to meet deadlines and consistently complete tasks.

    #     Communication style focused on clarity, simplicity, and actionable insights.
    #     """

    # interview_questions = qn_gen.generateInterviewQnAns(
    #     resume_json=result,
    #     job_description=jd,
    # )

    resume_questions = [
        QuestionItem(
            id=1,
            question="In your mental health project, you performed data cleaning and visualization before applying models like Random Forest and Decision Tree. Why is this initial data preprocessing step crucial for the success of predictive modeling?",
            target_concepts=[
                "Data cleaning",
                "visualization",
                "Data preprocessing",
                "Random Forest",
                "Decision Tree",
                "predictive modeling",
            ],
            difficulty="Easy",
            answer="Data preprocessing is crucial because models are sensitive to data quality. Cleaning handles errors and missing values, while visualization helps identify patterns and outliers. This ensures the models learn from accurate information, leading to more reliable and effective predictive modeling.",
        ),
        QuestionItem(
            id=2,
            question="Your resume lists skills in Django, Docker, and a DevOps workshop. Can you walk me through how you would use Docker to containerize the Django and Streamlit application from your data visualization project for a CI/CD pipeline?",
            target_concepts=["Django", "Streamlit", "Docker", "DevOps"],
            difficulty="Medium",
            answer="I would create a Dockerfile that specifies a Python base image, installs all dependencies for both Django and Streamlit from a requirements file, copies the application code into the container, and exposes the necessary ports. This single, self-contained image can then be used consistently across the DevOps pipeline.",
        ),
        QuestionItem(
            id=3,
            question="Your NLP project used Gemini-7B, LLAMA-8B, FAISS, and Google Embeddings for a chatbot. Explain how these components work together in a system that performs both sentiment analysis and text summarization on user reviews.",
            target_concepts=[
                "Gemini-7B",
                "LLAMA-8B",
                "FAISS",
                "Google Embeddings",
                "sentiment analysis",
                "text summarization",
                "AI-powered chatbot",
            ],
            difficulty="Hard",
            answer="First, Google Embeddings would convert all user reviews into vectors, which are then indexed by FAISS for fast retrieval. For a specific task, the system would retrieve relevant reviews using FAISS, and then an LLM like Gemini-7B or LLAMA-8B would be prompted to perform either sentiment analysis or text summarization on the retrieved text.",
        ),
    ]

    jd_questions = [
        QuestionItem(
            id=10,
            question="This job requires proficiency in an OOP language like Python and relational database basics. How would you use a library from the Python data science stack, like Pandas, to simplify retrieving and structuring data from a MySQL database?",
            target_concepts=[
                "OOP language",
                "Python",
                "My SQL",
                "Relational database",
                "data science libraries",
            ],
            difficulty="Easy",
            answer="I would use a Python library like SQLAlchemy to create a database engine and then use the Pandas 'read_sql' function. This function can execute a SQL query and directly load the results into a structured Pandas DataFrame, which is ideal for subsequent analysis.",
        ),
        QuestionItem(
            id=11,
            question="The role involves building ML infrastructure and requires Unix/Linux basics. How could you use a simple Unix/Linux shell script to automate a recurring machine learning task, like retraining a model?",
            target_concepts=["ML infrastructure", "Unix/Linux", "Machine Learning"],
            difficulty="Medium",
            answer="A shell script can automate this by chaining commands. It could first run a Python script to pull new data, then another for data preprocessing, followed by a script to train the model, and finally, one to save the new model artifact. This entire workflow can be scheduled to run periodically using a cron job.",
        ),
        QuestionItem(
            id=12,
            question="The job requires hands-on experience with LLMs, RAGs, and deep learning. Explain how a RAG architecture fundamentally differs from fine-tuning a deep learning model like a standard LLM for a knowledge-specific task.",
            target_concepts=[
                "LLMs",
                "RAGs",
                "deep learning",
                "Natural Language Processing (NLP)",
            ],
            difficulty="Hard",
            answer="Fine-tuning updates the actual weights of the LLM to bake in new knowledge, which is computationally expensive and static once completed. RAG, on the other hand, keeps the core LLM frozen and augments its knowledge at inference time by retrieving relevant information from an external, easily updatable database, making it better for handling rapidly changing information.",
        ),
    ]

    mixed_questions = [
        QuestionItem(
            id=13,
            question="You have experience with Git and certifications in Node.js and Express. What is the purpose of a '.gitignore' file in a project, and what kind of files would you typically include in it for a Node.js application?",
            target_concepts=["Git", "Version Control", "Node.js", "Express"],
            difficulty="Easy",
            answer="A '.gitignore' file tells Git which files or directories to ignore and not track. In a Node.js project, you would typically ignore the 'node_modules' directory, log files, environment variable files like '.env', and build outputs to keep the repository clean and lightweight.",
        ),
        QuestionItem(
            id=14,
            question="Your resume shows experience with both SQL and NoSQL (MongoDB). For an application requiring data annotation for NLP research, as you've done, would you choose MongoDB or MySQL, and why?",
            target_concepts=["MongoDB", "data annotation", "My SQL"],
            difficulty="Medium",
            answer="I would choose MongoDB. NLP data can be semi-structured or have evolving schemas, such as text with varying metadata or annotation formats. MongoDB's flexible, document-based structure is ideal for handling this variability, whereas the rigid schema of a SQL database would be more difficult to adapt.",
        ),
        QuestionItem(
            id=15,
            question="The job mentions Computer Vision (CV), and your resume details creating geo plots and spatial mapping. How could you combine CV techniques with spatial mapping to analyze agricultural production, as you did in your livestock project?",
            target_concepts=[
                "CV",
                "geo plots",
                "spatial mapping",
                "Artificial Intelligence (AI)",
            ],
            difficulty="Hard",
            answer="You could use Computer Vision models to analyze satellite or drone imagery of agricultural land to identify crop types, assess plant health, or count livestock. The outputs of this analysis could then be plotted on a map using spatial mapping techniques to visualize regional production patterns and identify areas needing intervention.",
        ),
    ]

    # -----------------------------
    # Create Interview Schema Instance
    # -----------------------------
    interview_questions = InterviewQuestionsSchema(
        resume_questions=resume_questions,
        jd_questions=jd_questions,
        mixed_questions=mixed_questions,
    )

    status = True
    eval_agent = EvaluationAgent()

    all_question = interview_questions
    new_ordered_qn = []
    eval_list = []

    for question_list_name in [
        "resume_questions",
        "jd_questions",
        "mixed_questions",
    ]:
        question_list = getattr(interview_questions, question_list_name)
        for question_item in question_list:
            print(f"ID: {question_item.id}, Question: {question_item.question}")
            ans = input("Enter Answer ")
            question_item.answer = ans
            new_ordered_qn.append(question_item)

            eval, followupQuestion = eval_agent.run(
                user_answer=question_item, jd=jd, session_id="session"
            )
            print("History \n")
            llm.print_history("session")
            eval_list.append(eval)
            while followupQuestion:
                new_ordered_qn.append(followupQuestion)
                print(
                    f"ID: {followupQuestion.id}, Question: {followupQuestion.question}"
                )
                ans = input("Enter Answer ")
                followupQuestion.answer = ans
                followup_eval, followupQuestion = eval_agent.run(
                    user_answer=followupQuestion, jd=jd, session_id="session"
                )
                eval_list.append(followup_eval)
                print("History \n")

                llm.print_history("session")

    print(new_ordered_qn)
    print(eval_list)


if __name__ == "__main__":
    main()
