# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v13.0.0
from __future__ import annotations
import os,json,re,urllib.request,urllib.error
from typing import Any,Dict,List,Optional

VERSION="13.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
SIM_NOTICE="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
NO_BOOKING="La aplicación no reserva, compra ni envía formularios oficiales."

def _text(v:Any)->str:
    return str(v or "").strip()

def _low(v:Any)->str:
    return _text(v).lower()

def _sources(topic:str="",query:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as sr
        if hasattr(sr,"get_sources"):return sr.get_sources(topic or "official",query,country,airline)
        if hasattr(sr,"sources_for"):return sr.sources_for(topic,country,airline)
    except Exception:
        return []
    return []

def _source(topic:str,id_:str)->Dict[str,Any]:
    try:
        import source_registry as sr
        x=sr.source_by_id(id_)
        if x:return x
    except Exception:pass
    xs=_sources(topic)
    for x in xs:
        if x.get("id")==id_:return x
    return {}

def _base(message:str,next_action:str="",sources:Optional[List[Dict[str,Any]]]=None)->Dict[str,Any]:
    return {"version":VERSION,"message":message,"next_action":next_action,"sources":sources or []}

def _official(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as sr
        if hasattr(sr,"official_sources"):return sr.official_sources(topic,country,airline)
    except Exception:pass
    return _sources(topic,"",country,airline)

def cuba_profile(data:Dict[str,Any])->Dict[str,Any]:
    cuban=bool(data.get("cuban_nationality") or data.get("has_cuban_passport"))
    dual=bool(data.get("dual_citizen") or data.get("has_other_passport"))
    return {"cuban_nationality":cuban,"dual_citizen":dual,"nationality":_text(data.get("nationality")),"passport_country":_text(data.get("passport_country")),"residence_country":_text(data.get("country_of_residence") or data.get("residence_country")),"has_cuban_passport":bool(data.get("has_cuban_passport")),"has_other_passport":bool(data.get("has_other_passport"))}

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    p=cuba_profile(data)
    checks=[]
    def add(key,label,ok,why):
        checks.append({"id":key,"label":label,"complete":bool(ok),"why":why})
    add("identity","Nacionalidad y situación migratoria",p["nationality"] or p["cuban_nationality"],"Necesitamos saber qué nacionalidad y documento corresponden a tu viaje.")
    add("passport","Pasaporte",p["passport_country"] or data.get("passport_number"),"Permite identificar el documento con el que practicarás el proceso.")
    add("passport_validity","Vigencia del pasaporte",data.get("passport_valid_until"),"La vigencia puede ser relevante para la entrada y debe verificarse oficialmente.")
    add("entry","Entrada a Cuba",data.get("destination") or "Cuba","Confirma que el destino del proceso es Cuba.")
    add("visa","Visa o autorización",bool(data.get("visa_checked")), "La necesidad y forma de autorización dependen de la nacionalidad y del caso.")
    add("dviajeros","D’Viajeros",bool(data.get("dviajeros_done")),"La declaración debe revisarse y realizarse en el sitio oficial cuando corresponda.")
    add("customs","Aduana y artículos",bool(data.get("customs_checked")),"Las reglas de entrada de artículos deben verificarse con Aduana.")
    add("baggage","Equipaje",bool(data.get("baggage_checked")),"El equipaje también depende de la aerolínea, tarifa y ruta.")
    add("documents","Documentos",bool(data.get("documents_checked")),"Los documentos deben revisarse antes del viaje.")
    completed=sum(1 for x in checks if x["complete"])
    pending=[x["label"] for x in checks if not x["complete"]]
    next_action="Completa: "+pending[0] if pending else "Puedes pasar a practicar el proceso de Cuba."
    return {"status":"ready" if not pending else "incomplete","profile":p,"checklist":checks,"completed":completed,"total":len(checks),"progress":round(completed/len(checks)*100),"pending":pending,"next_action":next_action,"details":{"entry_exit":"La aplicación prepara el proceso; los requisitos oficiales deben verificarse antes del viaje."},"sources":_official("cuba")}

def baggage_type_name(t:str)->str:
    return {"carry_on":"equipaje de mano","personal_item":"artículo personal","checked":"equipaje facturado","unknown":"equipaje"}.get(_low(t),"equipaje")

def baggage_explanation(t:str)->str:
    n=baggage_type_name(t)
    return f"Estamos preparando la revisión de {n}. El tamaño, peso, cantidad y contenido deben comprobarse según la aerolínea, tarifa, ruta y autoridades aplicables."

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    airline=_text(data.get("airline"))
    destination=_text(data.get("destination"))
    origin=_text(data.get("origin"))
    fare=_text(data.get("fare"))
    typ=_text(data.get("type") or data.get("baggage_type"))
    query="baggage"
    sources=_official(query,"",airline)
    return {"status":"review","type":typ,"type_name":baggage_type_name(typ),"airline":airline,"origin":origin,"destination":destination,"fare":fare,"message":baggage_explanation(typ),"do_not_assume":["peso","dimensiones","cantidad de piezas","costo"],"next_action":"Abre la fuente oficial de tu aerolínea y comprueba las condiciones de tu tarifa.","sources":sources}

def _item_category(item:str)->str:
    x=_low(item)
    if any(k in x for k in ["gasolina","gasoline","petróleo","petroleo","fuel","combustible"]):return "combustible"
    if any(k in x for k in ["soda cáustica","soda caustica","caustic soda"]):return "químico"
    if any(k in x for k in ["batería","bateria","battery","power bank","litio","lithium"]):return "batería"
    if any(k in x for k in ["semilla","seeds","planta","plant"]):return "agrícola"
    if any(k in x for k in ["carne","jamón","jamon","meat","food","comida","uva","guayaba","yogur","yogurt","agua","water","refresco","soda"]):return "alimento"
    if any(k in x for k in ["medicamento","medicine","drug","pastilla","pill"]):return "medicamento"
    if any(k in x for k in ["animal","mascota","pet"]):return "animal"
    if any(k in x for k in ["aerosol","spray","líquido","liquido","liquid"]):return "líquido"
    if any(k in x for k in ["electrónico","electronico","electronic","laptop","phone","teléfono","telefono"]):return "electrónico"
    return "general"

def _gemini(item:str,data:Dict[str,Any])->Optional[Dict[str,Any]]:
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key:return None
    model=os.getenv("GEMINI_MODEL","gemini-2.5-flash").strip()
    prompt=f"""You are an assistant inside a travel preparation app. Analyze ONLY whether the traveler should verify an item for air travel. Never invent a law, airline rule, customs rule, weight, quantity, or permission. Never claim final authorization. The official authorities and airline make the final decision. Item: {item}. Origin: {_text(data.get("origin"))}. Destination: {_text(data.get("destination"))}. Airline: {_text(data.get("airline"))}. Baggage: {_text(data.get("baggage_type") or data.get("type"))}. Quantity: {_text(data.get("quantity"))}. Weight: {_text(data.get("weight"))}. Return JSON only with keys: status,reason,verify_with,questions. status must be one of verify,likely_restricted,needs_official_confirmation. Keep it concise."""
    body=json.dumps({"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0,"responseMimeType":"application/json"}}).encode()
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=json.loads(r.read().decode("utf-8"))
        txt=raw["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(txt)
    except Exception:
        return None

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    item=_text(data.get("item"))
    category=_item_category(item)
    gem=_gemini(item,data)
    sources=[]
    if category in ("batería","electrónico"):sources+=_official("battery")
    elif category in ("líquido","medicamento"):sources+=_official(category)
    elif category=="alimento":sources+=_official("customs")
    elif category in ("combustible","químico"):sources+=_official("security")
    else:sources+=_official("baggage")
    if gem:
        message=gem.get("reason") or "Este artículo necesita verificación oficial antes de viajar."
        status=gem.get("status") or "verify"
        verify_with=gem.get("verify_with") or ["aerolínea","autoridad de seguridad","aduana del destino"]
    else:
        status="verify"
        message="No voy a inventar si este artículo está permitido. Hay que comprobarlo según seguridad, aerolínea y, cuando corresponda, aduana del destino."
        verify_with=["TSA u otra autoridad de seguridad aplicable","aerolínea","aduana del destino"]
    return {"status":status,"item":item,"category":category,"baggage_type":_text(data.get("baggage_type") or data.get("type")),"message":message,"gemini_used":bool(gem),"final_decision":False,"verify_with":verify_with,"next_action":"Consulta las fuentes oficiales antes de empacarlo.","sources":sources}

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    same=bool(data.get("same_ticket"))
    country_change=bool(data.get("country_change"))
    baggage=_text(data.get("baggage") or data.get("bag_recheck"))
    checks=[
        {"id":"arrival","label":"Ubica llegada y siguiente vuelo","complete":bool(data.get("airport") or data.get("next_flight"))},
        {"id":"terminal","label":"Comprueba terminal y puerta","complete":bool(data.get("terminal") or data.get("next_terminal") or data.get("gate") or data.get("next_gate"))},
        {"id":"ticket","label":"Comprueba si los vuelos están en el mismo billete","complete":same},
        {"id":"baggage","label":"Comprueba qué ocurre con el equipaje","complete":bool(baggage)},
        {"id":"border","label":"Comprueba si existe cambio de país","complete":country_change},
    ]
    pending=[x["label"] for x in checks if not x["complete"]]
    return {"status":"ready" if not pending else "incomplete","same_ticket":same,"country_change":country_change,"checks":checks,"pending":pending,"message":"Una conexión debe verificarse con la aerolínea y, cuando corresponda, con el aeropuerto o autoridad migratoria.","next_action":pending[0] if pending else "Practica ahora la conexión paso a paso.","sources":_official("flight")}

def _segments(data:Dict[str,Any])->List[Dict[str,Any]]:
    seg=data.get("segments")
    if isinstance(seg,list):return seg
    return [{"origin":data.get("origin"),"destination":data.get("destination"),"airline":data.get("airline"),"flight_number":data.get("flight_number")}]

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    origin=_text(data.get("origin"))
    destination=_text(data.get("destination"))
    airline=_text(data.get("airline"))
    stops=data.get("stops")
    segments=_segments(data)
    missing=[]
    for key,label in [("origin","origen"),("destination","destino"),("airline","aerolínea"),("departure","fecha de salida"),("passengers","pasajeros")]:
        if not data.get(key):missing.append(label)
    if stops in (None,""):stops=0
    try:stops=int(stops)
    except Exception:stops=0
    return {"status":"ready" if not missing else "incomplete","search":{"origin":origin,"destination":destination,"airline":airline,"stops":stops,"segments":segments},"missing":missing,"message":"Esto es preparación de un vuelo, no una reserva real.","next_action":"Practica la búsqueda y después abre el sitio oficial de la aerolínea.","sources":_official("airline","",airline) if airline else _official("flight")}

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    airline=_text(data.get("airline"))
    fields=["origen","destino","fecha de salida","fecha de regreso si aplica","pasajeros","cabina","tarifa","equipaje"]
    steps=[
        {"step":1,"title":"Buscar vuelo","instruction":"Introduce origen, destino y fechas.","fields":["origin","destination","departure","return_date"]},
        {"step":2,"title":"Elegir vuelo","instruction":"Compara las opciones mostradas por la aerolínea sin comprar.","fields":["airline","flight_number","flight_type","stops"]},
        {"step":3,"title":"Revisar condiciones","instruction":"Comprueba cabina, tarifa, equipaje y conexiones.","fields":["cabin","fare","bags","same_ticket"]},
        {"step":4,"title":"Revisar pasajeros","instruction":"En una reserva real se introducirían los datos solicitados por la aerolínea. Aquí no se envían.","fields":["passengers"]},
        {"step":5,"title":"Finalizar práctica","instruction":"No se realiza pago ni reserva. Abre el sitio oficial para continuar de verdad.","fields":[]}
    ]
    return {"simulation":True,"real_booking":False,"payment":False,"official_submission":False,"notice":SIM_NOTICE,"message":NO_BOOKING,"fields":fields,"steps":steps,"airline":airline,"next_action":"Continúa en el sitio oficial de la aerolínea.","sources":_official("airline","",airline) if airline else _official("airline")}

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    checks=[
        ("nationality","Nacionalidad",data.get("nationality")),
        ("passport_country","País del pasaporte",data.get("passport_country")),
        ("country_of_residence","País de residencia",data.get("country_of_residence")),
        ("purpose","Motivo del viaje",data.get("purpose")),
        ("arrival_date","Fecha de llegada",data.get("arrival_date")),
        ("departure_date","Fecha de salida",data.get("departure_date")),
        ("passport_valid_until","Vigencia del pasaporte",data.get("passport_valid_until")),
    ]
    result=[{"id":a,"label":b,"complete":bool(c)} for a,b,c in checks]
    pending=[x["label"] for x in result if not x["complete"]]
    return {"status":"ready" if not pending else "incomplete","checks":result,"pending":pending,"next_action":pending[0] if pending else "Comprueba los documentos con las fuentes oficiales.","sources":_official("documents") or _official("travel")}

def practice_scenario(scenario:str,data:Dict[str,Any])->Dict[str,Any]:
    sc=_low(scenario) or "airport"
    step_raw=data.get("step",0)
    try:step=max(0,int(step_raw))
    except Exception:step=0
    sets={
        "airport":[
            {"title":"Identificar el vuelo","question":"¿Cuál es tu aerolínea y número de vuelo?","fields":["airline","flight_number"]},
            {"title":"Encontrar la puerta","question":"¿Dónde aparece la terminal o puerta?","fields":["terminal","gate"]},
            {"title":"Prepararte para abordar","question":"¿Qué debes revisar antes de ir a la puerta?","fields":["boarding_time","passport","boarding_pass"]}
        ],
        "connection":[
            {"title":"Llegar al primer vuelo","question":"¿Cuál es tu aeropuerto de llegada?","fields":["airport","terminal","gate"]},
            {"title":"Encontrar el siguiente vuelo","question":"¿Cuál es tu siguiente vuelo y puerta?","fields":["next_flight","next_gate","next_terminal"]},
            {"title":"Comprobar equipaje","question":"¿Necesitas comprobar si el equipaje continúa automáticamente?","fields":["same_ticket","baggage","bag_recheck"]}
        ],
        "baggage":[
            {"title":"Elegir el equipaje","question":"¿Es artículo personal, equipaje de mano o facturado?","fields":["type"]},
            {"title":"Comprobar condiciones","question":"¿Cuál es tu aerolínea y tarifa?","fields":["airline","fare","cabin"]},
            {"title":"Comprobar medidas","question":"¿Qué peso y dimensiones permite tu tarifa?","fields":["weight","dimensions","pieces"]}
        ],
        "dviajeros":[
            {"title":"Datos personales","question":"Practica los datos personales que solicita el formulario oficial.","fields":["given_names","surnames","birth_date","nationality","sex"]},
            {"title":"Pasaporte","question":"Practica los datos del pasaporte sin enviar nada al sitio oficial.","fields":["passport_number","passport_country","country_of_residence"]},
            {"title":"Viaje","question":"Practica los datos del viaje y aeropuerto.","fields":["arrival_date","departure_date","flight","arrival_airport","departure_airport"]},
            {"title":"Contacto y destino","question":"Practica los datos de contacto y dirección en Cuba.","fields":["email","phone","address_destination"]}
        ],
        "visa":[
            {"title":"Identidad","question":"Practica los datos personales de la solicitud.","fields":["surname","given_names","birth_date","sex","nationality"]},
            {"title":"Pasaporte","question":"Practica los datos del pasaporte.","fields":["passport_number","passport_country"]},
            {"title":"Viaje","question":"Practica motivo y fechas del viaje.","fields":["purpose","arrival_date","departure_date","destination"]},
            {"title":"Contacto","question":"Practica los datos de contacto.","fields":["email","phone","country_of_residence"]}
        ]
    }
    steps=sets.get(sc,sets["airport"])
    if step>=len(steps):step=len(steps)-1
    current=steps[step]
    return {"mode":"practice","scenario":sc,"official_submission":False,"notice":SIM_NOTICE,"message":"Esta práctica no envía información ni crea una solicitud oficial.","current_step":current,"steps":steps,"step":step,"progress":round((step+1)/len(steps)*100),"completed":step+1,"pending":len(steps)-(step+1),"next_action":"Completa este paso y continúa con el siguiente." if step<len(steps)-1 else "Práctica terminada. Revisa el sitio oficial antes de realizar el trámite real.","sources":_official("dviajeros") if sc=="dviajeros" else _official("visa") if sc=="visa" else _official("flight")}

def dviajeros_simulation(data:Dict[str,Any])->Dict[str,Any]:
    return practice_scenario("dviajeros",data)

def visa_simulation(data:Dict[str,Any])->Dict[str,Any]:
    return practice_scenario("visa",data)

def build_guide(data:Dict[str,Any])->Dict[str,Any]:
    pending=[]
    required=[("origin","origen"),("destination","destino"),("nationality","nacionalidad"),("passport_country","país del pasaporte"),("airline","aerolínea")]
    for k,l in required:
        if not data.get(k):pending.append(l)
    if data.get("destination","").lower()=="cuba" or "cuba" in _low(data.get("destination")):
        if not data.get("dviajeros_done"):pending.append("D’Viajeros")
        if not data.get("visa_checked"):pending.append("verificación de visa/autorización")
        if not data.get("documents_checked"):pending.append("documentos")
        if not data.get("customs_checked"):pending.append("aduana")
    return {"status":"ready" if not pending else "incomplete","guide":{"trip":data,"pending":pending,"items":data.get("items",[]),"baggage":data.get("baggage",{}),"next_action":pending[0] if pending else "Revisa las fuentes oficiales y conserva tu guía de preparación."},"next_action":pending[0] if pending else "Guía preparada.","sources":_official("official")}

def create_travel_pdf(data:Dict[str,Any])->Dict[str,Any]:
    return {"created":False,"message":"El PDF se genera desde main.py. Este módulo prepara los datos.","data":data}

def solve(question:str,data:Optional[Dict[str,Any]]=None)->Dict[str,Any]:
    q=_text(question)
    if not q:return {"status":"incomplete","message":"Escribe la pregunta que quieres resolver.","next_action":"Escribe tu pregunta."}
    if any(x in _low(q) for x in ["llevar","equipaje","puedo llevar","can i bring"]):
        d=dict(data or {});d["item"]=d.get("item") or q
        return item_analysis(d)
    if "cuba" in _low(q):return cuba_check(data or {})
    return {"status":"verify","message":"Necesito identificar el tema exacto para darte una orientación segura sin inventar reglas.","next_action":"Indica si tu pregunta es sobre vuelo, equipaje, artículo, Cuba, visa, D’Viajeros o documentos.","sources":_official("official")}

def answer(question:str,data:Optional[Dict[str,Any]]=None)->Dict[str,Any]:
    return solve(question,data)

def resolve(question:str,data:Optional[Dict[str,Any]]=None)->Dict[str,Any]:
    return solve(question,data)

def get_charters(query:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as sr
        return sr.get_charters(query)
    except Exception:return []

def get_official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as sr
        return sr.get_official_sources(topic,country,airline)
    except Exception:return []

__all__=["VERSION","APP_NAME","SIM_NOTICE","cuba_profile","cuba_check","baggage_type_name","baggage_explanation","baggage_rules","item_analysis","connection_analysis","analyze_flight","booking_simulation","document_analysis","practice_scenario","dviajeros_simulation","visa_simulation","build_guide","create_travel_pdf","solve","answer","resolve","get_charters","get_official_sources"]
