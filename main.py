# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.2
import os,secrets,time
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Dict,List,Optional
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from rules_engine import advisor
from flight_engine import engine as flight_engine
from source_registry import REGISTRY
from legal_disclaimer import manager as legal_manager
from schemas import *

BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","")
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","")
APP_BASE_URL=os.getenv("APP_BASE_URL","").rstrip("/")

APP_VERSION="8.0.2"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
OWNER="May Roga LLC"
PRICE_USD=15.99
SESSION_MINUTES=15
SESSION_SECONDS=SESSION_MINUTES*60
PAYMENT_TYPE="one_time"

ACTIVE_PAID_SESSIONS:Dict[str,float]={}
ADMIN_SESSIONS:Dict[str,float]={}
PAYMENT_SESSIONS:Dict[str,Dict[str,Any]]={}

app=FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=f"{APP_NAME} | {OWNER}"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

def now()->float:
    return time.time()

def new_token(prefix:str="tok")->str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"

def clean_sessions():
    t=now()
    for store in (ACTIVE_PAID_SESSIONS,ADMIN_SESSIONS):
        expired=[k for k,v in store.items() if v<=t]
        for k in expired:
            store.pop(k,None)

def session_active(token:str)->bool:
    clean_sessions()
    return bool(token and ACTIVE_PAID_SESSIONS.get(token,0)>now())

def admin_active(token:str)->bool:
    clean_sessions()
    return bool(token and ADMIN_SESSIONS.get(token,0)>now())

def service_token_from_request(request:Request)->str:
    return str(request.headers.get("X-Service-Token") or "").strip()

def admin_token_from_request(request:Request)->str:
    return str(request.headers.get("X-Admin-Token") or "").strip()

def require_session(request:Request)->str:
    clean_sessions()
    service=service_token_from_request(request)
    if session_active(service):
        return service
    admin=admin_token_from_request(request)
    if admin_active(admin):
        return admin
    raise HTTPException(status_code=401,detail="Active service session required")

def require_admin(request:Request)->str:
    token=admin_token_from_request(request)
    if not admin_active(token):
        raise HTTPException(status_code=401,detail="Administrator session required")
    return token

def lang_of(value:Any)->str:
    return "en" if str(value or "es").lower()=="en" else "es"

def model_data(payload:Any)->Dict[str,Any]:
    if hasattr(payload,"model_dump"):
        return payload.model_dump(exclude_none=True)
    if isinstance(payload,dict):
        return dict(payload)
    return {}

def source_dict(source:Any)->Dict[str,Any]:
    if hasattr(source,"to_dict"):
        return source.to_dict()
    if isinstance(source,dict):
        return source
    return {}

def error_response(message:str,status:int=400,code:str="error"):
    return JSONResponse(
        status_code=status,
        content={"success":False,"error":code,"message":message}
    )

def datetime_from_timestamp(value:Any)->str:
    try:
        if not value:
            return ""
        return datetime.fromtimestamp(float(value),tz=timezone.utc).isoformat()
    except Exception:
        return ""

def official_links(language:str="es")->List[Dict[str,Any]]:
    en=lang_of(language)=="en"
    ids=[
        "tsa",
        "faa_packsafe",
        "faa_batteries",
        "dviajeros",
        "evisa_cuba"
    ]
    out=[]
    for sid in ids:
        s=REGISTRY.get(sid)
        if not s:
            continue
        d=s.to_dict()
        d["verified"]=bool(s.verified)
        if en and sid=="dviajeros":
            d["notes"]="Official Cuban government source. Confirm current requirements directly."
        elif not en and sid=="dviajeros":
            d["notes"]="Fuente oficial cubana. Confirma directamente los requisitos actuales."
        elif en and sid=="evisa_cuba":
            d["notes"]="Official Cuban eVisa source. Confirm current eligibility and requirements directly."
        elif not en and sid=="evisa_cuba":
            d["notes"]="Fuente oficial cubana de eVisa. Confirma directamente la elegibilidad y los requisitos actuales."
        out.append(d)
    return out

def official_source_payload(language:str="es")->Dict[str,Any]:
    lang=lang_of(language)
    return {
        "success":True,
        "sources":official_links(lang),
        "language":lang,
        "next_action":(
            "Open the applicable official source and confirm the current requirement directly."
            if lang=="en" else
            "Abre la fuente oficial correspondiente y confirma directamente el requisito actual."
        )
    }

@app.get("/")
def root():
    index=STATIC_DIR/"index.html"
    if index.exists():
        return FileResponse(index)
    return {
        "app":APP_NAME,
        "version":APP_VERSION,
        "owner":OWNER
    }

@app.get("/health")
def health():
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":APP_VERSION
    }

@app.get("/api")
def api_root():
    return {
        "success":True,
        "app":APP_NAME,
        "version":APP_VERSION
    }

@app.get("/api/v1/meta")
def meta(language:str="es"):
    return {
        "success":True,
        "app_name":APP_NAME,
        "owner":OWNER,
        "version":APP_VERSION,
        "price_usd":PRICE_USD,
        "session_minutes":SESSION_MINUTES,
        "payment_type":PAYMENT_TYPE,
        "stripe_enabled":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "stripe_publishable_key":STRIPE_PUBLISHABLE_KEY,
        "rules_are_verified":False,
        "language":lang_of(language),
        "independent_service":True
    }

@app.get("/api/v1/legal")
def legal(language:str="es"):
    return legal_manager.to_dict(lang_of(language))

@app.get("/api/v1/config")
def config(language:str="es"):
    return {
        "success":True,
        "app_name":APP_NAME,
        "version":APP_VERSION,
        "owner":OWNER,
        "price_usd":PRICE_USD,
        "session_minutes":SESSION_MINUTES,
        "payment_type":PAYMENT_TYPE,
        "stripe_enabled":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "stripe_publishable_key":STRIPE_PUBLISHABLE_KEY,
        "language":lang_of(language),
        "admin_login_enabled":bool(ADMIN_USERNAME and ADMIN_PASSWORD)
    }

@app.get("/api/v1/official")
def official(language:str="es"):
    return official_source_payload(language)

@app.get("/api/v1/sources/official")
def sources_official(language:str="es"):
    return official_source_payload(language)

@app.get("/api/v1/rules")
def rules(language:str="es"):
    data=advisor.repo.to_dicts() if hasattr(advisor,"repo") else []
    return {
        "success":True,
        "version":getattr(advisor,"VERSION","8.0.1"),
        "rules":data,
        "verified":False,
        "language":lang_of(language)
    }

@app.post("/api/v1/admin/login",response_model=AdminLoginResponse)
def admin_login(payload:AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="Administrator access is not configured"
        )
    username=str(payload.username or "")
    password=str(payload.password or "")
    if not secrets.compare_digest(username,ADMIN_USERNAME) or not secrets.compare_digest(password,ADMIN_PASSWORD):
        raise HTTPException(
            status_code=401,
            detail="Invalid administrator credentials"
        )
    clean_sessions()
    token=new_token("admin")
    ADMIN_SESSIONS[token]=now()+SESSION_SECONDS
    return {
        "success":True,
        "token":token,
        "expires_at":datetime_from_timestamp(ADMIN_SESSIONS[token]),
        "message":"Administrator access activated"
    }

@app.post("/api/v1/admin/logout")
def admin_logout(request:Request):
    token=admin_token_from_request(request)
    ADMIN_SESSIONS.pop(token,None)
    return {"success":True}

@app.get("/api/v1/admin/status")
def admin_status(request:Request):
    token=admin_token_from_request(request)
    active=admin_active(token)
    return {
        "success":True,
        "active":active,
        "expires_at":datetime_from_timestamp(ADMIN_SESSIONS.get(token)) if active else ""
    }

@app.post("/api/v1/create-checkout-session",response_model=CreateCheckoutResponse)
def create_checkout_session(payload:CreateCheckoutRequest,request:Request):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503,detail="Stripe is not configured")
    if not STRIPE_PRICE_ID1:
        raise HTTPException(status_code=503,detail="Stripe price is not configured")
    try:
        base=APP_BASE_URL or str(request.base_url).rstrip("/")
        success_url=f"{base}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url=f"{base}/?payment=cancelled"
        return_path=str(getattr(payload,"return_path","") or "/")
        if not return_path.startswith("/") or return_path.startswith("//"):
            return_path="/"
        session=stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "app":APP_NAME,
                "owner":OWNER,
                "payment_type":PAYMENT_TYPE,
                "return_path":return_path
            }
        )
        return {
            "success":True,
            "session_id":session.id,
            "url":session.url or ""
        }
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to start the payment session"
        )

@app.post("/api/v1/verify-payment",response_model=PaymentVerifyResponse)
def verify_payment(payload:PaymentVerifyRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503,detail="Stripe is not configured")
    sid=str(payload.session_id or "").strip()
    if not sid:
        raise HTTPException(
            status_code=400,
            detail="Stripe session id is required"
        )
    try:
        checkout=stripe.checkout.Session.retrieve(sid)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to verify the payment session"
        )
    if getattr(checkout,"payment_status","")!="paid":
        raise HTTPException(
            status_code=402,
            detail="Payment has not been completed"
        )
    metadata=dict(getattr(checkout,"metadata",{}) or {})
    if metadata.get("app")!=APP_NAME or metadata.get("owner")!=OWNER:
        raise HTTPException(
            status_code=400,
            detail="Payment session does not belong to this service"
        )
    if sid in PAYMENT_SESSIONS:
        token=PAYMENT_SESSIONS[sid].get("token","")
        if token and session_active(token):
            return {
                "success":True,
                "token":token,
                "expires_at":datetime_from_timestamp(ACTIVE_PAID_SESSIONS[token]),
                "minutes":SESSION_MINUTES
            }
    token=new_token("service")
    expires=now()+SESSION_SECONDS
    ACTIVE_PAID_SESSIONS[token]=expires
    PAYMENT_SESSIONS[sid]={
        "token":token,
        "expires_at":expires,
        "created_at":now()
    }
    return {
        "success":True,
        "token":token,
        "expires_at":datetime_from_timestamp(expires),
        "minutes":SESSION_MINUTES
    }

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Stripe webhook is not configured"
        )
    body=await request.body()
    signature=request.headers.get("stripe-signature","")
    try:
        event=stripe.Webhook.construct_event(
            body,
            signature,
            STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook payload"
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook signature"
        )
    obj=event.get("data",{}).get("object",{}) or {}
    if event.get("type")=="checkout.session.completed":
        sid=obj.get("id")
        metadata=obj.get("metadata",{}) or {}
        if sid and metadata.get("app")==APP_NAME:
            PAYMENT_SESSIONS.setdefault(
                sid,
                {
                    "token":"",
                    "expires_at":0,
                    "created_at":now(),
                    "event":event.get("type")
                }
            )
    return {"received":True}

@app.get("/api/v1/session/{token}",response_model=SessionStatusResponse)
def session_by_token(token:str):
    active=session_active(token)
    return {
        "success":True,
        "active":active,
        "expires_at":datetime_from_timestamp(
            ACTIVE_PAID_SESSIONS.get(token)
        ) if active else "",
        "minutes_remaining":max(
            0,
            int((ACTIVE_PAID_SESSIONS.get(token,0)-now())/60)
        ) if active else 0
    }

@app.get("/api/v1/session",response_model=SessionStatusResponse)
def session_status(request:Request):
    service=service_token_from_request(request)
    if session_active(service):
        expires=ACTIVE_PAID_SESSIONS.get(service,0)
        return {
            "success":True,
            "active":True,
            "expires_at":datetime_from_timestamp(expires),
            "minutes_remaining":max(
                0,
                int((expires-now())/60)
            )
        }
    admin=admin_token_from_request(request)
    if admin_active(admin):
        expires=ADMIN_SESSIONS.get(admin,0)
        return {
            "success":True,
            "active":True,
            "expires_at":datetime_from_timestamp(expires),
            "minutes_remaining":max(
                0,
                int((expires-now())/60)
            )
        }
    return {
        "success":True,
        "active":False,
        "expires_at":"",
        "minutes_remaining":0
    }

@app.get("/api/v1/flight/sources")
def flight_sources(
    origin:str="",
    destination:str="",
    airline:str="",
    language:str="es"
):
    lang=lang_of(language)
    sources=flight_engine.source_cards(
        origin,
        destination,
        airline,
        lang
    )
    charter=[]
    if flight_engine.is_cuba_route(origin,destination):
        charter=flight_engine.charter_sources(lang)
    return {
        "success":True,
        "sources":sources,
        "charter_sources":charter,
        "airline_sources":(
            flight_engine.airline_sources(airline,lang)
            if airline else []
        ),
        "is_cuba_route":flight_engine.is_cuba_route(
            origin,
            destination
        )
    }

@app.get("/api/v1/sources/charter")
def source_charter(language:str="es"):
    lang=lang_of(language)
    return {
        "success":True,
        "sources":flight_engine.charter_sources(lang),
        "language":lang,
        "next_action":(
            "Open a provider and confirm current routes, dates, availability, baggage and ticket conditions directly."
            if lang=="en" else
            "Abre un proveedor y confirma directamente las rutas, fechas, disponibilidad, equipaje y condiciones del boleto."
        )
    }

@app.get("/api/v1/sources/search")
def source_search(
    q:str="",
    country:str="",
    airline:str="",
    destination:str="",
    source_type:str=""
):
    return {
        "success":True,
        "sources":[
            source_dict(s)
            for s in REGISTRY.search(
                q,
                country,
                airline,
                destination,
                source_type
            )
        ]
    }

@app.get("/api/v1/sources/route")
def source_route(
    origin:str="",
    destination:str="",
    airline:str="",
    language:str="es"
):
    lang=lang_of(language)
    return {
        "success":True,
        "sources":flight_engine.source_cards(
            origin,
            destination,
            airline,
            lang
        ),
        "charter_sources":(
            flight_engine.charter_sources(lang)
            if flight_engine.is_cuba_route(origin,destination)
            else []
        ),
        "is_cuba_route":flight_engine.is_cuba_route(
            origin,
            destination
        )
    }

@app.get("/api/v1/sources/baggage")
def source_baggage(
    origin:str="",
    destination:str="",
    airline:str="",
    language:str="es"
):
    lang=lang_of(language)
    return {
        "success":True,
        "sources":[
            flight_engine._source_card(s,lang)
            for s in REGISTRY.baggage_sources(
                origin,
                destination,
                airline
            )
        ]
    }

@app.get("/api/v1/cuba/sources")
def cuba_sources(
    origin:str="",
    destination:str="Cuba",
    airline:str="",
    language:str="es"
):
    return {
        "success":True,
        "sources":flight_engine.cuba_sources(
            origin,
            destination,
            airline,
            lang_of(language)
        )
    }

@app.get("/api/v1/cuba/official")
def cuba_official(language:str="es"):
    lang=lang_of(language)
    return {
        "success":True,
        "sources":flight_engine.cuba_sources(
            "United States",
            "Cuba",
            "",
            lang
        ),
        "important":(
            [
                "Check entry and exit requirements.",
                "Check passport and nationality requirements.",
                "Check visa or eVisa requirements.",
                "Complete D’Viajeros when required.",
                "Check baggage and prohibited-item rules."
            ]
            if lang=="en"
            else
            [
                "Revisa los requisitos de entrada y salida.",
                "Revisa los requisitos de pasaporte y nacionalidad.",
                "Revisa los requisitos de visa o eVisa.",
                "Completa D’Viajeros cuando corresponda.",
                "Revisa las reglas de equipaje y artículos prohibidos."
            ]
        )
    }

@app.post("/api/v1/flight/search-external",response_model=FlightSearchResponse)
def flight_search_external(
    payload:FlightSearchRequest,
    request:Request
):
    require_session(request)
    return flight_engine.search(**model_data(payload))

@app.post("/api/v1/flight/understand",response_model=FlightUnderstandResponse)
def flight_understand(
    payload:FlightContext,
    request:Request
):
    require_session(request)
    data=model_data(payload)
    return flight_engine.understand(
        data,
        language=lang_of(data.get("language","es"))
    )

@app.post("/api/v1/consultar-articulo",response_model=ItemCheckResponse)
def consultar_articulo(
    payload:ItemCheckRequest,
    request:Request
):
    require_session(request)
    data=model_data(payload)
    try:
        result=advisor.advise(
            item=data.get("item",""),
            baggage_type=data.get("baggage_type"),
            airline=data.get("airline",""),
            destination=data.get("destination",""),
            origin=data.get("origin",""),
            cabin=data.get("cabin",""),
            fare=data.get("fare",""),
            language=lang_of(data.get("language","es"))
        )
    except TypeError:
        result=advisor.advise_item(
            data.get("item",""),
            baggage_type=data.get("baggage_type"),
            airline=data.get("airline",""),
            destination=data.get("destination",""),
            language=lang_of(data.get("language","es"))
        )
    return result

@app.post("/api/v1/item/teach",response_model=TeachTermResponse)
def teach_term(
    payload:TeachTermRequest,
    request:Request
):
    require_session(request)
    lang=lang_of(payload.language)
    try:
        result=advisor.explain_term(
            payload.term,
            language=lang
        )
    except TypeError:
        result=advisor.explain_term(payload.term)
    if isinstance(result,dict):
        return result
    return {
        "success":True,
        "term":payload.term,
        "explanation":str(result),
        "language":lang
    }

@app.post("/api/v1/guide",response_model=GuideResponse)
def guide(
    payload:GuideRequest,
    request:Request
):
    require_session(request)
    data=model_data(payload)
    lang=lang_of(data.get("language","es"))
    topic=str(data.get("topic") or "")
    flight=data.get("flight") or {}

    if hasattr(flight,"model_dump"):
        flight=flight.model_dump(exclude_none=True)

    if not isinstance(flight,dict):
        flight={}

    origin=str(flight.get("origin") or "")
    destination=str(flight.get("destination") or "")

    if lang=="en":
        steps=[
            {
                "id":"flight",
                "title":"1. Flight",
                "text":"Confirm the actual airline, route, date, fare and itinerary."
            },
            {
                "id":"documents",
                "title":"2. Documents",
                "text":"Review passport, nationality, visa and destination-entry requirements."
            },
            {
                "id":"entry_exit",
                "title":"3. Entry and exit",
                "text":"Check the current official entry and exit requirements for the destination."
            },
            {
                "id":"baggage",
                "title":"4. Baggage",
                "text":"Check carry-on, checked baggage, prohibited items and airline-specific conditions."
            },
            {
                "id":"declaration",
                "title":"5. Forms",
                "text":"Complete required official travel forms such as D’Viajeros when applicable."
            },
            {
                "id":"confirm",
                "title":"6. Final confirmation",
                "text":"Confirm the final conditions directly with the applicable official sources before traveling."
            }
        ]
        cuba=[
            "Check Cuban entry and exit requirements.",
            "Check passport rules according to nationality and any Cuban dual-nationality situation.",
            "Check passport validity and required travel documents.",
            "Check visa or eVisa requirements.",
            "Complete D’Viajeros when required.",
            "Check baggage allowances and prohibited items.",
            "Confirm the final requirements directly before travel."
        ]
    else:
        steps=[
            {
                "id":"flight",
                "title":"1. Vuelo",
                "text":"Confirma la aerolínea, ruta, fecha, tarifa e itinerario reales."
            },
            {
                "id":"documents",
                "title":"2. Documentos",
                "text":"Revisa pasaporte, nacionalidad, visa y requisitos de entrada del destino."
            },
            {
                "id":"entry_exit",
                "title":"3. Entrada y salida",
                "text":"Revisa los requisitos oficiales actuales de entrada y salida del destino."
            },
            {
                "id":"baggage",
                "title":"4. Equipaje",
                "text":"Revisa equipaje de mano, equipaje facturado, artículos prohibidos y condiciones de la aerolínea."
            },
            {
                "id":"declaration",
                "title":"5. Formularios",
                "text":"Completa los formularios oficiales de viaje que correspondan, como D’Viajeros."
            },
            {
                "id":"confirm",
                "title":"6. Confirmación final",
                "text":"Confirma las condiciones finales directamente con las fuentes oficiales correspondientes antes de viajar."
            }
        ]
        cuba=[
            "Revisa los requisitos cubanos de entrada y salida.",
            "Revisa las reglas de pasaporte según la nacionalidad y cualquier situación de doble nacionalidad cubana.",
            "Revisa la vigencia del pasaporte y los documentos de viaje requeridos.",
            "Revisa los requisitos de visa o eVisa.",
            "Completa D’Viajeros cuando corresponda.",
            "Revisa el equipaje permitido y los artículos prohibidos.",
            "Confirma los requisitos finales directamente antes del viaje."
        ]

    is_cuba=flight_engine.is_cuba_route(
        origin,
        destination
    )

    return {
        "success":True,
        "language":lang,
        "topic":topic,
        "steps":steps,
        "cuba_steps":cuba if is_cuba else [],
        "official_sources":official_links(lang),
        "legal_notice":legal_manager.short_notice(lang),
        "next_action":(
            "Confirm the final requirements directly with the applicable official sources."
            if lang=="en"
            else
            "Confirma los requisitos finales directamente con las fuentes oficiales correspondientes."
        )
    }

@app.get("/api/v1/admin/protected")
def admin_protected(request:Request):
    require_admin(request)
    return {
        "success":True,
        "message":"Administrator access active"
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(
    request:Request,
    exc:HTTPException
):
    detail=exc.detail
    if isinstance(detail,dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success":False,
            "error":"http_error",
            "message":str(detail)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(
    request:Request,
    exc:Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "success":False,
            "error":"server_error",
            "message":"An unexpected server error occurred."
        }
    )
