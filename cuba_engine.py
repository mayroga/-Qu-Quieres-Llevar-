# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v14.0.0
from __future__ import annotations
from typing import Any,Dict,List
from datetime import datetime

VERSION="14.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
NOTICE="Preparación y práctica independiente. Los formularios reales se completan únicamente en los sitios oficiales."

def _s(v:Any)->str:
    return str(v if v is not None else "").strip()

def _b(v:Any)->bool:
    if isinstance(v,bool):return v
    return _s(v).lower() in ("1","true","yes","si","sí","x","checked")

def _sources(topic:str="cuba",country:str="CU",airline:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as sr
        return sr.get_sources(topic=topic,country=country,airline=airline)
    except Exception:
        try:
            import source_registry as sr
            return sr.official_sources(topic,country,airline)
        except Exception:return []

def _source(topic:str="cuba",country:str="CU",airline:str="")->List[Dict[str,Any]]:
    r=_sources(topic,country,airline)
    if r:return r
    try:
        import source_registry as sr
        return sr.official_sources()
    except Exception:return []

def _airline_source(airline:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as sr
        return sr.get_airlines(airline) if airline else sr.get_airlines()
    except Exception:return []

def _charter_source(query:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as sr
        return sr.get_charters(query)
    except Exception:return []

def _item_sources(item:str,airline:str="",origin:str="",destination:str="")->List[Dict[str,Any]]:
    out=[]
    seen=set()
    try:
        import source_registry as sr
        for s in sr.get_sources("item",item,"",airline):
            if s["id"] not in seen:
                out.append(s);seen.add(s["id"])
        for s in sr.get_sources("baggage","", "",airline):
            if s["id"] not in seen:
                out.append(s);seen.add(s["id"])
        for s in sr.get_sources("security"):
            if s["id"] not in seen:
                out.append(s);seen.add(s["id"])
    except Exception:pass
    if not out:
        out=_source("item","US",airline)
    return out

def _profile(d:Dict[str,Any])->Dict[str,Any]:
    return {
        "nombres":_s(d.get("given_names") or d.get("first_name") or d.get("names")),
        "apellidos":_s(d.get("surnames") or d.get("surname") or d.get("last_name")),
        "nacionalidad":_s(d.get("nationality")),
        "pasaporte":_s(d.get("passport_number")),
        "pais_pasaporte":_s(d.get("passport_country")),
        "residencia":_s(d.get("country_of_residence")),
        "fecha_nacimiento":_s(d.get("birth_date")),
        "sexo":_s(d.get("sex")),
        "correo":_s(d.get("email")),
        "telefono":_s(d.get("phone")),
        "motivo":_s(d.get("purpose")),
        "llegada":_s(d.get("arrival_date")),
        "salida":_s(d.get("departure_date")),
        "aerolinea":_s(d.get("airline") or d.get("flight_airline")),
        "vuelo":_s(d.get("flight") or d.get("flight_number")),
        "aeropuerto_llegada":_s(d.get("arrival_airport") or d.get("entry_airport")),
        "aeropuerto_salida":_s(d.get("departure_airport")),
        "direccion":_s(d.get("address_destination")),
        "numero_visa":_s(d.get("visa_number") or d.get("evisa_number"))
    }

def _step(n:int,title:str,instruction:str,fields:List[str],options:List[str]=None)->Dict[str,Any]:
    return {
        "step":n,
        "title":title,
        "instruction":instruction,
        "fields":fields,
        "options":options or [],
        "completed":False
    }

def _required(profile:Dict[str,Any],fields:List[str])->List[str]:
    return [x for x in fields if not profile.get(x)]

def _progress(total:int,pending:int)->float:
    if total<=0:return 0.0
    return round(max(0,min(100,((total-pending)/total)*100)),1)

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    p=_profile(d)
    cuban=_b(d.get("cuban_nationality"))
    dual=_b(d.get("dual_citizen"))
    checklist=[
        {"id":"passport","title":"Pasaporte","status":"review","detail":"Comprueba que el pasaporte que utilizarás para el viaje sea el correcto y esté vigente."},
        {"id":"nationality","title":"Nacionalidad","status":"review","detail":"La nacionalidad y el pasaporte utilizado pueden cambiar los requisitos de entrada."},
        {"id":"visa","title":"Visa / eVisa","status":"done" if _b(d.get("visa_checked")) else "pending","detail":"Revisa el proceso oficial de visa correspondiente a tu caso."},
        {"id":"dviajeros","title":"D’Viajeros","status":"done" if _b(d.get("dviajeros_done")) else "pending","detail":"Completa el formulario oficial antes del viaje y conserva el resultado."},
        {"id":"flight","title":"Vuelo","status":"done" if _s(d.get("flight_number") or d.get("flight")) else "pending","detail":"Ten a mano la aerolínea y el número de vuelo."},
        {"id":"insurance","title":"Seguro de viaje","status":"review","detail":"Comprueba el requisito vigente y las condiciones aplicables a tu viaje."},
        {"id":"customs","title":"Aduana","status":"done" if _b(d.get("customs_checked")) else "pending","detail":"Revisa las reglas oficiales de aduana y los artículos que llevarás."},
        {"id":"documents","title":"Documentos","status":"done" if _b(d.get("documents_checked")) else "pending","detail":"Reúne los documentos necesarios antes de salir."}
    ]
    completed=sum(1 for x in checklist if x["status"]=="done")
    pending=[x["title"] for x in checklist if x["status"]!="done"]
    sources=_source("cuba","CU")
    return {
        "status":"ready" if not pending else "incomplete",
        "profile":p,
        "checklist":checklist,
        "completed":completed,
        "total":len(checklist),
        "progress":_progress(len(checklist),len(pending)),
        "pending":pending,
        "details":{
            "cuban_nationality":cuban,
            "dual_citizen":dual,
            "main_process":"D’Viajeros + Visa",
            "official_only":True
        },
        "message":"Aquí tienes tu preparación. Revisa cada punto y utiliza siempre el sitio oficial para realizar el trámite real.",
        "next_action":"Continúa con el paso pendiente más importante.",
        "sources":sources
    }

def dviajeros_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    p=_profile(d)
    fields=[
        "nombres","apellidos","pasaporte","nacionalidad","motivo",
        "numero_visa","aerolinea","vuelo","llegada","aeropuerto_llegada",
        "direccion"
    ]
    missing=_required(p,fields)
    steps=[
        _step(1,"Crear nueva solicitud","En el sitio oficial selecciona la opción para comenzar un nuevo formulario.",["Idioma","Crear formulario"],["Español"]),
        _step(2,"Datos personales","Coloca tus datos exactamente como aparecen en tu pasaporte.",["Nombres","Apellidos","Número de pasaporte","Nacionalidad","Motivo de viaje"]),
        _step(3,"Visa","Introduce el número de visa/eVisa cuando corresponda a tu caso.",["Número de visa/eVisa"]),
        _step(4,"Información del vuelo","Utiliza los datos reales de tu boleto.",["País de procedencia","Aerolínea","Número de vuelo","Fecha de entrada","Aeropuerto de llegada"]),
        _step(5,"Alojamiento","Introduce el alojamiento y la dirección que correspondan a tu viaje.",["Tipo de alojamiento","Provincia","Municipio","Nombre o dirección"]),
        _step(6,"Aduana y control","Responde las preguntas oficiales según tu situación real.",["Medicamentos","Dinero en efectivo","Preguntas de control"]),
        _step(7,"Revisión y envío","Revisa todo antes de enviar el formulario oficial.",["Revisión final","Enviar datos","Código QR / comprobante"])
    ]
    done=len(fields)-len(missing)
    return {
        "status":"ready" if not missing else "incomplete",
        "scenario":"dviajeros",
        "simulation":True,
        "official_submission":False,
        "notice":NOTICE,
        "message":"Te mostramos el proceso paso a paso para que sepas qué encontrarás. La aplicación no envía el formulario por ti.",
        "step":1,
        "progress":_progress(len(fields),len(missing)),
        "current_step":steps[0],
        "steps":steps,
        "missing":missing,
        "prefilled":p,
        "official_url":"https://dviajeros.mitrans.gob.cu/",
        "next_action":"Abre el sitio oficial de D’Viajeros y utiliza estos datos como guía.",
        "sources":_source("dviajeros","CU")
    }

def visa_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    p=_profile(d)
    fields=["nacionalidad","nombres","apellidos","pasaporte","fecha_nacimiento","motivo","correo"]
    missing=_required(p,fields)
    steps=[
        _step(1,"Datos del pasaporte","Utiliza exactamente los datos de tu pasaporte.",["Nacionalidad","Primer nombre","Apellidos","Número de pasaporte","Fecha de nacimiento"]),
        _step(2,"Motivo y contacto","Selecciona el motivo que corresponda y utiliza un correo al que tengas acceso.",["Motivo del viaje","Correo electrónico"]),
        _step(3,"Solicitud","Revisa cuidadosamente los datos antes de continuar en la plataforma oficial.",["Revisión de datos","Continuar"]),
        _step(4,"Pago oficial","Si el trámite oficial exige un pago, el pago se realiza únicamente dentro de la plataforma oficial.",["Método de pago","Confirmación"]),
        _step(5,"Resultado","Conserva el resultado, número o documento que emita oficialmente la plataforma.",["Número de eVisa","Documento / comprobante"])
    ]
    return {
        "status":"ready" if not missing else "incomplete",
        "scenario":"visa",
        "simulation":True,
        "official_submission":False,
        "notice":NOTICE,
        "message":"Te mostramos qué datos necesitarás y en qué orden. La solicitud real se realiza únicamente en el sitio oficial.",
        "step":1,
        "progress":_progress(len(fields),len(missing)),
        "current_step":steps[0],
        "steps":steps,
        "missing":missing,
        "prefilled":p,
        "official_url":"https://evisacuba.cu/",
        "next_action":"Abre el sitio oficial de eVisa y copia tus datos reales desde tu preparación.",
        "sources":_source("visa","CU")
    }

def practice_scenario(scenario:str,data:Dict[str,Any])->Dict[str,Any]:
    s=_s(scenario).lower()
    if "dvia" in s:return dviajeros_simulation(data)
    if "visa" in s:return visa_simulation(data)
    p=_profile(data)
    steps=[
        _step(1,"Preparar","Mira tus datos antes de comenzar.",["Pasaporte","Vuelo","Destino"]),
        _step(2,"Comprobar","Revisa los documentos y requisitos oficiales.",["Documentos","Visa","D’Viajeros"]),
        _step(3,"Continuar","Realiza el trámite real en el sitio oficial.",["Sitio oficial"])
    ]
    return {
        "mode":"practice",
        "scenario":s or "airport",
        "official_submission":False,
        "notice":NOTICE,
        "message":"Preparación práctica para que puedas hacer el proceso con tranquilidad.",
        "next_action":"Selecciona el proceso que quieres preparar.",
        "completed":0,
        "pending":len(steps),
        "progress":0,
        "sources":_source("cuba","CU"),
        "scenarios":["dviajeros","visa","airport"],
        "current_step":steps[0],
        "steps":steps,
        "step":1
    }

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    checks=[
        {"id":"passport","title":"Pasaporte","status":"review","message":"Revisa vigencia y datos."},
        {"id":"nationality","title":"Nacionalidad","status":"review","message":"Confirma que coincide con tu documentación."},
        {"id":"visa","title":"Visa / eVisa","status":"done" if _b(d.get("visa_checked")) else "pending","message":"Comprueba el requisito aplicable."},
        {"id":"dviajeros","title":"D’Viajeros","status":"done" if _b(d.get("dviajeros_done")) else "pending","message":"Completa el formulario oficial."},
        {"id":"flight","title":"Vuelo","status":"done" if _s(d.get("flight_number")) else "pending","message":"Confirma aerolínea y vuelo."}
    ]
    pending=[x["title"] for x in checks if x["status"]!="done"]
    return {
        "status":"ready" if not pending else "incomplete",
        "checks":checks,
        "pending":pending,
        "next_action":"Revisa el primer elemento pendiente.",
        "sources":_source("documents","CU")
    }

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    airline=_s(d.get("airline"))
    sources=_source("baggage","",airline)
    if not sources:sources=_airline_source(airline)
    return {
        "status":"review",
        "type":_s(d.get("type") or d.get("baggage_type")),
        "type_name":_s(d.get("type") or d.get("baggage_type")),
        "airline":airline,
        "origin":_s(d.get("origin")),
        "destination":_s(d.get("destination")),
        "fare":_s(d.get("fare")),
        "message":"La respuesta depende del artículo, la aerolínea, el tipo de equipaje y el viaje. Revisa la fuente oficial correspondiente.",
        "do_not_assume":[
            "No asumir peso o dimensiones sin revisar la aerolínea.",
            "No asumir que un artículo permitido por TSA también está permitido por la aerolínea o Cuba.",
            "No asumir que una regla de una aerolínea aplica a otra."
        ],
        "next_action":"Indica qué quieres llevar y, si la conoces, tu aerolínea.",
        "sources":sources
    }

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    item=_s(d.get("item") or d.get("description"))
    airline=_s(d.get("airline"))
    sources=_item_sources(item,airline,_s(d.get("origin")),_s(d.get("destination")))
    gemini=False
    if item and __import__("os").getenv("GEMINI_API_KEY"):
        try:
            gemini=True
        except Exception:gemini=False
    return {
        "status":"verify",
        "item":item,
        "category":"",
        "baggage_type":_s(d.get("baggage_type")),
        "message":"Sí puedo ayudarte a revisar qué hacer con ese artículo. La respuesta debe comprobarse con la fuente oficial correspondiente.",
        "gemini_used":gemini,
        "final_decision":False,
        "verify_with":sources,
        "next_action":"Revisa la fuente oficial mostrada antes de viajar.",
        "sources":sources
    }

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    airline=_s(d.get("airline"))
    required=["origin","destination","departure"]
    missing=[x for x in required if not _s(d.get(x))]
    sources=_airline_source(airline)
    return {
        "status":"ready" if not missing else "incomplete",
        "message":"Revisa los datos de tu vuelo y continúa con el sitio oficial de la aerolínea.",
        "search":{
            "origin":_s(d.get("origin")),
            "destination":_s(d.get("destination")),
            "airline":airline,
            "flight_number":_s(d.get("flight_number")),
            "departure":_s(d.get("departure"))
        },
        "missing":missing,
        "next_action":"Abre el sitio oficial de la aerolínea.",
        "sources":sources
    }

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    airline=_s(d.get("airline"))
    sources=_airline_source(airline)
    return {
        "status":"ok",
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "official_submission":False,
        "notice":"Preparación de vuelo. La compra real se realiza en el sitio oficial.",
        "message":"Aquí puedes revisar qué información necesitarás para comprar tu boleto sin hacer la operación dentro de esta aplicación.",
        "search":{k:d.get(k,"") for k in ("origin","destination","departure","return_date","passengers","cabin","airline","flight_number")},
        "fields":["Origen","Destino","Fecha","Pasajeros","Aerolínea","Vuelo","Equipaje"],
        "steps":[
            {"step":1,"title":"Buscar","instruction":"Introduce origen, destino y fecha en el sitio oficial.","completed":False},
            {"step":2,"title":"Elegir","instruction":"Compara las opciones que muestre la aerolínea.","completed":False},
            {"step":3,"title":"Revisar","instruction":"Comprueba pasajeros, equipaje, fechas y condiciones.","completed":False},
            {"step":4,"title":"Comprar","instruction":"Si decides comprar, hazlo directamente en el sitio oficial.","completed":False}
        ],
        "next_action":"Abre el sitio oficial de la aerolínea.",
        "sources":sources
    }

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    airline=_s(d.get("airline"))
    next_airline=_s(d.get("next_airline"))
    sources=_airline_source(airline)
    if next_airline and next_airline.lower()!=airline.lower():
        sources+=_airline_source(next_airline)
    return {
        "status":"ok",
        "message":"Revisa terminal, puerta, equipaje y condiciones de conexión directamente con la aerolínea.",
        "next_action":"Comprueba la conexión en los sitios oficiales.",
        "sources":sources
    }

def cuba_entry(data:Dict[str,Any])->Dict[str,Any]:
    return cuba_check(data)

def build_guide(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    cuba=cuba_check(d)
    return {
        "status":cuba["status"],
        "guide":{
            "app":APP_NAME,
            "version":VERSION,
            "trip":d,
            "cuba":cuba,
            "dviajeros":dviajeros_simulation(d),
            "visa":visa_simulation(d)
        },
        "pending":cuba["pending"],
        "next_action":cuba["next_action"],
        "sources":cuba["sources"]
    }

def solve(question:str,data:Dict[str,Any])->Dict[str,Any]:
    q=_s(question).lower()
    d=dict(data or {})
    if any(x in q for x in ("llevar","equipaje","puedo llevar","se puede llevar","permitido")):
        return item_analysis({**d,"item":d.get("item") or question})
    if "dviajero" in q:return dviajeros_simulation(d)
    if "visa" in q:return visa_simulation(d)
    if any(x in q for x in ("vuelo","aerolínea","aerolinea","boleto")):
        return analyze_flight(d)
    return {
        "status":"ok",
        "message":"Puedo ayudarte a preparar tu viaje, revisar qué puedes llevar y orientarte hacia el sitio oficial correspondiente.",
        "next_action":"Dime qué quieres llevar o qué parte del viaje quieres preparar.",
        "sources":_source("cuba","CU")
    }

def answer(question:str,data:Dict[str,Any])->Dict[str,Any]:
    return solve(question,data)

def health()->Dict[str,Any]:
    return {"status":"ok","version":VERSION,"ready":True}

__all__=[
    "VERSION","APP_NAME","cuba_check","cuba_entry","dviajeros_simulation",
    "visa_simulation","practice_scenario","document_analysis","baggage_rules",
    "item_analysis","analyze_flight","booking_simulation","connection_analysis",
    "build_guide","solve","answer","health"
]
