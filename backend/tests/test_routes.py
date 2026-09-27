import pytest
import io
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

def test_scenario_preflight_from_loopback_origin():
    with TestClient(app) as client:
        response = client.options(
            "/api/scenario?name=APT+Multi-Stage+Campaign&num_windows=20&window_size_sec=10.0",
            headers={
                "Origin": "http://127.0.0.1:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"

        fallback_port_response = client.options(
            "/api/scenario",
            headers={
                "Origin": "http://localhost:3001",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert fallback_port_response.status_code == 200
        assert fallback_port_response.headers["access-control-allow-origin"] == "http://localhost:3001"

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


# ── Error Handling Tests ──

def test_forecast_empty_windows_returns_valid():
    """Forecast with empty windows should return empty results, not crash."""
    with TestClient(app) as client:
        response = client.post("/api/forecast", json={"windows": [], "K": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["forecast_df"] == []
        assert data["risk_trajectory"] == []

def test_forecast_malformed_windows_returns_error():
    """Forecast with malformed window data should return 422 or 500, not raw traceback."""
    with TestClient(app) as client:
        response = client.post("/api/forecast", json={
            "windows": [{"bad_key": "bad_value"}],
            "K": 3
        })
        assert response.status_code in (422, 500)
        data = response.json()
        assert "detail" in data

def test_upload_unsupported_file_type():
    """Upload a .txt file should return 422 with helpful message."""
    with TestClient(app) as client:
        fake_file = io.BytesIO(b"not a csv or pcap file")
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", fake_file, "text/plain")}
        )
        assert response.status_code == 422
        assert "Unsupported file type" in response.json()["detail"]

def test_benchmark_insufficient_windows():
    """Benchmark with fewer windows than K should return zero metrics."""
    with TestClient(app) as client:
        response = client.post("/api/benchmark", json={
            "windows": [{"window_id": 0}],
            "risk_trajectory": [0.5, 0.6],
            "K": 5,
            "threshold": 0.5
        })
        assert response.status_code == 200
        data = response.json()
        assert data["gain_f1_pct"] == 0.0

def test_parser_unknown_labels_no_crash():
    """Parser should handle unknown attack labels gracefully (default risk, no crash)."""
    from backend.src.parser import TrafficParser
    import pandas as pd

    parser = TrafficParser(window_size_sec=10.0)
    data = pd.DataFrame([{
        'timestamp': '2023-01-01 00:00:01', 'src_ip': '1.1.1.1', 'dst_ip': '2.2.2.2',
        'src_port': 80, 'dst_port': 443, 'protocol': 6,
        'syn_flag': 1, 'ack_flag': 0, 'fin_flag': 0, 'rst_flag': 0, 'psh_flag': 0, 'urg_flag': 0,
        'flow_duration': 0.1, 'tot_bytes': 1000, 'tot_pkts': 2,
        'flow_iat_mean': 0.05, 'flow_iat_std': 0.01, 'flow_iat_max': 0.08,
        'ttl': 64, 'tcp_win': 1024, 'ip_frag': 0, 'payload_bytes': 500, 'retrans_count': 0,
        'label': 'FTP-Patator'  # Unknown label — previously would crash
    }])
    df_parsed = parser.parse_csv(data)
    df_win = parser.create_time_windows(df_parsed)

    assert not df_win.empty, "Parser should not crash on unknown labels."
    assert df_win.iloc[0]['target_risk_score'] == 0.5, "Unknown labels should default to 0.5 risk."

