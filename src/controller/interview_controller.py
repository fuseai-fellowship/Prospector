from ..agents.jd_resume_processor_agent import JdResumeProcessorAgent
from ..agents.evaluation_agent import EvaluationAgent
from ..tools.question_answer_generator import QuestionGenerator


class InterviewController:
    def __init__(self, resume_paths: list[str], jd: str):
        self.jd = jd
        self.resume_paths = resume_paths

    def process_resume_jd(self):
        resume_processor = JdResumeProcessorAgent()
        question_generator = QuestionGenerator()

        resume_texts = []
        questions = []

        for path in self.resume_paths:
            resume_text = resume_processor.run(resume_path=path, jd_path=self.jd)
            resume_texts.append(resume_text)

        for text in resume_texts:
            question = question_generator.generateInterviewQn(
                resume_json=text, job_description=self.jd
            )

            questions.append(question)

        return resume_texts, questions
