from fastapi.testclient import TestClient

from app.main import app


def test_incident_stream_endpoint_emits_sse() -> None:
    client = TestClient(app)

    with client.stream("GET", "/incidents/stream") as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        first_lines = []
        for line in response.iter_lines():
            if line:
                first_lines.append(line)
            if len(first_lines) >= 1:
                break

    assert first_lines
