import json

from ..agents.jd_resume_processor_agent import ResumeProcessorAgent


class JdController:
    def __init__(self):
        pass

    def process_jd(self, jd_text: str):
        word_count = len(jd_text.split())
        char_count = len(jd_text)
        processed_jd = jd_text

        return word_count, char_count, processed_jd


class InterviewController:
    def __init__(self):
        self.resume_processor = ResumeProcessorAgent()

    def process_resume(self, resume_path: str, jd_path: str):
        f = open(resume_path, "r", encoding="utf-8")
        resume_text = json.load(f)
        f.close()

        f = open(jd_path, "r", encoding="utf-8")
        jd_text = json.load(f)
        f.close()

        interview_questions = self.resume_processor.run_extraction_pipline(
            resume_text == resume_text, jd_text == jd_text
        )

        return interview_questions
