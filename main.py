# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v7.0.0
import os,secrets,time,json
from pathlib import Path
from typing import Any,Dict,Optional
from datetime import datetime,timezone
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from rules_engine import rule_repo,BaggageAdvisor
from flight_engine import flight_engine
from source_registry import source_registry
from legal_disclaimer import LegalNoticeManager
from schemas import *

APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="7.0.0"
OWNER="May Roga LLC"
SESSION_MINUTES=15
PRICE_USD=15.99
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","").strip()
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","").strip()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()

if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

app=FastAPI(title=APP_NAME,version=APP_VERSION,description="Servicio independiente de orientación para preparación de viajes.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

ACTIVE_PAID_SESSIONS:Dict[str,Dict[str,Any]]={}
ADMIN_SESSIONS:Dict[str,Dict[str,Any]]={}
PAYMENT_SESSIONS:Dict[str,Dict[str,Any]]={}

legal=LegalNoticeManager()
advisor=BaggageAdvisor()

if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")


def now_ts()->int:
    return int(time.time())


def iso_now()->str:
    return datetime.now(timezone.utc).isoformat()


def clean_expired_sessions():
    now=now_ts()
    for store in (ACTIVE_PAID_SESSIONS,ADMIN_SESSIONS):
        dead=[]
        for token,data in store.items():
            if int(data.get("expires_at",0))<=now:
                dead.append(token)
        for token in dead:
            store.pop(token,None)


def create_service_session(source="payment")->Dict[str,Any]:
    clean_expired_sessions()
    token=secrets.token_urlsafe(32)
    created=now_ts()
    expires=created+SESSION_MINUTES*60
    ACTIVE_PAID_SESSIONS[token]={
        "token":token,
        "created_at":created,
        "expires_at":expires,
        "source":source
    }
    return ACTIVE_PAID_SESSIONS[token]


def valid_service_session(token:Optional[str])->Optional[Dict[str,Any]]:
    clean_expired_sessions()
    if not token:
        return None
    data=ACTIVE_PAID_SESSIONS.get(token)
    if not data:
        return None
    if int(data.get("expires_at",0))<=now_ts():
        ACTIVE_PAID_SESSIONS.pop(token,None)
        return None
    return data


def valid_admin_session(token:Optional[str])->bool:
    if not token:
        return False
    data=ADMIN_SESSIONS.get(token)
    if not data:
        return False
    if int(data.get("expires_at",0))<=now_ts():
        ADMIN_SESSIONS.pop(token,None)
        return False
    return True


def request_token(request:Request)->Optional[str]:
    token=request.headers.get("X-Service-Token") or request.headers.get("Authorization")
    if token and token.lower().startswith("bearer "):
        token=token[7:].strip()
    return token or request.query_params.get("session_token")


def require_service(request:Request)->Dict[str,Any]:
    session=valid_service_session(request_token(request))
    if not session:
        raise HTTPException(
            status_code=401,
            detail={
                "success":False,
                "message":"Necesitas una sesión activa para utilizar este servicio.",
                "next_action":"Activa tu servicio de orientación de 15 minutos."
            }
        )
    return session


def request_admin_token(request:Request)->Optional[str]:
    token=request.headers.get("X-Admin-Token") or request.headers.get("Authorization")
    if token and token.lower().startswith("bearer "):
        token=token[7:].strip()
    return token or request.query_params.get("admin_token")


def require_admin(request:Request):
    if not valid_admin_session(request_admin_token(request)):
        raise HTTPException(status_code=401,detail={"success":False,"message":"Sesión administrativa no válida."})


def source_dicts(items):
    out=[]
    for item in items or []:
        if hasattr(item,"to_dict"):
            out.append(item.to_dict())
        elif hasattr(item,"__dict__"):
            out.append(dict(item.__dict__))
        elif isinstance(item,dict):
            out.append(item)
    return out


def official_links_from_sources(items):
    links=[]
    for s in source_dicts(items):
        url=s.get("url")
        name=s.get("name") or s.get("id") or "Fuente oficial"
        if not url:
            continue
        links.append({
            "name":name,
            "url":url,
            "description":s.get("notes"),
            "authority":s.get("source_type"),
            "country":s.get("country"),
            "verified":bool(s.get("verified",False)),
            "verified_at":s.get("verification_date")
        })
    return links


@app.get("/",response_class=FileResponse)
def root():
    index=STATIC_DIR/"index.html"
    if not index.exists():
        return JSONResponse({
            "success":True,
            "app_name":APP_NAME,
            "version":APP_VERSION,
            "owner":OWNER
        })
    return FileResponse(str(index))


@app.get("/health")
def health():
    clean_expired_sessions()
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":APP_VERSION,
        "owner":OWNER,
        "active_sessions":len(ACTIVE_PAID_SESSIONS),
        "stripe_configured":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1)
    }


@app.get("/api/v1/meta",response_model=AppMetaResponse)
def meta():
    return AppMetaResponse(
        app_name=APP_NAME,
        version=APP_VERSION,
        owner=OWNER,
        session_minutes=SESSION_MINUTES,
        payment_type="one_time",
        price_usd=PRICE_USD,
        ai_rule_authority="interpretation_only",
        rules_are_verified=False,
        legal_version=str(getattr(legal,"VERSION","6.0")),
        independent_service=True,
        booking_enabled=False,
        ticket_sales_enabled=False
    )


@app.get("/api/v1/legal",response_model=LegalResponse)
def get_legal():
    notice=legal.full_notice() if hasattr(legal,"full_notice") else legal.intro()
    short=legal.short_notice() if hasattr(legal,"short_notice") else None
    source=legal.source_notice() if hasattr(legal,"source_notice") else None
    return LegalResponse(
        success=True,
        version=str(getattr(legal,"VERSION","6.0")),
        owner=OWNER,
        app_name=APP_NAME,
        notice=notice,
        short_notice=short,
        source_notice=source
    )


@app.get("/api/v1/config")
def config():
    return {
        "success":True,
        "app_name":APP_NAME,
        "version":APP_VERSION,
        "owner":OWNER,
        "session_minutes":SESSION_MINUTES,
        "price_usd":PRICE_USD,
        "payment_type":"one_time",
        "stripe_publishable_key":STRIPE_PUBLISHABLE_KEY or None,
        "booking_enabled":False,
        "ticket_sales_enabled":False,
        "flight_search_mode":"source_guidance",
        "baggage_mode":"verified_rules_only",
        "language_default":"es",
        "languages":["es","en"]
    }


@app.get("/api/v1/official",response_model=OfficialSourcesResponse)
def official_sources():
    try:
        items=source_registry.official()
    except Exception:
        try:
            items=source_registry.verified()
        except Exception:
            items=[]
    return OfficialSourcesResponse(
        success=True,
        sources=official_links_from_sources(items)
    )


@app.get("/api/v1/rules")
def rules():
    try:
        data=rule_repo.all()
    except Exception:
        data=[]
    return {
        "success":True,
        "version":getattr(rule_repo,"version","7.0.0"),
        "rules":source_dicts(data),
        "count":len(data)
    }


@app.post("/api/v1/admin/login",response_model=AdminLoginResponse)
def admin_login(payload:AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=503,detail="La administración no está configurada.")
    if not secrets.compare_digest(payload.username,ADMIN_USERNAME) or not secrets.compare_digest(payload.password,ADMIN_PASSWORD):
        raise HTTPException(status_code=401,detail={"success":False,"message":"Usuario o contraseña incorrectos."})
    token=secrets.token_urlsafe(32)
    ADMIN_SESSIONS[token]={
        "created_at":now_ts(),
        "expires_at":now_ts()+60*60*8
    }
    return AdminLoginResponse(
        success=True,
        token=token,
        message="Sesión administrativa iniciada."
    )


@app.post("/api/v1/admin/logout")
def admin_logout(request:Request):
    token=request_admin_token(request)
    if token:
        ADMIN_SESSIONS.pop(token,None)
    return {"success":True,"message":"Sesión administrativa cerrada."}


@app.get("/api/v1/admin/status")
def admin_status(request:Request):
    token=request_admin_token(request)
    return {
        "success":True,
        "active":valid_admin_session(token),
        "sessions":len(ACTIVE_PAID_SESSIONS)
    }


@app.post("/api/v1/create-checkout-session",response_model=CreateCheckoutResponse)
def create_checkout_session(payload:CreateCheckoutRequest,request:Request):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1:
        raise HTTPException(
            status_code=503,
            detail="Stripe no está configurado. Revisa STRIPE_SECRET_KEY y STRIPE_PRICE_ID1 en Render."
        )
    try:
        origin=str(request.base_url).rstrip("/")
        return_path=payload.return_path or "/"
        if not return_path.startswith("/"):
            return_path="/"
        success_url=f"{origin}{return_path}?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url=f"{origin}{return_path}?payment=cancelled"
        checkout=stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price":STRIPE_PRICE_ID1,
                "quantity":1
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "app":APP_NAME,
                "owner":OWNER,
                "service_minutes":str(SESSION_MINUTES),
                "service_price_usd":str(PRICE_USD)
            }
        )
        PAYMENT_SESSIONS[checkout.id]={
            "created_at":now_ts(),
            "status":"created"
        }
        return CreateCheckoutResponse(
            success=True,
            checkout_url=checkout.url,
            session_id=checkout.id,
            message="Checkout creado."
        )
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"No se pudo crear el pago: {e}")


@app.post("/api/v1/verify-payment",response_model=PaymentVerifyResponse)
def verify_payment(payload:PaymentVerifyRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503,detail="Stripe no está configurado.")
    try:
        checkout=stripe.checkout.Session.retrieve(payload.session_id)
        paid=checkout.payment_status=="paid"
        if not paid:
            return PaymentVerifyResponse(
                success=True,
                paid=False,
                message="El pago todavía no aparece como completado."
            )
        session=create_service_session("stripe")
        PAYMENT_SESSIONS[payload.session_id]={
            "created_at":now_ts(),
            "status":"paid",
            "service_token":session["token"]
        }
        return PaymentVerifyResponse(
            success=True,
            paid=True,
            service_token=session["token"],
            expires_at=datetime.fromtimestamp(
                session["expires_at"],timezone.utc
            ).isoformat(),
            message="Pago confirmado. Tu servicio de orientación está activo."
        )
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"No se pudo verificar el pago: {e}")


@app.post("/api/v1/webhook")
async def stripe_webhook(request:Request):
    body=await request.body()
    signature=request.headers.get("stripe-signature")
    if not STRIPE_WEBHOOK_SECRET:
        return JSONResponse({"success":True,"received":True,"webhook_configured":False})
    try:
        event=stripe.Webhook.construct_event(
            body,signature,STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Webhook inválido: {e}")
    if event["type"]=="checkout.session.completed":
        session_obj=event["data"]["object"]
        sid=session_obj.get("id")
        if sid:
            PAYMENT_SESSIONS[sid]={
                "created_at":now_ts(),
                "status":"paid"
            }
    return {"success":True,"received":True}


@app.get("/api/v1/session/{token}",response_model=SessionStatusResponse)
def session_status(token:str):
    session=valid_service_session(token)
    if not session:
        return SessionStatusResponse(
            active=False,
            token=None,
            remaining_seconds=0,
            message="La sesión no está activa."
        )
    remaining=max(0,int(session["expires_at"]-now_ts()))
    return SessionStatusResponse(
        active=True,
        token=session["token"],
        remaining_seconds=remaining,
        expires_at=datetime.fromtimestamp(
            session["expires_at"],timezone.utc
        ).isoformat(),
        message="Sesión activa."
    )


@app.delete("/api/v1/session/{token}")
def delete_session(token:str):
    existed=token in ACTIVE_PAID_SESSIONS
    ACTIVE_PAID_SESSIONS.pop(token,None)
    return {
        "success":True,
        "deleted":existed,
        "message":"Sesión eliminada."
    }


@app.get("/api/v1/flight/sources")
def flight_sources(
    origin:Optional[str]=None,
    destination:Optional[str]=None,
    airline:Optional[str]=None
):
    try:
        data=flight_engine.search_sources(
            origin=origin,
            destination=destination,
            airline=airline
        )
    except TypeError:
        try:
            data=flight_engine.search_sources(origin,destination,airline)
        except Exception:
            data=[]
    except Exception:
        data=[]
    return {
        "success":True,
        "sources":source_dicts(data)
    }


@app.post("/api/v1/flight/search-external")
def flight_search_external(payload:FlightSearchRequest,request:Request):
    require_service(request)
    try:
        result=flight_engine.search(
            origin=payload.origin,
            destination=payload.destination,
            departure_date=payload.departure_date,
            return_date=payload.return_date,
            passengers=payload.passengers,
            cabin=payload.cabin,
            language=payload.language
        )
    except TypeError:
        try:
            result=flight_engine.search({
                "origin":payload.origin,
                "destination":payload.destination,
                "departure_date":payload.departure_date,
                "return_date":payload.return_date,
                "passengers":payload.passengers,
                "cabin":payload.cabin,
                "language":payload.language
            })
        except Exception as e:
            raise HTTPException(status_code=400,detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"No se pudo preparar la búsqueda: {e}")
    return {
        "success":True,
        "result":result,
        "important":"REMESAS no inventa vuelos, tarifas, horarios, disponibilidad ni condiciones comerciales."
    }


@app.post("/api/v1/flight/understand")
def flight_understand(payload:FlightContext,request:Request):
    require_service(request)
    try:
        result=flight_engine.understand(payload.model_dump(exclude_none=True))
    except TypeError:
        try:
            result=flight_engine.understand(payload.model_dump(exclude_none=True),payload.language if hasattr(payload,"language") else "es")
        except Exception as e:
            raise HTTPException(status_code=400,detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"No se pudo interpretar el vuelo: {e}")
    return {
        "success":True,
        "result":result,
        "legal_notice":legal.short_notice() if hasattr(legal,"short_notice") else None
    }


@app.post("/api/v1/consultar-articulo",response_model=ItemCheckResponse)
def consultar_articulo(payload:ItemCheckRequest,request:Request):
    require_service(request)
    flight=payload.flight.model_dump(exclude_none=True) if payload.flight else None
    try:
        result=advisor.advise(
            payload.item,
            flight=flight,
            baggage_type=payload.baggage_type.value if payload.baggage_type else None,
            language=payload.language
        )
    except TypeError:
        try:
            result=advisor.advise(
                rule_repo,
                payload.item,
                flight=flight,
                baggage_type=payload.baggage_type.value if payload.baggage_type else None,
                language=payload.language
            )
        except Exception as e:
            raise HTTPException(status_code=400,detail=f"No se pudo consultar el artículo: {e}")
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"No se pudo consultar el artículo: {e}")

    if hasattr(result,"model_dump"):
        result=result.model_dump(exclude_none=True)
    if not isinstance(result,dict):
        result=dict(result)

    result.setdefault("success",True)
    result.setdefault("item",payload.item)
    result.setdefault("explanation","")
    result.setdefault("conditions",[])
    result.setdefault("missing_information",[])
    result.setdefault("verified",False)
    result.setdefault("legal_notice",legal.source_notice() if hasattr(legal,"source_notice") else None)
    return result


@app.post("/api/v1/item/teach",response_model=TeachTermResponse)
def teach_item(payload:TeachTermRequest,request:Request):
    require_service(request)
    try:
        result=advisor.explain_term(payload.term,payload.language)
    except Exception:
        result={
            "term":payload.term,
            "explanation":"Te ayudaremos a identificar qué significa este término y qué debes revisar.",
            "example":None,
            "next_action":"Revisa la condición específica de tu vuelo o de la fuente oficial."
        }
    if hasattr(result,"model_dump"):
        result=result.model_dump(exclude_none=True)
    return {
        "success":True,
        **result
    }


@app.post("/api/v1/guide",response_model=GuideResponse)
def guide(payload:GuideRequest,request:Request):
    require_service(request)
    topic=(payload.topic or "").strip().lower()
    flight=payload.flight.model_dump(exclude_none=True) if payload.flight else None
    steps=[]
    title="Prepara tu viaje"
    links=[]

    if "escala" in topic or "conexion" in topic or "conexión" in topic:
        title="Tienes una escala o conexión"
        steps=[
            "Baja del primer avión y revisa las señales de Conexiones/Connections.",
            "Confirma si debes cambiar de avión.",
            "Revisa qué ocurre con tu equipaje.",
            "Confirma si debes pasar inmigración, seguridad o aduana.",
            "Busca la puerta de tu siguiente vuelo.",
            "Si existe una condición que no está confirmada, revisa la fuente oficial del aeropuerto o de la aerolínea."
        ]
    elif "equipaje" in topic or "maleta" in topic or "baggage" in topic:
        title="Revisa tu equipaje"
        steps=[
            "Identifica si llevas artículo personal, equipaje de mano o equipaje facturado.",
            "Revisa la condición específica de tu tarifa.",
            "Revisa las reglas de la aerolínea para tu vuelo.",
            "Consulta también las reglas de seguridad aplicables.",
            "Si un artículo tiene una condición especial, no asumas el límite: confirma la regla vigente."
        ]
    elif "cuba" in topic or (
        flight and (
            str(flight.get("destination","")).upper() in {"HAV","VRA","SCU","CMW"} or
            "cuba" in str(flight.get("destination","")).lower()
        )
    ):
        title="Prepara tu viaje a Cuba"
        steps=[
            "Confirma los documentos que corresponden a tu situación.",
            "Revisa los requisitos oficiales de entrada.",
            "Revisa D’Viajeros cuando corresponda.",
            "Confirma visa o autorización de viaje cuando corresponda.",
            "Revisa las condiciones de equipaje de tu aerolínea.",
            "Antes de viajar, vuelve a confirmar las reglas oficiales porque pueden cambiar."
        ]
        try:
            links=official_links_from_sources(
                source_registry.search("Cuba")
            )
        except Exception:
            links=[]
    else:
        title="Prepara tu viaje paso a paso"
        steps=[
            "Confirma origen y destino.",
            "Confirma fecha y pasajeros.",
            "Identifica la aerolínea y el vuelo.",
            "Revisa si es directo o tiene escala.",
            "Revisa tarifa y equipaje.",
            "Revisa documentos y requisitos oficiales aplicables.",
            "Guarda un resumen de lo que todavía necesitas confirmar."
        ]

    if not links:
        try:
            links=official_links_from_sources(
                source_registry.official()
            )
        except Exception:
            links=[]

    return GuideResponse(
        success=True,
        title=title,
        steps=steps,
        next_action="Continúa con el siguiente dato que sí puedas confirmar.",
        official_links=links
    )


@app.get("/api/v1/sources/search")
def search_sources(q:str):
    q=(q or "").strip()
    if not q:
        return {"success":True,"sources":[]}
    try:
        results=source_registry.search(q)
    except Exception:
        results=[]
    return {
        "success":True,
        "query":q,
        "sources":source_dicts(results)
    }


@app.get("/api/v1/sources/route")
def route_sources(origin:Optional[str]=None,destination:Optional[str]=None,airline:Optional[str]=None):
    try:
        results=source_registry.route_sources(
            origin=origin,
            destination=destination,
            airline=airline
        )
    except TypeError:
        try:
            results=source_registry.route_sources(origin,destination,airline)
        except Exception:
            results=[]
    except Exception:
        results=[]
    return {
        "success":True,
        "sources":source_dicts(results)
    }


@app.get("/api/v1/sources/baggage")
def baggage_sources(
    airline:Optional[str]=None,
    origin:Optional[str]=None,
    destination:Optional[str]=None
):
    try:
        results=source_registry.baggage_sources(
            airline=airline,
            origin=origin,
            destination=destination
        )
    except TypeError:
        try:
            results=source_registry.baggage_sources(airline,origin,destination)
        except Exception:
            results=[]
    except Exception:
        results=[]
    return {
        "success":True,
        "sources":source_dicts(results)
    }


@app.get("/api/v1/session")
def current_session(request:Request):
    token=request_token(request)
    session=valid_service_session(token)
    if not session:
        return {
            "success":True,
            "active":False,
            "remaining_seconds":0
        }
    return {
        "success":True,
        "active":True,
        "token":session["token"],
        "remaining_seconds":max(0,session["expires_at"]-now_ts()),
        "expires_at":datetime.fromtimestamp(
            session["expires_at"],timezone.utc
        ).isoformat()
    }


@app.get("/api/v1")
def api_index():
    return {
        "success":True,
        "app_name":APP_NAME,
        "version":APP_VERSION,
        "owner":OWNER,
        "endpoints":{
            "meta":"/api/v1/meta",
            "legal":"/api/v1/legal",
            "official":"/api/v1/official",
            "checkout":"/api/v1/create-checkout-session",
            "verify_payment":"/api/v1/verify-payment",
            "session":"/api/v1/session",
            "flight_search":"/api/v1/flight/search-external",
            "flight_understand":"/api/v1/flight/understand",
            "item_check":"/api/v1/consultar-articulo",
            "teach":"/api/v1/item/teach",
            "guide":"/api/v1/guide"
        }
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request:Request,exc:HTTPException):
    detail=exc.detail
    if isinstance(detail,dict):
        body=detail
    else:
        body={
            "success":False,
            "message":str(detail)
        }
    return JSONResponse(status_code=exc.status_code,content=body)


@app.exception_handler(Exception)
async def general_exception_handler(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success":False,
            "message":"Ocurrió un error interno. Intenta nuevamente.",
            "code":"INTERNAL_ERROR"
        }
    )
