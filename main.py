from __future__ import annotations
import os,json,re,io,datetime,time,hmac,hashlib,base64,urllib.parse,urllib.request,urllib.error
from typing import Any,Dict
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph,Spacer,SimpleDocTemplate
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from xml.sax.saxutils import escape
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
app=FastAPI(title=APP_NAME,version=VERSION)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

# CONFIGURACIÓN DE STRIPE Y ACCESO
APP_URL=os.getenv("APP_URL","https://qu-quieres-llevar.onrender.com").rstrip("/")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","").strip()
STRIPE_PRICE_ID2=os.getenv("STRIPE_PRICE_ID2","").strip()
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
ACCESS_COOKIE="qql_access"
SESSION_SIGNING_SECRET=os.getenv("SESSION_SIGNING_SECRET","").strip() or STRIPE_SECRET_KEY
ACCESS_SECONDS=20*60

PUBLIC_API_PATHS={
    "/api/config","/api/legal","/api/ping",
    "/api/v1/stripe/create-checkout",
    "/api/v1/stripe/webhook",
    "/api/v1/access/verify",
    "/api/v1/access/restore",
    "/api/v1/access/status",
    "/api/v1/admin/login",
    "/api/v1/admin/logout"
}

def _b64e(raw:bytes)->str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")

def _b64d(value:str)->bytes:
    return base64.urlsafe_b64decode(value+"="*((4-len(value)%4)%4))

def make_access_token(plan:str,checkout_id:str="")->str:
    payload={
        "plan":plan,
        "checkout_id":checkout_id,
        "exp":int(time.time())+ACCESS_SECONDS
    }
    raw=json.dumps(payload,separators=(",",":"),sort_keys=True).encode()
    encoded=_b64e(raw)
    secret=(SESSION_SIGNING_SECRET or "missing-config").encode()
    sig=_b64e(hmac.new(secret,encoded.encode(),hashlib.sha256).digest())
    return encoded+"."+sig

def read_access_token(token:str):
    try:
        encoded,sig=token.split(".",1)
        secret=(SESSION_SIGNING_SECRET or "missing-config").encode()
        expected=_b64e(hmac.new(secret,encoded.encode(),hashlib.sha256).digest())
        if not hmac.compare_digest(sig,expected):
            return None
        data=json.loads(_b64d(encoded))
        if int(data.get("exp",0))<int(time.time()):
            return None
        if data.get("plan") not in ("one_time","monthly","admin"):
            return None
        return data
    except Exception:
        return None

def set_access_cookie(response,plan:str,checkout_id:str=""):
    if not SESSION_SIGNING_SECRET:
        raise RuntimeError("Falta STRIPE_SECRET_KEY para firmar la sesión.")
    response.set_cookie(
        ACCESS_COOKIE,
        make_access_token(plan,checkout_id),
        max_age=ACCESS_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/"
    )

def clear_access_cookie(response):
    response.delete_cookie(
        ACCESS_COOKIE,
        path="/",
        secure=True,
        httponly=True,
        samesite="lax"
    )

def _stripe_request(path:str,method:str="GET",form=None):
    if not STRIPE_SECRET_KEY:
        raise RuntimeError("El pago no está configurado: falta STRIPE_SECRET_KEY.")
    url="https://api.stripe.com/v1/"+path.lstrip("/")
    data=urllib.parse.urlencode(form or {},doseq=True).encode() if form is not None else None
    req=urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization":"Bearer "+STRIPE_SECRET_KEY,
            "Content-Type":"application/x-www-form-urlencoded",
            "User-Agent":"May-Roga-QQL/17.0"
        }
    )
    try:
        with urllib.request.urlopen(req,timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body=json.loads(e.read().decode("utf-8"))
        except Exception:
            body={}
        message=(body.get("error") or {}).get("message") or "Stripe no pudo completar la solicitud."
        raise ValueError(message)
    except urllib.error.URLError:
        raise RuntimeError("No se pudo conectar con Stripe. Inténtalo nuevamente.")

def stripe_ready():
    return bool(
        STRIPE_SECRET_KEY
        and STRIPE_PRICE_ID1
        and STRIPE_PRICE_ID2
        and STRIPE_WEBHOOK_SECRET
    )

def _get_price_line_items(session_id):
    result=_stripe_request(
        "checkout/sessions/"+urllib.parse.quote(session_id,safe="")+"/line_items?limit=10"
    )
    return result.get("data",[])

def _verified_checkout(session_id):
    if not re.fullmatch(r"cs_(test|live)_[A-Za-z0-9]+",session_id or ""):
        raise ValueError("La sesión de pago no es válida.")

    session=_stripe_request(
        "checkout/sessions/"+urllib.parse.quote(session_id,safe="")
    )
    if session.get("status")!="complete":
        raise ValueError("El pago todavía no está completado.")

    mode=session.get("mode")
    items=_get_price_line_items(session_id)
    price_ids=[(x.get("price") or {}).get("id") for x in items]

    # PAGO ÚNICO: $15.99, con acceso de 20 minutos desde el pago.
    if mode=="payment" and STRIPE_PRICE_ID1 in price_ids and session.get("payment_status")=="paid":
        paid_at=int(session.get("created") or time.time())
        payment_intent=session.get("payment_intent")
        if payment_intent:
            try:
                intent=_stripe_request(
                    "payment_intents/"+urllib.parse.quote(payment_intent,safe="")+"?expand[]=latest_charge"
                )
                charge=intent.get("latest_charge")
                if isinstance(charge,dict) and charge.get("created"):
                    paid_at=int(charge["created"])
            except Exception:
                pass
        if time.time()-paid_at>=ACCESS_SECONDS:
            raise ValueError("Los 20 minutos de acceso de este pago ya terminaron. Puedes iniciar otro pago.")
        return "one_time"

    # SUSCRIPCIÓN: $25.99 al mes; cada sesión tiene un máximo de 20 minutos.
    if mode=="subscription" and STRIPE_PRICE_ID2 in price_ids:
        subscription=session.get("subscription")
        if isinstance(subscription,dict):
            subscription=subscription.get("id")
        if not subscription:
            raise ValueError("No se encontró la suscripción del pago.")

        sub=_stripe_request(
            "subscriptions/"+urllib.parse.quote(subscription,safe="")
        )
        if sub.get("status") not in ("active","trialing"):
            raise ValueError("La suscripción no está activa. Revisa tu pago en Stripe.")
        if int(sub.get("current_period_end") or 0)<=int(time.time()):
            raise ValueError("El período de suscripción terminó. Renueva para continuar.")
        return "monthly"

    raise ValueError("El pago no coincide con uno de los servicios autorizados.")

@app.middleware("http")
async def require_service_access(request:Request,call_next):
    path=request.url.path

    # Los recursos estáticos y la página inicial pueden cargarse para mostrar el muro.
    # Las operaciones de servicio de la API requieren acceso válido.
    if path.startswith("/api/") and path not in PUBLIC_API_PATHS:
        token=request.cookies.get(ACCESS_COOKIE,"")
        auth=request.headers.get("authorization","")
        if not token and auth.lower().startswith("bearer "):
            token=auth[7:].strip()
        data=read_access_token(token) if token else None
        if not data:
            return JSONResponse(
                status_code=401,
                content={
                    "status":"payment_required",
                    "message":"Necesitas activar el acceso para utilizar este servicio.",
                    "next_action":"Elige un plan o inicia sesión como administrador."
                }
            )
    return await call_next(request)

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def model_dict(x):
    if x is None:
        return {}
    if isinstance(x,dict):
        return x
    if hasattr(x,"model_dump"):
        return x.model_dump(exclude_none=False)
    if hasattr(x,"dict"):
        return x.dict()
    return dict(x)

def normalize_result(result,default_sources=None):
    if result is None:
        result={}
    if hasattr(result,"model_dump"):
        result=result.model_dump()
    elif not isinstance(result,dict):
        result={"message":str(result)}
    result=dict(result)
    if not isinstance(result.get("sources"),list):
        result["sources"]=default_sources or []
    return result

def call_engine(name,data=None):
    fn=getattr(engine,name,None)
    if not fn:
        return {
            "status":"error",
            "message":f"Función no disponible: {name}",
            "next_action":"Revisa la aplicación."
        }
    d=model_dict(data)
    try:
        return normalize_result(fn(d))
    except TypeError:
        try:
            return normalize_result(fn(**d))
        except Exception:
            return {
                "status":"error",
                "message":"No se pudo completar la operación.",
                "next_action":"Inténtalo nuevamente."
            }
    except Exception:
        return {
            "status":"error",
            "message":"No se pudo completar la operación.",
            "next_action":"Inténtalo nuevamente."
        }

@app.get("/",response_class=HTMLResponse)
async def home():
    path=os.path.join(STATIC_DIR,"index.html")
    try:
        with open(path,"r",encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except Exception:
        return HTMLResponse(
            "<h1>¿QUÉ QUIERES LLEVAR?</h1><p>No se pudo cargar la aplicación.</p>",
            status_code=500
        )

@app.get("/health")
async def health():
    return {
        "status":"ok",
        "version":VERSION,
        "source_version":SOURCE_VERSION,
        "app":APP_NAME,
        "ready":True,
        "gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY","").strip()),
        "stripe_enabled":stripe_ready()
    }

@app.get("/api/config")
async def config():
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":VERSION,
        "language":"es",
        "free":False,
        "login_required":True,
        "payment_required":True,
        "stripe_enabled":stripe_ready(),
        "plans":{
            "one_time":{
                "price":"15.99",
                "currency":"usd",
                "duration_minutes":20,
                "billing":"one_time"
            },
            "monthly":{
                "price":"25.99",
                "currency":"usd",
                "duration_minutes":20,
                "unlimited_sessions":True,
                "billing":"monthly"
            }
        },
        "server_storage":False,
        "features":{
            "dviajeros":True,
            "visa":True,
            "flights":True,
            "airlines":True,
            "charters":True,
            "pdf":True,
            "official_sources":True
        },
        "official_sources":official_sources()
    }

# CREAR SESIÓN DE CHECKOUT
@app.post("/api/v1/stripe/create-checkout")
async def create_checkout(request:Request):
    try:
        body=await request.json()
        plan=str(body.get("plan","")).strip().lower()
        if plan not in ("one_time","monthly"):
            return JSONResponse(
                status_code=400,
                content={"status":"error","message":"Elige uno de los planes disponibles."}
            )
        if not STRIPE_SECRET_KEY:
            return JSONResponse(
                status_code=503,
                content={"status":"error","message":"El pago no está configurado. Falta STRIPE_SECRET_KEY en Render."}
            )

        price=STRIPE_PRICE_ID1 if plan=="one_time" else STRIPE_PRICE_ID2
        if not price:
            return JSONResponse(
                status_code=503,
                content={"status":"error","message":"Falta configurar el precio de este plan en Render."}
            )

        mode="payment" if plan=="one_time" else "subscription"
        form={
            "mode":mode,
            "line_items[0][price]":price,
            "line_items[0][quantity]":"1",
            "success_url":APP_URL+"/?payment=success&session_id={CHECKOUT_SESSION_ID}",
            "cancel_url":APP_URL+"/?payment=cancelled",
            "client_reference_id":"qql_guest",
            "metadata[app]":"qql",
            "metadata[plan]":plan,
            "allow_promotion_codes":"true"
        }
        if mode=="subscription":
            form["subscription_data[metadata][app]"]="qql"
            form["subscription_data[metadata][plan]"]="monthly"

        session=_stripe_request("checkout/sessions","POST",form)
        if not session.get("url"):
            raise RuntimeError("Stripe no devolvió una dirección de pago.")
        return {
            "status":"ok",
            "url":session["url"],
            "session_id":session.get("id"),
            "plan":plan
        }
    except ValueError as e:
        return JSONResponse(status_code=400,content={"status":"error","message":str(e)})
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status":"error","message":"No se pudo iniciar el pago. Revisa la configuración de Stripe."}
        )

# VERIFICAR PAGO Y ACTIVAR ACCESO
@app.post("/api/v1/access/verify")
async def verify_access(request:Request):
    try:
        body=await request.json()
        session_id=str(body.get("session_id","")).strip()
        plan=_verified_checkout(session_id)
        response=JSONResponse({
            "status":"ok",
            "plan":plan,
            "duration_minutes":20,
            "message":"Acceso activado."
        })
        set_access_cookie(response,plan,session_id)
        return response
    except ValueError as e:
        return JSONResponse(status_code=402,content={"status":"error","message":str(e)})
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status":"error","message":"No se pudo verificar el pago. Inténtalo nuevamente."}
        )

# RESTAURAR ACCESO CON LA SESIÓN DE STRIPE
@app.post("/api/v1/access/restore")
async def restore_access(request:Request):
    try:
        body=await request.json()
        session_id=str(body.get("session_id","")).strip()
        plan=_verified_checkout(session_id)
        response=JSONResponse({
            "status":"ok",
            "plan":plan,
            "duration_minutes":20,
            "message":"Acceso renovado por 20 minutos."
        })
        set_access_cookie(response,plan,session_id)
        return response
    except ValueError as e:
        return JSONResponse(status_code=402,content={"status":"error","message":str(e)})
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status":"error","message":"No se pudo restaurar el acceso."}
        )

@app.get("/api/v1/access/status")
async def access_status(request:Request):
    data=read_access_token(request.cookies.get(ACCESS_COOKIE,""))
    if not data:
        return {"status":"locked","payment_required":True}
    return {
        "status":"ok",
        "plan":data.get("plan"),
        "expires_at":data.get("exp"),
        "payment_required":False
    }

# ACCESO DEL ADMINISTRADOR
@app.post("/api/v1/admin/login")
async def admin_login(request:Request):
    try:
        body=await request.json()
    except Exception:
        body={}

    username=str(body.get("username",""))
    password=str(body.get("password",""))

    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return JSONResponse(
            status_code=503,
            content={"status":"error","message":"El acceso de administrador no está configurado en Render."}
        )

    if not hmac.compare_digest(username,ADMIN_USERNAME) or not hmac.compare_digest(password,ADMIN_PASSWORD):
        return JSONResponse(
            status_code=401,
            content={"status":"error","message":"Usuario o contraseña incorrectos."}
        )

    try:
        response=JSONResponse({
            "status":"ok",
            "plan":"admin",
            "duration_minutes":20,
            "message":"Acceso de administrador activado."
        })
        set_access_cookie(response,"admin","")
        return response
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status":"error","message":"No se pudo activar el acceso de administrador."}
        )

@app.post("/api/v1/admin/logout")
async def admin_logout():
    response=JSONResponse({"status":"ok","message":"Sesión cerrada."})
    clear_access_cookie(response)
    return response

# WEBHOOK DE STRIPE
@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    if not STRIPE_WEBHOOK_SECRET:
        return JSONResponse(
            status_code=503,
            content={"status":"error","message":"Falta STRIPE_WEBHOOK_SECRET en Render."}
        )

    raw=await request.body()
    signature=request.headers.get("stripe-signature","")
    parts={}
    for part in signature.split(","):
        if "=" in part:
            key,value=part.split("=",1)
            parts.setdefault(key,[]).append(value)

    try:
        timestamp=int((parts.get("t") or [""])[0])
        signatures=parts.get("v1") or []
        if abs(int(time.time())-timestamp)>300:
            raise ValueError("Firma vencida.")

        signed=str(timestamp).encode()+b"."+raw
        expected=hmac.new(
            STRIPE_WEBHOOK_SECRET.encode(),
            signed,
            hashlib.sha256
        ).hexdigest()

        if not any(hmac.compare_digest(expected,s) for s in signatures):
            raise ValueError("Firma no válida.")

        event=json.loads(raw.decode("utf-8"))
        event_type=event.get("type","")
        supported_events={
            "checkout.session.completed",
            "checkout.session.async_payment_succeeded",
            "checkout.session.expired",
            "invoice.paid",
            "invoice.payment_failed",
            "customer.subscription.updated",
            "customer.subscription.deleted"
        }
        if event_type not in supported_events:
            return {"received":True,"ignored":True}

        # La verificación del acceso consulta directamente el estado de Stripe.
        # Este webhook valida la firma y confirma que Stripe entregó el evento.
        return {"received":True,"event":event_type}

    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status":"error","message":"Firma de webhook no válida."}
        )

# RUTAS ORIGINALES DE LA APLICACIÓN
@app.post("/api/flight")
async def flight(data:FlightRequest):
    return call_engine("analyze_flight",data)

@app.post("/api/booking")
async def booking(data:BookingRequest):
    return call_engine("booking_simulation",data)

@app.post("/api/connection")
async def connection(data:ConnectionRequest):
    return call_engine("connection_analysis",data)

@app.post("/api/baggage")
async def baggage(data:BaggageRequest):
    return call_engine("baggage_rules",data)

@app.post("/api/item")
async def item(data:ItemRequest):
    return call_engine("item_analysis",data)

@app.post("/api/cuba")
async def cuba(data:CubaRequest):
    return call_engine("cuba_check",data)

@app.post("/api/cuba/entry")
async def cuba_entry(data:CubaEntryRequest):
    return call_engine("cuba_entry",data)

@app.post("/api/documents")
async def documents(data:DocumentRequest):
    return call_engine("document_analysis",data)

@app.post("/api/practice")
async def practice(data:PracticeRequest):
    return call_engine("practice_scenario",data)

@app.post("/api/dviajeros")
async def dviajeros(data:DViajeroRequest):
    return call_engine("dviajeros_simulation",data)

@app.post("/api/visa")
async def visa(data:VisaRequest):
    return call_engine("visa_simulation",data)

@app.get("/api/sources")
async def sources_get(topic:str="official",query:str="",country:str="",airline:str=""):
    return {
        "status":"ok",
        "topic":topic,
        "sources":get_sources(topic,query,country,airline)
    }

@app.post("/api/sources")
async def sources_post(data:SourceRequest):
    return {
        "status":"ok",
        "topic":data.topic,
        "sources":get_sources(data.topic,data.query,data.country,data.airline)
    }

@app.get("/api/official")
async def official(topic:str="",country:str="",airline:str=""):
    return {
        "status":"ok",
        "topic":topic,
        "sources":official_sources(topic,country,airline)
    }

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
async def cuba_official():
    return {"status":"ok","sources":official_sources("cuba")}

@app.get("/api/airlines-cuba")
async def airlines_cuba():
    return {"status":"ok","airlines":get_airlines(),"charters":get_charters()}

@app.post("/api/solve")
async def solve(data:SolveRequest):
    return call_engine("solve",data)

@app.post("/api/guide")
async def guide(data:GuideRequest):
    return call_engine("build_guide",data)

# GENERACIÓN DE PDF
STYLES=getSampleStyleSheet()
STYLE=STYLES["BodyText"]
TITLE=STYLES["Title"]
TITLE.alignment=TA_CENTER

def add_line(story,label,value):
    if value in ("",None,False,[],{}):
        return
    if isinstance(value,(dict,list)):
        value=json.dumps(value,ensure_ascii=False)
    safe_label=escape(str(label))
    safe_value=escape(str(value))
    story.extend([
        Paragraph(f"<b>{safe_label}:</b> {safe_value}",STYLE),
        Spacer(1,4)
    ])

def make_pdf(data,lang="es",title=None):
    b=io.BytesIO()
    doc=SimpleDocTemplate(
        b,
        pagesize=letter,
        rightMargin=.55*inch,
        leftMargin=.55*inch,
        topMargin=.55*inch,
        bottomMargin=.55*inch
    )
    heading=escape(str(title or APP_NAME))
    story=[
        Paragraph(heading,TITLE),
        Spacer(1,8),
        Paragraph(
            "Guía independiente de preparación. No es un documento oficial ni sustituye las instrucciones de las autoridades.",
            STYLE
        ),
        Spacer(1,10),
        Paragraph("D’VIAJEROS",STYLES["Heading2"])
    ]
    dv=[
        ("1. Entrar al sitio oficial","Abre D’Viajeros y comienza el formulario."),
        ("2. Datos del viajero","Completa los datos que solicita el formulario."),
        ("3. Pasaporte","Escribe los datos exactamente como aparecen en el documento."),
        ("4. Viaje","Completa la información solicitada sobre tu entrada y estancia."),
        ("5. Revisar","Comprueba los datos antes de terminar."),
        ("6. Resultado","Conserva el resultado y el QR que entregue el sistema.")
    ]
    for label,value in dv:
        add_line(story,label,value)

    story.extend([
        Spacer(1,7),
        Paragraph("VISA PARA CUBA",STYLES["Heading2"])
    ])
    visa=[
        ("Visa electrónica","Consulta el portal oficial, completa la solicitud, realiza el proceso indicado y conserva el resultado recibido."),
        ("Trámite consular","Si tu caso corresponde al consulado o embajada, consulta directamente los requisitos, costo, forma de pago y tiempo vigente."),
        ("Aeropuerto","Si tu caso permite obtenerla en el aeropuerto, consulta antes del viaje el proceso vigente, el lugar y el costo correspondiente.")
    ]
    for label,value in visa:
        add_line(story,label,value)

    story.extend([
        Spacer(1,7),
        Paragraph("ENLACES OFICIALES",STYLES["Heading2"])
    ])
    for source in official_sources("cuba"):
        if isinstance(source,dict):
            url=(
                source.get("exact_url")
                or source.get("deep_url")
                or source.get("section_url")
                or source.get("url")
            )
            if url:
                add_line(
                    story,
                    source.get("title") or source.get("name") or "Fuente oficial",
                    url
                )

    story.extend([
        Spacer(1,12),
        Paragraph(
            escape(f"Generado: {now()} — {APP_NAME} | May Roga LLC"),
            STYLE
        )
    ])
    doc.build(story)
    b.seek(0)
    return b

@app.post("/api/pdf")
async def pdf(data:PDFRequest):
    b=make_pdf(model_dict(data.data),data.lang,data.title)
    return StreamingResponse(
        b,
        media_type="application/pdf",
        headers={"Content-Disposition":"attachment; filename=mi-guia-que-quieres-llevar.pdf"}
    )

@app.post("/api/pdf/import")
async def pdf_import(data:PDFImportRequest):
    return {
        "status":"verify",
        "recovered":False,
        "data":{},
        "next_action":"Esta versión utiliza el PDF como guía de pasos. Revisa siempre el sitio oficial."
    }

@app.post("/api/export")
async def export_trip(data:TripExportRequest):
    return {
        "status":"ok",
        "data":model_dict(data.data),
        "next_action":"Puedes conservar esta información localmente."
    }

@app.post("/api/local-data")
async def local_data(data:DeleteLocalRequest):
    return {
        "status":"ok",
        "message":"La aplicación no necesita conservar tus datos personales en el servidor."
    }

@app.get("/api/legal")
async def legal():
    return {
        "status":"ok",
        "title":"Aviso legal",
        "message":"¿QUÉ QUIERES LLEVAR? es una herramienta independiente de orientación y preparación de May Roga LLC.",
        "points":[
            "No es una agencia de viajes.",
            "No es una aerolínea ni operador charter.",
            "No realiza trámites oficiales en nombre del viajero.",
            "No vende ni emite boletos.",
            "No sustituye a las autoridades ni a los proveedores oficiales.",
            "La información puede cambiar y debe comprobarse en la fuente oficial."
        ]
    }

@app.get("/api/ping")
async def ping():
    return {"status":"ok","version":VERSION,"time":now()}

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status":"error",
            "message":"Faltan o no son válidos algunos datos.",
            "next_action":"Revisa los datos e inténtalo nuevamente.",
            "details":exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_error(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status":"error",
            "message":"La operación no pudo completarse.",
            "next_action":"Inténtalo nuevamente."
        }
    )

__all__=["app"]
