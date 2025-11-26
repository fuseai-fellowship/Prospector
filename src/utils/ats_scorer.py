import spacy
from sentence_transformers import SentenceTransformer, util


nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer("all-MiniLM-L6-v2")


def preprocess(text):
    return [
        token.text.lower() for token in nlp(text) if token.pos_ in ["NOUN", "PROPN"]
    ]


def ats_score(resume_words, job_words, threshold=0.7):
    # Exact match
    matched = [kw for kw in job_words if kw in resume_words]
    remaining_job_words = [kw for kw in job_words if kw not in matched]

    # Semantic match
    if remaining_job_words and resume_words:
        resume_embeds = model.encode(resume_words, convert_to_tensor=True)
        job_embeds = model.encode(remaining_job_words, convert_to_tensor=True)
        sim_matrix = util.cos_sim(resume_embeds, job_embeds)
        for i, kw in enumerate(remaining_job_words):
            if any(sim_matrix[:, i] >= threshold):
                matched.append(kw)

    missing = [kw for kw in job_words if kw not in matched]
    score = (len(matched) / len(job_words) * 100) if job_words else 0
    return round(score, 2), matched, missing
