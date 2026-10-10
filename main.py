
from __future__ import annotations
import os,json,re,io,datetime,time,hmac,hashlib,urllib.parse,urllib.request,urllib.error
from typing import Any,Dict
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
APP_URL=os.getenv("APP_URL","https://qu-quieres-llevar.onrender.com").strip().rstrip("/")
SESSION_COOKIE="qql_access"
COOKIE_MAX_AGE=60*60*24*35
SESSION_SECONDS=20*60
PUBLIC_API_PATHS={"/api/config","/api/access-status","/api/payment/options","/api/create-checkout-session","/api/payment/verify","/api/login","/api/logout","/api/stripe/webhook","/api/legal","/api/ping"}
app=FastAPI(title=APP_NAME,version=VERSION)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

def now():return datetime.datetime.now().isoformat(timespec="seconds")
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
        except Exception as e:return {"status":"error","message":str(e),"next_action":"Inténtalo nuevamente."}
    except Exception as e:return {"status":"error","message":str(e),"next_action":"Inténtalo nuevamente."}

# STRIPE: precios, sesiones firmadas y verificación de acceso
def _secret_key():
    key=os.getenv("STRIPE_SECRET_KEY","").strip() or os.getenv("ADMIN_PASSWORD","").strip()
    if not key:raise RuntimeError("Configura STRIPE_SECRET_KEY o ADMIN_PASSWORD en Render.")
    return key.encode("utf-8")
def _sign(value:str)->str:
    return hmac.new(_secret_key(),value.encode("utf-8"),hashlib.sha256).hexdigest()
def _make_cookie(kind:str,value:str)->str:
    issued=str(int(time.time()))
    payload=f"{kind}.{issued}.{value}"
    return payload+"."+_sign(payload)
def _read_cookie(raw:str|None):
    if not raw:return None
    try:
        kind,issued,value,sig=raw.split(".",3)
        payload=f"{kind}.{issued}.{value}"
        if not hmac.compare_digest(sig,_sign(payload)):return None
        if int(issued)>int(time.time())+60 or int(time.time())-int(issued)>COOKIE_MAX_AGE:return None
        if kind not in ("admin","single","subscription"):return None
        return {"kind":kind,"value":value,"issued":int(issued)}
    except Exception:return None
def _stripe_request(method:str,path:str,params:dict|None=None):
    key=os.getenv("STRIPE_SECRET_KEY","").strip()
    if not key:raise RuntimeError("Falta configurar STRIPE_SECRET_KEY en Render.")
    url="https://api.stripe.com/v1/"+path.lstrip("/")
    data=None
    headers={"Authorization":"Bearer "+key,"Content-Type":"application/x-www-form-urlencoded"}
    if method.upper()=="GET" and params:url+="?"+urllib.parse.urlencode(params,doseq=True)
    elif params:data=urllib.parse.urlencode(params,doseq=True).encode("utf-8")
    req=urllib.request.Request(url,data=data,headers=headers,method=method.upper())
    try:
        with urllib.request.urlopen(req,timeout=20) as resp:return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail=json.loads(e.read().decode("utf-8"))
            msg=detail.get("error",{}).get("message","Stripe rechazó la solicitud.")
        except Exception:msg="Stripe rechazó la solicitud."
        raise RuntimeError(msg)
def _price_id(plan:str)->str:
    return os.getenv("STRIPE_PRICE_ID"+plan,"").strip()
def _session(session_id:str)->dict:
    if not session_id or not session_id.startswith("cs_"):return {}
    return _stripe_request("GET","checkout/sessions/"+urllib.parse.quote(session_id,safe=""),{"expand[]":["subscription","line_items"]})
def _session_price(session:dict)->str:
    items=session.get("line_items",{}).get("data",[]) if isinstance(session.get("line_items"),dict) else []
    return str(items[0].get("price",{}).get("id","")) if items else ""
def _subscription_active(session:dict)->bool:
    sub=session.get("subscription")
    if isinstance(sub,str):
        sub=_stripe_request("GET","subscriptions/"+urllib.parse.quote(sub,safe=""))
    if not isinstance(sub,dict) or sub.get("status") not in ("active","trialing"):return False
    end=sub.get("current_period_end")
    if end and int(end)<=int(time.time()):return False
    items=sub.get("items",{}).get("data",[])
    return any(str(x.get("price",{}).get("id",""))==_price_id("2") for x in items)
def _payment_plan(session_id:str)->str|None:
    try:
        session=_session(session_id)
        if session.get("status")!="complete":return None
        price=_session_price(session)
        if session.get("mode")=="payment" and session.get("payment_status")=="paid" and price==_price_id("1"):return "single"
        if session.get("mode")=="subscription" and session.get("payment_status") in ("paid","no_payment_required") and price==_price_id("2") and _subscription_active(session):return "subscription"
    except Exception:return None
    return None
def _cookie_session(cookie:dict):
    try:
        session_id,expires=cookie["value"].rsplit("~",1)
        return session_id,int(expires)
    except Exception:return None,0
def _subscription_from_cookie(cookie:dict)->bool:
    session_id,_=_cookie_session(cookie)
    return bool(session_id and _payment_plan(session_id)=="subscription")
def _has_access(request:Request)->bool:
    cookie=_read_cookie(request.cookies.get(SESSION_COOKIE))
    if not cookie:return False
    if cookie["kind"]=="admin":return hmac.compare_digest(cookie["value"],"admin")
    session_id,expires=_cookie_session(cookie)
    if expires<=int(time.time()):return False
    plan=_payment_plan(session_id)
    if cookie["kind"]=="single":return plan=="single"
    if cookie["kind"]=="subscription":return plan=="subscription"
    return False
def _set_access_cookie(response,kind:str,session_id:str,max_age:int):
    value=f"{session_id}~{int(time.time())+SESSION_SECONDS}"
    response.set_cookie(SESSION_COOKIE,_make_cookie(kind,value),max_age=max_age,httponly=True,secure=APP_URL.startswith("https://"),samesite="lax",path="/")
def _set_admin_cookie(response):
    response.set_cookie(SESSION_COOKIE,_make_cookie("admin","admin"),max_age=COOKIE_MAX_AGE,httponly=True,secure=APP_URL.startswith("https://"),samesite="lax",path="/")

@app.middleware("http")
async def access_wall(request:Request,call_next):
    if request.url.path.startswith("/api/") and request.url.path not in PUBLIC_API_PATHS and not _has_access(request):
        return JSONResponse(status_code=402,content={"status":"payment_required","message":"Necesitas comprar una sesión o tener una suscripción activa y una sesión de 20 minutos vigente para continuar.","next_action":"Abre la pantalla de acceso."})
    return await call_next(request)

@app.get("/",response_class=HTMLResponse)
async def home():
    path=os.path.join(STATIC_DIR,"index.html")
    try:
        with open(path,"r",encoding="utf-8") as f:return HTMLResponse(f.read())
    except Exception:return HTMLResponse("<h1>¿QUÉ QUIERES LLEVAR?</h1><p>No se pudo cargar la aplicación.</p>",status_code=500)

@app.get("/health")
async def health():
    return {"status":"ok","version":VERSION,"source_version":SOURCE_VERSION,"app":APP_NAME,"ready":True,"gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY","").strip())}

@app.get("/api/access-status")
async def access_status(request:Request):
    cookie=_read_cookie(request.cookies.get(SESSION_COOKIE))
    if not cookie:return {"status":"ok","allowed":False,"kind":None,"session_minutes":20}
    if cookie["kind"]=="admin" and hmac.compare_digest(cookie["value"],"admin"):
        return {"status":"ok","allowed":True,"kind":"admin","session_minutes":20}
    session_id,expires=_cookie_session(cookie)
    plan=_payment_plan(session_id) if session_id else None
    if plan=="single":
        if expires>int(time.time()):
            return {"status":"ok","allowed":True,"kind":"single","session_minutes":20,"single_use":True}
        return {"status":"ok","allowed":False,"kind":None,"session_minutes":20,"message":"La sesión única de 20 minutos terminó."}
    if plan=="subscription":
        if expires<=int(time.time()):
            response=JSONResponse(content={"status":"ok","allowed":True,"kind":"subscription","session_minutes":20,"subscription_repeats":True,"session_expired":True})
            _set_access_cookie(response,"subscription",session_id,COOKIE_MAX_AGE)
            return response
        return {"status":"ok","allowed":True,"kind":"subscription","session_minutes":20,"subscription_repeats":True,"session_expired":False}
    return {"status":"ok","allowed":False,"kind":None,"session_minutes":20}

@app.get("/api/payment/options")
async def payment_options():
    return {"status":"ok","options":[{"id":1,"title":"Sesión única · $15.99","detail":"Un solo acceso de 20 minutos; pago único, no recurrente.","configured":bool(_price_id("1"))},{"id":2,"title":"Suscripción mensual · $25.99","detail":"Sesiones de 20 minutos ilimitadas durante el período mensual de suscripción activa.","configured":bool(_price_id("2"))}]}

@app.post("/api/create-checkout-session")
async def create_checkout_session(request:Request):
    try:body=await request.json()
    except Exception:body={}
    plan=str(body.get("plan",""))
    if plan not in ("1","2"):return JSONResponse(status_code=400,content={"message":"Selecciona una opción de pago válida."})
    price_id=_price_id(plan)
    if not price_id:return JSONResponse(status_code=503,content={"message":f"Falta configurar STRIPE_PRICE_ID{plan} en Render."})
    try:
        price=_stripe_request("GET","prices/"+urllib.parse.quote(price_id,safe=""))
        amount=price.get("unit_amount")
        currency=(price.get("currency") or "usd").lower()
        recurring=price.get("recurring")
        if plan=="1" and (recurring or amount!=1599 or currency!="usd"):
            raise RuntimeError("STRIPE_PRICE_ID1 debe ser un precio de pago único de USD 15.99.")
        if plan=="2" and (not recurring or amount!=2599 or currency!="usd" or recurring.get("interval")!="month" or int(recurring.get("interval_count",1))!=1):
            raise RuntimeError("STRIPE_PRICE_ID2 debe ser una suscripción de USD 25.99 facturada mensualmente.")
        mode="payment" if plan=="1" else "subscription"
        params={"mode":mode,"line_items[0][price]":price_id,"line_items[0][quantity]":"1","success_url":APP_URL+"/?payment=success&session_id={CHECKOUT_SESSION_ID}","cancel_url":APP_URL+"/?payment=cancel","client_reference_id":"qql_plan_"+plan,"metadata[plan]":plan,"allow_promotion_codes":"false"}
        if plan=="2":params["subscription_data[metadata][plan]"]="2"
        session=_stripe_request("POST","checkout/sessions",params)
        if not session.get("url"):raise RuntimeError("Stripe no devolvió el enlace de pago.")
        return {"status":"ok","url":session["url"],"plan":plan}
    except Exception as e:return JSONResponse(status_code=502,content={"message":str(e) or "No se pudo iniciar el pago de Stripe."})

@app.post("/api/payment/verify")
async def verify_payment(request:Request):
    try:body=await request.json()
    except Exception:body={}
    sid=str(body.get("session_id","")).strip()
    plan=_payment_plan(sid)
    if not plan:return JSONResponse(status_code=402,content={"allowed":False,"message":"Stripe todavía no confirma el pago y el plan correcto."})
    if plan=="single":
        response=JSONResponse(content={"status":"ok","allowed":True,"plan":"single","session_minutes":20,"message":"Pago confirmado. Tienes una sesión de 20 minutos."})
        _set_access_cookie(response,"single",sid,SESSION_SECONDS)
        return response
    response=JSONResponse(content={"status":"ok","allowed":True,"plan":"subscription","session_minutes":20,"message":"Suscripción confirmada. Puedes iniciar sesiones de 20 minutos mientras permanezca activa."})
    _set_access_cookie(response,"subscription",sid,COOKIE_MAX_AGE)
    return response

@app.post("/api/login")
async def admin_login(request:Request):
    try:body=await request.json()
    except Exception:body={}
    expected_user=os.getenv("ADMIN_USERNAME","").strip()
    expected_password=os.getenv("ADMIN_PASSWORD","")
    username=str(body.get("username",""))
    password=str(body.get("password",""))
    if not expected_user or not expected_password:
        return JSONResponse(status_code=503,content={"allowed":False,"message":"Configura ADMIN_USERNAME y ADMIN_PASSWORD en Render."})
    if not hmac.compare_digest(username,expected_user) or not hmac.compare_digest(password,expected_password):
        return JSONResponse(status_code=401,content={"allowed":False,"message":"Usuario o contraseña incorrectos."})
    response=JSONResponse(content={"status":"ok","allowed":True,"kind":"admin"})
    _set_admin_cookie(response)
    return response

@app.post("/api/logout")
async def admin_logout():
    response=JSONResponse(content={"status":"ok"})
    response.delete_cookie(SESSION_COOKIE,path="/")
    return response

@app.post("/api/stripe/webhook")
async def stripe_webhook(request:Request):
    raw=await request.body()
    signature=request.headers.get("stripe-signature","")
    secret=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
    if not secret:return JSONResponse(status_code=503,content={"status":"error","message":"Falta STRIPE_WEBHOOK_SECRET en Render."})
    try:
        parts={k:v for item in signature.split(",") if "=" in item for k,v in [item.split("=",1)]}
        ts=parts.get("t","")
        v1=parts.get("v1","")
        if not ts or not v1 or abs(int(time.time())-int(ts))>300:raise ValueError()
        expected=hmac.new(secret.encode(),ts.encode()+b"."+raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,v1):raise ValueError()
        event=json.loads(raw.decode("utf-8"))
        return {"status":"ok","received":True,"event":event.get("type","")}
    except Exception:return JSONResponse(status_code=400,content={"status":"error","message":"Firma de Stripe inválida."})

@app.get("/api/config")
async def config():
    return {"status":"ok","app":APP_NAME,"version":VERSION,"language":"es","free":False,"login_required":True,"payment_required":True,"server_storage":False,"stripe_configured":bool(os.getenv("STRIPE_SECRET_KEY","")),"publishable_key":os.getenv("STRIPE_PUBLISHABLE_KEY",""),"features":{"dviajeros":True,"visa":True,"flights":True,"airlines":True,"charters":True,"pdf":True,"official_sources":True},"official_sources":official_sources()}

# RUTAS ORIGINALES: se conservan
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
