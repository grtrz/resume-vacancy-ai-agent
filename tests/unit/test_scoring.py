from app.services.matching.scoring import skill_overlap_score


def test_skill_overlap_score_matches_case_insensitively() -> None:
    score = skill_overlap_score(["Python", "FastAPI"], ["python", "sql"])

    assert score == 0.5


def test_skill_overlap_score_handles_empty_requirements() -> None:
    assert skill_overlap_score(["python"], []) == 0.0
