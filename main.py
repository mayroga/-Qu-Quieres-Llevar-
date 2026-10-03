# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v9.0.0
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from pathlib import Path
from typing import Any,Optional
from datetime import datetime,timezone
import json,os,secrets

APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="9.0.0"
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
BRAIN_FILE=BASE_DIR/"app_brain.json"
SOURCE_FILE=BASE_DIR/"source_registry.py"
MAX_BODY=1024*1024

app=FastAPI(title=APP_NAME,version=APP_VERSION,description="Preparación independiente de viaje, vuelos, equipaje, artículos y procesos oficiales.")

if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

SESSIONS={}

def now():
    return datetime.now(timezone.utc).isoformat()

def clean(v,max_len=500):
    return str(v or "").strip()[:max_len]

def language(v):
    return "en" if str(v or "es").lower()=="en" else "es"

def session_new(lang="es"):
    token=secrets.token_urlsafe(24)
    SESSIONS[token]={"token":token,"language":language(lang),"created_at":now(),"data":{}}
    return SESSIONS[token]

def get_session(token):
    if not token or token not in SESSIONS:
        raise HTTPException(401,"Session not found.")
    return SESSIONS[token]

def source(name,url,description="",publisher="",verified=""):
    return {"name":name,"url":url,"description":description,"publisher":publisher,"verified":verified}

OFFICIAL_SOURCES=[
    source("D’Viajeros","https://dviajeros.mitrans.gob.cu/","Official Cuban D’Viajeros portal.","Cuban authorities","2026-10-01"),
    source("eVisa Cuba","https://evisacuba.cu/","Official Cuba eVisa information/application portal.","Cuban authorities","2026-10-01"),
    source("Cuba — Official Travel Information","https://www.cubaminrex.cu/","Official Cuban government information. Confirm the applicable authority for your case.","Ministerio de Relaciones Exteriores de Cuba","2026-10-01")
]

def result(title="",message="",next_action="",steps=None,sources=None,status="review"):
    return {
        "title":title,
        "message":message,
        "next_action":next_action,
        "steps":steps or [],
        "sources":sources or [],
        "status":status
    }

class SessionCreate(BaseModel):
    language:str="es"

class FlightRequest(BaseModel):
    session_token:Optional[str]=None
    language:str="es"
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    cabin:str=""
    fare:str=""
    passengers:int=1
    stops:int=0

class ItemRequest(BaseModel):
    session_token:Optional[str]=None
    language:str="es"
    item:str=""
    quantity:str="1"
    description:str=""
    baggage_type:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    cabin:str=""
    fare:str=""

class BaggageRequest(BaseModel):
    session_token:Optional[str]=None
    language:str="es"
    baggage_type:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    cabin:str=""
    fare:str=""

class GuideRequest(BaseModel):
    session_token:Optional[str]=None
    language:str="es"
    flight:dict[str,Any]={}

class TeachRequest(BaseModel):
    session_token:Optional[str]=None
    language:str="es"
    term:str=""

class PracticeRequest(BaseModel):
    session_token:Optional[str]=None
    language:str="es"
    practice_type:str="airline"
    mode:str=""
    airline:str=""

def save_data(token,data):
    if token and token in SESSIONS:
        SESSIONS[token]["data"].update(data)

@app.middleware("http")
async def body_limit(request:Request,call_next):
    size=request.headers.get("content-length")
    if size and int(size)>MAX_BODY:
        raise HTTPException(413,"Request too large.")
    return await call_next(request)

@app.get("/",include_in_schema=False)
async def root():
    index=STATIC_DIR/"index.html"
    if not index.exists():
        raise HTTPException(404,"Application interface not found.")
    return FileResponse(str(index))

@app.get("/health")
async def health():
    return {"status":"ok","app":APP_NAME,"version":APP_VERSION,"sessions":len(SESSIONS)}

@app.get("/api/v1/config")
async def config(language:str="es"):
    l=language(language)
    return {
        "app":{"name":APP_NAME,"version":APP_VERSION,"brand":"May Roga LLC","language":l},
        "service":{
            "type":"independent_travel_preparation",
            "real_booking":False,
            "real_payment":False,
            "official_confirmation_required":True
        },
        "flow":[
            "QUIERO VIAJAR",
            "ENTIENDO MI VUELO",
            "ENTIENDO MI ESCALA",
            "ENTIENDO MI EQUIPAJE",
            "REVISO LO QUE QUIERO LLEVAR",
            "PREPARO MIS DOCUMENTOS",
            "PRACTICO",
            "CONFIRMO EN LA FUENTE OFICIAL",
            "DESCARGO MI GUÍA"
        ],
        "cuba":{"dviajeros":"https://dviajeros.mitrans.gob.cu/","evisa":"https://evisacuba.cu/"},
        "official_sources":OFFICIAL_SOURCES
    }

@app.post("/api/v1/session")
async def create_session(body:SessionCreate):
    s=session_new(body.language)
    return {"active":True,"session_token":s["token"],"language":s["language"]}

@app.get("/api/v1/session")
async def current_session(session_token:Optional[str]=None):
    if session_token:
        s=get_session(session_token)
        return {"active":True,"session":s}
    return {"active":False}

@app.delete("/api/v1/session")
async def delete_session(session_token:Optional[str]=None):
    if session_token:
        SESSIONS.pop(session_token,None)
    return {"success":True}

@app.post("/api/v1/flight/understand")
async def flight_understand(body:FlightRequest):
    origin=clean(body.origin)
    destination=clean(body.destination)
    if not origin or not destination:
        raise HTTPException(422,"Origin and destination are required.")
    token=clean(body.session_token)
    save_data(token,body.model_dump())
    l=language(body.language)
    if l=="en":
        steps=[
            "Confirm the exact origin airport.",
            "Confirm the destination airport.",
            "Check the travel date and return date if applicable.",
            "Check the airline, cabin and fare shown by the official source.",
            "Check whether the trip is nonstop, has a connection or changes aircraft.",
            "Confirm baggage conditions for the exact itinerary and fare."
        ]
        message="Your trip information is organized. The airline or official provider remains the final source for current flight and fare conditions."
    else:
        steps=[
            "Confirma el aeropuerto exacto de salida.",
            "Confirma el aeropuerto exacto de llegada.",
            "Revisa la fecha de salida y la fecha de regreso si corresponde.",
            "Revisa la aerolínea, cabina y tarifa que muestra la fuente oficial.",
            "Comprueba si el viaje es directo, tiene conexión o cambia de avión.",
            "Confirma las condiciones de equipaje para ese itinerario y esa tarifa."
        ]
        message="Tus datos básicos están organizados. La aerolínea o fuente oficial sigue siendo la fuente final para las condiciones actuales del vuelo y la tarifa."
    return result(
        "Información del vuelo" if l=="es" else "Flight information",
        message,
        "Confirma los datos en la fuente oficial antes de comprar." if l=="es" else "Confirm the information with the official source before purchasing.",
        steps,
        [],
        "organized"
    )|{"origin":origin,"destination":destination,"departure_date":clean(body.departure_date),"return_date":clean(body.return_date),"airline":clean(body.airline)}

@app.post("/api/v1/flight/search")
async def flight_search(body:FlightRequest):
    return await flight_understand(body)

@app.post("/api/v1/flight/sources")
async def flight_sources(body:FlightRequest):
    airline=clean(body.airline)
    return {
        "airline":airline,
        "charter_sources":[],
        "sources":[],
        "message":"Confirma las reglas directamente con la aerolínea o proveedor correspondiente."
    }

@app.get("/api/v1/sources/official")
async def official_sources():
    return {"sources":OFFICIAL_SOURCES}

@app.get("/api/v1/official-sources")
async def official_sources_alt():
    return {"sources":OFFICIAL_SOURCES}

@app.post("/api/v1/item/check")
async def item_check(body:ItemRequest):
    item=clean(body.item)
    if not item:
        raise HTTPException(422,"Item is required.")
    token=clean(body.session_token)
    save_data(token,body.model_dump())
    l=language(body.language)
    if l=="en":
        steps=[
            "Identify what the item is.",
            "Determine where it would travel: personal item, cabin baggage or checked baggage.",
            "Check whether the item has a battery, liquid, aerosol, sharp component, food, medicine or other special condition.",
            "Check the airline rules for the exact itinerary and fare.",
            "Check government or airport rules when the item is subject to official restrictions.",
            "Confirm the final rule at the official source before traveling."
        ]
        message="The item needs contextual verification. The application does not invent an airline rule when the exact rule is not confirmed."
        action="Check the airline's official baggage and restricted-items information."
    else:
        steps=[
            "Identifica exactamente qué artículo es.",
            "Determina dónde viajaría: artículo personal, equipaje de cabina o equipaje documentado.",
            "Comprueba si tiene batería, líquido, aerosol, parte cortante, alimento, medicamento u otra condición especial.",
            "Revisa las reglas de la aerolínea para el itinerario y la tarifa exactos.",
            "Revisa las reglas del gobierno o aeropuerto cuando el artículo esté sujeto a restricciones oficiales.",
            "Confirma la regla final en la fuente oficial antes de viajar."
        ]
        message="El artículo necesita una revisión contextual. La aplicación no inventa una regla de una aerolínea cuando la regla exacta no está confirmada."
        action="Revisa la información oficial de equipaje y artículos restringidos de la aerolínea."
    return result("Revisión del artículo" if l=="es" else "Item review",message,action,steps,[],"review")|{"item":item}

@app.post("/api/v1/consultar-articulo")
async def item_check_legacy(body:ItemRequest):
    return await item_check(body)

@app.post("/api/v1/baggage")
async def baggage(body:BaggageRequest):
    token=clean(body.session_token)
    save_data(token,body.model_dump())
    l=language(body.language)
    if l=="en":
        title="Prepare your baggage"
        message="First identify the baggage type. Then confirm the exact allowance for your airline, route and fare."
        steps=[
            "Identify whether it is a personal item.",
            "Identify whether it is cabin baggage.",
            "Identify whether it is checked baggage.",
            "Check the number of pieces allowed.",
            "Check the dimensions and weight published by the airline.",
            "Check special restrictions for batteries, liquids, food, medicine and other items."
        ]
        action="Open the airline's official baggage rules and confirm the exact allowance."
    else:
        title="Prepara tu equipaje"
        message="Primero identifica el tipo de equipaje. Después confirma el límite exacto de tu aerolínea, ruta y tarifa."
        steps=[
            "Identifica si es un artículo personal.",
            "Identifica si es equipaje de cabina.",
            "Identifica si es equipaje documentado.",
            "Comprueba cuántas piezas permite la tarifa.",
            "Comprueba las medidas y el peso publicados por la aerolínea.",
            "Comprueba las restricciones especiales de baterías, líquidos, alimentos, medicamentos y otros artículos."
        ]
        action="Abre las reglas oficiales de equipaje de la aerolínea y confirma el límite exacto."
    return result(title,message,action,steps,[],"review")

@app.post("/api/v1/item/teach")
async def teach(body:TeachRequest):
    term=clean(body.term)
    if not term:
        raise HTTPException(422,"Term is required.")
    l=language(body.language)
    terms={
        "equipaje de mano":"La maleta o bolsa pequeña que puedes llevar contigo durante el viaje. La aerolínea determina sus medidas, peso y condiciones." if l=="es" else "Cabin baggage is the bag you may take with you during the trip. The airline determines its size, weight and conditions.",
        "equipaje documentado":"La maleta que entregas a la aerolínea antes de pasar al avión y que viaja en la bodega." if l=="es" else "Checked baggage is the bag you hand to the airline before boarding and that travels in the aircraft hold.",
        "artículo personal":"Una bolsa pequeña que puede acompañarte y que debe cumplir las condiciones de la aerolínea." if l=="es" else "A small bag that may accompany you and must meet the airline's conditions.",
        "escala":"Una parada durante el viaje. Puede ser necesario cambiar de avión o permanecer en el mismo avión según el itinerario." if l=="es" else "A stop during the trip. You may need to change aircraft or remain on the same aircraft depending on the itinerary.",
        "conexión":"Cuando un viaje continúa mediante otro vuelo después de una parada." if l=="es" else "When a trip continues on another flight after a stop.",
        "tarifa":"La modalidad de compra del boleto que determina condiciones que pueden incluir cambios, equipaje y otros servicios." if l=="es" else "The fare type that determines conditions that may include changes, baggage and other services."
    }
    text=terms.get(term.lower())
    if not text:
        text=("Busca el término en la página oficial de tu aerolínea o autoridad. La aplicación puede ayudarte a entenderlo cuando tengamos una definición confirmada."
              if l=="es" else
              "Look for the term on your airline's or authority's official page. The application can help explain it when a confirmed definition is available.")
    return {"title":term,"explanation":text,"next_action":"Comprueba cómo aplica a tu viaje específico." if l=="es" else "Check how it applies to your specific trip.","status":"educational"}

@app.post("/api/v1/guide")
async def guide(body:GuideRequest):
    l=language(body.language)
    if l=="en":
        steps=[
            "Confirm your origin, destination and travel dates.",
            "Confirm the airline, itinerary, connections and fare.",
            "Review baggage allowance for the exact fare.",
            "Review every special item you plan to carry.",
            "Prepare the documents required for your trip.",
            "Complete any official forms required for your destination.",
            "Practice the process before completing it for real.",
            "Confirm everything with the official source immediately before travel."
        ]
        action="Finish by checking the official airline and government sources for your exact trip."
    else:
        steps=[
            "Confirma origen, destino y fechas.",
            "Confirma aerolínea, itinerario, conexiones y tarifa.",
            "Revisa el equipaje permitido para esa tarifa.",
            "Revisa cada artículo especial que piensas llevar.",
            "Prepara los documentos necesarios para tu viaje.",
            "Completa los formularios oficiales que correspondan a tu destino.",
            "Practica el proceso antes de hacerlo de verdad.",
            "Confirma todo con las fuentes oficiales inmediatamente antes del viaje."
        ]
        action="Termina comprobando las fuentes oficiales de la aerolínea y del gobierno para tu viaje exacto."
    return result("Mi guía" if l=="es" else "My guide","Preparación organizada." if l=="es" else "Preparation organized.",action,steps,OFFICIAL_SOURCES,"guide")

@app.get("/api/v1/cuba/official")
async def cuba_official(language:str="es"):
    l=language(language)
    message="Confirma los requisitos de entrada según tu nacionalidad, documentos, fecha de viaje y situación particular." if l=="es" else "Confirm entry requirements according to your nationality, documents, travel date and particular situation."
    return result("Preparación para Cuba" if l=="es" else "Cuba preparation",message,"Confirma siempre la información en las fuentes oficiales.",[
        "Revisa los requisitos según tu nacionalidad.",
        "Comprueba el pasaporte y su vigencia aplicable.",
        "Comprueba si necesitas visa/eVisa.",
        "Completa D’Viajeros cuando corresponda.",
        "Revisa las reglas de equipaje y artículos restringidos.",
        "Confirma cualquier requisito adicional antes de viajar."
    ],OFFICIAL_SOURCES,"official_review")

@app.post("/api/v1/cuba/practice")
async def cuba_practice(body:PracticeRequest):
    mode=clean(body.mode).lower()
    l=language(body.language)
    if mode not in {"visa","dviajeros"}:mode="dviajeros"
    if mode=="dviajeros":
        steps=[
            "Abre el portal oficial de D’Viajeros.",
            "Identifica los campos que solicita el formulario.",
            "Practica el orden de la información sin introducir datos sensibles.",
            "Revisa la información antes de completar el proceso real.",
            "Completa el proceso real solamente en el portal oficial."
        ]
        title="Práctica D’Viajeros"
    else:
        steps=[
            "Abre la fuente oficial de visa/eVisa de Cuba.",
            "Comprueba el requisito correspondiente a tu nacionalidad.",
            "Revisa los documentos y datos solicitados.",
            "Practica el orden del proceso sin enviar información real.",
            "Completa el proceso real solamente mediante la fuente oficial correspondiente."
        ]
        title="Práctica visa/eVisa de Cuba"
    if l=="en":
        title=title.replace("Práctica","Practice").replace("D’Viajeros","D’Viajeros").replace("visa/eVisa de Cuba","Cuba visa/eVisa")
        steps=[
            "Open the official source.",
            "Identify the information requested.",
            "Practice the order without entering sensitive information.",
            "Review the information before completing the real process.",
            "Complete the real process only through the official source."
        ]
    return {"title":title,"steps":steps,"sources":OFFICIAL_SOURCES,"simulation":True}

@app.get("/api/v1/cuba/visa")
async def cuba_visa(language:str="es"):
    l=language(language)
    return {
        "title":"Visa/eVisa de Cuba" if l=="es" else "Cuba visa/eVisa",
        "message":"Revisa el requisito aplicable a tu nacionalidad y confirma la información en la fuente oficial." if l=="es" else "Check the requirement applicable to your nationality and confirm it with the official source.",
        "official_link":"https://evisacuba.cu/",
        "sources":[OFFICIAL_SOURCES[1]]
    }

@app.get("/api/v1/cuba/dviajeros")
async def cuba_dviajeros(language:str="es"):
    l=language(language)
    return {
        "title":"D’Viajeros",
        "message":"Practica el orden del proceso y completa el formulario real solamente en el portal oficial." if l=="es" else "Practice the process order and complete the real form only on the official portal.",
        "official_link":"https://dviajeros.mitrans.gob.cu/",
        "sources":[OFFICIAL_SOURCES[0]]
    }

@app.get("/api/v1/legal")
async def legal(language:str="es"):
    l=language(language)
    if l=="en":
        return {
            "short_notice":"May Roga LLC is independent and does not represent airlines, governments, airports, consulates or authorities.",
            "full_notice":"This application provides travel preparation and educational guidance. It does not sell or reserve flights and does not submit government or airline forms on your behalf.",
            "user_guidance":"Rules, prices, schedules and requirements can change. Confirm the final information with the applicable official source before traveling.",
            "source_notice":"When a rule cannot be confirmed, the application identifies what must be checked and where to check it."
        }
    return {
        "short_notice":"May Roga LLC es independiente y no representa a aerolíneas, gobiernos, aeropuertos, consulados ni autoridades.",
        "full_notice":"Esta aplicación ofrece preparación y orientación educativa para viajes. No vende ni reserva vuelos y no presenta formularios gubernamentales o de aerolíneas en nombre del usuario.",
        "user_guidance":"Las reglas, precios, horarios y requisitos pueden cambiar. Confirma la información final con la fuente oficial correspondiente antes de viajar.",
        "source_notice":"Cuando una regla no puede confirmarse, la aplicación indica qué debe comprobarse y dónde comprobarlo."
    }

@app.post("/api/v1/practice")
async def practice(body:PracticeRequest):
    if body.practice_type=="cuba":
        return await cuba_practice(body)
    l=language(body.language)
    airline=clean(body.airline) or ("mi aerolínea" if l=="es" else "my airline")
    if l=="en":
        steps=[
            f"Practice with {airline}. Nothing is purchased.",
            "Open the airline's official website or app.",
            "Enter a fictional origin, destination and date.",
            "Review flight options, airports, times and connections.",
            "Review a fictional passenger record.",
            "Review baggage and fare conditions.",
            "Review the trip before payment.",
            "Stop before payment. The real process must be completed on the official airline site or app."
        ]
        title=f"Practice: {airline}"
    else:
        steps=[
            f"Practicaremos con {airline}. No se compra nada.",
            "Abre el sitio o aplicación oficial de la aerolínea.",
            "Introduce un origen, destino y fecha ficticios.",
            "Revisa vuelos, aeropuertos, horarios y conexiones.",
            "Revisa un pasajero ficticio.",
            "Revisa equipaje y condiciones de la tarifa.",
            "Revisa el viaje antes del pago.",
            "Detente antes del pago. El proceso real debe hacerse en el sitio o aplicación oficial."
        ]
        title=f"Práctica: {airline}"
    return {"title":title,"steps":steps,"simulation":True,"real_transaction":False}

@app.get("/api/v1/pdf/prepare")
async def pdf_prepare():
    return {"available":False,"message":"El generador PDF se conectará cuando se complete el módulo de guía y persistencia local."}

@app.get("/api/v1/debug/routes")
async def debug_routes():
    return {"routes":[r.path for r in app.routes if getattr(r,"path",None)]}
