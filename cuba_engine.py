# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v10.0.0
from __future__ import annotations
from typing import Any,Dict,List,Optional
from datetime import date
import re
from source_registry import (
    get_source,get_sources,topic,simulation,item_lookup,
    source_for_question,legal_notice,AIRLINE_GROUPS
)

VERSION="10.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
OWNER="May Roga LLC"

def _s(v:Any)->str:
    return str(v or "").strip()

def _low(v:Any)->str:
    return _s(v).lower()

def _norm(v:Any)->str:
    x=_low(v)
    repl={"á":"a","é":"e","í":"i","ó":"o","ú":"u","ü":"u","ñ":"n"}
    for a,b in repl.items():x=x.replace(a,b)
    return " ".join(x.split())

def _yes(v:Any)->bool:
    return _norm(v) in {"si","sí","yes","true","1","y"}

def _source(ids:List[str])->List[Dict]:
    return [x for x in get_sources(ids) if x]

def _unique(items:List[str])->List[str]:
    out=[]
    for x in items:
        if x and x not in out:out.append(x)
    return out

def _result(title:str,message:str,next_action:str="",sources:Optional[List[str]]=None,status:str="verify",details:Optional[List[str]]=None)->Dict:
    ids=_unique(sources or [])
    return {
        "title":title,
        "message":message,
        "status":status,
        "details":details or [],
        "next_action":next_action,
        "sources":_source(ids)
    }

def app_identity()->Dict:
    return {
        "name":APP_NAME,
        "owner":OWNER,
        "version":VERSION,
        "promise":"Cuando tengas una duda antes o durante tu viaje, te ayudamos a entender qué está pasando, qué debes comprobar y dónde confirmarlo oficialmente.",
        "legal":legal_notice()
    }

def classify_problem(text:str)->Dict:
    q=_norm(text)
    if not q:
        return {"category":"unknown","title":"¿Qué está pasando?","message":"Cuéntame qué necesitas resolver.","next_action":"Escribe tu duda."}
    rules=[
        ("dviajeros",["dviajero","d viajeros","formulario viajero"]),
        ("visa",["visa","evisa","visado"]),
        ("baggage",["maleta","equipaje","carry on","equipaje de mano","maleta facturada"]),
        ("connection",["escala","conexion","cambiar avion","cambio de avion","stop","layover","conectar"]),
        ("flight",["vuelo","aerolinea","aerolínea","flight","boarding","puerta"]),
        ("items",["llevar","puedo llevar","puedo entrar con","articulo","artículo"]),
        ("customs",["aduana","importar","mercancia","mercancía"]),
        ("documents",["documento","pasaporte","papeles","requisito"]),
        ("cuba",["cuba","cubano","cubana","habana","varadero"]),
        ("airport",["aeropuerto","terminal","seguridad","checkpoint"]),
    ]
    for cat,words in rules:
        if any(w in q for w in words):
            return {"category":cat,"title":topic(cat if cat in ["baggage","connection","flight","items","documents","cuba"] else "official")["title"],"message":"La pregunta parece estar relacionada con "+cat+".","next_action":"Abrir la sección correspondiente."}
    return {"category":"general","title":"Resolver mi duda","message":"No encontré una categoría suficientemente específica. La aplicación no inventará una respuesta.","next_action":"Consulta la fuente oficial correspondiente."}

def cuba_check(data:Dict[str,Any])->Dict:
    nationality=_s(data.get("nationality"))
    cuban=_yes(data.get("cuban_nationality")) or _yes(data.get("dual_citizen"))
    passport=_s(data.get("passport_country"))
    travel_from=_s(data.get("origin"))
    purpose=_s(data.get("purpose"))
    flight_type=_low(data.get("flight_type"))
    result=[]
    pending=[]
    if cuban:
        result.append("Declaraste nacionalidad cubana o doble nacionalidad.")
        pending.append("Revisar la documentación aplicable a ciudadanos cubanos antes del viaje.")
    else:
        result.append("No declaraste nacionalidad cubana.")
        pending.append("Comprobar el requisito de entrada aplicable a tu nacionalidad.")
    if nationality:result.append(f"Nacionalidad indicada: {nationality}.")
    else:pending.append("Indicar nacionalidad para orientar la revisión.")
    if passport:result.append(f"Documento emitido por: {passport}.")
    else:pending.append("Indicar el país que emitió tu pasaporte.")
    if purpose:result.append(f"Motivo indicado: {purpose}.")
    else:pending.append("Indicar el motivo del viaje si deseas revisar requisitos relacionados.")
    if travel_from:result.append(f"Origen indicado: {travel_from}.")
    else:pending.append("Indicar desde dónde viajas.")
    if flight_type in {"charter","commercial","comercial"}:
        result.append("Tipo de vuelo indicado: "+("charter" if flight_type=="charter" else "comercial")+".")
    else:
        pending.append("Confirmar si el vuelo es comercial o charter cuando esa diferencia sea relevante.")
    return _result(
        "Preparación para Cuba",
        "Esta revisión organiza lo que debes comprobar; no certifica que puedas entrar a Cuba ni sustituye a las autoridades.",
        "Revisar documentos, visa/eVisa y D'Viajeros.",
        ["dviajeros","evisa_cuba","minrex_cuba","aduana_cuba","ofac_cuba","state_cuba"],
        "pending" if pending else "verify",
        result+["PENDIENTE: "+x for x in pending]
    )

def cuba_entry_path(data:Dict[str,Any])->Dict:
    cuban=_yes(data.get("cuban_nationality")) or _yes(data.get("dual_citizen"))
    nationality=_s(data.get("nationality"))
    passport=_s(data.get("passport_country"))
    if cuban:
        headline="Revisión especial por nacionalidad cubana"
        steps=[
            "Revisar qué documentación cubana corresponde utilizar.",
            "Comprobar directamente las instrucciones consulares o migratorias vigentes.",
            "Revisar D'Viajeros.",
            "Revisar Aduana si llevas artículos o mercancías."
        ]
    else:
        headline="Revisión de entrada según nacionalidad"
        steps=[
            "Identificar nacionalidad y pasaporte.",
            "Comprobar el mecanismo de visa o autorización que corresponda.",
            "Revisar D'Viajeros.",
            "Revisar Aduana y artículos que llevarás."
        ]
    return {
        "title":headline,
        "nationality":nationality,
        "passport_country":passport,
        "steps":steps,
        "sources":_source(["evisa_cuba","dviajeros","minrex_cuba","aduana_cuba"])
    }

def visa_check(data:Dict[str,Any])->Dict:
    nationality=_s(data.get("nationality"))
    passport_country=_s(data.get("passport_country"))
    purpose=_s(data.get("purpose"))
    if not nationality:
        return _result("Visa / eVisa","Necesitamos conocer tu nacionalidad para saber qué debes comprobar.","Indica tu nacionalidad.",["evisa_cuba","minrex_cuba"],"pending")
    details=[
        f"Nacionalidad indicada: {nationality}.",
        "País emisor del pasaporte: "+(passport_country or "no indicado")+".",
        "Motivo del viaje: "+(purpose or "no indicado")+".",
        "La aplicación no determinará automáticamente que una persona está autorizada a entrar.",
        "La comprobación final debe hacerse con la autoridad o plataforma oficial."
    ]
    return _result(
        "Revisión de visa / eVisa",
        "La aplicación puede ayudarte a preparar la información y practicar el proceso, pero no emite visas ni determina elegibilidad.",
        "Abrir la práctica de eVisa y después comprobar el proceso real.",
        ["evisa_cuba","minrex_cuba"],
        "verify",
        details
    )

def dviajeros_check(data:Dict[str,Any])->Dict:
    fields=[
        ("given_names","Nombres"),
        ("surnames","Apellidos"),
        ("birth_date","Fecha de nacimiento"),
        ("nationality","Nacionalidad"),
        ("passport_number","Número de pasaporte"),
        ("arrival_date","Fecha de llegada"),
        ("flight","Vuelo"),
        ("arrival_airport","Aeropuerto de llegada")
    ]
    completed=[]
    pending=[]
    for key,label in fields:
        if _s(data.get(key)):completed.append(label)
        else:pending.append(label)
    return {
        "title":"Preparación D'Viajeros",
        "mode":"simulation",
        "official_submission":False,
        "completed":completed,
        "pending":pending,
        "progress":round(len(completed)/len(fields)*100),
        "message":"Esta preparación no envía información a D'Viajeros.",
        "next_action":"Completa la práctica y utiliza el sitio oficial para el proceso real.",
        "sources":_source(["dviajeros"])
    }

def visa_simulation(data:Dict)->Dict:
    fields=[
        ("nationality","Nacionalidad"),
        ("passport_number","Número de pasaporte"),
        ("surname","Apellido"),
        ("given_names","Nombres"),
        ("birth_date","Fecha de nacimiento"),
        ("sex","Sexo"),
        ("email","Correo electrónico"),
        ("phone","Teléfono")
    ]
    completed=[]
    pending=[]
    for key,label in fields:
        if _s(data.get(key)):completed.append(label)
        else:pending.append(label)
    return {
        "title":"Práctica eVisa Cuba",
        "mode":"simulation",
        "official_submission":False,
        "completed":completed,
        "pending":pending,
        "progress":round(len(completed)/len(fields)*100),
        "message":"Esto es una simulación. No se envían datos a eVisa-Cuba.",
        "next_action":"Revisar la información en el sitio oficial antes de iniciar el trámite real.",
        "sources":_source(["evisa_cuba","minrex_cuba"])
    }

def flight_segments(data:Dict[str,Any])->Dict:
    origin=_s(data.get("origin"))
    destination=_s(data.get("destination"))
    stops=data.get("stops") or []
    if isinstance(stops,str):
        stops=[x.strip() for x in stops.split(",") if x.strip()]
    if not origin or not destination:
        return _result("Mi vuelo","Necesito origen y destino para organizar el itinerario.","Indica origen y destino.",["iata"],"pending")
    points=[origin]+stops+[destination]
    segments=[]
    for i in range(len(points)-1):
        segments.append({
            "number":i+1,
            "from":points[i],
            "to":points[i+1],
            "type":"first" if i==0 else ("last" if i==len(points)-2 else "connection")
        })
    return {
        "title":"Tu itinerario",
        "route":" → ".join(points),
        "segments":segments,
        "connections":max(0,len(points)-2),
        "has_connection":len(points)>2,
        "message":"Esta organización ayuda a entender los segmentos. No confirma horarios, puertas ni procedimientos del aeropuerto.",
        "next_action":"Comprobar el itinerario real con la aerolínea.",
        "sources":_source(["iata"])
    }

def connection_check(data:Dict[str,Any])->Dict:
    same_ticket=data.get("same_ticket")
    baggage=data.get("baggage")
    airport=_s(data.get("airport"))
    country_change=_yes(data.get("country_change"))
    details=[]
    if airport:details.append("Aeropuerto de conexión: "+airport+".")
    details.append("No asumir que una conexión requiere o no requiere recoger equipaje; comprobar las instrucciones de la aerolínea.")
    details.append("No asumir que se puede permanecer en la misma zona; los controles dependen del aeropuerto y del itinerario.")
    if country_change:details.append("Existe un cambio de país indicado; revisar inmigración, seguridad y requisitos de tránsito aplicables.")
    if same_ticket is not None:details.append("Billetes/reserva: "+("misma reserva indicada." if _yes(same_ticket) else "reservas separadas indicadas.")+"")
    if baggage is not None:details.append("Equipaje: "+("se indicó que debe revisarse la recogida." if _yes(baggage) else "no se indicó recogida.") )
    return _result(
        "Entender mi conexión",
        "Una escala puede implicar diferentes pasos según aeropuerto, país, aerolínea, tipo de boleto y equipaje.",
        "Comprueba las instrucciones del siguiente segmento en tu reserva y con la aerolínea.",
        ["iata","tsa","cbp_travel"],
        "verify",
        details
    )

def airport_now(data:Dict[str,Any])->Dict:
    state=_norm(data.get("state"))
    answers={
        "antes":"Antes de salir: revisa documentos, vuelo, equipaje y requisitos de entrada.",
        "aeropuerto":"En el aeropuerto: comprueba check-in, equipaje, seguridad y puerta.",
        "escala":"En la escala: localiza el siguiente vuelo, puerta y posibles controles.",
        "conexion":"En la conexión: confirma si debes cambiar de terminal, pasar seguridad o recoger equipaje.",
        "cuba":"Al llegar a Cuba: sigue las indicaciones oficiales de inmigración, equipaje y aduana.",
        "regreso":"Para regresar: comprueba nuevamente vuelo, equipaje, documentos y requisitos del siguiente destino."
    }
    msg=answers.get(state,"Indica si estás antes de salir, en el aeropuerto, en una escala, llegando a Cuba o regresando.")
    return {
        "title":"¿Qué hago ahora?",
        "state":state or "unknown",
        "message":msg,
        "next_action":"Busca el estado exacto de tu viaje y revisa la fuente correspondiente.",
        "sources":_source(["iata","tsa","cbp_travel","dviajeros","aduana_cuba"])
    }

def baggage_check(data:Dict[str,Any])->Dict:
    kind=_norm(data.get("type"))
    item=_s(data.get("item"))
    airline=_s(data.get("airline"))
    details=[]
    if kind in {"mano","cabina","carry on","carry-on"}:
        details.append("Equipaje de cabina: comprobar dimensiones, peso y cantidad permitida por la aerolínea.")
    elif kind in {"facturado","registrado","checked"}:
        details.append("Equipaje facturado: comprobar cantidad, peso, dimensiones y cargos aplicables con la aerolínea.")
    elif kind in {"personal","articulo personal","artículo personal"}:
        details.append("Artículo personal: comprobar las dimensiones y condiciones de la aerolínea.")
    else:
        details.append("Selecciona el tipo de equipaje para una revisión más específica.")
    if item:
        details.append("Artículo indicado: "+item+".")
        details.append("Además de la aerolínea, comprueba seguridad aeroportuaria y reglas del destino cuando corresponda.")
    if airline:details.append("Aerolínea indicada: "+airline+".")
    return _result(
        "Revisión de equipaje",
        "Las condiciones de la aerolínea y las reglas de seguridad no son necesariamente la misma cosa.",
        "Revisar la política de equipaje de tu aerolínea y, para artículos restringidos, la autoridad de seguridad.",
        ["tsa","iata"],
        "verify",
        details
    )

def item_check(item:str,context:Optional[Dict[str,Any]]=None)->Dict:
    context=context or {}
    base=item_lookup(item)
    details=[base["message"]]
    authorities=[]
    for a in base.get("authorities",[]):
        authorities.append(a)
    if context.get("airline"):
        details.append("Aerolínea indicada: "+_s(context["airline"])+".")
    if context.get("destination"):
        details.append("Destino indicado: "+_s(context["destination"])+".")
    details.append("No se presenta este resultado como autorización definitiva.")
    return {
        "title":"¿Qué quiero llevar?",
        "item":item,
        "category":base.get("category"),
        "status":base.get("status"),
        "message":base.get("message"),
        "details":details,
        "authorities":authorities,
        "sources":base.get("sources",[]),
        "next_action":"Revisar la fuente oficial correspondiente antes de viajar."
    }

def travel_documents(data:Dict[str,Any])->Dict:
    cuban=_yes(data.get("cuban_nationality")) or _yes(data.get("dual_citizen"))
    destination=_norm(data.get("destination"))
    docs=[
        {"id":"passport","name":"Pasaporte/documento de viaje","status":"review"},
        {"id":"entry","name":"Requisito de entrada","status":"review"},
        {"id":"airline","name":"Condiciones de la aerolínea","status":"review"},
        {"id":"baggage","name":"Equipaje","status":"review"}
    ]
    sources=["iata","state_cuba"]
    if "cuba" in destination or "cuba" in _norm(data.get("country")):
        docs += [
            {"id":"dviajeros","name":"D'Viajeros","status":"review"},
            {"id":"visa","name":"Visa / eVisa si corresponde","status":"review"},
            {"id":"customs","name":"Aduana","status":"review"}
        ]
        sources+=["dviajeros","evisa_cuba","aduana_cuba","minrex_cuba"]
        if cuban:
            docs.append({"id":"cuban_status","name":"Documentación relacionada con nacionalidad cubana","status":"review"})
    return {
        "title":"Mis documentos",
        "documents":docs,
        "message":"Esta lista organiza lo que debes revisar. No certifica que un documento sea válido o suficiente.",
        "next_action":"Completa cada revisión con la fuente oficial correspondiente.",
        "sources":_source(_unique(sources))
    }

def guide(data:Dict[str,Any])->Dict:
    flight=flight_segments(data.get("flight") or data)
    documents=travel_documents(data)
    items=data.get("items") or []
    if isinstance(items,str):items=[x.strip() for x in items.split(",") if x.strip()]
    reviewed_items=[item_check(x,data) for x in items[:20]]
    cuba="cuba" in _norm(data.get("destination")) or _yes(data.get("travel_to_cuba"))
    pending=[]
    if not _s(data.get("origin")):pending.append("Indicar origen")
    if not _s(data.get("destination")):pending.append("Indicar destino")
    if cuba:
        if not _s(data.get("nationality")):pending.append("Revisar nacionalidad")
        if not _yes(data.get("dviajeros_done")):pending.append("Revisar D'Viajeros")
        if not _yes(data.get("visa_checked")):pending.append("Revisar visa/eVisa si corresponde")
    return {
        "title":"Mi guía",
        "trip":{
            "origin":_s(data.get("origin")),
            "destination":_s(data.get("destination")),
            "airline":_s(data.get("airline")),
            "flight_number":_s(data.get("flight_number")),
            "flight_type":_s(data.get("flight_type")),
            "nationality":_s(data.get("nationality")),
            "cuban_nationality":cuba and (_yes(data.get("cuban_nationality")) or _yes(data.get("dual_citizen"))),
            "items":items
        },
        "flight":flight,
        "documents":documents,
        "items_reviewed":reviewed_items,
        "pending":pending,
        "next_action":pending[0] if pending else ("Practicar la parte del viaje que todavía genere dudas." if cuba else "Revisar tu itinerario y las condiciones oficiales."),
        "message":"Tu guía reúne tu preparación. No sustituye documentos, reservas, autorizaciones ni instrucciones oficiales."
    }

def practice(scenario:str,data:Optional[Dict[str,Any]]=None)->Dict:
    data=data or {}
    q=_norm(scenario)
    if "dviajero" in q:return dviajeros_check(data)
    if "visa" in q or "evisa" in q:return visa_simulation(data)
    if "escala" in q or "conexion" in q:return connection_check(data)
    if "aeropuerto" in q:return airport_now(data)
    if "equipaje" in q:return baggage_check(data)
    if "llevar" in q:return item_check(_s(data.get("item")),data)
    return {
        "title":"Práctica de viaje",
        "message":"Elige una situación para practicar.",
        "scenarios":[
            {"id":"airport","title":"Estoy en el aeropuerto"},
            {"id":"connection","title":"Tengo una escala"},
            {"id":"baggage","title":"Mi equipaje"},
            {"id":"dviajeros","title":"Practicar D'Viajeros"},
            {"id":"visa","title":"Practicar eVisa Cuba"}
        ]
    }

def booking_simulation(data:Dict[str,Any])->Dict:
    origin=_s(data.get("origin"))
    destination=_s(data.get("destination"))
    departure=_s(data.get("departure"))
    return {
        "title":"Práctica de búsqueda de vuelo",
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "message":"Esta simulación enseña cómo organizar una búsqueda; no muestra disponibilidad ni tarifas reales.",
        "search":{
            "origin":origin,
            "destination":destination,
            "departure":departure,
            "return":_s(data.get("return")),
            "passengers":data.get("passengers",1),
            "cabin":_s(data.get("cabin")) or "economy"
        },
        "next_action":"Para comprar, comprobar disponibilidad, precio, equipaje y condiciones directamente con el proveedor.",
        "sources":_source(["iata"])
    }

def airline_lookup(name:str)->Dict:
    q=_norm(name)
    matches=[]
    for sid in AIRLINE_GROUPS["commercial_us"]+AIRLINE_GROUPS["commercial_international"]+AIRLINE_GROUPS["charter"]:
        src=get_source(sid)
        if not src:continue
        hay=_norm(src["name"]+" "+src["id"])
        if q in hay or any(part and part in hay for part in q.split()):
            matches.append(src)
    return {
        "query":name,
        "matches":matches,
        "message":"La inclusión de una aerolínea no confirma que opere actualmente la ruta que buscas.",
        "next_action":"Consultar el sitio oficial para comprobar ruta, fecha y disponibilidad."
    }

def official_handoff(topic_id:str="official")->Dict:
    t=topic(topic_id)
    return {
        "title":t["title"],
        "message":t["description"],
        "fallback":t["fallback"],
        "sources":t.get("source_data",[])
    }

def solve(question:str,data:Optional[Dict[str,Any]]=None)->Dict:
    data=data or {}
    c=classify_problem(question)
    cat=c["category"]
    if cat=="dviajeros":return dviajeros_check(data)
    if cat=="visa":return visa_check(data)
    if cat=="baggage":return baggage_check(data)
    if cat=="connection":return connection_check(data)
    if cat=="flight":return flight_segments(data)
    if cat=="items":return item_check(_s(data.get("item")) or question,data)
    if cat=="documents":return travel_documents(data)
    if cat=="cuba":return cuba_check(data)
    if cat=="airport":return airport_now(data)
    return {
        "classification":c,
        "title":"Vamos a resolverlo",
        "message":"La aplicación necesita identificar qué parte del viaje está causando la duda.",
        "next_action":"Selecciona vuelo, equipaje, artículo, Cuba, documentos o práctica."
    }

def validate_trip(data:Dict[str,Any])->Dict:
    required=["origin","destination"]
    missing=[x for x in required if not _s(data.get(x))]
    warnings=[]
    if not _s(data.get("airline")):warnings.append("No se indicó aerolínea.")
    if not _s(data.get("flight_number")):warnings.append("No se indicó número de vuelo.")
    if not _s(data.get("nationality")):warnings.append("No se indicó nacionalidad.")
    cuba="cuba" in _norm(data.get("destination"))
    if cuba and not _s(data.get("passport_country")):warnings.append("Para una preparación de Cuba conviene indicar el país que emitió el pasaporte.")
    return {
        "valid":not missing,
        "missing":missing,
        "warnings":warnings,
        "cuba":cuba,
        "next_action":"Completa los datos faltantes antes de construir una guía personalizada." if missing else "Puedes continuar con la preparación."
    }

def export_trip_state(data:Dict)->Dict:
    return {
        "version":VERSION,
        "created_for":"local_trip_guide",
        "data":{
            "origin":_s(data.get("origin")),
            "destination":_s(data.get("destination")),
            "airline":_s(data.get("airline")),
            "flight_number":_s(data.get("flight_number")),
            "flight_type":_s(data.get("flight_type")),
            "nationality":_s(data.get("nationality")),
            "passport_country":_s(data.get("passport_country")),
            "cuban_nationality":bool(data.get("cuban_nationality")),
            "dual_citizen":bool(data.get("dual_citizen")),
            "items":data.get("items") or []
        },
        "notice":"La guía es una herramienta de preparación y no constituye una autorización de viaje."
    }

def engine_status()->Dict:
    return {
        "engine":"cuba_engine",
        "version":VERSION,
        "status":"ready",
        "modules":[
            "cuba_entry",
            "visa_evisa",
            "dviajeros",
            "flight_itinerary",
            "connections",
            "airport_situations",
            "baggage",
            "item_check",
            "documents",
            "booking_simulation",
            "practice",
            "personal_guide",
            "official_handoff"
        ]
    }

class TravelEngine:
    def solve(self,question,data=None):return solve(question,data)
    def cuba(self,data):return cuba_check(data)
    def visa(self,data):return visa_check(data)
    def dviajeros(self,data):return dviajeros_check(data)
    def flight(self,data):return flight_segments(data)
    def connection(self,data):return connection_check(data)
    def baggage(self,data):return baggage_check(data)
    def item(self,item,data=None):return item_check(item,data)
    def documents(self,data):return travel_documents(data)
    def guide(self,data):return guide(data)
    def practice(self,scenario,data=None):return practice(scenario,data)
    def booking(self,data):return booking_simulation(data)
    def airline(self,name):return airline_lookup(name)
    def sources(self,topic_id="official"):return official_handoff(topic_id)
    def validate(self,data):return validate_trip(data)
    def status(self):return engine_status()

engine=TravelEngine()

__all__=[
"VERSION","APP_NAME","OWNER","app_identity","classify_problem","cuba_check",
"cuba_entry_path","visa_check","dviajeros_check","visa_simulation","flight_segments",
"connection_check","airport_now","baggage_check","item_check","travel_documents",
"guide","practice","booking_simulation","airline_lookup","official_handoff",
"solve","validate_trip","export_trip_state","engine_status","TravelEngine","engine"
]
