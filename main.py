from __future__ import annotations
import os,json,io,datetime,time,hmac,hashlib,base64,re
from typing import Any
from urllib.parse import urlparse
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph,Spacer,SimpleDocTemplate
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
import cuba_engine as engine
try:
    import stripe
except ImportError:
    stripe=None
from schemas import *

VERSION="17.1.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
STATIC_DIR="static"
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
APP_URL=os.getenv("APP_URL","https://qu-quieres-llevar.onrender.com").rstrip("/")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","").strip()
STRIPE_PRICE_ID2=os.getenv("STRIPE_PRICE_ID2","").strip()
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
SESSION_SIGNING_SECRET=os.getenv("SESSION_SIGNING_SECRET","").strip()
COOKIE_NAME="qql_access"
ENTITLEMENT_COOKIE="qql_entitlement"
SESSION_SECONDS=20*60
SUB_ENTITLEMENT_SECONDS=400*24*60*60
COOKIE_SECURE=urlparse(APP_URL).scheme=="https"
app=FastAPI(title=APP_NAME,version=VERSION)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")
if stripe and STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

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
    if not fn:return {"status":"error","message":f"Función no disponible: {name}","next_action":"Revisa la aplicación."}
    d=model_dict(data)
    try:return normalize_result(fn(d))
    except TypeError:
        try:return normalize_result(fn(**d))
        except Exception:return {"status":"error","message":"La operación no pudo completarse.","next_action":"Inténtalo nuevamente."}
    except Exception:return {"status":"error","message":"La operación no pudo completarse.","next_action":"Inténtalo nuevamente."}

def signing_key():
    return (SESSION_SIGNING_SECRET or STRIPE_SECRET_KEY or ADMIN_PASSWORD or "").encode()

def make_token(data,max_age):
    key=signing_key()
    if not key:raise RuntimeError("Falta SESSION_SIGNING_SECRET en Render.")
    payload=dict(data)
    payload["exp"]=int(time.time())+int(max_age)
    raw=base64.urlsafe_b64encode(json.dumps(payload,separators=(",",":"),ensure_ascii=False).encode()).decode().rstrip("=")
    sig=hmac.new(key,raw.encode(),hashlib.sha256).hexdigest()
    return raw+"."+sig

def read_token(token):
    if not token or "." not in token or not signing_key():return None
    try:
        raw,sig=token.rsplit(".",1)
        expected=hmac.new(signing_key(),raw.encode(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig,expected):return None
        data=json.loads(base64.urlsafe_b64decode(raw+"="*(-len(raw)%4)))
        if int(data.get("exp",0))<int(time.time()):return None
        return data
    except Exception:return None

def get_access(request):
    return read_token(request.cookies.get(COOKIE_NAME,""))

def get_entitlement(request):
    return read_token(request.cookies.get(ENTITLEMENT_COOKIE,""))

def set_access_cookie(response,kind,extra=None):
    data={"kind":kind,"issued":int(time.time())}
    if extra:data.update(extra)
    response.set_cookie(COOKIE_NAME,make_token(data,SESSION_SECONDS),max_age=SESSION_SECONDS,httponly=True,secure=COOKIE_SECURE,samesite="lax",path="/")

def set_entitlement_cookie(response,kind,extra=None):
    data={"kind":kind,"issued":int(time.time())}
    if extra:data.update(extra)
    age=SUB_ENTITLEMENT_SECONDS if kind=="subscription" else SESSION_SECONDS
    response.set_cookie(ENTITLEMENT_COOKIE,make_token(data,age),max_age=age,httponly=True,secure=COOKIE_SECURE,samesite="lax",path="/")

def clear_access_cookies(response):
    response.delete_cookie(COOKIE_NAME,path="/")
    response.delete_cookie(ENTITLEMENT_COOKIE,path="/")

def safe_stripe_object(obj):
    if hasattr(obj,"to_dict_recursive"):return obj.to_dict_recursive()
    if isinstance(obj,dict):return obj
    return {}

def stripe_ready():
    return bool(stripe and STRIPE_SECRET_KEY)

def price_for(plan):
    if plan in ("single","1","one_time"):return STRIPE_PRICE_ID1,"payment"
    if plan in ("subscription","2","monthly"):return STRIPE_PRICE_ID2,"subscription"
    return None,None

def stripe_subscription_active(subscription_id):
    if not stripe_ready() or not subscription_id:return False
    try:
        sub=safe_stripe_object(stripe.Subscription.retrieve(subscription_id))
        return sub.get("status") in ("active","trialing")
    except Exception:return False

def response_error(message,status=400):
    return JSONResponse({"status":"error","allowed":False,"message":message},status_code=status)

# Acceso público limitado a configuración, pagos y autenticación.
PUBLIC_API={
    "/api/config","/api/health","/api/ping","/api/legal",
    "/api/v1/access/status","/api/v1/access/verify",
    "/api/v1/access/restore","/api/v1/stripe/create-checkout",
    "/api/v1/admin/login","/api/v1/stripe/webhook",
    "/api/access-status","/api/payment/options",
    "/api/payment/verify","/api/create-checkout-session",
    "/api/session/resume","/api/login"
}
PUBLIC_PREFIXES=("/api/v1/access/","/api/v1/stripe/")

@app.middleware("http")
async def require_service_access(request:Request,call_next):
    path=request.url.path
    if path.startswith("/api/") and path not in PUBLIC_API:
        if path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)
        token=get_access(request)
        if not token:
            return JSONResponse({"status":"payment_required","message":"Necesitas una sesión activa para usar esta función."},status_code=401)
        if token.get("kind")!="admin" and int(token.get("exp",0))<int(time.time()):
            return JSONResponse({"status":"session_expired","message":"Tu sesión de 20 minutos terminó."},status_code=401)
    return await call_next(request)

# Botón pequeño de administración inyectado en la página sin reemplazar el HTML.
ADMIN_CORNER=r"""
<style>
#qql-admin-corner{position:fixed;top:5px;right:7px;z-index:2147483000;font:11px Arial,sans-serif}
#qql-admin-open{border:1px solid #777;border-radius:4px;background:#111;color:#fff;padding:3px 6px;font-size:9px;opacity:.38;cursor:pointer}
#qql-admin-open:hover,#qql-admin-open:focus{opacity:1}
#qql-admin-box{display:none;position:absolute;top:22px;right:0;width:235px;padding:12px;background:#111;color:#fff;border:1px solid #666;border-radius:7px;box-shadow:0 5px 20px #0008}
#qql-admin-box input{box-sizing:border-box;width:100%;margin:5px 0;padding:9px;background:#fff;color:#111;border:1px solid #aaa;border-radius:4px;font-size:14px}
#qql-admin-box button{cursor:pointer;padding:7px 10px;border:1px solid #888;border-radius:4px}
#qql-admin-submit{background:#fff;color:#111}
#qql-admin-close{float:right;background:#333;color:#fff}
#qql-admin-message{font-size:11px;overflow-wrap:anywhere;margin-top:7px}
</style>
<div id="qql-admin-corner">
<button id="qql-admin-open" type="button" aria-label="Acceso privado de administración" title="Acceso privado">Acceso</button>
<div id="qql-admin-box" role="dialog" aria-label="Entrada gratuita de administración">
<button id="qql-admin-close" type="button">×</button>
<strong>Acceso privado gratuito</strong>
<form id="qql-admin-form" autocomplete="on">
<input name="username" type="text" placeholder="USERNAME" aria-label="USERNAME" autocomplete="username" required>
<input name="password" type="password" placeholder="PASSWORD" aria-label="PASSWORD" autocomplete="current-password" required>
<button id="qql-admin-submit" type="submit">Entrar</button>
<div id="qql-admin-message" role="status"></div>
</form>
</div>
</div>
<script>
(function(){
const open=document.getElementById("qql-admin-open");
const box=document.getElementById("qql-admin-box");
const close=document.getElementById("qql-admin-close");
const form=document.getElementById("qql-admin-form");
const msg=document.getElementById("qql-admin-message");
if(!open||!box||!form)return;
open.addEventListener("click",()=>{box.style.display=box.style.display==="block"?"none":"block";});
close.addEventListener("click",()=>{box.style.display="none";});
form.addEventListener("submit",async function(e){
e.preventDefault();msg.textContent="Verificando…";
const fd=new FormData(form);
try{
const r=await fetch("/api/v1/admin/login",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:fd.get("username"),password:fd.get("password")})});
const d=await r.json();
if(r.ok&&d.status==="ok"&&d.allowed){msg.textContent="Acceso autorizado.";location.reload();return;}
msg.textContent=d.message||"No se pudo iniciar sesión.";
}catch(e){msg.textContent="No se pudo conectar. Inténtalo de nuevo.";}
});
})();
</script>
"""

@app.get("/",response_class=HTMLResponse)
async def home():
    path=os.path.join(STATIC_DIR,"index.html")
    try:
        with open(path,"r",encoding="utf-8") as f:
            page=f.read()
        if "qql-admin-corner" not in page:
            if re.search(r"</body\s*>",page,re.I):
                page=re.sub(r"</body\s*>",lambda m:ADMIN_CORNER+m.group(0),page,count=1,flags=re.I)
            else:page+=ADMIN_CORNER
        return HTMLResponse(page)
    except Exception:
        return HTMLResponse("<h1>¿QUÉ QUIERES LLEVAR?</h1><p>No se pudo cargar la aplicación.</p>",status_code=500)

@app.get("/health")
@app.get("/api/health")
async def health():
    return {"status":"ok","version":VERSION,"source_version":SOURCE_VERSION,"app":APP_NAME,"ready":True,"stripe_configured":stripe_ready(),"gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY","").strip())}

@app.get("/api/config")
async def config():
    return {"status":"ok","app":APP_NAME,"version":VERSION,"language":"es","free":False,"login_required":True,"payment_required":True,"session_minutes":20,"server_storage":False,"features":{"dviajeros":True,"visa":True,"flights":True,"airlines":True,"charters":True,"pdf":True,"official_sources":True},"official_sources":official_sources()}

@app.post("/api/v1/stripe/create-checkout")
@app.post("/api/create-checkout-session")
async def create_checkout(request:Request):
    if not stripe_ready():return response_error("El pago no está configurado. Contacta al administrador.",503)
    try:
        data=await request.json()
        plan=str(data.get("plan",""))
        price_id,mode=price_for(plan)
        if not price_id:return response_error("El plan solicitado no está disponible.")
        params={
            "mode":mode,
            "line_items":[{"price":price_id,"quantity":1}],
            "success_url":APP_URL+"/?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url":APP_URL+"/",
            "client_reference_id":"qql",
            "metadata":{"app":"qql","plan":plan},
            "allow_promotion_codes":True
        }
        if mode=="subscription":params["subscription_data"]={"metadata":{"app":"qql","plan":"subscription"}}
        session=stripe.checkout.Session.create(**params)
        return {"status":"ok","url":session.url,"session_id":session.id}
    except Exception:return response_error("No se pudo iniciar el pago. Comprueba la configuración de Stripe.",502)

@app.get("/api/v1/access/status")
@app.get("/api/access-status")
async def access_status(request:Request):
    access=get_access(request)
    if access:
        kind=access.get("kind","single")
        if kind=="admin":return {"status":"ok","allowed":True,"kind":"admin","admin":True,"free":True,"session_expired":False}
        return {"status":"ok","allowed":True,"kind":kind,"session_expired":False,"expires_at":access.get("exp")}
    entitlement=get_entitlement(request)
    if entitlement and entitlement.get("kind")=="subscription":
        active=stripe_subscription_active(entitlement.get("subscription_id"))
        if active:return {"status":"ok","allowed":False,"kind":"subscription","session_expired":True,"subscription_active":True}
    return {"status":"ok","allowed":False,"session_expired":True}

@app.post("/api/v1/access/verify")
@app.post("/api/payment/verify")
async def verify_payment(request:Request):
    if not stripe_ready():return response_error("Stripe no está configurado.",503)
    try:
        data=await request.json()
        sid=str(data.get("session_id","")).strip()
        if not sid or len(sid)>250:return response_error("Falta el identificador del pago.")
        session=safe_stripe_object(stripe.checkout.Session.retrieve(sid,expand=["subscription","payment_intent"]))
        if session.get("status")!="complete":return response_error("El pago todavía no está completado.",402)
        meta=session.get("metadata") or {}
        if meta.get("app")!="qql":return response_error("El pago no corresponde a esta aplicación.",403)
        mode=session.get("mode")
        if mode=="payment":
            if session.get("payment_status")!="paid":return response_error("Stripe todavía no confirma el pago.",402)
            response=JSONResponse({"status":"ok","allowed":True,"kind":"single","session_minutes":20})
            set_access_cookie(response,"single")
            set_entitlement_cookie(response,"single")
            return response
        if mode=="subscription":
            sub=session.get("subscription")
            if isinstance(sub,dict):sub_id=sub.get("id");sub_data=sub
            else:
                sub_id=sub
                sub_data=safe_stripe_object(stripe.Subscription.retrieve(sub_id)) if sub_id else {}
            if not sub_id or sub_data.get("status") not in ("active","trialing"):
                return response_error("La suscripción no está activa. Comprueba el pago en Stripe.",402)
            extra={"subscription_id":sub_id,"customer_id":session.get("customer")}
            response=JSONResponse({"status":"ok","allowed":True,"kind":"subscription","session_minutes":20})
            set_access_cookie(response,"subscription",extra)
            set_entitlement_cookie(response,"subscription",extra)
            return response
        return response_error("El tipo de pago no es válido.",400)
    except Exception:return response_error("No se pudo verificar el pago. Inténtalo nuevamente.",502)

@app.post("/api/v1/access/restore")
@app.post("/api/session/resume")
async def restore_access(request:Request):
    entitlement=get_entitlement(request)
    if not entitlement or entitlement.get("kind")!="subscription":
        return response_error("No hay una suscripción disponible para renovar la sesión.",403)
    sub_id=entitlement.get("subscription_id")
    if not stripe_subscription_active(sub_id):
        response=JSONResponse({"status":"error","allowed":False,"message":"La suscripción no está activa. Comprueba su estado en Stripe."},status_code=403)
        clear_access_cookies(response)
        return response
    extra={"subscription_id":sub_id,"customer_id":entitlement.get("customer_id")}
    response=JSONResponse({"status":"ok","allowed":True,"kind":"subscription","session_minutes":20})
    set_access_cookie(response,"subscription",extra)
    set_entitlement_cookie(response,"subscription",extra)
    return response

@app.post("/api/v1/admin/login")
@app.post("/api/login")
async def admin_login(request:Request):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD or not SESSION_SIGNING_SECRET:
        return response_error("El acceso de administración no está configurado correctamente.",503)
    try:data=await request.json()
    except Exception:return response_error("Solicitud no válida.")
    username=str(data.get("username",""))
    password=str(data.get("password",""))
    if not hmac.compare_digest(username,ADMIN_USERNAME) or not hmac.compare_digest(password,ADMIN_PASSWORD):
        return response_error("Usuario o contraseña incorrectos.",401)
    response=JSONResponse({"status":"ok","allowed":True,"kind":"admin","free":True,"session_minutes":20})
    set_access_cookie(response,"admin",{"admin":True})
    return response

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    if not stripe_ready() or not STRIPE_WEBHOOK_SECRET:return response_error("Webhook no configurado.",503)
    body=await request.body()
    signature=request.headers.get("stripe-signature","")
    try:
        event=stripe.Webhook.construct_event(body,signature,STRIPE_WEBHOOK_SECRET)
        event_type=event.get("type","")
        if event_type in ("checkout.session.completed","customer.subscription.updated","customer.subscription.deleted","invoice.paid","invoice.payment_failed"):
            return {"status":"ok","received":True,"event":event_type}
        return {"status":"ok","received":True}
    except Exception:return response_error("Firma del webhook no válida.",400)

@app.get("/api/payment/options")
async def payment_options():
    return {"status":"ok","payment_required":True,"session_minutes":20,"options":[{"id":"single","plan":"single","available":bool(STRIPE_PRICE_ID1)},{"id":"subscription","plan":"subscription","available":bool(STRIPE_PRICE_ID2)}]}

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
    return {"status":"ok","sources":official_sources(topic,country,airline)}
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
@app.get("/api/v1/airlines-cuba")
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
    safe_label=str(label).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    safe_value=str(value).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    story.extend([Paragraph(f"<b>{safe_label}:</b> {safe_value}",STYLE),Spacer(1,4)])

def make_pdf(data,lang="es",title=None):
    b=io.BytesIO()
    doc=SimpleDocTemplate(b,pagesize=letter,rightMargin=.55*inch,leftMargin=.55*inch,topMargin=.55*inch,bottomMargin=.55*inch)
    heading=title or ("Cuba Travel Guide" if lang=="en" else APP_NAME)
    heading=str(heading).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    disclaimer="Independent preparation guide. This is not an official document and does not replace instructions from authorities." if lang=="en" else "Guía independiente de preparación. No es un documento oficial ni sustituye las instrucciones de las autoridades."
    story=[Paragraph(heading,TITLE),Spacer(1,8),Paragraph(disclaimer,STYLE),Spacer(1,10)]
    story.append(Paragraph("D’VIAJEROS",STYLES["Heading2"]))
    dv=[("1. Open the official site","Open D’Viajeros and start the form."),("2. Traveler information","Complete the information requested."),("3. Passport","Enter details exactly as shown on the document."),("4. Trip","Complete the requested entry and stay information."),("5. Review","Check the information before finishing."),("6. Result","Keep the result and QR code issued by the system.")]
    if lang!="en":dv=[("1. Entrar al sitio oficial","Abre D’Viajeros y comienza el formulario."),("2. Datos del viajero","Completa los datos que solicita el formulario."),("3. Pasaporte","Escribe los datos exactamente como aparecen en el documento."),("4. Viaje","Completa la información solicitada sobre tu entrada y estancia."),("5. Revisar","Comprueba los datos antes de terminar."),("6. Resultado","Conserva el resultado y el QR que entregue el sistema.")]
    for a,c in dv:add_line(story,a,c)
    story.extend([Spacer(1,7),Paragraph("VISA FOR CUBA" if lang=="en" else "VISA PARA CUBA",STYLES["Heading2"])])
    visa=[("Electronic visa","Check the official portal, complete the steps, and keep the result."),("Consular process","Check current requirements, fees, payment methods and processing times with the consulate."),("Airport option","Before traveling, confirm whether this option is available for your case and its current conditions.")]
    if lang!="en":visa=[("Visa electrónica","Consulta el portal oficial, completa el proceso indicado y conserva el resultado."),("Trámite consular","Consulta los requisitos, el costo, la forma de pago y el tiempo vigente."),("Opción en aeropuerto","Confirma antes del viaje si está disponible para tu caso y cuáles son las condiciones.")]
    for a,c in visa:add_line(story,a,c)
    story.extend([Spacer(1,7),Paragraph("OFFICIAL LINKS" if lang=="en" else "ENLACES OFICIALES",STYLES["Heading2"])])
    for s in official_sources("cuba"):
        if isinstance(s,dict):
            u=s.get("exact_url") or s.get("deep_url") or s.get("section_url") or s.get("url")
            if u:add_line(story,s.get("title") or s.get("name") or "Official source",u)
    story.extend([Spacer(1,12),Paragraph(f"Generated: {now()} — {APP_NAME} | May Roga LLC",STYLE)])
    doc.build(story)
    b.seek(0)
    return b

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
