from configs.config import settings
from src.utils.resume_extractor import parse_resume


def main():
    print("Helo")

    parse_resume(r"data\resume_data\SandeshShrestha_CV.pdf")


if __name__ == "__main__":
    main()
