# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
import hmac,json,os,secrets,time
from pathlib import Path
from typing import Any,Dict
from urllib.parse import quote_plus
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict
from cuba_engine import engine as cuba_engine,is_cuba_route
from source_registry import SOURCES,AIRLINES,CHARTERS,get_sources,get_airlines,get_charters,get_official_sources,official_url

APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="12.1.0"
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

app=FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Preparación y orientación independiente para viajes, vuelos, aerolíneas, equipaje y procesos oficiales.",
    docs_url="/docs",
    redoc_url="/redoc"
)

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
    return "en" if str(value or "").strip().lower()=="en" else "es"

def text(value:Any)->str:
    return str(value or "").strip()

def clean(value:Any,max_len:int=1000)->str:
    return text(value)[:max_len]

def token(prefix:str="tok")->str:
    return f"{prefix}_{secrets.token_urlsafe(24)}"

def localized(es:str,en:str,language:str="es")->str:
    return en if lang(language)=="en" else es

def source_dict(value:Any)->Dict[str,Any]:
    if hasattr(value,"model_dump"):
        try:return value.model_dump()
        except Exception:pass
    if hasattr(value,"__dict__"):
        return dict(value.__dict__)
    if isinstance(value,dict):
        return dict(value)
    return {"name":text(value)}

def source_list(items:Any)->list:
    return [source_dict(x) for x in (items or [])]

def access_ok(value:Any)->bool:
    t=text(value)
    if not t:return False
    row=PAID_SESSIONS.get(t)
    if row and float(row.get("expires",0))>time.time():
        return True
    if t in ADMIN_SESSIONS and ADMIN_SESSIONS[t]>time.time():
        return True
    PAID_SESSIONS.pop(t,None)
    ADMIN_SESSIONS.pop(t,None)
    return False

def require_access(request:Request)->str:
    auth=request.headers.get("authorization","")
    t=auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if not access_ok(t):
        raise HTTPException(401,"Acceso requerido.")
    return t

def flight_steps(language:str="es")->list:
    return [
        localized("Confirma origen y destino.","Confirm origin and destination.",language),
        localized("Confirma la fecha del viaje.","Confirm the travel date.",language),
        localized("Revisa la aerolínea, aeropuerto y número de vuelo en tu reserva.","Review the airline, airport and flight number in your reservation.",language),
        localized("Comprueba si tienes escalas o conexiones.","Check whether you have stops or connections.",language),
        localized("Revisa la tarifa y las condiciones de equipaje.","Review the fare and baggage conditions.",language),
        localized("Confirma la información directamente con la fuente oficial.","Confirm the information directly with the official source.",language)
    ]

def airline_matches(query:str="",language:str="es")->list:
    q=text(query).lower()
    items=get_airlines(q) if q else AIRLINES
    return source_list(items)

def guide_data(data:Dict[str,Any])->Dict[str,Any]:
    language=lang(data.get("language"))
    origin=clean(data.get("origin"),100)
    destination=clean(data.get("destination"),100)
    cuba=is_cuba_route(origin,destination)
    steps=flight_steps(language)
    cuba_steps=[]
    if cuba:
        cuba_steps=[
            localized("Confirma los requisitos aplicables a tu nacionalidad.","Confirm the requirements applicable to your nationality.",language),
            localized("Revisa el pasaporte y su vigencia.","Review your passport and its validity.",language),
            localized("Comprueba si corresponde visa o eVisa.","Check whether a visa or eVisa applies.",language),
            localized("Practica D’Viajeros antes de realizar el formulario real.","Practice D’Viajeros before completing the real form.",language),
            localized("Revisa las reglas oficiales de Aduana y equipaje.","Review the official Customs and baggage rules.",language),
            localized("Confirma todo nuevamente antes de viajar.","Confirm everything again before traveling.",language)
        ]
    return {
        "success":True,
        "next_action":localized("Sigue estos pasos en orden.","Follow these steps in order.",language),
        "steps":steps,
        "cuba_route":cuba,
        "cuba_steps":cuba_steps,
        "official_sources":source_list(get_official_sources(language)),
        "charter_sources":source_list(get_charters(language))
    }

def build_flight_response(data:Dict[str,Any])->Dict[str,Any]:
    language=lang(data.get("language"))
    origin=clean(data.get("origin"),100)
    destination=clean(data.get("destination"),100)
    airline=clean(data.get("airline"),100)
    departure=clean(data.get("departure_date") or data.get("departure"),40)
    return_date=clean(data.get("return_date") or data.get("return"),40)
    cabin=clean(data.get("cabin"),50)
    fare=clean(data.get("fare"),100)
    flight_number=clean(data.get("flight_number"),50)
    stops=data.get("stops",0)
    passengers=data.get("passengers",1)
    cuba=is_cuba_route(origin,destination)
    matches=airline_matches(airline,language) if airline else source_list(AIRLINES)
    charter=source_list(get_charters(language)) if cuba else []
    return {
        "success":True,
        "origin":origin,
        "destination":destination,
        "departure_date":departure,
        "return_date":return_date,
        "airline":airline,
        "flight_number":flight_number,
        "cabin":cabin,
        "fare":fare,
        "passengers":passengers,
        "stops":stops,
        "cuba_route":cuba,
        "understood":localized(
            "Aquí organizamos la información de tu viaje para que sepas qué revisar. Los datos actuales del vuelo deben confirmarse directamente con la aerolínea o fuente correspondiente.",
            "Here we organize your trip information so you know what to check. Current flight information must be confirmed directly with the airline or applicable source.",
            language
        ),
        "steps":flight_steps(language),
        "airline_sources":matches,
        "charter_sources":charter,
        "google_flights_url":f"https://www.google.com/travel/flights?q={quote_plus((origin+' '+destination).strip())}" if origin and destination else ""
    }

def item_result(data:Dict[str,Any])->Dict[str,Any]:
    language=lang(data.get("language"))
    item=clean(data.get("item") or data.get("item_name") or data.get("item_description"),160)
    description=clean(data.get("description"),1000)
    airline=clean(data.get("airline"),100)
    destination=clean(data.get("destination"),100)
    quantity=data.get("quantity",1)
    low=item.lower()

    status="verify"
    category="REVISA ESTO ANTES DE VIAJAR"
    if any(x in low for x in ("arma de fuego","munición","municion","explosivo","granada")):
        status="restricted"
        category="NO PUEDES ASUMIR QUE PUEDES LLEVARLO"
    elif any(x in low for x in ("power bank","powerbank","batería externa","bateria externa")):
        status="verify"
        category="PUEDE TENER CONDICIONES ESPECIALES"
    elif any(x in low for x in ("ropa","camiseta","pantalon","pantalón","zapato","zapatos")):
        status="general"
        category="NORMALMENTE ES UN ARTÍCULO PERSONAL"
    elif any(x in low for x in ("medicamento","medicina","medication")):
        status="verify"
        category="REVISA ESTO ANTES DE VIAJAR"
    elif any(x in low for x in ("liquido","líquido","aerosol","perfume","shampoo","champú")):
        status="verify"
        category="PUEDE TENER CONDICIONES ESPECIALES"

    links=[
        {"title":"TSA","url":"https://www.tsa.gov/travel/security-screening/whatcanibring/all"},
        {"title":"FAA","url":"https://www.faa.gov/hazmat/packsafe"},
        {"title":"IATA Travel Centre","url":"https://www.iatatravelcentre.com/"}
    ]

    if is_cuba_route("",destination):
        links.append({"title":"Aduana de Cuba","url":"https://www.aduana.gob.cu/"})

    return {
        "success":True,
        "status":status,
        "status_category":category,
        "short_answer":localized(
            "Revisa las condiciones antes de empacarlo.",
            "Review the conditions before packing it.",
            language
        ),
        "details":localized(
            f"El artículo identificado es “{item}”. La condición exacta puede depender de la aerolínea, ruta, tipo de equipaje y características del artículo. No se presenta una autorización universal.",
            f"The identified item is “{item}”. The exact condition may depend on the airline, route, baggage type and item characteristics. No universal authorization is presented.",
            language
        ),
        "item":item,
        "description":description,
        "quantity":quantity,
        "airline":airline,
        "destination":destination,
        "official_links":links,
        "source_reference":localized(
            "Confirma la regla aplicable directamente con la fuente oficial correspondiente.",
            "Confirm the applicable rule directly with the corresponding official source.",
            language
        )
    }

def teach_result(term:str,language:str="es")->Dict[str,Any]:
    t=clean(term,100)
    k=t.lower()
    definitions={
        "equipaje de mano":(
            "La maleta pequeña que llevas contigo dentro del avión.",
            "The small bag you take with you inside the aircraft."
        ),
        "carry-on":(
            "Equipaje que normalmente viaja contigo en la cabina, sujeto a las condiciones de la aerolínea.",
            "Baggage that normally travels with you in the cabin, subject to the airline's conditions."
        ),
        "equipaje documentado":(
            "La maleta que entregas antes de pasar a la zona de embarque y que viaja en la bodega.",
            "The bag you check before boarding and that travels in the aircraft hold."
        ),
        "checked baggage":(
            "Equipaje que entregas para que viaje en la bodega del avión.",
            "Baggage you check to travel in the aircraft hold."
        ),
        "escala":(
            "Una parada del itinerario entre tu origen y destino. Puede implicar cambio de avión o no.",
            "A stop between your origin and destination. It may or may not involve changing aircraft."
        ),
        "conexión":(
            "Cuando continúas el viaje utilizando otro vuelo después de una parada.",
            "When you continue your trip on another flight after a stop."
        ),
        "tarifa":(
            "El tipo de boleto comprado y las condiciones que vienen asociadas a él.",
            "The type of ticket purchased and its associated conditions."
        )
    }
    es,en=definitions.get(
        k,
        (
            f"“{t}” es un término cuyo significado debes entender según el contexto de tu viaje.",
            f"“{t}” is a term whose meaning should be understood according to your travel context."
        )
    )
    return {
        "success":True,
        "title":t,
        "explanation":en if language=="en" else es,
        "next_action":localized(
            "Confirma el significado y la condición concreta en la fuente oficial aplicable.",
            "Confirm the meaning and specific condition with the applicable official source.",
            language
        )
    }

def legal_data(language:str="es")->Dict[str,Any]:
    return {
        "success":True,
        "short_notice":localized(
            "Servicio independiente de May Roga LLC.",
            "Independent service provided by May Roga LLC.",
            language
        ),
        "full_notice":localized(
            "¿QUÉ QUIERES LLEVAR? no es una aerolínea, agencia de viajes, aeropuerto, gobierno, consulado ni autoridad. No vende ni reserva vuelos. Las simulaciones son de práctica y no presentan formularios oficiales como enviados.",
            "¿QUÉ QUIERES LLEVAR? is not an airline, travel agency, airport, government, consulate or authority. It does not sell or book flights. Simulations are for practice and do not present official forms as submitted.",
            language
        ),
        "user_guidance":localized(
            "Las reglas, horarios, tarifas, requisitos y disponibilidad pueden cambiar. Confirma la información final directamente con la fuente oficial correspondiente.",
            "Rules, schedules, fares, requirements and availability can change. Confirm final information directly with the applicable official source.",
            language
        ),
        "source_notice":localized(
            "Cuando una respuesta depende de una autoridad o proveedor, la aplicación muestra una fuente para que puedas verificarla.",
            "When an answer depends on an authority or provider, the application provides a source so you can verify it.",
            language
        )
    }

def practice_data(data:Dict[str,Any])->Dict[str,Any]:
    language=lang(data.get("language"))
    airline=clean(data.get("airline"),100)
    origin=clean(data.get("origin"),100)
    destination=clean(data.get("destination"),100)
    date=clean(data.get("date") or data.get("departure_date"),40)
    passengers=data.get("passengers",1)
    cabin=clean(data.get("cabin"),40)
    cuba=is_cuba_route(origin,destination)

    steps=[
        {"step":1,"title":localized("Buscar vuelo","Search for a flight",language),"instruction":localized("Introduce origen, destino y fecha.","Enter origin, destination and date.",language)},
        {"step":2,"title":localized("Elegir vuelo","Choose a flight",language),"instruction":localized("Compara las opciones que aparezcan en el proceso real de la aerolínea.","Review the options that appear in the airline's real process.",language)},
        {"step":3,"title":localized("Revisar pasajeros","Review passengers",language),"instruction":localized("Practica cómo se solicitan los datos del pasajero. No introduzcas contraseñas, códigos de seguridad ni datos innecesarios.","Practice how passenger information is requested. Do not enter passwords, security codes or unnecessary data.",language)},
        {"step":4,"title":localized("Revisar tarifa","Review fare",language),"instruction":localized("Identifica qué tarifa y condiciones aparecen.","Identify the fare and conditions shown.",language)},
        {"step":5,"title":localized("Revisar equipaje","Review baggage",language),"instruction":localized("Comprueba qué equipaje corresponde a esa tarifa en la fuente oficial.","Check what baggage applies to that fare on the official source.",language)},
        {"step":6,"title":localized("Revisar antes de comprar","Review before purchase",language),"instruction":localized("En la práctica no se realiza ninguna compra.","No purchase is made in this practice.",language)}
    ]

    if cuba:
        steps.append({
            "step":7,
            "title":localized("Preparación para Cuba","Cuba preparation",language),
            "instruction":localized("Después de practicar el vuelo, revisa documentos, visa/eVisa, D’Viajeros, aduana y equipaje con las fuentes correspondientes.","After practicing the flight, review documents, visa/eVisa, D’Viajeros, customs and baggage with the applicable sources.",language)
        })

    return {
        "success":True,
        "mode":"airline_practice",
        "simulation":True,
        "official_submission":False,
        "payment":False,
        "notice":localized(
            "SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL.",
            "PRACTICE SIMULATION — NOT THE OFFICIAL SITE.",
            language
        ),
        "airline":airline,
        "origin":origin,
        "destination":destination,
        "date":date,
        "passengers":passengers,
        "cabin":cabin,
        "cuba_route":cuba,
        "steps":steps,
        "official_source":next((source_dict(x) for x in AIRLINES if text(getattr(x,"name","")).lower()==airline.lower()),None),
        "charter_sources":source_list(get_charters(language)) if cuba else []
    }

@app.get("/",include_in_schema=False)
async def root():
    index=STATIC_DIR/"index.html"
    if not index.exists():
        raise HTTPException(404,"Application interface not found.")
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
async def ping():
    return {"status":"ok","version":APP_VERSION}

@app.get("/api/config")
async def config(language:str="es"):
    language=lang(language)
    return {
        "success":True,
        "app":{"name":APP_NAME,"version":APP_VERSION},
        "stripe":{
            "enabled":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
            "publishable_key":STRIPE_PUBLISHABLE_KEY,
            "price":15.99,
            "currency":"USD"
        },
        "cuba":cuba_engine.public_config(language),
        "airlines":source_list(AIRLINES),
        "charters":source_list(CHARTERS),
        "legal":legal_data(language)
    }

@app.get("/api/v1/config")
async def config_v1(language:str="es"):
    return await config(language)

@app.post("/api/v1/admin/login")
async def admin_login(payload:LoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(503,"Admin credentials are not configured.")
    if not hmac.compare_digest(payload.username,ADMIN_USERNAME) or not hmac.compare_digest(payload.password,ADMIN_PASSWORD):
        raise HTTPException(401,"Credenciales inválidas.")
    t=token("admin")
    ADMIN_SESSIONS[t]=time.time()+SESSION_TTL
    return {
        "status":"success",
        "access":"granted",
        "session_token":t,
        "role":"admin",
        "expires_in":SESSION_TTL
    }

@app.post("/login-admin")
async def login_admin(payload:LoginRequest):
    return await admin_login(payload)

@app.get("/api/v1/sources/charter")
async def charter_sources(language:str="es"):
    return {
        "success":True,
        "sources":source_list(get_charters(lang(language)))
    }

@app.get("/api/v1/sources/official")
async def official_sources(language:str="es"):
    return {
        "success":True,
        "sources":source_list(get_official_sources(lang(language)))
    }

@app.post("/api/v1/flight/sources")
async def flight_sources(payload:Body):
    d=payload.model_dump()
    language=lang(d.get("language"))
    airline=clean(d.get("airline"),100)
    destination=clean(d.get("destination"),100)
    origin=clean(d.get("origin"),100)
    cuba=is_cuba_route(origin,destination)
    return {
        "success":True,
        "airline_sources":airline_matches(airline,language),
        "charter_sources":source_list(get_charters(language)) if cuba else []
    }

@app.get("/api/v1/airlines")
async def airlines(q:str=""):
    return {
        "success":True,
        "airlines":airline_matches(q)
    }

@app.get("/api/v1/airlines/{airline_id}")
async def airline(airline_id:str):
    aid=text(airline_id).lower()
    matches=[
        source_dict(x) for x in AIRLINES
        if text(getattr(x,"id","")).lower()==aid
    ]
    if not matches:
        raise HTTPException(404,"Airline not found.")
    return {"success":True,"airline":matches[0]}

@app.post("/api/v1/flight/understand")
async def understand_flight(payload:Body):
    return build_flight_response(payload.model_dump())

@app.post("/api/v1/flight/search-external")
async def search_external(payload:Body):
    d=payload.model_dump()
    q=clean(d.get("natural_query") or d.get("query"),300)
    matches=airline_matches(q)
    return {
        "status":"success",
        "query":q,
        "flights":[
            {
                "airline":x.get("name",""),
                "route":q,
                "status":"Fuente de referencia; confirma la ruta actual directamente.",
                "booking_url":x.get("url","")
            }
            for x in matches
        ],
        "charter_sources":source_list(get_charters(lang(d.get("language"))))
    }

@app.post("/api/v1/airline/practice")
async def airline_practice(payload:Body):
    return practice_data(payload.model_dump())

@app.post("/api/v1/practice/airline")
async def airline_practice_legacy(payload:Body):
    return practice_data(payload.model_dump())

@app.post("/api/v1/practice")
async def practice(payload:Body):
    return practice_data(payload.model_dump())

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
    return {
        **cuba_engine.visa_information(lang(language)),
        "official_submission":False
    }

@app.get("/api/v1/cuba/dviajeros")
async def cuba_dviajeros_info(language:str="es"):
    return {
        **cuba_engine.dviajeros_information(lang(language)),
        "official_submission":False
    }

@app.get("/api/v1/cuba/official")
async def cuba_official(language:str="es"):
    return cuba_engine.official_information(lang(language))

@app.post("/api/v1/cuba/simulation")
async def cuba_simulation(payload:Body):
    d=payload.model_dump()
    return cuba_engine.simulation(
        clean(d.get("mode") or "visa",40),
        lang(d.get("language"))
    )

@app.post("/api/v1/cuba/practice")
async def cuba_practice(payload:Body):
    d=payload.model_dump()
    return cuba_engine.simulation(
        clean(d.get("mode") or "visa",40),
        lang(d.get("language"))
    )

@app.post("/api/v1/guide")
async def guide(payload:Body):
    return guide_data(payload.model_dump())

@app.get("/api/v1/legal")
async def legal(language:str="es"):
    return legal_data(lang(language))

@app.post("/api/v1/sources/search")
async def sources_search(payload:Body):
    d=payload.model_dump()
    q=clean(d.get("query"),200)
    language=lang(d.get("language"))
    return {
        "success":True,
        "sources":source_list(get_sources("official",q)),
        "airlines":airline_matches(q,language),
        "charters":source_list(get_charters(language))
    }

@app.get("/api/v1/charters")
async def charters(q:str="",language:str="es"):
    items=get_charters(q) if q else get_charters(language)
    return {
        "success":True,
        "matches":source_list(items)
    }

@app.get("/api/v1/cuba/charters")
async def cuba_charters(language:str="es"):
    return {
        "success":True,
        "matches":source_list(get_charters(language))
    }

@app.get("/api/v1/stripe/public")
async def stripe_public():
    return {
        "enabled":bool(STRIPE_PUBLISHABLE_KEY and STRIPE_PRICE_ID1),
        "publishable_key":STRIPE_PUBLISHABLE_KEY,
        "price":15.99,
        "currency":"USD"
    }

@app.get("/api/v1/access/check")
async def access_check(request:Request):
    auth=request.headers.get("authorization","")
    t=auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    return {
        "status":"success",
        "access":"granted" if access_ok(t) else "denied"
    }

@app.post("/api/v1/create-checkout-session")
async def create_checkout(payload:CheckoutRequest,request:Request):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1:
        raise HTTPException(503,"Stripe is not configured.")
    base=str(request.base_url).rstrip("/")
    try:
        checkout=stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],
            success_url=f"{base}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base}/?payment=cancelled",
            allow_promotion_codes=True
        )
        return {
            "success":True,
            "url":checkout.url,
            "session_id":checkout.id
        }
    except Exception:
        raise HTTPException(502,"Unable to create the payment session.")

@app.post("/api/create-checkout-session")
async def create_checkout_legacy(payload:CheckoutRequest,request:Request):
    return await create_checkout(payload,request)

@app.get("/api/v1/payment-success")
async def payment_success(session_id:str):
    if not stripe.api_key:
        raise HTTPException(503,"Stripe is not configured.")
    try:
        session=stripe.checkout.Session.retrieve(session_id)
        paid=getattr(session,"payment_status","")
        if paid!="paid":
            raise HTTPException(402,"Payment has not been confirmed.")
        t=token("access")
        PAID_SESSIONS[t]={
            "created":time.time(),
            "expires":time.time()+SESSION_TTL,
            "stripe_session":session_id
        }
        return {
            "status":"success",
            "access":"granted",
            "token":t,
            "expires_in":SESSION_TTL
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400,"Unable to verify payment.")

@app.get("/api/payment-success")
async def payment_success_legacy(session_id:str):
    return await payment_success(session_id)

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    payload=await request.body()
    signature=request.headers.get("stripe-signature","")
    if STRIPE_WEBHOOK_SECRET:
        try:
            event=stripe.Webhook.construct_event(
                payload,
                signature,
                STRIPE_WEBHOOK_SECRET
            )
        except Exception:
            raise HTTPException(400,"Invalid webhook signature.")
    else:
        try:
            event=json.loads(payload.decode("utf-8"))
        except Exception:
            return {"status":"ignored"}

    if event.get("type")=="checkout.session.completed":
        obj=event.get("data",{}).get("object",{})
        sid=obj.get("id")
        if sid:
            t=token("access")
            PAID_SESSIONS[t]={
                "created":time.time(),
                "expires":time.time()+SESSION_TTL,
                "stripe_session":sid
            }

    return {"status":"success"}

@app.get("/api/v1/pdf")
async def pdf_info(language:str="es"):
    return {
        "success":True,
        "available":False,
        "message":localized(
            "La guía puede prepararse con los datos de la sesión; la generación final del PDF requiere el módulo PDF.",
            "The guide can be prepared from session data; final PDF generation requires the PDF module.",
            language
        )
    }

@app.post("/api/v1/pdf")
async def pdf_prepare(payload:Body):
    d=payload.model_dump()
    language=lang(d.get("language"))
    return {
        "success":True,
        "format":"PDF",
        "ready":True,
        "data":d,
        "message":localized(
            "Resumen preparado para generar PDF.",
            "Summary prepared for PDF generation.",
            language
        )
    }

@app.get("/api/v1/health")
async def health_v1():
    return await health()

@app.exception_handler(HTTPException)
async def http_error(request:Request,exc:HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success":False,
            "detail":exc.detail
        }
    )

@app.exception_handler(Exception)
async def general_error(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success":False,
            "detail":"Error interno del servidor."
        }
    )
