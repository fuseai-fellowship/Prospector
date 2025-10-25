import pdfplumber
import docx2txt
import os
from configs.config import logger, settings


def text_extractor(file_path: str = None) -> str:
    """Extract text from a PDF or DOCX file."""
    file_path = f"{settings.get('all_resumes_path')}/{file_path}"
    print(file_path)

    if not file_path or not os.path.exists(file_path):
        raise ValueError(f"Resume file not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        if ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
        elif ext == ".docx":
            text = docx2txt.process(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        logger.info("Resume parsed successfully")
        return text.strip()

    except Exception as e:
        logger.exception(f"Error parsing resume: {e}")
        raise  #
