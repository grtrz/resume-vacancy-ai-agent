def skill_overlap_score(resume_skills: list[str], required_skills: list[str]) -> float:
    if not required_skills:
        return 0.0
    resume_set = {skill.lower() for skill in resume_skills}
    required_set = {skill.lower() for skill in required_skills}
    return len(resume_set & required_set) / len(required_set)
