# Agent instructions

- Use Python 3.11+.
- Keep modules small and typed.
- Prefer FastAPI dependencies for services.
- Use Pydantic v2.
- Use pytest for tests.
- Run ruff and tests after changes.
- Do not introduce LangChain unless explicitly needed.
- LangGraph is allowed only for workflow orchestration.
- Do not add paid API calls in tests.
- Do not commit secrets or local files.