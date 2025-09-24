import pdfplumber
import docx2txt
import os


class ResumeExtractor:
    def __init__(self):
        pass

    def _parse_resume(self, file_path: str = None) -> str:
        """Extract text from a PDF or DOCX file."""
        if not file_path:
            raise ValueError("Please provide a file path")

        ext = os.path.splitext(file_path)[1].lower()
        text = ""

        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""

        elif ext == ".docx":
            text = docx2txt.process(file_path)

        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return text.strip()

    def get_structured_json(self, text: str = None) -> dict:
        """Convert raw text into a structured JSON (stub for now)."""
        if not text:
            return {}

        # TODO: Add parsing logic for name, email, phone, skills, etc.
        return {"raw_text": text}
