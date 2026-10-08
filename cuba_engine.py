# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v16.0.0
from __future__ import annotations
import os,json,re,urllib.request,urllib.error
from datetime import datetime
from typing import Any,Dict,List,Optional
from source_registry import source_by_id,get_sources,official_sources,answer_sources,get_airlines,get_charters,official_url

VERSION="16.0.0"
APP="¿QUÉ QUIERES LLEVAR?"
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
TIMEOUT=25

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
    try:return source_by_id(i) or {}
    except Exception:return {}

def _sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    try:return official_sources(topic,country,airline)
    except Exception:return []

def _airline_source(name:str)->Dict[str,Any]:
    name=_s(name)
    if not name:return {}
    try:
        a=get_airlines(name)
        return a[0] if a else {}
    except Exception:return {}

def _charter_source(name:str)->Dict[str,Any]:
    name=_s(name)
    if not name:return {}
    try:
        a=get_charters(name)
        return a[0] if a else {}
    except Exception:return {}

def _dedupe_sources(items:List[Dict[str,Any]])->List[Dict[str,Any]]:
    out=[]
    seen=set()
    for x in items or []:
        if not isinstance(x,dict):continue
        url=_s(x.get("url") or x.get("link"))
        name=_s(x.get("name") or x.get("title"))
        key=_s(x.get("id")) or url or name
        if key and key not in seen:
            seen.add(key)
            out.append(x)
    return out

def _item_sources(item:str="",airline:str="",origin:str="",destination:str="Cuba")->List[Dict[str,Any]]:
    out=[]
    item=_s(item)
    airline=_s(airline)
    origin=_s(origin)
    destination=_s(destination or "Cuba")
    try:
        if airline:
            out+=get_sources("airline","",destination,airline)
        q=f"{item} {origin} {destination}".strip()
        out+=get_sources("item",q,destination,airline)
        out+=get_sources("baggage","",destination,airline)
        if airline:
            out+=get_sources("security",q,origin,airline)
        if "cuba" in _l(destination):
            out+=get_sources("customs",q,destination,airline)
            out+=get_sources("cuba","",destination,airline)
    except Exception:
        pass
    if not out:
        out=_sources("",destination,airline)
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
        "departure_airport":_s(d.get("departure_airport")),
        "address_destination":_s(d.get("address_destination")),
        "visa_number":_s(d.get("visa_number") or d.get("evisa_number")),
        "dviajeros_done":_b(d.get("dviajeros_done")),
        "visa_checked":_b(d.get("visa_checked")),
        "customs_checked":_b(d.get("customs_checked")),
        "baggage_checked":_b(d.get("baggage_checked")),
        "documents_checked":_b(d.get("documents_checked"))
    }

def _required(v:Any)->bool:
    return bool(_s(v))

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
    if total<=0:return 0
    return round(max(0,min(100,completed/total*100)),1)

def _simulation_steps(scenario:str,data:Dict[str,Any])->List[Dict[str,Any]]:
    s=_l(scenario)
    d=data or {}
    if s in ("dviajeros","dviajero","d'viajeros","d viajeros"):
        return [
            _step(1,"Tus datos","Pon tus datos exactamente como aparecen en tu pasaporte.",["given_names","surnames","birth_date","sex","nationality","passport_number","passport_country"],completed=all(_required(d.get(x)) for x in ("given_names","surnames","birth_date","nationality","passport_number"))),
            _step(2,"Tu viaje","Pon los datos que ya tengas de tu viaje.",["country_of_residence","purpose"],completed=_required(d.get("country_of_residence")) and _required(d.get("purpose"))),
            _step(3,"Tu vuelo","Pon los datos del vuelo cuando ya los tengas.",["airline","flight_number","arrival_date","arrival_airport","departure_airport"],completed=_required(d.get("airline")) and _required(d.get("arrival_date"))),
            _step(4,"Dónde te quedarás","Pon el lugar donde te alojarás.",["accommodation_type","province","municipality","accommodation_name","address_destination"],completed=_required(d.get("address_destination")) or _required(d.get("accommodation_name"))),
            _step(5,"Últimas preguntas","Responde cada pregunta según tu situación real.",["medications","health_status","cash_over_5000"],completed=False),
            _step(6,"Revisa","Mira que todo coincida con tus documentos.",["review"],completed=False),
            _step(7,"Formulario oficial","Ahora puedes abrir D’Viajeros y hacerlo allí.",["official_submission"],completed=False,official_step=True)
        ]
    if s in ("visa","evisa","visa_electronica","visa electrónica"):
        return [
            _step(1,"Tu pasaporte","Pon los datos exactamente como aparecen en tu pasaporte.",["given_names","surnames","passport_number","passport_country","birth_date","nationality"],completed=all(_required(d.get(x)) for x in ("given_names","surnames","passport_number","nationality"))),
            _step(2,"Tu viaje","Prepara el motivo y las fechas de tu viaje.",["purpose","arrival_date","departure_date"],completed=_required(d.get("purpose")) and _required(d.get("arrival_date"))),
            _step(3,"Tu contacto","Usa un correo que puedas revisar.",["email","phone"],completed=_required(d.get("email"))),
            _step(4,"Revisa","Comprueba que todo coincida con tu pasaporte.",["review"],completed=False),
            _step(5,"Sitio oficial","Continúa en el sitio oficial de la visa.",["official_submission"],completed=False,official_step=True)
        ]
    if s in ("flight","flights","vuelo","vuelos","booking","flight_search"):
        return [
            _step(1,"De dónde sales","Indica desde dónde quieres salir y tu destino.",["origin","destination"],completed=_required(d.get("origin")) and _required(d.get("destination"))),
            _step(2,"Cuándo viajas","Indica la fecha y cuántas personas viajan.",["departure","return_date","passengers"],completed=_required(d.get("departure")) and _n(d.get("passengers"),0)>0),
            _step(3,"Quién te lleva","Puedes indicar una aerolínea concreta.",["airline","flight_type"],completed=_required(d.get("airline"))),
            _step(4,"Revisa","Comprueba ruta, fechas, personas y lo que incluye tu boleto.",["review"],completed=False),
            _step(5,"Continúa","La compra se hace directamente con el proveedor.",["official_booking"],completed=False,official_step=True)
        ]
    return [
        _step(1,"Prepara","Completa solamente la información que corresponda.",["data"]),
        _step(2,"Revisa","Comprueba tus datos.",["review"]),
        _step(3,"Continúa","Cuando corresponda, abre el sitio oficial.",["official_source"],official_step=True)
    ]

def _simulation_result(scenario:str,data:Dict[str,Any],step:Any=0)->Dict[str,Any]:
    steps=_simulation_steps(scenario,data)
    total=len(steps)
    requested=max(0,min(total-1,_n(step,0)))
    current=steps[requested]
    completed=sum(1 for x in steps if x.get("completed"))
    s=_l(scenario)
    sources=[]
    if "dvia" in s:sources=[_source("dviajeros")]
    elif "visa" in s:sources=[_source("evisa_cuba"),_source("cuba_minrex")]
    elif "flight" in s or "booking" in s:sources=get_airlines()+get_charters()
    else:sources=_sources("cuba")
    sources=_dedupe_sources(sources)
    if "dvia" in s:
        url=official_url("dviajeros")
    elif "visa" in s:
        url=official_url("evisa_cuba")
    else:
        url=""
    return {
        "status":"ok",
        "scenario":scenario,
        "simulation":True,
        "official_submission":False,
        "notice":"Esta es una práctica. El formulario real se completa solamente en el sitio oficial.",
        "message":current.get("instruction",""),
        "step":requested,
        "current_step":current,
        "progress":_progress(total,completed),
        "steps":steps,
        "next_action":"Completa este paso y continúa." if not current.get("official_step") else "Cuando estés listo, abre el sitio oficial.",
        "sources":sources,
        "missing":[],
        "prefilled":data or {},
        "official_url":url,
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
    d=data or {}
    return _simulation_result(_s(d.get("scenario") or "dviajeros"),d,_n(d.get("step"),0))

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",_required(d.get("passport_number")),"Ten tu pasaporte disponible y revisa sus datos."),
        ("Nacionalidad","nationality",_required(d.get("nationality")),"Indica la nacionalidad que corresponde a tu caso."),
        ("Fechas","arrival_date",_required(d.get("arrival_date")),"Ten claras las fechas de tu viaje."),
        ("Vuelo","flight_number",_required(d.get("flight_number")) or _required(d.get("airline")),"Ten los datos de tu vuelo."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba si necesitas visa."),
        ("D’Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa D’Viajeros cuando corresponda.")
    ]
    rows=[{"name":a,"field":b,"ok":c,"message":m} for a,b,c,m in checks]
    pending=[a for a,b,c,m in checks if not c]
    return {
        "status":"complete" if not pending else "incomplete",
        "checks":rows,
        "pending":pending,
        "next_action":pending[0] if pending else "Revisa todo y conserva tus comprobantes.",
        "sources":_dedupe_sources([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_minrex")]),
        "version":VERSION
    }

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    airline=_s(d.get("airline"))
    origin=_s(d.get("origin"))
    destination=_s(d.get("destination") or "Cuba")
    fare=_s(d.get("fare"))
    cabin=_s(d.get("cabin"))
    typ=_s(d.get("type") or d.get("baggage_type") or "unknown")
    names={
        "carry_on":"Lo que llevas contigo",
        "checked":"La maleta que entregas",
        "personal":"El artículo pequeño que llevas contigo",
        "unknown":"Tu equipaje"
    }
    src=[]
    if airline:
        a=_airline_source(airline)
        if a:src.append(a)
    src+=_item_sources("",airline,origin,destination)
    src=_dedupe_sources(src)
    conditions=[]
    if not airline:
        conditions.append("Dinos la aerolínea para comprobar las condiciones de tu viaje.")
    if not fare:
        conditions.append("Si sabes el tipo de boleto, indícalo porque puede cambiar lo que incluye.")
    if not d.get("weight"):
        conditions.append("Si tienes el peso, escríbelo para revisarlo.")
    if not d.get("dimensions"):
        conditions.append("Si tienes las medidas, escríbelas para revisarlas.")
    if not d.get("pieces"):
        conditions.append("Si sabes cuántas piezas llevas, indícalo.")
    return {
        "status":"review",
        "type":typ,
        "type_name":names.get(typ,"Tu equipaje"),
        "airline":airline,
        "origin":origin,
        "destination":destination,
        "fare":fare,
        "cabin":cabin,
        "weight":_s(d.get("weight")),
        "dimensions":_s(d.get("dimensions")),
        "pieces":_s(d.get("pieces")),
        "message":"Vamos a comprobar las condiciones de tu viaje. No vamos a adivinar el peso, las medidas ni la cantidad.",
        "do_not_assume":"No des por hecho el peso, las medidas o la cantidad hasta comprobarlos para tu aerolínea y boleto.",
        "conditions":conditions,
        "next_action":"Completa los datos que conozcas y revisaremos la información disponible.",
        "sources":src,
        "version":VERSION
    }

def _simple_item(item:str)->Dict[str,Any]:
    q=_l(item)
    if not q:
        return {
            "decision":"verify",
            "decision_label":"Dime primero qué quieres llevar.",
            "category":"",
            "message":"Escribe el nombre del artículo y lo comprobamos.",
            "explanation":"",
            "conditions":[],
            "alternatives":[],
            "warnings":[]
        }
    if any(x in q for x in ("arma","explosivo","granada","municion","munición","fuego artificial")):
        return {
            "decision":"red",
            "decision_label":"No lo lleves sin comprobarlo.",
            "category":"Artículo con reglas especiales",
            "message":"Este artículo puede tener restricciones importantes.",
            "explanation":"Necesitamos comprobar la regla exacta antes de decirte cómo llevarlo.",
            "conditions":["No lo prepares todavía.","Vamos a comprobar la información específica."],
            "alternatives":[],
            "warnings":[]
        }
    if any(x in q for x in ("bateria","batería","power bank","litio","lithium")):
        return {
            "decision":"yellow",
            "decision_label":"Sí puede ser posible, pero hay que comprobar un dato.",
            "category":"Batería",
            "message":"La respuesta depende del tipo y capacidad de la batería.",
            "explanation":"Dinos qué batería es y, si aparece, qué capacidad indica.",
            "conditions":["No la coloques todavía en una maleta hasta comprobarla.","Si tienes una foto o los datos de la batería, úsalos para identificarla."],
            "alternatives":[],
            "warnings":[]
        }
    if any(x in q for x in ("liquido","líquido","perfume","crema","shampoo","champú")):
        return {
            "decision":"yellow",
            "decision_label":"Sí puede ser posible, pero necesitamos saber cuál es.",
            "category":"Líquido",
            "message":"El tamaño del envase y el tipo de líquido pueden cambiar la respuesta.",
            "explanation":"Dinos qué líquido es y cuánto contiene el envase.",
            "conditions":["No necesitas aprender ninguna regla.","Nosotros comprobamos la información con los datos que nos des."],
            "alternatives":[],
            "warnings":[]
        }
    if any(x in q for x in ("carne","comida","alimento","queso","fruta","vegetal","semilla","comida")):
        return {
            "decision":"yellow",
            "decision_label":"Hay que comprobarlo antes de viajar.",
            "category":"Comida",
            "message":"La respuesta puede cambiar según el alimento, la cantidad y el destino.",
            "explanation":"Para Cuba importa saber exactamente qué alimento llevas.",
            "conditions":["Dinos qué alimento es.","Si sabes la cantidad, indícala."],
            "alternatives":[],
            "warnings":[]
        }
    if any(x in q for x in ("laptop","computadora","ordenador","tablet","telefono","teléfono","celular","cámara","camara")):
        return {
            "decision":"green",
            "decision_label":"En principio, sí puedes llevarlo.",
            "category":"Dispositivo electrónico",
            "message":"Este tipo de dispositivo normalmente puede viajar contigo.",
            "explanation":"Antes de viajar comprobaremos las condiciones de la aerolínea y del viaje.",
            "conditions":["Tenlo disponible durante el control si te piden mostrarlo.","Si tiene batería especial, comprobaremos también esa batería."],
            "alternatives":[],
            "warnings":[]
        }
    return {
        "decision":"verify",
        "decision_label":"Vamos a comprobarlo antes de decirte que sí.",
        "category":"Artículo",
        "message":"No quiero darte una respuesta inventada.",
        "explanation":"Necesitamos comprobar el artículo exacto y, si corresponde, la aerolínea y el destino.",
        "conditions":[],
        "alternatives":[],
        "warnings":[]
    }

def _gemini_prompt(data:Dict[str,Any],sources:List[Dict[str,Any]])->str:
    d=data or {}
    item=_s(d.get("item"))
    airline=_s(d.get("airline"))
    origin=_s(d.get("origin"))
    destination=_s(d.get("destination") or "Cuba")
    baggage=_s(d.get("baggage_type") or d.get("type"))
    source_text=[]
    for x in sources[:20]:
        if not isinstance(x,dict):continue
        source_text.append({
            "name":_s(x.get("name") or x.get("title")),
            "url":_s(x.get("url")),
            "publisher":_s(x.get("publisher")),
            "covers":_s(x.get("what_it_covers") or x.get("description")),
            "official":x.get("official",True)
        })
    return f"""
You are the item assistant inside the travel preparation application "¿QUÉ QUIERES LLEVAR?".
Your job is to solve the traveler's specific question, not to make the traveler research the rules.

IMPORTANT:
- You are not a government agency, airline, airport, customs office or consulate.
- Never invent a rule.
- Use the airline information when an airline is supplied.
- Use official information available for the destination when destination rules matter.
- If current information cannot be verified, clearly say that it could not be verified.
- Never claim that you personally approved an item.
- Do not give a generic lecture.
- Do not make the traveler study regulations.
- Give the answer first.
- Then give the exact action the traveler should take.
- Ask for only one missing detail at a time when necessary.
- Do not use technical institutional names in the traveler-facing message unless absolutely necessary.
- Do not mention internal source-search instructions.
- Do not mention sanctions, embargoes, legal theory or unrelated political subjects.
- Do not frighten the traveler.

Traveler language: {_s(d.get("language") or "es")}
Item: {item}
Description: {_s(d.get("description"))}
Airline: {airline}
Origin: {origin}
Destination: {destination}
Where traveler wants to carry it: {baggage}
Quantity: {_s(d.get("quantity"))}
Weight: {_s(d.get("weight"))}
Size: {_s(d.get("size"))}
Battery: {_b(d.get("contains_battery"))}
Liquid: {_b(d.get("contains_liquid"))}
Food: {_b(d.get("contains_food"))}
Medicine: {_b(d.get("is_medication"))}
Electronic: {_b(d.get("is_electronic"))}

Available sources:
{json.dumps(source_text,ensure_ascii=False)}

Return ONLY valid JSON:
{{
"decision":"green|yellow|red|verify",
"decision_label":"very short traveler-friendly answer",
"category":"short category",
"message":"direct answer in simple words",
"explanation":"short explanation",
"conditions":["specific action 1","specific action 2"],
"alternatives":["alternative if useful"],
"warnings":["only necessary warning"],
"authority":"source/provider to verify if needed",
"confidence":"high|medium|low"
}}

Decision rules:
green = available information supports a generally favorable answer.
yellow = possible, but a specific condition must be checked.
red = available verified information clearly says not to carry it in that way.
verify = insufficient verified information.

If airline-specific information is available, use it.
If destination-specific information changes the answer, use it.
If sources disagree, do not choose a side without explaining the conflict.
Never invent a weight, size, quantity, capacity, fee, date or permission.
Keep the final answer short enough for a nervous traveler to understand immediately.
"""

def _gemini_item(data:Dict[str,Any],sources:List[Dict[str,Any]])->Optional[Dict[str,Any]]:
    if not GEMINI_API_KEY:return None
    endpoint=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body={
        "contents":[{"role":"user","parts":[{"text":_gemini_prompt(data,sources)}]}],
        "tools":[{"google_search":{}}],
        "generationConfig":{
            "temperature":0.1,
            "responseMimeType":"application/json"
        }
    }
    try:
        req=urllib.request.Request(
            endpoint,
            data=json.dumps(body,ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type":"application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req,timeout=TIMEOUT) as response:
            raw=response.read().decode("utf-8")
        obj=json.loads(raw)
        candidates=obj.get("candidates") or []
        if not candidates:return None
        parts=candidates[0].get("content",{}).get("parts",[])
        text=""
        for p in parts:
            if isinstance(p,dict) and p.get("text"):
                text+=p["text"]
        text=text.strip()
        text=re.sub(r"^```(?:json)?\s*","",text,flags=re.I)
        text=re.sub(r"\s*```$","",text)
        result=json.loads(text)
        if not isinstance(result,dict):return None
        return result
    except Exception:
        return None

def _normalize_list(v:Any)->List[str]:
    if isinstance(v,list):
        return [_s(x) for x in v if _s(x)]
    if _s(v):return [_s(v)]
    return []

def _item_response(data:Dict[str,Any],result:Dict[str,Any],sources:List[Dict[str,Any]],gemini:Optional[Dict[str,Any]],gemini_error:bool)->Dict[str,Any]:
    r=result or {}
    decision=_l(r.get("decision"))
    if decision not in ("green","yellow","red","verify"):
        decision="verify"
    labels={
        "green":"Sí puedes llevarlo.",
        "yellow":"Sí puede ser posible, pero hay que comprobarlo.",
        "red":"No lo lleves de esa manera.",
        "verify":"Vamos a comprobarlo antes de decirte que sí."
    }
    message=_s(r.get("message")) or labels[decision]
    label=_s(r.get("decision_label")) or labels[decision]
    conditions=_normalize_list(r.get("conditions"))
    alternatives=_normalize_list(r.get("alternatives"))
    warnings=_normalize_list(r.get("warnings"))
    authority=_s(r.get("authority"))
    confidence=_s(r.get("confidence")) or ("high" if gemini else "low")
    if not conditions and decision=="green":
        conditions=["Comprueba que el artículo sea exactamente el que describiste."]
    if decision=="verify" and not conditions:
        conditions=["Necesitamos un dato más para comprobarlo."]
    next_action=""
    if decision=="green":
        next_action="Puedes continuar preparando este artículo."
    elif decision=="yellow":
        next_action="Comprueba la condición indicada antes de viajar."
    elif decision=="red":
        next_action="No lo prepares de esa manera. Revisa la alternativa indicada."
    else:
        next_action="Dime el dato que falta y lo comprobamos."
    return {
        "status":"ok",
        "decision":decision,
        "decision_label":label,
        "category":_s(r.get("category")),
        "message":message,
        "explanation":_s(r.get("explanation")),
        "conditions":conditions,
        "alternatives":alternatives,
        "warnings":warnings,
        "official_authority":authority,
        "verify_with":sources[:8],
        "confidence":confidence,
        "final_decision":decision in ("green","red"),
        "next_action":next_action,
        "item":_s(data.get("item")),
        "airline":_s(data.get("airline")),
        "destination":_s(data.get("destination") or "Cuba"),
        "baggage_type":_s(data.get("baggage_type") or data.get("type")),
        "gemini_used":bool(gemini),
        "gemini_available":bool(GEMINI_API_KEY),
        "gemini_error":gemini_error,
        "checked_current_information":bool(gemini),
        "sources":sources,
        "version":VERSION,
        "checked_at":_now()
    }

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    item=_s(d.get("item"))
    if not item:
        return {
            "status":"incomplete",
            "decision":"verify",
            "decision_label":"Dime primero qué quieres llevar.",
            "message":"Escribe el nombre del artículo y lo comprobamos.",
            "explanation":"",
            "conditions":[],
            "alternatives":[],
            "warnings":[],
            "next_action":"Escribe el nombre del artículo.",
            "sources":[],
            "gemini_used":False,
            "gemini_available":bool(GEMINI_API_KEY),
            "version":VERSION
        }
    airline=_s(d.get("airline"))
    origin=_s(d.get("origin"))
    destination=_s(d.get("destination") or "Cuba")
    sources=_item_sources(item,airline,origin,destination)
    base=_simple_item(item)
    gemini=None
    gemini_error=False
    if GEMINI_API_KEY:
        gemini=_gemini_item(d,sources)
        if gemini is None:
            gemini_error=True
    result=dict(base)
    if gemini:
        for key in ("decision","decision_label","category","message","explanation","conditions","alternatives","warnings","authority","confidence"):
            if key in gemini:
                result[key]=gemini[key]
    return _item_response(d,result,sources,gemini,gemini_error)

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    origin=_s(d.get("origin"))
    destination=_s(d.get("destination") or "Cuba")
    airline=_s(d.get("airline"))
    departure=_s(d.get("departure") or d.get("arrival_date"))
    missing=[]
    if not origin:missing.append("origen")
    if not departure:missing.append("fecha")
    providers=[]
    if airline:
        a=_airline_source(airline)
        if a:providers.append(a)
    if not providers:
        providers=get_airlines()+get_charters()
    providers=_dedupe_sources(providers)
    return {
        "status":"incomplete" if missing else "ok",
        "version":VERSION,
        "message":"Completa solamente los datos que faltan." if missing else "La búsqueda está preparada.",
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
        "next_action":"Completa: "+", ".join(missing) if missing else "Continúa con el proveedor que hayas elegido.",
        "sources":providers,
        "airlines":get_airlines(),
        "charters":get_charters(),
        "official_url":official_url(airline) if airline else "",
        "simulation":True,
        "real_booking":False
    }

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    airline=_s(d.get("airline"))
    steps=_simulation_steps("flight",d)
    src=[]
    if airline:
        a=_airline_source(airline)
        if a:src.append(a)
    else:
        src=get_airlines()+get_charters()
    return {
        "status":"ok",
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "official_submission":False,
        "notice":"Esta es una práctica. La compra real se hace directamente con el proveedor.",
        "message":"Prepara tu búsqueda y después continúa directamente con el proveedor.",
        "search":analyze_flight(d).get("search",{}),
        "fields":["origin","destination","departure","return_date","passengers","airline","flight_type","cabin","fare"],
        "steps":steps,
        "next_action":"Completa el paso actual.",
        "sources":_dedupe_sources(src),
        "official_url":official_url(airline) if airline else "",
        "version":VERSION
    }

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    warnings=[]
    mins=d.get("connection_minutes")
    if mins not in (None,""):
        try:
            if float(mins)<90:
                warnings.append("El tiempo entre vuelos puede ser corto. Confirma el tiempo indicado para tu viaje.")
        except Exception:
            pass
    if _b(d.get("country_change")):
        warnings.append("El viaje cambia de país. Comprueba los documentos necesarios antes de salir.")
    if _b(d.get("bag_recheck")):
        warnings.append("Puede ser necesario volver a preparar el equipaje durante la conexión.")
    src=[]
    for x in (_airline_source(d.get("airline")),_airline_source(d.get("next_airline"))):
        if x:src.append(x)
    return {
        "status":"review",
        "message":"Revisa la conexión con los datos de tus vuelos.",
        "warnings":warnings,
        "next_action":"Comprueba dónde debes ir al llegar al primer vuelo y qué debes hacer después.",
        "sources":_dedupe_sources(src),
        "version":VERSION
    }

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",_required(d.get("passport_number")),"Ten tu pasaporte disponible y revisa sus datos."),
        ("Nacionalidad","nationality",_required(d.get("nationality")),"Indica tu nacionalidad."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba si necesitas visa."),
        ("D’Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa D’Viajeros cuando corresponda."),
        ("Vuelo","airline",_required(d.get("airline")) or _required(d.get("flight_number")),"Ten los datos del vuelo."),
        ("Seguro de viaje","travel_insurance",_b(d.get("travel_insurance")),"Comprueba el requisito que corresponda a tu viaje."),
        ("Lo que llevas","customs_checked",_b(d.get("customs_checked")),"Revisa las reglas para los artículos que llevas."),
        ("Documentos","documents_checked",_b(d.get("documents_checked")),"Revisa tus documentos.")
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
        "message":"Tu preparación básica está completa." if not pending else "Todavía hay cosas que debes comprobar.",
        "next_action":pending[0] if pending else "Revisa tus comprobantes y conserva tu resumen.",
        "sources":_dedupe_sources([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_aduana"),_source("cuba_minrex")]),
        "version":VERSION
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
    pending=list(checks.get("pending",[]))
    last=_s(d.get("last_item"))
    if last:pending.append("Comprobar artículo: "+last)
    next_action=pending[0] if pending else "Puedes revisar tu PDF y continuar con los sitios oficiales."
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
        "practice":d.get("practice") if isinstance(d.get("practice"),dict) else []
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
        return {
            "status":"incomplete",
            "message":"Escribe qué quieres comprobar.",
            "next_action":"Escribe el artículo o la pregunta.",
            "sources":_sources("cuba"),
            "version":VERSION
        }
    item_data={**d,"item":d.get("item") or q}
    return item_analysis(item_data)

def answer(data:Dict[str,Any])->Dict[str,Any]:
    return solve(data)

def resolve(data:Dict[str,Any])->Dict[str,Any]:
    return solve(data)

def get_charters_safe(query:str="")->List[Dict[str,Any]]:
    try:return get_charters(query)
    except Exception:return []

def get_official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return _sources(topic,country,airline)

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
        "gemini_item_assistant":bool(GEMINI_API_KEY),
        "gemini_model":GEMINI_MODEL,
        "gemini_search_enabled":bool(GEMINI_API_KEY)
    }

__all__=[
"VERSION","GEMINI_MODEL",
"cuba_check","cuba_entry",
"dviajeros_simulation","visa_simulation",
"practice_scenario","document_analysis",
"baggage_rules","item_analysis",
"analyze_flight","booking_simulation",
"connection_analysis","build_guide",
"solve","answer","resolve","health",
"get_charters_safe","get_official_sources"
]
