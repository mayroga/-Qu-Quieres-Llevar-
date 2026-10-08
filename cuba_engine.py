from __future__ import annotations
import os,json,re,urllib.request,urllib.error
from typing import Any,Dict,List
VERSION="17.0.0"
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
GEMINI_KEY=os.getenv("GEMINI_API_KEY","").strip()
DVIAJEROS="https://dviajeros.mitrans.gob.cu/"
VISA="https://evisacuba.cu/"
GOOGLE_FLIGHTS="https://www.google.com/travel/flights"
CUBA="https://www.cubatravel.cu/"
OFFICIAL={
"dviajeros":{"name":"D’Viajeros","url":DVIAJEROS,"topic":"formulario de entrada a Cuba"},
"visa":{"name":"Visa electrónica Cuba","url":VISA,"topic":"visa electrónica"},
"google_flights":{"name":"Google Flights","url":GOOGLE_FLIGHTS,"topic":"vuelos a Cuba"},
"cuba":{"name":"Información oficial de Cuba","url":CUBA,"topic":"viaje a Cuba"}
}
AIRLINES=[
{"name":"American Airlines","url":"https://www.aa.com/","cuba":True},
{"name":"Delta Air Lines","url":"https://www.delta.com/","cuba":True},
{"name":"Southwest Airlines","url":"https://www.southwest.com/","cuba":True},
{"name":"United Airlines","url":"https://www.united.com/","cuba":True},
{"name":"JetBlue","url":"https://www.jetblue.com/","cuba":True},
{"name":"Copa Airlines","url":"https://www.copaair.com/","cuba":True},
{"name":"Viva Aerobus","url":"https://www.vivaaerobus.com/","cuba":True},
{"name":"Air Europa","url":"https://www.aireuropa.com/","cuba":True},
{"name":"Iberia","url":"https://www.iberia.com/","cuba":True},
{"name":"Turkish Airlines","url":"https://www.turkishairlines.com/","cuba":True}
]
CHARTERS=[
{"name":"Aerocuba","url":"https://www.aerocuba.com/","note":"Comprueba disponibilidad antes de comprar."},
{"name":"Havanatur","url":"https://www.havanatur.cu/","note":"Consulta las opciones de viaje disponibles."}
]
def _d(x):
    if hasattr(x,"model_dump"): return x.model_dump()
    if isinstance(x,dict): return x
    return {}
def _s(x): return str(x or "").strip()
def _low(x): return _s(x).lower()
def _source(name,url,topic="",section="",description=""):
    return {"name":name,"url":url,"topic":topic,"section":section,"description":description}
def official_url(kind):
    k=_low(kind)
    if k in OFFICIAL:return OFFICIAL[k]["url"]
    if k=="dviajeros":return DVIAJEROS
    if k=="visa":return VISA
    if k=="flights":return GOOGLE_FLIGHTS
    return CUBA
def get_sources():
    return [
        _source("D’Viajeros",DVIAJEROS,"formulario","Inicio","Formulario oficial para el viajero."),
        _source("Visa electrónica Cuba",VISA,"visa","Inicio","Sitio oficial para la visa electrónica."),
        _source("Google Flights",GOOGLE_FLIGHTS,"vuelos","Buscar vuelo","Búsqueda de vuelos."),
        _source("Información oficial de Cuba",CUBA,"viaje","Información","Información general del destino.")
    ]
def official_sources():
    return get_sources()
def answer_sources():
    return get_sources()
def get_airlines():
    return AIRLINES
def get_charters():
    return CHARTERS
def _gemini_prompt(data):
    item=_s(data.get("item"))
    desc=_s(data.get("description"))
    airline=_s(data.get("airline"))
    origin=_s(data.get("origin"))
    destination=_s(data.get("destination")) or "Cuba"
    bag=_s(data.get("baggage_type"))
    capacity=_s(data.get("capacity"))
    weight=_s(data.get("weight"))
    quantity=_s(data.get("quantity"))
    flight=_s(data.get("flight_number"))
    lang=_s(data.get("language")) or "es"
    return f"""
Eres el asistente de preparación de viaje de ¿QUÉ QUIERES LLEVAR?.
Resuelve exactamente la duda del viajero. Responde primero con una conclusión clara.
No inventes reglas. Si falta un dato necesario, pregunta SOLO por ese dato.
Si existe información oficial relevante, úsala y proporciona el enlace directo a la página o sección concreta cuando sea posible.
Si hay información específica de la aerolínea indicada, úsala.
No uses lenguaje alarmista. No des teoría legal. No conviertas la respuesta en una lista de advertencias.
El viajero necesita saber qué puede hacer.
Idioma: {lang}
Artículo: {item}
Descripción: {desc}
Aerolínea: {airline}
Origen: {origin}
Destino: {destination}
Forma de llevarlo: {bag}
Capacidad: {capacity}
Peso: {weight}
Cantidad: {quantity}
Vuelo: {flight}

Devuelve SOLO JSON válido:
{{
"decision":"yes|no|conditional|need_info",
"decision_label":"respuesta corta",
"message":"respuesta directa para el viajero",
"explanation":"explicación sencilla",
"conditions":["condiciones concretas"],
"alternatives":["alternativas útiles"],
"warnings":["solo advertencias necesarias"],
"missing_information":["datos que faltan"],
"next_action":"qué debe hacer ahora",
"official_url":"URL exacta si existe",
"official_label":"qué debe leer en esa página",
"confidence":"high|medium|low"
}}
"""
def _gemini(data):
    if not GEMINI_KEY:return None
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"
    body={
        "contents":[{"role":"user","parts":[{"text":_gemini_prompt(data)}]}],
        "tools":[{"google_search":{}}],
        "generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}
    }
    try:
        req=urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req,timeout=35) as r:
            raw=json.loads(r.read().decode("utf-8","ignore"))
        txt=""
        for c in raw.get("candidates",[]):
            for p in c.get("content",{}).get("parts",[]):
                if p.get("text"):txt+=p["text"]
        txt=txt.strip()
        if txt.startswith("```"):
            txt=re.sub(r"^```(?:json)?","",txt).strip()
            txt=re.sub(r"```$","",txt).strip()
        return json.loads(txt)
    except Exception:
        return None
def _item_fallback(data):
    item=_low(data.get("item"))
    desc=_low(data.get("description"))
    text=f"{item} {desc}"
    cap=_s(data.get("capacity"))
    if any(x in text for x in ["arma","pistola","explosivo","granada","munición","municion"]):
        return {
            "decision":"no","decision_label":"No lo lleves.",
            "message":"No lleves este artículo en el avión.",
            "explanation":"Este tipo de artículo no debe transportarse como un artículo normal de viaje.",
            "conditions":[],"alternatives":[],"warnings":[],
            "next_action":"Si necesitas una respuesta sobre un objeto concreto, dime exactamente qué es.",
            "official_url":"","official_label":"","confidence":"high"
        }
    if any(x in text for x in ["batería","bateria","power bank","powerbank","litio"]):
        if not cap:
            return {
                "decision":"need_info",
                "decision_label":"Necesito un dato.",
                "message":"Necesito saber la capacidad de la batería para decirte cómo puedes llevarla.",
                "explanation":"Busca en la etiqueta un dato que diga Wh, mAh o capacidad.",
                "conditions":["Dime exactamente lo que aparece en la etiqueta."],
                "alternatives":[],
                "warnings":[],
                "next_action":"Escribe aquí el valor de Wh o mAh que aparece en la batería.",
                "official_url":"",
                "official_label":"",
                "confidence":"high"
            }
        return {
            "decision":"conditional",
            "decision_label":"Hay que comprobar la capacidad.",
            "message":"La forma de llevar esta batería depende de su capacidad y del tipo de batería.",
            "explanation":f"Me indicaste una capacidad de {cap}. Para darte una respuesta definitiva también importa el tipo exacto de batería.",
            "conditions":["Confirma la capacidad que aparece en la etiqueta.","Indica qué dispositivo alimenta la batería."],
            "alternatives":[],
            "warnings":[],
            "next_action":"Dime qué aparece en la etiqueta y para qué dispositivo es.",
            "official_url":"",
            "official_label":"",
            "confidence":"medium"
        }
    if any(x in text for x in ["líquido","liquido","perfume","champú","shampoo","crema","gel"]):
        return {
            "decision":"conditional",
            "decision_label":"Depende de cómo lo lleves.",
            "message":"Puedo decirte cómo llevarlo, pero necesito saber qué líquido es y cuánto contiene.",
            "explanation":"La cantidad y la forma de transportarlo pueden cambiar la respuesta.",
            "conditions":["Dime qué producto es.","Dime cuántos mililitros contiene."],
            "alternatives":[],"warnings":[],
            "next_action":"Escribe el nombre del producto y los mililitros.",
            "official_url":"","official_label":"","confidence":"medium"
        }
    if any(x in text for x in ["comida","alimento","carne","queso","semilla","fruta","vegetal","comida"]):
        return {
            "decision":"conditional",
            "decision_label":"Necesito saber qué alimento es.",
            "message":"La respuesta depende del alimento y del lugar al que viajas.",
            "explanation":"Dime exactamente qué alimento quieres llevar y cómo está preparado.",
            "conditions":[],"alternatives":[],"warnings":[],
            "next_action":"Escribe el nombre exacto del alimento.",
            "official_url":"","official_label":"","confidence":"medium"
        }
    return {
        "decision":"need_info",
        "decision_label":"Necesito un poco más de información.",
        "message":"Dime exactamente qué artículo quieres llevar y cómo piensas transportarlo.",
        "explanation":"Con esos datos puedo darte una respuesta más útil.",
        "conditions":[],"alternatives":[],"warnings":[],
        "next_action":"Escribe el nombre del artículo y, si tiene etiqueta, sus datos.",
        "official_url":"","official_label":"","confidence":"low"
    }
def item_analysis(request):
    data=_d(request)
    result=_gemini(data)
    used=result is not None
    if not result:result=_item_fallback(data)
    result=dict(result)
    result["gemini_used"]=used
    result["gemini_error"]=bool(GEMINI_KEY and not used)
    result["version"]=VERSION
    if not result.get("sources"):result["sources"]=[]
    if result.get("official_url"):
        result["sources"].append(_source(
            result.get("official_label") or "Regla oficial",
            result["official_url"],
            "respuesta"
        ))
    result.setdefault("decision","need_info")
    result.setdefault("decision_label","Necesito información.")
    result.setdefault("message","Necesito un dato para darte una respuesta.")
    result.setdefault("explanation","")
    result.setdefault("conditions",[])
    result.setdefault("alternatives",[])
    result.setdefault("warnings",[])
    result.setdefault("next_action","")
    result.setdefault("confidence","medium")
    return result
def baggage_rules(request):
    d=_d(request)
    airline=_s(d.get("airline"))
    weight=d.get("weight")
    dimensions=_s(d.get("dimensions"))
    pieces=d.get("pieces")
    kind=_low(d.get("baggage_type") or d.get("type"))
    names={
        "carry_on":"Lo que llevas contigo",
        "checked":"La maleta que entregas",
        "personal":"El artículo pequeño que llevas contigo"
    }
    name=names.get(kind,"Tu equipaje")
    missing=[]
    if weight is None:missing.append("peso")
    if not dimensions:missing.append("medidas")
    if pieces is None:missing.append("cantidad")
    msg=f"Para saber exactamente qué permite tu boleto con {airline or 'la aerolínea'}, necesito revisar peso, medidas y cantidad."
    if not missing:
        msg="Ya tenemos los datos principales de tu equipaje. Ahora hay que compararlos con las condiciones de tu boleto."
    return {
        "status":"need_info" if missing else "ready",
        "type":kind,
        "type_name":name,
        "airline":airline,
        "origin":_s(d.get("origin")),
        "destination":_s(d.get("destination")),
        "fare":_s(d.get("fare")),
        "cabin":_s(d.get("cabin")),
        "message":msg,
        "do_not_assume":[f"Falta indicar {x}." for x in missing],
        "conditions":[],
        "next_action":"Completa los datos que faltan." if missing else "Revisa la respuesta de tu aerolínea.",
        "sources":[],
        "version":VERSION
    }
def _sim_step(n,title,text,link="",image=""):
    return {
        "number":n,
        "title":title,
        "text":text,
        "reference_image":image,
        "reference_type":"visual-guide" if image else "",
        "official_step":text,
        "link":link
    }
def dviajeros_simulation(request):
    lang=_s(_d(request).get("language")) or "es"
    if lang=="en":
        steps=[
            _sim_step(1,"Open the official form","Open the official D’Viajeros website.",DVIAJEROS),
            _sim_step(2,"Start","Choose the option to complete the traveler information."),
            _sim_step(3,"Enter your information","Use your passport and travel information exactly as shown."),
            _sim_step(4,"Review","Check the information before finishing."),
            _sim_step(5,"Finish","Complete the official process and keep the result."),
            _sim_step(6,"At the airport","Have the result available on your phone when you need it."),
            _sim_step(7,"If you need help","Return to the official form and follow the instructions shown there.",DVIAJEROS)
        ]
        return {"title":"D’Viajeros","message":"Visual practice before using the official form.","steps":steps,"official_url":DVIAJEROS,"official_label":"Open D’Viajeros","airport_steps":steps[5:],"reference_images":[],"language":"en","version":VERSION}
    steps=[
        _sim_step(1,"Abre el formulario","Abre el sitio oficial de D’Viajeros.",DVIAJEROS),
        _sim_step(2,"Comienza","Busca la opción para completar la información del viajero."),
        _sim_step(3,"Pon tus datos","Usa tu pasaporte y tus datos del viaje exactamente como aparecen."),
        _sim_step(4,"Revisa","Mira nuevamente los datos antes de terminar."),
        _sim_step(5,"Termina","Completa el proceso oficial y guarda el resultado."),
        _sim_step(6,"En el aeropuerto","Ten el resultado disponible en tu teléfono cuando lo necesites."),
        _sim_step(7,"Si necesitas ayuda","Vuelve al formulario oficial y sigue las instrucciones que aparecen allí.",DVIAJEROS)
    ]
    return {"title":"D’Viajeros","message":"Clase visual antes de entrar al formulario oficial.","steps":steps,"official_url":DVIAJEROS,"official_label":"Abrir D’Viajeros","airport_steps":steps[5:],"reference_images":[],"language":"es","version":VERSION}
def visa_simulation(request):
    d=_d(request)
    lang=_s(d.get("language")) or "es"
    if lang=="en":
        texts=[
            ("1","Open the official website","Open the official electronic visa website.",VISA),
            ("2","Start","Choose the option to begin the electronic visa process.",""),
            ("3","Complete the information","Use the information shown on your passport.",""),
            ("4","Review and finish","Check everything before completing the official process.",""),
            ("5","Keep your result","Save the confirmation or document you receive.",""),
            ("6","At the airport","Keep the information available with your travel documents.","")
        ]
    else:
        texts=[
            ("1","Abre el sitio oficial","Abre el sitio oficial de la visa electrónica.",VISA),
            ("2","Comienza","Busca la opción para comenzar el proceso de visa.",""),
            ("3","Completa la información","Usa exactamente los datos que aparecen en tu pasaporte.",""),
            ("4","Revisa y termina","Comprueba los datos antes de terminar el proceso oficial.",""),
            ("5","Guarda el resultado","Guarda la confirmación o documento que recibas.",""),
            ("6","En el aeropuerto","Ten esa información junto con tus documentos de viaje.","")
        ]
    steps=[_sim_step(int(n),t,x,l) for n,t,x,l in texts]
    return {
        "title":"Visa electrónica",
        "message":"Clase visual antes de utilizar el sitio oficial.",
        "steps":steps,
        "official_url":VISA,
        "official_label":"Abrir visa electrónica",
        "airport_steps":steps[-1:],
        "reference_images":[],
        "language":lang,
        "version":VERSION
    }
def analyze_flight(request):
    d=_d(request)
    airline=_s(d.get("airline"))
    origin=_s(d.get("origin"))
    destination=_s(d.get("destination")) or "Cuba"
    return {
        "ok":True,
        "message":"Puedes comenzar buscando el vuelo y después revisar la aerolínea, el boleto y el equipaje antes de comprar.",
        "search_url":GOOGLE_FLIGHTS,
        "search_label":"Buscar vuelos a Cuba",
        "airline":airline,
        "origin":origin,
        "destination":destination,
        "official_airline":next((x for x in AIRLINES if _low(x["name"])==_low(airline)),None),
        "sources":[_source("Google Flights",GOOGLE_FLIGHTS,"vuelos","Buscar vuelo")],
        "version":VERSION
    }
def booking_simulation(request):
    d=_d(request)
    return {
        "ok":True,
        "message":"Esta práctica te enseña el recorrido. No compra, paga ni reserva un vuelo.",
        "steps":[
            _sim_step(1,"Busca","Elige origen, destino y fecha."),
            _sim_step(2,"Compara","Mira los vuelos y el horario que te conviene."),
            _sim_step(3,"Revisa","Comprueba aerolínea, boleto y equipaje."),
            _sim_step(4,"Continúa","Para comprar, pasa al sitio de la aerolínea.")
        ],
        "official_url":GOOGLE_FLIGHTS,
        "version":VERSION
    }
def connection_analysis(request):
    return {
        "ok":True,
        "message":"Si tienes una conexión, revisa el tiempo entre vuelos y las instrucciones que aparecen en tu boleto.",
        "next_action":"Si me das los vuelos y horarios, puedo ayudarte a entender la conexión.",
        "version":VERSION
    }
def cuba_check(request):
    d=_d(request)
    return {
        "ok":True,
        "message":"Para preparar tu entrada a Cuba, revisa D’Viajeros, la visa que corresponda y tus documentos de viaje.",
        "dviajeros":DVIAJEROS,
        "visa":VISA,
        "version":VERSION
    }
def cuba_entry(request):
    return cuba_check(request)
def document_analysis(request):
    return {
        "ok":True,
        "message":"Revisa tus documentos de viaje y compara los datos con los que aparecen en tu boleto y formularios.",
        "next_action":"Si tienes una duda concreta, escribe exactamente qué documento quieres revisar.",
        "version":VERSION
    }
def practice_scenario(request):
    d=_d(request)
    return {
        "ok":True,
        "message":"Esta es una práctica. No es un trámite oficial y no envía información a ninguna autoridad.",
        "scenario":_s(d.get("scenario")),
        "step":d.get("step",1),
        "version":VERSION
    }
def solve(data):
    d=_d(data)
    return item_analysis(d) if d.get("item") else {
        "ok":True,
        "message":"Dime qué necesitas resolver.",
        "next_action":"Escribe tu duda con tus propias palabras.",
        "version":VERSION
    }
def guide(data):
    d=_d(data)
    topic=_low(d.get("topic"))
    if "visa" in topic:return visa_simulation(d)
    if "viajero" in topic or "dviajero" in topic:return dviajeros_simulation(d)
    if "vuelo" in topic:return booking_simulation(d)
    if "equipaje" in topic:return baggage_rules(d)
    return {
        "ok":True,
        "message":"Dime si necesitas ayuda con D’Viajeros, visa, vuelos, equipaje o algo que quieras llevar.",
        "version":VERSION
    }
def create_pdf(request):
    return {
        "ok":False,
        "message":"El PDF es opcional. La creación del archivo se realiza desde la función de PDF cuando el cliente pulsa para sacarlo.",
        "version":VERSION
    }
def import_pdf(request):
    return {"ok":False,"message":"La recuperación por PDF no forma parte del recorrido principal.","version":VERSION}
def export_data(data):
    return {"ok":True,"data":_d(data),"version":VERSION}
def add_source(data):
    return {"ok":True,"source":_d(data)}
def add_airline(data):
    return {"ok":True,"airline":_d(data)}
def health():
    return {
        "version":VERSION,
        "gemini_configured":bool(GEMINI_KEY),
        "gemini_model":GEMINI_MODEL,
        "dviajeros":DVIAJEROS,
        "visa":VISA
    }
