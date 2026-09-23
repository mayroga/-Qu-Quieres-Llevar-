# test_main.py - Pruebas Unitarias para el modelo de 15 minutos
from fastapi.testclient import TestClient
from main import app, ACTIVE_PAID_SESSIONS
import datetime

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["owner"] == "May Roga LLC"
    assert "intro_explanation" in response.json()

def test_consultar_sin_token_activo():
    payload = {
        "session_token": "token_inexistente",
        "item_description": "power bank",
        "destination": "Cuba"
    }
    response = client.post("/api/v1/consultar-articulo", json=payload)
    assert response.status_code == 403

def test_consultar_con_token_valido():
    # Simular la emisión de un token válido por Stripe Webhook por 15 minutos
    test_token = "tkn_test_12345"
    ACTIVE_PAID_SESSIONS[test_token] = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)

    payload = {
        "session_token": test_token,
        "item_description": "power bank",
        "airline": "American Airlines",
        "destination": "Cuba"
    }
    response = client.post("/api/v1/consultar-articulo", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status_category"] == "PUEDES LLEVARLO, PERO..."
    assert "equipaje de mano" in data["short_answer"].lower()

    # Limpiar
    if test_token in ACTIVE_PAID_SESSIONS:
        del ACTIVE_PAID_SESSIONS[test_token]
