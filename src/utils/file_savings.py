import os
import json
from datetime import datetime
from configs.config import settings, logger
from ..schemas.resume_schema import ResumeSchema


def save_processed_json_resume(
    json_text: str | ResumeSchema, file_name: str | None = None
) -> str:
    """
    Save processed JSON resume to the configured path.
    Accepts either a ResumeSchema object or a JSON string.
    Returns the relative path to the saved JSON file.
    """
    # Get output directory
    output_dir = settings.get("processed_json_resumes_path")
    if not output_dir:
        raise ValueError("'processed_json_resumes_path' not found in settings.")
    os.makedirs(output_dir, exist_ok=True)

    # Handle JSON or ResumeSchema
    if isinstance(json_text, ResumeSchema):
        resume_data = json_text.dict()
    elif isinstance(json_text, str):
        try:
            resume_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON format: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
    else:
        raise TypeError("json_text must be a JSON string or ResumeSchema instance.")

    # Sanitize filename
    if not file_name:
        file_name = f"resume_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        # Strip directory parts
        file_name = os.path.basename(file_name)
        # Remove illegal characters
        file_name = "".join(c for c in file_name if c not in r'\/:*?"<>|')

    # Construct final relative path
    file_path = os.path.join(output_dir, f"{file_name}.json")
    file_path = file_path.replace("\\", "/")

    # Save JSON
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(resume_data, f, ensure_ascii=False, indent=4)

    logger.info(f"Resume JSON saved to: {file_path}")
    return file_path


def save_interview_result(json_text: str, file_name: str | None = None) -> str:
    """
    Save interview result to the configured path.
    Accepts either a JSON string or plain text input.
    Returns the relative path to the saved file.
    """

    # Get output directory from settings
    output_dir = settings.get("interview_result")
    if not output_dir:
        raise ValueError("'interview_result' path not found in settings.")
    os.makedirs(output_dir, exist_ok=True)

    # Determine if content is JSON or plain text
    try:
        result_data = json.loads(json_text)
        is_json = True
    except json.JSONDecodeError:
        result_data = json_text
        is_json = False

    # Sanitize filename
    if not file_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"interview_result_{timestamp}"
    else:
        file_name = os.path.basename(file_name)
        file_name = "".join(c for c in file_name if c not in r'\/:*?"<>|')

    # Determine extension
    extension = "json" if is_json else "txt"
    file_path = os.path.join(output_dir, f"{file_name}.{extension}")
    file_path = file_path.replace("\\", "/")

    # Save file
    with open(file_path, "w", encoding="utf-8") as f:
        if is_json:
            json.dump(result_data, f, ensure_ascii=False, indent=4)
        else:
            f.write(result_data)

    logger.info(f"Interview result saved to: {file_path}")
    return file_path
