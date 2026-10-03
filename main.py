# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
import hmac,json,os,secrets,time,urllib.request
from pathlib import Path
from typing import Any,Dict,Optional
from urllib.parse import quote_plus
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from cuba_engine import engine as cuba_engine
from source_registry import SOURCES,AIRLINES,CHARTERS,get_sources,get_airlines,get_charters,get_official_sources,official_url

APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="12.1.0"
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash").strip()
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","").strip()
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","").strip()
PRICE=15.99
CURRENCY="USD"
SESSION_MINUTES=15

if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

app=FastAPI(title=APP_NAME,version=APP_VERSION)
if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

PAID_SESSIONS:Dict[str,float]={}
ADMIN_SESSIONS:Dict[str,float]={}

def now()->float:
    return time.time()

def clean(v:Any)->str:
    return str(v or "").strip()

def lang(v:Any)->str:
    return "en" if clean(v).lower().startswith("en") else "es"

def source_dict(x:Any)->Dict[str,Any]:
    if isinstance(x,dict):
        return dict(x)
    if hasattr(x,"__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(x)
    if hasattr(x,"__dict__"):
        return dict(x.__dict__)
    return {"name":clean(x)}

def source_list(items:Any)->list:
    if items is None:
        return []
    if isinstance(items,dict):
        return [source_dict(items)]
    try:
        return [source_dict(x) for x in items]
    except Exception:
        return []

def source_url(x:Any)->str:
    d=source_dict(x)
    return clean(d.get("url") or d.get("official_url"))

def normalize_airline(value:str)->Optional[Dict[str,Any]]:
    q=clean(value).lower()
    if not q:
        return None
    rows=source_list(get_airlines(""))
    exact=[]
    for x in rows:
        blob=" ".join([
            clean(x.get("id")),
            clean(x.get("name")),
            clean(x.get("publisher")),
            clean(x.get("country")),
            " ".join(x.get("topics") or [])
        ]).lower()
        if q==clean(x.get("id")).lower() or q==clean(x.get("name")).lower():
            exact.append(x)
        elif q in blob:
            exact.append(x)
    return exact[0] if exact else None

def airline_sources(value:str)->list:
    a=normalize_airline(value)
    if not a:
        return []
    sid=clean(a.get("id"))
    out=[]
    for x in source_list(SOURCES):
        if sid and (sid==clean(x.get("id")) or sid in [clean(t) for t in x.get("topics",[])]):
            out.append(x)
    if not out:
        out=[a]
    return out

def official_airline_url(value:str)->str:
    a=normalize_airline(value)
    return source_url(a) if a else ""

def is_cuba_route(origin:str,destination:str)->bool:
    blob=(clean(origin)+" "+clean(destination)).lower()
    cuba_terms=[
        "cuba","hav","havana","holguin","hol","santiago","scu","camaguey",
        "cayo coco","ccc","cayo largo","vra","varadero","santa clara","snu"
    ]
    return any(x in blob for x in cuba_terms)

def active_token(token:str)->bool:
    token=clean(token)
    if not token:
        return False
    exp=PAID_SESSIONS.get(token,0)
    if exp<=now():
        PAID_SESSIONS.pop(token,None)
        return False
    return True

def admin_token_ok(token:str)->bool:
    token=clean(token)
    exp=ADMIN_SESSIONS.get(token,0)
    if exp<=now():
        ADMIN_SESSIONS.pop(token,None)
        return False
    return True

def bearer(request:Request)->str:
    value=clean(request.headers.get("authorization"))
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return clean(request.headers.get("x-session-token"))

def grant_session()->str:
    token=secrets.token_urlsafe(32)
    PAID_SESSIONS[token]=now()+SESSION_MINUTES*60
    return token

def fallback_teach(term:str,language:str="es")->Dict[str,Any]:
    t=clean(term).lower()
    es={
        "equipaje de mano":"Es la maleta o bolso que llevas contigo en la cabina. El tamaño, peso y cantidad dependen de la aerolínea y del boleto.",
        "equipaje facturado":"Es la maleta que entregas en el mostrador para que viaje en la bodega del avión. La cantidad, peso y precio dependen del boleto y la ruta.",
        "booking":"Es el proceso de buscar y reservar un vuelo. La compra real siempre debe hacerse en el sitio oficial correspondiente.",
        "check-in":"Es el proceso mediante el cual confirmas tu viaje antes del vuelo y, cuando corresponde, obtienes tu pase de abordar.",
        "d'viajeros":"Es el formulario oficial de viaje de Cuba. Debes comprobar los requisitos y realizar el proceso en el sitio oficial.",
        "visa":"Es una autorización de entrada que puede ser necesaria según la nacionalidad, propósito y situación del viajero. Cuba tiene reglas específicas.",
        "escala":"Es una parada intermedia entre el origen y el destino final. Puede requerir revisar aeropuerto, tiempo disponible y requisitos del país de conexión.",
        "artículo personal":"Es un objeto pequeño que puede colocarse en el espacio permitido para artículos personales. La definición exacta depende de la aerolínea."
    }
    en={
        "carry-on baggage":"A bag or item you take into the aircraft cabin. Size, weight and quantity depend on the airline and ticket.",
        "checked baggage":"A bag you hand over at the airport counter to travel in the aircraft hold. Allowance and fees depend on the ticket and route.",
        "booking":"The process of searching for and reserving a flight. The real purchase must always be completed on the official site.",
        "check-in":"The process of confirming your trip before the flight and, when available, obtaining your boarding pass.",
        "d'viajeros":"Cuba's official travel form. Always verify requirements and complete the process on the official website.",
        "visa":"An authorization that may be required depending on nationality, purpose and traveler circumstances. Cuba has specific rules.",
        "connection":"An intermediate stop between origin and final destination. Airport, connection time and entry requirements may need to be checked.",
        "personal item":"A small item allowed in the personal-item space. The exact definition depends on the airline."
    }
    table=en if language=="en" else es
    return {
        "term":term,
        "explanation":table.get(
            t,
            "Consulta el término en la fuente oficial correspondiente y revisa cómo aparece en tu boleto o proceso."
        )
    }

def gemini(question:str,data:Dict[str,Any],language:str="es")->Dict[str,Any]:
    if not GEMINI_API_KEY:
        return {"success":False,"answer":"","reason":"GEMINI_API_KEY no configurada"}
    q=clean(question)
    if not q:
        return {"success":False,"answer":""}
    language_name="English" if language=="en" else "Spanish"
    prompt=f"""You are the limited AI assistant inside ¿QUÉ QUIERES LLEVAR? by May Roga LLC.
Your ONLY function is to help identify whether a travel item may be allowed, restricted, prohibited, or requires official verification for air travel.
Answer in {language_name}.
Do NOT invent airline, TSA, CBP, customs, Cuba, airport or government rules.
Do NOT make assumptions when the information is incomplete.
Do NOT provide booking, visa, D'Viajeros or immigration instructions as if you were an authority.
If you cannot establish the answer from the supplied verified information, clearly say that it must be checked on the official source.
Never request passwords, CVV, bank credentials, authentication codes or airline account credentials.
Separate confirmed information from uncertainty.
Question: {q}
Verified context: {json.dumps(data,ensure_ascii=False)[:12000]}
"""
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{quote_plus(GEMINI_MODEL)}:generateContent?key={quote_plus(GEMINI_API_KEY)}"
    body={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.1,"maxOutputTokens":700}}
    try:
        req=urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req,timeout=20) as response:
            result=json.loads(response.read().decode("utf-8"))
        text=""
        for candidate in result.get("candidates",[]):
            for part in candidate.get("content",{}).get("parts",[]):
                if part.get("text"):
                    text+=part["text"]
        return {"success":bool(text.strip()),"answer":text.strip()}
    except Exception:
        return {"success":False,"answer":"","reason":"No fue posible consultar la IA en este momento."}

def booking_steps(language:str="es")->list:
    if language=="en":
        return [
            {"step":1,"id":"route","title":"1. Your trip","description":"Check origin, destination and date.","instruction":"Enter the route exactly as you want to travel."},
            {"step":2,"id":"flight","title":"2. Find the flight","description":"Compare the available flights shown by the airline.","instruction":"Check the flight number, time and airports."},
            {"step":3,"id":"passenger","title":"3. Passenger information","description":"Enter the information requested by the airline.","instruction":"Use your real travel document when completing the official process."},
            {"step":4,"id":"baggage","title":"4. Baggage","description":"Check what your ticket includes.","instruction":"Confirm carry-on, personal item and checked baggage."},
            {"step":5,"id":"review","title":"5. Review","description":"Review every field before paying.","instruction":"Check names, dates, route, baggage and price."},
            {"step":6,"id":"official","title":"6. Official booking","description":"Now use the airline's official website.","instruction":"The simulation ends here. Complete the real booking only on the official site."}
        ]
    return [
        {"step":1,"id":"route","title":"1. Tu viaje","description":"Revisa origen, destino y fecha.","instruction":"Escribe la ruta exactamente como quieres viajar."},
        {"step":2,"id":"flight","title":"2. Buscar el vuelo","description":"Revisa los vuelos que muestra la aerolínea.","instruction":"Comprueba número de vuelo, horario y aeropuertos."},
        {"step":3,"id":"passenger","title":"3. Datos del pasajero","description":"Mira qué información solicita la aerolínea.","instruction":"En el proceso oficial usarás tu documento real."},
        {"step":4,"id":"baggage","title":"4. Equipaje","description":"Comprueba qué incluye tu boleto.","instruction":"Revisa equipaje de mano, artículo personal y equipaje facturado."},
        {"step":5,"id":"review","title":"5. Revisar","description":"Revisa todos los datos antes de pagar.","instruction":"Comprueba nombres, fechas, ruta, equipaje y precio."},
        {"step":6,"id":"official","title":"6. Booking oficial","description":"Ahora pasa al sitio oficial de la aerolínea.","instruction":"La simulación termina aquí. El booking real se hace únicamente en el sitio oficial."}
    ]

def charter_rows(language:str="es")->list:
    try:
        rows=source_list(get_charters(""))
    except Exception:
        rows=[]
    try:
        cuba_rows=source_list(cuba_engine.get_charter_sources(language))
    except Exception:
        cuba_rows=[]
    merged=[]
    seen=set()
    for x in rows+cuba_rows:
        sid=clean(x.get("id") or x.get("name")).lower()
        if sid not in seen:
            seen.add(sid)
            merged.append(x)
    return merged

def charter_baggage(name:str)->Dict[str,Any]:
    n=clean(name).lower()
    if "xael" in n:
        return {
            "carry_on":"Generalmente 1 pieza incluida; algunas condiciones pueden indicar hasta 35 lb según temporada.",
            "checked":"Tarifa por libra que puede variar según la maleta; el límite por bulto suele rondar 70 lb.",
            "note":"Confirma el boleto y las condiciones actuales con Xael Charters."
        }
    if "aerocuba" in n:
        return {
            "carry_on":"1 pieza de mano; pueden existir franquicias promocionales de hasta 35 lb.",
            "checked":"Puede cobrarse por peso o por libra según ruta y condiciones.",
            "note":"Confirma el boleto y las condiciones actuales con Aerocuba."
        }
    if "cubazul" in n:
        return {
            "carry_on":"Incluido según los términos del boleto adquirido.",
            "checked":"Pueden existir piezas de hasta 70 lb y tarifas por libra para piezas adicionales.",
            "note":"Confirma el boleto y las condiciones actuales con Cubazul Air Charter."
        }
    if "cuballama" in n:
        return {
            "carry_on":"Depende del operador y boleto.",
            "checked":"Depende del operador, ruta y boleto.",
            "note":"Confirma directamente las condiciones del vuelo adquirido."
        }
    return {"carry_on":"Verificar","checked":"Verificar","note":"Consulta el operador oficial."}

def item_result(item:str,airline:str="",origin:str="",destination:str="",language:str="es")->Dict[str,Any]:
    text=clean(item)
    low=text.lower()
    warnings=[]
    restricted_terms=[
        "gasolina","gasoline","fuel","petróleo","petroleo","sosa caustica",
        "sodium hydroxide","explosivo","explosive","dinamita","gas","butano"
    ]
    food_terms=[
        "carne","meat","jamon","jamón","yogurt","leche","milk","agua","water",
        "refresco","soda","uva","uvas","guayaba","semilla","semillas",
        "cooked food","comida cocinada"
    ]
    battery_terms=[
        "bateria","batería","battery","power bank","litio","lithium"
    ]
    if any(x in low for x in restricted_terms):
        status="verify"
        result="Artículo que requiere verificación oficial antes de viajar."
        warnings.append("No lo lleves al aeropuerto asumiendo que está permitido.")
    elif any(x in low for x in battery_terms):
        status="verify"
        result="Los dispositivos y baterías pueden tener reglas específicas de seguridad, ubicación y capacidad."
        warnings.append("Verifica las reglas de la aerolínea y la autoridad de seguridad antes de empacarlo.")
    elif any(x in low for x in food_terms):
        status="verify"
        result="Los alimentos pueden estar sujetos a reglas diferentes de seguridad aérea y de importación del destino."
        warnings.append("Si viajas a Cuba, también debes comprobar las reglas de Aduana de Cuba.")
    else:
        status="verify"
        result="No se debe determinar el permiso únicamente por el nombre del artículo. Debe comprobarse según la naturaleza del artículo, cantidad, presentación, equipaje y destino."
        warnings.append("Si existe duda, consulta la fuente oficial antes de viajar.")
    sources=[]
    if airline:
        sources+=airline_sources(airline)
    official=[
        source_dict(x) for x in source_list(SOURCES)
        if clean(x.get("category")) in {"government","security","aviation"}
    ]
    for x in official:
        if x not in sources:
            sources.append(x)
    if is_cuba_route(origin,destination):
        try:
            for x in source_list(cuba_engine.get_official_sources(language)):
                if x not in sources:
                    sources.append(x)
        except Exception:
            pass
    return {
        "success":True,
        "item":text,
        "status":status,
        "result":result,
        "explanation":fallback_teach("equipaje de mano",language)["explanation"],
        "warnings":warnings,
        "sources":sources[:12],
        "official_url":official_airline_url(airline),
        "next_action":"Revisa la fuente oficial antes de empacar el artículo."
    }

@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR/"index.html"))

@app.get("/health")
async def health():
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":APP_VERSION,
        "brain_loaded":True,
        "stripe_configured":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "gemini_configured":bool(GEMINI_API_KEY)
    }

@app.get("/api/v1/health")
async def api_health():
    return await health()

@app.get("/api/config")
async def config():
    return {
        "success":True,
        "name":APP_NAME,
        "version":APP_VERSION,
        "price":PRICE,
        "currency":CURRENCY,
        "session_minutes":SESSION_MINUTES,
        "stripe_publishable_key":STRIPE_PUBLISHABLE_KEY,
        "airlines":source_list(get_airlines("")),
        "charters":charter_rows("es")
    }

@app.get("/api/v1/config")
async def config_v1():
    return await config()

@app.get("/api/v1/access/check")
async def access_check(request:Request):
    token=bearer(request)
    active=active_token(token)
    return {
        "success":True,
        "active":active,
        "token":token if active else "",
        "expires_at":PAID_SESSIONS.get(token) if active else None
    }

@app.post("/api/v1/create-checkout-session")
async def create_checkout_session(request:Request):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1:
        raise HTTPException(503,"Pago no configurado.")
    try:
        body=await request.json()
    except Exception:
        body={}
    origin=clean(request.headers.get("origin")) or clean(body.get("origin"))
    if not origin:
        origin=f"https://{clean(request.headers.get('host'))}"
    success_url=clean(body.get("success_url")) or origin+"/?payment=success&session_id={CHECKOUT_SESSION_ID}"
    cancel_url=clean(body.get("cancel_url")) or origin+"/?payment=cancelled"
    try:
        session=stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"app":APP_NAME,"version":APP_VERSION}
        )
        return {
            "success":True,
            "checkout_url":session.url,
            "session_id":session.id,
            "publishable_key":STRIPE_PUBLISHABLE_KEY,
            "price":PRICE,
            "currency":CURRENCY,
            "period":"1_month"
        }
    except Exception:
        raise HTTPException(500,"No fue posible iniciar el pago.")

@app.post("/api/v1/payment-success")
async def payment_success(request:Request):
    try:
        body=await request.json()
    except Exception:
        body={}
    sid=clean(body.get("session_id") or body.get("sessionId"))
    if not sid or not STRIPE_SECRET_KEY:
        raise HTTPException(400,"Sesión de pago no válida.")
    try:
        session=stripe.checkout.Session.retrieve(sid)
        if clean(getattr(session,"status",""))!="complete":
            raise HTTPException(402,"El pago todavía no aparece completado.")
        payment_status=clean(getattr(session,"payment_status",""))
        if payment_status not in {"paid","no_payment_required"}:
            raise HTTPException(402,"El pago no aparece confirmado.")
        token=grant_session()
        return {
            "success":True,
            "active":True,
            "token":token,
            "expires_at":PAID_SESSIONS[token],
            "message":"Sesión activada."
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(400,"No fue posible verificar el pago.")

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
    payload=await request.body()
    signature=request.headers.get("stripe-signature","")
    try:
        if STRIPE_WEBHOOK_SECRET:
            event=stripe.Webhook.construct_event(
                payload,
                signature,
                STRIPE_WEBHOOK_SECRET
            )
        else:
            event=json.loads(payload.decode("utf-8"))
    except Exception:
        raise HTTPException(400,"Webhook inválido.")
    obj=event.get("data",{}).get("object",{})
    if event.get("type")=="checkout.session.completed":
        status=clean(obj.get("payment_status"))
        if status in {"paid","no_payment_required"}:
            grant_session()
    return {"received":True}

@app.post("/api/v1/admin/login")
async def admin_login(request:Request):
    try:
        body=await request.json()
    except Exception:
        body={}
    user=clean(body.get("username"))
    password=clean(body.get("password"))
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(503,"Acceso administrativo no configurado.")
    if not hmac.compare_digest(user,ADMIN_USERNAME) or not hmac.compare_digest(password,ADMIN_PASSWORD):
        raise HTTPException(401,"Credenciales no válidas.")
    token=secrets.token_urlsafe(32)
    ADMIN_SESSIONS[token]=now()+3600
    return {
        "success":True,
        "token":token,
        "expires_at":ADMIN_SESSIONS[token]
    }

@app.get("/api/v1/admin/status")
async def admin_status(request:Request):
    return {"success":True,"active":admin_token_ok(bearer(request))}

@app.get("/api/v1/airlines")
async def airlines(query:str=""):
    return {"success":True,"airlines":source_list(get_airlines(query))}

@app.post("/api/v1/airline")
async def airline(request:Request):
    body=await request.json()
    name=clean(body.get("airline"))
    a=normalize_airline(name)
    if not a:
        return {
            "success":False,
            "airline":{},
            "sources":[],
            "official_url":"",
            "next_action":"Selecciona una aerolínea disponible."
        }
    return {
        "success":True,
        "airline":a,
        "sources":airline_sources(name),
        "official_url":source_url(a),
        "next_action":"Revisa primero la información de tu boleto y después confirma en el sitio oficial."
    }

@app.get("/api/v1/charters")
async def charters(language:str="es"):
    return {"success":True,"charters":charter_rows(lang(language))}

@app.post("/api/v1/charter")
async def charter(request:Request):
    body=await request.json()
    name=clean(body.get("charter_operator") or body.get("charter"))
    rows=charter_rows(lang(body.get("language","es")))
    found=None
    for x in rows:
        if name.lower() in (clean(x.get("name"))+" "+clean(x.get("id"))).lower():
            found=x
            break
    if not found:
        return {
            "success":False,
            "charter":{},
            "sources":rows,
            "baggage":{},
            "next_action":"Selecciona un operador."
        }
    return {
        "success":True,
        "charter":found,
        "sources":[found],
        "baggage":charter_baggage(clean(found.get("name"))),
        "official_url":source_url(found),
        "next_action":"Confirma las condiciones actuales directamente con el operador."
    }

@app.get("/api/v1/sources/search")
async def sources_search(q:str="",topic:str="all"):
    rows=source_list(get_sources("all",q))
    return {"success":True,"sources":rows[:50],"query":q}

@app.post("/api/v1/sources/search")
async def sources_search_post(request:Request):
    body=await request.json()
    q=clean(body.get("query") or body.get("q"))
    rows=source_list(get_sources("all",q))
    return {"success":True,"sources":rows[:50],"query":q}

@app.get("/api/v1/sources/official")
async def official_sources(language:str="es",query:str=""):
    rows=source_list(get_official_sources("",query))
    rows=[x for x in rows if clean(x.get("category")) not in {"airline","charter"}]
    return {"success":True,"sources":rows[:50]}

@app.get("/api/v1/cuba/official")
async def cuba_official(language:str="es"):
    try:
        rows=source_list(cuba_engine.get_official_sources(lang(language)))
    except Exception:
        rows=[]
    return {"success":True,"sources":rows,"official":True}

@app.get("/api/v1/cuba/charters")
async def cuba_charters(language:str="es"):
    return {"success":True,"charters":charter_rows(lang(language))}

@app.post("/api/v1/flight")
async def flight(request:Request):
    body=await request.json()
    origin=clean(body.get("origin"))
    destination=clean(body.get("destination"))
    airline=clean(body.get("airline"))
    date=clean(body.get("departure_date") or body.get("date"))
    try:
        passengers=max(1,int(body.get("passengers") or 1))
    except Exception:
        passengers=1
    language=lang(body.get("language"))
    a=normalize_airline(airline)
    sources=airline_sources(airline) if a else []
    cuba=is_cuba_route(origin,destination)
    if cuba:
        try:
            sources+=source_list(cuba_engine.get_official_sources(language))
        except Exception:
            pass
    return {
        "success":True,
        "flight":{
            "origin":origin,
            "destination":destination,
            "departure_date":date,
            "airline":airline,
            "passengers":passengers,
            "cuba_route":cuba
        },
        "sources":sources[:15],
        "official_url":source_url(a) if a else "",
        "notice":"La aplicación orienta y enseña. No muestra inventario de vuelos ni realiza una reserva real.",
        "next_action":"Ahora revisa la aerolínea y después practica el booking."
    }

@app.post("/api/v1/flight/search")
async def flight_search(request:Request):
    return await flight(request)

@app.post("/api/v1/booking/simulation")
async def booking_simulation(request:Request):
    body=await request.json()
    language=lang(body.get("language"))
    airline=clean(body.get("airline"))
    steps=booking_steps(language)
    a=normalize_airline(airline)
    sid=secrets.token_urlsafe(18)
    fields=[
        {"id":"origin","label":"Origen","value":clean(body.get("origin"))},
        {"id":"destination","label":"Destino","value":clean(body.get("destination"))},
        {"id":"departure_date","label":"Fecha","value":clean(body.get("departure_date") or body.get("date"))},
        {"id":"passengers","label":"Pasajeros","value":body.get("passengers") or 1},
        {"id":"airline","label":"Aerolínea","value":airline}
    ]
    return {
        "success":True,
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "notice":"SIMULACIÓN: no reserva, no cobra y no envía datos a la aerolínea.",
        "search":{
            "airline":airline,
            "origin":clean(body.get("origin")),
            "destination":clean(body.get("destination"))
        },
        "fields":fields,
        "steps":steps,
        "next_action":steps[0]["instruction"],
        "sources":airline_sources(airline),
        "official_url":source_url(a) if a else "",
        "simulation_id":sid
    }

@app.post("/api/v1/booking")
async def booking(request:Request):
    return await booking_simulation(request)

@app.post("/api/v1/practice/start")
async def practice_start(request:Request):
    body=await request.json()
    language=lang(body.get("language"))
    scenario=clean(body.get("scenario")) or "airline_booking"
    airline=clean(body.get("airline"))
    sid=secrets.token_urlsafe(18)
    if scenario in {"cuba","cuba_booking","cuba_dviajeros","cuba_visa"}:
        try:
            sim=cuba_engine.simulation(
                "dviajeros" if "viajero" in scenario else "visa",
                language
            )
            steps=sim.get("steps",[]) if isinstance(sim,dict) else []
        except Exception:
            steps=[]
    else:
        steps=booking_steps(language)
    if not steps:
        steps=booking_steps(language)
    return {
        "success":True,
        "mode":scenario,
        "official_submission":False,
        "notice":"SIMULACIÓN DE MAY ROGA LLC. No es un sitio oficial y no envía información.",
        "completed":False,
        "pending":[str(x.get("title","")) for x in steps],
        "progress":0,
        "sources":airline_sources(airline),
        "scenarios":[
            {"id":"airline_booking","title":"Booking de aerolínea"},
            {"id":"cuba_visa","title":"Visa / eVisa de Cuba"},
            {"id":"cuba_dviajeros","title":"D’Viajeros"}
        ],
        "current_step":steps[0] if steps else {},
        "official_url":official_airline_url(airline),
        "simulation_id":sid,
        "ai_assisted":False
    }

@app.post("/api/v1/practice/step")
async def practice_step(request:Request):
    body=await request.json()
    language=lang(body.get("language"))
    scenario=clean(body.get("scenario")) or "airline_booking"
    try:
        step=max(1,int(body.get("step") or 1))
    except Exception:
        step=1
    airline=clean(body.get("airline"))
    steps=booking_steps(language)
    if scenario in {"cuba","cuba_booking","cuba_dviajeros","cuba_visa"}:
        try:
            sim=cuba_engine.simulation(
                "dviajeros" if "viajero" in scenario else "visa",
                language
            )
            csteps=sim.get("steps",[]) if isinstance(sim,dict) else []
            if csteps:
                steps=csteps
        except Exception:
            pass
    total=len(steps)
    if not total:
        return {
            "success":False,
            "mode":scenario,
            "official_submission":False,
            "notice":"No hay pasos disponibles para esta práctica.",
            "completed":False,
            "pending":[],
            "progress":0,
            "sources":airline_sources(airline),
            "scenarios":[],
            "current_step":{},
            "official_url":official_airline_url(airline),
            "simulation_id":clean(body.get("simulation_id")) or secrets.token_urlsafe(18),
            "ai_assisted":False
        }
    step=min(step,total)
    completed=step>=total
    current=steps[step-1]
    progress=100 if completed else int((step-1)*100/total)
    next_action=(
        "Práctica terminada. Ahora revisa la fuente oficial y realiza el proceso real allí."
        if completed else clean(current.get("instruction"))
    )
    return {
        "success":True,
        "mode":scenario,
        "official_submission":False,
        "notice":"SIMULACIÓN: nada de lo escrito aquí se envía a la aerolínea o autoridad.",
        "completed":completed,
        "pending":[] if completed else [clean(x.get("title")) for x in steps[step:]],
        "progress":progress,
        "sources":airline_sources(airline),
        "scenarios":[],
        "current_step":current,
        "official_url":official_airline_url(airline),
        "simulation_id":clean(body.get("simulation_id")) or secrets.token_urlsafe(18),
        "ai_assisted":False,
        "next_action":next_action
    }

@app.post("/api/v1/practice")
async def practice(request:Request):
    body=await request.json()
    if body.get("step") and body.get("simulation_id"):
        return await practice_step(request)
    return await practice_start(request)

@app.post("/api/v1/item")
async def item(request:Request):
    body=await request.json()
    return item_result(
        clean(body.get("item") or body.get("item_name") or body.get("name")),
        clean(body.get("airline")),
        clean(body.get("origin")),
        clean(body.get("destination")),
        lang(body.get("language"))
    )

@app.post("/api/v1/item/teach")
async def item_teach(request:Request):
    body=await request.json()
    term=clean(body.get("item") or body.get("term") or body.get("question"))
    language=lang(body.get("language"))
    return item_result(
        term,
        clean(body.get("airline")),
        clean(body.get("origin")),
        clean(body.get("destination")),
        language
    )

@app.post("/api/v1/baggage")
async def baggage(request:Request):
    body=await request.json()
    airline=clean(body.get("airline"))
    language=lang(body.get("language"))
    sources=airline_sources(airline)
    if is_cuba_route(clean(body.get("origin")),clean(body.get("destination"))):
        try:
            sources+=source_list(cuba_engine.get_official_sources(language))
        except Exception:
            pass
    return {
        "success":True,
        "airline":airline,
        "status":"verify",
        "baggage":{
            "carry_on":"Debe comprobarse según la aerolínea, tarifa y ruta.",
            "personal_item":"Debe comprobarse según la aerolínea.",
            "checked":"Debe comprobarse según la tarifa, ruta, temporada y condiciones del boleto.",
            "weight":body.get("weight"),
            "pieces":body.get("pieces") or 1
        },
        "explanation":"No existe una franquicia universal para todos los vuelos. La condición exacta debe comprobarse en el sitio oficial de la aerolínea.",
        "warnings":[
            "No pagues sobrepeso sin comprobar primero qué incluye tu boleto.",
            "Pesa tus maletas antes de ir al aeropuerto."
        ],
        "sources":sources[:15],
        "official_url":official_airline_url(airline),
        "next_action":"Abre la fuente oficial de tu aerolínea y comprueba tu boleto."
    }

@app.post("/api/v1/cuba/visa")
async def cuba_visa(request:Request):
    body=await request.json()
    language=lang(body.get("language"))
    data={
        "travel_purpose":clean(body.get("travel_purpose") or body.get("purpose") or body.get("purpose_of_trip")),
        "entry_type":clean(body.get("entry_type") or "air"),
        "has_passport":bool(body.get("has_passport")),
        "passport_valid":bool(body.get("passport_valid")),
        "dual_nationality":bool(body.get("dual_nationality") or body.get("dual_citizen")),
        "nationality":clean(body.get("nationality")),
        "passport_country":clean(body.get("passport_country")),
        "cuban_nationality":bool(body.get("cuban_nationality"))
    }
    try:
        result=cuba_engine.evaluate_visa(data,language)
    except Exception:
        result={
            "status":"review",
            "message":"Revisa los requisitos oficiales de Cuba antes de continuar.",
            "error":False
        }
    try:
        sources=source_list(cuba_engine.get_official_sources(language))
    except Exception:
        sources=[]
    return {
        "success":True,
        "status":clean(result.get("status")) or "review",
        "result":result,
        "notice":"La práctica no solicita ni envía una visa real.",
        "official_url":clean(getattr(cuba_engine,"OFFICIAL_VISA_URL","")),
        "sources":sources,
        "next_action":"Después de practicar, abre el sitio oficial para realizar el proceso real."
    }

@app.post("/api/v1/cuba/dviajeros")
async def cuba_dviajeros(request:Request):
    body=await request.json()
    language=lang(body.get("language"))
    data={
        "first_name":clean(body.get("first_name") or body.get("given_names")),
        "last_name":clean(body.get("last_name") or body.get("surnames")),
        "nationality":clean(body.get("nationality")),
        "date_of_birth":clean(body.get("date_of_birth") or body.get("birth_date")),
        "passport_country":clean(body.get("passport_country")),
        "arrival_date":clean(body.get("arrival_date")),
        "airline":clean(body.get("airline")),
        "accommodation":clean(body.get("accommodation")),
        "purpose_of_trip":clean(body.get("purpose_of_trip") or body.get("purpose"))
    }
    try:
        result=cuba_engine.evaluate_dviajeros(data,language)
    except Exception:
        result={
            "status":"review",
            "message":"Completa y confirma el proceso en el sitio oficial de D’Viajeros."
        }
    try:
        sources=source_list(cuba_engine.get_official_sources(language))
    except Exception:
        sources=[]
    return {
        "success":True,
        "status":clean(result.get("status")) or "review",
        "result":result,
        "notice":"SIMULACIÓN: no genera un QR oficial ni envía datos a D’Viajeros.",
        "official_url":clean(getattr(cuba_engine,"OFFICIAL_DVIAJEROS_URL","")),
        "sources":sources,
        "next_action":"Cuando termines la práctica, abre D’Viajeros oficial y completa el proceso real."
    }

@app.post("/api/v1/cuba/practice")
async def cuba_practice(request:Request):
    body=await request.json()
    language=lang(body.get("language"))
    mode=clean(body.get("mode") or body.get("scenario") or "dviajeros").lower()
    mode="visa" if "visa" in mode else "dviajeros"
    try:
        sim=cuba_engine.simulation(mode,language)
    except Exception:
        sim={}
    steps=sim.get("steps",[]) if isinstance(sim,dict) else []
    sid=clean(body.get("simulation_id")) or secrets.token_urlsafe(18)
    return {
        "success":True,
        "simulation":True,
        "official_submission":False,
        "mode":mode,
        "simulation_id":sid,
        "current_step":1,
        "total_steps":len(steps),
        "progress":0,
        "completed":False,
        "notice":"Esta simulación no crea una visa, no genera un QR oficial y no envía datos.",
        "steps":steps,
        "official_url":clean(getattr(
            cuba_engine,
            "OFFICIAL_VISA_URL" if mode=="visa" else "OFFICIAL_DVIAJEROS_URL",
            ""
        )),
        "next_action":clean(
            steps[0].get("instruction") if steps else "Comienza por el primer paso."
        )
    }

@app.post("/api/v1/cuba")
async def cuba(request:Request):
    body=await request.json()
    return await cuba_visa(request) if body.get("mode")=="visa" or body.get("purpose") else await cuba_dviajeros(request)

@app.post("/api/v1/guide")
async def guide(request:Request):
    body=await request.json()
    language=lang(body.get("language"))
    airline=clean(body.get("airline"))
    origin=clean(body.get("origin"))
    destination=clean(body.get("destination"))
    cuba=is_cuba_route(origin,destination)
    steps=[
        {"id":"flight","number":1,"title":"Entender mi vuelo","done":False},
        {"id":"airline","number":2,"title":"Revisar mi aerolínea","done":False},
        {"id":"baggage","number":3,"title":"Revisar mi equipaje","done":False},
        {"id":"items","number":4,"title":"Revisar lo que llevo","done":False},
        {"id":"practice","number":5,"title":"Practicar antes del proceso real","done":False}
    ]
    if cuba:
        steps+=[
            {"id":"visa","number":6,"title":"Revisar visa / eVisa de Cuba","done":False},
            {"id":"dviajeros","number":7,"title":"Practicar D’Viajeros","done":False}
        ]
    steps.append({
        "id":"official",
        "number":len(steps)+1,
        "title":"Confirmar todo en las fuentes oficiales",
        "done":False
    })
    sources=airline_sources(airline)
    try:
        if cuba:
            sources+=source_list(cuba_engine.get_official_sources(language))
    except Exception:
        pass
    official_urls=[source_url(x) for x in sources if source_url(x)]
    return {
        "success":True,
        "guide":{
            "origin":origin,
            "destination":destination,
            "airline":airline,
            "departure_date":clean(body.get("departure_date")),
            "passengers":body.get("passengers") or 1,
            "cuba_route":cuba
        },
        "steps":steps,
        "completed_steps":[],
        "next_action":steps[0]["title"] if steps else "",
        "sources":sources[:20],
        "official_urls":list(dict.fromkeys(official_urls))
    }

@app.post("/api/v1/solve")
async def solve(request:Request):
    body=await request.json()
    question=clean(body.get("question"))
    language=lang(body.get("language"))
    data=body.get("data") if isinstance(body.get("data"),dict) else {}
    result=gemini(question,data,language)
    if result.get("success"):
        return {
            "success":True,
            "answer":result["answer"],
            "ai_assisted":True,
            "official_required":True,
            "next_action":"Si la respuesta no está confirmada, consulta la fuente oficial."
        }
    return {
        "success":True,
        "answer":"",
        "ai_assisted":False,
        "official_required":True,
        "next_action":"No hay una respuesta verificada disponible. Consulta la fuente oficial correspondiente."
    }

@app.post("/api/v1/ai/interpret")
async def ai_interpret(request:Request):
    return await solve(request)

@app.post("/api/v1/teach")
async def teach(request:Request):
    body=await request.json()
    term=clean(body.get("term") or body.get("question"))
    language=lang(body.get("language"))
    return {
        "success":True,
        **fallback_teach(term,language),
        "ai_assisted":False
    }

@app.post("/api/v1/pdf")
async def pdf(request:Request):
    body=await request.json()
    state=body.get("state") if isinstance(body.get("state"),dict) else {}
    language=lang(body.get("language"))
    return {
        "success":True,
        "format":"pdf-ready",
        "notice":"Resumen preparado con la información introducida por el cliente. No es un documento oficial.",
        "sections":{
            "trip":{
                "origin":clean(state.get("origin")),
                "destination":clean(state.get("destination")),
                "airline":clean(state.get("airline"))
            },
            "booking":state.get("booking",{}),
            "baggage":state.get("baggage",{}),
            "visa":state.get("visa",{}),
            "dviajeros":state.get("dviajeros",{})
        },
        "next_action":"Usa este resumen como guía para comprobar la información en los sitios oficiales."
    }

@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success":False,
            "error":"server_error",
            "message":"Ocurrió un error interno. Intenta nuevamente."
        }
    )

@app.get("/favicon.ico")
async def favicon():
    f=STATIC_DIR/"favicon.ico"
    if f.exists():
        return FileResponse(str(f))
    raise HTTPException(404,"Not found")
