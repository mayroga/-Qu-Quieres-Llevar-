# test_main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.1
import os
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("ADMIN_USERNAME","test_admin")
os.environ.setdefault("ADMIN_PASSWORD","test_password")
os.environ.setdefault("STRIPE_PUBLISHABLE_KEY","")
os.environ.setdefault("STRIPE_SECRET_KEY","")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET","")
os.environ.setdefault("STRIPE_PRICE_ID1","")

from main import app,SESSION_SECONDS

client=TestClient(app)

def _ok(r):
    assert r.status_code<500,r.text

def _admin_login():
    r=client.post("/api/v1/admin/login",json={"username":"test_admin","password":"test_password"})
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("success") is True
    assert d.get("token")
    return d["token"]

def test_root():
    r=client.get("/")
    _ok(r)

def test_health():
    r=client.get("/health")
    assert r.status_code==200,r.text
    assert r.json().get("status")=="ok"

def test_meta():
    r=client.get("/api/v1/meta")
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("app_name")=="¿QUÉ QUIERES LLEVAR?"
    assert d.get("version")=="8.0.1"
    assert d.get("owner")=="May Roga LLC"
    assert d.get("session_minutes")==15
    assert d.get("payment_type")=="one_time"
    assert d.get("price_usd")==15.99

def test_legal():
    r=client.get("/api/v1/legal")
    assert r.status_code==200,r.text
    d=r.json()
    assert isinstance(d,dict)
    assert d.get("success") is True
    assert d.get("app_name")=="¿QUÉ QUIERES LLEVAR?"

def test_config():
    r=client.get("/api/v1/config")
    assert r.status_code==200,r.text
    d=r.json()
    assert isinstance(d,dict)
    assert d.get("payment_type")=="one_time"
    assert d.get("price_usd")==15.99
    assert d.get("session_minutes")==15

def test_official_sources():
    r=client.get("/api/v1/official")
    assert r.status_code==200,r.text
    d=r.json()
    assert isinstance(d,dict)
    assert d.get("success") is True
    assert isinstance(d.get("sources"),list)

def test_rules():
    r=client.get("/api/v1/rules")
    assert r.status_code==200,r.text
    d=r.json()
    assert isinstance(d,dict)
    assert "rules" in d
    assert isinstance(d["rules"],list)

def test_flight_sources():
    r=client.get("/api/v1/flight/sources")
    assert r.status_code==200,r.text
    assert isinstance(r.json(),dict)

def test_source_search_empty_query():
    r=client.get("/api/v1/sources/search?q=")
    assert r.status_code==200,r.text
    assert isinstance(r.json(),dict)

def test_source_search_baggage():
    r=client.get("/api/v1/sources/search?q=equipaje")
    assert r.status_code==200,r.text
    assert isinstance(r.json(),dict)

def test_route_sources():
    r=client.get("/api/v1/sources/route?origin=MIA&destination=HAV")
    assert r.status_code==200,r.text
    assert isinstance(r.json(),dict)

def test_baggage_sources():
    r=client.get("/api/v1/sources/baggage?origin=MIA&destination=HAV")
    assert r.status_code==200,r.text
    assert isinstance(r.json(),dict)

def test_cuba_sources():
    r=client.get("/api/v1/cuba/sources")
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("success") is True
    assert isinstance(d.get("sources"),list)

def test_cuba_guide():
    r=client.get("/api/v1/cuba/guide?language=es")
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("success") is True
    assert isinstance(d.get("steps"),list)
    assert len(d["steps"])>=1

def test_flight_search_requires_valid_input():
    r=client.post("/api/v1/flight/search-external",json={})
    assert r.status_code in (401,422),r.text

def test_flight_search_miami_havana_requires_session():
    payload={
        "origin":"MIA",
        "destination":"HAV",
        "departure_date":"2026-11-15",
        "passengers":1,
        "language":"es"
    }
    r=client.post("/api/v1/flight/search-external",json=payload)
    assert r.status_code==401,r.text

def test_flight_understand_requires_session():
    payload={
        "flight":{
            "origin":"MIA",
            "destination":"HAV",
            "departure_date":"2026-11-15",
            "passengers":1
        },
        "language":"es"
    }
    r=client.post("/api/v1/flight/understand",json=payload)
    assert r.status_code==401,r.text

def test_item_check_requires_session():
    r=client.post("/api/v1/consultar-articulo",json={"item":"power bank","language":"es"})
    assert r.status_code==401,r.text

def test_item_teach_requires_session():
    r=client.post("/api/v1/item/teach",json={"term":"equipaje de mano","language":"es"})
    assert r.status_code==401,r.text

def test_guide_requires_session():
    r=client.post("/api/v1/guide",json={"language":"es"})
    assert r.status_code==401,r.text

def test_admin_status_without_login():
    r=client.get("/api/v1/admin/status")
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("active") is False

def test_admin_login_rejects_wrong_credentials():
    r=client.post("/api/v1/admin/login",json={"username":"wrong_user","password":"wrong_password"})
    assert r.status_code==401,r.text
    d=r.json()
    assert d.get("success") is False

def test_admin_login_accepts_render_credentials():
    token=_admin_login()
    r=client.get("/api/v1/admin/status",headers={"X-Admin-Token":token})
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("active") is True
    assert d.get("remaining_seconds")>0

def test_admin_logout():
    token=_admin_login()
    r=client.post("/api/v1/admin/logout",headers={"X-Admin-Token":token})
    assert r.status_code==200,r.text
    r=client.get("/api/v1/admin/status",headers={"X-Admin-Token":token})
    assert r.status_code==200,r.text
    assert r.json().get("active") is False

def test_session_without_token_rejected():
    r=client.get("/api/v1/session")
    assert r.status_code==401,r.text
    assert r.json().get("success") is False

def test_session_invalid_token_rejected():
    r=client.get("/api/v1/session/not-a-real-session-token")
    assert r.status_code==401,r.text

def test_session_valid_token():
    from main import ACTIVE_PAID_SESSIONS,new_token,now
    token=new_token()
    ACTIVE_PAID_SESSIONS[token]=now()+SESSION_SECONDS
    r=client.get("/api/v1/session",headers={"X-Service-Token":token})
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("active") is True
    assert d.get("token")==token
    assert d.get("remaining_seconds")>0
    ACTIVE_PAID_SESSIONS.pop(token,None)

def test_session_path_valid_token():
    from main import ACTIVE_PAID_SESSIONS,new_token,now
    token=new_token()
    ACTIVE_PAID_SESSIONS[token]=now()+SESSION_SECONDS
    r=client.get(f"/api/v1/session/{token}")
    assert r.status_code==200,r.text
    assert r.json().get("active") is True
    ACTIVE_PAID_SESSIONS.pop(token,None)

def test_payment_endpoint_does_not_crash_without_real_stripe():
    r=client.post("/api/v1/create-checkout-session",json={"language":"es"})
    assert r.status_code<500,r.text
    d=r.json()
    assert isinstance(d,dict)

def test_payment_verification_without_stripe():
    r=client.post("/api/v1/verify-payment",json={"session_id":"test-session"})
    assert r.status_code==200,r.text
    d=r.json()
    assert d.get("paid") is False

def test_webhook_without_secret_returns_configuration_error():
    r=client.post("/api/v1/webhook",content=b"invalid-webhook")
    assert r.status_code in (400,503),r.text

def test_unknown_api_route():
    r=client.get("/api/v1/this-route-does-not-exist")
    assert r.status_code==404

def test_health_or_meta_available():
    r=client.get("/api/v1/meta")
    assert r.status_code==200
