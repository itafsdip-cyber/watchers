from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_incident_filters_do_not_error() -> None:
    response = client.get("/incidents?min_score=0.5")
    assert response.status_code == 200

    response = client.get("/incidents?status=credible")
    assert response.status_code == 200
