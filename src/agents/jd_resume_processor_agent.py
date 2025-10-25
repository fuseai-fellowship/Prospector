from langchain_core.runnables import RunnableLambda, RunnableSequence
from ..tools.stur_resume_extractor import SturResumeExtractor
from ..tools.question_answer_generator import QuestionGenerator
from ..tools.jd_processor_tool import JdProcessor
from ..utils.resume_parser import text_extractor
from ..schemas.interview_questions_schema import InterviewQuestionsSchema
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
        questions = self.question_generator.generateInterviewQn(
            resume_json=resume_json, job_description=jd_json, no_of_qn=no_of_qn
        )
        return questions
