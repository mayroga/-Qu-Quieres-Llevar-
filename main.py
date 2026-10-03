# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.0.0
from __future__ import annotations
import hmac,os,secrets,time
from pathlib import Path
from typing import Any,Dict,Optional
from urllib.parse import quote_plus
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse,HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict
from cuba_engine import engine as cuba_engine
from source_registry import SOURCES,AIRLINES,CHARTERS,get_sources,get_airlines,get_charters,get_official_sources,official_url
APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="12.0.0"
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","").strip()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","").strip()
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","").strip()
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY
app=FastAPI(title=APP_NAME,version=APP_VERSION,description="Preparación y orientación independiente para viajes.",docs_url="/docs",redoc_url="/redoc")
if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")
PAID_SESSIONS:Dict[str,Dict[str,Any]]={}
ADMIN_SESSIONS:Dict[str,float]={}
SESSION_TTL=24*60*60

class Body(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)

class LoginRequest(Body):
    username:str=""
    password:str=""

class CheckoutRequest(Body):
    price_type:str="1"

def lang(value:Any="es")->str:
    return "en" if str(value or "").lower().strip()=="en" else "es"

def text(value:Any)->str:
    return str(value or "").strip()

def clean(value:Any,max_len:int=1000)->str:
    return text(value)[:max_len]

def token(prefix:str="tok")->str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"

def access_ok(value:Any)->bool:
    t=text(value)
    if not t:return False
    row=PAID_SESSIONS.get(t)
    if row and row.get("expires",0)>time.time():return True
    if t in ADMIN_SESSIONS and ADMIN_SESSIONS[t]>time.time():return True
    return False

def require_access(request:Request)->str:
    auth=request.headers.get("authorization","")
    t=auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if not access_ok(t):raise HTTPException(401,"Acceso requerido.")
    return t

def source_dict(s:Any)->Dict[str,Any]:
    if hasattr(s,"__dict__"):return dict(s.__dict__)
    if hasattr(s,"model_dump"):return s.model_dump()
    if isinstance(s,dict):return dict(s)
    return {"name":text(s)}

def source_list(items:Any)->list:
    return [source_dict(x) for x in (items or [])]

def localized(es:str,en:str,language:str="es")->str:
    return en if lang(language)=="en" else es

def flight_steps(language:str="es")->list:
    return [
        localized("Confirma origen y destino.","Confirm origin and destination.",language),
        localized("Confirma la fecha del viaje.","Confirm the travel date.",language),
        localized("Revisa la aerolínea, aeropuerto y número de vuelo en tu reserva.","Review the airline, airport and flight number in your reservation.",language),
        localized("Comprueba si tienes escalas o conexiones.","Check whether you have stops or connections.",language),
        localized("Revisa la tarifa y las condiciones de equipaje.","Review the fare and baggage conditions.",language),
        localized("Confirma la información directamente con la fuente oficial.","Confirm the information directly with the official source.",language)
    ]

def guide_data(data:Dict[str,Any])->Dict[str,Any]:
    language=lang(data.get("language"))
    cuba=is_cuba_route(data.get("origin",""),data.get("destination",""))
    steps=flight_steps(language)
    if cuba:
        cuba_steps=[
            localized("Confirma los requisitos aplicables a tu nacionalidad.","Confirm the requirements applicable to your nationality.",language),
            localized("Revisa pasaporte y vigencia.","Review your passport and validity.",language),
            localized("Comprueba si corresponde visa o eVisa.","Check whether a visa or eVisa applies.",language),
            localized("Practica D’Viajeros antes de realizar el formulario real.","Practice D’Viajeros before completing the real form.",language),
            localized("Revisa las reglas oficiales de aduanas y equipaje.","Review the official customs and baggage rules.",language),
            localized("Confirma todo nuevamente antes de viajar.","Confirm everything again before traveling.",language)
        ]
    else:cuba_steps=[]
    return {
        "success":True,
        "next_action":localized("Sigue estos pasos en orden.","Follow these steps in order.",language),
        "steps":steps,
        "cuba_steps":cuba_steps,
        "official_sources":source_list(get_official_sources(language)),
        "charter_sources":source_list(get_charters(language))
    }

def is_cuba_route(origin:str="",destination:str="")->bool:
    s=f"{text(origin)} {text(destination)}".lower()
    return any(x in s for x in ("cuba","havana","habana","varadero","camaguey","camagüey","holguin","holguín","santiago de cuba","santa clara"))

def airline_matches(query:str="")->list:
    q=text(query).lower()
    if not q:return source_list(AIRLINES)
    return source_list([x for x in AIRLINES if q in text(getattr(x,"name","")).lower() or q in text(getattr(x,"publisher","")).lower() or q in text(getattr(x,"country","")).lower()])

def build_flight_response(data:Dict[str,Any])->Dict[str,Any]:
    language=lang(data.get("language"))
    origin=clean(data.get("origin"),100)
    destination=clean(data.get("destination"),100)
    airline=clean(data.get("airline"),100)
    departure=clean(data.get("departure_date"),30)
    return_date=clean(data.get("return_date"),30)
    stops=data.get("stops",0)
    passengers=data.get("passengers",1)
    cuba=is_cuba_route(origin,destination)
    q=f"{origin} {destination} {airline}"
    matches=airline_matches(airline)
    charter=source_list(get_charters(language)) if cuba else []
    understood=localized(
        "Aquí organizamos la información de tu viaje para que sepas qué revisar. Los datos de vuelo deben confirmarse en una fuente actual.",
        "Here we organize your trip information so you know what to check. Flight data must be confirmed with a current source.",
        language
    )
    return {
        "success":True,
        "origin":origin,
        "destination":destination,
        "departure_date":departure,
        "return_date":return_date,
        "airline":airline,
        "cabin":clean(data.get("cabin"),50),
        "fare":clean(data.get("fare"),100),
        "passengers":passengers,
        "stops":stops,
        "understood":understood,
        "steps":flight_steps(language),
        "airline_sources":matches,
        "charter_sources":charter,
        "google_flights_url":f"https://www.google.com/travel/flights?q={quote_plus((origin+' '+destination).strip())}" if origin and destination else "",
        "cuba_route":cuba
    }

def item_result(data:Dict[str,Any])->Dict[str,Any]:
    language=lang(data.get("language"))
    item=clean(data.get("item") or data.get("item_description"),160)
    description=clean(data.get("description"),1000)
    airline=clean(data.get("airline"),100)
    destination=clean(data.get("destination"),100)
    low=item.lower()
    category="REVISA ESTO ANTES DE VIAJAR"
    if any(x in low for x in ("explosivo","granada","arma de fuego","munición","municion")):
        category="NO PUEDES LLEVARLO"
    elif any(x in low for x in ("power bank","batería externa","bateria externa","litio","powerbank")):
        category="PUEDES LLEVARLO, PERO…"
    elif any(x in low for x in ("ropa","camiseta","pantalon","pantalón","zapato","zapatos")):
        category="PUEDES LLEVARLO"
    elif any(x in low for x in ("medicamento","medicina","medication")):
        category="REVISA ESTO ANTES DE VIAJAR"
    elif any(x in low for x in ("liquido","líquido","aerosol","perfume","shampoo","champú")):
        category="PUEDES LLEVARLO, PERO…"
    details=localized(
        f"El artículo identificado es “{item}”. La condición exacta puede depender de la aerolínea, ruta, tipo de equipaje y características del artículo. No inventamos una autorización universal.",
        f"The identified item is “{item}”. The exact condition may depend on the airline, route, baggage type and item characteristics. We do not invent a universal authorization.",
        language
    )
    links=[
        {"title":"TSA","url":"https://www.tsa.gov/travel/security-screening/whatcanibring/all"},
        {"title":"FAA","url":"https://www.faa.gov/hazmat/packsafe"},
        {"title":"IATA Travel Centre","url":"https://www.iatatravelcentre.com/"}
    ]
    if destination.lower().find("cuba")>=0:
        links.append({"title":"Aduana de Cuba","url":"https://www.aduana.gob.cu/"})
    return {
        "success":True,
        "status_category":category,
        "short_answer":localized("Revisa las condiciones antes de empacarlo.","Review the conditions before packing it.",language),
        "details":details,
        "item":item,
        "description":description,
        "quantity":data.get("quantity",1),
        "airline":airline,
        "destination":destination,
        "official_links":links,
        "source_reference":"Confirma la regla aplicable directamente con la fuente oficial."
    }

def teach_result(term:str,language:str="es")->Dict[str,Any]:
    t=clean(term,100)
    k=t.lower()
    definitions={
        "equipaje de mano":("La maleta pequeña que llevas contigo dentro del avión.","The small bag you take with you inside the aircraft."),
        "carry-on":("Equipaje que normalmente viaja contigo en la cabina, sujeto a las condiciones de la aerolínea.","Baggage that normally travels with you in the cabin, subject to the airline's conditions."),
        "equipaje documentado":("La maleta que entregas antes de pasar a la zona de embarque y que viaja en la bodega.","The bag you check before boarding and that travels in the aircraft hold."),
        "checked baggage":("Equipaje que entregas para que viaje en la bodega del avión.","Baggage you check to travel in the aircraft hold."),
        "escala":("Una parada del itinerario entre tu origen y destino. Puede implicar cambio de avión o no.","A stop between your origin and destination. It may or may not involve changing aircraft."),
        "conexión":("Cuando continúas el viaje utilizando otro vuelo después de una parada.","When you continue your trip on another flight after a stop."),
        "tarifa":("El tipo de boleto comprado y las condiciones que vienen asociadas a él.","The type of ticket purchased and its associated conditions.")
    }
    es,en=definitions.get(k,(f"“{t}” es un término que debes confirmar según el contexto de tu viaje.","“{t}” is a term you should confirm according to your travel context."))
    return {"success":True,"title":t,"explanation":en if language=="en" else es,"next_action":"Confirma el significado y la condición concreta en la fuente oficial aplicable." if language=="es" else "Confirm the meaning and specific condition with the applicable official source."}

def legal_data(language:str="es")->Dict[str,Any]:
    return {
        "success":True,
        "short_notice":localized("Servicio independiente de May Roga LLC.","Independent service provided by May Roga LLC.",language),
        "full_notice":localized("¿QUÉ QUIERES LLEVAR? no es una aerolínea, agencia de viajes, aeropuerto, gobierno, consulado ni autoridad. No vende ni reserva vuelos. Las simulaciones son educativas y no presentan formularios oficiales como enviados.","¿QUÉ QUIERES LLEVAR? is not an airline, travel agency, airport, government, consulate or authority. It does not sell or book flights. Simulations are educational and do not present official forms as submitted.",language),
        "user_guidance":localized("Las reglas, horarios, tarifas, requisitos y disponibilidad pueden cambiar. Confirma la información final directamente con la fuente oficial correspondiente.","Rules, schedules, fares, requirements and availability can change. Confirm final information directly with the applicable official source.",language),
        "source_notice":localized("Cuando una respuesta depende de una autoridad o proveedor, la aplicación muestra una fuente para que puedas verificarla.","When an answer depends on an authority or provider, the application provides a source so you can verify it.",language)
    }

@app.get("/",include_in_schema=False)
async def root():
    index=STATIC_DIR/"index.html"
    if not index.exists():raise HTTPException(404,"Application interface not found.")
    return FileResponse(str(index))

@app.get("/health")
async def health():
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":APP_VERSION,
        "stripe_configured":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "gemini_configured":bool(GEMINI_API_KEY),
        "airlines":len(AIRLINES),
        "charters":len(CHARTERS)
    }

@app.get("/ping",include_in_schema=False)
async def ping():return {"status":"ok"}

@app.get("/api/config")
async def config(language:str="es"):
    language=lang(language)
    return {
        "success":True,
        "app":{"name":APP_NAME,"version":APP_VERSION},
        "stripe":{"enabled":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),"publishable_key":STRIPE_PUBLISHABLE_KEY,"price":15.99,"currency":"USD"},
        "cuba":cuba_engine.public_config(language),
        "airlines":source_list(AIRLINES),
        "charters":source_list(CHARTERS)
    }

@app.get("/api/v1/config")
async def config_v1(language:str="es"):return await config(language)

@app.post("/api/v1/admin/login")
async def admin_login(payload:LoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:raise HTTPException(503,"Admin credentials are not configured.")
    if not hmac.compare_digest(payload.username,ADMIN_USERNAME) or not hmac.compare_digest(payload.password,ADMIN_PASSWORD):raise HTTPException(401,"Credenciales inválidas.")
    t=token("admin")
    ADMIN_SESSIONS[t]=time.time()+SESSION_TTL
    return {"status":"success","access":"granted","session_token":t,"role":"admin","expires_in":SESSION_TTL}

@app.post("/login-admin")
async def login_admin(payload:LoginRequest):return await admin_login(payload)

@app.get("/api/v1/sources/charter")
async def charter_sources(language:str="es"):
    return {"success":True,"sources":source_list(get_charters(lang(language)))}

@app.get("/api/v1/sources/official")
async def official_sources(language:str="es"):
    return {"success":True,"sources":source_list(get_official_sources(lang(language)))}

@app.post("/api/v1/flight/sources")
async def flight_sources(payload:Body):
    language=lang(payload.model_dump().get("language"))
    return {"success":True,"airline_sources":source_list(get_airlines(payload.model_dump().get("airline",""))),"charter_sources":source_list(get_charters(language))}

@app.get("/api/v1/airlines")
async def airlines(q:str=""):
    return {"success":True,"airlines":airline_matches(q)}

@app.get("/api/v1/airlines/{airline_id}")
async def airline(airline_id:str):
    matches=[source_dict(x) for x in AIRLINES if text(getattr(x,"id",""))==airline_id]
    if not matches:raise HTTPException(404,"Airline not found.")
    return {"success":True,"airline":matches[0]}

@app.post("/api/v1/flight/understand")
async def understand_flight(payload:Body):
    return build_flight_response(payload.model_dump())

@app.post("/api/v1/flight/search-external")
async def search_external(payload:Body):
    d=payload.model_dump()
    result=build_flight_response({"language":d.get("language","es"),"origin":d.get("natural_query",""),"destination":"","airline":""})
    q=clean(d.get("natural_query"),300)
    matches=airline_matches(q)
    if matches:result["airline_sources"]=matches
    return {
        "status":"success",
        "flights":[
            {"airline":x.get("name",""),"route":q,"status":"Fuente de referencia; confirma la ruta actual directamente.","booking_url":x.get("url","")}
            for x in result["airline_sources"]
        ],
        "charter_sources":result.get("charter_sources",[])
    }

@app.post("/api/v1/consultar-articulo")
async def consultar_articulo(payload:Body):
    return item_result(payload.model_dump())

@app.post("/api/v1/item/teach")
async def item_teach(payload:Body):
    d=payload.model_dump()
    return teach_result(d.get("term",""),lang(d.get("language")))

@app.post("/api/v1/cuba/visa")
async def cuba_visa(payload:Body):
    return cuba_engine.evaluate_visa(payload)

@app.post("/api/v1/cuba/dviajeros")
async def cuba_dviajeros(payload:Body):
    return cuba_engine.evaluate_dviajeros(payload)

@app.get("/api/v1/cuba/visa")
async def cuba_visa_info(language:str="es"):
    return cuba_engine.public_config(lang(language))["cuba"]|{"information":cuba_engine.get_visa_data()}

@app.get("/api/v1/cuba/dviajeros")
async def cuba_dviajeros_info(language:str="es"):
    return cuba_engine.public_config(lang(language))["cuba"]|{"information":cuba_engine.get_dviajeros_data()}

@app.get("/api/v1/cuba/official")
async def cuba_official(language:str="es"):
    return cuba_engine.official_information(lang(language))

@app.post("/api/v1/cuba/simulation")
async def cuba_simulation(payload:Body):
    d=payload.model_dump()
    return cuba_engine.simulation(d.get("mode","visa"),lang(d.get("language")))

@app.post("/api/v1/cuba/practice")
async def cuba_practice(payload:Body):
    d=payload.model_dump()
    return cuba_engine.simulation(d.get("mode","visa"),lang(d.get("language")))

@app.post("/api/v1/guide")
async def guide(payload:Body):
    return guide_data(payload.model_dump())

@app.get("/api/v1/legal")
async def legal(language:str="es"):return legal_data(lang(language))

@app.post("/api/v1/sources/search")
async def sources_search(payload:Body):
    d=payload.model_dump()
    q=clean(d.get("query"),200)
    language=lang(d.get("language"))
    return {"success":True,"sources":source_list(get_sources(q)),"airlines":airline_matches(q),"charters":source_list(get_charters(language))}

@app.get("/api/v1/stripe/public")
async def stripe_public():
    return {"enabled":bool(STRIPE_PUBLISHABLE_KEY and STRIPE_PRICE_ID1),"publishable_key":STRIPE_PUBLISHABLE_KEY,"price":15.99,"currency":"USD"}

@app.get("/api/v1/access/check")
async def access_check(request:Request):
    auth=request.headers.get("authorization","")
    t=auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    return {"status":"success","access":"granted" if access_ok(t) else "denied"}

@app.post("/api/v1/create-checkout-session")
async def create_checkout(payload:CheckoutRequest,request:Request):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1:raise HTTPException(503,"Stripe is not configured.")
    base=str(request.base_url).rstrip("/")
    try:
        checkout=stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],
            success_url=f"{base}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/?payment=cancelled",
            allow_promotion_codes=True
        )
        return {"success":True,"url":checkout.url,"session_id":checkout.id}
    except Exception:
        raise HTTPException(502,"Unable to create the payment session.")

@app.post("/api/create-checkout-session")
async def create_checkout_legacy(payload:CheckoutRequest,request:Request):return await create_checkout(payload,request)

@app.get("/api/v1/payment-success")
async def payment_success(session_id:str):
    if not stripe.api_key:raise HTTPException(503,"Stripe is not configured.")
    try:
        session=stripe.checkout.Session.retrieve(session_id)
        if getattr(session,"payment_status","")!="paid":raise HTTPException(402,"Payment has not been confirmed.")
        t=token("access")
        PAID_SESSIONS[t]={"created":time.time(),"expires":time.time()+SESSION_TTL,"stripe_session":session_id}
        return {"status":"success","access":"granted","token":t,"expires_in":SESSION_TTL}
    except HTTPException:raise
    except Exception:raise HTTPException(400,"Unable to verify payment.")

@app.get("/api/payment-success")
async def payment_success_legacy(session_id:str):return await payment_success(session_id)

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    payload=await request.body()
    signature=request.headers.get("stripe-signature","")
    if STRIPE_WEBHOOK_SECRET:
        try:event=stripe.Webhook.construct_event(payload,signature,STRIPE_WEBHOOK_SECRET)
        except Exception:raise HTTPException(400,"Invalid webhook signature.")
    else:
        try:event=__import__("json").loads(payload.decode("utf-8"))
        except Exception:return {"status":"ignored"}
    if event.get("type")=="checkout.session.completed":
        obj=event.get("data",{}).get("object",{})
        sid=obj.get("id")
        if sid:
            t=token("access")
            PAID_SESSIONS[t]={"created":time.time(),"expires":time.time()+SESSION_TTL,"stripe_session":sid}
    return {"status":"success"}

@app.get("/api/v1/pdf")
async def pdf_info(language:str="es"):
    return {
        "success":True,
        "available":False,
        "message":localized("La guía puede prepararse con los datos de la sesión; la generación de PDF se habilita cuando el módulo PDF está instalado.","The guide can be prepared from session data; PDF generation is enabled when the PDF module is installed.",language)
    }

@app.post("/api/v1/pdf")
async def pdf_prepare(payload:Body):
    d=payload.model_dump()
    return {"success":True,"format":"PDF","ready":True,"data":d,"message":localized("Resumen preparado para generar PDF.","Summary prepared for PDF generation.",d.get("language"))}

@app.get("/api/v1/health")
async def health_v1():return await health()

@app.exception_handler(HTTPException)
async def http_error(request:Request,exc:HTTPException):
    return JSONResponse(status_code=exc.status_code,content={"success":False,"detail":exc.detail})

@app.exception_handler(Exception)
async def general_error(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"success":False,"detail":"Error interno del servidor."})
