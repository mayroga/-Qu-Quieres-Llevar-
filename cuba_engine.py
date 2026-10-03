# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v14.0.0
from __future__ import annotations
import json,os,re
from typing import Any,Dict,List,Optional
from source_registry import (
    VERSION as SOURCE_VERSION,FORM_STEPS,process_steps,get_sources,sources_for,
    official_sources,source_by_id,official_url
)

VERSION="14.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
SIM_NOTICE="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
NO_BOOKING="La aplicación no reserva, compra, paga ni envía formularios oficiales."

def _text(v:Any)->str:
    if v is None:return ""
    if isinstance(v,bool):return "sí" if v else "no"
    return str(v).strip()

def _low(v:Any)->str:
    return _text(v).lower()

def _bool(v:Any)->Optional[bool]:
    if v is None:return None
    if isinstance(v,bool):return v
    if isinstance(v,(int,float)):return bool(v)
    x=_low(v)
    if x in {"true","1","yes","y","si","sí","s","on"}:return True
    if x in {"false","0","no","n","off"}:return False
    return None

def _sources(process:str)->List[Dict[str,Any]]:
    return sources_for(process,True)

def _source(source_id:str)->Optional[Dict[str,Any]]:
    return source_by_id(source_id)

def _official(source_id:str)->str:
    return official_url(source_id)

def _base(process:str,title:str="",message:str="")->Dict[str,Any]:
    return {
        "ok":True,"version":VERSION,"process":process,"title":title,
        "message":message,"simulation_notice":SIM_NOTICE,
        "no_booking":NO_BOOKING,"sources":_sources(process)
    }

def _clean_list(v:Any)->List[str]:
    if isinstance(v,list):
        return [_text(x) for x in v if _text(x)]
    if _text(v):return [_text(v)]
    return []

def _merge(data:Dict[str,Any],*names:str)->Dict[str,Any]:
    out={}
    for name in names:
        v=data.get(name)
        if isinstance(v,dict):out.update(v)
    return out

def _step_map(process:str)->List[Dict[str,Any]]:
    return process_steps(process)

def _step_fields(process:str,step_id:str)->List[str]:
    for step in _step_map(process):
        if step.get("id")==step_id:return list(step.get("fields",[]))
    return []

def _completed(data:Dict[str,Any],process:str)->List[str]:
    value=data.get("completed_steps",[])
    if isinstance(value,list):
        return [str(x) for x in value]
    return []

def _progress(process:str,data:Dict[str,Any])->Dict[str,Any]:
    steps=_step_map(process)
    done=set(_completed(data,process))
    total=len(steps)
    count=sum(1 for s in steps if s.get("id") in done)
    current=data.get("step","")
    if current and current not in {s.get("id") for s in steps}:current=""
    return {
        "total_steps":total,
        "completed_steps":count,
        "progress":int(count*100/total) if total else 0,
        "current_step":current or (steps[0]["id"] if steps else ""),
        "steps":steps
    }

def _mark(data:Dict[str,Any],process:str,step:str)->List[str]:
    done=_completed(data,process)
    if step and step not in done:done.append(step)
    return done

def _field_value(data:Dict[str,Any],field:str)->Any:
    if field in data:return data.get(field)
    for group in ("answers","extra","cuba","dviajeros","visa","documents","flight","baggage_data"):
        value=data.get(group)
        if isinstance(value,dict) and field in value:return value.get(field)
    return None

def _has(data:Dict[str,Any],fields:List[str])->bool:
    for field in fields:
        value=_field_value(data,field)
        if value is not None and _text(value):
            if isinstance(value,list) and not value:return False
            return True
    return False

def _missing(data:Dict[str,Any],fields:List[str])->List[str]:
    return [f for f in fields if _field_value(data,f) in (None,"",[])]

def cuba_profile(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    cuban=_bool(d.get("cuban_nationality"))
    if cuban is None:cuban=_bool(d.get("Cuban_nationality"))
    dual=_bool(d.get("dual_nationality"))
    if dual is None:dual=_bool(d.get("dual_citizen"))
    passport_cuba=_bool(d.get("cuban_passport"))
    if passport_cuba is None:passport_cuba=_bool(d.get("Cuban_passport"))
    nationality=_low(d.get("nationality"))
    passport_country=_low(d.get("passport_country") or d.get("passport_issuing_country"))
    if cuban is None:
        cuban=("cuba" in nationality or nationality=="cu")
    if passport_cuba is None:
        passport_cuba=("cuba" in passport_country or passport_country=="cu")
    if dual is None:
        dual=bool(cuban and _text(d.get("nationality")) and "cuba" not in nationality)
    return {
        "nationality":_text(d.get("nationality")),
        "passport_country":_text(d.get("passport_country") or d.get("passport_issuing_country")),
        "residence_country":_text(d.get("residence_country")),
        "cuban_nationality":cuban,
        "dual_nationality":dual,
        "dual_citizen":dual,
        "cuban_passport":passport_cuba,
        "other_passport":_bool(d.get("other_passport")),
    }

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    profile=cuba_profile(d)
    pending=[]
    checks={}
    identity_fields=["nationality","passport_country","residence_country"]
    passport_fields=["passport_number","passport_expiry"]
    flight_fields=["airline","flight_number","arrival_date"]
    checks["identity"]=_has(d,identity_fields)
    checks["passport"]=_has(d,passport_fields)
    checks["flight"]=_has(d,flight_fields)
    checks["purpose"]=bool(_text(d.get("purpose")))
    checks["dviajeros"]=bool(d.get("dviajeros_done"))
    checks["visa"]=bool(d.get("visa_checked"))
    checks["documents"]=bool(d.get("documents_checked"))
    checks["baggage"]=bool(d.get("baggage_checked"))
    checks["customs"]=bool(d.get("customs_checked"))
    if not checks["identity"]:pending.append("Completar tus datos de identidad y nacionalidad.")
    if not checks["passport"]:pending.append("Completar los datos de tu pasaporte.")
    if not checks["flight"]:pending.append("Completar los datos básicos de tu vuelo.")
    if not checks["purpose"]:pending.append("Indicar el motivo del viaje.")
    if not checks["documents"]:pending.append("Revisar los documentos de entrada.")
    if not checks["visa"]:pending.append("Comprobar y preparar la visa si corresponde.")
    if not checks["dviajeros"]:pending.append("Practicar y completar la preparación de D’Viajeros.")
    if not checks["baggage"]:pending.append("Revisar tu equipaje.")
    if not checks["customs"]:pending.append("Revisar la parte de aduana.")
    total=len(checks)
    done=sum(1 for x in checks.values() if x)
    return {
        **_base("cuba","Preparación para Cuba"),
        "profile":profile,"checks":checks,
        "status":"complete" if done==total else "in_progress",
        "progress":int(done*100/total) if total else 0,
        "pending":pending,
        "next_action":pending[0] if pending else "Tu preparación principal está completa. Guarda tu resumen.",
        "sources":_sources("cuba"),
        "official_links":{
            "dviajeros":_official("cuba_dviajeros"),
            "visa":_official("cuba_evisa"),
            "customs":_official("cuba_customs"),
            "minrex":_official("cuba_minrex")
        }
    }

def baggage_type_name(value:str)->str:
    x=_low(value)
    return {
        "carry_on":"Equipaje de mano",
        "cabin":"Equipaje de mano",
        "checked":"Equipaje facturado",
        "personal":"Artículo personal",
        "personal_item":"Artículo personal",
        "special":"Equipaje especial"
    }.get(x,_text(value) or "Equipaje")

def baggage_explanation(data:Dict[str,Any])->str:
    airline=_text(data.get("airline"))
    fare=_text(data.get("fare"))
    cabin=_text(data.get("cabin"))
    if airline and fare:
        return f"Para {airline} y la tarifa {fare}, comprueba directamente las condiciones oficiales antes de comprar o preparar la maleta."
    if airline:
        return f"Las condiciones de equipaje pueden depender de {airline}, la ruta y la tarifa. Compruébalas en la fuente oficial."
    if cabin:
        return f"La cabina seleccionada es {cabin}. La cantidad, peso y dimensiones deben comprobarse con la aerolínea."
    return "La cantidad, peso, dimensiones y costo del equipaje dependen de la aerolínea, ruta y tarifa."

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    return {
        "type":baggage_type_name(d.get("baggage_type")),
        "airline":_text(d.get("airline")),
        "fare":_text(d.get("fare")),
        "cabin":_text(d.get("cabin")),
        "do_not_assume":True,
        "weight":d.get("weight"),
        "dimensions":{
            "length":d.get("length"),
            "width":d.get("width"),
            "height":d.get("height"),
            "unit":_text(d.get("dimensions_unit") or "in")
        },
        "message":baggage_explanation(d),
        "verify_with":["La aerolínea","TSA cuando corresponda","Aduana del destino cuando corresponda"]
    }

def baggage_analysis(data:Dict[str,Any])->Dict[str,Any]:
    result=baggage_rules(data)
    sources=_sources("baggage")
    airline=_text(data.get("airline"))
    airline_url=""
    for s in sources:
        if airline and _low(s["name"])==_low(airline):
            airline_url=s["url"]
            break
    if not airline_url:
        airline_url=_official("tsa_what_can_i_bring")
    return {
        **_base("baggage","Mi equipaje",result["message"]),
        "rules":result,
        "sources":sources,
        "official_url":airline_url,
        "next_action":"Comprueba la regla oficial de tu aerolínea antes de preparar o pagar el equipaje.",
        "pdf_ready":True,
        "pdf_type":"baggage"
    }

def _item_category(item:str)->str:
    x=_low(item)
    groups={
        "battery":["batería","bateria","power bank","powerbank","litio","lithium","vape","vapeador","cigarrillo electrónico","cigarrillo electronico"],
        "chemical":["químico","quimico","bleach","lejía","lejia","pintura","paint","gas","combustible","fuel","aerosol"],
        "liquid":["líquido","liquido","perfume","shampoo","champú","crema","gel"],
        "medication":["medicina","medicamento","medication","medicine","pastilla","pill"],
        "food":["comida","food","carne","meat","queso","cheese","fruta","fruit","vegetal","vegetable"],
        "animal":["animal","mascota","pet","perro","gato","dog","cat"],
        "agricultural":["semilla","seed","planta","plant","tierra","soil"],
        "electronic":["laptop","computadora","tablet","teléfono","telefono","phone","camera","cámara"],
        "general":[]
    }
    for category,words in groups.items():
        if any(w in x for w in words):return category
    return "general"

def _gemini(prompt:str)->Optional[Dict[str,Any]]:
    key=os.getenv("GEMINI_API_KEY","").strip()
    if not key:return None
    try:
        import urllib.request
        model=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        body=json.dumps({
            "contents":[{"parts":[{"text":prompt}]}],
            "generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}
        }).encode()
        req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=json.loads(r.read().decode())
        text=raw["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except Exception:
        return None

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    item=_text(d.get("item") or d.get("item_name"))
    category=_text(d.get("category")) or _item_category(item)
    category_sources={
        "battery":["tsa_batteries","tsa_what_can_i_bring"],
        "chemical":["tsa_what_can_i_bring"],
        "liquid":["tsa_liquids","tsa_what_can_i_bring"],
        "medication":["tsa_medication","tsa_what_can_i_bring"],
        "food":["tsa_what_can_i_bring","cuba_customs"],
        "animal":["cuba_customs"],
        "agricultural":["cuba_customs"],
        "electronic":["tsa_batteries","tsa_what_can_i_bring"],
        "general":["tsa_what_can_i_bring"]
    }
    source_ids=category_sources.get(category,category_sources["general"])
    verify=[x for x in get_sources(ids=source_ids,official_only=True)]
    ai=None
    if item:
        ai=_gemini(
            "Analiza únicamente como apoyo de verificación el siguiente artículo de viaje. "
            "No decidas legalidad ni inventes una regla. Devuelve JSON con category, "
            "questions_to_verify y reason. Artículo: "+item
        )
    return {
        **_base("item","¿Puedo llevar esto?"),
        "item":item,"category":category,
        "decision":"verify_official",
        "final_decision":False,
        "message":"No vamos a darte una autorización inventada. Te mostramos qué debes comprobar y dónde hacerlo oficialmente.",
        "result":{"ai_verification":ai or {}},
        "verify_with":verify,
        "sources":verify,
        "next_action":"Comprueba el artículo en la fuente oficial de la aerolínea, TSA o Aduana según corresponda.",
        "pdf_ready":True,
        "pdf_type":"item"
    }

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    pending=[]
    if not _text(d.get("arrival_airport")):pending.append("Aeropuerto de llegada.")
    if not _text(d.get("departure_airport")):pending.append("Aeropuerto del siguiente vuelo.")
    if d.get("same_ticket") is None:pending.append("Si todos los vuelos están en el mismo boleto.")
    if d.get("baggage_checked") is None:pending.append("Si debes recoger y volver a entregar el equipaje.")
    if d.get("country_change") is None:pending.append("Si cambias de país durante la conexión.")
    return {
        **_base("flight","Conexión"),
        "result":{
            "arrival_airport":_text(d.get("arrival_airport")),
            "departure_airport":_text(d.get("departure_airport")),
            "same_ticket":_bool(d.get("same_ticket")),
            "baggage_checked":_bool(d.get("baggage_checked")),
            "country_change":_bool(d.get("country_change")),
            "terminal_change":_bool(d.get("terminal_change")),
            "connection_time_minutes":d.get("connection_time_minutes")
        },
        "pending":pending,
        "next_action":pending[0] if pending else "Revisa las instrucciones de tu aerolínea y aeropuerto para tu conexión.",
        "sources":_sources("flight")
    }

def _segments(data:Dict[str,Any])->List[Dict[str,Any]]:
    value=data.get("segments")
    if isinstance(value,list) and value:return value
    return [{
        "origin":_text(data.get("origin") or data.get("origin_city")),
        "destination":_text(data.get("destination") or data.get("destination_city")),
        "departure_date":_text(data.get("departure_date")),
        "airline":_text(data.get("airline")),
        "flight_number":_text(data.get("flight_number")),
        "cabin":_text(data.get("cabin")),
        "fare":_text(data.get("fare")),
        "stops":data.get("stops",0)
    }]

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    required={
        "origin":_text(d.get("origin") or d.get("origin_city")),
        "destination":_text(d.get("destination") or d.get("destination_city")),
        "departure_date":_text(d.get("departure_date")),
        "passengers":d.get("passengers") or d.get("adults") or 1
    }
    missing=[k for k,v in required.items() if not _text(v)]
    return {
        **_base("flight","Mi vuelo"),
        "result":{
            **required,
            "return_date":_text(d.get("return_date")),
            "trip_type":_text(d.get("trip_type") or "one_way"),
            "adults":d.get("adults",1),
            "children":d.get("children",0),
            "infants":d.get("infants",0),
            "direct":_bool(d.get("direct")),
            "connections":_bool(d.get("connections")),
            "cabin":_text(d.get("cabin")),
            "airline":_text(d.get("airline")),
            "flight_number":_text(d.get("flight_number")),
            "fare":_text(d.get("fare")),
            "segments":_segments(d)
        },
        "missing":missing,
        "preparation_ready":not missing,
        "next_action":(
            "Revisa los datos y continúa en el sitio oficial de la aerolínea."
            if not missing else
            f"Completa primero: {missing[0]}."
        ),
        "sources":_sources("flight"),
        "official_url":_official("iata"),
        "pdf_ready":not bool(missing),
        "pdf_type":"flight"
    }

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    steps=_step_map("flight")
    current=_text(d.get("step"))
    completed=_completed(d,"flight")
    if current:completed=_mark(d,"flight",current)
    result=analyze_flight(d)
    return {
        **result,
        "process":"booking",
        "title":"Practicar búsqueda de vuelo",
        "simulation_notice":SIM_NOTICE,
        "no_booking":NO_BOOKING,
        "steps":steps,
        "completed_steps":completed,
        "next_action":"Continúa paso a paso. Al terminar podrás abrir el sitio oficial y hacer la compra tú mismo.",
        "official_url":_official("iata")
    }

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    pending=[]
    for field,label in [
        ("nationality","nacionalidad"),
        ("passport_country","país del pasaporte"),
        ("passport_number","número de pasaporte"),
        ("passport_expiry","vigencia del pasaporte"),
        ("origin","origen"),
        ("destination","destino"),
        ("purpose","motivo del viaje")
    ]:
        if not _text(d.get(field)):pending.append(f"Completa {label}.")
    return {
        **_base("documents","Mis documentos"),
        "result":d,
        "pending":pending,
        "requirements":[],
        "next_action":pending[0] if pending else "Comprueba los requisitos oficiales para tu itinerario.",
        "sources":_sources("documents"),
        "pdf_ready":not bool(pending),
        "pdf_type":"documents"
    }

def _simulation_field(field:str,lang:str="es")->Dict[str,Any]:
    labels={
        "first_name":("Nombre","First name","Nombre tal como aparece en el documento."),
        "middle_name":("Segundo nombre","Middle name","Escribe el segundo nombre si aparece."),
        "surname":("Apellido","Surname","Escribe el apellido exactamente como aparece."),
        "second_surname":("Segundo apellido","Second surname","Escribe el segundo apellido si corresponde."),
        "given_names":("Nombres","Given names","Todos los nombres tal como aparecen."),
        "birth_date":("Fecha de nacimiento","Date of birth","Usa la fecha de tu documento."),
        "gender":("Sexo","Sex","Selecciona la opción que corresponda al formulario."),
        "nationality":("Nacionalidad","Nationality","Indica tu nacionalidad."),
        "passport_number":("Número de pasaporte","Passport number","Escríbelo exactamente."),
        "document_issuing_country":("País que emitió el pasaporte","Passport issuing country","País que emitió el documento."),
        "residence_country":("País de residencia","Country of residence","País donde resides actualmente."),
        "email":("Correo electrónico","Email","Usa un correo al que tengas acceso."),
        "phone":("Teléfono","Phone","Número donde puedas recibir comunicaciones."),
        "arrival_date":("Fecha de entrada","Entry date","Fecha prevista de entrada."),
        "flight_number":("Número de vuelo","Flight number","Aparece en tu boleto o reserva."),
        "airline_name":("Aerolínea","Airline","Nombre de la aerolínea."),
        "origin_country":("País de origen","Origin country","País desde el que comienza tu viaje."),
        "traveler_country_origin":("País desde el que viajas","Traveler origin","País desde donde llegas."),
        "travel_reason":("Motivo del viaje","Reason for travel","Selecciona el motivo que corresponda."),
        "visa_number":("Número de visa","Visa number","Escríbelo si ya tienes una visa."),
        "evisa_number":("Número de eVisa","eVisa number","Escríbelo si ya tienes una eVisa."),
        "province":("Provincia","Province","Provincia donde te alojarás."),
        "municipality":("Municipio","Municipality","Municipio donde te alojarás."),
        "accommodation_type":("Tipo de alojamiento","Accommodation type","Selecciona el tipo."),
        "accommodation_place":("Lugar de alojamiento","Accommodation","Nombre del alojamiento."),
        "address":("Dirección","Address","Dirección del alojamiento."),
        "countries_last_15_days":("Países visitados recientemente","Countries visited","Responde según el formulario oficial."),
        "symptoms_last_15_days":("Síntomas","Symptoms","Responde según tu situación."),
        "vaccination":("Vacunación","Vaccination","Responde según corresponda."),
        "cash_currency":("Moneda del efectivo","Cash currency","Indica la moneda."),
        "cash_amount":("Cantidad de efectivo","Cash amount","Indica la cantidad cuando corresponda."),
        "goods_description":("Bienes que declaras","Goods","Describe los bienes cuando corresponda."),
        "truthful_confirmation":("Confirmación","Confirmation","Confirma que revisaste la información.")
    }
    a=labels.get(field,(field.replace("_"," ").title(),field.replace("_"," ").title(),"Completa este dato cuando corresponda."))
    return {
        "id":field,"name":field,"label_es":a[0],"label_en":a[1],
        "type":"text","required":False,
        "explanation_es":a[2],"explanation_en":a[2],
        "options":[],"placeholder_es":"","placeholder_en":"",
        "source_id":"cuba_dviajeros"
    }

def practice_scenario(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    scenario=_low(d.get("scenario"))
    aliases={
        "dviajeros":"dviajeros","d'viajeros":"dviajeros","dviajero":"dviajeros",
        "visa":"visa","evisa":"visa","flight":"flight","vuelo":"flight",
        "baggage":"baggage","equipaje":"baggage","airport":"airport","connection":"connection"
    }
    scenario=aliases.get(scenario,scenario or "airport")
    if scenario not in {"dviajeros","visa","flight","baggage","airport","connection"}:
        scenario="airport"
    steps=_step_map("dviajeros" if scenario=="dviajeros" else "visa" if scenario=="visa" else "flight" if scenario=="flight" else "baggage")
    if scenario=="airport":
        fields=["origin_airport","destination_airport","flight_number"]
    elif scenario=="connection":
        fields=["arrival_airport","departure_airport","same_ticket","baggage_checked","country_change"]
    else:
        index=max(1,int(d.get("step",1)))-1
        index=min(index,len(steps)-1)
        step=steps[index]
        fields=step.get("fields",[])
    specs=[_simulation_field(x,d.get("language","es")) for x in fields]
    current_step=int(d.get("step",1) or 1)
    total=len(steps) if scenario not in {"airport","connection"} else 3
    return {
        **_base(scenario,"Práctica paso a paso"),
        "scenario":scenario,
        "steps":steps,
        "step":current_step,
        "total_steps":total,
        "progress":int(current_step*100/total) if total else 0,
        "current":{
            "id":steps[min(current_step-1,len(steps)-1)].get("id") if steps else "",
            "title":steps[min(current_step-1,len(steps)-1)].get("title") if steps else "",
            "fields":fields,
            "field_specs":specs
        },
        "data":d.get("data",{}),
        "answers":d.get("answers",{}),
        "next_action":"Completa este paso y continúa. Puedes volver atrás sin perder lo escrito.",
        "completed":current_step>=total,
        "official_url":_official("cuba_dviajeros") if scenario=="dviajeros" else _official("cuba_evisa") if scenario=="visa" else "",
        "pdf_ready":current_step>=total,
        "pdf_type":scenario
    }

def dviajeros_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    d["scenario"]="dviajeros"
    result=practice_scenario(d)
    result["title"]="Practicar D’Viajeros"
    result["official_url"]=_official("cuba_dviajeros")
    result["sources"]=_sources("dviajeros")
    result["next_action"]="Al terminar la práctica, revisa todo y luego abre el sitio oficial para hacerlo tú mismo."
    result["pdf_type"]="dviajeros"
    return result

def visa_simulation(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    d["scenario"]="visa"
    result=practice_scenario(d)
    result["title"]="Preparar mi visa"
    result["official_url"]=_official("cuba_evisa")
    result["sources"]=_sources("visa")
    result["next_action"]="Al terminar la preparación, abre el sitio oficial y realiza el proceso allí."
    result["pdf_type"]="visa"
    return result

def build_guide(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    trip=d.get("trip") if isinstance(d.get("trip"),dict) else d
    pending=[]
    required=["origin","destination","nationality","passport_country","airline"]
    for f in required:
        if not _text(trip.get(f)):pending.append(f)
    is_cuba="cuba" in _low(trip.get("destination") or "")
    sections=["flight","baggage","items","documents"]
    if is_cuba:sections+=["cuba","dviajeros","visa","customs"]
    return {
        **_base("guide","Mi guía personal"),
        "result":{
            "sections":sections,
            "trip":trip
        },
        "pending":pending,
        "next_action":pending[0] if pending else "Guarda tu guía y continúa con el siguiente proceso.",
        "pdf_ready":not bool(pending),
        "pdf_type":"guide",
        "sources":_sources("guide")
    }

def create_travel_pdf(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    pdf_type=_text(d.get("pdf_type") or d.get("process") or "guide")
    allowed={"flight","baggage","item","documents","cuba","dviajeros","visa","customs","guide"}
    if pdf_type not in allowed:pdf_type="guide"
    return {
        "ok":True,
        "version":VERSION,
        "pdf_ready":True,
        "pdf_type":pdf_type,
        "title":_text(d.get("title")) or f"Mi preparación — {pdf_type}",
        "message":"Tu resumen puede guardarse o imprimirse.",
        "data":d
    }

def solve(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    process=_low(d.get("process"))
    if process in {"flight","booking"}:return analyze_flight(d)
    if process=="baggage":return baggage_analysis(d)
    if process=="item":return item_analysis(d)
    if process=="cuba":return cuba_check(d)
    if process=="documents":return document_analysis(d)
    if process=="dviajeros":return dviajeros_simulation(d)
    if process in {"visa","evisa"}:return visa_simulation(d)
    if process=="connection":return connection_analysis(d)
    if process=="guide":return build_guide(d)
    return {
        **_base(process or "general","Preparación"),
        "message":"Selecciona qué quieres preparar.",
        "next_action":"Elige un proceso para comenzar."
    }

def answer(data:Dict[str,Any])->Dict[str,Any]:
    return solve(data)

def resolve(data:Dict[str,Any])->Dict[str,Any]:
    return solve(data)

def get_charters()->List[Dict[str,Any]]:
    return get_sources(ids=["xael","aerocuba","cubazul","cuballama_viajes"])

def get_official_sources(process:Optional[str]=None)->List[Dict[str,Any]]:
    return official_sources(process)

__all__=[
"VERSION","APP_NAME","SIM_NOTICE","NO_BOOKING","cuba_profile","cuba_check",
"baggage_type_name","baggage_explanation","baggage_rules","baggage_analysis",
"item_analysis","connection_analysis","analyze_flight","booking_simulation",
"document_analysis","practice_scenario","dviajeros_simulation","visa_simulation",
"build_guide","create_travel_pdf","solve","answer","resolve","get_charters",
"get_official_sources"
]
