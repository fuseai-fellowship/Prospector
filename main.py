from pathlib import Path

from src.agents.jd_resume_processor_agent import JdResumeProcessorAgent
from src.utils.llm_client import LLMClient
from configs.config import settings
from src.tools.question_generator import QuestionGenerator


def main():
    resume_path = Path("data/resume_data/SandeshShrestha_CV.pdf")
    agent = JdResumeProcessorAgent(resume_path=resume_path)
    result = agent.process_resume()

    qn_gen = QuestionGenerator()
    jd = """
        Job Description (JD)

        Position: Software Engineer I, Machine Learning
        Company: Smart Data Solutions (SDS)

        Responsibilities:

        Build, deploy, maintain, troubleshoot, and improve machine learning models.

        Design and implement new applications leveraging ML and related technologies.

        Develop and enhance ML infrastructure.

        Automate and optimize existing processes using ML.

        Investigate and resolve issues with ML processes.

        Perform business analysis and process improvements.

        Prepare process documentation and communicate effectively.

        Other duties as assigned.

        Why Join SDS?

        Authentic, innovative, and collaborative culture.

        Strong focus on professional growth and development.

        Competitive benefits package (insurance, Social Security Fund contribution, PTO, holidays, floating day, etc.).

        Flexible work environment.

        Opportunity to work with healthcare automation and interoperability at scale.

        Job Requirements (JR)

        Education & Experience:

        Bachelor’s degree in Computer Science or equivalent.

        1+ year experience in machine learning, NLP, or deep learning.

        Hands-on experience with LLMs and RAGs.

        Technical Skills:

        Proficiency in at least one modern OOP language (Python, Java, C#, C++).

        Knowledge of ML, NLP, CV, and data science libraries.

        Relational database basics (MySQL).

        Unix/Linux basics.

        Experience with Git/version control.

        Strong skills in Microsoft Excel, Word, and Windows.

        Soft Skills & Attributes:

        Highly organized, disciplined, and responsive communicator.

        Strong analytical, problem-solving, and process improvement mindset.

        Effective writing/documentation skills.

        Ability to meet deadlines and consistently complete tasks.

        Communication style focused on clarity, simplicity, and actionable insights.
        """

    questions = qn_gen.generateInterviewQuestion(resume_json=result, job_description=jd)
    print(questions)


if __name__ == "__main__":
    main()
