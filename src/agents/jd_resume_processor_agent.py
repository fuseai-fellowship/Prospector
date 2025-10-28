from langchain_core.runnables import RunnableLambda, RunnableSequence
from ..tools.stur_resume_extractor import SturResumeExtractor
from ..tools.question_answer_generator import QuestionGenerator
from ..tools.jd_processor_tool import JdProcessor
from ..utils.resume_parser import text_extractor
from ..schemas.interview_questions_schema import InterviewQuestionsSchema, QuestionItem
from ..schemas.job_description_schema import JobDescription
from ..schemas.resume_schema import ResumeSchema


class ResumeProcessorAgent:
    def __init__(self, model: str = None, temperature: int = None) -> None:
        self.extractor = SturResumeExtractor(model=model, temperature=temperature)
        self.question_generator = QuestionGenerator(
            model=model, temperature=temperature
        )

        self.pipeline = RunnableSequence(
            RunnableLambda(self._get_text_resume),
            RunnableLambda(self._extract_resume_data),
        )

    def run_extraction_pipline(self, resume_file: str) -> ResumeSchema:
        """
        Executes the full processing pipeline.
        """
        result = self.pipeline.invoke(resume_file)
        return result

    def _get_text_resume(self, resume_file) -> str:
        parsed_text = text_extractor(resume_file)
        return parsed_text

    def _extract_resume_data(self, parsed_text) -> ResumeSchema:
        extracted_data = self.extractor.extract(parsed_text)
        return extracted_data

    def generate_questions(
        self, resume_json: str, jd_json: str, no_of_qn: int = 9
    ) -> InterviewQuestionsSchema:
        # questions = self.question_generator.generateInterviewQn(
        #     resume_json=resume_json, job_description=jd_json, no_of_qn=no_of_qn
        # )
        # return questions

        # 1. Create 3 sample resume questions
        resume_qns = [
            QuestionItem(
                id=1,
                question="Can you tell me about your project [Project Name from Resume]?",
                target_concepts=["Past Experience", "Communication"],
                difficulty="Easy",
            ),
            QuestionItem(
                id=2,
                question="I see you used [Skill from Resume, e.g., 'Python'] at [Company from Resume]. What was a major challenge you faced there?",
                target_concepts=["Python", "Problem-Solving", "Technical Deep-Dive"],
                difficulty="Medium",
            ),
            QuestionItem(
                id=3,
                question="How did your role as [Previous Role from Resume] prepare you for this position?",
                target_concepts=["Role Fit", "Self-Awareness"],
                difficulty="Medium",
            ),
        ]

        # 2. Create 3 sample JD questions
        jd_qns = [
            QuestionItem(
                id=4,
                question="This role requires experience with [JD Skill, e.g., 'AWS']. What's your experience with it?",
                target_concepts=["AWS", "Technical Skill", "JD Fit"],
                difficulty="Medium",
            ),
            QuestionItem(
                id=5,
                question="How do you align with our company value of [Company Value from JD]?",
                target_concepts=["Culture Fit", "Behavioral"],
                difficulty="Easy",
            ),
            QuestionItem(
                id=6,
                question="Describe how you would handle [JD Responsibility, e.g., 'managing stakeholders'].",
                target_concepts=["Stakeholder Management", "Process", "Behavioral"],
                difficulty="Hard",
            ),
        ]

        # 3. Create 3 sample mixed questions
        mixed_qns = [
            QuestionItem(
                id=7,
                question="How would you apply your experience with [Resume Skill, e.g., 'FastAPI'] to our need for [JD Need, e.g., 'building scalable microservices']?",
                target_concepts=["FastAPI", "Scalability", "Application", "Role Fit"],
                difficulty="Hard",
            ),
            QuestionItem(
                id=8,
                question="Your resume shows [Resume Strength, e.g., 'data analysis']. How would you use that to improve our [JD Goal, e.g., 'customer reporting']?",
                target_concepts=["Data Analysis", "Reporting", "Proactive Thinking"],
                difficulty="Medium",
            ),
            QuestionItem(
                id=9,
                question="This job involves [JD Duty]. I see from your resume you've [Resume Experience]. Can you connect those two for me?",
                target_concepts=["Connecting Experience", "Role Fit"],
                difficulty="Medium",
            ),
        ]

        # 4. Create and return the InterviewQuestionsSchema instance
        return InterviewQuestionsSchema(
            resume_questions=resume_qns, jd_questions=jd_qns, mixed_questions=mixed_qns
        )
