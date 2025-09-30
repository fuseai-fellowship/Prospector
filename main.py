from pathlib import Path

# from agents.jd_resume_processor_agent import JdResumeProcessorAgent
from src.utils.llm_client import LLMClient
from configs.config import settings


def main():
    # resume_path = Path("data/resume_data/SandeshShrestha_CV.pdf")
    # agent = JdResumeProcessorAgent(resume_path=resume_path)
    # result = agent.process_resume()
    # print(result)

    print(settings)
    print(
        "normal_model from settings:",
        settings.get("normal_model", settings.get("NORMAL_MODEL", None)),
    )

    # llm_client = LLMClient()
    # result = llm_client.ask("Hello who are yous")

    # llm_client2 = LLMClient()
    # result2 = llm_client2.ask("Hello who are yous")

    # print(result)
    # print(result2)


if __name__ == "__main__":
    main()
