# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v11.0.0
from __future__ import annotations
import os,secrets,time,re
from pathlib import Path
from typing import Any,Dict,List,Optional
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from schemas import *
import cuba_engine as CE
import source_registry as SR

APP_NAME="¿QUÉ QUIERES LLEVAR?"
VERSION="11.0.0"
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

app=FastAPI(title=APP_NAME,version=VERSION,description="Preparación y orientación independiente para viajes.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

if STATIC.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC)),name="static")

ACCESS:Dict[str,float]={}
ACCESS_TTL=12*60*60

def s(v:Any)->str:
    return str(v or "").strip()

def low(v:Any)->str:
    return s(v).lower()

def boolean(v:Any)->bool:
    if isinstance(v,bool):
        return v
    return low(v) in {"1","true","yes","si","sí","y","on"}

def dump(v:Any)->Dict[str,Any]:
    if hasattr(v,"model_dump"):
        return v.model_dump()
    if isinstance(v,dict):
        return dict(v)
    return {}

def call_engine(names:List[str],data:Dict[str,Any],default=None):
    for name in names:
        fn=getattr(CE,name,None)
        if callable(fn):
            try:
                value=fn(data)
                if value is not None:
                    return value
            except TypeError:
                try:
                    value=fn(**data)
                    if value is not None:
                        return value
                except Exception:
                    pass
            except Exception:
                pass
    return default

def call_source(names:List[str],*args,**kwargs):
    for name in names:
        fn=getattr(SR,name,None)
        if callable(fn):
            try:
                return fn(*args,**kwargs)
            except Exception:
                pass
    return []

def source(topic:str="official",query:str=""):
    value=call_source(
        ["get_sources","sources_for","find_sources","official_sources"],
        topic,query
    )
    if isinstance(value,dict):
        return value.get("sources") or value.get("official") or []
    return value if isinstance(value,list) else []

def source_for_item(item:str="",destination:str="",airline:str=""):
    value=call_source(
        ["sources_for_item","item_sources","get_item_sources"],
        item,destination,airline
    )
    if isinstance(value,list):
        return value
    return source("items",item)

def clean_sources(items:Any)->List[Dict[str,Any]]:
    if not isinstance(items,list):
        return []
    out=[]
    for x in items:
        if isinstance(x,dict):
            y=dict(x)
            if y.get("url") or y.get("official_url"):
                out.append(y)
    return out

def token_valid(token:str)->bool:
    token=s(token)
    if not token or token not in ACCESS:
        return False
    if time.time()>ACCESS[token]:
        ACCESS.pop(token,None)
        return False
    return True

def normalize_booking(d:Dict[str,Any])->Dict[str,Any]:
    d=dict(d)
    if not s(d.get("return_date")):
        d["return_date"]=d.get("return","")
    if not s(d.get("flight_type")):
        d["flight_type"]="commercial"
    return d

def is_cuba(destination:str)->bool:
    x=low(destination)
    return x in {"cuba","cu","república de cuba","republica de cuba","havana","la habana","habana"} or "cuba" in x

def authorities_for_item(item:str)->List[str]:
    x=low(item)
    authorities=["Aerolínea"]
    if any(k in x for k in ["líquido","liquido","liquid","aerosol","perfume","shampoo","gel"]):
        authorities.append("Seguridad del transporte")
    if any(k in x for k in ["comida","food","carne","meat","fruta","fruit","semilla","plant","planta"]):
        authorities.append("Aduana/autoridad del destino")
    if any(k in x for k in ["medic","medicine","pastilla","pill","farmaco","fármaco"]):
        authorities.append("Reglas del destino para medicamentos")
    if any(k in x for k in ["bater","power bank","litio","lithium"]):
        authorities.append("Seguridad del transporte")
    if any(k in x for k in ["animal","mascota","perro","gato","pet"]):
        authorities.append("Aerolínea y autoridad veterinaria/entrada")
    if any(k in x for k in ["arma","weapon","munición","munition","cuchillo","knife"]):
        authorities.append("Autoridad de seguridad y leyes aplicables")
    return list(dict.fromkeys(authorities))

def human_baggage_type(value:str)->str:
    x=low(value)
    if any(k in x for k in ["personal","artículo personal","articulo personal","personal item"]):
        return "Artículo personal"
    if any(k in x for k in ["carry","cabina","mano","hand"]):
        return "Equipaje de cabina"
    if any(k in x for k in ["checked","documentado","facturado","registrado","bodega"]):
        return "Equipaje documentado"
    return "Tipo de equipaje"

def baggage_explanation(data:Dict[str,Any])->Dict[str,Any]:
    item=s(data.get("item"))
    typ=human_baggage_type(data.get("type",""))
    airline=s(data.get("airline"))
    origin=s(data.get("origin"))
    destination=s(data.get("destination"))
    weight=data.get("weight")
    dimensions=s(data.get("dimensions"))
    details=[
        f"Esto es lo que indicaste: {item or 'todavía no has indicado un artículo'}.",
        f"Tipo seleccionado: {typ}.",
        "La palabra 'equipaje de mano' no significa automáticamente que cualquier maleta pueda entrar contigo al avión.",
        "La aerolínea puede establecer un límite de piezas, peso y medidas según el boleto o tarifa.",
        "Seguridad puede tener reglas diferentes a las de la aerolínea.",
        "El país de destino puede tener reglas adicionales para determinados artículos."
    ]
    if weight not in (None,""):
        details.append(f"Peso indicado por ti: {weight}. Ese dato debe compararse con el límite oficial de tu tarifa.")
    if dimensions:
        details.append(f"Medidas indicadas por ti: {dimensions}. Deben compararse con las medidas oficiales de la aerolínea.")
    if airline:
        details.append(f"Aerolínea indicada: {airline}. La regla concreta debe comprobarse en su fuente oficial.")
    if origin:
        details.append(f"Salida indicada: {origin}. Las reglas de seguridad pueden depender del aeropuerto y país de salida.")
    if destination:
        details.append(f"Destino indicado: {destination}. También puede haber reglas de entrada o aduana.")
    return {
        "title":"Entiende tu equipaje",
        "message":"Antes de decidir dónde poner una cosa, hay que saber qué tipo de equipaje tienes, qué permite tu tarifa y qué reglas aplican al artículo.",
        "status":"verify",
        "details":details,
        "authorities":["Aerolínea","Seguridad del transporte","Autoridad del destino cuando corresponda"],
        "next_action":"Busca la regla oficial de tu aerolínea y compara piezas, peso y medidas con tu boleto.",
        "sources":source("baggage",airline)
    }

@app.get("/",response_class=FileResponse)
async def home():
    f=STATIC/"index.html"
    if not f.exists():
        raise HTTPException(404,"No se encontró static/index.html")
    return FileResponse(str(f))

@app.get("/health",response_model=HealthResponse)
async def health():
    return HealthResponse(ok=True,app=APP_NAME,version=VERSION,status="ready")

@app.get("/api/config")
async def config():
    return {
        "ok":True,
        "app":APP_NAME,
        "version":VERSION,
        "price":"15.99",
        "currency":"USD",
        "stripe_ready":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID),
        "language":"es",
        "features":{
            "flight":True,
            "flight_understanding":True,
            "booking_simulation":True,
            "connections":True,
            "baggage":True,
            "baggage_rules":True,
            "item_advisor":True,
            "documents":True,
            "cuba":True,
            "dviajeros":True,
            "visa_simulation":True,
            "practice":True,
            "official_sources":True,
            "guide":True,
            "pdf":True
        }
    }

@app.get("/api/legal")
async def legal():
    return {
        "ok":True,
        "title":"Preparación independiente de viaje",
        "message":"¿QUÉ QUIERES LLEVAR? es un servicio independiente de May Roga LLC para ayudar al viajero a entender y preparar su viaje. No somos aerolínea, agencia de viajes, vendedor de boletos, gobierno, aeropuerto, consulado, autoridad migratoria ni sitio oficial de ningún trámite.",
        "details":[
            "La aplicación no reserva ni vende vuelos.",
            "Las simulaciones no realizan trámites reales.",
            "Las políticas y requisitos pueden cambiar.",
            "La confirmación final debe hacerse en la fuente oficial correspondiente.",
            "Cuando una regla dependa de una aerolínea, tarifa, ruta, aeropuerto, país o artículo concreto, la aplicación debe indicarlo."
        ]
    }

@app.post("/api/access",response_model=AccessResponse)
async def access(req:AccessRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return AccessResponse(ok=False,authorized=False,message="El acceso administrativo no está configurado en Render.")
    if secrets.compare_digest(s(req.username),ADMIN_USERNAME) and secrets.compare_digest(req.password,ADMIN_PASSWORD):
        token=secrets.token_urlsafe(32)
        ACCESS[token]=time.time()+ACCESS_TTL
        return AccessResponse(ok=True,authorized=True,token=token,message="Acceso autorizado.")
    return AccessResponse(ok=False,authorized=False,message="Usuario o contraseña incorrectos.")

@app.post("/api/checkout",response_model=CheckoutResponse)
async def checkout(req:CheckoutRequest,request:Request):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        return CheckoutResponse(ok=False,message="Stripe no está configurado todavía.")
    success=s(req.success_url) or STRIPE_SUCCESS_URL or str(request.base_url).rstrip("/")+"/?payment=success"
    cancel=s(req.cancel_url) or STRIPE_CANCEL_URL or str(request.base_url).rstrip("/")+"/?payment=cancelled"
    try:
        params={
            "mode":"payment" if STRIPE_MODE=="payment" else "subscription",
            "line_items":[{"price":STRIPE_PRICE_ID,"quantity":1}],
            "success_url":success,
            "cancel_url":cancel
        }
        session=stripe.checkout.Session.create(**params)
        return CheckoutResponse(ok=True,url=session.url,session_id=session.id,message="Sesión segura de Stripe creada.")
    except Exception as e:
        return CheckoutResponse(ok=False,message=f"No se pudo iniciar Stripe: {s(e)}")

@app.post("/api/flight",response_model=FlightResponse)
async def flight(req:FlightRequest):
    d=dump(req)
    result=call_engine(["analyze_flight","flight_analysis","understand_flight"],d)
    if isinstance(result,dict):
        result.setdefault("ok",True)
        return result
    origin=s(d.get("origin"))
    destination=s(d.get("destination"))
    airline=s(d.get("airline"))
    number=s(d.get("flight_number"))
    stops=d.get("stops","")
    segments=[]
    if isinstance(stops,list):
        route=[origin]+[s(x) for x in stops if s(x)]+[destination]
        for i in range(len(route)-1):
            segments.append({
                "number":i+1,
                "from":route[i],
                "to":route[i+1],
                "airline":airline,
                "flight_number":number if i==0 else ""
            })
        connections=max(0,len(route)-2)
    else:
        text=s(stops)
        connections=0 if not text else 1
        segments=[{"number":1,"from":origin,"to":destination,"airline":airline,"flight_number":number}]
    if not origin or not destination:
        return FlightResponse(
            ok=False,
            title="Primero dime tu ruta",
            message="Para entender tu vuelo necesito al menos saber desde dónde sales y hacia dónde vas.",
            next_action="Escribe origen y destino."
        )
    has=connections>0
    msg="Tu viaje aparece como un trayecto entre esos puntos."
    if has:
        msg="Tienes una escala o conexión indicada. Eso significa que tu viaje puede tener más de un tramo. No significa automáticamente que debas hacer todos los procedimientos posibles: depende del aeropuerto, boleto, aerolíneas y ruta."
    else:
        msg="Has indicado un viaje sin escala. Aun así, debes confirmar los detalles concretos del vuelo y del boleto."
    return FlightResponse(
        ok=True,
        title="Así se entiende tu vuelo",
        route=f"{origin} → {destination}",
        segments=segments,
        connections=connections,
        has_connection=has,
        message=msg,
        next_action="Ahora revisa equipaje, tarifa, documentos y cualquier escala.",
        sources=clean_sources(source("flight",airline))
    )

@app.post("/api/connection")
async def connection(req:ConnectionRequest):
    d=dump(req)
    result=call_engine(["connection_analysis","analyze_connection","connection_check"],d)
    if isinstance(result,dict):
        return result
    airport=s(d.get("airport"))
    terminal=s(d.get("terminal"))
    next_flight=s(d.get("next_flight"))
    details=[
        "Una escala significa que el viaje tiene otro tramo antes de llegar al destino final.",
        "Una conexión significa que necesitas pasar de un tramo de tu viaje al siguiente.",
        "Primero confirma si debes cambiar de avión.",
        "Después confirma la terminal y la puerta del siguiente vuelo.",
        "Confirma con la aerolínea qué ocurre con tu equipaje.",
        "Confirma si debes pasar nuevamente por seguridad, inmigración o aduana cuando corresponda.",
        "Si los vuelos están en boletos separados, confirma especialmente qué responsabilidad tiene cada aerolínea."
    ]
    if airport:
        details.insert(1,f"Aeropuerto indicado: {airport}.")
    if terminal:
        details.insert(2,f"Terminal indicada: {terminal}.")
    if next_flight:
        details.insert(3,f"Siguiente vuelo indicado: {next_flight}.")
    return {
        "ok":True,
        "title":"Entiende tu escala",
        "message":"No necesitas memorizar palabras técnicas. Lo importante es saber qué avión tomas después, dónde debes ir y qué debes hacer con tu equipaje.",
        "details":details,
        "questions":[
            "¿Tengo que cambiar de avión?",
            "¿Tengo que cambiar de terminal?",
            "¿Tengo que pasar seguridad otra vez?",
            "¿Tengo que recoger mi maleta?",
            "¿Dónde está la puerta de mi siguiente vuelo?"
        ],
        "next_action":"Confirma estas respuestas en la información de tu vuelo y con la aerolínea.",
        "sources":clean_sources(source("connection",airport))
    }

@app.post("/api/booking",response_model=BookingResponse)
async def booking(req:BookingRequest):
    d=normalize_booking(dump(req))
    result=call_engine(["booking_simulation","flight_search_simulation","simulate_booking"],d)
    if isinstance(result,dict):
        result["simulation"]=True
        result["real_booking"]=False
        result["payment"]=False
        return result
    origin=s(d.get("origin"))
    destination=s(d.get("destination"))
    if not origin or not destination:
        return BookingResponse(
            ok=False,
            title="Vamos a practicar una búsqueda",
            message="Escribe primero de dónde sales y a dónde quieres llegar.",
            next_action="Completa origen y destino."
        )
    return BookingResponse(
        ok=True,
        title="Búsqueda de práctica",
        simulation=True,
        real_booking=False,
        payment=False,
        message="Esto es una práctica de May Roga. No reserva, no compra y no cobra. Su objetivo es enseñarte qué información debes revisar antes de entrar al sitio real.",
        search={
            "origin":origin,
            "destination":destination,
            "departure":s(d.get("departure")),
            "return_date":s(d.get("return_date")),
            "passengers":d.get("passengers",1),
            "cabin":s(d.get("cabin")) or "Economy",
            "bags":d.get("bags",0),
            "nonstop":d.get("nonstop")
        },
        next_action="Antes de comprar, revisa tarifa, equipaje, cambios, conexiones y condiciones directamente con la fuente oficial.",
        sources=clean_sources(source("airlines"))
    )

@app.post("/api/baggage",response_model=BaggageResponse)
async def baggage(req:BaggageRequest):
    d=dump(req)
    result=call_engine(
        ["baggage_analysis","analyze_baggage","check_baggage","baggage_check"],
        d
    )
    if isinstance(result,dict):
        result.setdefault("ok",True)
        return result
    x=baggage_explanation(d)
    return BaggageResponse(
        ok=True,
        title=x["title"],
        message=x["message"],
        status=x["status"],
        details=x["details"],
        sources=clean_sources(x["sources"]),
        next_action=x["next_action"]
    )

@app.post("/api/item",response_model=ItemResponse)
async def item(req:ItemRequest):
    d=dump(req)
    result=call_engine(
        ["item_analysis","analyze_item","check_item","item_check"],
        d
    )
    if isinstance(result,dict):
        result.setdefault("ok",True)
        return result
    item=s(d.get("item"))
    airline=s(d.get("airline"))
    destination=s(d.get("destination"))
    origin=s(d.get("origin"))
    baggage=s(d.get("baggage_type"))
    if not item:
        return ItemResponse(
            ok=False,
            title="Dime qué quieres llevar",
            message="Escribe el artículo con palabras sencillas. Por ejemplo: medicamentos, comida, laptop, batería, perfume o una herramienta.",
            next_action="Escribe el artículo."
        )
    x=low(item)
    status="verify"
    category="Artículo que requiere revisión"
    details=[]
    if any(k in x for k in ["ropa","camisa","pantalon","pantalón","zapato","shoes","mochila"]):
        status="verify"
        category="Objetos personales"
        details.append("Normalmente la pregunta principal será dónde puedes colocarlo y qué límites de equipaje aplica tu tarifa.")
    elif any(k in x for k in ["medic","pastilla","medicine","pill","fármaco","farmaco"]):
        category="Medicamentos"
        details+=["No basta con saber que cabe en una maleta.","Revisa las reglas de transporte y las reglas del país de destino.","Si existen requisitos especiales para el medicamento, deben comprobarse oficialmente."]
    elif any(k in x for k in ["bateria","batería","power bank","litio","lithium"]):
        category="Batería/equipo electrónico"
        details+=["Las baterías pueden estar sujetas a reglas específicas de transporte.","No asumas que una batería puede ir en cualquier equipaje solo porque es pequeña.","Revisa la regla de la aerolínea y la seguridad aplicable."]
    elif any(k in x for k in ["perfume","liquido","líquido","shampoo","gel","aerosol"]):
        category="Líquidos/aerosoles"
        details+=["Hay que diferenciar lo que permite la aerolínea de lo que permite seguridad.","El envase, cantidad, tipo de producto y forma de transporte pueden importar.","Confirma la regla oficial antes de empacar."]
    elif any(k in x for k in ["comida","food","carne","meat","fruta","fruit","queso","cheese"]):
        category="Alimento"
        details+=["Aquí pueden existir reglas distintas para transporte aéreo y entrada al país.","La autoridad del destino puede tener reglas propias.","No confundas 'puedo subirlo al avión' con 'puedo entrar con él al país'."]
    elif any(k in x for k in ["animal","perro","gato","mascota","pet"]):
        category="Animal/mascota"
        details+=["La aerolínea puede tener condiciones propias.","El país de destino puede exigir documentación o requisitos de entrada.","La autorización debe comprobarse antes del viaje."]
    else:
        details+=["Primero identifica si el problema pertenece al equipaje, seguridad, aduana o requisitos de entrada.","Una misma cosa puede estar permitida para viajar pero tener restricciones para entrar al destino.","La respuesta debe depender de tu ruta y de la fuente oficial aplicable."]
    details.insert(0,f"Artículo que quieres llevar: {item}.")
    if baggage:
        details.append(f"Lo quieres transportar como: {human_baggage_type(baggage)}.")
    authorities=authorities_for_item(item)
    if airline:
        details.append(f"Aerolínea indicada: {airline}.")
    if destination:
        details.append(f"Destino indicado: {destination}.")
    if origin:
        details.append(f"Origen indicado: {origin}.")
    return ItemResponse(
        ok=True,
        title=f"Vamos a revisar: {item}",
        item=item,
        category=category,
        status=status,
        message="No voy a decirte simplemente 'sí' o 'no' sin saber qué regla corresponde. Primero identificamos qué autoridad controla la respuesta y después te llevamos a la fuente oficial.",
        details=details,
        authorities=authorities,
        sources=clean_sources(source_for_item(item,destination,airline)),
        next_action="Confirma la regla específica antes de empacar."
    )

@app.post("/api/cuba",response_model=CubaResponse)
async def cuba(req:CubaRequest):
    d=dump(req)
    result=call_engine(["cuba_analysis","cuba_check","analyze_cuba","cuba_entry_check"],d)
    if isinstance(result,dict):
        result.setdefault("ok",True)
        return result
    nationality=s(d.get("nationality"))
    passport=s(d.get("passport_country"))
    details=[
        "Primero identifica tu nacionalidad y el pasaporte con el que viajarás.",
        "Si tienes nacionalidad cubana o doble nacionalidad, revisa específicamente las reglas oficiales que correspondan a tu situación.",
        "Después revisa documentación de viaje y cualquier visa/eVisa que corresponda.",
        "Revisa D’Viajeros cuando sea aplicable.",
        "Revisa equipaje y artículos antes de viajar.",
        "Finalmente revisa las reglas oficiales de entrada y aduana."
    ]
    if nationality:
        details.insert(1,f"Nacionalidad indicada: {nationality}.")
    if passport:
        details.insert(2,f"Pasaporte indicado: {passport}.")
    return CubaResponse(
        ok=True,
        title="Vamos a preparar tu viaje a Cuba",
        message="Cuba requiere revisar varias partes del viaje por separado. La aplicación las organiza para que no tengas que intentar entender todo de una vez.",
        status="verify",
        details=details,
        next_action="Comienza por Documentos y después practica D’Viajeros.",
        sources=clean_sources(source("cuba"))
    )

@app.post("/api/documents",response_model=DocumentResponse)
async def documents(req:DocumentRequest):
    d=dump(req)
    result=call_engine(["document_analysis","document_check","documents_check"],d)
    if isinstance(result,dict):
        result.setdefault("ok",True)
        return result
    destination=s(d.get("destination"))
    docs=[
        {"name":"Documento de viaje/pasaporte","status":"pending","why":"Identifica con qué documento viajarás y revisa su vigencia según la fuente oficial."},
        {"name":"Requisitos de entrada del destino","status":"pending","why":"Confirma qué exige el destino para tu nacionalidad."},
        {"name":"Condiciones de la aerolínea","status":"pending","why":"Revisa las condiciones del vuelo y de tu tarifa."}
    ]
    if is_cuba(destination):
        docs += [
            {"name":"Visa/eVisa, cuando corresponda","status":"pending","why":"La necesidad depende de la nacionalidad y situación del viajero."},
            {"name":"D’Viajeros","status":"pending","why":"Practica primero y después utiliza el sitio oficial cuando corresponda."},
            {"name":"Aduana de Cuba","status":"pending","why":"Revisa artículos y declaraciones antes de viajar."}
        ]
    return DocumentResponse(
        ok=True,
        title="Tus documentos",
        message="Esta lista organiza lo que debes comprobar. No significa por sí sola que estés legalmente autorizado a viajar.",
        documents=docs,
        next_action="Abre cada documento y confirma su requisito en la fuente oficial.",
        sources=clean_sources(source("documents",destination))
    )

@app.post("/api/practice",response_model=PracticeResponse)
async def practice(req:PracticeRequest):
    d=dump(req)
    result=call_engine(["practice","practice_scenario","run_practice"],d)
    if isinstance(result,dict):
        result.setdefault("ok",True)
        result.setdefault("official_submission",False)
        return result
    scenarios=[
        {"id":"airport","title":"Estoy en el aeropuerto","question":"No sé qué hacer ahora.","steps":["Mira tu tarjeta o reserva y localiza el número del vuelo.","Busca las pantallas de salidas.","Compara vuelo, destino y puerta.","Si algo cambió, confirma con la aerolínea." ]},
        {"id":"connection","title":"Tengo una escala","question":"Bajé del avión y tengo otro vuelo.","steps":["Busca las señales de conexiones.","Confirma terminal y puerta.","Revisa si debes pasar seguridad.","Confirma qué ocurre con tu equipaje."]},
        {"id":"bag","title":"Mi maleta no aparece","question":"Llegué y no encuentro mi maleta.","steps":["Confirma que estás en la zona correcta.","Busca las pantallas de equipaje.","Busca el mostrador de la aerolínea.","Conserva tu comprobante de equipaje."]},
        {"id":"gate","title":"No encuentro mi puerta","question":"Tengo el vuelo pero no sé dónde ir.","steps":["Busca el número de vuelo en las pantallas.","Comprueba la puerta y terminal.","Sigue las señales del aeropuerto.","Si la información cambió, verifica nuevamente."]},
        {"id":"dviajeros","title":"Practicar D’Viajeros","question":"Quiero practicar antes de entrar al sitio oficial.","steps":["Prepara datos del viajero.","Prepara datos del vuelo.","Revisa la información.","Recuerda: la práctica no envía información."]},
        {"id":"baggage_item","title":"No sé dónde poner algo","question":"Tengo un artículo y no sé si va conmigo.","steps":["Identifica el artículo.","Identifica el tipo de equipaje.","Revisa aerolínea.","Revisa seguridad.","Revisa destino/aduana cuando corresponda."]}
    ]
    return PracticeResponse(
        ok=True,
        title="Practicar antes de viajar",
        mode="practice",
        official_submission=False,
        message="Estas prácticas están diseñadas para que sepas qué hacer antes de enfrentarte a la situación real.",
        next_action="Elige una situación y practica paso por paso.",
        scenarios=scenarios,
        pending=[],
        completed=[],
        progress=0,
        sources=clean_sources(source("practice"))
    )

@app.post("/api/airlines",response_model=AirlineResponse)
async def airlines(req:AirlineRequest):
    d=dump(req)
    result=call_source(["find_airlines","search_airlines","airlines_for"],s(d.get("name") or d.get("airline")))
    matches=result if isinstance(result,list) else []
    return AirlineResponse(
        ok=True,
        query=s(d.get("name") or d.get("airline")),
        matches=matches,
        message="La lista sirve para encontrar la fuente oficial de cada aerolínea. Que una aerolínea aparezca aquí no significa que opere actualmente una ruta concreta.",
        next_action="Confirma la ruta y las condiciones actuales en la fuente oficial."
    )

@app.post("/api/sources",response_model=SourceResponse)
async def sources(req:SourceRequest):
    d=dump(req)
    topic=s(d.get("topic")) or "official"
    query=s(d.get("query"))
    return SourceResponse(
        ok=True,
        topic=topic,
        sources=clean_sources(source(topic,query))
    )

@app.post("/api/solve")
async def solve(req:SolveRequest):
    d=dump(req)
    result=call_engine(["solve_question","solve","travel_question"],d)
    if isinstance(result,dict):
        result.setdefault("ok",True)
        return result
    q=low(d.get("question"))
    if not q:
        return {
            "ok":False,
            "title":"Cuéntame qué está pasando",
            "message":"Escribe tu duda como se la contarías a una persona.",
            "next_action":"Escribe tu problema."
        }
    if any(k in q for k in ["equipaje","maleta","carry","baggage","luggage"]):
        return {
            "ok":True,
            "title":"Vamos a revisar tu equipaje",
            "message":"No necesitamos adivinar. Primero identificamos qué llevas, dónde quieres ponerlo y qué aerolínea/ruta tienes.",
            "next_action":"Abre Mi equipaje."
        }
    if any(k in q for k in ["escala","conex","stop","layover"]):
        return {
            "ok":True,
            "title":"Vamos a entender tu conexión",
            "message":"Primero identifica si cambias de avión, dónde está el siguiente vuelo y qué ocurre con tu equipaje.",
            "next_action":"Abre Mi vuelo."
        }
    if any(k in q for k in ["cuba","dviajero","visa","evisa"]):
        return {
            "ok":True,
            "title":"Vamos a preparar Cuba",
            "message":"Primero revisaremos nacionalidad, pasaporte, documentación, visa/eVisa cuando corresponda, D’Viajeros, equipaje y aduana.",
            "next_action":"Abre Viajo a Cuba."
        }
    return {
        "ok":True,
        "title":"Vamos a ordenar tu duda",
        "message":"No necesitas saber el nombre técnico del problema. Cuéntame qué quieres hacer o qué te preocupa y lo convertimos en pasos.",
        "next_action":"Elige Mi vuelo, Mi equipaje, ¿Qué quiero llevar? o Viajo a Cuba."
    }

@app.post("/api/guide",response_model=GuideResponse)
async def guide(req:GuideRequest):
    d=dump(req)
    result=call_engine(["build_guide","make_guide","guide"],d)
    if isinstance(result,dict):
        result.setdefault("ok",True)
        return result
    destination=s(d.get("destination"))
    pending=[]
    if not s(d.get("origin")):
        pending.append("Completar origen")
    if not destination:
        pending.append("Completar destino")
    if not s(d.get("nationality")):
        pending.append("Revisar nacionalidad")
    if not s(d.get("passport_country")):
        pending.append("Revisar pasaporte")
    if destination:
        pending.append("Confirmar requisitos oficiales del destino")
    if is_cuba(destination):
        if not boolean(d.get("visa_checked")):
            pending.append("Verificar visa/eVisa cuando corresponda")
        if not boolean(d.get("dviajeros_done")):
            pending.append("Practicar/revisar D’Viajeros")
        if not boolean(d.get("customs_checked")):
            pending.append("Revisar aduana")
    items=d.get("items") or []
    next_action=pending[0] if pending else "Revisar nuevamente la información oficial antes de viajar."
    return GuideResponse(
        ok=True,
        title="Mi guía",
        trip={k:d.get(k) for k in [
            "origin","destination","airline","flight_number","flight_type",
            "stops","nationality","passport_country","cuban_nationality",
            "dual_citizen","purpose","arrival_date","departure_date","current_state"
        ]},
        flight={
            "airline":s(d.get("airline")),
            "flight_number":s(d.get("flight_number")),
            "stops":d.get("stops","")
        },
        documents={
            "dviajeros":boolean(d.get("dviajeros_done")),
            "visa":boolean(d.get("visa_checked")),
            "customs":boolean(d.get("customs_checked"))
        },
        items_reviewed=[
            {"name":s(x),"status":"reviewed"}
            for x in items if s(x)
        ],
        pending=pending,
        next_action=next_action,
        message="Tu guía reúne lo que has preparado y lo que todavía debes confirmar. No sustituye la fuente oficial."
    )

@app.post("/api/simulation/dviajeros",response_model=SimulationResponse)
async def simulation_dviajeros():
    result=call_engine(["dviajeros_simulation","simulate_dviajeros"],{})
    if isinstance(result,dict):
        return result
    return SimulationResponse(
        ok=True,
        id="dviajeros",
        title="Práctica D’Viajeros",
        notice="PRÁCTICA DE MAY ROGA — NO SE ENVÍA INFORMACIÓN A D’VIAJEROS",
        steps=[
            SimulationStep(id="traveler",title="Datos del viajero",fields=["given_names","surnames","birth_date","nationality"],help="Aprende qué información debes preparar."),
            SimulationStep(id="passport",title="Documento de viaje",fields=["passport_country"],help="Usa datos de práctica. No necesitas enviar información real aquí."),
            SimulationStep(id="trip",title="Datos del viaje",fields=["arrival_date","flight","arrival_airport"],help="Identifica la información que tendrás que localizar."),
            SimulationStep(id="review",title="Revisión",fields=[],help="Comprueba que entiendes cada dato antes de entrar al sitio oficial.")
        ]
    )

@app.post("/api/simulation/visa",response_model=SimulationResponse)
async def simulation_visa():
    result=call_engine(["visa_simulation","simulate_visa"],{})
    if isinstance(result,dict):
        return result
    return SimulationResponse(
        ok=True,
        id="visa",
        title="Práctica de visa/eVisa",
        notice="PRÁCTICA DE MAY ROGA — NO SE ENVÍA NINGUNA SOLICITUD REAL",
        steps=[
            SimulationStep(id="nationality",title="Nacionalidad",fields=["nationality"],help="La nacionalidad puede cambiar qué requisito debes revisar."),
            SimulationStep(id="identity",title="Identidad",fields=["given_names","surname","birth_date"],help="Aprende dónde aparecen estos datos."),
            SimulationStep(id="passport",title="Pasaporte",fields=["passport_country","passport_number"],help="Utiliza datos de práctica."),
            SimulationStep(id="trip",title="Datos del viaje",fields=["purpose","arrival_date","destination"],help="Relaciona tu viaje con el trámite que estás revisando."),
            SimulationStep(id="review",title="Revisión final",fields=[],help="La práctica no presenta ni envía una solicitud real.")
        ]
    )

@app.post("/api/pdf")
async def create_pdf(request:Request):
    data=await request.json()
    if not isinstance(data,dict):
        raise HTTPException(400,"Datos inválidos.")
    result=call_engine(["create_travel_pdf","generate_pdf","travel_pdf"],data)
    if isinstance(result,dict):
        return result
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from fastapi.responses import Response
        from io import BytesIO
        buf=BytesIO()
        doc=SimpleDocTemplate(buf,pagesize=letter,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40)
        styles=getSampleStyleSheet()
        story=[Paragraph("¿QUÉ QUIERES LLEVAR?",styles["Title"]),Paragraph("May Roga LLC · Guía de preparación de viaje",styles["Heading2"]),Spacer(1,12)]
        trip=data.get("trip") or data
        rows=[]
        labels=[
            ("Origen","origin"),
            ("Destino","destination"),
            ("Aerolínea","airline"),
            ("Vuelo","flight_number"),
            ("Tipo de vuelo","flight_type"),
            ("Nacionalidad","nationality"),
            ("Pasaporte","passport_country"),
            ("Fecha de llegada","arrival_date"),
            ("Fecha de salida","departure_date")
        ]
        for label,key in labels:
            value=s(trip.get(key))
            if value:
                rows.append([label,value])
        if rows:
            t=Table(rows,colWidths=[1.7*inch,4.5*inch])
            t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.4,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP")]))
            story.append(t)
            story.append(Spacer(1,14))
        story.append(Paragraph("IMPORTANTE",styles["Heading2"]))
        story.append(Paragraph("Esta guía es una herramienta de preparación independiente. No sustituye la información oficial de la aerolínea, aeropuerto, gobierno, autoridad migratoria o aduana. Confirma los requisitos antes de viajar.",styles["BodyText"]))
        doc.build(story)
        buf.seek(0)
        return Response(
            content=buf.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition":"attachment; filename=mi-guia-viaje.pdf"}
        )
    except Exception as e:
        return JSONResponse(status_code=500,content={"ok":False,"message":f"No se pudo generar el PDF: {s(e)}"})

@app.exception_handler(Exception)
async def errors(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "ok":False,
            "error":"server_error",
            "message":"Ocurrió un problema inesperado. Vuelve a intentarlo."
        }
    )

if __name__=="__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT","10000")),
        reload=False
    )
