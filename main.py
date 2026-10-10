from __future__ import annotations
import os,json,re,io,datetime,time,hmac,hashlib,base64
from typing import Any,Dict
from urllib.parse import urlparse
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph,Spacer,SimpleDocTemplate,Table,TableStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
import cuba_engine as engine
from schemas import *

try:
    import stripe
except ImportError:
    stripe=None

SOURCE_VERSION=engine.VERSION
SOURCES=engine.SOURCES
all_sources=engine.all_sources
source_by_id=engine.source_by_id
get_sources=engine.get_sources
official_sources=engine.official_sources
get_airlines=engine.get_airlines
get_charters=engine.get_charters
official_url=engine.official_url
answer_sources=engine.answer_sources

VERSION="17.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
STATIC_DIR="static"
SINGLE_PRICE=1599
SUBSCRIPTION_PRICE=2599
SESSION_MINUTES=20
SESSION_COOKIE="qql_access"
ENTITLEMENT_COOKIE="qql_entitlement"
ADMIN_COOKIE="qql_admin"
COOKIE_SECURE_DEFAULT=os.getenv("COOKIE_SECURE","true").lower() in ("1","true","yes")
PAYWALL_ENABLED=os.getenv("PAYWALL_ENABLED","true").lower() in ("1","true","yes")
SESSION_SIGNING_SECRET=os.getenv("SESSION_SIGNING_SECRET","").strip()
if not SESSION_SIGNING_SECRET:
    SESSION_SIGNING_SECRET=os.getenv("ADMIN_PASSWORD","").strip()
if not SESSION_SIGNING_SECRET:
    SESSION_SIGNING_SECRET=os.urandom(32).hex()

if stripe:
    stripe.api_key=os.getenv("STRIPE_SECRET_KEY","").strip() or None

app=FastAPI(title=APP_NAME,version=VERSION)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def epoch():
    return int(time.time())

def model_dict(x):
    if x is None:return {}
    if isinstance(x,dict):return x
    if hasattr(x,"model_dump"):return x.model_dump(exclude_none=False)
    if hasattr(x,"dict"):return x.dict()
    return dict(x)

def normalize_result(result,default_sources=None):
    if result is None:result={}
    if hasattr(result,"model_dump"):result=result.model_dump()
    elif not isinstance(result,dict):result={"message":str(result)}
    result=dict(result)
    if not isinstance(result.get("sources"),list):result["sources"]=default_sources or []
    return result

def call_engine(name,data=None):
    fn=getattr(engine,name,None)
    if not fn:
        return {"status":"error","message":f"Función no disponible: {name}","next_action":"Revisa la aplicación."}
    d=model_dict(data)
    try:
        return normalize_result(fn(d))
    except TypeError:
        try:return normalize_result(fn(**d))
        except Exception:
            return {"status":"error","message":"La operación no pudo completarse.","next_action":"Inténtalo nuevamente."}
    except Exception:
        return {"status":"error","message":"La operación no pudo completarse.","next_action":"Inténtalo nuevamente."}

# -------- SESIONES FIRMADAS EN EL SERVIDOR --------
def _b64(data:bytes)->str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def _unb64(value:str)->bytes:
    return base64.urlsafe_b64decode(value+"="*((4-len(value)%4)%4))

def sign_payload(payload:dict)->str:
    raw=json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()
    body=_b64(raw)
    signature=hmac.new(SESSION_SIGNING_SECRET.encode(),body.encode(),hashlib.sha256).digest()
    return body+"."+_b64(signature)

def read_token(token:str|None):
    if not token or "." not in token:return None
    try:
        body,sig=token.rsplit(".",1)
        expected=_b64(hmac.new(SESSION_SIGNING_SECRET.encode(),body.encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(sig,expected):return None
        payload=json.loads(_unb64(body).decode())
        if int(payload.get("exp",0))<epoch():return None
        return payload
    except Exception:return None

def cookie_payload(request:Request,name:str):
    return read_token(request.cookies.get(name))

def secure_cookie(request:Request)->bool:
    proto=request.headers.get("x-forwarded-proto","").split(",")[0].strip().lower()
    return COOKIE_SECURE_DEFAULT or request.url.scheme=="https" or proto=="https"

def set_signed_cookie(response,request,name,payload,max_age,httponly=True):
    response.set_cookie(
        key=name,
        value=sign_payload(payload),
        max_age=max_age,
        httponly=httponly,
        secure=secure_cookie(request),
        samesite="lax",
        path="/"
    )

def set_access_cookie(response,request,kind,plan="",minutes=SESSION_MINUTES,subscription_id=""):
    payload={
        "kind":kind,
        "plan":plan,
        "iat":epoch(),
        "exp":epoch()+max(60,int(minutes)*60),
        "subscription_id":subscription_id or ""
    }
    set_signed_cookie(response,request,SESSION_COOKIE,payload,minutes*60)
    return payload

def clear_cookie(response,name):
    response.delete_cookie(key=name,path="/",samesite="lax")

def active_session(request:Request):
    payload=cookie_payload(request,SESSION_COOKIE)
    if not payload:return None
    if payload.get("kind") not in ("admin","single","subscription"):return None
    return payload

def admin_credentials_ok(username,password):
    expected_user=os.getenv("ADMIN_USERNAME","").strip()
    expected_pass=os.getenv("ADMIN_PASSWORD","")
    if not expected_user or not expected_pass:return False
    return hmac.compare_digest(str(username),expected_user) and hmac.compare_digest(str(password),expected_pass)

def stripe_ready():
    return bool(stripe and os.getenv("STRIPE_SECRET_KEY","").strip())

def stripe_price_id(plan):
    if plan=="single":return os.getenv("STRIPE_PRICE_SINGLE","").strip()
    if plan=="subscription":return os.getenv("STRIPE_PRICE_SUBSCRIPTION","").strip()
    return ""

def stripe_base_url(request:Request):
    configured=os.getenv("APP_BASE_URL","").strip().rstrip("/")
    if configured:
        parsed=urlparse(configured)
        if parsed.scheme in ("https","http") and parsed.netloc:return configured
    return str(request.base_url).rstrip("/")

def checkout_metadata(plan):
    return {"app":"que_quieres_llevar","plan":plan,"version":VERSION}

def create_stripe_checkout(plan,request:Request):
    if not stripe_ready():
        raise RuntimeError("Stripe no está configurado. Revisa STRIPE_SECRET_KEY y la instalación de stripe.")
    if plan not in ("single","subscription"):
        raise ValueError("El plan seleccionado no es válido.")
    base=stripe_base_url(request)
    success=base+"/?session_id={CHECKOUT_SESSION_ID}"
    cancel=base+"/?payment=cancelled"
    price_id=stripe_price_id(plan)
    common={
        "success_url":success,
        "cancel_url":cancel,
        "client_reference_id":"may-roga-qql",
        "metadata":checkout_metadata(plan),
        "allow_promotion_codes":False
    }
    if price_id:
        common["line_items"]=[{"price":price_id,"quantity":1}]
        common["mode"]="payment" if plan=="single" else "subscription"
    else:
        product_name="¿QUÉ QUIERES LLEVAR? — Acceso"
        if plan=="single":
            common["mode"]="payment"
            common["line_items"]=[{
                "price_data":{
                    "currency":"usd",
                    "unit_amount":SINGLE_PRICE,
                    "product_data":{"name":product_name,"description":"Acceso individual de 20 minutos"}
                },
                "quantity":1
            }]
        else:
            common["mode"]="subscription"
            common["line_items"]=[{
                "price_data":{
                    "currency":"usd",
                    "unit_amount":SUBSCRIPTION_PRICE,
                    "recurring":{"interval":"month"},
                    "product_data":{"name":product_name,"description":"Suscripción mensual"}
                },
                "quantity":1
            }]
    return stripe.checkout.Session.create(**common)

def retrieve_checkout(session_id):
    if not stripe_ready():raise RuntimeError("Stripe no está configurado.")
    if not session_id or not re.fullmatch(r"[A-Za-z0-9_]+",str(session_id)):
        raise ValueError("La sesión de pago no es válida.")
    return stripe.checkout.Session.retrieve(session_id,expand=["subscription"])

def stripe_obj_value(obj,key,default=None):
    if isinstance(obj,dict):return obj.get(key,default)
    return getattr(obj,key,default)

def verify_checkout_payment(session_id):
    session=retrieve_checkout(session_id)
    plan=stripe_obj_value(session,"metadata",{}) or {}
    if not isinstance(plan,dict):plan=dict(plan)
    if plan.get("app")!="que_quieres_llevar":
        raise ValueError("La sesión no pertenece a esta aplicación.")
    selected=plan.get("plan","")
    mode=stripe_obj_value(session,"mode","")
    subscription_id=""
    if selected=="single" and mode=="payment":
        if stripe_obj_value(session,"payment_status","")!="paid":
            raise ValueError("Stripe todavía no confirma el pago.")
        return {"kind":"single","plan":"single","subscription_id":""}
    if selected=="subscription" and mode=="subscription":
        sub=stripe_obj_value(session,"subscription")
        if isinstance(sub,str):
            sub=stripe.Subscription.retrieve(sub)
        status=stripe_obj_value(sub,"status","")
        if status not in ("active","trialing"):
            raise ValueError("La suscripción no está activa en Stripe.")
        subscription_id=stripe_obj_value(sub,"id","") or ""
        return {"kind":"subscription","plan":"subscription","subscription_id":subscription_id}
    raise ValueError("El plan o el estado del pago no coincide.")

def subscription_is_active(subscription_id):
    if not stripe_ready() or not subscription_id:return False
    try:
        sub=stripe.Subscription.retrieve(subscription_id)
        return stripe_obj_value(sub,"status","") in ("active","trialing")
    except Exception:return False

def entitlement_payload(request:Request):
    return cookie_payload(request,ENTITLEMENT_COOKIE)

def has_active_subscription_entitlement(request:Request):
    entitlement=entitlement_payload(request)
    if not entitlement or entitlement.get("plan")!="subscription":return False
    sid=entitlement.get("subscription_id","")
    return subscription_is_active(sid)

# -------- MURO DE ACCESO SIN CAMBIAR LOS ENDPOINTS ORIGINALES --------
PUBLIC_API_PATHS={
    "/api/config","/api/legal","/api/ping","/api/sources","/api/official",
    "/api/airlines","/api/charters","/api/cuba-official","/api/airlines-cuba",
    "/api/v1/stripe/create-checkout","/api/v1/access/status",
    "/api/v1/access/verify","/api/v1/access/restore",
    "/api/v1/admin/login","/api/v1/admin/logout","/api/v1/stripe/webhook",
    "/health"
}

@app.middleware("http")
async def access_wall(request:Request,call_next):
    path=request.url.path
    if not PAYWALL_ENABLED or request.method=="OPTIONS" or not path.startswith("/api/") or path in PUBLIC_API_PATHS:
        return await call_next(request)
    if path.startswith("/api/v1/"):
        return await call_next(request)
    session=active_session(request)
    if not session:
        return JSONResponse(
            status_code=402,
            content={
                "status":"access_required",
                "message":"Necesitas un acceso activo para continuar.",
                "next_action":"Abre la aplicación y completa el acceso."
            }
        )
    if session.get("kind")=="subscription":
        sid=session.get("subscription_id","")
        if sid and not subscription_is_active(sid):
            response=JSONResponse(
                status_code=402,
                content={"status":"access_required","message":"La suscripción no aparece activa.","next_action":"Revisa tu suscripción o restaura el acceso."}
            )
            clear_cookie(response,SESSION_COOKIE)
            return response
    return await call_next(request)

# -------- RUTAS NUEVAS: STRIPE Y ENTRADA ADMINISTRATIVA --------
@app.post("/api/v1/stripe/create-checkout")
async def stripe_create_checkout(request:Request):
    try:
        data=await request.json()
        plan=str(data.get("plan","")).strip().lower()
        if plan not in ("single","subscription"):
            return JSONResponse(status_code=400,content={"status":"error","message":"Selecciona un plan válido."})
        session=create_stripe_checkout(plan,request)
        return {"status":"ok","url":stripe_obj_value(session,"url"),"session_id":stripe_obj_value(session,"id"),"plan":plan}
    except ValueError as e:
        return JSONResponse(status_code=400,content={"status":"error","message":str(e)})
    except Exception:
        return JSONResponse(status_code=503,content={"status":"error","message":"No se pudo iniciar el pago. Comprueba la configuración de Stripe e inténtalo nuevamente."})

@app.get("/api/v1/access/status")
async def access_status(request:Request):
    session=active_session(request)
    entitlement=entitlement_payload(request)
    subscription_ok=False
    if entitlement and entitlement.get("plan")=="subscription":
        subscription_ok=has_active_subscription_entitlement(request)
    allowed=bool(session)
    kind=session.get("kind","") if session else ""
    plan=session.get("plan","") if session else ""
    if session and kind=="subscription":
        sid=session.get("subscription_id","")
        if sid and not subscription_is_active(sid):
            allowed=False
            kind=""
            plan=""
    remaining=0
    if session and allowed:
        remaining=max(0,int(session.get("exp",0))-epoch())
    return {
        "status":"ok",
        "allowed":allowed,
        "kind":kind,
        "plan":plan,
        "session_expired":not allowed,
        "remaining_seconds":remaining,
        "has_subscription":subscription_ok,
        "payment_required":PAYWALL_ENABLED,
        "options":{
            "single":{"amount":15.99,"currency":"USD","duration_minutes":SESSION_MINUTES},
            "subscription":{"amount":25.99,"currency":"USD","interval":"month"}
        }
    }

@app.post("/api/v1/access/verify")
async def access_verify(request:Request):
    try:
        data=await request.json()
        session_id=str(data.get("session_id","")).strip()
        result=verify_checkout_payment(session_id)
        kind=result["kind"]
        plan=result["plan"]
        subscription_id=result.get("subscription_id","")
        response=JSONResponse({
            "status":"ok",
            "allowed":True,
            "kind":kind,
            "plan":plan,
            "message":"Pago verificado por Stripe.",
            "remaining_seconds":SESSION_MINUTES*60
        })
        entitlement_exp=epoch()+(365*86400 if kind=="single" else 86400)
        set_signed_cookie(response,request,ENTITLEMENT_COOKIE,{
            "kind":kind,"plan":plan,"subscription_id":subscription_id,
            "session_id":session_id,"exp":entitlement_exp,"iat":epoch()
        },max_age=365*86400 if kind=="single" else 86400)
        set_access_cookie(response,request,kind,plan,SESSION_MINUTES,subscription_id)
        return response
    except ValueError as e:
        return JSONResponse(status_code=400,content={"status":"error","allowed":False,"message":str(e)})
    except Exception:
        return JSONResponse(status_code=503,content={"status":"error","allowed":False,"message":"No se pudo verificar el pago con Stripe. Inténtalo nuevamente."})

@app.post("/api/v1/access/restore")
async def access_restore(request:Request):
    entitlement=entitlement_payload(request)
    if not entitlement or entitlement.get("plan")!="subscription":
        response=JSONResponse(status_code=403,content={
            "status":"error","allowed":False,
            "message":"No se encontró una suscripción que pueda restaurarse."
        })
        clear_cookie(response,SESSION_COOKIE)
        return response
    sid=entitlement.get("subscription_id","")
    if not subscription_is_active(sid):
        response=JSONResponse(status_code=403,content={
            "status":"error","allowed":False,
            "message":"Stripe no confirma una suscripción activa. Revisa el estado de tu suscripción."
        })
        clear_cookie(response,SESSION_COOKIE)
        return response
    response=JSONResponse({
        "status":"ok","allowed":True,"kind":"subscription",
        "plan":"subscription","remaining_seconds":SESSION_MINUTES*60,
        "message":"Acceso restaurado."
    })
    set_access_cookie(response,request,"subscription","subscription",SESSION_MINUTES,sid)
    return response

@app.post("/api/v1/admin/login")
async def admin_login(request:Request):
    try:data=await request.json()
    except Exception:data={}
    username=str(data.get("username",""))
    password=str(data.get("password",""))
    if not admin_credentials_ok(username,password):
        return JSONResponse(status_code=401,content={
            "status":"error","allowed":False,
            "message":"Usuario o contraseña incorrectos."
        })
    response=JSONResponse({
        "status":"ok","allowed":True,"kind":"admin","plan":"admin",
        "message":"Acceso administrativo autorizado."
    })
    set_access_cookie(response,request,"admin","admin",365*24*60)
    return response

@app.post("/api/v1/admin/logout")
async def admin_logout():
    response=JSONResponse({"status":"ok","message":"Sesión cerrada."})
    clear_cookie(response,SESSION_COOKIE)
    return response

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    if not stripe_ready():
        return JSONResponse(status_code=503,content={"status":"error","message":"Stripe no está configurado."})
    secret=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
    if not secret:
        return JSONResponse(status_code=503,content={"status":"error","message":"Falta STRIPE_WEBHOOK_SECRET."})
    body=await request.body()
    signature=request.headers.get("stripe-signature","")
    try:
        event=stripe.Webhook.construct_event(body,signature,secret)
    except Exception:
        return JSONResponse(status_code=400,content={"status":"error","message":"Firma de webhook no válida."})
    event_type=stripe_obj_value(event,"type","")
    if event_type in ("customer.subscription.deleted","customer.subscription.paused"):
        pass
    return {"status":"ok","received":True,"event":event_type}

# -------- PÁGINA Y RUTAS ORIGINALES CONSERVADAS --------
@app.get("/",response_class=HTMLResponse)
async def home():
    path=os.path.join(STATIC_DIR,"index.html")
    try:
        with open(path,"r",encoding="utf-8") as f:return HTMLResponse(f.read())
    except Exception:return HTMLResponse("<h1>¿QUÉ QUIERES LLEVAR?</h1><p>No se pudo cargar la aplicación.</p>",status_code=500)

@app.get("/health")
async def health():
    return {"status":"ok","version":VERSION,"source_version":SOURCE_VERSION,"app":APP_NAME,"ready":True,"gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY","").strip()),"stripe_configured":stripe_ready(),"paywall_enabled":PAYWALL_ENABLED}

@app.get("/api/config")
async def config():
    return {
        "status":"ok","app":APP_NAME,"version":VERSION,"language":"es",
        "free":not PAYWALL_ENABLED,"login_required":False,
        "payment_required":PAYWALL_ENABLED,"server_storage":False,
        "features":{"dviajeros":True,"visa":True,"flights":True,"airlines":True,"charters":True,"pdf":True,"official_sources":True},
        "official_sources":official_sources()
    }

@app.post("/api/flight")
async def flight(data:FlightRequest):return call_engine("analyze_flight",data)
@app.post("/api/booking")
async def booking(data:BookingRequest):return call_engine("booking_simulation",data)
@app.post("/api/connection")
async def connection(data:ConnectionRequest):return call_engine("connection_analysis",data)
@app.post("/api/baggage")
async def baggage(data:BaggageRequest):return call_engine("baggage_rules",data)
@app.post("/api/item")
async def item(data:ItemRequest):return call_engine("item_analysis",data)
@app.post("/api/cuba")
async def cuba(data:CubaRequest):return call_engine("cuba_check",data)
@app.post("/api/cuba/entry")
async def cuba_entry(data:CubaEntryRequest):return call_engine("cuba_entry",data)
@app.post("/api/documents")
async def documents(data:DocumentRequest):return call_engine("document_analysis",data)
@app.post("/api/practice")
async def practice(data:PracticeRequest):return call_engine("practice_scenario",data)
@app.post("/api/dviajeros")
async def dviajeros(data:DViajeroRequest):return call_engine("dviajeros_simulation",data)
@app.post("/api/visa")
async def visa(data:VisaRequest):return call_engine("visa_simulation",data)

@app.get("/api/sources")
async def sources_get(topic:str="official",query:str="",country:str="",airline:str=""):
    return {"status":"ok","topic":topic,"sources":get_sources(topic,query,country,airline)}
@app.post("/api/sources")
async def sources_post(data:SourceRequest):
    return {"status":"ok","topic":data.topic,"sources":get_sources(data.topic,data.query,data.country,data.airline)}
@app.get("/api/official")
async def official(topic:str="",country:str="",airline:str=""):
    return {"status":"ok","topic":topic,"sources":official_sources(topic,country,airline)}

@app.get("/api/airlines")
async def airlines_get(query:str=""):
    return {"status":"ok","airlines":get_airlines(query),"charters":get_charters(query)}
@app.post("/api/airlines")
async def airlines_post(data:AirlineRequest):
    q=getattr(data,"query","") or getattr(data,"name","") or getattr(data,"airline","")
    return {"status":"ok","airlines":get_airlines(q),"charters":get_charters(q)}
@app.get("/api/charters")
async def charters(query:str=""):
    return {"status":"ok","charters":get_charters(query)}
@app.get("/api/cuba-official")
async def cuba_official():return {"status":"ok","sources":official_sources("cuba")}
@app.get("/api/airlines-cuba")
async def airlines_cuba():return {"status":"ok","airlines":get_airlines(),"charters":get_charters()}

@app.post("/api/solve")
async def solve(data:SolveRequest):return call_engine("solve",data)
@app.post("/api/guide")
async def guide(data:GuideRequest):return call_engine("build_guide",data)

STYLES=getSampleStyleSheet()
STYLE=STYLES["BodyText"]
TITLE=STYLES["Title"]
TITLE.alignment=TA_CENTER

def add_line(story,label,value):
    if value in ("",None,False,[],{}):return
    if isinstance(value,(dict,list)):value=json.dumps(value,ensure_ascii=False)
    story.extend([Paragraph(f"<b>{label}:</b> {value}",STYLE),Spacer(1,4)])

def make_pdf(data,lang="es",title=None):
    b=io.BytesIO()
    doc=SimpleDocTemplate(b,pagesize=letter,rightMargin=.55*inch,leftMargin=.55*inch,topMargin=.55*inch,bottomMargin=.55*inch)
    story=[Paragraph(title or APP_NAME,TITLE),Spacer(1,8),Paragraph("Guía independiente de preparación. No es un documento oficial ni sustituye las instrucciones de las autoridades.",STYLE),Spacer(1,10)]
    story.append(Paragraph("D’VIAJEROS",STYLES["Heading2"]))
    dv=[
        ("1. Entrar al sitio oficial","Abre D’Viajeros y comienza el formulario."),
        ("2. Datos del viajero","Completa los datos que solicita el formulario."),
        ("3. Pasaporte","Escribe los datos exactamente como aparecen en el documento."),
        ("4. Viaje","Completa la información solicitada sobre tu entrada y estancia."),
        ("5. Revisar","Comprueba los datos antes de terminar."),
        ("6. Resultado","Conserva el resultado y el QR que entregue el sistema.")
    ]
    for a,c in dv:add_line(story,a,c)
    story.append(Spacer(1,7));story.append(Paragraph("VISA PARA CUBA",STYLES["Heading2"]))
    visa=[
        ("Visa electrónica","Consulta el portal oficial, completa la solicitud, realiza el proceso indicado y conserva el resultado recibido."),
        ("Trámite consular","Si tu caso corresponde al consulado/embajada, consulta directamente los requisitos, costo, forma de pago y tiempo vigente."),
        ("Aeropuerto","Si tu caso permite obtenerla en el aeropuerto, consulta antes del viaje el proceso vigente, el lugar y el costo correspondiente.")
    ]
    for a,c in visa:add_line(story,a,c)
    story.append(Spacer(1,7));story.append(Paragraph("ENLACES OFICIALES",STYLES["Heading2"]))
    for s in official_sources("cuba"):
        if isinstance(s,dict):
            u=s.get("exact_url") or s.get("deep_url") or s.get("section_url") or s.get("url")
            if u:add_line(story,s.get("title") or s.get("name") or "Fuente oficial",u)
    story.extend([Spacer(1,12),Paragraph(f"Generado: {now()} — {APP_NAME} | May Roga LLC",STYLE)])
    doc.build(story);b.seek(0);return b

@app.post("/api/pdf")
async def pdf(data:PDFRequest):
    b=make_pdf(model_dict(data.data),data.lang,data.title)
    return StreamingResponse(b,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=mi-guia-que-quieres-llevar.pdf"})

@app.post("/api/pdf/import")
async def pdf_import(data:PDFImportRequest):
    return {"status":"verify","recovered":False,"data":{},"next_action":"Esta versión utiliza el PDF como guía de pasos. Revisa siempre el sitio oficial."}

@app.post("/api/export")
async def export_trip(data:TripExportRequest):
    return {"status":"ok","data":model_dict(data.data),"next_action":"Puedes conservar esta información localmente."}

@app.post("/api/local-data")
async def local_data(data:DeleteLocalRequest):
    return {"status":"ok","message":"La aplicación no necesita conservar tus datos personales en el servidor."}

@app.get("/api/legal")
async def legal():
    return {"status":"ok","title":"Aviso legal","message":"¿QUÉ QUIERES LLEVAR? es una herramienta independiente de orientación y preparación de May Roga LLC.","points":["No es una agencia de viajes.","No es una aerolínea ni operador charter.","No realiza trámites oficiales en nombre del viajero.","No vende ni emite boletos.","No sustituye a las autoridades ni a los proveedores oficiales.","La información puede cambiar y debe comprobarse en la fuente oficial."]}

@app.get("/api/ping")
async def ping():return {"status":"ok","version":VERSION,"time":now()}

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    return JSONResponse(status_code=422,content={"status":"error","message":"Faltan o no son válidos algunos datos.","next_action":"Revisa los datos e inténtalo nuevamente.","details":exc.errors()})

@app.exception_handler(Exception)
async def global_error(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"status":"error","message":"La operación no pudo completarse.","next_action":"Inténtalo nuevamente."})

__all__=["app"]
