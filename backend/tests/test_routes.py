import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_healthz():
    with TestClient(app) as client:
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

def test_upload_missing_file():
    with TestClient(app) as client:
        response = client.post("/api/upload")
        assert response.status_code == 422

def test_forecast_missing_body():
    with TestClient(app) as client:
        response = client.post("/api/forecast")
        assert response.status_code == 422
        
def test_scenario_default():
    with TestClient(app) as client:
        response = client.get("/api/scenario")
        assert response.status_code == 200
        data = response.json()
        assert "windows" in data
        assert "raw_packets" in data
def test_mitre_missing_body():
    with TestClient(app) as client:
        response = client.post("/api/mitre")
        assert response.status_code == 422

def test_xai_missing_body():
    with TestClient(app) as client:
        response = client.post("/api/xai")
        assert response.status_code == 422

def test_soc_missing_body():
    with TestClient(app) as client:
        response = client.post("/api/soc")
        assert response.status_code == 422

def test_benchmark_missing_body():
    with TestClient(app) as client:
        response = client.post("/api/benchmark")
        assert response.status_code == 422

def test_report_missing_body():
    with TestClient(app) as client:
        response = client.post("/api/report")
        assert response.status_code == 422
