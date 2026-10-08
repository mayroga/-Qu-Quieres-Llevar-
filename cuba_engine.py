from __future__ import annotations
import os,json,re,urllib.request
from datetime import datetime
from typing import Any,Dict,List,Optional
from source_registry import source_by_id,get_sources,official_sources,answer_sources,get_airlines,get_charters,official_url

VERSION="16.0.0"
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
def _source(i:str)->Dict[str,Any]:
    try:return source_by_id(i) or {}
    except:return {}
def _sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    try:return official_sources(topic,country,airline)
    except:return []
def _airline_source(name:str)->Dict[str,Any]:
    a=_s(name)
    if not a:return {}
    try:
        x=get_airlines(a)
        return x[0] if x else {}
    except:return {}
def _dedupe(xs:List[Dict[str,Any]])->List[Dict[str,Any]]:
    out=[];seen=set()
    for x in xs or []:
        if not isinstance(x,dict):continue
        i=_s(x.get("id")) or _s(x.get("url"))
        if i and i not in seen:seen.add(i);out.append(x)
    return out

def _item_sources(item:str="",airline:str="",origin:str="",destination:str="Cuba")->List[Dict[str,Any]]:
    out=[]
    try:
        if airline:out+=get_sources("airline","",destination,airline)
        q=f"{item} {_s(origin)} {_s(destination)}".strip()
        out+=get_sources("security",q,origin,airline)
        out+=get_sources("customs",q,destination,airline)
        out+=get_sources("item",q,destination,airline)
        out+=get_sources("baggage","",destination,airline)
        if "cuba" in _l(destination):out+=get_sources("cuba","",destination,airline)
    except:pass
    return _dedupe(out or _sources("",destination,airline))

def _step(n:int,title:str,instruction:str,fields:List[str],data:Dict[str,Any],required:Optional[List[str]]=None,official:bool=False)->Dict[str,Any]:
    req=required or []
    complete=all(_s(data.get(x)) for x in req) if req else False
    return {"step":n,"title":title,"instruction":instruction,"fields":fields,"options":[],"completed":complete,"reference_image":"","reference_type":"","official_step":official}

def _simulation_steps(scenario:str,data:Dict[str,Any])->List[Dict[str,Any]]:
    s=_l(scenario);d=data or {}
    if "dvia" in s:
        return [
            _step(1,"Datos personales","Escribe tus datos exactamente como aparecen en tu documento.",["given_names","surnames","birth_date","nationality","passport_number"],d,["given_names","surnames","birth_date","nationality","passport_number"]),
            _step(2,"Residencia y viaje","Indica dónde resides y el motivo del viaje.",["country_of_residence","purpose"],d,["country_of_residence","purpose"]),
            _step(3,"Vuelo","Coloca los datos de tu vuelo cuando los tengas.",["airline","flight_number","arrival_date","arrival_airport"],d,["airline","arrival_date"]),
            _step(4,"Alojamiento","Indica dónde te alojarás en Cuba.",["province","municipality","accommodation_name","address_destination"],d,["address_destination"]),
            _step(5,"Revisión","Comprueba que los datos coincidan con tus documentos.",["review"],d),
            _step(6,"Sitio oficial","Abre D'Viajeros y completa el formulario real. Esta aplicación no lo envía.",["official_submission"],d,official=True)
        ]
    if "visa" in s:
        return [
            _step(1,"Pasaporte","Usa los datos exactamente como aparecen en tu pasaporte.",["given_names","surnames","passport_number","nationality"],d,["given_names","surnames","passport_number","nationality"]),
            _step(2,"Viaje","Prepara el motivo y las fechas de tu viaje.",["purpose","arrival_date","departure_date"],d,["purpose","arrival_date"]),
            _step(3,"Contacto","Usa un correo electrónico que puedas consultar.",["email","phone"],d,["email"]),
            _step(4,"Revisión","Comprueba que los datos coincidan con tu pasaporte.",["review"],d),
            _step(5,"Proceso oficial","Continúa en el canal oficial que corresponda a tu caso.",["official_submission"],d,official=True)
        ]
    if "flight" in s or "booking" in s:
        return [
            _step(1,"Origen y destino","Indica desde dónde quieres salir y confirma Cuba como destino.",["origin","destination"],d,["origin","destination"]),
            _step(2,"Fecha y pasajeros","Indica la fecha y las personas que viajan.",["departure","return_date","passengers"],d,["departure"]),
            _step(3,"Proveedor","Revisa las aerolíneas y charters disponibles.",["airline","flight_type"],d),
            _step(4,"Revisión","Comprueba ruta, fechas y condiciones.",["review"],d),
            _step(5,"Sitio oficial","La compra o reserva real se hace directamente con el proveedor.",["official_booking"],d,official=True)
        ]
    return [
        _step(1,"Preparación","Completa la información que corresponda.",["data"],d),
        _step(2,"Revisión","Comprueba los datos.",["review"],d),
        _step(3,"Fuente oficial","Comprueba el dato final en el sitio oficial.",["official_source"],d,official=True)
    ]

def _simulation_result(scenario:str,data:Dict[str,Any],step:Any=0)->Dict[str,Any]:
    d=data or {};steps=_simulation_steps(scenario,d);total=len(steps)
    pos=max(0,min(total-1,_n(step)))
    current=steps[pos]
    done=sum(1 for x in steps if x["completed"])
    s=_l(scenario)
    if "dvia" in s:
        sources=[_source("dviajeros")];url=official_url("dviajeros")
    elif "visa" in s:
        sources=[_source("evisa_cuba"),_source("cuba_minrex")];url=official_url("evisa_cuba")
    else:
        sources=get_airlines()+get_charters();url=official_url(_s(d.get("airline"))) if d.get("airline") else ""
    return {
        "status":"ok","scenario":scenario,"simulation":True,"official_submission":False,
        "notice":"Esta es una práctica guiada. No es el formulario oficial y no envía información.",
        "message":current["instruction"],"step":pos,"progress":round(done/total*100,1),
        "current_step":current,"steps":steps,
        "next_action":"Completa este paso y continúa." if not current["official_step"] else "Cuando estés listo, abre el sitio oficial.",
        "sources":_dedupe(sources),"missing":[],"prefilled":d,
        "official_url":url,"total_steps":total,"can_go_back":pos>0,"can_go_home":True,
        "reference_images":[],"version":VERSION
    }

def dviajeros_simulation(data:Dict[str,Any])->Dict[str,Any]:
    return _simulation_result("dviajeros",data,data.get("step",0))
def visa_simulation(data:Dict[str,Any])->Dict[str,Any]:
    return _simulation_result("visa",data,data.get("step",0))
def practice_scenario(data:Dict[str,Any])->Dict[str,Any]:
    return _simulation_result(_s(data.get("scenario") or "dviajeros"),data,_n(data.get("step")))

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",bool(_s(d.get("passport_number"))),"Ten tu pasaporte disponible."),
        ("Nacionalidad","nationality",bool(_s(d.get("nationality"))),"Indica tu nacionalidad."),
        ("Vuelo","flight_number",bool(_s(d.get("flight_number")) or _s(d.get("airline"))),"Ten los datos del vuelo."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba el proceso de visa que corresponde."),
        ("D'Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa el proceso oficial cuando corresponda.")
    ]
    rows=[{"name":a,"field":b,"ok":c,"message":m} for a,b,c,m in checks]
    pending=[a for a,b,c,m in checks if not c]
    return {"status":"complete" if not pending else "incomplete","checks":rows,"pending":pending,"next_action":pending[0] if pending else "Revisa y conserva tus comprobantes.","sources":_dedupe([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_minrex")]),"version":VERSION}

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};airline=_s(d.get("airline"));typ=_s(d.get("type") or d.get("baggage_type") or "carry_on")
    names={"carry_on":"Equipaje de mano","checked":"Equipaje facturado","personal":"Artículo personal"}
    conditions=[]
    if not airline:conditions.append("Primero identifica la aerolínea.")
    if not _s(d.get("fare")):conditions.append("La tarifa puede cambiar lo que incluye el boleto.")
    if not _s(d.get("cabin")):conditions.append("La cabina puede cambiar las condiciones.")
    src=_dedupe(([_airline_source(airline)] if airline else [])+_item_sources("",airline,_s(d.get("origin")),_s(d.get("destination") or "Cuba")))
    return {
        "status":"review","type":typ,"type_name":names.get(typ,typ),"airline":airline,
        "origin":_s(d.get("origin")),"destination":_s(d.get("destination") or "Cuba"),
        "fare":_s(d.get("fare")),"cabin":_s(d.get("cabin")),
        "message":"La cantidad, peso y medidas dependen de la aerolínea, ruta, tarifa y boleto. No se deben suponer.",
        "do_not_assume":["No asumir peso o cantidad sin revisar el boleto.","No asumir que una regla general sustituye la regla de la aerolínea.","No asumir que una regla de salida sustituye una regla de entrada a Cuba."],
        "conditions":conditions,"next_action":"Revisa la condición exacta en el proveedor oficial.","sources":src,"version":VERSION
    }

def _fallback_item(item:str)->Dict[str,Any]:
    q=_l(item)
    if any(x in q for x in ("arma","explosivo","granada","municion","munición","fuego artificial")):
        return {"decision":"red","decision_label":"🔴 NO LO LLEVES SIN VERIFICAR","category":"Artículo restringido","message":"Este artículo puede estar prohibido o sujeto a controles especiales.","explanation":"No se debe asumir que puede viajar en el equipaje.","conditions":["Comprueba la regla oficial específica antes de viajar."],"alternatives":[],"warnings":[],"authority":"Autoridad oficial correspondiente"}
    if any(x in q for x in ("bateria","batería","power bank","litio","lithium")):
        return {"decision":"yellow","decision_label":"🟡 VERIFICA ANTES","category":"Batería","message":"Las baterías pueden tener reglas específicas.","explanation":"El tipo y capacidad de la batería pueden cambiar la respuesta.","conditions":["Comprueba el tipo y capacidad.","Revisa la regla vigente de la aerolínea."],"alternatives":[],"warnings":[],"authority":"Aerolínea y autoridad de seguridad"}
    if any(x in q for x in ("liquido","líquido","perfume","crema","shampoo","champú")):
        return {"decision":"yellow","decision_label":"🟡 VERIFICA ANTES","category":"Líquido","message":"Los líquidos pueden estar sujetos a límites.","explanation":"El recipiente y la forma de transporte pueden cambiar la respuesta.","conditions":["Comprueba la regla vigente antes de viajar."],"alternatives":[],"warnings":[],"authority":"Aerolínea y autoridad de seguridad"}
    if any(x in q for x in ("carne","comida","alimento","queso","fruta","vegetal","semilla")):
        return {"decision":"yellow","decision_label":"🟡 VERIFICA ANTES","category":"Alimento","message":"Los alimentos pueden tener reglas distintas para seguridad y entrada a Cuba.","explanation":"Que algo pueda pasar el control de salida no significa que pueda entrar en Cuba.","conditions":["Comprueba las reglas de entrada a Cuba."],"alternatives":[],"warnings":[],"authority":"Autoridad de entrada a Cuba"}
    if any(x in q for x in ("laptop","computadora","ordenador","tablet","telefono","teléfono","celular","camara","cámara")):
        return {"decision":"green","decision_label":"🟢 GENERALMENTE POSIBLE","category":"Electrónico","message":"Los dispositivos electrónicos generalmente pueden viajar.","explanation":"Pueden estar sujetos a controles durante el viaje.","conditions":["Sigue las instrucciones del control y de la aerolínea."],"alternatives":[],"warnings":[],"authority":"Aerolínea y autoridad de seguridad"}
    return {"decision":"verify","decision_label":"🔵 HAY QUE COMPROBARLO","category":"Consulta específica","message":"No sería responsable decirte que puedes llevarlo sin comprobar el artículo exacto.","explanation":"La respuesta puede depender del artículo, contenido, cantidad, equipaje, aerolínea y destino.","conditions":["Comprueba la regla oficial específica antes de viajar."],"alternatives":[],"warnings":[],"authority":"Proveedor o autoridad oficial"}

def _gemini_prompt(d:Dict[str,Any],sources:List[Dict[str,Any]])->str:
    src=[{"name":x.get("name",""),"publisher":x.get("publisher",""),"url":x.get("url",""),"covers":x.get("what_it_covers","")} for x in sources[:12]]
    return f"""Eres un asistente independiente de preparación de viaje.
No eres una autoridad. No inventes reglas.
Artículo: {_s(d.get("item"))}
Descripción: {_s(d.get("description"))}
Aerolínea: {_s(d.get("airline"))}
Origen: {_s(d.get("origin"))}
Destino: {_s(d.get("destination") or "Cuba")}
Equipaje: {_s(d.get("baggage_type") or d.get("type"))}
Cantidad: {_s(d.get("quantity"))}
Peso: {_s(d.get("weight"))}
Tamaño: {_s(d.get("size"))}
Fuentes: {json.dumps(src,ensure_ascii=False)}
Devuelve SOLO JSON válido:
decision: green,yellow,red,verify
decision_label: etiqueta breve en español
category: categoría
message: respuesta breve
explanation: explicación
conditions: lista
alternatives: lista
warnings: lista
authority: quién debe confirmar
confidence: high,medium,low
Nunca inventes límites, cantidades, pesos, medidas, precios o autorizaciones.
Si falta información usa verify o yellow.
"""

def _gemini_item(d:Dict[str,Any],sources:List[Dict[str,Any]])->Optional[Dict[str,Any]]:
    if not GEMINI_API_KEY:return None
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    body={"contents":[{"parts":[{"text":_gemini_prompt(d,sources)}]}],"generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}}
    try:
        req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=15) as r:obj=json.loads(r.read().decode())
        txt=obj.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
        txt=re.sub(r"^```(?:json)?\s*|\s*```$","",txt.strip(),flags=re.I)
        x=json.loads(txt)
        return x if isinstance(x,dict) else None
    except:return None

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};item=_s(d.get("item"));airline=_s(d.get("airline"));destination=_s(d.get("destination") or "Cuba")
    sources=_item_sources(item,airline,_s(d.get("origin")),destination)
    result=_fallback_item(item);gem=_gemini_item(d,sources)
    if gem:
        for k in ("decision","decision_label","category","message","explanation","conditions","alternatives","warnings","authority","confidence"):
            if k in gem and gem[k] not in (None,""):result[k]=gem[k]
    result["decision"]=result.get("decision") if result.get("decision") in ("green","yellow","red","verify") else "verify"
    for k in ("conditions","alternatives","warnings"):
        if not isinstance(result.get(k),list):result[k]=[]
    result.update({"status":"ok","item":item,"baggage_type":_s(d.get("baggage_type") or d.get("type")),"gemini_used":bool(gem),"gemini_available":bool(GEMINI_API_KEY),"gemini_error":bool(GEMINI_API_KEY and not gem),"confidence":_s(result.get("confidence")) or ("medium" if gem else "low"),"final_decision":False,"official_authority":_s(result.get("authority")),"verify_with":sources[:8],"next_action":"Comprueba la fuente oficial indicada antes de viajar.","sources":sources,"version":VERSION})
    return result

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};origin=_s(d.get("origin"));destination=_s(d.get("destination") or "Cuba");airline=_s(d.get("airline"));departure=_s(d.get("departure") or d.get("arrival_date"))
    missing=[]
    if not origin:missing.append("origen")
    if not departure:missing.append("fecha")
    providers=[_airline_source(airline)] if airline else get_airlines()+get_charters()
    providers=_dedupe([x for x in providers if x])
    return {
        "status":"incomplete" if missing else "ok","version":VERSION,
        "message":"Completa los datos que faltan." if missing else "Búsqueda preparada. Comprueba la disponibilidad en el proveedor oficial.",
        "search":{"origin":origin,"destination":destination,"airline":airline,"flight_number":_s(d.get("flight_number")),"departure":departure,"return_date":_s(d.get("return_date")),"passengers":d.get("passengers",1),"cabin":_s(d.get("cabin")),"fare":_s(d.get("fare")),"stops":d.get("stops",0)},
        "missing":missing,"next_action":"Completa: "+", ".join(missing) if missing else "Abre el proveedor oficial.",
        "sources":providers,"airlines":get_airlines(),"charters":get_charters(),
        "official_url":official_url(airline) if airline else "","simulation":True,"real_booking":False
    }

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};airline=_s(d.get("airline"))
    return {"status":"ok","simulation":True,"real_booking":False,"payment":False,"official_submission":False,"notice":"Preparación de vuelo. Esta aplicación no compra, reserva ni cobra el boleto.","message":"Prepara la búsqueda y continúa en el proveedor oficial.","search":analyze_flight(d)["search"],"fields":["origin","destination","departure","return_date","passengers","airline","flight_type","cabin","fare"],"steps":_simulation_steps("flight",d),"next_action":"Completa el paso actual y revisa el proveedor oficial.","sources":_dedupe([_airline_source(airline)] if airline else get_airlines()+get_charters()),"official_url":official_url(airline) if airline else "","version":VERSION}

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};warnings=[]
    try:
        if d.get("connection_minutes") not in (None,"") and float(d["connection_minutes"])<90:warnings.append("Confirma con la aerolínea que el tiempo de conexión sea suficiente.")
    except:pass
    if _b(d.get("country_change")):warnings.append("Comprueba los requisitos del país de tránsito.")
    if _b(d.get("bag_recheck")):warnings.append("Comprueba si debes volver a entregar el equipaje.")
    return {"status":"review","message":"Revisa la conexión directamente con las aerolíneas del itinerario.","warnings":warnings,"next_action":"Comprueba terminal, puerta, equipaje y tránsito.","sources":_dedupe([_airline_source(d.get("airline")),_airline_source(d.get("next_airline"))])}

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {}
    checks=[
        ("Pasaporte","passport_number",_s(d.get("passport_number")),"Ten tu pasaporte disponible."),
        ("Nacionalidad","nationality",_s(d.get("nationality")),"Indica tu nacionalidad."),
        ("Visa","visa_checked",_b(d.get("visa_checked")),"Comprueba el proceso que corresponde a tu caso."),
        ("D'Viajeros","dviajeros_done",_b(d.get("dviajeros_done")),"Completa el proceso oficial."),
        ("Vuelo","airline",_s(d.get("airline")) or _s(d.get("flight_number")),"Ten los datos de tu vuelo."),
        ("Documentos","documents_checked",_b(d.get("documents_checked")),"Revisa los documentos que correspondan.")
    ]
    rows=[{"name":a,"field":b,"ok":bool(c),"message":m} for a,b,c,m in checks]
    pending=[a for a,b,c,m in checks if not c]
    return {"status":"complete" if not pending else "incomplete","checklist":rows,"completed":len(rows)-len(pending),"total":len(rows),"progress":round((len(rows)-len(pending))/len(rows)*100,1),"pending":pending,"message":"Tu preparación básica está completa." if not pending else "Todavía hay elementos que debes comprobar.","next_action":pending[0] if pending else "Revisa y conserva tus comprobantes.","sources":_dedupe([_source("dviajeros"),_source("evisa_cuba"),_source("cuba_aduana"),_source("cuba_minrex")]),"version":VERSION}

def cuba_entry(data:Dict[str,Any])->Dict[str,Any]:
    return cuba_check(data)

def build_guide(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};c=cuba_check(d);pending=c["pending"][:]
    if _s(d.get("last_item")):pending.append("Comprobar artículo: "+_s(d["last_item"]))
    return {"status":"complete" if not pending else "incomplete","guide":{"title":APP,"promise":"Preparación sencilla para viajar a Cuba.","flight":{"origin":_s(d.get("origin")),"destination":_s(d.get("destination") or "Cuba"),"airline":_s(d.get("airline")),"flight_number":_s(d.get("flight_number")),"departure":_s(d.get("departure"))},"checklist":c["checklist"],"items":d.get("items",[]) if isinstance(d.get("items"),list) else [],"baggage":d.get("baggage",{}) if isinstance(d.get("baggage"),dict) else {},"practice":d.get("practice",{}) if isinstance(d.get("practice"),dict) else {}}, "pending":pending,"next_action":pending[0] if pending else "Puedes revisar tu PDF y continuar con los sitios oficiales.","sources":c["sources"],"version":VERSION}

def solve(data:Dict[str,Any])->Dict[str,Any]:
    d=data or {};q=_s(d.get("question"))
    if not q:return {"status":"incomplete","message":"Escribe la pregunta que quieres resolver.","next_action":"Escribe una pregunta concreta.","sources":_sources("cuba"),"version":VERSION}
    return item_analysis({"item":q,**d}) if any(x in _l(q) for x in ("llevar","puedo","comida","medic","bateria","batería","liquido","líquido","equipaje","laptop")) else {"status":"verify","message":"Necesito saber exactamente qué quieres comprobar.","next_action":"Escribe el artículo, documento o parte del viaje.","sources":answer_sources(q,"",_s(d.get("airline")),_s(d.get("destination") or "Cuba")),"version":VERSION}

def answer(data:Dict[str,Any])->Dict[str,Any]:return solve(data)
def health()->Dict[str,Any]:
    return {"status":"ok","version":VERSION,"app":APP,"ready":True,"free":True,"login_required":False,"payment_required":False,"server_storage":False,"gemini_item_assistant":bool(GEMINI_API_KEY)}

__all__=["VERSION","GEMINI_MODEL","cuba_check","cuba_entry","dviajeros_simulation","visa_simulation","practice_scenario","document_analysis","baggage_rules","item_analysis","analyze_flight","booking_simulation","connection_analysis","build_guide","solve","answer","health"]
