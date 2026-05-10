# Resume Vacancy AI Agent

## Goal
Build a production-like NLP/LLM application for matching resumes with job vacancies and generating grounded CV improvement recommendations.

## Core features
1. Upload and parse PDF/DOCX resumes.
2. Parse job vacancy text.
3. Extract structured entities:
   - hard skills
   - frameworks
   - tools
   - years of experience
   - education
   - responsibilities
   - achievements
4. Compute resume-vacancy match score.
5. Generate gap analysis.
6. Generate improved resume bullet points grounded in the original resume.
7. Use RAG over a small knowledge base of strong resume examples.
8. Add automated evaluation for generated recommendations.

## Tech stack
- Python 3.11+
- FastAPI
- Pydantic v2
- PostgreSQL
- Qdrant
- SQLAlchemy
- Alembic
- sentence-transformers
- optional: OpenAI / local LLM provider abstraction
- LangGraph for workflow orchestration
- Ragas or custom evaluation module
- Docker Compose
- pytest
- ruff
- mypy

## Architecture
src/
  app/
    main.py
    api/
      routes/
        health.py
        resumes.py
        vacancies.py
        reports.py
    core/
      config.py
      logging.py
      exceptions.py
    schemas/
      resume.py
      vacancy.py
      report.py
      extraction.py
    services/
      parsing/
        pdf_parser.py
        docx_parser.py
        text_cleaner.py
      extraction/
        skill_extractor.py
        llm_extractor.py
        normalizer.py
      matching/
        scoring.py
        semantic_matcher.py
        hybrid_ranker.py
      rag/
        embeddings.py
        vector_store.py
        retriever.py
      agents/
        workflow.py
        nodes.py
        state.py
      generation/
        bullet_rewriter.py
        gap_analyzer.py
      evaluation/
        metrics.py
        evaluator.py
    db/
      models.py
      session.py
      migrations/
tests/
  unit/
  integration/
data/
  examples/
  knowledge_base/
docs/
  architecture.md
  api.md

## MVP scope
Implement first:
1. FastAPI app with health endpoint.
2. Resume/vacancy schemas.
3. PDF/DOCX/text parsing.
4. Basic skill extraction.
5. Hybrid scoring.
6. Report endpoint.
7. Tests for parser, extractor, scoring.

## Development rules
- Keep code modular.
- Use type hints everywhere.
- Use Pydantic models for structured outputs.
- Avoid huge files.
- Add tests for every service.
- Do not hardcode secrets.
- Use .env.example.
- Prefer simple working implementation over over-engineered abstractions.