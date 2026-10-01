# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v6.0.0
from __future__ import annotations
import os,secrets,time
from pathlib import Path
from typing import Any,Dict,Optional
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from schemas import (
    AppMetaResponse,AdminLoginRequest,AdminLoginResponse,CreateCheckoutRequest,
    CreateCheckoutResponse,PaymentVerifyRequest,PaymentVerifyResponse,
    FlightSearchRequest,FlightSearchResponse,FlightResult,FlightContext,
    ItemCheckRequest,ItemCheckResponse,TeachTermRequest,TeachTermResponse,
    GuideRequest,GuideResponse,SessionStatusResponse,LegalResponse,
    OfficialSourcesResponse,OfficialLink,CategoryVisualEnum
)
from rules_engine import rule_repo,BaggageAdvisor
from legal_disclaimer import LegalNoticeManager

APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="6.0.0"
OWNER="May Roga LLC"
SESSION_MINUTES=15
PRICE_USD=15.99
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","").strip()
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","").strip()
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()

if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

app=FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Servicio independiente de orientación y preparación de viajes de May Roga LLC.",
    docs_url="/docs",
    redoc_url="/redoc"
)

if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

ACTIVE_PAID_SESSIONS:Dict[str,Dict[str,Any]]={}
ADMIN_SESSIONS:Dict[str,float]={}
PENDING_CHECKOUTS:Dict[str,float]={}

legal=LegalNoticeManager()
advisor=BaggageAdvisor()

def now()->float:
    return time.time()

def make_token(n:int=32)->str:
    return secrets.token_urlsafe(n)

def clean_text(value:Any,max_len:int=1000)->str:
    if value is None:return ""
    return str(value).strip()[:max_len]

def session_data(token:str)->Optional[Dict[str,Any]]:
    data=ACTIVE_PAID_SESSIONS.get(token)
    if not data:return None
    if float(data.get("expires_at",0))<=now():
        ACTIVE_PAID_SESSIONS.pop(token,None)
        return None
    return data

def active_session(token:Optional[str])->Optional[Dict[str,Any]]:
    if not token:return None
    return session_data(token)

def get_service_token(request:Request)->Optional[str]:
    token=request.query_params.get("session_token") or request.headers.get("X-Service-Token")
    if token:return token.strip()
    auth=request.headers.get("Authorization","")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None

def require_service(request:Request)->str:
    token=get_service_token(request)
    if not active_session(token):
        raise HTTPException(403,"Se requiere una sesión activa del servicio.")
    return token

def create_paid_session(stripe_session_id:Optional[str]=None)->str:
    token=make_token()
    expires=now()+SESSION_MINUTES*60
    ACTIVE_PAID_SESSIONS[token]={
        "created_at":now(),
        "expires_at":expires,
        "stripe_session_id":stripe_session_id,
        "owner":OWNER
    }
    return token

def cleanup_sessions():
    current=now()
    for token,data in list(ACTIVE_PAID_SESSIONS.items()):
        if float(data.get("expires_at",0))<=current:
            ACTIVE_PAID_SESSIONS.pop(token,None)
    for token,expires in list(ADMIN_SESSIONS.items()):
        if expires<=current:
            ADMIN_SESSIONS.pop(token,None)
    for sid,expires in list(PENDING_CHECKOUTS.items()):
        if expires<=current:
            PENDING_CHECKOUTS.pop(sid,None)

def localized(es:str,en:str,language:str)->str:
    return en if language=="en" else es

def normalize_language(language:str)->str:
    return "en" if str(language).lower()=="en" else "es"

def official_sources()->list[OfficialLink]:
    return [
        OfficialLink(
            name="TSA",
            url="https://www.tsa.gov/travel/security-screening/whatcanibring",
            description="Fuente oficial de Estados Unidos para revisar artículos y seguridad de equipaje.",
            authority="Transportation Security Administration",
            country="US"
        ),
        OfficialLink(
            name="FAA",
            url="https://www.faa.gov/hazmat/packsafe",
            description="Información oficial sobre artículos y materiales regulados en vuelos.",
            authority="Federal Aviation Administration",
            country="US"
        )
    ]

@app.on_event("startup")
async def startup():
    cleanup_sessions()

@app.get("/",include_in_schema=False)
async def root():
    index=STATIC_DIR/"index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({
        "app":APP_NAME,
        "owner":OWNER,
        "version":APP_VERSION,
        "message":"Interfaz no encontrada. La API está disponible."
    })

@app.get("/health")
async def health():
    cleanup_sessions()
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":APP_VERSION,
        "owner":OWNER,
        "stripe_configured":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "admin_configured":bool(ADMIN_USERNAME and ADMIN_PASSWORD),
        "rules_active":rule_repo.count("active"),
        "rules_pending":rule_repo.count("pending")
    }

@app.get("/ping",include_in_schema=False)
async def ping():
    return {"status":"ok"}

@app.get("/api/v1/meta",response_model=AppMetaResponse)
async def meta():
    return AppMetaResponse(
        app_name=APP_NAME,
        version=APP_VERSION,
        owner=OWNER,
        session_minutes=SESSION_MINUTES,
        payment_type="one_time",
        price_usd=PRICE_USD,
        ai_rule_authority="interpretation_only",
        rules_are_verified=False,
        legal_version=LegalNoticeManager.VERSION,
        independent_service=True,
        booking_enabled=False,
        ticket_sales_enabled=False
    )

@app.get("/api/v1/legal",response_model=LegalResponse)
async def legal_endpoint():
    return LegalResponse(
        success=True,
        version=LegalNoticeManager.VERSION,
        owner=OWNER,
        app_name=APP_NAME,
        notice=legal.full_notice(),
        short_notice=legal.short_notice(),
        source_notice=legal.source_notice()
    )

@app.get("/api/v1/official",response_model=OfficialSourcesResponse)
async def official_endpoint():
    return OfficialSourcesResponse(success=True,sources=official_sources())

@app.post("/api/v1/admin/login",response_model=AdminLoginResponse)
async def admin_login(payload:AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(503,"La administración no está configurada.")
    if not secrets.compare_digest(payload.username,ADMIN_USERNAME) or not secrets.compare_digest(payload.password,ADMIN_PASSWORD):
        raise HTTPException(401,"Credenciales incorrectas.")
    token=make_token()
    ADMIN_SESSIONS[token]=now()+60*60
    return AdminLoginResponse(success=True,token=token,message="Acceso administrativo autorizado.")

@app.post("/api/v1/create-checkout-session",response_model=CreateCheckoutResponse)
async def create_checkout(request:Request,payload:CreateCheckoutRequest):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1:
        raise HTTPException(503,"El pago todavía no está configurado.")
    base_url=str(request.base_url).rstrip("/")
    return_path=clean_text(payload.return_path,300)
    if not return_path.startswith("/"):
        return_path="/"
    success_url=f"{base_url}{return_path}?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url=f"{base_url}{return_path}?payment=cancelled"
    try:
        checkout=stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],
            success_url=success_url,
            cancel_url=cancel_url,
            customer_creation="if_required",
            metadata={"app":APP_NAME,"owner":OWNER,"service_minutes":str(SESSION_MINUTES)}
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(502,"No fue posible crear la sesión de pago.") from exc
    PENDING_CHECKOUTS[checkout.id]=now()+3600
    return CreateCheckoutResponse(
        success=True,
        checkout_url=checkout.url,
        session_id=checkout.id,
        message="Sesión de pago creada."
    )

@app.post("/api/v1/payment/verify",response_model=PaymentVerifyResponse)
async def verify_payment(payload:PaymentVerifyRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503,"Stripe no está configurado.")
    try:
        checkout=stripe.checkout.Session.retrieve(payload.session_id)
    except stripe.error.StripeError as exc:
        raise HTTPException(502,"No fue posible verificar el pago.") from exc
    paid=checkout.payment_status=="paid"
    if not paid:
        return PaymentVerifyResponse(
            success=True,
            paid=False,
            message="El pago todavía no aparece como completado."
        )
    for token,data in ACTIVE_PAID_SESSIONS.items():
        if data.get("stripe_session_id")==checkout.id and data.get("expires_at",0)>now():
            return PaymentVerifyResponse(
                success=True,
                paid=True,
                service_token=token,
                expires_at=str(data["expires_at"]),
                message="Pago confirmado. Sesión activa."
            )
    token=create_paid_session(checkout.id)
    data=ACTIVE_PAID_SESSIONS[token]
    PENDING_CHECKOUTS.pop(checkout.id,None)
    return PaymentVerifyResponse(
        success=True,
        paid=True,
        service_token=token,
        expires_at=str(data["expires_at"]),
        message="Pago confirmado. Sesión activa."
    )

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    payload=await request.body()
    signature=request.headers.get("stripe-signature","")
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(503,"Webhook no configurado.")
    try:
        event=stripe.Webhook.construct_event(payload,signature,STRIPE_WEBHOOK_SECRET)
    except ValueError as exc:
        raise HTTPException(400,"Webhook inválido.") from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(400,"Firma del webhook inválida.") from exc
    if event["type"]=="checkout.session.completed":
        obj=event["data"]["object"]
        if obj.get("payment_status")=="paid":
            PENDING_CHECKOUTS.pop(obj.get("id",""),None)
    return {"received":True}

@app.get("/api/v1/session/{session_token}",response_model=SessionStatusResponse)
async def session_status(session_token:str):
    cleanup_sessions()
    data=session_data(session_token)
    if not data:
        return SessionStatusResponse(
            active=False,
            token=session_token,
            remaining_seconds=0,
            message=legal.session_expired_message()
        )
    remaining=max(0,int(float(data["expires_at"])-now()))
    return SessionStatusResponse(
        active=True,
        token=session_token,
        remaining_seconds=remaining,
        expires_at=str(data["expires_at"]),
        message="Sesión activa."
    )

@app.delete("/api/v1/session/{session_token}")
async def delete_session(session_token:str):
    removed=ACTIVE_PAID_SESSIONS.pop(session_token,None) is not None
    return {"success":True,"cleared":removed,"message":"Sesión cerrada."}

@app.post("/api/v1/flight/understand")
async def understand_flight(request:Request,payload:FlightContext):
    require_service(request)
    return {
        "success":True,
        "flight":payload.model_dump(),
        "message":localized(
            "Usa estos datos para entender tu viaje. La aplicación no los convierte en una reserva ni confirma información que no tenga fuente.",
            "Use these details to understand your trip. The application does not turn them into a booking or confirm information without a source.",
            "en"
        ),
        "verified":payload.verified,
        "next_action":localized(
            "Confirma los datos en la fuente oficial de la aerolínea antes de viajar.",
            "Confirm the details on the airline's official source before traveling.",
            "en"
        )
    }

@app.post("/api/v1/flight/search-external",response_model=FlightSearchResponse)
async def search_external_flights(request:Request,payload:FlightSearchRequest):
    require_service(request)
    origin=clean_text(payload.origin,120)
    destination=clean_text(payload.destination,120)
    if not origin or not destination:
        raise HTTPException(422,"Indica origen y destino.")
    return FlightSearchResponse(
        success=True,
        results=[],
        message=localized(
            "La aplicación no inventa vuelos ni precios. Para confirmar vuelos disponibles debes revisar una fuente de vuelos o la aerolínea correspondiente.",
            "The application does not invent flights or prices. To confirm available flights, review a flight source or the relevant airline.",
            payload.language
        ),
        source=None,
        verified=False,
        official_source=False,
        next_action=localized(
            "Busca el vuelo en la fuente oficial y trae sus datos aquí para aprender a interpretarlos.",
            "Find the flight on the official source and bring its details here to learn how to interpret them.",
            payload.language
        )
    )

@app.post("/api/v1/item/teach",response_model=TeachTermResponse)
async def teach_term(request:Request,payload:TeachTermRequest):
    require_service(request)
    term=clean_text(payload.term,150)
    explanation=advisor.explain_term(term,payload.language)
    if not explanation:
        explanation=localized(
            f'Busca "{term}" en la página oficial de tu aerolínea. Si aparece, significa que debes revisar sus condiciones específicas antes de viajar.',
            f'Look for "{term}" on your airline\'s official website. If it appears, review its specific conditions before traveling.',
            payload.language
        )
    return TeachTermResponse(
        success=True,
        term=term,
        explanation=explanation,
        example=None,
        next_action=localized(
            "Si este término aparece en tu vuelo, revisa su significado y después confirma la regla oficial.",
            "If this term appears in your flight, learn its meaning and then confirm the official rule.",
            payload.language
        )
    )

@app.post("/api/v1/consultar-articulo",response_model=ItemCheckResponse)
async def check_item(request:Request,payload:ItemCheckRequest):
    require_service(request)
    flight=payload.flight.model_dump() if payload.flight else {}
    result=advisor.advise(
        payload.item,
        flight=flight,
        baggage_type=payload.baggage_type.value if payload.baggage_type else None,
        language=payload.language
    )
    if not isinstance(result,dict):
        result={}
    category=result.get("category",CategoryVisualEnum.REVIEW.value)
    try:
        category=CategoryVisualEnum(category)
    except ValueError:
        category=CategoryVisualEnum.REVIEW
    conditions=result.get("conditions") or []
    missing=result.get("missing_information") or []
    source=result.get("source")
    source_name=result.get("source_name")
    verified=bool(result.get("verified",False))
    official_link=None
    if source:
        official_link=OfficialLink(
            name=source_name or "Fuente oficial",
            url=str(source),
            description="Fuente indicada para confirmar la información.",
            verified=verified
        )
    return ItemCheckResponse(
        success=True,
        item=payload.item,
        category=category,
        explanation=result.get("explanation") or localized(
            "Este artículo requiere revisión específica antes de viajar.",
            "This item requires specific review before traveling.",
            payload.language
        ),
        baggage_place=result.get("baggage_place"),
        conditions=conditions,
        missing_information=missing,
        source=source,
        source_name=source_name,
        verified=verified,
        verification_date=result.get("verification_date"),
        official_link=official_link,
        next_action=result.get("next_action") or localized(
            "Confirma la regla en la fuente oficial antes de preparar la maleta.",
            "Confirm the rule on the official source before packing.",
            payload.language
        ),
        legal_notice=legal.short_notice()
    )

@app.post("/api/v1/guide",response_model=GuideResponse)
async def guide(request:Request,payload:GuideRequest):
    require_service(request)
    lang=payload.language
    topic=clean_text(payload.topic,150).lower()
    if payload.flight and payload.flight.connection:
        title=localized("TIENES UNA ESCALA O CONEXIÓN","YOU HAVE A STOP OR CONNECTION",lang)
        steps=[
            localized("Baja del primer avión.","Get off the first aircraft.",lang),
            localized("Busca las señales de Conexiones o Connections.","Look for Connections signs.",lang),
            localized("Confirma si debes cambiar de avión.","Confirm whether you must change aircraft.",lang),
            localized("Revisa qué ocurre con tu equipaje.","Check what happens to your baggage.",lang),
            localized("Confirma seguridad, inmigración o aduana si corresponde.","Confirm security, immigration, or customs if applicable.",lang),
            localized("Busca la puerta de tu siguiente vuelo.","Find the gate for your next flight.",lang)
        ]
    elif "equip" in topic or "maleta" in topic or "baggage" in topic:
        title=localized("PREPARA TU EQUIPAJE","PREPARE YOUR BAGGAGE",lang)
        steps=[
            localized("Identifica qué tipo de equipaje permite tu vuelo.","Identify what type of baggage your flight allows.",lang),
            localized("Separa lo que quieres llevar contigo.","Separate what you want to carry with you.",lang),
            localized("Revisa cada artículo que pueda tener una restricción.","Review each item that may have a restriction.",lang),
            localized("Confirma peso, medidas y condiciones en la fuente oficial.","Confirm weight, dimensions, and conditions on the official source.",lang),
            localized("Guarda los documentos importantes contigo.","Keep important documents with you.",lang)
        ]
    else:
        title=localized("PREPARA TU VIAJE PASO A PASO","PREPARE YOUR TRIP STEP BY STEP",lang)
        steps=[
            localized("Entiende tu vuelo.","Understand your flight.",lang),
            localized("Revisa si tienes escala o conexión.","Check whether you have a stop or connection.",lang),
            localized("Entiende tu equipaje.","Understand your baggage.",lang),
            localized("Revisa los artículos que quieres llevar.","Review the items you want to bring.",lang),
            localized("Prepara tus documentos.","Prepare your documents.",lang),
            localized("Confirma la información en la fuente oficial.","Confirm the information on the official source.",lang)
        ]
    return GuideResponse(
        success=True,
        title=title,
        steps=steps,
        next_action=localized(
            "Haz el primer paso y después continúa con el siguiente.",
            "Do the first step and then continue with the next one.",
            lang
        ),
        official_links=official_sources()
    )

@app.get("/api/v1/rules")
async def rules_summary(request:Request):
    token=get_service_token(request)
    if not active_session(token):
        raise HTTPException(403,"Se requiere una sesión activa.")
    return {
        "success":True,
        "active_rules":rule_repo.count("active"),
        "pending_rules":rule_repo.count("pending"),
        "message":"Las reglas pendientes no se presentan como reglas confirmadas."
    }

@app.get("/api/v1/config")
async def public_config():
    return {
        "app":{
            "name":APP_NAME,
            "version":APP_VERSION,
            "brand":OWNER,
            "price_usd":PRICE_USD,
            "session_minutes":SESSION_MINUTES
        },
        "service":{
            "payment_type":"one_time",
            "booking":False,
            "ticket_sales":False,
            "independent":True
        },
        "stripe":{
            "enabled":bool(STRIPE_PUBLISHABLE_KEY and STRIPE_PRICE_ID1),
            "publishable_key":STRIPE_PUBLISHABLE_KEY if STRIPE_PUBLISHABLE_KEY else None,
            "price_usd":PRICE_USD,
            "currency":"USD"
        },
        "legal":{
            "version":LegalNoticeManager.VERSION,
            "owner":OWNER
        },
        "languages":["es","en"]
    }

@app.get("/api/v1/admin/status")
async def admin_status(request:Request):
    token=request.headers.get("X-Admin-Token","")
    expires=ADMIN_SESSIONS.get(token,0)
    if not token or expires<=now():
        raise HTTPException(403,"Acceso administrativo requerido.")
    return {
        "success":True,
        "authenticated":True,
        "rules_active":rule_repo.count("active"),
        "rules_pending":rule_repo.count("pending"),
        "service_sessions":len(ACTIVE_PAID_SESSIONS)
    }

@app.exception_handler(HTTPException)
async def http_error_handler(request:Request,exc:HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success":False,
            "message":str(exc.detail),
            "path":request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_error_handler(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success":False,
            "message":"Ocurrió un error interno. Intenta nuevamente."
        }
    )
