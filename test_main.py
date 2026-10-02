# test_main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.1.0
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
VERSION="8.1.0"

def admin_login():
    r=client.post("/api/v1/admin/login",json={
        "username":os.getenv("ADMIN_USERNAME","admin"),
        "password":os.getenv("ADMIN_PASSWORD","admin123")
    })
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("ok") is True or data.get("success") is True
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
    assert data.get("version")==VERSION
    assert data.get("app")

def test_config():
    r=client.get("/api/v1/config")
    assert r.status_code==200
    data=r.json()
    assert data.get("app_name")
    assert data.get("version")==VERSION
    assert data.get("price_usd")==15.99
    assert data.get("session_minutes")==15
    assert data.get("payment_type")=="one_time"
    assert isinstance(data.get("official_sources"),list)

def test_legal():
    r=client.get("/api/v1/legal")
    assert r.status_code==200
    data=r.json()
    assert data.get("short_notice")
    assert data.get("full_notice")
    assert "May Roga LLC" in data.get("short_notice","")

def test_legal_english():
    r=client.get("/api/v1/legal?language=en")
    assert r.status_code==200
    data=r.json()
    assert data.get("short_notice")
    assert data.get("full_notice")
    assert "May Roga LLC" in data.get("short_notice","")

def test_official_sources():
    r=client.get("/api/v1/sources/official")
    assert r.status_code==200
    data=r.json()
    assert isinstance(data.get("sources"),list)
    assert isinstance(data.get("official_sources"),list)

def test_official():
    r=client.get("/api/v1/official")
    assert r.status_code==200
    data=r.json()
    assert isinstance(data.get("sources"),list)
    assert isinstance(data.get("official_sources"),list)

def test_source_search_without_token_is_protected():
    r=client.get("/api/v1/sources/search?q=Cuba")
    assert r.status_code==401

def test_source_search_with_admin():
    token=admin_login()
    r=client.get("/api/v1/sources/search?q=Cuba",headers=admin_headers(token))
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("sources"),list)

def test_source_search_empty_with_admin():
    token=admin_login()
    r=client.get("/api/v1/sources/search",headers=admin_headers(token))
    assert r.status_code==200,r.text
    assert isinstance(r.json().get("sources"),list)

def test_rules_without_token():
    r=client.get("/api/v1/rules")
    assert r.status_code==401

def test_rules_with_admin():
    token=admin_login()
    r=client.get("/api/v1/rules",headers=admin_headers(token))
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("rules"),list)

def test_cuba_official_without_token():
    r=client.get("/api/v1/cuba/official")
    assert r.status_code==401

def test_cuba_official_with_admin():
    token=admin_login()
    r=client.get("/api/v1/cuba/official",headers=admin_headers(token))
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("title")
    assert isinstance(data.get("important_requirements"),list)
    assert len(data.get("important_requirements",[]))>0
    assert isinstance(data.get("sources"),list)
    assert isinstance(data.get("official_sources"),list)

def test_cuba_official_contains_required_topics():
    token=admin_login()
    r=client.get("/api/v1/cuba/official",headers=admin_headers(token))
    assert r.status_code==200,r.text
    data=r.json()
    text=" ".join(
        str(x)
        for x in data.get("important_requirements",[])
    ).lower()
    assert "pasaporte" in text
    assert "visa" in text or "evisa" in text
    assert "viajeros" in text or "d'viajeros" in text
    assert "equipaje" in text or "baggage" in text

def test_session_without_token():
    r=client.get("/api/v1/session")
    assert r.status_code==200
    data=r.json()
    assert data.get("active") is False

def test_invalid_service_token():
    r=client.get(
        "/api/v1/session",
        headers=service_headers("invalid-service-token")
    )
    assert r.status_code==200
    assert r.json().get("active") is False

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
    assert r.json().get("detail")

def test_admin_status():
    token=admin_login()
    r=client.get("/api/v1/admin/status",headers=admin_headers(token))
    assert r.status_code in (200,404)

def test_admin_protected():
    token=admin_login()
    r=client.get("/api/v1/admin/protected",headers=admin_headers(token))
    assert r.status_code in (200,404)

def test_admin_session_is_active():
    token=admin_login()
    r=client.get("/api/v1/session",headers=admin_headers(token))
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("active") is True
    assert data.get("admin") is True

def test_invalid_admin_token():
    r=client.get(
        "/api/v1/admin/status",
        headers={"X-Admin-Token":"invalid-admin-token"}
    )
    assert r.status_code in (401,404)

def test_protected_flight_without_token():
    r=client.post("/api/v1/flight/search-external",json={
        "origin":"MIA",
        "destination":"HAV",
        "language":"es"
    })
    assert r.status_code==401

def test_protected_item_without_token():
    r=client.post("/api/v1/consultar-articulo",json={
        "item":"medicamentos",
        "language":"es"
    })
    assert r.status_code==401

def test_protected_teach_without_token():
    r=client.post("/api/v1/item/teach",json={
        "term":"D'Viajeros",
        "language":"es"
    })
    assert r.status_code==401

def test_protected_guide_without_token():
    r=client.post("/api/v1/guide",json={
        "language":"es"
    })
    assert r.status_code==401

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

def test_admin_can_understand_flight():
    token=admin_login()
    r=client.post(
        "/api/v1/flight/understand",
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
    assert data.get("origin")=="MIA"
    assert data.get("destination")=="HAV"
    assert isinstance(data.get("results",[]),list)

def test_admin_can_get_flight_sources():
    token=admin_login()
    r=client.get(
        "/api/v1/flight/sources",
        headers=admin_headers(token)
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("sources"),list)

def test_admin_can_post_flight_sources():
    token=admin_login()
    r=client.post(
        "/api/v1/flight/sources",
        headers=admin_headers(token),
        json={
            "origin":"MIA",
            "destination":"HAV",
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("sources"),list)
    assert isinstance(data.get("charter_sources"),list)

def test_admin_can_get_charter_sources():
    token=admin_login()
    r=client.get(
        "/api/v1/sources/charter",
        headers=admin_headers(token)
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("sources"),list)

def test_admin_can_get_route_sources():
    token=admin_login()
    r=client.get(
        "/api/v1/sources/route",
        headers=admin_headers(token),
        params={
            "origin":"MIA",
            "destination":"HAV",
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("sources"),list)

def test_admin_can_get_baggage_sources():
    token=admin_login()
    r=client.get(
        "/api/v1/sources/baggage",
        headers=admin_headers(token),
        params={
            "origin":"MIA",
            "destination":"HAV",
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("sources"),list)

def test_admin_can_get_cuba_sources():
    token=admin_login()
    r=client.get(
        "/api/v1/cuba/sources",
        headers=admin_headers(token),
        params={
            "origin":"MIA",
            "destination":"HAV",
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("sources"),list)

def test_admin_can_check_item():
    token=admin_login()
    r=client.post(
        "/api/v1/consultar-articulo",
        headers=admin_headers(token),
        json={
            "item":"power bank",
            "quantity":1,
            "language":"es"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("success") is True
    assert data.get("item")=="power bank"
    assert data.get("requires_official_check") is True or "next_action" in data

def test_admin_can_check_medicine():
    token=admin_login()
    r=client.post(
        "/api/v1/consultar-articulo",
        headers=admin_headers(token),
        json={
            "item":"medicamentos",
            "quantity":1,
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
    assert data.get("term")=="D'Viajeros"

def test_admin_can_teach_power_bank():
    token=admin_login()
    r=client.post(
        "/api/v1/item/teach",
        headers=admin_headers(token),
        json={
            "term":"power bank",
            "language":"en"
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("success") is True
    assert data.get("term")=="power bank"

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
    assert data.get("steps")
    assert isinstance(data.get("steps"),list)
    assert isinstance(data.get("cuba_steps"),list)
    assert isinstance(data.get("official_sources"),list)

def test_admin_can_use_english_guide():
    token=admin_login()
    r=client.post(
        "/api/v1/guide",
        headers=admin_headers(token),
        json={
            "language":"en",
            "flight":{
                "origin":"MIA",
                "destination":"HAV"
            }
        }
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert data.get("steps")
    assert isinstance(data.get("cuba_steps"),list)

def test_admin_can_access_rules_without_payment():
    token=admin_login()
    r=client.get(
        "/api/v1/rules",
        headers=admin_headers(token)
    )
    assert r.status_code==200,r.text
    data=r.json()
    assert isinstance(data.get("rules"),list)

def test_admin_can_access_cuba_official_without_payment():
    token=admin_login()
    r=client.get(
        "/api/v1/cuba/official",
        headers=admin_headers(token)
    )
    assert r.status_code==200,r.text

def test_create_checkout_without_stripe_configuration():
    r=client.post(
        "/api/v1/create-checkout-session",
        json={
            "language":"es"
        }
    )
    if os.getenv("STRIPE_SECRET_KEY") and os.getenv("STRIPE_PRICE_ID1"):
        assert r.status_code in (200,502,503)
    else:
        assert r.status_code==503

def test_verify_payment_requires_session_id():
    r=client.post(
        "/api/v1/verify-payment",
        json={
            "session_id":""
        }
    )
    assert r.status_code in (400,422)

def test_webhook_without_secret():
    r=client.post(
        "/api/v1/webhook",
        content=b"{}",
        headers={"stripe-signature":"test"}
    )
    if os.getenv("STRIPE_WEBHOOK_SECRET"):
        assert r.status_code==400
    else:
        assert r.status_code==200
        assert r.json().get("received") is True

def test_health_does_not_require_payment():
    r=client.get("/health")
    assert r.status_code==200

def test_config_does_not_require_payment():
    r=client.get("/api/v1/config")
    assert r.status_code==200

def test_official_does_not_require_payment():
    r=client.get("/api/v1/sources/official")
    assert r.status_code==200

def test_legal_does_not_require_payment():
    r=client.get("/api/v1/legal")
    assert r.status_code==200

def test_session_endpoint_exists():
    r=client.get("/api/v1/session")
    assert r.status_code==200

if __name__=="__main__":
    import pytest
    raise SystemExit(pytest.main([__file__,"-q"]))
