def normalize_token(value: str) -> str:
    return " ".join(value.strip().lower().split())
