from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

import app_final

client = TestClient(app_final.app)


@pytest.fixture(autouse=True)
def clean_storage(monkeypatch):
    """Перед каждым тестом очищаем данные и настройку, чтобы тесты не влияли друг на друга."""
    app_final.deadlines.clear()
    app_final.counter["next_id"] = 1
    monkeypatch.delenv("WARN_DAYS", raising=False)


def add(title="Лаба 3", subject="Инфраструктура", days_ahead=2):
    due = (date.today() + timedelta(days=days_ahead)).isoformat()
    return client.post(
        "/deadlines",
        json={"title": title, "subject": subject, "due_date": due},
    )


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": app_final.VERSION}


def test_create_and_list():
    created = add()
    assert created.status_code == 201
    response = client.get("/deadlines")
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Лаба 3"


def test_get_missing_returns_404():
    response = client.get("/deadlines/999")
    assert response.status_code == 404


def test_past_date_is_rejected():
    response = add(days_ahead=-1)
    assert response.status_code == 400


def test_upcoming_uses_days_parameter():
    add(title="Скоро", days_ahead=2)
    add(title="Нескоро", days_ahead=20)
    response = client.get("/deadlines/upcoming?days=5")
    titles = [d["title"] for d in response.json()]
    assert titles == ["Скоро"]


def test_upcoming_uses_env_setting(monkeypatch):
    add(title="Через 10 дней", days_ahead=10)
    assert client.get("/deadlines/upcoming").json() == []
    monkeypatch.setenv("WARN_DAYS", "15")
    assert len(client.get("/deadlines/upcoming").json()) == 1
