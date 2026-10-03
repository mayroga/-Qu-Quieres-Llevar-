# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v10.0.0
from __future__ import annotations
import os,secrets,time
from pathlib import Path
from typing import Any,Dict
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from cuba_engine import *
from source_registry import *
from schemas import *

APP_NAME="¿QUÉ QUIERES LLEVAR?"
VERSION="10.0.0"
BASE=Path(__file__).resolve().parent
STATIC=BASE/"static"
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","").strip()
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","").strip()
STRIPE_PRICE_ID=os.getenv("STRIPE_PRICE_ID",os.getenv("STRIPE_PRICE_ID1","")).strip()
STRIPE_MODE=os.getenv("STRIPE_MODE","subscription").strip().lower()
STRIPE_SUCCESS_URL=os.getenv("STRIPE_SUCCESS_URL","").strip()
STRIPE_CANCEL_URL=os.getenv("STRIPE_CANCEL_URL","").strip()
if STRIPE_SECRET_KEY:
    stripe.api_key=STRIPE_SECRET_KEY

app=FastAPI(title=APP_NAME,version=VERSION)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
if STATIC.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC)),name="static")

ACCESS_TTL=12*60*60
ACCESS:Dict[str,float]={}

def clean(v:Any)->str:
    return str(v or "").strip()

def truth(v:Any)->bool:
    if isinstance(v,bool): return v
    return clean(v).lower() in {"1","true","yes","si","sí","y","on"}

def data_dict(obj:Any)->Dict[str,Any]:
    if hasattr(obj,"model_dump"): return obj.model_dump()
    if isinstance(obj,dict): return dict(obj)
    return {}

def token_ok(token:str)->bool:
    token=clean(token)
    if not token or token not in ACCESS:return False
    if time.time()>ACCESS[token]:
        ACCESS.pop(token,None)
        return False
    return True

def result(title:str,message:str,next_action:str="",sources=None,**kwargs):
    d={"ok":True,"title":title,"message":message,"next_action":next_action,"sources":sources or []}
    d.update(kwargs)
    return d

def normalize_booking(d:Dict[str,Any])->Dict[str,Any]:
    if not d.get("return_date") and d.get("return"):
        d["return_date"]=d.get("return")
    return d

def official(topic:str="official",query:str=""):
    try:
        return get_sources(topic,query)
    except Exception:
        try:return sources_for(topic)
        except Exception:return []

@app.get("/",response_class=FileResponse)
async def home():
    f=STATIC/"index.html"
    if not f.exists():raise HTTPException(404,"Archivo principal no encontrado")
    return FileResponse(str(f))

@app.get("/health",response_model=HealthResponse)
async def health():
    return HealthResponse(ok=True,app=APP_NAME,version=VERSION,status="ready")

@app.get("/api/config")
async def config():
    return {"ok":True,"app":APP_NAME,"version":VERSION,"price":"15.99","stripe_ready":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID),"language":"es","features":{"flight":True,"booking_simulation":True,"baggage":True,"items":True,"cuba":True,"documents":True,"practice":True,"sources":True,"guide":True,"dviajeros_simulation":True,"visa_simulation":True}}

@app.get("/api/legal")
async def legal():
    return {"ok":True,"title":"Servicio independiente","message":"May Roga LLC ofrece preparación y orientación independiente. No somos gobierno, aerolínea, aeropuerto, autoridad migratoria, proveedor oficial de D’Viajeros ni proveedor oficial de visa/eVisa. Las simulaciones no envían información ni realizan trámites reales.","next_action":"Cuando un trámite deba realizarse, utiliza la fuente oficial correspondiente."}

@app.post("/api/access",response_model=AccessResponse)
async def access(req:AccessRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return AccessResponse(ok=False,authorized=False,message="El acceso administrativo no está configurado.")
    if secrets.compare_digest(clean(req.username),ADMIN_USERNAME) and secrets.compare_digest(req.password,ADMIN_PASSWORD):
        token=secrets.token_urlsafe(32)
        ACCESS[token]=time.time()+ACCESS_TTL
        return AccessResponse(ok=True,authorized=True,token=token,message="Acceso autorizado.")
    return AccessResponse(ok=False,authorized=False,message="Usuario o contraseña incorrectos.")

@app.post("/api/checkout",response_model=CheckoutResponse)
async def checkout(req:CheckoutRequest,request:Request):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        return CheckoutResponse(ok=False,message="El acceso de Stripe todavía no está configurado.")
    success=clean(req.success_url) or STRIPE_SUCCESS_URL or str(request.base_url).rstrip("/")+"/?payment=success"
    cancel=clean(req.cancel_url) or STRIPE_CANCEL_URL or str(request.base_url).rstrip("/")+"/?payment=cancelled"
    try:
        params={"mode":"subscription" if STRIPE_MODE!="payment" else "payment","line_items":[{"price":STRIPE_PRICE_ID,"quantity":1}],"success_url":success,"cancel_url":cancel}
        session=stripe.checkout.Session.create(**params)
        return CheckoutResponse(ok=True,url=session.url,session_id=session.id,message="Sesión de Stripe creada.")
    except Exception as e:
        return CheckoutResponse(ok=False,message=f"No se pudo crear la sesión de Stripe: {clean(e)}")

@app.post("/api/flight",response_model=FlightResponse)
async def flight(req:FlightRequest):
    d=data_dict(req)
    try:
        r=analyze_flight(d)
        if isinstance(r,dict):return r
    except Exception:pass
    origin=clean(d.get("origin"))
    destination=clean(d.get("destination"))
    airline=clean(d.get("airline"))
    number=clean(d.get("flight_number"))
    stops=d.get("stops","")
    stop_text=clean(stops)
    connections=0
    if isinstance(stops,list):connections=len(stops)
    elif stop_text:
        try:connections=int(stop_text)
        except Exception:connections=0
    has=connections>0 or any(x in stop_text.lower() for x in ["escala","conex","stop","layover"])
    if not origin or not destination:
        return FlightResponse(ok=False,title="Completa tu vuelo",message="Indica origen y destino para poder organizar el itinerario.",next_action="Escribe origen y destino.")
    segments=[{"from":origin,"to":destination,"airline":airline,"flight_number":number,"type":"segmento"}]
    return FlightResponse(ok=True,title="Tu itinerario",route=f"{origin} → {destination}",segments=segments,connections=connections,has_connection=has,message="La app puede ayudarte a entender cada tramo, pero los procedimientos de conexión dependen de la ruta, aeropuerto, aerolínea, boleto y situación del viaje.",next_action="Verifica los detalles de la conexión con la aerolínea y el aeropuerto.",sources=official("flight"))

@app.post("/api/booking",response_model=BookingResponse)
async def booking(req:BookingRequest):
    d=normalize_booking(data_dict(req))
    origin=clean(d.get("origin"));destination=clean(d.get("destination"))
    if not origin or not destination:
        return BookingResponse(ok=False,title="Completa la búsqueda",message="Indica origen y destino para practicar una búsqueda de vuelo.",next_action="Completa origen y destino.",sources=official("flight"))
    nonstop=d.get("nonstop")
    return BookingResponse(ok=True,title="Simulación de búsqueda",simulation=True,real_booking=False,payment=False,message="Esta pantalla representa una búsqueda de vuelos para practicar el proceso. No reserva, no compra y no cobra.",search={"origin":origin,"destination":destination,"departure":clean(d.get("departure")),"return_date":clean(d.get("return_date")),"passengers":d.get("passengers",1),"cabin":clean(d.get("cabin")) or "Economy","bags":d.get("bags",0),"nonstop":nonstop},next_action="Compara los detalles que aparecen en la fuente oficial antes de comprar.",sources=official("airlines"))

@app.post("/api/baggage",response_model=BaggageResponse)
async def baggage(req:BaggageRequest):
    d=data_dict(req)
    try:
        r=check_baggage(d)
        if isinstance(r,dict):return r
    except Exception:pass
    typ=clean(d.get("type"));item=clean(d.get("item"));airline=clean(d.get("airline"))
    details=[]
    if typ:details.append(f"Tipo de equipaje indicado: {typ}.")
    if item:details.append(f"Artículo indicado: {item}.")
    details+=["La aerolínea puede establecer límites de cantidad, peso, tamaño o piezas.","La seguridad aeroportuaria puede aplicar reglas diferentes a las de la aerolínea.","El país de destino puede aplicar reglas adicionales de aduana o entrada."]
    return BaggageResponse(ok=True,title="Revisión de equipaje",message="No se debe asumir que un artículo está permitido solo por pertenecer a un tipo de equipaje.",status="verify",details=details,sources=official("baggage",airline),next_action="Confirma la regla específica con la aerolínea y, cuando corresponda, seguridad y aduana.")

@app.post("/api/item",response_model=ItemResponse)
async def item(req:ItemRequest):
    d=data_dict(req)
    try:
        r=check_item(d)
        if isinstance(r,dict):return r
    except Exception:pass
    item_name=clean(d.get("item"))
    if not item_name:
        return ItemResponse(ok=False,title="Escribe el artículo",message="Indica qué quieres llevar para organizar qué reglas debes revisar.",next_action="Escribe el nombre del artículo.")
    low=item_name.lower()
    authorities=["Aerolínea","Seguridad del transporte","Aduana del destino"]
    category="Artículo por verificar"
    if any(x in low for x in ["medic","medicine","pill","tableta"]):
        category="Medicamentos"
        authorities=["Aerolínea","Seguridad del transporte","Aduana del destino","Requisitos del país de destino"]
    elif any(x in low for x in ["bater","power bank","litio","lithium"]):
        category="Baterías/electrónicos"
        authorities=["Aerolínea","Seguridad del transporte"]
    elif any(x in low for x in ["comida","food","carne","meat","fruta","fruit"]):
        category="Alimentos"
        authorities=["Aerolínea","Seguridad del transporte","Aduana del destino"]
    elif any(x in low for x in ["líquido","liquido","liquid","perfume","shampoo"]):
        category="Líquidos"
        authorities=["Aerolínea","Seguridad del transporte"]
    return ItemResponse(ok=True,title=f"Revisión: {item_name}",item=item_name,category=category,status="verify",message="La aplicación no certifica por sí sola que el artículo esté permitido. Te indica qué reglas debes revisar y dónde confirmarlas.",details=["Primero revisa las condiciones de transporte de la aerolínea.","Después revisa las reglas de seguridad aplicables al aeropuerto/origen.","Si viajas internacionalmente, revisa además las reglas de aduana y entrada del destino."],authorities=authorities,sources=official("items",item_name),next_action="Confirma la regla específica en las fuentes oficiales antes de empacar.")

@app.post("/api/cuba",response_model=CubaResponse)
async def cuba(req:CubaRequest):
    d=data_dict(req)
    try:
        r=cuba_check(d)
        if isinstance(r,dict):return r
    except Exception:pass
    details=[]
    nationality=clean(d.get("nationality"))
    passport=clean(d.get("passport_country"))
    if nationality:details.append(f"Nacionalidad indicada: {nationality}.")
    if passport:details.append(f"Pasaporte indicado: {passport}.")
    if truth(d.get("cuban_nationality")) or truth(d.get("dual_citizen")):
        details.append("La situación de nacionalidad cubana/doble nacionalidad requiere revisar las reglas oficiales aplicables a tu caso.")
    details+=["Revisa pasaporte y documentación de viaje.","Verifica si necesitas visa/eVisa según tu nacionalidad y situación concreta.","Completa D’Viajeros cuando corresponda siguiendo el sitio oficial.","Revisa aduana y artículos que piensas llevar."]
    return CubaResponse(ok=True,title="Preparación para Cuba",message="Tu preparación depende de tu nacionalidad, documentación, ruta y propósito del viaje. La aplicación organiza las verificaciones, pero no determina por sí sola tu elegibilidad legal.",status="verify",details=details,next_action="Continúa con Documentos y Practicar para revisar los pasos pendientes.",sources=official("cuba"))

@app.post("/api/documents",response_model=DocumentResponse)
async def documents(req:DocumentRequest):
    d=data_dict(req)
    try:
        r=document_check(d)
        if isinstance(r,dict):return r
    except Exception:pass
    docs=[{"name":"Pasaporte/documento de viaje","status":"pending"},{"name":"Requisitos de entrada del destino","status":"pending"}]
    destination=clean(d.get("destination")).lower()
    if "cuba" in destination or clean(d.get("destination")).lower()=="cu":
        docs += [{"name":"Visa/eVisa, si corresponde","status":"pending"},{"name":"D’Viajeros","status":"pending"},{"name":"Requisitos de aduana","status":"pending"}]
    return DocumentResponse(ok=True,title="Mis documentos",message="Esta lista es una guía de preparación. No certifica que cumplas los requisitos legales de entrada.",documents=docs,next_action="Revisa cada documento en la fuente oficial correspondiente.",sources=official("documents",clean(d.get("destination"))))

@app.post("/api/practice",response_model=PracticeResponse)
async def practice(req:PracticeRequest):
    d=data_dict(req)
    try:
        r=practice_scenario(d)
        if isinstance(r,dict):return r
    except Exception:pass
    scenario=clean(d.get("scenario")) or "aeropuerto"
    scenarios=[
        {"id":"airport","title":"Estoy en el aeropuerto","question":"¿Qué revisarías primero?","options":["Puerta y vuelo","Reglas oficiales","Ambas según la situación"]},
        {"id":"connection","title":"Tengo una escala","question":"¿Qué necesitas confirmar?","options":["Si cambio de avión","Puerta/terminal","Equipaje","Requisitos del aeropuerto"]},
        {"id":"lost_connection","title":"Perdí una conexión","question":"¿Cuál es el siguiente paso práctico?","options":["Buscar asistencia de la aerolínea","Revisar nueva información del vuelo","Confirmar opciones con el personal autorizado"]},
        {"id":"baggage","title":"Mi maleta no aparece","question":"¿Qué haces?","options":["Buscar el área de equipaje","Localizar el mostrador de equipaje de la aerolínea","Conservar documentos y comprobantes"]},
        {"id":"dviajeros","title":"Practicar D’Viajeros","question":"¿Qué tipo de información debes preparar?","options":["Datos personales","Datos del viaje","Información requerida por el formulario"]}
    ]
    return PracticeResponse(ok=True,title="Practicar",mode="practice",official_submission=False,message="Estas prácticas sirven para preparar decisiones y pasos. No envían información a autoridades.",next_action="Elige un escenario y completa la práctica.",completed=[],pending=[scenario],progress=0,sources=official("practice"),scenarios=scenarios)

@app.post("/api/connection")
async def connection(req:ConnectionRequest):
    d=data_dict(req)
    airport=clean(d.get("airport"));next_flight=clean(d.get("next_flight"))
    details=["Confirma si el siguiente vuelo sale del mismo terminal.","Confirma si debes pasar nuevamente por seguridad.","Confirma con la aerolínea si debes recoger y volver a entregar el equipaje.","Si cambias de país, revisa los requisitos migratorios correspondientes."]
    if truth(d.get("same_ticket")):details.append("Indicaste que los vuelos están en el mismo boleto; confirma con la aerolínea qué asistencia y manejo de equipaje aplica a tu itinerario.")
    else:details.append("Si son boletos separados, confirma directamente con las aerolíneas cómo se maneja la conexión.")
    return result("Entender mi conexión","Una conexión puede cambiar según aeropuerto, ruta, aerolíneas, boleto y equipaje.", "Confirma estos puntos antes de continuar.",official("connection",airport),details=details,airport=airport,next_flight=next_flight)

@app.post("/api/airlines",response_model=AirlineResponse)
async def airlines(req:AirlineRequest):
    d=data_dict(req)
    q=clean(d.get("name") or d.get("airline"))
    try:
        matches=find_airlines(q)
    except Exception:
        matches=[]
    return AirlineResponse(ok=True,query=q,matches=matches or airline_list(),message="La lista identifica fuentes oficiales. La presencia de una aerolínea en la lista no significa que opere actualmente una ruta específica.",next_action="Confirma la ruta y condiciones actuales directamente con la aerolínea.")

@app.post("/api/sources",response_model=SourceResponse)
async def sources(req:SourceRequest):
    d=data_dict(req)
    topic=clean(d.get("topic")) or "official"
    q=clean(d.get("query"))
    return SourceResponse(ok=True,topic=topic,sources=official(topic,q))

@app.post("/api/guide",response_model=GuideResponse)
async def guide(req:GuideRequest):
    d=data_dict(req)
    trip={k:d.get(k) for k in ["origin","destination","airline","flight_number","flight_type","stops","nationality","passport_country","cuban_nationality","dual_citizen","purpose","arrival_date","departure_date","current_state"]}
    items=d.get("items") or []
    pending=[]
    if not clean(d.get("origin")) or not clean(d.get("destination")):pending.append("Completar origen y destino")
    if not clean(d.get("nationality")):pending.append("Revisar nacionalidad")
    if not clean(d.get("passport_country")):pending.append("Revisar pasaporte")
    if str(d.get("destination","")).lower() in {"cuba","cu","cuba republic"}:
        if not truth(d.get("visa_checked")):pending.append("Verificar visa/eVisa")
        if not truth(d.get("dviajeros_done")):pending.append("Practicar/completar D’Viajeros")
        if not truth(d.get("customs_checked")):pending.append("Revisar aduana")
    if not pending:next_action="Tu guía no muestra pasos pendientes con la información proporcionada."
    else:next_action=pending[0]
    docs={"dviajeros":truth(d.get("dviajeros_done")),"visa":truth(d.get("visa_checked")),"customs":truth(d.get("customs_checked"))}
    return GuideResponse(ok=True,title="Mi guía",trip=trip,flight={"airline":clean(d.get("airline")),"flight_number":clean(d.get("flight_number")),"stops":d.get("stops","")},documents=docs,items_reviewed=[{"name":clean(x),"status":"reviewed"} for x in items if clean(x)],pending=pending,next_action=next_action,message="La guía organiza tu preparación. No sustituye la confirmación oficial de requisitos.")

@app.post("/api/solve")
async def solve(req:SolveRequest):
    d=data_dict(req)
    q=clean(d.get("question"))
    if not q:return result("Cuéntame qué ocurre","Escribe qué está pasando durante tu preparación o viaje.","Describe el problema con tus propias palabras.")
    low=q.lower()
    if any(x in low for x in ["escala","conex","connection","layover"]):
        return result("Revisemos tu conexión","Para una escala hay que confirmar aeropuerto, terminal, puerta, cambio de avión, seguridad y equipaje según tu ruta.","Abre Mi vuelo y completa los datos de tu itinerario.",official("connection"),category="connection")
    if any(x in low for x in ["maleta","equipaje","baggage","luggage"]):
        return result("Revisemos tu equipaje","La regla puede depender de la aerolínea, seguridad y destino.","Abre Mi equipaje y escribe qué llevas.",official("baggage"),category="baggage")
    if any(x in low for x in ["cuba","dviajero","visa","evisa"]):
        return result("Revisemos tu viaje a Cuba","Primero hay que identificar nacionalidad, pasaporte, ruta y trámite que estás intentando preparar.","Abre Viajo a Cuba.",official("cuba"),category="cuba")
    return result("Vamos paso a paso","Necesito identificar si tu duda es sobre vuelo, conexión, equipaje, artículo, documentos o entrada al destino.","Elige el área que más se parece a lo que está ocurriendo.",official("general"),category="general")

@app.post("/api/simulation/dviajeros",response_model=SimulationResponse)
async def dviajeros():
    try:
        return simulation("dviajeros")
    except Exception:
        return SimulationResponse(ok=True,id="dviajeros",title="Práctica D’Viajeros",notice="PRÁCTICA — NO SE ENVÍA INFORMACIÓN A D’VIAJEROS",steps=[SimulationStep(id="traveler",title="Datos del viajero",fields=["given_names","surnames","birth_date","nationality"],help="Usa datos de práctica."),SimulationStep(id="trip",title="Datos del viaje",fields=["arrival_date","flight","arrival_airport"],help="Información de ejemplo."),SimulationStep(id="review",title="Revisión",fields=[],help="Revisa antes de terminar.")])

@app.post("/api/simulation/visa",response_model=SimulationResponse)
async def visa():
    try:
        return simulation("visa")
    except Exception:
        return SimulationResponse(ok=True,id="visa",title="Práctica de visa/eVisa",notice="PRÁCTICA — NO SE ENVÍA NINGUNA SOLICITUD REAL",steps=[SimulationStep(id="identity",title="Identidad",fields=["given_names","surname","birth_date","nationality"],help="Usa datos de práctica."),SimulationStep(id="passport",title="Pasaporte",fields=["passport_country","passport_number"],help="No introduzcas credenciales ni información innecesaria."),SimulationStep(id="trip",title="Viaje",fields=["purpose","arrival_date","destination"],help="Información de práctica."),SimulationStep(id="review",title="Revisión",fields=[],help="La práctica no presenta una solicitud real.")])

@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"ok":False,"error":"server_error","message":"Ocurrió un error procesando la solicitud."})

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=int(os.getenv("PORT","10000")),reload=False)
