import re

SKILL_ALIASES = {
    "air flow": "airflow",
    "amazon web services": "aws",
    "apache airflow": "airflow",
    "apache kafka": "kafka",
    "apache spark": "spark",
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous integration continuous delivery": "ci/cd",
    "continuous integration continuous deployment": "ci/cd",
    "docker compose": "docker",
    "faiss": "faiss",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "huggingface": "hugging face",
    "hf": "hugging face",
    "js": "javascript",
    "k8s": "kubernetes",
    "large language model": "llm",
    "large language models": "llm",
    "llms": "llm",
    "machine learning engineering": "ml engineering",
    "ml engineer": "ml engineering",
    "ml engineering": "ml engineering",
    "mlops": "mlops",
    "node": "node.js",
    "node js": "node.js",
    "nodejs": "node.js",
    "postgres sql": "postgresql",
    "postgres": "postgresql",
    "postgre sql": "postgresql",
    "qdrant": "qdrant",
    "react js": "react",
    "reactjs": "react",
    "retrieval augmented generation": "rag",
    "rest": "rest api",
    "restful api": "rest api",
    "restful apis": "rest api",
    "scikit learn": "scikit-learn",
    "sentence transformers": "sentence-transformers",
    "sbert": "sentence-transformers",
    "sklearn": "scikit-learn",
    "torch": "pytorch",
    "transformers": "hugging face transformers",
    "ts": "typescript",
    "vector database": "vector databases",
    "vector db": "vector databases",
    "vector search": "vector databases",
}


def normalize_token(value: str) -> str:
    return " ".join(value.strip().lower().split())


def fold_for_matching(value: str) -> str:
    folded = value.replace("&", " and ")
    folded = re.sub(r"(?i)ci\s*/\s*cd", "ci cd", folded)
    folded = re.sub(r"(?i)node\.js", "node js", folded)
    folded = re.sub(r"(?i)react\.js", "react js", folded)
    folded = re.sub(r"(?i)scikit-learn", "scikit learn", folded)
    folded = re.sub(r"(?i)sentence-transformers", "sentence transformers", folded)
    folded = re.sub(r"[^\w+#]+", " ", folded.lower())
    return normalize_token(folded)


def normalize_skill(value: str) -> str:
    folded = fold_for_matching(value)
    return SKILL_ALIASES.get(folded, folded)
