# test_main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.0
import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ADMIN_USERNAME","test_admin")
os.environ.setdefault("ADMIN_PASSWORD","test_password")
os.environ.setdefault("STRIPE_PUBLISHABLE_KEY","")
os.environ.setdefault("STRIPE_SECRET_KEY","")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET","")
os.environ.setdefault("STRIPE_PRICE_ID1","")
os.environ.setdefault("GEMINI_API_KEY","")

from main import app

client=TestClient(app)

def _ok(r):
    assert r.status_code<500,r.text

def test_root():
    r=client.get("/")
    _ok(r)

def test_meta():
    r=client.get("/api/v1/meta")
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("success") is True
    assert d.get("app_name")=="¿QUÉ QUIERES LLEVAR?"
    assert d.get("version")=="8.0.0"
    assert d.get("owner")=="May Roga LLC"

def test_legal():
    r=client.get("/api/v1/legal")
    assert r.status_code==200,r.text
    d=r.json()
    assert isinstance(d,dict)
    assert d

def test_config():
    r=client.get("/api/v1/config")
    assert r.status_code==200,r.text
    d=r.json()
    assert isinstance(d,dict)

def test_official_sources():
    r=client.get("/api/v1/official")
    _ok(r)
    assert isinstance(r.json(),dict)

def test_rules():
    r=client.get("/api/v1/rules")
    assert r.status_code==200,r.text
    d=r.json()
    assert isinstance(d,dict)
    assert "rules" in d or "items" in d or "data" in d

def test_flight_sources():
    r=client.get("/api/v1/flight/sources")
    _ok(r)
    assert isinstance(r.json(),dict)

def test_source_search_empty_query():
    r=client.get("/api/v1/sources/search?q=")
    _ok(r)
    assert isinstance(r.json(),dict)

def test_source_search_baggage():
    r=client.get("/api/v1/sources/search?q=equipaje")
    _ok(r)
    assert isinstance(r.json(),dict)

def test_route_sources():
    r=client.get("/api/v1/sources/route?origin=MIA&destination=HAV")
    _ok(r)
    assert isinstance(r.json(),dict)

def test_baggage_sources():
    r=client.get("/api/v1/sources/baggage?origin=MIA&destination=HAV")
    _ok(r)
    assert isinstance(r.json(),dict)

def test_flight_search_requires_valid_input():
    r=client.post("/api/v1/flight/search-external",json={})
    assert r.status_code in (200,400,422),r.text

def test_flight_search_miami_havana():
    payload={
        "origin":"MIA",
        "destination":"HAV",
        "departure_date":"2026-11-15",
        "passengers":1,
        "language":"es"
    }
    r=client.post("/api/v1/flight/search-external",json=payload)
    assert r.status_code<500,r.text
    d=r.json()
    assert isinstance(d,dict)
    if r.status_code==200:
        assert "search" in d or "results" in d or "sources" in d or "message" in d

def test_flight_understand_does_not_invent_airline():
    payload={
        "origin":"MIA",
        "destination":"HAV",
        "departure_date":"2026-11-15",
        "passengers":1,
        "language":"es"
    }
    r=client.post("/api/v1/flight/understand",json=payload)
    assert r.status_code<500,r.text
    d=r.json()
    assert isinstance(d,dict)
    raw=str(d).lower()
    assert "xael" not in raw

def test_item_check_battery():
    payload={
        "item":"batería",
        "language":"es"
    }
    r=client.post("/api/v1/consultar-articulo",json=payload)
    assert r.status_code<500,r.text
    d=r.json()
    assert isinstance(d,dict)

def test_item_check_power_bank():
    payload={
        "item":"power bank",
        "language":"es"
    }
    r=client.post("/api/v1/consultar-articulo",json=payload)
    assert r.status_code<500,r.text
    d=r.json()
    assert isinstance(d,dict)

def test_item_teach():
    payload={
        "term":"equipaje de mano",
        "language":"es"
    }
    r=client.post("/api/v1/item/teach",json=payload)
    assert r.status_code<500,r.text
    assert isinstance(r.json(),dict)

def test_guide():
    payload={
        "language":"es"
    }
    r=client.post("/api/v1/guide",json=payload)
    assert r.status_code<500,r.text
    assert isinstance(r.json(),dict)

def test_admin_status_without_login():
    r=client.get("/api/v1/admin/status")
    _ok(r)
    d=r.json()
    assert isinstance(d,dict)

def test_admin_login_rejects_wrong_credentials():
    payload={
        "username":"wrong_user",
        "password":"wrong_password"
    }
    r=client.post("/api/v1/admin/login",json=payload)
    assert r.status_code in (401,403),r.text

def test_session_without_token_rejected():
    r=client.get("/api/v1/session")
    assert r.status_code in (401,403,404),r.text

def test_session_invalid_token_rejected():
    r=client.get("/api/v1/session/not-a-real-session-token")
    assert r.status_code in (401,403,404),r.text

def test_payment_endpoint_does_not_crash_without_real_stripe():
    payload={"language":"es"}
    r=client.post("/api/v1/create-checkout-session",json=payload)
    assert r.status_code<500,r.text

def test_webhook_rejects_invalid_request():
    r=client.post("/api/v1/webhook",content=b"invalid-webhook")
    assert r.status_code in (400,401,403),r.text

def test_unknown_api_route():
    r=client.get("/api/v1/this-route-does-not-exist")
    assert r.status_code==404

def test_health_or_meta_available():
    r=client.get("/api/v1/meta")
    assert r.status_code==200

if __name__=="__main__":
    pytest.main(["-q",__file__])
