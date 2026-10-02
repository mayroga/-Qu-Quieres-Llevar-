# test_main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.1
import os
from fastapi.testclient import TestClient

os.environ.setdefault("ADMIN_USERNAME","admin")
os.environ.setdefault("ADMIN_PASSWORD","admin123")
os.environ.setdefault("STRIPE_PRICE_ID1","")
os.environ.setdefault("STRIPE_PUBLISHABLE_KEY","")
os.environ.setdefault("STRIPE_SECRET_KEY","")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET","")
os.environ.setdefault("GEMINI_API_KEY","")

from main import app

client=TestClient(app)

def admin_login():
    r=client.post("/api/v1/admin/login",json={
        "username":os.getenv("ADMIN_USERNAME","admin"),
        "password":os.getenv("ADMIN_PASSWORD","admin123")
    })
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("success") is True
    assert data.get("token")
    return data["token"]

def admin_headers(token=None):
    return {"X-Admin-Token":token or admin_login()}

def service_headers(token):
    return {"X-Service-Token":token}

def test_root():
    r=client.get("/")
    assert r.status_code==200
    assert "text/html" in r.headers.get("content-type","")

def test_health():
    r=client.get("/health")
    assert r.status_code==200
    data=r.json()
    assert data.get("status")=="ok"
    assert data.get("version")=="8.0.1"

def test_meta():
    r=client.get("/api/v1/meta")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("version")=="8.0.1"
    assert data.get("name")
    assert data.get("owner")=="May Roga LLC"
    assert data.get("price_usd")==15.99
    assert data.get("session_minutes")==15

def test_config():
    r=client.get("/api/v1/config")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("app_name")
    assert data.get("owner")=="May Roga LLC"
    assert data.get("price_usd")==15.99
    assert data.get("session_minutes")==15

def test_legal():
    r=client.get("/api/v1/legal")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("owner")=="May Roga LLC"
    assert data.get("app_name")
    assert data.get("short_notice")
    assert data.get("full_notice")

def test_legal_english():
    r=client.get("/api/v1/legal?language=en")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("language")=="en"
    assert data.get("short_notice")
    assert data.get("full_notice")

def test_official_sources():
    r=client.get("/api/v1/sources/official")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert isinstance(data.get("sources"),list)

def test_source_search():
    r=client.get("/api/v1/sources/search?q=Cuba")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert isinstance(data.get("sources"),list)

def test_source_search_empty():
    r=client.get("/api/v1/sources/search")
    assert r.status_code in (200,422)

def test_rules():
    r=client.get("/api/v1/rules")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert isinstance(data.get("rules"),list)

def test_cuba_official():
    r=client.get("/api/v1/cuba/official")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert isinstance(data.get("steps"),list)
    assert len(data["steps"])>0
    assert isinstance(data.get("official_sources"),list)

def test_session_without_token():
    r=client.get("/api/v1/session")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("active") is False

def test_protected_endpoint_without_token():
    r=client.post("/api/v1/flight/search-external",json={
        "origin":"MIA",
        "destination":"HAV"
    })
    assert r.status_code==401

def test_protected_item_without_token():
    r=client.post("/api/v1/consultar-articulo",json={
        "item":"medicamentos"
    })
    assert r.status_code==401

def test_protected_teach_without_token():
    r=client.post("/api/v1/item/teach",json={
        "term":"D'Viajeros"
    })
    assert r.status_code==401

def test_protected_guide_without_token():
    r=client.post("/api/v1/guide",json={
        "language":"es"
    })
    assert r.status_code==401

def test_admin_login():
    token=admin_login()
    assert isinstance(token,str)
    assert len(token)>10

def test_admin_invalid_login():
    r=client.post("/api/v1/admin/login",json={
        "username":"wrong-user",
        "password":"wrong-password"
    })
    assert r.status_code==401
    data=r.json()
    assert data.get("detail")

def test_admin_status():
    token=admin_login()
    r=client.get("/api/v1/admin/status",headers=admin_headers(token))
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("active") is True

def test_admin_status_without_token():
    r=client.get("/api/v1/admin/status")
    assert r.status_code==401

def test_admin_protected():
    token=admin_login()
    r=client.get("/api/v1/admin/protected",headers=admin_headers(token))
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("active") is True

def test_admin_session_is_active():
    token=admin_login()
    r=client.get("/api/v1/session",headers=admin_headers(token))
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert data.get("active") is True
    assert data.get("admin") is True

def test_admin_can_use_flight_search():
    token=admin_login()
    r=client.post(
        "/api/v1/flight/search-external",
        headers=admin_headers(token),
        json={
            "origin":"MIA",
            "destination":"HAV",
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("success") is True
    assert isinstance(data.get("results"),list)

def test_admin_can_check_item():
    token=admin_login()
    r=client.post(
        "/api/v1/consultar-articulo",
        headers=admin_headers(token),
        json={
            "item":"power bank",
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("success") is True
    assert data.get("item")

def test_admin_can_teach_term():
    token=admin_login()
    r=client.post(
        "/api/v1/item/teach",
        headers=admin_headers(token),
        json={
            "term":"D'Viajeros",
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("success") is True
    assert data.get("term")

def test_admin_can_use_guide():
    token=admin_login()
    r=client.post(
        "/api/v1/guide",
        headers=admin_headers(token),
        json={
            "language":"es",
            "flight":{
                "origin":"MIA",
                "destination":"HAV"
            }
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("success") is True
    assert isinstance(data.get("steps"),list)

def test_admin_logout():
    token=admin_login()
    r=client.post("/api/v1/admin/logout",headers=admin_headers(token))
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True

def test_invalid_service_token():
    r=client.get(
        "/api/v1/session",
        headers=service_headers("invalid-service-token")
    )
    assert r.status_code==200
    data=r.json()
    assert data.get("active") is False

def test_invalid_admin_token():
    r=client.get(
        "/api/v1/admin/status",
        headers={"X-Admin-Token":"invalid-admin-token"}
    )
    assert r.status_code==401

def test_flight_sources():
    r=client.get("/api/v1/flight/sources")
    assert r.status_code==200
    data=r.json()
    assert data.get("success") is True
    assert isinstance(data.get("sources"),list)

def test_flight_search_public_is_protected():
    r=client.post("/api/v1/flight/search-external",json={
        "origin":"MIA",
        "destination":"HAV",
        "language":"es"
    })
    assert r.status_code==401

def test_cuba_official_contains_required_topics():
    r=client.get("/api/v1/cuba/official")
    assert r.status_code==200
    data=r.json()
    steps=data.get("steps",[])
    text=" ".join(
        str(x)
        for x in steps
    ).lower()
    assert "pasaporte" in text
    assert "visa" in text or "evisa" in text
    assert "viajeros" in text or "d'viajeros" in text
    assert "equipaje" in text or "baggage" in text

def test_create_checkout_without_stripe_configuration():
    r=client.post("/api/v1/create-checkout-session",json={
        "return_path":"/"
    })
    if os.getenv("STRIPE_SECRET_KEY") and os.getenv("STRIPE_PRICE_ID1"):
        assert r.status_code in (200,400,500,502,503)
    else:
        assert r.status_code==503

def test_verify_payment_requires_session_id():
    r=client.post("/api/v1/verify-payment",json={
        "session_id":""
    })
    assert r.status_code==422

def test_webhook_without_secret():
    r=client.post(
        "/api/v1/webhook",
        content=b"{}",
        headers={"stripe-signature":"test"}
    )
    if os.getenv("STRIPE_WEBHOOK_SECRET"):
        assert r.status_code in (400,401,403,400)
    else:
        assert r.status_code==503

def test_health_does_not_require_payment():
    r=client.get("/health")
    assert r.status_code==200

def test_meta_does_not_require_payment():
    r=client.get("/api/v1/meta")
    assert r.status_code==200

def test_official_does_not_require_payment():
    r=client.get("/api/v1/sources/official")
    assert r.status_code==200

def test_legal_does_not_require_payment():
    r=client.get("/api/v1/legal")
    assert r.status_code==200

def test_admin_can_access_cuba_official_without_payment():
    token=admin_login()
    r=client.get(
        "/api/v1/cuba/official",
        headers=admin_headers(token)
    )
    assert r.status_code==200
    assert r.json().get("success") is True

def test_admin_can_access_rules_without_payment():
    token=admin_login()
    r=client.get(
        "/api/v1/rules",
        headers=admin_headers(token)
    )
    assert r.status_code==200
    assert r.json().get("success") is True

if __name__=="__main__":
    import pytest
    raise SystemExit(pytest.main([__file__,"-q"]))
