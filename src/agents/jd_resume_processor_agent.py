from langchain_core.runnables import RunnableSequence
from ..tools.stur_resume_extractor import SturResumeExtractor
from ..utils.parse_resume import parse_resume


class JdResumeProcessorAgent:
    def __init__(self, resume_path: str, job_description: str = None):
        self.resume_path = resume_path
        self.extractor = SturResumeExtractor()

        if job_description:
            # Pass steps as separate arguments
            self.pipeline = RunnableSequence(
                self._get_text_resume,
                self._extract_resume_data,
                self.process_jd,
            )
        else:
            self.pipeline = RunnableSequence(
                self._get_text_resume,
                self._extract_resume_data,
                self.process_jd,
            )

    def _get_text_resume(self, _input=None) -> str:
        return parse_resume(self.resume_path)

    def _extract_resume_data(self, resume_text: str):
        return self.extractor.extract(resume_text)

    def process_resume(self) -> dict:
        result = self.pipeline.invoke(self.resume_path)
        return {"resume_data": result}

    def process_jd(self) -> str:
        processed_jd = "Something"
        return processed_jd
