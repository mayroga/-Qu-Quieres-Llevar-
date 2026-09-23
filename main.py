# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC
# Producción: FastAPI + Stripe + Gemini API + Acceso Admin / Gratis
# Producto actual: $15.99 = 1 servicio / 15 minutos (o acceso libre por Administrador)
# Gemini: búsqueda/interpretación de vuelos únicamente.
# Motor de reglas: autoridad interna para las respuestas de equipaje.

import os, re, json, html, hmac, hashlib, secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import stripe
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from rules_engine import RuleRepository, RuleStatus
from legal_disclaimer import LegalNoticeManager

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

APP_NAME = "¿Qué Quieres Llevar?"
APP_VERSION = "6.1.0"
OWNER = "May Roga LLC"
SESSION_MINUTES = 15

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
STRIPE_PRICE_ID1 = os.getenv("STRIPE_PRICE_ID1", "").strip()
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://que-quieres-llevar.onrender.com").rstrip("/")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

rule_repo = RuleRepository()
gemini_client = None
if GEMINI_API_KEY and genai is not None:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        gemini_client = None

app = FastAPI(title=APP_NAME, description="Herramienta independiente de orientación preventiva sobre equipaje, artículos y vuelos. May Roga LLC.", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[APP_BASE_URL],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Stripe-Signature"],
)

class FlightSearchRequest(BaseModel):
    natural_query: str = Field(..., min_length=3, max_length=1200)
    session_token: str = Field(..., min_length=20, max_length=300)

class ItemCheckRequest(BaseModel):
    session_token: str = Field(..., min_length=20, max_length=300)
    item_description: str = Field(..., min_length=1, max_length=2000)
    airline: Optional[str] = Field(default=None, max_length=150)
    destination: Optional[str] = Field(default=None, max_length=150)
    flight_context: Optional[dict[str, Any]] = None

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminFreeSessionRequest(BaseModel):
    username: str
    password: str

class ActivateSessionRequest(BaseModel):
    checkout_session_id: str = Field(..., min_length=10, max_length=300)

class CheckoutRequest(BaseModel):
    pass

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()

def clean_text(value: Any, max_len: int = 2000) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_len]

def safe_url(url: str) -> bool:
    return bool(isinstance(url, str) and (url.startswith("https://") or url.startswith("http://")))

def escape(value: Any) -> str:
    return html.escape(str(value or ""))

SESSION_SECRET = os.getenv("SESSION_SIGNING_SECRET", "").strip()

def require_session_secret():
    if not SESSION_SECRET:
        raise HTTPException(status_code=503, detail="El servicio de sesiones no está configurado.")

def sign_session(raw: str) -> str:
    require_session_secret()
    sig = hmac.new(SESSION_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"

def build_session_token(checkout_session_id: str, started_at: datetime, expires_at: datetime) -> str:
    raw = json.dumps(
        {"v": 1, "cs": checkout_session_id, "st": int(started_at.timestamp()), "ex": int(expires_at.timestamp())},
        separators=(",", ":"), sort_keys=True
    )
    return sign_session(raw)

def verify_session_token(token: str) -> dict:
    require_session_secret()
    try:
        raw, signature = token.rsplit(".", 1)
        expected = hmac.new(SESSION_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("firma")
        data = json.loads(raw)
        if data.get("v") != 1:
            raise ValueError("version")
        
        checkout_id = data.get("cs")
        started = int(data.get("st"))
        expires = int(data.get("ex"))
        now = int(utcnow().timestamp())

        if now >= expires:
            raise HTTPException(status_code=403, detail="La sesión de 15 minutos ha terminado.")
        if expires <= started:
            raise ValueError("fechas")
        if not checkout_id:
            raise ValueError("checkout")
        return data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Sesión inválida o expirada.")

def stripe_payment_is_valid(checkout_session_id: str) -> dict:
    if checkout_session_id.startswith("admin_free_"):
        return {"payment_status": "paid", "id": checkout_session_id, "metadata": {"service": "que_quieres_llevar"}}
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no está configurado.")
    if not checkout_session_id.startswith("cs_"):
        raise HTTPException(status_code=400, detail="Identificador de pago inválido.")
    try:
        session = stripe.checkout.Session.retrieve(checkout_session_id, expand=["line_items"])
    except Exception:
        raise HTTPException(status_code=400, detail="No fue posible verificar el pago.")

    if session.get("payment_status") != "paid":
        raise HTTPException(status_code=402, detail="El pago todavía no está confirmado.")

    line_items = session.get("line_items", {}).get("data", [])
    valid_price = any(item.get("price", {}).get("id") == STRIPE_PRICE_ID1 for item in line_items)
    if not valid_price:
        raise HTTPException(status_code=403, detail="El pago no corresponde al servicio solicitado.")
    return session

def get_active_session(token: str) -> dict:
    data = verify_session_token(token)
    session = stripe_payment_is_valid(data["cs"])
    if session.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="El pago ya no está confirmado.")
    return data

def legal_intro() -> dict:
    try:
        return LegalNoticeManager.get_intro_explanation()
    except Exception:
        return {
            "what_is_it": "¿QUÉ QUIERES LLEVAR? es una aplicación independiente desarrollada por May Roga LLC.",
            "what_it_does": "Ayuda al pasajero a revisar información sobre equipaje y artículos antes de viajar.",
            "problem_solved": "Reduce la incertidumbre y evita decisiones basadas únicamente en suposiciones.",
            "core_message": "Dime qué quieres llevar y te ayudaremos a revisar si puede viajar contigo según los datos de tu vuelo y las reglas que podamos verificar."
        }

def legal_disclaimer() -> str:
    try:
        return LegalNoticeManager.get_official_disclaimer()["content"]
    except Exception:
        return "Esta aplicación proporciona información orientativa basada en fuentes verificadas. No sustituye a la aerolínea, TSA, DOT, FAA, CBP ni a ninguna autoridad competente."

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "stripe_configured": bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "gemini_configured": bool(gemini_client)
    }

@app.get("/api/v1/status")
def service_status():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "payment": "configured" if STRIPE_SECRET_KEY and STRIPE_PRICE_ID1 else "not_configured",
        "flight_search": "configured" if gemini_client else "not_configured",
        "session_minutes": SESSION_MINUTES
    }

@app.get("/", response_class=HTMLResponse)
def read_root():
    intro = legal_intro()
    html_content = f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(APP_NAME)} — May Roga LLC</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f3f6f8;color:#1f2937;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:700px;margin:auto;padding:18px}}
.card{{background:#fff;border-radius:16px;padding:22px;box-shadow:0 5px 25px rgba(0,0,0,.08)}}
h1{{text-align:center;margin:4px 0;color:#0f3d59;font-size:25px}}
.sub{{text-align:center;color:#64748b;font-size:13px}}
.box{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin:14px 0;line-height:1.5;font-size:14px}}
.warning{{border-left:4px solid #0f3d59}}
label{{display:block;font-weight:700;margin:15px 0 6px;font-size:14px}}
textarea,input{{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:9px;font-size:15px}}
button{{width:100%;border:0;border-radius:9px;padding:13px;margin-top:10px;background:#0f3d59;color:#fff;font-weight:700;font-size:15px;cursor:pointer}}
button.secondary{{background:#64748b}}
button.green{{background:#166534}}
button.admin-btn{{background:#7c3aed;margin-top:20px}}
button:disabled{{opacity:.55;cursor:not-allowed}}
.small{{font-size:12px;color:#64748b;line-height:1.45}}
#appArea{{display:none}}
#adminArea{{margin-top:25px;border-top:1px dashed #cbd5e1;padding-top:15px}}
#adminInputs{{display:none;margin-top:10px}}
#result{{margin-top:15px}}
.result{{padding:15px;border-radius:10px;background:#f8fafc;border:1px solid #e2e8f0}}
.ok{{color:#166534;font-weight:800}}
.no{{color:#991b1b;font-weight:800}}
.warn{{color:#92400e;font-weight:800}}
.info{{color:#1e40af;font-weight:800}}
.timer{{text-align:center;font-size:20px;font-weight:800;margin:12px 0;color:#0f3d59}}
a{{color:#0f3d59;font-weight:700}}
ul{{padding-left:20px}}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h1>¿QUÉ QUIERES LLEVAR?</h1>
<div class="sub">May Roga LLC</div>

<div class="box warning">
<strong>¿Qué es?</strong><br>{escape(intro.get("what_is_it",""))}<br><br>
<strong>¿Para qué sirve?</strong><br>{escape(intro.get("what_it_does",""))}<br><br>
<strong>¿Qué problema busca resolver?</strong><br>{escape(intro.get("problem_solved",""))}<br><br>
<strong>Mensaje principal:</strong><br>{escape(intro.get("core_message",""))}
</div>

<div class="box">
<strong>Importante:</strong><br>
La aplicación ayuda a reducir la incertidumbre antes de llegar al aeropuerto. No garantiza que una aerolínea acepte un artículo ni sustituye la decisión final de la aerolínea o autoridad competente. Si una regla no puede verificarse, la aplicación no debe inventar una respuesta.
</div>

<div id="legal">
<h3>Antes de comenzar</h3>
<p class="small">Al continuar reconoces que esta aplicación ofrece orientación informativa y preventiva basada en fuentes verificadas. No sustituye a la aerolínea, TSA, DOT, FAA, CBP ni a otra autoridad competente.</p>
<p class="small">El servicio actual cuesta <strong>$15.99</strong> y corresponde a <strong>un solo servicio de 15 minutos</strong>. No es una suscripción.</p>
<label><input type="checkbox" id="acceptLegal" style="width:auto"> He leído y acepto esta explicación.</label>
<button id="payBtn" onclick="startPayment()" disabled>PAGAR $15.99 — INICIAR SERVICIO</button>

<div id="adminArea">
<button class="admin-btn" onclick="toggleAdminPanel()">🔑 Acceso Administrador (Entrada Gratis)</button>
<div id="adminInputs">
<label>Usuario Admin</label>
<input type="text" id="adminUser" placeholder="Usuario administrador">
<label>Contraseña Admin</label>
<input type="password" id="adminPass" placeholder="Contraseña administrador">
<button class="green" onclick="adminFreeAccess()">INGRESAR GRATIS COMO ADMIN</button>
</div>
</div>
</div>

<div id="appArea">
<div class="timer">Tiempo restante: <span id="timer">15:00</span></div>
<label>1. ¿Dónde y cuándo viajas?</label>
<textarea id="flightQuery" rows="3" placeholder="Ejemplo: Miami a La Habana el 15 de diciembre con American Airlines"></textarea>
<button onclick="searchFlight()">✈️ BUSCAR / IDENTIFICAR MI VUELO</button>

<label>2. ¿Qué quieres llevar?</label>
<textarea id="item" rows="3" placeholder="Ejemplo: una cafetera de 8 libras"></textarea>
<button class="green" onclick="checkItem()">🔎 REVISAR SI PUEDO LLEVARLO</button>
<button class="secondary" onclick="clearForm()">BORRAR</button>
<div id="result"></div>
</div>

<div class="box small" style="margin-top:20px"><strong>Aviso:</strong><br>{escape(legal_disclaimer())}</div>
<div class="small" style="text-align:center">&copy; 2026 May Roga LLC. Todos los derechos reservados.</div>
</div>
</div>

<script>
let sessionToken = "";
let expiresAt = 0;
let timerHandle = null;

const legalCheck = document.getElementById("acceptLegal");
const payBtn = document.getElementById("payBtn");

legalCheck.addEventListener("change", () => {{
    payBtn.disabled = !legalCheck.checked;
}});

function toggleAdminPanel() {{
    const panel = document.getElementById("adminInputs");
    panel.style.display = panel.style.display === "block" ? "none" : "block";
}}

async function startPayment() {{
    payBtn.disabled = true;
    payBtn.innerText = "CREANDO PAGO...";
    try {{
        const response = await fetch("/api/v1/stripe/create-checkout", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{}})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No fue posible iniciar el pago.");
        window.location.href = data.checkout_url;
    }} catch(error) {{
        alert(error.message);
        payBtn.disabled = false;
        payBtn.innerText = "PAGAR $15.99 — INICIAR SERVICIO";
    }}
}}

async function adminFreeAccess() {{
    const u = document.getElementById("adminUser").value.trim();
    const p = document.getElementById("adminPass").value.trim();
    if (!u || !p) {{ alert("Introduce usuario y contraseña de administrador."); return; }}

    try {{
        const response = await fetch("/api/v1/admin/free-session", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ username: u, password: p }})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Credenciales de administrador inválidas.");

        sessionToken = data.session_token;
        expiresAt = Date.parse(data.expires_at);

        document.getElementById("legal").style.display = "none";
        document.getElementById("appArea").style.display = "block";
        startTimer();
    }} catch(error) {{
        alert(error.message);
    }}
}}

async function activateFromStripe() {{
    const params = new URLSearchParams(window.location.search);
    const checkoutSessionId = params.get("session_id");
    if (!checkoutSessionId) return false;

    try {{
        const response = await fetch("/api/v1/stripe/activate", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ checkout_session_id: checkoutSessionId }})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No se pudo activar el servicio.");

        sessionToken = data.session_token;
        expiresAt = Date.parse(data.expires_at);

        document.getElementById("legal").style.display = "none";
        document.getElementById("appArea").style.display = "block";
        history.replaceState({{}}, document.title, "/");
        startTimer();
        return true;
    }} catch(error) {{
        document.getElementById("result").innerHTML = "<div class='result'><strong>No se pudo activar el servicio.</strong><br>" + escapeHtml(error.message) + "</div>";
        return false;
    }}
}}

function startTimer() {{
    clearInterval(timerHandle);
    function update() {{
        const remaining = Math.max(0, expiresAt - Date.now());
        const totalSeconds = Math.floor(remaining / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        document.getElementById("timer").innerText = String(minutes).padStart(2,"0") + ":" + String(seconds).padStart(2,"0");
        if (remaining <= 0) {{
            clearInterval(timerHandle);
            sessionToken = "";
            document.getElementById("appArea").innerHTML = "<div class='result'><h3>⏱️ SERVICIO TERMINADO</h3><p>Tu servicio de 15 minutos ha terminado.</p><button onclick='window.location.href=\"/\"'>INICIAR DE NUEVO</button></div>";
        }}
    }}
    update();
    timerHandle = setInterval(update, 1000);
}}

async function searchFlight() {{
    const query = document.getElementById("flightQuery").value.trim();
    if (!query) {{ alert("Escribe primero los datos de tu viaje."); return; }}
    showResult("Buscando información actual del vuelo...");

    try {{
        const response = await fetch("/api/v1/flight/search", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ natural_query: query, session_token: sessionToken }})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No fue posible buscar el vuelo.");

        let out = "<div class='result'><h3>✈️ Resultado de búsqueda</h3>";
        if (!data.flights || !data.flights.length) {{
            out += "<p class='info'>🔵 NECESITO MÁS INFORMACIÓN</p><p>No encontramos suficiente información verificable.</p>";
        }} else {{
            data.flights.forEach((f) => {{
                out += "<div class='box'><strong>" + escapeHtml(f.airline || "") + "</strong><br>" + escapeHtml(f.route || "") + "<br>";
                if (f.flight_number) out += "Vuelo: " + escapeHtml(f.flight_number) + "<br>";
                if (f.source) out += "<span class='small'>Fuente: " + escapeHtml(f.source) + "</span><br>";
                if (f.url && /^https?:\\/\\//i.test(f.url)) out += "<a target='_blank' rel='noopener noreferrer' href='" + escapeAttr(f.url) + "'>Ver fuente</a>";
                out += "</div>";
            }});
        }}
        out += "</div>";
        document.getElementById("result").innerHTML = out;
    }} catch(error) {{
        showResult("<div class='result'><p class='info'>🔵 NECESITO MÁS INFORMACIÓN</p><p>" + escapeHtml(error.message) + "</p></div>");
    }}
}}

async function checkItem() {{
    const item = document.getElementById("item").value.trim();
    const flightQuery = document.getElementById("flightQuery").value.trim();
    if (!item) {{ alert("Escribe primero qué quieres llevar."); return; }}
    showResult("Revisando la información disponible...");

    try {{
        const response = await fetch("/api/v1/consultar-articulo", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ session_token: sessionToken, item_description: item, flight_context: {{ natural_query: flightQuery }} }})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No fue posible realizar la consulta.");

        let cls = "info";
        if ((data.status_category || "").includes("PUEDES LLEVARLO")) cls = "ok";
        if ((data.status_category || "").includes("NO PUEDES")) cls = "no";

        let links = "";
        if (Array.isArray(data.official_links)) {{
            links = "<ul>";
            data.official_links.forEach((link) => {{
                if (link.url && /^https?:\\/\\//i.test(link.url)) {{
                    links += "<li><a target='_blank' rel='noopener noreferrer' href='" + escapeAttr(link.url) + "'>" + escapeHtml(link.title || "Fuente oficial") + "</a></li>";
                }}
            }});
            links += "</ul>";
        }}

        document.getElementById("result").innerHTML = "<div class='result'><h3 class='" + cls + "'>" + escapeHtml(data.status_category || "RESULTADO") + "</h3><p><strong>" + escapeHtml(data.short_answer || "") + "</strong></p><div class='box'>" + escapeHtml(data.details || "") + "</div>" + (links ? "<div class='box'><strong>Fuentes:</strong>" + links + "</div>" : "") + "<p class='small'>" + escapeHtml(data.source_reference || "") + "</p></div>";
    }} catch(error) {{
        showResult("<div class='result'><p class='info'>🔵 NECESITO MÁS INFORMACIÓN</p><p>" + escapeHtml(error.message) + "</p></div>");
    }}
}}

function clearForm() {{
    document.getElementById("flightQuery").value = "";
    document.getElementById("item").value = "";
    document.getElementById("result").innerHTML = "";
}}

function showResult(text) {{
    document.getElementById("result").innerHTML = "<div class='result'>" + text + "</div>";
}}

function escapeHtml(value) {{
    return String(value ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}}

function escapeAttr(value) {{
    return escapeHtml(value);
}}

activateFromStripe();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/v1/stripe/create-checkout")
def create_checkout(_: CheckoutRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no está configurado.")
    if not STRIPE_PRICE_ID1:
        raise HTTPException(status_code=503, detail="STRIPE_PRICE_ID1 no está configurado.")

    try:
        checkout = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID1, "quantity": 1}],
            success_url=f"{APP_BASE_URL}/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_BASE_URL}/",
            allow_promotion_codes=False,
            metadata={"service": "que_quieres_llevar", "service_version": APP_VERSION, "duration_minutes": str(SESSION_MINUTES)}
        )
    except Exception:
        raise HTTPException(status_code=502, detail="No fue posible crear el pago.")

    return {"status": "created", "checkout_url": checkout.url, "checkout_session_id": checkout.id}

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET no está configurado.")
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Falta la firma de Stripe.")
    try:
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Firma de Stripe inválida.")
    return {"received": True, "event_type": event.get("type")}

@app.post("/api/v1/stripe/activate")
def activate_session(payload: ActivateSessionRequest):
    session = stripe_payment_is_valid(payload.checkout_session_id)
    metadata = dict(session.get("metadata") or {})
    
    if not payload.checkout_session_id.startswith("admin_free_"):
        if metadata.get("service") != "que_quieres_llevar":
            raise HTTPException(status_code=403, detail="El pago no corresponde a este servicio.")
        if metadata.get("activated_at"):
            raise HTTPException(status_code=403, detail="Este pago ya fue utilizado para iniciar un servicio.")

    started_at = utcnow()
    expires_at = started_at + timedelta(minutes=SESSION_MINUTES)

    if not payload.checkout_session_id.startswith("admin_free_"):
        try:
            stripe.checkout.Session.modify(
                payload.checkout_session_id,
                metadata={**metadata, "activated_at": iso(started_at), "expires_at": iso(expires_at), "service_status": "active"}
            )
        except Exception:
            raise HTTPException(status_code=502, detail="No fue posible registrar el inicio del servicio.")

    token = build_session_token(payload.checkout_session_id, started_at, expires_at)
    return {"status": "active", "session_token": token, "started_at": iso(started_at), "expires_at": iso(expires_at), "minutes": SESSION_MINUTES}

@app.get("/api/v1/session/status")
def session_status(session_token: str):
    data = get_active_session(session_token)
    expires = datetime.fromtimestamp(int(data["ex"]), tz=timezone.utc)
    remaining = max(0, int((expires - utcnow()).total_seconds()))
    return {"active": remaining > 0, "expires_at": iso(expires), "remaining_seconds": remaining}

def extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except Exception:
        pass
    match = re.search(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, flags=re.S)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except Exception:
        return None

def gemini_flight_search(query: str) -> dict:
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="La búsqueda de vuelos no está configurada.")

    prompt = f"""
Eres un módulo interno de búsqueda de vuelos de una aplicación llamada ¿QUÉ QUIERES LLEVAR? de May Roga LLC.
Tu trabajo aquí NO es decidir reglas de equipaje.
Busca información actual disponible públicamente sobre vuelos que correspondan a la solicitud del usuario.
SOLICITUD DEL USUARIO:{query}
Devuelve exclusivamente JSON válido con estructura:
{{
  "flights": [
    {{
      "airline": "",
      "flight_number": "",
      "origin": "",
      "destination": "",
      "date": "",
      "route": "",
      "source": "",
      "url": ""
    }}
  ],
  "notice": ""
}}
"""
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        )
    except Exception:
        raise HTTPException(status_code=502, detail="No fue posible consultar el servicio de búsqueda.")

    result = extract_json_object(getattr(response, "text", "") or "")
    if not result:
        return {"flights": [], "notice": "No encontramos información suficientemente verificable."}

    flights = result.get("flights")
    if not isinstance(flights, list):
        flights = []

    cleaned = []
    for flight in flights[:10]:
        if not isinstance(flight, dict):
            continue
        item = {
            "airline": clean_text(flight.get("airline"), 150),
            "flight_number": clean_text(flight.get("flight_number"), 50),
            "route": clean_text(flight.get("route"), 250),
            "source": clean_text(flight.get("source"), 200),
            "url": clean_text(flight.get("url"), 500)
        }
        if item["url"] and not safe_url(item["url"]):
            item["url"] = ""
        if item["airline"] or item["flight_number"] or item["route"]:
            cleaned.append(item)

    return {"flights": cleaned, "notice": clean_text(result.get("notice", "Confirmar antes de viajar."), 500)}

@app.post("/api/v1/flight/search")
def search_flight(payload: FlightSearchRequest):
    get_active_session(payload.session_token)
    query = clean_text(payload.natural_query, 1200)
    result = gemini_flight_search(query)
    return {"status": "success", **result}

def normalize_airline(value: Optional[str]) -> str:
    return clean_text(value, 150) or "general"

def official_rule_links(rule) -> list:
    source = getattr(rule, "source_name", "") or ""
    return [{"title": source or "Fuente de referencia", "url": "https://www.iata.org/"}]

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    get_active_session(payload.session_token)
    item = clean_text(payload.item_description, 2000)
    airline = normalize_airline(payload.airline)

    if not item:
        raise HTTPException(status_code=422, detail="Debes indicar qué artículo quieres consultar.")

    rule = rule_repo.find_rule(airline, item.lower())
    if rule and rule.status == RuleStatus.ACTIVA:
        return {
            "status_category": rule.category_visual,
            "short_answer": rule.short_answer,
            "details": rule.details,
            "source_reference": f"{rule.source_name} (Verificado el {rule.verification_date})",
            "official_links": official_rule_links(rule),
            "disclaimer": legal_disclaimer()
        }

    return {
        "status_category": "NECESITO MÁS INFORMACIÓN",
        "short_answer": "No encontramos una regla verificada suficiente para darte una respuesta segura sobre este artículo.",
        "details": "No vamos a inventar una autorización o prohibición. Necesitamos información adicional o una fuente oficial que permita verificar la condición aplicable.",
        "source_reference": "Regla no verificada",
        "official_links": [
            {"title": "IATA", "url": "https://www.iata.org/"},
            {"title": "TSA — What Can I Bring?", "url": "https://www.tsa.gov/travel/security-screening/whatcanibring/"},
            {"title": "U.S. DOT — Air Consumer", "url": "https://www.transportation.gov/airconsumer"}
        ],
        "disclaimer": legal_disclaimer()
    }

ADMIN_TOKENS = {}

@app.post("/api/v1/admin/login")
def admin_login(payload: AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Acceso administrativo no configurado.")
    if not hmac.compare_digest(payload.username, ADMIN_USERNAME) or not hmac.compare_digest(payload.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")

    token = secrets.token_urlsafe(32)
    ADMIN_TOKENS[token] = utcnow() + timedelta(hours=2)
    return {"status": "success", "session_token": token, "expires_at": iso(ADMIN_TOKENS[token])}

@app.post("/api/v1/admin/free-session")
def admin_free_session(payload: AdminFreeSessionRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Acceso administrativo no configurado.")
    if not hmac.compare_digest(payload.username, ADMIN_USERNAME) or not hmac.compare_digest(payload.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")

    fake_checkout_id = f"admin_free_{secrets.token_hex(8)}"
    started_at = utcnow()
    expires_at = started_at + timedelta(minutes=SESSION_MINUTES)
    token = build_session_token(fake_checkout_id, started_at, expires_at)

    return {
        "status": "active",
        "session_token": token,
        "started_at": iso(started_at),
        "expires_at": iso(expires_at),
        "minutes": SESSION_MINUTES
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "detail": str(exc.detail)})

@app.on_event("startup")
async def startup_check():
    missing = []
    if not STRIPE_SECRET_KEY: missing.append("STRIPE_SECRET_KEY")
    if not STRIPE_PRICE_ID1: missing.append("STRIPE_PRICE_ID1")
    if not STRIPE_WEBHOOK_SECRET: missing.append("STRIPE_WEBHOOK_SECRET")
    if not SESSION_SECRET: missing.append("SESSION_SIGNING_SECRET")
    if not GEMINI_API_KEY: missing.append("GEMINI_API_KEY")
    if not ADMIN_USERNAME: missing.append("ADMIN_USERNAME")
    if not ADMIN_PASSWORD: missing.append("ADMIN_PASSWORD")

    if missing:
        print(f"[CONFIGURACIÓN] Variables faltantes: {', '.join(missing)}")
    else:
        print(f"[OK] {APP_NAME} v{APP_VERSION} configurado con acceso administrador.")
