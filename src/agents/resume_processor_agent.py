from langchain_core.runnables import RunnableSequence
from ..tools.stur_resume_extractor import SturResumeExtractor
from ..utils.parse_resume import parse_resume


class ResumeProcessorAgent:
    def __init__(self, resume_path: str = None):
        self.resume_path = resume_path
        self.extractor = SturResumeExtractor()

        # Pass steps as separate arguments
        self.pipeline = RunnableSequence(
            self._get_text_resume, self._extract_resume_data
        )

    def _get_text_resume(self, _input=None) -> str:
        return parse_resume(self.resume_path)

    def _extract_resume_data(self, resume_text: str):
        return self.extractor.extract(resume_text)

    def process(self) -> dict:
        result = self.pipeline.invoke(self.resume_path)
        return {"resume_data": result}
