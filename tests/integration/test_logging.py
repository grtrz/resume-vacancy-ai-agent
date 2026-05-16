import logging

from fastapi.testclient import TestClient

from app.main import app


def test_request_logging_middleware_logs_request_metadata(caplog) -> None:
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="app.api.middleware"):
        response = client.get("/health")

    assert response.status_code == 200
    records = [
        record
        for record in caplog.records
        if record.name == "app.api.middleware" and record.getMessage() == "request_completed"
    ]
    assert records

    record = records[-1]
    assert record.method == "GET"
    assert record.path == "/health"
    assert record.status_code == 200
    assert record.duration_ms >= 0
