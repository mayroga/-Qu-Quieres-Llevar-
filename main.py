# main.py — QU-QUIERES-LLEVAR | May Roga LLC | v6.0.0
import os,re,secrets,time,datetime as dt
from typing import Optional,Any
from urllib.parse import quote_plus
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse,JSONResponse
from pydantic import BaseModel,Field
from legal_disclaimer import LegalNoticeManager

APP=LegalNoticeManager
VERSION="6.0.0"
SESSION_MINUTES=APP.SESSION_MINUTES
ACTIVE_PAID_SESSIONS={}
ADMIN_SESSIONS={}
MAX_TEXT=1200

app=FastAPI(
    title="¿QUÉ QUIERES LLEVAR?",
    description="Preparación sencilla de vuelos, equipaje y viaje — May Roga LLC",
    version=VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["*"]
)

STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
STRIPE_PRICE_ID=os.getenv("STRIPE_PRICE_ID","").strip() or os.getenv("STRIPE_PRICE_ID1","").strip()
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","").strip()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

class FlightSearchRequest(BaseModel):
    natural_query:str=Field(...,min_length=2,max_length=MAX_TEXT)
    session_token:Optional[str]=None

class ItemCheckRequest(BaseModel):
    session_token:Optional[str]=None
    item_description:str=Field(...,min_length=2,max_length=MAX_TEXT)
    airline:Optional[str]=Field(default=None,max_length=120)
    baggage_place:Optional[str]=Field(default=None,max_length=80)

class AdminLoginRequest(BaseModel):
    username:str=Field(...,min_length=1,max_length=120)
    password:str=Field(...,min_length=1,max_length=200)

class OfficialGuideRequest(BaseModel):
    topic:str=Field(...,min_length=2,max_length=120)
    official_url:str=Field(...,min_length=8,max_length=1000)

class PaymentVerifyRequest(BaseModel):
    checkout_session_id:str=Field(...,min_length=5,max_length=300)

def now():
    return time.time()

def token(prefix="tkn"):
    return f"{prefix}_{secrets.token_urlsafe(32)}"

def clean_text(value:str)->str:
    return re.sub(r"\s+"," ",str(value or "")).strip()

def active_session(tkn:Optional[str],admin=False)->bool:
    if not tkn:
        return False
    store=ADMIN_SESSIONS if admin else ACTIVE_PAID_SESSIONS
    exp=store.get(tkn)
    if not exp:
        return False
    if exp<=now():
        store.pop(tkn,None)
        return False
    return True

def require_service(tkn:Optional[str]):
    if active_session(tkn,admin=True):
        return
    if not active_session(tkn):
        raise HTTPException(status_code=403,detail="Sesión de servicio requerida.")

def official_link(url:str,label:str):
    return {"label":label,"url":url}

def google_flights_url(query:str):
    return "https://www.google.com/travel/flights?q="+quote_plus(query)

def airline_search_hint(query:str):
    q=clean_text(query)
    return {
        "title":"Encuentra tu vuelo",
        "message":"Puedes usar Google Flights para localizar opciones y después confirmar los detalles directamente con la aerolínea.",
        "steps":[
            "Escribe origen y destino.",
            "Selecciona la fecha.",
            "Revisa si dice directo o si tiene una escala.",
            "Mira el nombre de la aerolínea.",
            "Abre la información del vuelo.",
            "Después confirma equipaje, tarifa y condiciones en el sitio oficial de la aerolínea."
        ],
        "official_links":[official_link(google_flights_url(q),"Buscar vuelos en Google Flights")]
    }

def baggage_explanation(item:str,airline:Optional[str]=None):
    q=clean_text(item).lower()
    a=clean_text(airline)
    explanations=[]

    if any(x in q for x in ["equipaje de mano","carry-on","carry on","cabina","maleta de cabina"]):
        explanations.append({
            "term":"EQUIPAJE DE MANO",
            "simple":"Es la maleta que normalmente llevas contigo dentro del avión.",
            "next":"Revisa el peso, las medidas y la cantidad permitida por tu aerolínea y tarifa."
        })

    if any(x in q for x in ["documentado","facturado","checked baggage","checked bag","maleta registrada"]):
        explanations.append({
            "term":"EQUIPAJE DOCUMENTADO",
            "simple":"Es la maleta que entregas a la aerolínea antes de subir al avión y que viaja en la bodega.",
            "next":"Revisa cuántas piezas permite tu tarifa, el peso, las medidas y si existe un costo."
        })

    if any(x in q for x in ["artículo personal","articulo personal","personal item","mochila pequeña"]):
        explanations.append({
            "term":"ARTÍCULO PERSONAL",
            "simple":"Es el bolso o mochila pequeña que la aerolínea permite llevar contigo y colocar en el espacio indicado.",
            "next":"Revisa las medidas exactas de tu aerolínea y tarifa."
        })

    if any(x in q for x in ["escala","conexión","conexion","stop","estancia"]):
        explanations.append({
            "term":"ESCALA O CONEXIÓN",
            "simple":"Tu viaje tiene una parada antes de llegar al destino final.",
            "next":"Revisa si debes cambiar de avión, cuánto dura la conexión y qué debes hacer con el equipaje."
        })

    if any(x in q for x in ["bateria","batería","power bank","litio","lithium"]):
        explanations.append({
            "term":"BATERÍA",
            "simple":"Las baterías pueden tener reglas especiales según su tipo, capacidad y dónde viajan.",
            "next":"Busca la regla específica de tu aerolínea y del tipo de batería antes de viajar."
        })

    if any(x in q for x in ["liquido","líquido","liquids","aerosol","spray"]):
        explanations.append({
            "term":"LÍQUIDOS Y AEROSOLES",
            "simple":"Los líquidos y aerosoles pueden tener límites y condiciones diferentes según dónde los lleves.",
            "next":"Revisa la regla oficial del aeropuerto, autoridad y aerolínea que corresponda a tu viaje."
        })

    if any(x in q for x in ["medicina","medicamento","medicamentos","medicine"]):
        explanations.append({
            "term":"MEDICAMENTOS",
            "simple":"Los medicamentos pueden necesitar condiciones especiales durante el viaje.",
            "next":"Revisa las reglas de la aerolínea y las autoridades del origen, tránsito y destino."
        })

    if not explanations:
        explanations.append({
            "term":"REVISEMOS TU ARTÍCULO",
            "simple":f"Quieres llevar: {clean_text(item)}.",
            "next":"Primero necesitamos saber qué artículo es, dónde quieres llevarlo y qué aerolínea opera tu vuelo."
        })

    return {
        "airline":a or None,
        "items":explanations,
        "rule_authority":"No se inventan reglas. La condición exacta debe confirmarse con la fuente oficial aplicable.",
        "next_action":{
            "title":"Confirma la regla oficial",
            "message":"Te enseñamos qué buscar y después puedes continuar directamente en el sitio oficial."
        }
    }

def teaching_path(topic:str,url:str):
    t=clean_text(topic)
    return {
        "title":"Te enseñamos primero",
        "topic":t,
        "steps":[
            f"Busca en el sitio oficial la palabra: {t}.",
            "Abre la sección que hable específicamente de tu viaje.",
            "Busca peso, medidas, cantidad y condiciones.",
            "Comprueba si la regla corresponde a tu aerolínea, tarifa, ruta y tipo de artículo.",
            "Si encuentras una palabra que no entiendes, tráela aquí y te explicamos qué significa."
        ],
        "official_url":url,
        "notice":"La información final debe confirmarse en la fuente oficial."
    }

@app.get("/",response_class=HTMLResponse)
def root():
    return HTMLResponse(f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>¿Qué Quieres Llevar? — May Roga LLC</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f4f7fa;color:#183044;font-family:Arial,sans-serif}}
main{{max-width:720px;margin:0 auto;padding:18px}}
.card{{background:#fff;border-radius:18px;padding:22px;margin:12px 0;box-shadow:0 5px 22px rgba(0,0,0,.07)}}
h1{{text-align:center;font-size:28px;margin:5px 0;color:#123d59}}
h2{{font-size:20px;margin:5px 0 12px}}
p{{line-height:1.5}}
.small{{font-size:13px;color:#607080}}
button,a.btn{{display:block;width:100%;border:0;border-radius:12px;padding:14px;margin-top:10px;background:#123d59;color:#fff;font-weight:700;text-align:center;text-decoration:none;cursor:pointer}}
.secondary{{background:#e9eff4!important;color:#183044!important}}
textarea,input{{width:100%;padding:14px;border:1px solid #cbd5df;border-radius:12px;font-size:16px;margin-top:8px}}
.result{{white-space:pre-line;background:#f7fafc;border-radius:12px;padding:15px;margin-top:12px}}
.term{{font-weight:800;color:#123d59}}
.warn{{background:#fff8e6;padding:12px;border-radius:10px}}
</style>
</head>
<body>
<main>
<div class="card">
<h1>¿QUÉ QUIERES LLEVAR?</h1>
<p style="text-align:center">May Roga LLC</p>
<p>Te ayudamos a entender tu viaje y preparar tu equipaje sin palabras complicadas.</p>
<p class="small">{APP.short_notice()}</p>
</div>
<div class="card">
<h2>✈️ Primero: entiende tu vuelo</h2>
<p>Escribe lo que sabes de tu viaje. No necesitas saber palabras técnicas.</p>
<textarea id="flight" placeholder="Ejemplo: Miami a La Habana, 20 de diciembre, American Airlines"></textarea>
<button onclick="flightInfo()">ENSEÑARME MI VUELO</button>
<div id="flightResult"></div>
</div>
<div class="card">
<h2>🧳 Ahora: ¿qué quieres llevar?</h2>
<p>Escribe una cosa. Nosotros te explicamos qué significa y qué debes revisar.</p>
<input id="item" placeholder="Ejemplo: mochila, maleta, medicina, batería...">
<input id="airline" placeholder="Aerolínea, si la sabes">
<button onclick="checkItem()">REVISAR MI ARTÍCULO</button>
<div id="itemResult"></div>
</div>
<div class="card">
<h2>🔎 ¿Te falta información?</h2>
<p>No te dejamos solo. Te enseñamos qué buscar y después te llevamos al sitio oficial.</p>
<a class="btn secondary" href="https://www.google.com/travel/flights" target="_blank">BUSCAR VUELOS</a>
</div>
<div class="card small">
<strong>May Roga LLC</strong><br>{APP.INDEPENDENCE}<br><br>
{APP.FINAL_AUTHORITY}
</div>
</main>
<script>
const out=(id,obj)=>document.getElementById(id).innerHTML='<div class="result">'+JSON.stringify(obj,null,2).replace(/[<>]/g,'')+'</div>';
async function flightInfo(){{
 const q=document.getElementById('flight').value.trim();
 if(!q)return;
 const r=await fetch('/api/v1/flight/understand',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{natural_query:q}})}});
 const d=await r.json();
 out('flightResult',d);
}}
async function checkItem(){{
 const item=document.getElementById('item').value.trim();
 const airline=document.getElementById('airline').value.trim();
 if(!item)return;
 const r=await fetch('/api/v1/item/teach',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{item_description:item,airline:airline||null}})}});
 const d=await r.json();
 out('itemResult',d);
}}
</script>
</body>
</html>""")

@app.get("/health")
def health():
    return {
        "status":"ok",
        "app":"Qu-Quieres-Llevar",
        "version":VERSION,
        "owner":APP.OWNER,
        "stripe_configured":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID),
        "admin_configured":bool(ADMIN_USERNAME and ADMIN_PASSWORD)
    }

@app.get("/api/v1/meta")
def meta():
    return APP.metadata()

@app.post("/api/v1/admin/login")
def admin_login(payload:AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=503,detail="Acceso administrativo no configurado en Render.")
    if not secrets.compare_digest(payload.username,ADMIN_USERNAME) or not secrets.compare_digest(payload.password,ADMIN_PASSWORD):
        raise HTTPException(status_code=401,detail="Credenciales inválidas.")
    t=token("admin")
    ADMIN_SESSIONS[t]=now()+86400
    return {"status":"success","session_token":t,"expires_in":86400}

@app.post("/api/v1/create-checkout-session")
def create_checkout():
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        raise HTTPException(status_code=503,detail="El servicio de pago todavía no está configurado.")
    try:
        session=stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price":STRIPE_PRICE_ID,"quantity":1}],
            success_url="{CHECKOUT_SESSION_ID}",
            cancel_url="/"
        )
        return {"status":"success","checkout_url":session.url}
    except Exception as e:
        raise HTTPException(status_code=502,detail="No fue posible crear el pago.")

@app.post("/api/v1/payment/verify")
def verify_payment(payload:PaymentVerifyRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503,detail="Stripe no está configurado.")
    try:
        session=stripe.checkout.Session.retrieve(payload.checkout_session_id)
        if session.payment_status!="paid":
            raise HTTPException(status_code=402,detail="El pago todavía no está confirmado.")
        if STRIPE_PRICE_ID:
            line_items=stripe.checkout.Session.list_line_items(payload.checkout_session_id,limit=10)
            valid=any(getattr(getattr(x,"price",None),"id",None)==STRIPE_PRICE_ID for x in line_items.data)
            if not valid:
                raise HTTPException(status_code=403,detail="El pago no corresponde a este servicio.")
        t=token()
        ACTIVE_PAID_SESSIONS[t]=now()+SESSION_MINUTES*60
        return {"status":"success","session_token":t,"expires_in":SESSION_MINUTES*60}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400,detail="No fue posible confirmar el pago.")

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503,detail="Webhook de Stripe no configurado.")
    payload=await request.body()
    signature=request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400,detail="Firma de Stripe ausente.")
    try:
        event=stripe.Webhook.construct_event(payload,signature,STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400,detail="Firma de Stripe inválida.")
    if event["type"]=="checkout.session.completed":
        obj=event["data"]["object"]
        if obj.get("payment_status")=="paid":
            pass
    return {"status":"received"}

@app.post("/api/v1/flight/understand")
def understand_flight(payload:FlightSearchRequest):
    q=clean_text(payload.natural_query)
    if not q:
        raise HTTPException(status_code=400,detail="Escribe los datos que conozcas de tu viaje.")
    return {
        "status":"success",
        "message":"Vamos a entender tu viaje antes de tomar decisiones.",
        "what_we_can_do":[
            "Identificar lo que sabes del origen y destino.",
            "Ayudarte a distinguir vuelo directo, escala y conexión.",
            "Enseñarte qué revisar en la tarifa.",
            "Enseñarte dónde revisar el equipaje.",
            "Llevarte a la fuente oficial cuando necesites confirmar un dato."
        ],
        "search":airline_search_hint(q),
        "important":"Los datos concretos del vuelo deben confirmarse en la fuente correspondiente. No mostramos vuelos inventados."
    }

@app.post("/api/v1/flight/search-external")
def flight_search_external(payload:FlightSearchRequest):
    q=clean_text(payload.natural_query)
    if not q:
        raise HTTPException(status_code=400,detail="Escribe una ruta o vuelo.")
    return {
        "status":"success",
        "results":[],
        "message":"Para encontrar vuelos reales, utiliza el buscador y después confirma el vuelo en la aerolínea.",
        "official_search":google_flights_url(q),
        "next_step":[
            "Encuentra el vuelo.",
            "Anota la aerolínea y número de vuelo.",
            "Revisa si es directo o tiene escala.",
            "Abre los detalles del vuelo.",
            "Después revisa la política oficial de equipaje."
        ],
        "no_booking":True
    }

@app.post("/api/v1/item/teach")
def teach_item(payload:ItemCheckRequest):
    item=clean_text(payload.item_description)
    if not item:
        raise HTTPException(status_code=400,detail="Escribe qué quieres llevar.")
    return {
        "status":"success",
        "result":baggage_explanation(item,payload.airline),
        "official_action":{
            "title":"¿No encontramos una regla confirmada?",
            "message":"Busca la regla oficial de tu aerolínea. Si necesitas ayuda, la aplicación te enseña qué palabra buscar y qué significa."
        }
    }

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload:ItemCheckRequest):
    return teach_item(payload)

@app.post("/api/v1/guide")
def official_guide(payload:OfficialGuideRequest):
    return {
        "status":"success",
        "guide":teaching_path(payload.topic,payload.official_url)
    }

@app.get("/api/v1/session/{session_token}")
def session_status(session_token:str):
    if active_session(session_token,admin=True):
        return {"active":True,"type":"admin","expires_in":max(0,int(ADMIN_SESSIONS[session_token]-now()))}
    if active_session(session_token):
        return {"active":True,"type":"paid","expires_in":max(0,int(ACTIVE_PAID_SESSIONS[session_token]-now()))}
    return {"active":False}

@app.delete("/api/v1/session/{session_token}")
def delete_session(session_token:str):
    ACTIVE_PAID_SESSIONS.pop(session_token,None)
    ADMIN_SESSIONS.pop(session_token,None)
    return {"status":"deleted"}

@app.get("/api/v1/legal")
def legal():
    return {
        "version":APP.VERSION,
        "notice":APP.full_notice(),
        "intro":APP.intro(),
        "independence":APP.INDEPENDENCE,
        "purpose":APP.PURPOSE,
        "payment":APP.PAYMENT
    }

@app.get("/api/v1/official")
def official_sources():
    return {
        "google_flights":official_link("https://www.google.com/travel/flights","Google Flights"),
        "note":"La aplicación puede enseñar al usuario cómo encontrar información; la confirmación final debe hacerse en la fuente oficial correspondiente."
    }

@app.on_event("startup")
async def startup():
    async def cleanup():
        while True:
            current=now()
            for store in (ACTIVE_PAID_SESSIONS,ADMIN_SESSIONS):
                for k,v in list(store.items()):
                    if v<=current:
                        store.pop(k,None)
            import asyncio
            await asyncio.sleep(300)
    import asyncio
    asyncio.create_task(cleanup())

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=int(os.getenv("PORT","8000")))
