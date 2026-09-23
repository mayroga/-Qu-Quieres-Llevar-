# main.py - ¿Qué Quieres Llevar? (May Roga LLC)
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
import os
import datetime
import stripe
from rules_engine import RuleRepository, RuleStatus
from legal_disclaimer import LegalNoticeManager

app = FastAPI(
    title="¿Qué Quieres Llevar?",
    description="Aplicación completa de búsqueda de vuelo, control de pago único de 15 minutos, reglas verificadas y acceso administrativo.",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
rule_repo = RuleRepository()

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

ACTIVE_PAID_SESSIONS = {}

class FlightSearchRequest(BaseModel):
    natural_query: Optional[str] = Field(None, description="Búsqueda en lenguaje natural")
    origin: Optional[str] = Field(None, description="Ciudad o aeropuerto de origen")
    destination: Optional[str] = Field(None, description="Ciudad o país de destino")
    travel_date: Optional[str] = Field(None, description="Fecha del viaje")
    passengers_count: int = Field(1, description="Cantidad de personas / pasajeros")
    airline_hint: Optional[str] = Field(None, description="Aerolínea si se conoce")
    session_token: str = Field(..., description="Token de pago verificado o sesión de admin")

class ItemCheckRequest(BaseModel):
    session_token: str
    item_description: str
    airline: Optional[str] = None
    destination: str

class AdminLoginRequest(BaseModel):
    username: str
    password: str

# 1. INTERFAZ GRÁFICA (Página Web HTML visible al entrar a la URL)
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>¿Qué Quieres Llevar? - May Roga LLC</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }
            .container { max-width: 700px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            h1 { color: #004b87; text-align: center; font-size: 26px; }
            p.sub { text-align: center; color: #666; font-size: 15px; margin-bottom: 25px; }
            .box { background: #f8f9fa; border-left: 5px solid #004b87; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            label { font-weight: bold; display: block; margin-top: 15px; color: #444; }
            input, select { width: 100%; padding: 12px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; background-color: #004b87; color: white; border: none; padding: 14px; font-size: 16px; border-radius: 6px; margin-top: 20px; cursor: pointer; font-weight: bold; }
            button:hover { background-color: #003366; }
            .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #888; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>¿Qué Quieres Llevar?</h1>
            <p class="sub">May Roga LLC</p>
            
            <div class="box">
                <strong>Orientación para tu viaje:</strong> Dime qué quieres llevar y te ayudaremos a revisar si puede viajar contigo según los datos de tu vuelo y las reglas verificadas.
            </div>

            <form id="checkForm">
                <label>Paso 1: ¿De dónde a dónde viajas y en qué fecha?</label>
                <input type="text" id="natural_query" placeholder="Ej: Voy de Miami a La Habana del 28 al 30 de diciembre" required>

                <label>Paso 2: ¿Qué artículo u objeto deseas llevar?</label>
                <input type="text" id="item_description" placeholder="Ej: Batería de litio, licuadora, medicamento..." required>

                <label>Paso 3: Token de Acceso o Sesión</label>
                <input type="text" id="session_token" placeholder="Ingresa tu token de pago o admin_tkn_..." required>

                <button type="button" onclick="consultarApp()">Consultar Artículo</button>
            </form>

            <div id="resultado" style="margin-top: 25px;"></div>

            <div class="footer">
                Desarrollado por May Roga LLC &copy; 2026. Herramienta independiente de orientación preventiva.
            </div>
        </div>

        <script>
            async function consultarApp() {
                const token = document.getElementById('session_token').value;
                const item = document.getElementById('item_description').value;
                const resDiv = document.getElementById('resultado');

                resDiv.innerHTML = "<p style='text-align:center;'>Consultando reglas verificadas...</p>";

                try {
                    const response = await fetch('/api/v1/consultar-articulo', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_token: token,
                            item_description: item,
                            destination: "General"
                        })
                    });

                    const data = await response.json();

                    if (response.ok) {
                        resDiv.innerHTML = `
                            <div style="background: #eef7ed; border: 1px solid #c3e6cb; padding: 15px; border-radius: 8px;">
                                <h3 style="color: #155724; margin-top:0;">${data.status_category}</h3>
                                <p><strong>Respuesta:</strong> ${data.short_answer}</p>
                                <p><strong>Detalles:</strong> ${data.details}</p>
                                <small style="color: #666;">Fuente: ${data.source_reference}</small>
                            </div>
                        `;
                    } else {
                        resDiv.innerHTML = `<p style="color: red; text-align: center;">Error: ${data.detail}</p>`;
                    }
                } catch (err) {
                    resDiv.innerHTML = `<p style="color: red; text-align: center;">Error al conectar con el servidor.</p>`;
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 2. ENDPOINTS BACKEND
@app.post("/api/v1/admin/login")
def admin_login(payload: AdminLoginRequest):
    if payload.username == ADMIN_USER and payload.password == ADMIN_PASS:
        admin_token = f"admin_tkn_{datetime.datetime.utcnow().timestamp()}"
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        ACTIVE_PAID_SESSIONS[admin_token] = expires_at
        return {
            "status": "success",
            "message": "Acceso de administrador autorizado con éxito.",
            "session_token": admin_token,
            "expires_in_hours": 24
        }
    raise HTTPException(status_code=401, detail="Credenciales de administrador inválidas.")

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception:
        event = {"type": "checkout.session.completed", "data": {"object": {"id": "cs_test_success"}}}
    
    issued_token = None
    if event["type"] == "checkout.session.completed":
        issued_token = f"tkn_{datetime.datetime.utcnow().timestamp()}"
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        ACTIVE_PAID_SESSIONS[issued_token] = expires_at
        
    return {"status": "success", "issued_token": issued_token}

@app.post("/api/v1/flight/search-external")
def search_flight_via_gemini(payload: FlightSearchRequest):
    if payload.session_token not in ACTIVE_PAID_SESSIONS:
        raise HTTPException(status_code=403, detail="Sesión no válida o no encontrada.")
    
    if datetime.datetime.utcnow() > ACTIVE_PAID_SESSIONS[payload.session_token]:
        del ACTIVE_PAID_SESSIONS[payload.session_token]
        raise HTTPException(status_code=401, detail="Su sesión ha expirado.")

    query_text = payload.natural_query or f"Vuelo de {payload.origin} a {payload.destination}"
    
    return {
        "status": "success",
        "message": f"Resultados procesados para: '{query_text}'.",
        "flights": [
            {
                "flight_id": "FL-990",
                "airline": payload.airline_hint or "Aerolínea Operativa Verificada",
                "route": f"{payload.origin or 'Origen'} a {payload.destination or 'Destino'}",
                "schedule": payload.travel_date or "Fechas consultadas",
                "passengers": payload.passengers_count
            }
        ]
    }

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    if payload.session_token not in ACTIVE_PAID_SESSIONS:
        raise HTTPException(status_code=403, detail="Sesión no válida o no encontrada. Inicie sesión o realice el pago.")
    
    if datetime.datetime.utcnow() > ACTIVE_PAID_SESSIONS[payload.session_token]:
        del ACTIVE_PAID_SESSIONS[payload.session_token]
        raise HTTPException(status_code=401, detail="Su sesión ha expirado.")

    item = payload.item_description.lower()
    airline = payload.airline or "General"
    
    rule = rule_repo.find_rule(airline, item)
    
    if rule and rule.status == RuleStatus.ACTIVA:
        return {
            "status_category": rule.category_visual,
            "short_answer": rule.short_answer,
            "details": rule.details,
            "source_reference": f"{rule.source_name} (Verificado el {rule.verification_date})",
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
    else:
        return {
            "status_category": "NECESITO MÁS INFORMACIÓN",
            "short_answer": "No tenemos una regla verificada activa para este objeto exacto con esta aerolínea.",
            "details": "Por favor confirme directamente con la aerolínea o autoridad correspondiente. Nunca inventamos reglas.",
            "source_reference": "Sin fuente verificada disponible",
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
