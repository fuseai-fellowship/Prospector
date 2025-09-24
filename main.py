from pathlib import Path
from src.agents.resume_processor_agent import ResumeProcessorAgent


def main():
    resume_path = Path("data/resume_data/SandeshShrestha_CV.pdf")
    agent = ResumeProcessorAgent(resume_path=resume_path)
    result = agent.process()
    print(result)


if __name__ == "__main__":
    main()
