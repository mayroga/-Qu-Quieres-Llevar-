# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.1.0
import os,secrets,time,json
from pathlib import Path
from typing import Any,Dict,Optional

import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles

try:
    from flight_engine import engine as flight_engine
except Exception:
    try:
        from flight_engine import flight_engine
    except Exception:
        flight_engine=None

try:
    from source_registry import REGISTRY
except Exception:
    REGISTRY=None

try:
    import rules_engine as advisor
except Exception:
    advisor=None

APP_VERSION="8.1.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
PRICE_USD=15.99
SESSION_MINUTES=15
SESSION_SECONDS=SESSION_MINUTES*60

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","").strip()
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","").strip()
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","").strip()
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","").strip()

if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
INDEX_FILE=STATIC_DIR/"index.html"

app=FastAPI(title=APP_NAME,version=APP_VERSION)
if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

ACTIVE_PAID_SESSIONS:Dict[str,Dict[str,Any]]={}
ADMIN_SESSIONS:Dict[str,Dict[str,Any]]={}
PAYMENT_SESSIONS:Dict[str,Dict[str,Any]]={}


def now():
    return int(time.time())


def clean(v):
    if v is None:
        return ""
    return str(v).strip()


def lang_of(data=None):
    if isinstance(data,dict):
        return "en" if clean(data.get("language")).lower()=="en" else "es"
    return "es"


def public_error(e):
    s=clean(e)
    return s or "No se pudo completar la operación."


def token():
    return secrets.token_urlsafe(32)


def cleanup_sessions():
    t=now()
    for store in (ACTIVE_PAID_SESSIONS,ADMIN_SESSIONS,PAYMENT_SESSIONS):
        dead=[]
        for k,v in store.items():
            exp=v.get("expires_at")
            if exp and exp<t:
                dead.append(k)
        for k in dead:
            store.pop(k,None)


def active_service(t):
    cleanup_sessions()
    return bool(t and t in ACTIVE_PAID_SESSIONS and ACTIVE_PAID_SESSIONS[t].get("expires_at",0)>now())


def active_admin(t):
    cleanup_sessions()
    return bool(t and t in ADMIN_SESSIONS and ADMIN_SESSIONS[t].get("expires_at",0)>now())


def get_auth(request:Request):
    return clean(request.headers.get("X-Service-Token")),clean(request.headers.get("X-Admin-Token"))


def authorized(request:Request):
    service,admin=get_auth(request)
    if active_service(service):
        return "service",service
    if active_admin(admin):
        return "admin",admin
    return None,None


def require_access(request:Request):
    kind,t=authorized(request)
    if not kind:
        raise HTTPException(status_code=401,detail="Se requiere acceso mediante pago o administrador.")
    return kind,t


def source_to_dict(s):
    if isinstance(s,dict):
        return dict(s)
    if hasattr(s,"to_dict"):
        try:
            return dict(s.to_dict())
        except Exception:
            pass
    d={}
    for k in ("id","name","url","category","description","official","alternate_url","verified","verified_date","country","airline","source_type"):
        if hasattr(s,k):
            d[k]=getattr(s,k)
    return d


def normalize_sources(items,language="es"):
    if items is None:
        return []
    if isinstance(items,dict):
        items=items.get("sources") or items.get("charter_sources") or items.get("official_sources") or items.get("links") or []
    if not isinstance(items,(list,tuple)):
        return []
    out=[]
    for s in items:
        if isinstance(s,dict):
            d=dict(s)
        else:
            d=source_to_dict(s)
        if not d.get("url"):
            continue
        if not d.get("name"):
            d["name"]="Fuente oficial"
        if not d.get("description"):
            d["description"]=""
        if "verified" not in d:
            d["verified"]=bool(d.get("verified_date") or d.get("official",False))
        out.append(d)
    return out


def call(fn,*args,**kwargs):
    if not callable(fn):
        return None
    try:
        return fn(*args,**kwargs)
    except TypeError:
        try:
            return fn(*args)
        except Exception:
            return None
    except Exception:
        return None


def engine_call(name,*args,**kwargs):
    if not flight_engine:
        return None
    return call(getattr(flight_engine,name,None),*args,**kwargs)


def registry_call(name,*args,**kwargs):
    if not REGISTRY:
        return None
    return call(getattr(REGISTRY,name,None),*args,**kwargs)


def advisor_call(name,*args,**kwargs):
    if not advisor:
        return None
    return call(getattr(advisor,name,None),*args,**kwargs)


def model_data(data):
    if isinstance(data,dict):
        return dict(data)
    if hasattr(data,"model_dump"):
        try:
            return data.model_dump(exclude_none=True)
        except Exception:
            pass
    if hasattr(data,"dict"):
        try:
            return data.dict(exclude_none=True)
        except Exception:
            pass
    return {}


def official_links():
    items=[]
    if REGISTRY:
        x=registry_call("official_sources")
        items=normalize_sources(x)
    if not items:
        items=[
            {
                "id":"dviajeros",
                "name":"D’Viajeros",
                "url":"https://dviajeros.mitrans.gob.cu/",
                "category":"Cuba",
                "description":"Portal oficial para el formulario D’Viajeros.",
                "official":True,
                "verified":True
            },
            {
                "id":"evisa-cuba",
                "name":"eVisa Cuba",
                "url":"https://evisacuba.cu/",
                "category":"Cuba",
                "description":"Portal oficial relacionado con la visa electrónica de Cuba.",
                "official":True,
                "verified":True
            },
            {
                "id":"tsa",
                "name":"TSA",
                "url":"https://www.tsa.gov/travel/security-screening/whatcanibring/all",
                "category":"Baggage",
                "description":"Información oficial de seguridad y artículos permitidos.",
                "official":True,
                "verified":True
            },
            {
                "id":"faa-packsafe",
                "name":"FAA PackSafe",
                "url":"https://www.faa.gov/hazmat/packsafe",
                "category":"Baggage",
                "description":"Información oficial de la FAA sobre artículos regulados.",
                "official":True,
                "verified":True
            }
        ]
    return items


def legal_notice(language="es"):
    if language=="en":
        return {
            "short_notice":"¿QUÉ QUIERES LLEVAR? is an independent service of May Roga LLC. It is not the Cuban government, D’Viajeros, eVisa Cuba, an airline, airport, bank, travel agency or government authority.",
            "full_notice":"The application organizes information, explains processes and directs the user to official sources. It does not issue visas, guarantee entry, sell airline tickets, determine customs decisions or replace official requirements.",
            "user_guidance":"Always verify current requirements directly with the official source before traveling.",
            "source_notice":"Official links are provided for the user's direct verification."
        }
    return {
        "short_notice":"¿QUÉ QUIERES LLEVAR? es un servicio independiente de May Roga LLC. No es el gobierno de Cuba, D’Viajeros, eVisa Cuba, una aerolínea, aeropuerto, banco, agencia de viajes ni autoridad gubernamental.",
        "full_notice":"La aplicación organiza información, explica procesos y dirige al usuario a fuentes oficiales. No emite visas, no garantiza la entrada a Cuba, no vende boletos, no decide sobre aduanas y no sustituye los requisitos oficiales.",
        "user_guidance":"Antes de viajar, verifica siempre los requisitos vigentes directamente con la fuente oficial correspondiente.",
        "source_notice":"Los enlaces oficiales se ofrecen para que el usuario pueda verificar directamente la información."
    }


def google_url(origin="",destination=""):
    if flight_engine:
        x=engine_call("google_flights_url",origin,destination)
        if x:
            return x
    if REGISTRY:
        x=registry_call("google_flights_url",origin,destination)
        if x:
            return x
    o=clean(origin).replace(" ","+")
    d=clean(destination).replace(" ","+")
    return f"https://www.google.com/travel/flights?q=flights+from+{o}+to+{d}"


@app.get("/")
async def root():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return JSONResponse({"app":APP_NAME,"version":APP_VERSION})


@app.get("/health")
async def health():
    cleanup_sessions()
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":APP_VERSION,
        "stripe":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "flight_engine":bool(flight_engine),
        "registry":bool(REGISTRY),
        "advisor":bool(advisor)
    }


@app.get("/api/v1/config")
async def config():
    return {
        "app_name":APP_NAME,
        "version":APP_VERSION,
        "price_usd":PRICE_USD,
        "session_minutes":SESSION_MINUTES,
        "payment_type":"one_time",
        "language":"es",
        "stripe_publishable_key":STRIPE_PUBLISHABLE_KEY,
        "official_sources":official_links()
    }


@app.get("/api/v1/session")
async def session(request:Request):
    kind,t=authorized(request)
    if not kind:
        return {"active":False,"authenticated":False}
    if kind=="admin":
        s=ADMIN_SESSIONS.get(t,{})
        return {
            "active":True,
            "authenticated":True,
            "admin":True,
            "expires_at":s.get("expires_at"),
            "remaining_seconds":max(0,s.get("expires_at",0)-now())
        }
    s=ACTIVE_PAID_SESSIONS.get(t,{})
    return {
        "active":True,
        "authenticated":True,
        "admin":False,
        "expires_at":s.get("expires_at"),
        "remaining_seconds":max(0,s.get("expires_at",0)-now())
    }


@app.post("/api/v1/admin/login")
async def admin_login(request:Request):
    data=await request.json()
    user=clean(data.get("username"))
    password=clean(data.get("password"))
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=503,detail="El acceso de administrador no está configurado en Render.")
    if not secrets.compare_digest(user,ADMIN_USERNAME) or not secrets.compare_digest(password,ADMIN_PASSWORD):
        raise HTTPException(status_code=401,detail="Usuario o contraseña incorrectos.")
    t=token()
    ADMIN_SESSIONS[t]={
        "created_at":now(),
        "expires_at":now()+86400*30,
        "admin":True
    }
    return {"ok":True,"token":t,"admin_token":t,"expires_at":ADMIN_SESSIONS[t]["expires_at"]}


@app.post("/api/v1/create-checkout-session")
async def create_checkout_session(request:Request):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503,detail="Stripe no está configurado.")
    if not STRIPE_PRICE_ID1:
        raise HTTPException(status_code=503,detail="STRIPE_PRICE_ID1 no está configurado.")
    try:
        data=await request.json()
    except Exception:
        data={}
    language=lang_of(data)
    base=str(request.base_url).rstrip("/")
    success=f"{base}/?session_id={{CHECKOUT_SESSION_ID}}"
    cancel=f"{base}/?payment=cancelled"
    try:
        s=stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],
            success_url=success,
            cancel_url=cancel,
            metadata={"app":"qql","language":language,"version":APP_VERSION},
            allow_promotion_codes=False
        )
        PAYMENT_SESSIONS[s.id]={
            "created_at":now(),
            "status":"created",
            "language":language
        }
        return {"ok":True,"checkout_url":s.url,"url":s.url,"session_id":s.id}
    except Exception as e:
        raise HTTPException(status_code=502,detail=f"No se pudo crear el pago: {public_error(e)}")


@app.post("/api/v1/verify-payment")
async def verify_payment(request:Request):
    data=await request.json()
    sid=clean(data.get("session_id") or data.get("checkout_session_id"))
    if not sid:
        raise HTTPException(status_code=400,detail="Falta session_id.")
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503,detail="Stripe no está configurado.")
    try:
        s=stripe.checkout.Session.retrieve(sid)
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"No se pudo verificar el pago: {public_error(e)}")
    paid=(getattr(s,"payment_status","")=="paid")
    status=clean(getattr(s,"status",""))
    if not paid or status!="complete":
        raise HTTPException(status_code=402,detail="El pago todavía no está confirmado.")
    t=token()
    exp=now()+SESSION_SECONDS
    ACTIVE_PAID_SESSIONS[t]={
        "created_at":now(),
        "expires_at":exp,
        "stripe_session_id":sid,
        "language":clean((getattr(s,"metadata",{}) or {}).get("language")) or "es"
    }
    PAYMENT_SESSIONS[sid]={
        "created_at":PAYMENT_SESSIONS.get(sid,{}).get("created_at",now()),
        "status":"paid",
        "token":t,
        "expires_at":exp
    }
    return {
        "ok":True,
        "token":t,
        "service_token":t,
        "expires_at":exp,
        "minutes":SESSION_MINUTES
    }


@app.post("/api/v1/webhook")
async def stripe_webhook(request:Request):
    payload=await request.body()
    signature=request.headers.get("stripe-signature","")
    if not STRIPE_WEBHOOK_SECRET:
        return {"received":True}
    try:
        event=stripe.Webhook.construct_event(payload,signature,STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400,detail=f"Webhook inválido: {public_error(e)}")
    typ=event.get("type","")
    obj=event.get("data",{}).get("object",{})
    if typ=="checkout.session.completed":
        sid=obj.get("id")
        if sid:
            PAYMENT_SESSIONS[sid]={
                **PAYMENT_SESSIONS.get(sid,{}),
                "status":"paid",
                "updated_at":now()
            }
    return {"received":True}


@app.get("/api/v1/legal")
async def legal():
    return legal_notice("es")


@app.get("/api/v1/official")
async def official(request:Request):
    return {"sources":official_links(),"official_sources":official_links()}


@app.get("/api/v1/sources/official")
async def sources_official(request:Request):
    return {"sources":official_links(),"official_sources":official_links()}


@app.get("/api/v1/rules")
async def rules(request:Request):
    kind,_=require_access(request)
    data=[]
    if advisor:
        repo=getattr(advisor,"repo",None)
        if repo and hasattr(repo,"to_dicts"):
            try:
                data=repo.to_dicts()
            except Exception:
                data=[]
    return {
        "version":getattr(advisor,"VERSION",APP_VERSION) if advisor else APP_VERSION,
        "rules":data or []
    }


@app.get("/api/v1/sources/charter")
async def sources_charter(request:Request):
    require_access(request)
    language=clean(request.query_params.get("language")) or "es"
    items=engine_call("charter_sources",language)
    if items is None:
        items=engine_call("charter_sources")
    return {"sources":normalize_sources(items,language),"charter_sources":normalize_sources(items,language)}


@app.get("/api/v1/sources/search")
async def sources_search(request:Request):
    require_access(request)
    q=clean(request.query_params.get("q"))
    country=clean(request.query_params.get("country"))
    airline=clean(request.query_params.get("airline"))
    destination=clean(request.query_params.get("destination"))
    source_type=clean(request.query_params.get("source_type"))
    items=registry_call("search",q,country,airline,destination,source_type)
    if items is None:
        items=registry_call("search",q)
    return {"sources":normalize_sources(items)}


@app.get("/api/v1/sources/route")
async def sources_route(request:Request):
    require_access(request)
    origin=clean(request.query_params.get("origin"))
    destination=clean(request.query_params.get("destination"))
    airline=clean(request.query_params.get("airline"))
    language=clean(request.query_params.get("language")) or "es"
    items=engine_call("source_cards",origin,destination,airline,language)
    if items is None:
        items=engine_call("sources_for_route",origin,destination,airline,language)
    return {
        "sources":normalize_sources(items,language),
        "google_flights_url":google_url(origin,destination),
        "is_cuba_route":bool(engine_call("is_cuba_route",origin,destination))
    }


@app.get("/api/v1/sources/baggage")
async def sources_baggage(request:Request):
    require_access(request)
    origin=clean(request.query_params.get("origin"))
    destination=clean(request.query_params.get("destination"))
    airline=clean(request.query_params.get("airline"))
    language=clean(request.query_params.get("language")) or "es"
    items=registry_call("baggage_sources",origin,destination,airline)
    if items is None:
        items=official_links()
    cards=[]
    for s in normalize_sources(items,language):
        cards.append(s)
    return {"sources":cards,"baggage_sources":cards}


@app.get("/api/v1/cuba/sources")
async def cuba_sources(request:Request):
    require_access(request)
    origin=clean(request.query_params.get("origin"))
    destination=clean(request.query_params.get("destination")) or "Cuba"
    airline=clean(request.query_params.get("airline"))
    language=clean(request.query_params.get("language")) or "es"
    items=engine_call("cuba_sources",origin,destination,airline,language)
    if items is None:
        items=official_links()
    return {"sources":normalize_sources(items,language),"official_sources":normalize_sources(items,language)}


@app.get("/api/v1/cuba/official")
async def cuba_official(request:Request):
    require_access(request)
    language=clean(request.query_params.get("language")) or "es"
    src=official_links()
    if language=="en":
        title="Official Cuba information"
        intro="Verify current Cuba entry, travel and required-form information directly through official sources."
        req=[
            "Check the current visa or eVisa requirement for your nationality.",
            "Check passport validity and nationality-specific requirements.",
            "Complete D’Viajeros when required.",
            "Verify baggage and prohibited-item rules before departure.",
            "Verify airline requirements directly before traveling."
        ]
    else:
        title="Información oficial de Cuba"
        intro="Verifica directamente las condiciones vigentes de entrada, viaje y formularios mediante las fuentes oficiales."
        req=[
            "Comprueba el requisito de visa o eVisa según tu nacionalidad.",
            "Comprueba la vigencia del pasaporte y los requisitos según tu nacionalidad.",
            "Completa D’Viajeros cuando corresponda.",
            "Verifica el equipaje y los artículos prohibidos antes de salir.",
            "Verifica directamente con la aerolínea sus requisitos antes del viaje."
        ]
    return {
        "title":title,
        "intro":intro,
        "important_requirements":req,
        "sources":src,
        "official_sources":src,
        "next_action":(
            "Abre la fuente oficial correspondiente y verifica tu situación antes de comprar o viajar."
            if language=="es" else
            "Open the corresponding official source and verify your situation before buying or traveling."
        ),
        "legal_notice":legal_notice(language)
    }


@app.post("/api/v1/flight/sources")
async def flight_sources_post(request:Request):
    require_access(request)
    data=await request.json()
    origin=clean(data.get("origin"))
    destination=clean(data.get("destination"))
    airline=clean(data.get("airline"))
    language=lang_of(data)
    items=engine_call("source_cards",origin,destination,airline,language)
    if items is None:
        items=engine_call("sources_for_route",origin,destination,airline,language)
    if items is None:
        items=engine_call("charter_sources",language)
    return {
        "sources":normalize_sources(items,language),
        "charter_sources":normalize_sources(items,language),
        "google_flights_url":google_url(origin,destination),
        "is_cuba_route":bool(engine_call("is_cuba_route",origin,destination))
    }


@app.get("/api/v1/flight/sources")
async def flight_sources_get(request:Request):
    require_access(request)
    origin=clean(request.query_params.get("origin"))
    destination=clean(request.query_params.get("destination"))
    airline=clean(request.query_params.get("airline"))
    language=clean(request.query_params.get("language")) or "es"
    items=engine_call("source_cards",origin,destination,airline,language)
    if items is None:
        items=engine_call("sources_for_route",origin,destination,airline,language)
    if items is None:
        items=engine_call("charter_sources",language)
    return {
        "sources":normalize_sources(items,language),
        "charter_sources":normalize_sources(items,language),
        "google_flights_url":google_url(origin,destination),
        "is_cuba_route":bool(engine_call("is_cuba_route",origin,destination))
    }


@app.post("/api/v1/flight/search-external")
async def flight_search_external(request:Request):
    require_access(request)
    payload=await request.json()
    data=model_data(payload)
    result=engine_call("search",**data)
    if result is None:
        result=engine_call("search_external",**data)
    if result is None:
        return {
            "ok":True,
            "results":[],
            "message":"No se obtuvieron resultados externos verificados."
        }
    return result


@app.post("/api/v1/flight/understand")
async def flight_understand(request:Request):
    require_access(request)
    payload=await request.json()
    data=model_data(payload)
    language=lang_of(data)
    result=engine_call("understand",data,language=language)
    if result is None:
        origin=clean(data.get("origin"))
        destination=clean(data.get("destination"))
        departure_date=clean(data.get("departure_date"))
        return {
            "origin":origin,
            "destination":destination,
            "departure_date":departure_date,
            "google_flights_url":google_url(origin,destination),
            "charter_sources":normalize_sources(engine_call("charter_sources",language),language),
            "airline_sources":normalize_sources(engine_call("airline_sources",clean(data.get("airline")),language),language),
            "next_action":"Verifica directamente los resultados y requisitos con las fuentes oficiales."
        }
    if isinstance(result,dict):
        return result
    if hasattr(result,"model_dump"):
        return result.model_dump()
    return {"result":result}


@app.post("/api/v1/consultar-articulo")
async def consultar_articulo(request:Request):
    require_access(request)
    data=await request.json()
    item=clean(data.get("item") or data.get("article") or data.get("itemName"))
    quantity=data.get("quantity",1)
    description=clean(data.get("description"))
    if not item:
        raise HTTPException(status_code=400,detail="Escribe el artículo.")
    kwargs={
        "item":item,
        "quantity":quantity,
        "description":description,
        "baggage_type":clean(data.get("baggage_type")),
        "airline":clean(data.get("airline")),
        "destination":clean(data.get("destination")),
        "origin":clean(data.get("origin")),
        "cabin":clean(data.get("cabin")),
        "fare":clean(data.get("fare")),
        "language":lang_of(data)
    }
    result=advisor_call("advise",**kwargs)
    if result is None:
        result=advisor_call("advise_item",item,language=kwargs["language"])
    if result is None:
        result={
            "item":item,
            "status":"verify",
            "message":(
                "No se pudo determinar de forma verificable si el artículo está permitido. "
                "Consulta la fuente oficial de seguridad y las reglas de la aerolínea."
                if kwargs["language"]=="es" else
                "It could not be verified whether this item is allowed. "
                "Check the official security source and the airline's rules."
            ),
            "official_sources":official_links()
        }
    if hasattr(result,"model_dump"):
        return result.model_dump()
    return result if isinstance(result,dict) else {"result":result}


@app.post("/api/v1/item/teach")
async def item_teach(request:Request):
    require_access(request)
    data=await request.json()
    term=clean(data.get("term") or data.get("item"))
    language=lang_of(data)
    if not term:
        raise HTTPException(status_code=400,detail="Escribe un término.")
    result=advisor_call("explain_term",term,language=language)
    if result is None:
        result={
            "term":term,
            "explanation":(
                f"No hay una explicación verificada disponible para “{term}”."
                if language=="es" else
                f"No verified explanation is available for “{term}”."
            ),
            "official_sources":official_links()
        }
    if hasattr(result,"model_dump"):
        return result.model_dump()
    return result if isinstance(result,dict) else {"result":result}


@app.post("/api/v1/guide")
async def guide(request:Request):
    require_access(request)
    data=await request.json()
    language=lang_of(data)
    flight=data.get("flight") if isinstance(data.get("flight"),dict) else data
    origin=clean(flight.get("origin"))
    destination=clean(flight.get("destination"))
    cuba=bool(engine_call("is_cuba_route",origin,destination))
    if language=="en":
        steps=[
            "Confirm your origin, destination and travel date.",
            "Check your airline's current requirements directly.",
            "Check passport validity and nationality-specific requirements.",
            "Check visa or eVisa requirements when applicable.",
            "Complete D’Viajeros when required.",
            "Check baggage and prohibited-item rules.",
            "Keep the official confirmations and documents available for travel."
        ]
        next_action="Start with the official source that applies to your nationality and trip."
    else:
        steps=[
            "Confirma tu origen, destino y fecha de viaje.",
            "Comprueba directamente los requisitos vigentes de tu aerolínea.",
            "Comprueba la vigencia del pasaporte y los requisitos según tu nacionalidad.",
            "Comprueba si necesitas visa o eVisa.",
            "Completa D’Viajeros cuando corresponda.",
            "Comprueba las reglas de equipaje y artículos prohibidos.",
            "Conserva las confirmaciones y documentos oficiales disponibles para el viaje."
        ]
        next_action="Comienza por la fuente oficial que corresponda a tu nacionalidad y viaje."
    cuba_steps=[]
    if cuba:
        if language=="en":
            cuba_steps=[
                "Check the current Cuba entry requirements.",
                "Check the visa or eVisa requirement for your nationality.",
                "Check passport validity and any Cuba-specific nationality rules.",
                "Complete D’Viajeros when required.",
                "Verify airline and baggage requirements directly."
            ]
        else:
            cuba_steps=[
                "Comprueba los requisitos vigentes de entrada a Cuba.",
                "Comprueba el requisito de visa o eVisa según tu nacionalidad.",
                "Comprueba la vigencia del pasaporte y las reglas específicas de Cuba según tu nacionalidad.",
                "Completa D’Viajeros cuando corresponda.",
                "Verifica directamente los requisitos de la aerolínea y del equipaje."
            ]
    return {
        "steps":steps,
        "cuba_steps":cuba_steps,
        "official_sources":official_links(),
        "next_action":next_action,
        "legal_notice":legal_notice(language)
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request:Request,exc:HTTPException):
    return JSONResponse(status_code=exc.status_code,content={"detail":exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail":"Se produjo un error interno. Intenta nuevamente.",
            "error_type":type(exc).__name__
        }
    )
