# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v14.0.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional

VERSION="14.0.0"
VERIFICATION_DATE="2026-10-03"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
OFFICIAL_ONLY=True

@dataclass(frozen=True)
class Source:
    id:str
    name:str
    url:str
    category:str
    country:str="US"
    official:bool=True
    description:str=""
    language:str="EN"
    process:str=""
    verified:str=VERIFICATION_DATE

def S(id,name,url,category,country="US",description="",language="EN",process="",official=True):
    return Source(id,name,url,category,country,official,description,language,process)

SOURCES=[
S("tsa","TSA","https://www.tsa.gov/","security","US","Transportation Security Administration.","EN","security"),
S("tsa_what_can_i_bring","TSA — What Can I Bring?","https://www.tsa.gov/travel/security-screening/whatcanibring/all","baggage","US","Official TSA baggage and screening reference.","EN","baggage"),
S("tsa_liquids","TSA — Liquids","https://www.tsa.gov/travel/security-screening/whatcanibring/all","baggage","US","Official TSA liquids and screening information.","EN","baggage"),
S("tsa_medication","TSA — Medication","https://www.tsa.gov/travel/security-screening/whatcanibring/medications","baggage","US","Official TSA medication information.","EN","baggage"),
S("tsa_batteries","TSA — Batteries","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=batteries","baggage","US","Official TSA battery guidance.","EN","baggage"),
S("tsa_travel_checklist","TSA — Travel Checklist","https://www.tsa.gov/travel/travel-tips/travel-checklist","travel","US","Official TSA preparation checklist.","EN","travel"),
S("faa","FAA","https://www.faa.gov/","aviation","US","Federal Aviation Administration.","EN","flight"),
S("cbp","U.S. Customs and Border Protection","https://www.cbp.gov/","border","US","Official U.S. border and customs information.","EN","documents"),
S("cbp_travelers","CBP — For International Travelers","https://www.cbp.gov/travel/international-visitors","border","US","Official information for international travelers.","EN","documents"),
S("travel_state","U.S. Department of State","https://travel.state.gov/","government","US","Official U.S. Department of State travel information.","EN","documents"),
S("travel_state_cuba","U.S. Department of State — Cuba","https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html","government","CU","Official U.S. government Cuba travel information.","EN","cuba"),
S("iata","IATA","https://www.iata.org/","aviation","INT","International Air Transport Association.","EN","flight"),
S("iata_travel_centre","IATA Travel Centre","https://www.iata.org/en/travel-centre/","travel_requirements","INT","Passport, visa and health requirement information based on itinerary and traveler details.","EN","documents"),
S("iata_timatic","IATA Timatic","https://www.iata.org/timatic","travel_requirements","INT","International travel document requirement reference used by the aviation industry.","EN","documents"),
S("icao","ICAO","https://www.icao.int/","aviation","INT","International Civil Aviation Organization.","EN","flight"),

S("cuba_dviajeros","D'Viajeros — Gobierno de Cuba","https://dviajeros.mitrans.gob.cu/","official_form","CU","Portal oficial para la declaración del viajero.","ES/EN","dviajeros"),
S("cuba_evisa","Cuba eVisa — Gobierno de Cuba","https://evisacuba.cu/","official_form","CU","Portal oficial relacionado con la visa electrónica cubana.","ES/EN","visa"),
S("cuba_customs","Aduana General de la República de Cuba","https://www.aduana.gob.cu/","customs","CU","Fuente oficial de Aduana de Cuba.","ES","customs"),
S("cuba_mitrans","MITRANS — Cuba","https://www.mitrans.gob.cu/","government","CU","Ministerio de Transporte de Cuba.","ES","cuba"),
S("cuba_minrex","MINREX — Cuba","https://www.minrex.gob.cu/","government","CU","Ministerio de Relaciones Exteriores de Cuba.","ES","visa"),
S("cuba_minsap","MINSAP — Cuba","https://salud.msp.gob.cu/","health","CU","Ministerio de Salud Pública de Cuba.","ES","health"),

S("american","American Airlines","https://www.aa.com/","airline","US","Official American Airlines website.","EN","flight"),
S("delta","Delta Air Lines","https://www.delta.com/","airline","US","Official Delta website.","EN","flight"),
S("united","United Airlines","https://www.united.com/","airline","US","Official United Airlines website.","EN","flight"),
S("southwest","Southwest Airlines","https://www.southwest.com/","airline","US","Official Southwest website.","EN","flight"),
S("jetblue","JetBlue","https://www.jetblue.com/","airline","US","Official JetBlue website.","EN","flight"),
S("spirit","Spirit Airlines","https://www.spirit.com/","airline","US","Official Spirit website.","EN","flight"),
S("frontier","Frontier Airlines","https://www.flyfrontier.com/","airline","US","Official Frontier website.","EN","flight"),
S("copa","Copa Airlines","https://www.copaair.com/","airline","PA","Official Copa Airlines website.","ES/EN","flight"),
S("avianca","Avianca","https://www.avianca.com/","airline","CO","Official Avianca website.","ES/EN","flight"),
S("latam","LATAM Airlines","https://www.latam.com/","airline","CL","Official LATAM website.","ES/EN","flight"),
S("aeromexico","Aeromexico","https://www.aeromexico.com/","airline","MX","Official Aeromexico website.","ES/EN","flight"),
S("volaris","Volaris","https://www.volaris.com/","airline","MX","Official Volaris website.","ES/EN","flight"),
S("viva","Viva","https://www.vivaaerobus.com/","airline","MX","Official Viva Aerobus website.","ES/EN","flight"),

S("xael","Xael Charters","https://www.xaelcharter.com/","charter","US","Official charter source when applicable.","EN","flight"),
S("aerocuba","Aerocuba","https://www.aerocuba.com/","charter","US","Charter information source when applicable.","EN","flight"),
S("cubazul","Cubazul","https://www.cubazulairlines.com/","charter","CU","Charter information source when applicable.","ES/EN","flight"),
S("cuballama_viajes","Cuballama Viajes","https://www.cuballama.com/","travel","US","Travel information source; verify official airline/provider details before action.","ES/EN","flight",False),

S("destination_mexico","Gobierno de México","https://www.gob.mx/","destination","MX","Official government information.","ES","documents"),
S("destination_guatemala","Gobierno de Guatemala","https://www.gob.gt/","destination","GT","Official government information.","ES","documents"),
S("destination_honduras","Gobierno de Honduras","https://www.gob.hn/","destination","HN","Official government information.","ES","documents"),
S("destination_elsalvador","Gobierno de El Salvador","https://www.presidencia.gob.sv/","destination","SV","Official government information.","ES","documents"),
S("destination_dominican_republic","Gobierno de República Dominicana","https://www.gob.do/","destination","DO","Official government information.","ES","documents"),
]

AIRLINE_IDS=[
"american","delta","united","southwest","jetblue","spirit","frontier",
"copa","avianca","latam","aeromexico","volaris","viva"
]

CHARTER_IDS=["xael","aerocuba","cubazul","cuballama_viajes"]

PROCESS_SOURCE_IDS={
"flight":["iata","faa"]+AIRLINE_IDS+CHARTER_IDS,
"booking":["iata"]+AIRLINE_IDS+CHARTER_IDS,
"baggage":["tsa_what_can_i_bring","tsa_liquids","tsa_medication","tsa_batteries"]+AIRLINE_IDS,
"item":["tsa_what_can_i_bring","tsa_liquids","tsa_medication","tsa_batteries","cuba_customs"],
"documents":["iata_travel_centre","iata_timatic","travel_state","cbp"],
"cuba":["cuba_mitrans","cuba_minrex","cuba_customs","cuba_dviajeros","cuba_evisa","cuba_minsap","iata_travel_centre"],
"dviajeros":["cuba_dviajeros","cuba_mitrans","cuba_customs","cuba_minsap"],
"visa":["cuba_evisa","cuba_minrex","iata_travel_centre"],
"customs":["cuba_customs","cbp"],
"health":["cuba_minsap","iata_travel_centre"],
"security":["tsa","tsa_what_can_i_bring"],
"practice":["cuba_dviajeros","cuba_evisa","iata_travel_centre"],
"guide":["iata_travel_centre","tsa_what_can_i_bring","cuba_dviajeros","cuba_evisa","cuba_customs"]
}

# Los pasos representan la experiencia de preparación de la app.
# No sustituyen los campos reales del portal oficial: sirven para que
# index.html/main.py/cuba_engine.py mantengan el mismo recorrido.
FORM_STEPS={
"flight":[
{"id":"origin","title":"¿Desde dónde viajas?","fields":["origin_country","origin_city","origin_airport","origin_iata"]},
{"id":"destination","title":"¿A dónde vas?","fields":["destination_country","destination_city","destination_airport","destination_iata"]},
{"id":"dates","title":"¿Cuándo viajas?","fields":["trip_type","departure_date","return_date"]},
{"id":"travelers","title":"¿Cuántas personas viajan?","fields":["adults","children","infants"]},
{"id":"flight_type","title":"¿Cómo quieres viajar?","fields":["direct","connections","unknown","cabin"]},
{"id":"airline","title":"¿Con qué aerolínea?","fields":["airline","flight_number","fare","baggage"]},
{"id":"review","title":"Revisa antes de continuar","fields":["origin","destination","dates","travelers","airline","flight_number"]},
{"id":"official","title":"Hazlo en el sitio oficial","fields":["official_airline_url"]},
{"id":"result","title":"Guarda tu preparación","fields":["pdf","summary","next_action"]}
],
"existing_flight":[
{"id":"ticket","title":"Ya tengo mi vuelo","fields":["airline","flight_number","origin","destination","departure_date","return_date"]},
{"id":"passengers","title":"Comprueba los datos del viaje","fields":["passengers","cabin","fare","booking_reference"]},
{"id":"baggage","title":"Prepara tu equipaje","fields":["baggage"]},
{"id":"documents","title":"Prepara tus documentos","fields":["documents"]},
{"id":"destination","title":"Prepara la entrada al destino","fields":["entry_requirements"]},
{"id":"result","title":"Guarda tu preparación","fields":["pdf","summary","next_action"]}
],
"dviajeros":[
{"id":"start","title":"Crear nueva aplicación","fields":["language","create_form"]},
{"id":"personal","title":"Datos personales y del documento","fields":["first_name","middle_name","surname","second_surname","birth_date","gender","country_of_birth","nationality","document_issuing_country","passport_number","residence_country","email","phone","other_phone"]},
{"id":"immigration","title":"Información migratoria y del vuelo","fields":["arrival_date","flight_number","airline_name","seat_number","point_of_entry","traveler_country_origin","travel_reason","organism","visa_number"]},
{"id":"accommodation","title":"Alojamiento en Cuba","fields":["province","municipality","accommodation_type","accommodation_place","address"]},
{"id":"health","title":"Salud","fields":["countries_last_15_days","symptoms_last_15_days","questionnaire","vaccination","vaccine","vaccination_scheme","pcr_rt_test"]},
{"id":"customs","title":"Aduana","fields":["has_customs_declaration","cash_currency","cash_amount","goods","unaccompanied_luggage"]},
{"id":"review","title":"Revisa toda la información","fields":["truthful_confirmation","captcha"]},
{"id":"submit","title":"Finaliza y guarda tu resultado","fields":["submit","qr","official_pdf"]}
],
"visa":[
{"id":"personal","title":"Datos personales","fields":["given_names","surname","gender","nationality","birth_date","place_of_birth"]},
{"id":"contact","title":"Datos de contacto","fields":["email","phone","current_address","city","state_province","country"]},
{"id":"passport","title":"Datos del pasaporte","fields":["passport_type","passport_number","issuing_country","issuing_authority","issue_date","expiry_date"]},
{"id":"travel","title":"Datos del viaje","fields":["arrival_date","length_of_stay","flight_number","purpose","destination","accommodation"]},
{"id":"additional","title":"Información adicional","fields":["additional_information"]},
{"id":"review","title":"Revisa antes de enviar","fields":["application_confirmation"]},
{"id":"official","title":"Continúa en el sitio oficial","fields":["official_visa_url"]},
{"id":"result","title":"Guarda tu preparación","fields":["pdf","summary","next_action"]}
],
"documents":[
{"id":"identity","title":"Tu identidad","fields":["nationality","residence_country","passport_country","passport_number","passport_expiry"]},
{"id":"trip","title":"Tu viaje","fields":["origin","destination","departure_date","return_date","purpose"]},
{"id":"requirements","title":"Comprueba los requisitos","fields":["passport","visa","health","entry_authorization"]},
{"id":"result","title":"Guarda tu preparación","fields":["pdf","summary","next_action"]}
],
"baggage":[
{"id":"trip","title":"Identifica tu viaje","fields":["airline","origin","destination","departure_date"]},
{"id":"fare","title":"Identifica tu tarifa","fields":["fare","cabin"]},
{"id":"bags","title":"Identifica tu equipaje","fields":["baggage_type","quantity","weight","dimensions"]},
{"id":"items","title":"Revisa lo que llevas","fields":["items"]},
{"id":"official","title":"Comprueba la regla oficial","fields":["official_airline_url","tsa_url"]},
{"id":"result","title":"Guarda tu resultado","fields":["pdf","summary","next_action"]}
]
}

def all_sources()->List[Dict[str,Any]]:
    return [asdict(x) for x in SOURCES]

def source_by_id(source_id:str)->Optional[Dict[str,Any]]:
    if not source_id:return None
    for source in SOURCES:
        if source.id==source_id:return asdict(source)
    return None

def get_sources(ids:Optional[List[str]]=None,category:Optional[str]=None,process:Optional[str]=None,official_only:bool=False)->List[Dict[str,Any]]:
    selected=SOURCES
    if ids:
        wanted=set(ids)
        selected=[x for x in selected if x.id in wanted]
    if category:
        selected=[x for x in selected if x.category==category]
    if process:
        selected=[x for x in selected if x.id in PROCESS_SOURCE_IDS.get(process,[])]
    if official_only:
        selected=[x for x in selected if x.official]
    return [asdict(x) for x in selected]

def sources_for(process:str,official_only:bool=True)->List[Dict[str,Any]]:
    return get_sources(process=process,official_only=official_only)

def find_sources(query:str,official_only:bool=False)->List[Dict[str,Any]]:
    q=(query or "").strip().lower()
    if not q:return []
    result=[]
    for source in SOURCES:
        hay=" ".join([source.id,source.name,source.category,source.country,source.description,source.process]).lower()
        if q in hay and (not official_only or source.official):
            result.append(asdict(source))
    return result

def official_sources(process:Optional[str]=None)->List[Dict[str,Any]]:
    return sources_for(process,True) if process else get_sources(official_only=True)

def get_official_sources(process:Optional[str]=None)->List[Dict[str,Any]]:
    return official_sources(process)

def airline_sources()->List[Dict[str,Any]]:
    return get_sources(ids=AIRLINE_IDS,official_only=True)

def charter_sources()->List[Dict[str,Any]]:
    return get_sources(ids=CHARTER_IDS)

def official_url(source_id:str)->str:
    source=source_by_id(source_id)
    return source["url"] if source else ""

def process_steps(process:str)->List[Dict[str,Any]]:
    return FORM_STEPS.get(process,[])

def source_registry_status()->Dict[str,Any]:
    return {
        "version":VERSION,
        "verification_date":VERIFICATION_DATE,
        "official_only":OFFICIAL_ONLY,
        "source_count":len(SOURCES),
        "processes":sorted(FORM_STEPS.keys())
    }

__all__=[
"VERSION","VERIFICATION_DATE","APP_NAME","OFFICIAL_ONLY","Source","SOURCES",
"AIRLINE_IDS","CHARTER_IDS","PROCESS_SOURCE_IDS","FORM_STEPS",
"all_sources","source_by_id","get_sources","sources_for","find_sources",
"official_sources","get_official_sources","airline_sources","charter_sources",
"official_url","process_steps","source_registry_status"
]
