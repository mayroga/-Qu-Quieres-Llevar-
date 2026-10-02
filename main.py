# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.0
import os,secrets,time
from pathlib import Path
from typing import Any,Dict,Optional
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from rules_engine import rule_repo,BaggageAdvisor
from flight_engine import flight_engine
from source_registry import source_registry
from legal_disclaimer import LegalNoticeManager
from schemas import *
try:
    from remittance_engine import engine as remittance_engine
except Exception:
    remittance_engine=None

BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","")
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","")
APP_VERSION="8.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
OWNER="May Roga LLC"
PRICE_USD=15.99
SESSION_MINUTES=15
SESSION_SECONDS=SESSION_MINUTES*60
PAYMENT_TYPE="one_time"
ACTIVE_PAID_SESSIONS:Dict[str,float]={}
ADMIN_SESSIONS:Dict[str,float]={}
PAYMENT_SESSIONS:Dict[str,float]={}
app=FastAPI(title=APP_NAME,version=APP_VERSION,description="Acompañante independiente de preparación de viaje de May Roga LLC.")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY
if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

def now()->float:return time.time()
def new_token()->str:return secrets.token_urlsafe(32)
def clean_sessions():
    t=now()
    for store in (ACTIVE_PAID_SESSIONS,ADMIN_SESSIONS,PAYMENT_SESSIONS):
        for k,v in list(store.items()):
            if v<=t:store.pop(k,None)
def session_active(token:Optional[str])->bool:
    clean_sessions()
    return bool(token and ACTIVE_PAID_SESSIONS.get(token,0)>now())
def admin_active(token:Optional[str])->bool:
    clean_sessions()
    return bool(token and ADMIN_SESSIONS.get(token,0)>now())
def require_session(token:Optional[str]):
    if not session_active(token):raise HTTPException(status_code=401,detail="Sesión de servicio no activa.")
def require_admin(token:Optional[str]):
    if not admin_active(token):raise HTTPException(status_code=401,detail="Sesión administrativa no activa.")
def lang_of(value:Any)->str:
    try:
        if hasattr(value,"language"):return "en" if value.language=="en" else "es"
        if isinstance(value,dict):return "en" if value.get("language")=="en" else "es"
    except Exception:pass
    return "es"
def model_data(value:Any)->Dict[str,Any]:
    if hasattr(value,"model_dump"):return value.model_dump()
    if hasattr(value,"dict"):return value.dict()
    return dict(value) if isinstance(value,dict) else {}
def source_dict(source):
    if hasattr(source,"to_dict"):return source.to_dict()
    return dict(source)
def source_cards(items):
    return [source_dict(x) for x in items]
def error_response(message:str,code:str="error",status:int=400,next_action:Optional[str]=None):
    return JSONResponse(status_code=status,content={"success":False,"message":message,"code":code,"next_action":next_action})
def official_links():
    return [
        {"name":"TSA — What Can I Bring","url":"https://www.tsa.gov/travel/security-screening/whatcanibring/all-list","description":"Consulta artículos y seguridad en el control TSA.","authority":"TSA","country":"United States","verified":True,"verified_at":"2026-10-01"},
        {"name":"FAA — PackSafe","url":"https://www.faa.gov/hazmat/packsafe","description":"Consulta reglas de artículos y materiales peligrosos.","authority":"FAA","country":"United States","verified":True,"verified_at":"2026-10-01"},
        {"name":"FAA — Batteries","url":"https://www.faa.gov/hazmat/packsafe/airline-passengers-and-batteries","description":"Consulta baterías y power banks.","authority":"FAA","country":"United States","verified":True,"verified_at":"2026-10-01"},
        {"name":"D'Viajeros Cuba","url":"https://dviajeros.mitrans.gob.cu/","description":"Sitio oficial de D'Viajeros. Confirma la información vigente antes del viaje.","authority":"Cuba","country":"Cuba","verified":False,"verified_at":None},
        {"name":"eVisa Cuba","url":"https://evisacuba.cu/","description":"Información oficial sobre visa electrónica de Cuba.","authority":"Cuba","country":"Cuba","verified":False,"verified_at":None}
    ]

@app.get("/",include_in_schema=False)
async def root():
    index=STATIC_DIR/"index.html"
    if index.exists():return FileResponse(index)
    return {"success":True,"app_name":APP_NAME,"version":APP_VERSION,"owner":OWNER}

@app.get("/health")
async def health():
    return {"status":"ok","app_name":APP_NAME,"version":APP_VERSION}

@app.get("/api/v1")
async def api_root():
    return {"success":True,"app_name":APP_NAME,"version":APP_VERSION,"owner":OWNER}

@app.get("/api/v1/meta",response_model=AppMetaResponse)
async def meta():
    return {"app_name":APP_NAME,"version":APP_VERSION,"owner":OWNER,"session_minutes":SESSION_MINUTES,"payment_type":PAYMENT_TYPE,"price_usd":PRICE_USD,"ai_rule_authority":"Las reglas verificadas y las fuentes oficiales tienen prioridad; la IA no sustituye a la autoridad.","rules_are_verified":False,"legal_version":LegalNoticeManager.VERSION,"independent_service":True,"booking_enabled":False,"ticket_sales_enabled":False}

@app.get("/api/v1/legal",response_model=LegalResponse)
async def legal(language:str="es"):
    m=LegalNoticeManager(language)
    return {"success":True,"version":m.VERSION,"owner":m.OWNER,"app_name":m.APP_NAME,"notice":m.full_notice(),"short_notice":m.short_notice(),"source_notice":m.source_notice()}

@app.get("/api/v1/config")
async def config():
    return {"success":True,"app_name":APP_NAME,"version":APP_VERSION,"owner":OWNER,"price_usd":PRICE_USD,"session_minutes":SESSION_MINUTES,"payment_type":PAYMENT_TYPE,"stripe_enabled":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),"publishable_key":STRIPE_PUBLISHABLE_KEY or None,"booking_enabled":False,"ticket_sales_enabled":False,"independent_service":True}

@app.get("/api/v1/official",response_model=OfficialSourcesResponse)
async def official():
    return {"success":True,"sources":official_links()}

@app.get("/api/v1/rules",response_model=RulesResponse)
async def rules(status:Optional[str]=None):
    try:
        rules=rule_repo.to_dicts(status=status) if hasattr(rule_repo,"to_dicts") else [x.to_dict() if hasattr(x,"to_dict") else dict(x) for x in rule_repo.all()]
    except Exception:
        rules=[]
    return {"success":True,"version":getattr(rule_repo,"VERSION",None),"rules":rules,"count":len(rules)}

@app.post("/api/v1/admin/login",response_model=AdminLoginResponse)
async def admin_login(payload:AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:return {"success":False,"message":"La administración no está configurada en Render."}
    if not secrets.compare_digest(payload.username,ADMIN_USERNAME) or not secrets.compare_digest(payload.password,ADMIN_PASSWORD):
        return {"success":False,"message":"Usuario o contraseña incorrectos."}
    token=new_token();ADMIN_SESSIONS[token]=now()+SESSION_SECONDS
    return {"success":True,"token":token,"message":"Sesión administrativa activa."}

@app.post("/api/v1/admin/logout")
async def admin_logout(request:Request):
    token=request.headers.get("X-Admin-Token") or request.query_params.get("token")
    if token:ADMIN_SESSIONS.pop(token,None)
    return {"success":True,"message":"Sesión administrativa cerrada."}

@app.get("/api/v1/admin/status")
async def admin_status(request:Request):
    token=request.headers.get("X-Admin-Token") or request.query_params.get("token")
    clean_sessions()
    remaining=max(0,int(ADMIN_SESSIONS.get(token,0)-now())) if token else 0
    return {"success":True,"active":bool(token and remaining>0),"remaining_seconds":remaining}

@app.post("/api/v1/create-checkout-session",response_model=CreateCheckoutResponse)
async def create_checkout(payload:CreateCheckoutRequest,request:Request):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1:return {"success":False,"message":"El pago no está configurado todavía."}
    try:
        host=request.headers.get("origin") or str(request.base_url).rstrip("/")
        path=payload.return_path or "/"
        success_url=f"{host}{path}?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url=f"{host}{path}?payment=cancelled"
        session=stripe.checkout.Session.create(mode="payment",line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],success_url=success_url,cancel_url=cancel_url,metadata={"app":APP_NAME,"owner":OWNER,"service":"travel_preparation"})
        return {"success":True,"checkout_url":session.url,"session_id":session.id,"message":"Continúa con el pago para iniciar tu servicio de preparación."}
    except Exception as e:
        return {"success":False,"message":f"No pudimos iniciar el pago: {str(e)}"}

@app.post("/api/v1/verify-payment",response_model=PaymentVerifyResponse)
async def verify_payment(payload:PaymentVerifyRequest):
    if not STRIPE_SECRET_KEY:return {"success":False,"paid":False,"message":"El pago no está configurado."}
    try:
        session=stripe.checkout.Session.retrieve(payload.session_id)
        paid=session.payment_status=="paid"
        if not paid:return {"success":True,"paid":False,"message":"El pago todavía no aparece como completado."}
        token=new_token();expires=now()+SESSION_SECONDS;ACTIVE_PAID_SESSIONS[token]=expires;PAYMENT_SESSIONS[payload.session_id]=expires
        return {"success":True,"paid":True,"service_token":token,"expires_at":datetime_from_timestamp(expires),"message":"Pago confirmado. Tu sesión de preparación está activa."}
    except Exception as e:
        return {"success":False,"paid":False,"message":f"No pudimos confirmar el pago: {str(e)}"}

def datetime_from_timestamp(ts:float)->str:
    return datetime.fromtimestamp(ts,timezone.utc).isoformat()

@app.post("/api/v1/webhook")
async def stripe_webhook(request:Request):
    body=await request.body()
    signature=request.headers.get("stripe-signature")
    if not STRIPE_WEBHOOK_SECRET:
        return {"received":True,"verified":False}
    try:
        event=stripe.Webhook.construct_event(body,signature,STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Webhook inválido: {str(e)}")
    if event["type"]=="checkout.session.completed":
        obj=event["data"]["object"]
        sid=obj.get("id")
        if sid:PAYMENT_SESSIONS[sid]=now()+SESSION_SECONDS
    return {"received":True,"verified":True}

@app.get("/api/v1/session/{token}",response_model=SessionStatusResponse)
async def session_status(token:str):
    clean_sessions()
    remaining=max(0,int(ACTIVE_PAID_SESSIONS.get(token,0)-now()))
    return {"active":remaining>0,"token":token if remaining>0 else None,"remaining_seconds":remaining,"expires_at":datetime_from_timestamp(now()+remaining) if remaining>0 else None,"message":None if remaining>0 else LegalNoticeManager().session_expired_message()}

@app.get("/api/v1/session",response_model=SessionStatusResponse)
async def session_from_header(request:Request):
    token=request.headers.get("X-Service-Token") or request.query_params.get("token")
    return await session_status(token or "")

@app.get("/api/v1/flight/sources",response_model=FlightSourcesResponse)
async def flight_sources(origin:Optional[str]=None,destination:Optional[str]=None,airline:Optional[str]=None):
    sources=flight_engine.search_sources(origin,destination,airline)
    return {"success":True,"sources":sources}

@app.post("/api/v1/flight/search-external",response_model=FlightSearchResponse)
async def flight_search_external(payload:FlightSearchRequest):
    data=model_data(payload)
    result=flight_engine.search(**data)
    return result

@app.post("/api/v1/flight/understand",response_model=FlightUnderstandResponse)
async def flight_understand(payload:SelectedFlightRequest):
    data=model_data(payload.flight)
    return flight_engine.understand(data,language=payload.language)

@app.post("/api/v1/consultar-articulo",response_model=ItemCheckResponse)
async def check_item(payload:ItemCheckRequest):
    data=model_data(payload)
    language=data.pop("language","es")
    flight=data.pop("flight",None)
    baggage_type=data.pop("baggage_type",None)
    try:
        result=BaggageAdvisor().advise(data.get("item"),flight=flight,baggage_type=baggage_type,language=language,quantity=data.get("quantity"),weight=data.get("weight"),weight_unit=data.get("weight_unit"),dimensions=data.get("dimensions"),category=data.get("category"),description=data.get("description"))
    except TypeError:
        try:
            result=BaggageAdvisor().advise(data.get("item"),flight=flight,baggage_type=baggage_type,language=language)
        except Exception as e:
            return error_response(f"No pudimos analizar el artículo todavía: {e}","item_error",500)
    except Exception as e:
        return error_response(f"No pudimos analizar el artículo todavía: {e}","item_error",500)
    if hasattr(result,"to_dict"):result=result.to_dict()
    if not isinstance(result,dict):result=dict(result)
    return result

@app.post("/api/v1/item/teach",response_model=TeachTermResponse)
async def teach_item(payload:TeachTermRequest):
    advisor=BaggageAdvisor()
    try:
        result=advisor.explain_term(payload.term,payload.language)
    except Exception:
        result={"term":payload.term,"explanation":"Este término se refiere a una condición de viaje que debemos entender antes de decidir dónde llevar el artículo.","example":None,"next_action":"Busca el término en las condiciones de tu vuelo y confirma su significado."}
    if not isinstance(result,dict):result=dict(result)
    return {"success":True,"term":result.get("term",payload.term),"explanation":result.get("explanation",""),"example":result.get("example"),"next_action":result.get("next_action")}

@app.post("/api/v1/guide",response_model=GuideResponse)
async def guide(payload:GuideRequest):
    lang=payload.language
    topic=(payload.topic or "").strip().lower()
    if lang=="en":
        title="Prepare your trip"
        steps=["Understand your flight.","Check whether you have a connection.","Understand your baggage.","Review the items you want to carry.","Prepare your documents.","Practice important steps.","Confirm current requirements with the official source.","Save your personalized preparation guide."]
        next_action="Start with your flight or tell us what you want to carry."
    else:
        title="Prepara tu viaje"
        steps=["Entiende tu vuelo.","Comprueba si tienes una escala o conexión.","Entiende tu equipaje.","Revisa lo que quieres llevar.","Prepara tus documentos.","Practica los pasos importantes.","Confirma los requisitos vigentes en la fuente oficial.","Guarda tu guía personalizada de preparación."]
        next_action="Empieza por tu vuelo o dime qué quieres llevar."
    links=[OfficialLink(**x) for x in official_links()]
    return {"success":True,"title":title,"steps":steps,"next_action":next_action,"official_links":links}

@app.get("/api/v1/sources/search",response_model=SourceSearchResponse)
async def sources_search(q:str="",official_only:bool=False,verified_only:bool=False):
    items=source_registry.search(q,official_only=official_only,verified_only=verified_only)
    return {"success":True,"query":q,"sources":[source_dict(x) for x in items]}

@app.get("/api/v1/sources/route")
async def sources_route(origin:Optional[str]=None,destination:Optional[str]=None,airline:Optional[str]=None):
    items=source_registry.route_sources(origin,destination,airline,include_search=True)
    return {"success":True,"origin":origin,"destination":destination,"airline":airline,"sources":[source_dict(x) for x in items]}

@app.get("/api/v1/sources/baggage")
async def sources_baggage(airline:Optional[str]=None,origin:Optional[str]=None,destination:Optional[str]=None):
    items=source_registry.baggage_sources(airline,origin,destination)
    return {"success":True,"airline":airline,"origin":origin,"destination":destination,"sources":[source_dict(x) for x in items]}

@app.get("/api/v1/cuba/sources")
async def cuba_sources(airline:Optional[str]=None):
    return {"success":True,"sources":flight_engine.cuba_sources(airline)}

@app.get("/api/v1/cuba/guide")
async def cuba_guide(language:str="es"):
    if language=="en":
        return {"success":True,"title":"Cuba travel preparation","steps":["Identify whether you are traveling as a Cuban citizen, foreign traveler or dual national and determine which documents apply to your situation.","Check passport and travel-document requirements using the applicable official source.","Check visa or entry authorization requirements when applicable.","Complete D'Viajeros when required by the current official process.","Review airline baggage rules for your exact itinerary.","Confirm current requirements immediately before traveling."],"official_sources":flight_engine.cuba_sources()}
    return {"success":True,"title":"Preparación para viajar a Cuba","steps":["Identifica si viajas como ciudadano cubano, extranjero o persona con doble nacionalidad y determina qué documentos corresponden a tu caso.","Revisa la vigencia y los documentos de viaje en la fuente oficial correspondiente.","Comprueba si necesitas visa o autorización de entrada según tu situación.","Completa D'Viajeros cuando corresponda según el proceso oficial vigente.","Revisa las reglas de equipaje de tu itinerario concreto.","Confirma nuevamente los requisitos oficiales antes de viajar."],"official_sources":flight_engine.cuba_sources()}

@app.get("/api/v1/official/{source_id}")
async def official_source(source_id:str):
    source=source_registry.get(source_id)
    if not source:return error_response("No encontramos esa fuente en el registro.","source_not_found",404)
    return {"success":True,"source":source_dict(source)}

@app.get("/api/v1/legal/full")
async def legal_full(language:str="es"):
    m=LegalNoticeManager(language)
    return {"success":True,**m.to_dict(),"notice":m.full_notice()}

@app.exception_handler(HTTPException)
async def http_exception_handler(request:Request,exc:HTTPException):
    return JSONResponse(status_code=exc.status_code,content={"success":False,"message":str(exc.detail),"code":"http_error"})

@app.exception_handler(Exception)
async def general_exception_handler(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"success":False,"message":"Ocurrió un error inesperado. Puedes volver a intentar la acción.","code":"internal_error"})

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=int(os.getenv("PORT","10000")))
