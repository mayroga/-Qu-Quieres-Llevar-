from fastapi.testclient import TestClient
from main import app

client=TestClient(app)

def test_home():
    r=client.get("/")
    assert r.status_code==200

def test_health():
    r=client.get("/health")
    assert r.status_code==200
    assert r.json().get("status")=="ok"

def test_config():
    r=client.get("/api/v1/config")
    assert r.status_code==200
    d=r.json()
    assert "app_name" in d
    assert "version" in d

def test_session():
    r=client.post("/api/v1/session",json={"language":"es"})
    assert r.status_code==200
    d=r.json()
    assert d.get("token")
    assert d.get("language")=="es"

def test_session_get():
    r=client.get("/api/v1/session")
    assert r.status_code in (200,401)

def test_flight_missing():
    r=client.post("/api/v1/flight/understand",json={})
    assert r.status_code in (200,400,422)

def test_flight_success():
    r=client.post("/api/v1/flight/understand",json={
        "origin":"Miami",
        "destination":"Madrid",
        "airline":"American Airlines",
        "flight_number":"AA1",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_flight_search():
    r=client.post("/api/v1/flight/search",json={
        "origin":"Miami",
        "destination":"Madrid",
        "airline":"American Airlines",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_flight_sources():
    r=client.post("/api/v1/flight/sources",json={
        "airline":"American Airlines",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_item_missing():
    r=client.post("/api/v1/item/check",json={})
    assert r.status_code in (200,400,422)

def test_item_success():
    r=client.post("/api/v1/item/check",json={
        "item":"medicinas",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_item_legacy():
    r=client.post("/api/v1/consultar-articulo",json={
        "item_description":"medicinas",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_baggage():
    r=client.post("/api/v1/baggage",json={
        "airline":"American Airlines",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_teach():
    r=client.post("/api/v1/item/teach",json={
        "term":"check-in",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_official_sources():
    r=client.get("/api/v1/sources/official")
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_official_sources_legacy():
    r=client.get("/api/v1/official-sources")
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_cuba_official():
    r=client.post("/api/v1/cuba/official",json={
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_cuba_practice():
    r=client.post("/api/v1/cuba/practice",json={
        "topic":"visa",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_cuba_visa():
    r=client.post("/api/v1/cuba/visa",json={
        "nationality":"United States",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_cuba_dviajeros():
    r=client.post("/api/v1/cuba/dviajeros",json={
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_legal():
    r=client.get("/api/v1/legal")
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_practice():
    r=client.post("/api/v1/practice",json={
        "topic":"flight",
        "language":"es"
    })
    assert r.status_code==200
    assert isinstance(r.json(),dict)

def test_english():
    r=client.get("/api/v1/config?language=en")
    assert r.status_code==200
    assert isinstance(r.json(),dict)
