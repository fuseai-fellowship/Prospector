from langchain_core.runnables import RunnableLambda, RunnableSequence
from ..tools.stur_resume_extractor import SturResumeExtractor
from ..tools.question_generator import QuestionGenerator
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
        resume_questions = [
            {
                "id": 1,
                "question": "Can you describe the AI project where you implemented a transformer-based NLP model and your role in it?",
                "target_concepts": ["Transformers", "NLP", "Project Experience"],
                "difficulty": "Easy",
                "answer": "Explain the project goal, dataset, model architecture, and your specific contributions.",
            },
            {
                "id": 2,
                "question": "I see you used PyTorch for model training. What was the most challenging optimization or debugging issue you faced?",
                "target_concepts": ["PyTorch", "Optimization", "Debugging"],
                "difficulty": "Medium",
                "answer": "Describe a specific problem with model convergence, gradient issues, or training performance and how you resolved it.",
            },
            {
                "id": 3,
                "question": "How did your experience as a Machine Learning Engineer at [Previous Company] prepare you for production-level AI deployment?",
                "target_concepts": [
                    "Machine Learning",
                    "Production Deployment",
                    "Role Fit",
                ],
                "difficulty": "Medium",
                "answer": "Highlight experience with model deployment, monitoring, and scaling in real-world applications.",
            },
        ]

        jd_questions = [
            {
                "id": 4,
                "question": "This role requires experience with cloud platforms like AWS or GCP. Can you explain a scenario where you deployed an AI model on cloud infrastructure?",
                "target_concepts": [
                    "Cloud Deployment",
                    "AWS",
                    "GCP",
                    "Technical Skill",
                ],
                "difficulty": "Medium",
                "answer": "Describe the cloud setup, services used (EC2, S3, Lambda, etc.), and deployment process.",
            },
            {
                "id": 5,
                "question": "Our company values collaboration and code quality. Can you give an example of how you maintained high-quality ML code in a team project?",
                "target_concepts": ["Collaboration", "Code Quality", "Behavioral"],
                "difficulty": "Easy",
                "answer": "Explain code review processes, unit tests, CI/CD pipelines, and teamwork practices.",
            },
            {
                "id": 6,
                "question": "You may need to manage multiple AI projects simultaneously. How would you prioritize tasks and ensure stakeholder alignment?",
                "target_concepts": [
                    "Project Management",
                    "Stakeholder Communication",
                    "Prioritization",
                ],
                "difficulty": "Hard",
                "answer": "Discuss task triaging, setting milestones, communicating progress, and using tools like Jira or Trello.",
            },
        ]

        mixed_questions = [
            {
                "id": 7,
                "question": "How would you apply your experience with PyTorch and transformers to our need for a scalable NLP pipeline for customer feedback analysis?",
                "target_concepts": ["PyTorch", "Transformers", "NLP", "Scalability"],
                "difficulty": "Hard",
                "answer": "Explain preprocessing, model training, deployment strategies, and performance optimization for large-scale inference.",
            },
            {
                "id": 8,
                "question": "Your resume highlights expertise in computer vision. How would you leverage that to enhance our image-based anomaly detection system?",
                "target_concepts": [
                    "Computer Vision",
                    "Anomaly Detection",
                    "Deep Learning",
                ],
                "difficulty": "Medium",
                "answer": "Discuss model architectures, dataset considerations, and potential improvements in accuracy and speed.",
            },
            {
                "id": 9,
                "question": "This role requires experience in end-to-end ML pipelines. You mentioned working on a recommendation system before. How do your previous experiences translate to building robust pipelines here?",
                "target_concepts": [
                    "ML Pipelines",
                    "Recommendation Systems",
                    "Role Fit",
                ],
                "difficulty": "Medium",
                "answer": "Connect past work on preprocessing, feature engineering, model training, evaluation, and deployment to the current role requirements.",
            },
        ]

        # 4. Create and return the InterviewQuestionsSchema instance
        return InterviewQuestionsSchema(
            resume_questions=resume_questions,
            jd_questions=jd_questions,
            mixed_questions=mixed_questions,
        )
