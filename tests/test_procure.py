from datetime import date

from fastapi.testclient import TestClient

from backend.db import init_db, seed_db
from backend.main import app


client = TestClient(app)


def setup_module() -> None:
    init_db()
    seed_db()


def test_list_vendors():
    resp = client.get("/vendors")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3


def test_procure_split_order():
    payload = {
        "strain": "C57BL/6J",
        "quantity": 60,
        "experiment_start_date": date.today().isoformat(),
        "approved_quota": 100,
    }
    resp = client.post("/procure", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["allocation"]) >= 2
    assert sum(a["quantity"] for a in data["allocation"]) == 60


def test_history_records():
    resp = client.get("/history")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
