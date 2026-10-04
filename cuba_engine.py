# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v15.0.0
from __future__ import annotations
import os,json,re,urllib.request,urllib.error
from datetime import datetime
from typing import Any,Dict,List,Optional
from source_registry import (
    source_by_id,get_sources,official_sources,answer_sources,
    get_airlines,get_charters,official_url
)

VERSION="15.0.0"
APP="¿QUÉ QUIERES LLEVAR?"
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()

def _s(v:Any)->str:
    return str(v or "").strip()

def _l(v:Any)->str:
    return _s(v).lower()

def _b(v:Any)->bool:
    if isinstance(v,bool):return v
    return _l(v) in ("1","true","yes","si","sí","y","on")

def _n(v:Any,default:int=0)->int:
    try:return int(v)
    except Exception:return default

def _now()->str:
    return datetime.utcnow().replace(microsecond=0).isoformat()+"Z"

def _source(i:str)->Dict[str,Any]:
    return source_by_id(i) or {}

def _sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return official_sources(topic,country,airline)

def _airline_source(name:str)->Dict[str,Any]:
    a=_s(name)
    if not a:return {}
    found=get_airlines(a)
    return found[0] if found else {}

def _charter_source(name:str)->Dict[str,Any]:
    a=_s(name)
    if not a:return {}
    found=get_charters(a)
    return found[0] if found else {}

def _dedupe_sources(items:List[Dict[str,Any]])->List[Dict[str,Any]]:
    out=[];seen=set()
    for x in items or []:
        if not isinstance(x,dict):continue
        i=_s(x.get("id"))
        if i and i not in seen:
            seen.add(i);out.append(x)
    return out

def _item_sources(item:str="",airline:str="",origin:str="",destination:str="Cuba")->List[Dict[str,Any]]:
    out=[]
    if airline:
        out+=get_sources("airline","",destination,airline)
    q=f"{item} {_s(origin)} {_s(destination)}".strip()
    out+=get_sources("security",q,origin,airline)
    out+=get_sources("customs",q,destination,airline)
    out+=get_sources("item",q,destination,airline)
    out+=get_sources("baggage","",destination,airline)
    if _l(destination)=="cuba" or "cuba" in _l(destination):
        out+=get_sources("cuba","",destination,airline)
    if not out:out+=official_sources("",destination,airline)
    return _dedupe_sources(out)

def _profile(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    return {
        "given_names":_s(d.get("given_names")),
        "surnames":_s(d.get("surnames")),
        "nationality":_s(d.get("nationality")),
        "passport_country":_s(d.get("passport_country")),
        "country_of_residence":_s(d.get("country_of_residence") or d.get("residence_country")),
        "passport_number":_s(d.get("passport_number")),
        "cuban_nationality":_b(d.get("cuban_nationality")),
        "dual_citizen":_b(d.get("dual_citizen")),
        "has_cuban_passport":_b(d.get("has_cuban_passport")),
        "has_other_passport":_b(d.get("has_other_passport")),
        "purpose":_s(d.get("purpose")),
        "arrival_date":_s(d.get("arrival_date")),
        "departure_date":_s(d.get("departure_date")),
        "airline":_s(d.get("airline")),
        "flight_number":_s(d.get("flight_number")),
        "arrival_airport":_s(d.get("arrival_airport")),
        "address_destination":_s(d.get("address_destination")),
        "visa_number":_s(d.get("visa_number") or d.get("evisa_number")),
        "dviajeros_done":_b(d.get("dviajeros_done")),
        "visa_checked":_b(d.get("visa_checked")),
        "customs_checked":_b(d.get("customs_checked")),
        "baggage_checked":_b(d.get("baggage_checked")),
        "documents_checked":_b(d.get("documents_checked"))
    }

def _required(value:Any)->bool:
    return bool(_s(value))

def _step(num:int,title:str,instruction:str,fields:List[str],options:Optional[List[str]]=None,completed:bool=False,reference_image:str="",reference_type:str="",official_step:bool=False)->Dict[str,Any]:
    return {
        "step":num,
        "title":title,
        "instruction":instruction,
        "fields":fields,
        "options":options or [],
        "completed":completed,
        "reference_image":reference_image,
        "reference_type":reference_type,
        "official_step":official_step
    }

def _progress(total:int,completed:int)->float:
    if total<=0:return 0.0
    return round(max(0,min(100,(completed/total)*100)),1)

def _simulation_steps(scenario:str,data:Dict[str,Any])->List[Dict[str,Any]]:
    s=_l(scenario)
    d=data or {}
    if s in ("dviajeros","dviajero","d'viajeros","d viajeros"):
        return [
            _step(1,"Datos personales","Escribe los datos exactamente como aparecen en tu documento de viaje.",["given_names","surnames","birth_date","sex","nationality","passport_number","passport_country"],completed=all(_required(d.get(x)) for x in ["given_names","surnames","birth_date","nationality","passport_number"])),
            _step(2,"Residencia y viaje","Revisa tu país de residencia y el motivo de tu viaje.",["country_of_residence","purpose"],completed=_required(d.get("country_of_residence")) and _required(d.get("purpose"))),
            _step(3,"Vuelo","Coloca los datos de tu viaje cuando ya los tengas.",["airline","flight_number","arrival_date","arrival_airport","departure_airport"],completed=_required(d.get("airline")) and _required(d.get("arrival_date"))),
            _step(4,"Alojamiento","Escribe dónde te alojarás en Cuba.",["accommodation_type","province","municipality","accommodation_name","address_destination"],completed=_required(d.get("address_destination")) or _required(d.get("accommodation_name"))),
            _step(5,"Salud y declaración","Contesta las preguntas oficiales según tu situación real. No adivines.",["medications","health_status","cash_over_5000"],completed=False),
            _step(6,"Revisión","Comprueba que nombres, pasaporte, vuelo y alojamiento coincidan con tus documentos.",["review"],completed=False),
            _step(7,"Sitio oficial","Abre D'Viajeros y completa el formulario real. Esta aplicación no lo presenta ni lo envía por ti.",["official_submission"],completed=False,official_step=True)
        ]
    if s in ("visa","evisa","visa_electronica","visa electrónica"):
        return [
            _step(1,"Pasaporte","Introduce los datos exactamente como aparecen en tu pasaporte.",["given_names","surnames","passport_number","passport_country","birth_date","nationality"],completed=all(_required(d.get(x)) for x in ["given_names","surnames","passport_number","nationality"])),
            _step(2,"Viaje","Prepara motivo y fechas del viaje.",["purpose","arrival_date","departure_date"],completed=_required(d.get("purpose")) and _required(d.get("arrival_date"))),
            _step(3,"Contacto","Utiliza un correo que puedas consultar.",["email","phone"],completed=_required(d.get("email"))),
            _step(4,"Revisión","Comprueba que todos los datos coincidan con tu pasaporte.",["review"],completed=False),
            _step(5,"Proceso oficial","Continúa en la plataforma oficial de e-Visa. Cualquier pago se realiza allí.",["official_submission"],completed=False,official_step=True)
        ]
    if s in ("flight","flights","vuelo","vuelos","booking","flight_search"):
        return [
            _step(1,"Origen y destino","Indica desde dónde quieres salir y confirma Cuba como destino.",["origin","destination"],completed=_required(d.get("origin")) and _required(d.get("destination"))),
            _step(2,"Fecha y pasajeros","Indica la fecha y cuántas personas viajan.",["departure","return_date","passengers"],completed=_required(d.get("departure")) and _n(d.get("passengers"),0)>0),
            _step(3,"Aerolínea o charter","Puedes elegir un proveedor concreto o revisar las opciones oficiales disponibles.",["airline","flight_type"],completed=_required(d.get("airline"))),
            _step(4,"Revisión","Comprueba ruta, fechas, pasajeros, equipaje y condiciones antes de continuar.",["review"],completed=False),
            _step(5,"Sitio oficial","La compra o reserva real se hace directamente con la aerolínea u operador.",["official_booking"],completed=False,official_step=True)
        ]
    return [
        _step(1,"Preparación","Completa la información que corresponda a tu situación.",["data"],completed=False),
        _step(2,"Revisión","Comprueba los datos antes de continuar.",["review"],completed=False),
        _step(3,"Fuente oficial","Comprueba el dato final directamente con la autoridad o proveedor.",["official_source"],completed=False,official_step=True)
    ]

def _simulation_result(scenario:str,data:Dict[str,Any],step:Any=0)->Dict[str,Any]:
    steps=_simulation_steps(scenario,data)
    total=len(steps)
    requested=max(0,min(total-1,_n(step,0)))
    completed=sum(1 for x in steps if x.get("completed"))
    current=steps[requested] if steps else {}
    sources=[]
    s=_l(scenario)
    if "dvia" in s:sources=[_source("dviajeros")]
    elif "visa" in s:sources=[_source("evisa_cuba"),_source("cuba_minrex")]
    elif "flight" in s or "booking" in s:sources=get_airlines()+get_charters()
    else:sources=official_sources("cuba")
    sources=_dedupe_sources(sources)
    return {
        "status":"ok",
        "scenario":scenario,
        "simulation":True,
        "official_submission":False,
        "notice":"Esto es una práctica guiada. No es el formulario oficial y no envía información a la autoridad.",
        "message":current.get("instruction",""),
        "step":requested,
        "progress":_progress(total,completed),
        "current_step":current,
        "steps":steps,
        "next_action":"Completa este paso y continúa." if not current.get("official_step") else "Cuando estés listo, abre el sitio oficial.",
        "sources":sources,
        "missing":[],
        "prefilled":data or {},
        "official_url":official_url("dviajeros" if "dvia" in s else "evisa_cuba" if "visa" in s else ""),
        "total_steps":total,
        "can_go_back":requested>0,
        "can_go_home":True,
        "reference_images":[],
        "version":VERSION
    }

def dviajeros_simulation(data:Dict[str,Any])->Dict[str,Any]:
    return _simulation_result("dviajeros",data,data.get("step",0))

def visa_simulation(data:Dict[str,Any])->Dict[str,Any]:
    return _simulation_result("visa",data,data.get("step",0))

def practice_scenario(data:Dict[str,Any])->Dict[str,Any]:
    return _simulation_result(_s(data.get("scenario") or "dviajeros"),data,_n(data.get("step"),0))

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",_required(d.get("passport_number")),"Ten tu pasaporte disponible y verifica sus datos."),
        ("Nacionalidad","nationality",_required(d.get("nationality")),"Indica la nacionalidad que corresponde a tu caso."),
        ("Fechas","arrival_date",_required(d.get("arrival_date")),"Ten claras las fechas de viaje."),
        ("Vuelo","flight_number",_required(d.get("flight_number")) or _required(d.get("airline")),"Ten el itinerario o los datos de tu vuelo."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba si necesitas visa y el proceso aplicable."),
        ("D'Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa el proceso oficial cuando corresponda.")
    ]
    rows=[{"name":a,"field":b,"ok":c,"message":m} for a,b,c,m in checks]
    pending=[a for a,b,c,m in checks if not c]
    return {
        "status":"complete" if not pending else "incomplete",
        "checks":rows,
        "pending":pending,
        "next_action":pending[0] if pending else "Revisa todo y conserva tus comprobantes oficiales.",
        "sources":_dedupe_sources([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_minrex"),_source("state_cuba")]),
        "version":VERSION
    }

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    airline=_s(d.get("airline"))
    origin=_s(d.get("origin"))
    destination=_s(d.get("destination") or "Cuba")
    fare=_s(d.get("fare"))
    cabin=_s(d.get("cabin"))
    typ=_s(d.get("type") or d.get("baggage_type") or "carry_on")
    names={"carry_on":"Equipaje de mano","checked":"Equipaje facturado","personal":"Artículo personal"}
    src=[]
    if airline:
        a=_airline_source(airline)
        if a:src.append(a)
    src+=_item_sources("",airline,origin,destination)
    src=_dedupe_sources(src)
    msg="La franquicia exacta depende de la aerolínea, ruta, tarifa y condiciones del boleto. No la damos por supuesta."
    if typ in names:msg+=f" Estás consultando: {names[typ]}."
    conditions=[]
    if not airline:conditions.append("Indica la aerolínea antes de tomar una decisión sobre cantidad, peso o dimensiones.")
    if not fare:conditions.append("La tarifa puede cambiar lo que incluye el boleto.")
    if not cabin:conditions.append("La cabina puede afectar las condiciones del equipaje.")
    return {
        "status":"review",
        "type":typ,
        "type_name":names.get(typ,typ),
        "airline":airline,
        "origin":origin,
        "destination":destination,
        "fare":fare,
        "cabin":cabin,
        "message":msg,
        "do_not_assume":["No asumir peso o número de piezas sin revisar el boleto.","No asumir que una regla de TSA sustituye la regla de la aerolínea.","No asumir que una regla de EE.UU. sustituye una regla de Cuba."],
        "conditions":conditions,
        "next_action":"Abre la fuente de la aerolínea y revisa las condiciones de tu itinerario.",
        "sources":src,
        "version":VERSION
    }

def _fallback_item(item:str,airline:str,destination:str)->Dict[str,Any]:
    q=_l(item)
    decision="verify"
    label="🔵 NO SE PUEDE DETERMINAR CON SEGURIDAD"
    category="Consulta específica"
    message="Necesito comprobar la regla aplicable antes de decirte que puedes llevarlo."
    explanation="La respuesta puede depender del artículo exacto, su contenido, cantidad, forma de transporte, control de seguridad, aerolínea y destino."
    conditions=[]
    alternatives=[]
    authority="TSA / aerolínea / autoridad de destino"
    if any(x in q for x in ("arma","explosivo","granada","municion","munición","fuego artificial")):
        decision="red";label="🔴 NO LO LLEVES SIN VERIFICAR";category="Artículo restringido";message="Este tipo de artículo puede estar sujeto a prohibiciones o controles especiales.";explanation="No debe asumirse que puede viajar en equipaje de mano o facturado.";conditions=["Comprueba la regla oficial específica antes de viajar."];authority="TSA y autoridad competente"
    elif any(x in q for x in ("medicamento","medicina","pastilla","medicación","medicacion")):
        decision="yellow";label="🟡 VERIFICA ANTES";category="Medicamento";message="Los medicamentos requieren comprobar las condiciones aplicables.";explanation="Las reglas de seguridad del transporte y las reglas del país de destino pueden ser diferentes.";conditions=["Conserva el medicamento identificado.","Comprueba las reglas del destino y de TSA."];alternatives=["Llévalo en su envase original cuando sea apropiado."];authority="TSA y autoridad de destino"
    elif any(x in q for x in ("bateria","batería","power bank","litio","lithium")):
        decision="yellow";label="🟡 VERIFICA ANTES";category="Batería";message="Las baterías pueden tener reglas específicas según su tipo y capacidad.";explanation="La forma de transporte y las características de la batería importan.";conditions=["Comprueba la capacidad y el tipo de batería.","Revisa la regla vigente de TSA y la aerolínea."];authority="TSA / FAA / aerolínea"
    elif any(x in q for x in ("liquido","líquido","perfume","crema","shampoo","champú")):
        decision="yellow";label="🟡 VERIFICA ANTES";category="Líquido";message="Los líquidos pueden estar sujetos a límites de seguridad y a reglas del destino.";explanation="El tamaño del recipiente, el equipaje y el punto de control pueden cambiar la respuesta.";conditions=["Revisa la regla de líquidos de TSA.","Comprueba además la regla de la aerolínea y Cuba."];authority="TSA / aerolínea / Cuba"
    elif any(x in q for x in ("carne","comida","alimento","queso","fruta","vegetal","semilla","comida")):
        decision="yellow";label="🟡 VERIFICA ANTES";category="Alimento";message="Los alimentos pueden estar sujetos a reglas de seguridad y aduana.";explanation="Que TSA permita un artículo no significa necesariamente que Cuba permita su entrada.";conditions=["Comprueba TSA para el control de salida.","Comprueba Aduana de Cuba para la entrada."];authority="TSA / Aduana de Cuba"
    elif any(x in q for x in ("laptop","computadora","ordenador","tablet","telefono","teléfono","celular","cámara","camara")):
        decision="green";label="🟢 GENERALMENTE POSIBLE";category="Electrónico";message="Los dispositivos electrónicos suelen poder viajar, pero deben pasar los controles correspondientes.";explanation="La autorización concreta puede depender del tipo de dispositivo, batería y reglas del control.";conditions=["Sigue las instrucciones de TSA durante el control.","Comprueba las condiciones de la aerolínea si corresponde."];authority="TSA / aerolínea"
    return {"decision":decision,"decision_label":label,"category":category,"message":message,"explanation":explanation,"conditions":conditions,"alternatives":alternatives,"authority":authority}

def _gemini_prompt(data:Dict[str,Any],sources:List[Dict[str,Any]])->str:
    item=_s(data.get("item"))
    context=[]
    for x in sources[:12]:
        context.append({
            "name":x.get("name",""),
            "publisher":x.get("publisher",""),
            "url":x.get("url",""),
            "covers":x.get("what_it_covers",""),
            "limitations":x.get("limitations","")
        })
    return f"""
Eres un asistente de preparación de viaje para una aplicación independiente llamada ¿QUÉ QUIERES LLEVAR?.
NO eres TSA, CBP, Aduana de Cuba, una aerolínea ni una autoridad.
Analiza solamente el artículo consultado y NO inventes reglas.
Artículo: {item}
Descripción: {_s(data.get("description"))}
Aerolínea: {_s(data.get("airline"))}
Origen: {_s(data.get("origin"))}
Destino: {_s(data.get("destination") or "Cuba")}
Tipo de equipaje: {_s(data.get("baggage_type") or data.get("type"))}
Cantidad: {_s(data.get("quantity"))}
Peso: {_s(data.get("weight"))}
Tamaño: {_s(data.get("size"))}
Contiene batería: {_b(data.get("contains_battery"))}
Contiene líquido: {_b(data.get("contains_liquid"))}
Contiene comida: {_b(data.get("contains_food"))}
Es medicamento: {_b(data.get("is_medication"))}
Es electrónico: {_b(data.get("is_electronic"))}

Fuentes disponibles:
{json.dumps(context,ensure_ascii=False)}

Devuelve SOLO JSON válido con estas claves:
decision: una de green,yellow,red,verify
decision_label: una etiqueta corta en español
category: categoría
message: respuesta humana breve
explanation: por qué
conditions: lista de condiciones concretas
alternatives: lista de alternativas seguras o prácticas
warnings: lista de advertencias
authority: autoridad o proveedor que debe confirmar
confidence: high,medium,low

Reglas:
- green significa que la información disponible permite una orientación generalmente favorable, pero no una garantía.
- yellow significa que depende de una condición que debe comprobarse.
- red significa que existe una prohibición/restricción clara en la información proporcionada.
- verify significa que no hay información suficiente para clasificar.
- Nunca inventes límites de peso, tamaño, cantidad, tarifas, disponibilidad o autorización.
- Nunca digas que una autoridad aprobó el artículo.
- Si hay conflicto o falta información, usa verify o yellow.
- Mantén la respuesta breve y comprensible.
"""

def _gemini_item(data:Dict[str,Any],sources:List[Dict[str,Any]])->Optional[Dict[str,Any]]:
    if not GEMINI_API_KEY:return None
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body={
        "contents":[{"parts":[{"text":_gemini_prompt(data,sources)}]}],
        "generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}
    }
    try:
        req=urllib.request.Request(url,data=json.dumps(body).encode("utf-8"),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=15) as r:
            raw=r.read().decode("utf-8")
        obj=json.loads(raw)
        text=obj.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
        text=re.sub(r"^```(?:json)?\s*|\s*```$","",text.strip(),flags=re.I)
        result=json.loads(text)
        if not isinstance(result,dict):return None
        return result
    except Exception:
        return None

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    item=_s(d.get("item"))
    airline=_s(d.get("airline"))
    destination=_s(d.get("destination") or "Cuba")
    sources=_item_sources(item,airline,_s(d.get("origin")),destination)
    fallback=_fallback_item(item,airline,destination)
    gem=_gemini_item(d,sources)
    result=dict(fallback)
    used=False
    error=False
    if GEMINI_API_KEY:
        used=True
        if gem:
            for k in ("decision","decision_label","category","message","explanation","conditions","alternatives","warnings","authority","confidence"):
                if k in gem and gem[k] not in (None,""):result[k]=gem[k]
        else:error=True
    decision=_l(result.get("decision"))
    if decision not in ("green","yellow","red","verify"):decision="verify"
    result["decision"]=decision
    result["decision_label"]=_s(result.get("decision_label")) or "🔵 NO SE PUEDE DETERMINAR CON SEGURIDAD"
    result["conditions"]=result.get("conditions") if isinstance(result.get("conditions"),list) else []
    result["alternatives"]=result.get("alternatives") if isinstance(result.get("alternatives"),list) else []
    result["warnings"]=result.get("warnings") if isinstance(result.get("warnings"),list) else []
    result["item"]=item
    result["baggage_type"]=_s(d.get("baggage_type") or d.get("type"))
    result["gemini_used"]=used and bool(gem)
    result["gemini_available"]=bool(GEMINI_API_KEY)
    result["gemini_error"]=error
    result["confidence"]=_s(result.get("confidence")) or ("medium" if gem else "low")
    result["final_decision"]=False
    result["official_authority"]=_s(result.get("authority"))
    result["verify_with"]=sources[:6]
    result["next_action"]="Comprueba la fuente oficial indicada antes de viajar."
    result["sources"]=sources
    result["version"]=VERSION
    return result

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    origin=_s(d.get("origin"))
    destination=_s(d.get("destination") or "Cuba")
    airline=_s(d.get("airline"))
    departure=_s(d.get("departure") or d.get("arrival_date"))
    missing=[]
    if not origin:missing.append("origen")
    if not destination:missing.append("destino")
    if not departure:missing.append("fecha")
    providers=[]
    if airline:
        a=_airline_source(airline)
        if a:providers.append(a)
    if not providers:providers=get_airlines()+get_charters()
    providers=_dedupe_sources(providers)
    return {
        "status":"incomplete" if missing else "ok",
        "version":VERSION,
        "message":"Completa los datos que faltan y después revisa el proveedor oficial." if missing else "Datos de búsqueda preparados. La disponibilidad real debe comprobarse en el proveedor.",
        "search":{
            "origin":origin,
            "destination":destination,
            "airline":airline,
            "flight_number":_s(d.get("flight_number")),
            "departure":departure,
            "return_date":_s(d.get("return_date")),
            "passengers":d.get("passengers",1),
            "cabin":_s(d.get("cabin")),
            "fare":_s(d.get("fare")),
            "stops":d.get("stops",0)
        },
        "missing":missing,
        "next_action":"Completa: "+", ".join(missing) if missing else "Abre el proveedor oficial que quieras consultar.",
        "sources":providers,
        "airlines":get_airlines(),
        "charters":get_charters(),
        "official_url":official_url(airline) if airline else "",
        "simulation":True,
        "real_booking":False
    }

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    steps=_simulation_steps("flight",d)
    airline=_s(d.get("airline"))
    src=[]
    if airline:
        a=_airline_source(airline)
        if a:src.append(a)
    else:src=get_airlines()+get_charters()
    return {
        "status":"ok",
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "official_submission":False,
        "notice":"Preparación de vuelo. Esta aplicación no compra, reserva ni cobra el boleto.",
        "message":"Primero prepara la búsqueda y después continúa en el sitio oficial.",
        "search":analyze_flight(d).get("search",{}),
        "fields":["origin","destination","departure","return_date","passengers","airline","flight_type","cabin","fare"],
        "steps":steps,
        "next_action":"Completa el paso actual y revisa el proveedor oficial.",
        "sources":_dedupe_sources(src),
        "official_url":official_url(airline),
        "version":VERSION
    }

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    mins=d.get("connection_minutes")
    warnings=[]
    if mins not in (None,""):
        try:
            if float(mins)<90:warnings.append("La conexión indicada parece corta; confirma el tiempo mínimo aplicable con la aerolínea y el aeropuerto.")
        except Exception:pass
    if _b(d.get("country_change")):warnings.append("Hay cambio de país: comprueba documentos y controles de entrada o tránsito.")
    if _b(d.get("bag_recheck")):warnings.append("Puede ser necesario volver a gestionar el equipaje según el itinerario.")
    return {
        "status":"review",
        "message":"Revisa la conexión directamente con las aerolíneas del itinerario.",
        "warnings":warnings,
        "next_action":"Comprueba terminal, puerta, equipaje y requisitos de tránsito en las fuentes oficiales.",
        "sources":_dedupe_sources([_airline_source(d.get("airline")), _airline_source(d.get("next_airline")), _source("iata_travel")])
    }

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",_required(d.get("passport_number")),"Ten tu pasaporte y verifica su vigencia según tu caso."),
        ("Nacionalidad","nationality",_required(d.get("nationality")),"Indica tu nacionalidad y, si corresponde, tu situación de doble nacionalidad."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba el requisito y proceso de visa aplicable a tu nacionalidad."),
        ("D'Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa o prepara el formulario oficial D'Viajeros."),
        ("Vuelo","airline",_required(d.get("airline")) or _required(d.get("flight_number")),"Ten los datos del vuelo."),
        ("Seguro de viaje","travel_insurance",_b(d.get("travel_insurance")),"Comprueba si el seguro es exigible o recomendable para tu caso y fecha."),
        ("Aduana","customs_checked",_b(d.get("customs_checked")),"Revisa las reglas de Aduana de Cuba para lo que llevas."),
        ("Documentos","documents_checked",_b(d.get("documents_checked")),"Revisa los documentos que correspondan a tu situación.")
    ]
    rows=[{"name":a,"field":b,"ok":c,"message":m} for a,b,c,m in checks]
    pending=[a for a,b,c,m in checks if not c]
    completed=len(checks)-len(pending)
    return {
        "status":"complete" if not pending else "incomplete",
        "profile":_profile(d),
        "checklist":rows,
        "completed":completed,
        "total":len(checks),
        "progress":_progress(len(checks),completed),
        "pending":pending,
        "details":{"note":"Las condiciones oficiales pueden cambiar y pueden depender de nacionalidad, documentación y fecha."},
        "message":"Tu preparación básica está completa." if not pending else "Todavía hay elementos que debes comprobar.",
        "next_action":pending[0] if pending else "Revisa tus comprobantes y conserva tu resumen.",
        "sources":_dedupe_sources([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_aduana"),_source("cuba_minrex"),_source("state_cuba")])
    }

def cuba_entry(data:Dict[str,Any])->Dict[str,Any]:
    result=cuba_check(data)
    result["profile"]["entry_airport"]=_s(data.get("entry_airport"))
    result["profile"]["return_ticket"]=_b(data.get("return_ticket"))
    result["profile"]["travel_insurance"]=_b(data.get("travel_insurance"))
    return result

def build_guide(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=cuba_check(d)
    pending=checks.get("pending",[])
    last=_s(d.get("last_item"))
    if last:
        pending.append("Comprobar artículo: "+last)
    if pending:
        next_action=pending[0]
    else:
        next_action="Puedes revisar tu PDF y continuar con los sitios oficiales."
    guide={
        "title":APP,
        "promise":"Prepararte paso a paso para viajar a Cuba sin tener que adivinar qué hacer.",
        "current_state":_s(d.get("current_state")),
        "next_action":next_action,
        "profile":_profile(d),
        "flight":{
            "origin":_s(d.get("origin")),
            "destination":_s(d.get("destination") or "Cuba"),
            "airline":_s(d.get("airline")),
            "flight_number":_s(d.get("flight_number")),
            "departure":_s(d.get("departure") or d.get("arrival_date")),
            "return_date":_s(d.get("return_date"))
        },
        "items":d.get("items") if isinstance(d.get("items"),list) else [],
        "baggage":d.get("baggage") if isinstance(d.get("baggage"),dict) else {},
        "checklist":checks.get("checklist",[]),
        "practice":d.get("practice") if isinstance(d.get("practice"),dict) else {}
    }
    return {
        "status":"complete" if not pending else "incomplete",
        "guide":guide,
        "pending":pending,
        "next_action":next_action,
        "sources":checks.get("sources",[]),
        "version":VERSION
    }

def solve(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    q=_s(d.get("question"))
    if not q:
        return {"status":"incomplete","message":"Escribe la pregunta que quieres resolver.","next_action":"Escribe una pregunta concreta.","sources":official_sources("cuba")}
    result=item_analysis({"item":q,**d}) if any(x in _l(q) for x in ("llevar","puedo","comida","medic","bateria","batería","liquido","líquido","equipaje","laptop")) else {
        "status":"verify",
        "message":"Para darte una respuesta concreta necesito saber exactamente qué quieres comprobar.",
        "next_action":"Escribe el artículo, documento o parte del viaje que quieres revisar.",
        "sources":answer_sources(q,"",_s(d.get("airline")),_s(d.get("destination") or "Cuba")),
        "version":VERSION
    }
    return result

def answer(data:Dict[str,Any])->Dict[str,Any]:
    return solve(data)

def health()->Dict[str,Any]:
    return {
        "status":"ok",
        "version":VERSION,
        "app":APP,
        "ready":True,
        "free":True,
        "login_required":False,
        "payment_required":False,
        "server_storage":False,
        "gemini_item_assistant":bool(GEMINI_API_KEY)
    }

__all__=[
"VERSION","GEMINI_MODEL","cuba_check","cuba_entry","dviajeros_simulation",
"visa_simulation","practice_scenario","document_analysis","baggage_rules",
"item_analysis","analyze_flight","booking_simulation","connection_analysis",
"build_guide","solve","answer","health"
]
