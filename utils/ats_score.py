import re

def calculate_ats_score(resume_text, job_description):

    resume_text = resume_text.lower()
    job_description = job_description.lower()

    words = set(re.findall(r"\w+", job_description))

    matched = []

    missing = []

    for word in words:

        if len(word) < 3:
            continue

        if word in resume_text:
            matched.append(word)
        else:
            missing.append(word)

    score = int((len(matched) / len(words)) * 100) if words else 0

    return score, matched, missing