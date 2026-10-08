# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v15.0.2
from __future__ import annotations
import os,json,re,urllib.request
from datetime import datetime
from typing import Any,Dict,List,Optional
from source_registry import source_by_id,get_sources,official_sources,answer_sources,get_airlines,get_charters,official_url

VERSION="15.0.2"
APP="¿QUÉ QUIERES LLEVAR?"
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()

def _s(v:Any)->str:return str(v or "").strip()
def _l(v:Any)->str:return _s(v).lower()
def _b(v:Any)->bool:
    if isinstance(v,bool):return v
    return _l(v) in ("1","true","yes","si","sí","y","on")
def _n(v:Any,default:int=0)->int:
    try:return int(v)
    except:return default
def _now()->str:return datetime.utcnow().replace(microsecond=0).isoformat()+"Z"
def _source(i:str)->Dict[str,Any]:return source_by_id(i) or {}
def _sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:return official_sources(topic,country,airline)

def _airline_source(name:str)->Dict[str,Any]:
    a=_s(name)
    if not a:return {}
    x=get_airlines(a)
    return x[0] if x else {}

def _charter_source(name:str)->Dict[str,Any]:
    a=_s(name)
    if not a:return {}
    x=get_charters(a)
    return x[0] if x else {}

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
    if airline:out+=get_sources("airline","",destination,airline)
    q=f"{item} {_s(origin)} {_s(destination)}".strip()
    out+=get_sources("security",q,origin,airline)
    out+=get_sources("customs",q,destination,airline)
    out+=get_sources("item",q,destination,airline)
    out+=get_sources("baggage","",destination,airline)
    if "cuba" in _l(destination):out+=get_sources("cuba","",destination,airline)
    if not out:out+=official_sources("",destination,airline)
    return _dedupe_sources(out)

def _profile(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    return {
        "given_names":_s(d.get("given_names")),"surnames":_s(d.get("surnames")),
        "nationality":_s(d.get("nationality")),"passport_country":_s(d.get("passport_country")),
        "country_of_residence":_s(d.get("country_of_residence") or d.get("residence_country")),
        "passport_number":_s(d.get("passport_number")),
        "cuban_nationality":_b(d.get("cuban_nationality")),"dual_citizen":_b(d.get("dual_citizen")),
        "has_cuban_passport":_b(d.get("has_cuban_passport")),"has_other_passport":_b(d.get("has_other_passport")),
        "purpose":_s(d.get("purpose")),"arrival_date":_s(d.get("arrival_date")),"departure_date":_s(d.get("departure_date")),
        "airline":_s(d.get("airline")),"flight_number":_s(d.get("flight_number")),
        "arrival_airport":_s(d.get("arrival_airport")),"address_destination":_s(d.get("address_destination")),
        "visa_number":_s(d.get("visa_number") or d.get("evisa_number")),
        "dviajeros_done":_b(d.get("dviajeros_done")),"visa_checked":_b(d.get("visa_checked")),
        "customs_checked":_b(d.get("customs_checked")),"baggage_checked":_b(d.get("baggage_checked")),
        "documents_checked":_b(d.get("documents_checked"))
    }

def _required(v:Any)->bool:return bool(_s(v))

def _step(num:int,title:str,instruction:str,fields:List[str],options:Optional[List[str]]=None,completed:bool=False,reference_image:str="",reference_type:str="",official_step:bool=False)->Dict[str,Any]:
    return {"step":num,"title":title,"instruction":instruction,"fields":fields,"options":options or [],"completed":completed,"reference_image":reference_image,"reference_type":reference_type,"official_step":official_step}

def _progress(total:int,completed:int)->float:
    if total<=0:return 0.0
    return round(max(0,min(100,completed/total*100)),1)

def _simulation_steps(scenario:str,data:Dict[str,Any])->List[Dict[str,Any]]:
    s=_l(scenario);d=data or {}
    if s in ("dviajeros","dviajero","d'viajeros","d viajeros"):
        return [
            _step(1,"Datos personales","Escribe los datos exactamente como aparecen en tu documento de viaje.",["given_names","surnames","birth_date","sex","nationality","passport_number","passport_country"],completed=all(_required(d.get(x)) for x in ("given_names","surnames","birth_date","nationality","passport_number"))),
            _step(2,"Residencia y viaje","Indica dónde vives y el motivo de tu viaje.",["country_of_residence","purpose"],completed=_required(d.get("country_of_residence")) and _required(d.get("purpose"))),
            _step(3,"Vuelo","Coloca los datos de tu viaje cuando ya los tengas.",["airline","flight_number","arrival_date","arrival_airport","departure_airport"],completed=_required(d.get("airline")) and _required(d.get("arrival_date"))),
            _step(4,"Alojamiento","Escribe dónde te alojarás en Cuba.",["accommodation_type","province","municipality","accommodation_name","address_destination"],completed=_required(d.get("address_destination")) or _required(d.get("accommodation_name"))),
            _step(5,"Salud y declaración","Contesta las preguntas oficiales según tu situación real. No adivines.",["medications","health_status","cash_over_5000"]),
            _step(6,"Revisión","Comprueba nombres, pasaporte, vuelo y alojamiento.",["review"]),
            _step(7,"Formulario oficial","Abre D'Viajeros y completa el formulario real.",["official_submission"],official_step=True)
        ]
    if s in ("visa","evisa","visa_electronica","visa electrónica"):
        return [
            _step(1,"Pasaporte","Escribe los datos exactamente como aparecen en tu pasaporte.",["given_names","surnames","passport_number","passport_country","birth_date","nationality"],completed=all(_required(d.get(x)) for x in ("given_names","surnames","passport_number","nationality"))),
            _step(2,"Viaje","Prepara el motivo y las fechas.",["purpose","arrival_date","departure_date"],completed=_required(d.get("purpose")) and _required(d.get("arrival_date"))),
            _step(3,"Contacto","Utiliza un correo que puedas consultar.",["email","phone"],completed=_required(d.get("email"))),
            _step(4,"Revisión","Comprueba que los datos coincidan con tu pasaporte.",["review"]),
            _step(5,"Proceso oficial","Continúa en la plataforma oficial de eVisa.",["official_submission"],official_step=True)
        ]
    if s in ("flight","flights","vuelo","vuelos","booking","flight_search"):
        return [
            _step(1,"Origen y destino","Indica desde dónde sales y hacia dónde vas.",["origin","destination"],completed=_required(d.get("origin")) and _required(d.get("destination"))),
            _step(2,"Fecha y pasajeros","Indica la fecha y cuántas personas viajan.",["departure","return_date","passengers"],completed=_required(d.get("departure")) and _n(d.get("passengers"),0)>0),
            _step(3,"Aerolínea o charter","Selecciona una aerolínea u operador para consultar.",["airline","flight_type"],completed=_required(d.get("airline"))),
            _step(4,"Revisión","Comprueba ruta, fechas, pasajeros y equipaje.",["review"]),
            _step(5,"Sitio oficial","La compra real se hace directamente con el proveedor.",["official_booking"],official_step=True)
        ]
    return [
        _step(1,"Preparación","Completa la información que corresponda.",["data"]),
        _step(2,"Revisión","Comprueba los datos antes de continuar.",["review"]),
        _step(3,"Fuente oficial","Comprueba el dato final en la fuente oficial.",["official_source"],official_step=True)
    ]

def _simulation_result(scenario:str,data:Dict[str,Any],step:Any=0)->Dict[str,Any]:
    steps=_simulation_steps(scenario,data)
    total=len(steps);requested=max(0,min(total-1,_n(step,0)))
    completed=sum(1 for x in steps if x.get("completed"));current=steps[requested] if steps else {}
    s=_l(scenario)
    if "dvia" in s:sources=[_source("dviajeros")]
    elif "visa" in s:sources=[_source("evisa_cuba"),_source("cuba_minrex")]
    elif "flight" in s or "booking" in s:sources=get_airlines()+get_charters()
    else:sources=official_sources("cuba")
    return {
        "status":"ok","scenario":scenario,"simulation":True,"official_submission":False,
        "notice":"Esto es una práctica guiada. No es el formulario oficial y no envía información por ti.",
        "message":current.get("instruction",""),"step":requested,"progress":_progress(total,completed),
        "current_step":current,"steps":steps,
        "next_action":"Completa este paso y continúa." if not current.get("official_step") else "Cuando estés listo, abre el sitio oficial.",
        "sources":_dedupe_sources(sources),"missing":[],"prefilled":data or {},
        "official_url":official_url("dviajeros" if "dvia" in s else "evisa_cuba" if "visa" in s else ""),
        "total_steps":total,"can_go_back":requested>0,"can_go_home":True,"reference_images":[],"version":VERSION
    }

def dviajeros_simulation(data:Dict[str,Any])->Dict[str,Any]:return _simulation_result("dviajeros",data,data.get("step",0))
def visa_simulation(data:Dict[str,Any])->Dict[str,Any]:return _simulation_result("visa",data,data.get("step",0))
def practice_scenario(data:Dict[str,Any])->Dict[str,Any]:return _simulation_result(_s(data.get("scenario") or "dviajeros"),data,_n(data.get("step"),0))

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",_required(d.get("passport_number")),"Ten tu pasaporte disponible."),
        ("Nacionalidad","nationality",_required(d.get("nationality")),"Indica tu nacionalidad."),
        ("Fechas","arrival_date",_required(d.get("arrival_date")),"Ten claras las fechas del viaje."),
        ("Vuelo","flight_number",_required(d.get("flight_number")) or _required(d.get("airline")),"Ten los datos del vuelo."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba el proceso de visa que corresponda."),
        ("D'Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa el proceso oficial cuando corresponda.")
    ]
    rows=[{"name":a,"field":b,"ok":c,"message":m} for a,b,c,m in checks]
    pending=[a for a,b,c,m in checks if not c]
    return {"status":"complete" if not pending else "incomplete","checks":rows,"pending":pending,"next_action":pending[0] if pending else "Revisa todo y conserva tus comprobantes.","sources":_dedupe_sources([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_minrex"),_source("state_cuba")]),"version":VERSION}

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};airline=_s(d.get("airline"));origin=_s(d.get("origin"));destination=_s(d.get("destination") or "Cuba")
    fare=_s(d.get("fare"));cabin=_s(d.get("cabin"));typ=_s(d.get("type") or d.get("baggage_type") or "carry_on")
    names={"carry_on":"Equipaje de mano","checked":"Maleta facturada","personal":"Artículo personal"}
    src=[]
    if airline:
        a=_airline_source(airline)
        if a:src.append(a)
    src+=_item_sources("",airline,origin,destination)
    conditions=[]
    if not airline:conditions.append("Indica la aerolínea para comprobar sus condiciones.")
    if not fare:conditions.append("La tarifa puede cambiar lo que incluye el boleto.")
    if not cabin:conditions.append("La cabina puede cambiar las condiciones.")
    return {
        "status":"review","type":typ,"type_name":names.get(typ,typ),"airline":airline,"origin":origin,"destination":destination,"fare":fare,"cabin":cabin,
        "message":f"Estás consultando {names.get(typ,typ)}. El peso, las medidas y la cantidad dependen del boleto y la aerolínea.",
        "do_not_assume":["No asumir peso, medidas o cantidad sin revisar el boleto.","No asumir que una regla de seguridad sustituye la regla de la aerolínea.","No asumir que una regla de salida sustituye una regla de entrada a Cuba."],
        "conditions":conditions,
        "next_action":"Revisa las condiciones oficiales de tu aerolínea y tarifa.",
        "sources":_dedupe_sources(src),"version":VERSION
    }

def _fallback_item(item:str,airline:str,destination:str)->Dict[str,Any]:
    q=_l(item)
    result={"decision":"verify","decision_label":"🔵 NECESITA COMPROBACIÓN","category":"Artículo","message":"Necesito comprobar la regla aplicable antes de decirte que puedes llevarlo.","explanation":"La respuesta puede depender del artículo, cantidad, equipaje, aerolínea y destino.","conditions":[],"alternatives":[],"warnings":[],"authority":"Fuente oficial correspondiente"}
    if any(x in q for x in ("arma","explosivo","granada","municion","munición","fuego artificial")):
        result.update(decision="red",decision_label="🔴 NO LO LLEVES SIN COMPROBAR",category="Artículo restringido",message="Este tipo de artículo puede estar prohibido o tener controles especiales.",explanation="No debe asumirse que puede viajar en ningún tipo de equipaje.",authority="Autoridad de seguridad y proveedor")
    elif any(x in q for x in ("medicamento","medicina","pastilla","medicación","medicacion")):
        result.update(decision="yellow",decision_label="🟡 COMPRUÉBALO ANTES",category="Medicamento",message="Los medicamentos necesitan una comprobación específica.",explanation="Pueden existir reglas diferentes para el control de seguridad y para la entrada al destino.",authority="TSA / autoridad del destino")
    elif any(x in q for x in ("bateria","batería","power bank","litio","lithium")):
        result.update(decision="yellow",decision_label="🟡 COMPRUÉBALO ANTES",category="Batería",message="Las baterías pueden tener condiciones especiales.",explanation="Importan el tipo, capacidad y forma de transportarla.",authority="TSA / FAA / aerolínea")
    elif any(x in q for x in ("liquido","líquido","perfume","crema","shampoo","champú")):
        result.update(decision="yellow",decision_label="🟡 COMPRUÉBALO ANTES",category="Líquido",message="Los líquidos pueden tener límites de seguridad.",explanation="El recipiente, el equipaje y el destino pueden cambiar la respuesta.",authority="TSA / aerolínea / destino")
    elif any(x in q for x in ("carne","comida","alimento","queso","fruta","vegetal","semilla")):
        result.update(decision="yellow",decision_label="🟡 COMPRUÉBALO ANTES",category="Alimento",message="Los alimentos pueden tener reglas de entrada al destino.",explanation="Que algo pueda pasar el control de salida no significa que pueda entrar en Cuba.",authority="TSA / Aduana de Cuba")
    elif any(x in q for x in ("laptop","computadora","ordenador","tablet","telefono","teléfono","celular","camara","cámara")):
        result.update(decision="green",decision_label="🟢 GENERALMENTE SE PUEDE",category="Electrónico",message="Este tipo de dispositivo normalmente puede viajar.",explanation="Debe cumplir las condiciones del control y de la aerolínea.",authority="TSA / aerolínea")
    return result

def _gemini_prompt(data:Dict[str,Any],sources:List[Dict[str,Any]])->str:
    context=[{"name":x.get("name",""),"publisher":x.get("publisher",""),"url":x.get("url",""),"covers":x.get("what_it_covers",""),"limitations":x.get("limitations","")} for x in sources[:12]]
    return f"""Eres un asistente de preparación de viaje.
No eres una autoridad ni una aerolínea.
No inventes reglas.
Artículo: {_s(data.get("item"))}
Descripción: {_s(data.get("description"))}
Aerolínea: {_s(data.get("airline"))}
Origen: {_s(data.get("origin"))}
Destino: {_s(data.get("destination") or "Cuba")}
Equipaje: {_s(data.get("baggage_type") or data.get("type"))}
Cantidad: {_s(data.get("quantity"))}
Peso: {_s(data.get("weight"))}
Tamaño: {_s(data.get("size"))}
Batería: {_b(data.get("contains_battery"))}
Líquido: {_b(data.get("contains_liquid"))}
Comida: {_b(data.get("contains_food"))}
Medicamento: {_b(data.get("is_medication"))}
Fuentes:
{json.dumps(context,ensure_ascii=False)}
Devuelve SOLO JSON válido:
{{"decision":"green|yellow|red|verify","decision_label":"etiqueta corta","category":"categoría","message":"respuesta breve","explanation":"explicación","conditions":[],"alternatives":[],"warnings":[],"authority":"fuente que debe confirmar","confidence":"high|medium|low"}}
Nunca inventes cantidades, pesos, medidas, tarifas, autorizaciones o disponibilidad.
Si falta información usa verify o yellow."""

def _gemini_item(data:Dict[str,Any],sources:List[Dict[str,Any]])->Optional[Dict[str,Any]]:
    if not GEMINI_API_KEY:return None
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body={"contents":[{"parts":[{"text":_gemini_prompt(data,sources)}]}],"generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}}
    try:
        req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=15) as r:obj=json.loads(r.read().decode())
        text=obj.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
        text=re.sub(r"^```(?:json)?\s*|\s*```$","",text.strip(),flags=re.I)
        value=json.loads(text)
        return value if isinstance(value,dict) else None
    except:return None

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};item=_s(d.get("item"));airline=_s(d.get("airline"));destination=_s(d.get("destination") or "Cuba")
    sources=_item_sources(item,airline,_s(d.get("origin")),destination)
    result=_fallback_item(item,airline,destination);gem=_gemini_item(d,sources)
    if gem:
        for k in ("decision","decision_label","category","message","explanation","conditions","alternatives","warnings","authority","confidence"):
            if k in gem and gem[k] not in (None,""):result[k]=gem[k]
    if _l(result.get("decision")) not in ("green","yellow","red","verify"):result["decision"]="verify"
    for k in ("conditions","alternatives","warnings"):
        if not isinstance(result.get(k),list):result[k]=[]
    result.update({
        "item":item,"baggage_type":_s(d.get("baggage_type") or d.get("type")),
        "gemini_used":bool(gem),"gemini_available":bool(GEMINI_API_KEY),
        "confidence":_s(result.get("confidence")) or ("medium" if gem else "low"),
        "final_decision":False,"official_authority":_s(result.get("authority")),
        "verify_with":sources[:6],"next_action":"Comprueba la fuente oficial indicada antes de viajar.",
        "sources":sources,"version":VERSION
    })
    return result

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};origin=_s(d.get("origin"));destination=_s(d.get("destination") or "Cuba");airline=_s(d.get("airline"));departure=_s(d.get("departure") or d.get("arrival_date"))
    missing=[]
    if not origin:missing.append("origen")
    if not destination:missing.append("destino")
    if not departure:missing.append("fecha")
    providers=[]
    if airline:
        a=_airline_source(airline)
        if a:providers.append(a)
    if not providers:providers=get_airlines()+get_charters()
    return {
        "status":"incomplete" if missing else "ok","version":VERSION,
        "message":"Completa los datos que faltan." if missing else "La búsqueda está preparada. La disponibilidad real se comprueba con el proveedor.",
        "search":{"origin":origin,"destination":destination,"airline":airline,"flight_number":_s(d.get("flight_number")),"departure":departure,"return_date":_s(d.get("return_date")),"passengers":d.get("passengers",1),"cabin":_s(d.get("cabin")),"fare":_s(d.get("fare")),"stops":d.get("stops",0)},
        "missing":missing,"next_action":"Completa: "+", ".join(missing) if missing else "Selecciona el proveedor oficial.",
        "sources":_dedupe_sources(providers),"airlines":get_airlines(),"charters":get_charters(),
        "official_url":official_url(airline) if airline else "","simulation":True,"real_booking":False
    }

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};airline=_s(d.get("airline"));src=[]
    if airline:
        a=_airline_source(airline)
        if a:src.append(a)
    else:src=get_airlines()+get_charters()
    return {
        "status":"ok","simulation":True,"real_booking":False,"payment":False,"official_submission":False,
        "notice":"Esta es una práctica. No compra, reserva ni cobra el boleto.",
        "message":"Prepara la búsqueda y después continúa con el proveedor oficial.",
        "search":analyze_flight(d).get("search",{}),
        "fields":["origin","destination","departure","return_date","passengers","airline","flight_type","cabin","fare"],
        "steps":_simulation_steps("flight",d),"next_action":"Completa el paso actual.",
        "sources":_dedupe_sources(src),"official_url":official_url(airline),"version":VERSION
    }

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};warnings=[]
    try:
        if d.get("connection_minutes") not in (None,"") and float(d.get("connection_minutes"))<90:
            warnings.append("La conexión indicada parece corta. Confirma el tiempo necesario con el proveedor.")
    except:pass
    if _b(d.get("country_change")):warnings.append("Hay cambio de país. Comprueba los documentos que puedan pedirte.")
    if _b(d.get("bag_recheck")):warnings.append("Puede ser necesario volver a gestionar el equipaje.")
    src=[]
    for x in (_airline_source(d.get("airline")),_airline_source(d.get("next_airline")),_source("iata_travel")):
        if x:src.append(x)
    return {"status":"review","message":"Revisa la conexión directamente con los proveedores del itinerario.","warnings":warnings,"next_action":"Comprueba terminal, puerta, equipaje y documentos.","sources":_dedupe_sources(src),"version":VERSION}

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",_required(d.get("passport_number")),"Ten tu pasaporte y revisa su vigencia."),
        ("Nacionalidad","nationality",_required(d.get("nationality")),"Indica tu nacionalidad y tu situación de nacionalidad cubana si corresponde."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba el proceso de visa que corresponda."),
        ("D'Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa el formulario oficial cuando corresponda."),
        ("Vuelo","airline",_required(d.get("airline")) or _required(d.get("flight_number")),"Ten los datos de tu vuelo."),
        ("Seguro","travel_insurance",_b(d.get("travel_insurance")),"Comprueba las condiciones que correspondan a tu viaje."),
        ("Aduana","customs_checked",_b(d.get("customs_checked")),"Revisa las reglas para lo que llevas."),
        ("Documentos","documents_checked",_b(d.get("documents_checked")),"Revisa los documentos de tu caso.")
    ]
    rows=[{"name":a,"field":b,"ok":c,"message":m} for a,b,c,m in checks];pending=[a for a,b,c,m in checks if not c]
    return {
        "status":"complete" if not pending else "incomplete","profile":_profile(d),"checklist":rows,
        "completed":len(checks)-len(pending),"total":len(checks),"progress":_progress(len(checks),len(checks)-len(pending)),
        "pending":pending,"message":"Tu preparación básica está completa." if not pending else "Todavía tienes elementos por comprobar.",
        "next_action":pending[0] if pending else "Revisa y conserva tus comprobantes.",
        "sources":_dedupe_sources([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_aduana"),_source("cuba_minrex"),_source("state_cuba")]),
        "version":VERSION
    }

def cuba_entry(data:Dict[str,Any])->Dict[str,Any]:
    r=cuba_check(data);r["profile"]["entry_airport"]=_s(data.get("entry_airport"));r["profile"]["return_ticket"]=_b(data.get("return_ticket"));r["profile"]["travel_insurance"]=_b(data.get("travel_insurance"));return r

def build_guide(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};checks=cuba_check(d);pending=checks.get("pending",[])
    last=_s(d.get("last_item"))
    if last:pending.append("Comprobar artículo: "+last)
    next_action=pending[0] if pending else "Puedes revisar tu PDF y continuar con los sitios oficiales."
    guide={
        "title":APP,"promise":"Prepararte paso a paso para viajar sin tener que adivinar qué hacer.",
        "current_state":_s(d.get("current_state")),"next_action":next_action,"profile":_profile(d),
        "flight":{"origin":_s(d.get("origin")),"destination":_s(d.get("destination") or "Cuba"),"airline":_s(d.get("airline")),"flight_number":_s(d.get("flight_number")),"departure":_s(d.get("departure") or d.get("arrival_date")),"return_date":_s(d.get("return_date"))},
        "items":d.get("items") if isinstance(d.get("items"),list) else [],
        "baggage":d.get("baggage") if isinstance(d.get("baggage"),dict) else {},
        "checklist":checks.get("checklist",[]),"practice":d.get("practice") if isinstance(d.get("practice"),dict) else {}
    }
    return {"status":"complete" if not pending else "incomplete","guide":guide,"pending":pending,"next_action":next_action,"sources":checks.get("sources",[]),"version":VERSION}

def solve(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};q=_s(d.get("question"))
    if not q:return {"status":"incomplete","message":"Escribe la pregunta que quieres resolver.","next_action":"Escribe una pregunta concreta.","sources":official_sources("cuba"),"version":VERSION}
    if any(x in _l(q) for x in ("llevar","puedo","comida","medic","bateria","batería","liquido","líquido","equipaje","laptop")):
        return item_analysis({"item":q,**d})
    return {"status":"verify","message":"Necesito saber exactamente qué quieres comprobar.","next_action":"Escribe el artículo, documento o parte del viaje.","sources":answer_sources(q,"",_s(d.get("airline")),_s(d.get("destination") or "Cuba")),"version":VERSION}

def answer(data:Dict[str,Any])->Dict[str,Any]:return solve(data)

def health()->Dict[str,Any]:
    return {"status":"ok","version":VERSION,"app":APP,"ready":True,"free":True,"login_required":False,"payment_required":False,"server_storage":False,"gemini_item_assistant":bool(GEMINI_API_KEY)}

__all__=["VERSION","GEMINI_MODEL","cuba_check","cuba_entry","dviajeros_simulation","visa_simulation","practice_scenario","document_analysis","baggage_rules","item_analysis","analyze_flight","booking_simulation","connection_analysis","build_guide","solve","answer","health"]
