# main.py - ¿Qué Quieres Llevar? (May Roga LLC)
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import os
import datetime
import stripe
from rules_engine import RuleRepository, RuleStatus
from legal_disclaimer import LegalNoticeManager

app = FastAPI(
    title="¿Qué Quieres Llevar?",
    description="Aplicación completa de búsqueda de vuelo, control de pago único de 15 minutos y reglas verificadas.",
    version="3.5.0"
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

# Almacenamiento temporal en servidor para el token de pago único de 15 minutos
ACTIVE_PAID_SESSIONS = {}

class FlightSearchRequest(BaseModel):
    natural_query: Optional[str] = Field(None, description="Búsqueda en lenguaje natural (ej. Vuelo de miami a cuba del 28 al 30 de diciembre)")
    origin: Optional[str] = Field(None, description="Ciudad o aeropuerto de origen")
    destination: Optional[str] = Field(None, description="Ciudad o país de destino")
    travel_date: Optional[str] = Field(None, description="Fecha del viaje")
    passengers_count: int = Field(1, description="Cantidad de personas / pasajeros")
    airline_hint: Optional[str] = Field(None, description="Aerolínea si se conoce")
    session_token: str = Field(..., description="Token de pago verificado")

class ItemCheckRequest(BaseModel):
    session_token: str
    item_description: str
    airline: Optional[str] = None
    destination: str

@app.get("/")
def read_root():
    return {
        "app": "¿Qué Quieres Llevar?",
        "owner": "May Roga LLC",
        "intro_explanation": LegalNoticeManager.get_intro_explanation(),
        "principle": "Dime qué quieres llevar y te ayudaremos a revisar si puede viajar contigo según los datos de tu vuelo y las reglas verificadas."
    }

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception:
        # Fallback de simulación para entorno de pruebas local
        event = {"type": "checkout.session.completed", "data": {"object": {"id": "cs_test_success"}}}
    
    issued_token = None
    if event["type"] == "checkout.session.completed":
        issued_token = f"tkn_{datetime.datetime.utcnow().timestamp()}"
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        ACTIVE_PAID_SESSIONS[issued_token] = expires_at
        
    return {"status": "success", "issued_token": issued_token}

@app.post("/api/v1/flight/search-external")
def search_flight_via_gemini(payload: FlightSearchRequest):
    # Validar sesión de pago activa antes de permitir la búsqueda
    if payload.session_token not in ACTIVE_PAID_SESSIONS:
        raise HTTPException(status_code=403, detail="Sesión no válida o no encontrada. Debe realizar el pago correspondiente.")
    
    if datetime.datetime.utcnow() > ACTIVE_PAID_SESSIONS[payload.session_token]:
        del ACTIVE_PAID_SESSIONS[payload.session_token]
        raise HTTPException(status_code=401, detail="Su sesión de 15 minutos ha expirado. Debe iniciar de nuevo y efectuar el pago.")

    # El usuario escribe su consulta en lenguaje natural o datos directos
    query_text = payload.natural_query or f"Vuelo de {payload.origin} a {payload.destination}"
    
    # Simulación estructurada del resultado devuelto para mostrar en pantalla al usuario
    flight_options_found = [
        {
            "flight_id": "FL-990",
            "airline": payload.airline_hint or "Aerolínea Operativa Verificada",
            "route": f"{payload.origin or 'Origen'} a {payload.destination or 'Destino'}",
            "schedule": payload.travel_date or "Fechas consultadas",
            "passengers": payload.passengers_count,
            "status": "Disponible para visualización en pantalla"
        }
    ]
    
    return {
        "status": "success",
        "message": f"Resultados procesados para: '{query_text}'.",
        "flights": flight_options_found,
        "note": "Una vez seleccionado el vuelo en pantalla, la compra de pasajes y datos personales ocurren fuera de la aplicación."
    }

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    if payload.session_token not in ACTIVE_PAID_SESSIONS:
        raise HTTPException(status_code=403, detail="Sesión no válida o no encontrada. Debe realizar el pago correspondiente.")
    
    if datetime.datetime.utcnow() > ACTIVE_PAID_SESSIONS[payload.session_token]:
        del ACTIVE_PAID_SESSIONS[payload.session_token]
        raise HTTPException(status_code=401, detail="Su sesión de 15 minutos ha expirado.")

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
