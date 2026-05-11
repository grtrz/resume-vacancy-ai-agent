import re

SKILL_ALIASES = {
    "amazon web services": "aws",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "docker compose": "docker",
    "js": "javascript",
    "k8s": "kubernetes",
    "node": "node.js",
    "node js": "node.js",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "react js": "react",
    "reactjs": "react",
    "rest": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "torch": "pytorch",
    "ts": "typescript",
}


def normalize_token(value: str) -> str:
    return " ".join(value.strip().lower().split())


def fold_for_matching(value: str) -> str:
    folded = value.replace("&", " and ")
    folded = re.sub(r"(?i)ci\s*/\s*cd", "ci cd", folded)
    folded = re.sub(r"(?i)node\.js", "node js", folded)
    folded = re.sub(r"(?i)react\.js", "react js", folded)
    folded = re.sub(r"[^\w+#]+", " ", folded.lower())
    return normalize_token(folded)


def normalize_skill(value: str) -> str:
    folded = fold_for_matching(value)
    return SKILL_ALIASES.get(folded, folded)
