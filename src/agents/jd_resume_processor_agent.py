from langchain_core.runnables import RunnableSequence
from ..tools.stur_resume_extractor import SturResumeExtractor
from ..utils.resume_parser import parse_resume


class JdResumeProcessorAgent:
    def __init__(
        self, job_description: str = None, model: str = None, temperature: int = None
    ):
        self.extractor = SturResumeExtractor(model=model, temperature=temperature)

        if job_description:
            # Pass steps as separate arguments
            self.pipeline = RunnableSequence(
                self._get_text_resume,
                self._extract_resume_data,
                self._process_jd,
            )
        else:
            self.pipeline = RunnableSequence(
                self._get_text_resume,
                self._extract_resume_data,
            )

    def run(self, resume_path: str) -> dict:
        """
        Executes the full processing pipeline on the given resume path.
        Returns structured results for resume and optionally job description.
        """
        result = self.pipeline.invoke(resume_path)
        return {"resume_data": result}

    def _get_text_resume(self, resume_path: str) -> str:
        """Parse the resume file into text."""
        return parse_resume(resume_path)

    def _extract_resume_data(self, resume_text: str) -> dict:
        """Extract structured resume data using the extractor."""
        return self.extractor.extract(resume_text)

    def _process_jd(self) -> str:
        processed_jd = "Something"
        return processed_jd
