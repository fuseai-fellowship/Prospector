from ..utils.llm_client import LLMClient
from configs.config import logger
from ..schemas.job_description_schema import JobDescription


class JdProcessor:
    def __init__(self, model: str = None, temperature: str = None):
        self.llm = LLMClient(model=model, temperature=temperature)

    def process_jd(self, jd_text):
        prompt = f"""
                    You are an expert job description generator.

                    Given the following job description text, analyze it carefully and generate a well-structured summary including:
                    1. **Title** — A concise, professional job title.
                    2. **Requirements** — A clear, bullet-point list of required skills, experience, and competencies.
                    3. **Responsibilities** — A detailed list of key roles and daily duties.
                    4. **Qualifications** — Educational background, certifications, or other necessary qualifications.

                    Specify tools, technology they need to use. 

                    Ensure the output is clear, formatted in JSON, and uses consistent key names: 
                    "title", "requirements", "responsibilities", and "qualifications".

                    Job Description:
                    {jd_text}
                """
        try:
            logger.info("Processing the provided Job Description")

            response = self.llm.get_structured_response(
                prompt=prompt, schema=JobDescription
            )

            logger.info(
                f"✅ Job description processing completed for : {response.title}"
            )
            return response
        except Exception as e:
            logger.critical(f"❌ Error processing job description: {e}")
            raise
