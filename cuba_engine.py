# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional

VERSION="12.1.0"
COUNTRY="Cuba"

OFFICIAL_VISA_URL="https://evisacuba.cu/"
OFFICIAL_DVIAJEROS_URL="https://dviajeros.mitrans.gob.cu/"
OFFICIAL_CUSTOMS_URL="https://www.aduana.gob.cu/"
OFFICIAL_MITRANS_URL="https://www.mitrans.gob.cu/"
OFFICIAL_MINREX_URL="https://cubaminrex.cu/"

@dataclass(frozen=True)
class CubaSource:
    id:str
    name:str
    url:str
    purpose:str
    official:bool=True

OFFICIAL_SOURCES=[
    CubaSource("visa","eVisa Cuba",OFFICIAL_VISA_URL,"Visa y eVisa de Cuba"),
    CubaSource("dviajeros","D’Viajeros",OFFICIAL_DVIAJEROS_URL,"Formulario oficial de entrada"),
    CubaSource("customs","Aduana de Cuba",OFFICIAL_CUSTOMS_URL,"Equipaje, mercancías y aduana"),
    CubaSource("mitrans","MITRANS",OFFICIAL_MITRANS_URL,"Transporte"),
    CubaSource("minrex","MINREX",OFFICIAL_MINREX_URL,"Información consular y de entrada")
]

CHARTER_SOURCES=[
    {"id":"xael_charter","name":"Xael Charters","url":"https://www.xaelcharter.com/","baggage_hand":"Generalmente 1 pieza incluida; por ejemplo hasta 35 lb según temporada","baggage_checked":"Tarifas por libra que pueden comenzar alrededor de $1 o $2/lb según la maleta; el límite por bulto suele rondar 70 lb","notice":"Referencia orientativa. Confirma el boleto y las condiciones actuales con el operador."},
    {"id":"aerocuba","name":"Aerocuba","url":"https://www.aerocuba.com/","baggage_hand":"1 pieza de mano permitida; pueden existir franquicias promocionales de hasta 35 lb","baggage_checked":"Cobro por peso o por libra; pueden existir tarifas desde $1/lb según ruta y pieza","notice":"Referencia orientativa. Confirma el boleto y las condiciones actuales con el operador."},
    {"id":"cubazul","name":"Cubazul Air Charter","url":"https://cubazulaircharter.com/","baggage_hand":"Incluido según los términos del boleto adquirido","baggage_checked":"Maletas de hasta 70 lb; piezas adicionales pueden tener tarifas escalonadas por libra","notice":"Referencia orientativa. Confirma el boleto y las condiciones actuales con el operador."},
    {"id":"cuballama_charters","name":"Cuballama Viajes — Vuelos chárter","url":"https://www.cuballama.com/viajes/vuelos/charters","baggage_hand":"Depende del boleto y operador correspondiente","baggage_checked":"Depende de la ruta, operador y condiciones de la reserva","notice":"Verifica directamente las condiciones de la reserva."}
]

COMMERCIAL_BAGGAGE=[
    {"id":"aa","airline":"American Airlines","url":"https://www.aa.com/web/i18n/travel-info/baggage/checked-baggage-policy.html?locale=es_US","hand":"1 maleta de mano y 1 artículo personal","checked":"Para Cuba existe una restricción general de hasta 2 maletas facturadas; pueden aplicar límites de hasta 70 lb por pieza según la ruta y condiciones del boleto","notice":"Verifica peso, tarifa, temporada y excepciones en American Airlines."},
    {"id":"delta","airline":"Delta Air Lines","url":"https://es.delta.com/us/es/baggage/checked-baggage/embargoes-restrictions","hand":"1 pieza de mano y 1 artículo personal","checked":"Puede haber límites específicos para La Habana y restricciones de temporada/capacidad; el peso depende de tarifa y clase","notice":"Verifica la fecha de compra, ruta, tarifa y temporada en Delta."},
    {"id":"southwest","airline":"Southwest Airlines","url":"https://support.southwest.com/helpcenter/article/baggage-embargo-for-checked-bags","hand":"1 equipaje de mano y 1 artículo personal","checked":"Para Cuba pueden existir restricciones específicas y permanentes; se indica un máximo de 2 maletas y límites de 50 lb/23 kg y 62 pulgadas lineales según la política","notice":"Verifica la política oficial antes de acudir al aeropuerto."},
    {"id":"aeromexico","airline":"Aeroméxico","url":"https://www.aeromexico.com/en-us/travel-information/baggage/carry-on-baggage","hand":"1 equipaje de mano y 1 artículo personal; el peso combinado depende de la tarifa","checked":"La franquicia depende de la familia tarifaria, ruta y boleto; pueden existir piezas de 23 kg o 32 kg según condiciones","notice":"Verifica exactamente la franquicia del boleto adquirido."}
]

def _norm(v:Any)->str:
    return str(v or "").strip().lower()

def _source(x:CubaSource)->Dict[str,Any]:
    return asdict(x)

def _bool(v:Any)->bool:
    if isinstance(v,bool):return v
    return _norm(v) in ("1","true","yes","si","sí","y","on")

def _pick(d:Dict[str,Any],*keys:str)->Any:
    for k in keys:
        v=d.get(k)
        if v is not None and str(v).strip()!="":return v
    return ""

def _fill(data:Dict[str,Any],keys:List[str])->Dict[str,Any]:
    return {k:_pick(data,k) for k in keys}

def official_information(language:str="es")->Dict[str,Any]:
    es=language!="en"
    return {
        "title":"Preparación oficial para Cuba" if es else "Official Cuba preparation",
        "notice":"La aplicación explica y practica. La confirmación y el trámite final se hacen en el sitio oficial." if es else "The app explains and lets you practice. Final confirmation and official processing are done on the official website.",
        "sources":[_source(x) for x in OFFICIAL_SOURCES],
        "steps":[
            {"step":1,"title":"Visa" if es else "Visa","action":"Revisa si necesitas visa o eVisa según tu nacionalidad y viaje." if es else "Check whether you need a visa or eVisa based on your nationality and trip.","url":OFFICIAL_VISA_URL},
            {"step":2,"title":"D’Viajeros","action":"Practica primero y después completa el formulario oficial." if es else "Practice first and then complete the official form.","url":OFFICIAL_DVIAJEROS_URL},
            {"step":3,"title":"Equipaje y aduana" if es else "Baggage and customs","action":"Revisa qué puedes introducir y las cantidades permitidas." if es else "Review what you may bring and the permitted quantities.","url":OFFICIAL_CUSTOMS_URL},
            {"step":4,"title":"Confirma" if es else "Confirm","action":"Comprueba nuevamente la información oficial antes de viajar." if es else "Check the official information again before traveling.","url":OFFICIAL_MINREX_URL}
        ]
    }

def get_charter_sources(language:str="es")->List[Dict[str,Any]]:
    if language=="en":
        return [
            {**x,
             "baggage_hand":x["baggage_hand"],
             "baggage_checked":x["baggage_checked"],
             "notice":"Reference information only. Confirm the current ticket and baggage conditions with the operator."}
            for x in CHARTER_SOURCES
        ]
    return [dict(x) for x in CHARTER_SOURCES]

def get_commercial_baggage(language:str="es")->List[Dict[str,Any]]:
    if language=="en":
        return [{**x,"notice":"Verify the exact baggage allowance on the official airline website before travel."} for x in COMMERCIAL_BAGGAGE]
    return [dict(x) for x in COMMERCIAL_BAGGAGE]

def baggage_guide(language:str="es")->Dict[str,Any]:
    es=language!="en"
    return {
        "title":"Guía de Equipaje para Vuelos Chárter a Cuba" if es else "Baggage Guide for Charter Flights to Cuba",
        "charters":get_charter_sources(language),
        "commercial":get_commercial_baggage(language),
        "recommendations":[
            "Pesa cada maleta antes de ir al aeropuerto de salida en Florida, especialmente Miami o Tampa.",
            "No asumas que una franquicia de un operador sirve para otro operador.",
            "Revisa las normas vigentes de la Aduana de Cuba sobre electrodomésticos, medicamentos autorizados y límites de misceláneas.",
            "Lleva contigo la información del boleto y revisa el sitio oficial de la aerolínea u operador antes de salir."
        ] if es else [
            "Weigh every bag before going to the departure airport in Florida, especially Miami or Tampa.",
            "Do not assume one operator's baggage allowance applies to another operator.",
            "Review current Cuban Customs rules for appliances, authorized medicines and miscellaneous-item limits.",
            "Keep your ticket information and check the airline or operator official website before departure."
        ],
        "official_customs":OFFICIAL_CUSTOMS_URL,
        "official_mitrans":OFFICIAL_MITRANS_URL,
        "next_action":"Revisa la fuente oficial correspondiente antes de viajar." if es else "Review the applicable official source before traveling."
    }

def evaluate_visa(data:Dict[str,Any],language:str="es")->Dict[str,Any]:
    d=dict(data or {})
    nationality=_pick(d,"nationality","passport_country","country")
    purpose=_pick(d,"travel_purpose","purpose","purpose_of_trip")
    entry_type=_pick(d,"entry_type","entry","entry_method") or "air"
    passport_country=_pick(d,"passport_country","passport_nationality","nationality")
    has_passport=_bool(d.get("has_passport",d.get("passport")))
    passport_valid=_bool(d.get("passport_valid",d.get("valid_passport")))
    dual=_bool(d.get("dual_nationality",d.get("dual_citizen",d.get("cuban_nationality")))
    )
    passport_number=_pick(d,"passport_number","passport_no")
    first_name=_pick(d,"first_name","given_names","name")
    last_name=_pick(d,"last_name","surnames","family_name")
    birth_date=_pick(d,"date_of_birth","birth_date")
    arrival_date=_pick(d,"arrival_date","travel_date")
    accommodation=_pick(d,"accommodation","lodging")
    fields={
        "first_name":first_name,
        "last_name":last_name,
        "nationality":nationality,
        "passport_country":passport_country,
        "passport_number":passport_number,
        "date_of_birth":birth_date,
        "arrival_date":arrival_date,
        "travel_purpose":purpose,
        "entry_type":entry_type,
        "accommodation":accommodation,
        "has_passport":has_passport,
        "passport_valid":passport_valid,
        "dual_nationality":dual
    }
    required=["nationality","passport_country","travel_purpose"]
    missing=[x for x in required if not str(fields.get(x) or "").strip()]
    if not has_passport:missing.append("has_passport")
    if language=="en":
        title="Cuba visa preparation"
        steps=["Identify your nationality and travel purpose.","Confirm the passport you will use.","If you have Cuban nationality or dual nationality, review the official Cuban requirements.","Check the official Cuba visa/eVisa site.","Use the official site for the real process."]
        message="Your information has been organized for preparation. The official authority determines the applicable visa or entry requirement."
        next_action="Complete any missing preparation information, then open the official Cuba visa/eVisa website."
        notice="PRACTICE ONLY: this does not submit a visa application or create a real visa."
    else:
        title="Preparación de visa para Cuba"
        steps=["Identifica tu nacionalidad y motivo del viaje.","Confirma el pasaporte que vas a utilizar.","Si tienes nacionalidad cubana o doble nacionalidad, revisa los requisitos oficiales de Cuba.","Consulta el sitio oficial de visa/eVisa.","Utiliza el sitio oficial para realizar el proceso real."]
        message="Tus datos quedaron organizados para la preparación. La autoridad oficial determina el requisito de visa o entrada aplicable."
        next_action="Completa los datos que realmente falten y después abre el sitio oficial de visa/eVisa de Cuba."
        notice="SOLO PRÁCTICA: esto no presenta una solicitud de visa ni crea una visa real."
    return {
        "title":title,
        "status":"ready" if not missing else "needs_information",
        "message":message,
        "nationality":nationality,
        "purpose":purpose,
        "entry_type":entry_type,
        "passport_country":passport_country,
        "has_passport":has_passport,
        "passport_valid":passport_valid,
        "dual_nationality":dual,
        "fields":fields,
        "missing":missing,
        "completed":not missing,
        "steps":steps,
        "notice":notice,
        "next_action":next_action,
        "official_url":OFFICIAL_VISA_URL,
        "official_source":"eVisa Cuba"
    }

def evaluate_dviajeros(data:Dict[str,Any],language:str="es")->Dict[str,Any]:
    d=dict(data or {})
    fields=[
        ("given_names","first_name"),
        ("surnames","last_name"),
        ("nationality","nationality"),
        ("birth_date","date_of_birth"),
        ("passport_country","passport_country"),
        ("passport_number","passport_number"),
        ("arrival_date","arrival_date"),
        ("airline","airline"),
        ("accommodation","accommodation"),
        ("purpose_of_trip","purpose_of_trip")
    ]
    collected={}
    for a,b in fields:
        collected[a]=_pick(d,a,b)
    missing=[k for k,v in collected.items() if not str(v).strip()]
    if language=="en":
        title="D’Viajeros practice"
        next_action="Complete only the information that is actually missing, then use the official D’Viajeros website."
        notice="PRACTICE ONLY: this does not submit the official D’Viajeros form or create an official QR."
        message="Information already provided in the app has been placed into the practice automatically."
    else:
        title="Práctica de D’Viajeros"
        next_action="Completa solamente los datos que realmente falten y después utiliza el sitio oficial de D’Viajeros."
        notice="SOLO PRÁCTICA: esto no envía el formulario oficial de D’Viajeros ni crea un QR oficial."
        message="La información que ya proporcionaste en la aplicación fue colocada automáticamente en la práctica."
    return {
        "title":title,
        "fields":collected,
        "missing":missing,
        "completed":not missing,
        "notice":notice,
        "message":message,
        "next_action":next_action,
        "official_url":OFFICIAL_DVIAJEROS_URL,
        "qr":False,
        "official_submission":False
    }

def simulation(mode:str="booking",language:str="es")->Dict[str,Any]:
    en=language=="en"
    if mode=="visa":
        titles=["Identificar nacionalidad","Revisar pasaporte","Revisar necesidad de visa","Organizar información","Ir al sitio oficial"]
        titles_en=["Identify nationality","Review passport","Review visa requirement","Organize information","Open official website"]
    elif mode=="dviajeros":
        titles=["Datos personales","Pasaporte","Vuelo","Alojamiento","Motivo del viaje","Revisar antes de continuar"]
        titles_en=["Personal information","Passport","Flight","Accommodation","Trip purpose","Review before continuing"]
    else:
        titles=["Datos del pasajero","Ruta","Vuelo","Equipaje","Revisión","Confirmación simulada"]
        titles_en=["Passenger information","Route","Flight","Baggage","Review","Practice confirmation"]
    selected=titles_en if en else titles
    return {
        "simulation":True,
        "official_submission":False,
        "mode":mode,
        "notice":"SIMULATION: no information is submitted to Cuba, an airline or another authority." if en else "SIMULACIÓN: no se envía información a Cuba, una aerolínea ni otra autoridad.",
        "steps":[{"step":i+1,"title":t,"completed":False} for i,t in enumerate(selected)],
        "official_url":OFFICIAL_DVIAJEROS_URL if mode=="dviajeros" else OFFICIAL_VISA_URL if mode=="visa" else "",
        "next_action":"Continue with the official process on the official website when the practice is complete." if en else "Cuando termines la práctica, continúa con el proceso real en el sitio oficial."
    }

def public_config(language:str="es")->Dict[str,Any]:
    return {
        "version":VERSION,
        "country":COUNTRY,
        "language":language,
        "official_sources":official_information(language)["sources"],
        "charter_sources":get_charter_sources(language),
        "commercial_baggage":get_commercial_baggage(language),
        "baggage_guide":baggage_guide(language),
        "visa_url":OFFICIAL_VISA_URL,
        "dviajeros_url":OFFICIAL_DVIAJEROS_URL,
        "customs_url":OFFICIAL_CUSTOMS_URL,
        "mitrans_url":OFFICIAL_MITRANS_URL,
        "minrex_url":OFFICIAL_MINREX_URL
    }

def disclaimer(language:str="es")->str:
    if language=="en":
        return "¿QUÉ QUIERES LLEVAR? is an independent May Roga LLC preparation and orientation service. It is not an airline, government, airport, customs authority, immigration authority, consulate or travel agency. Simulations are not official submissions. Rules can change. When an official process is required, the app directs the customer to the responsible official website."
    return "¿QUÉ QUIERES LLEVAR? es un servicio independiente de preparación y orientación de May Roga LLC. No es una aerolínea, gobierno, aeropuerto, autoridad aduanera, autoridad migratoria, consulado ni agencia de viajes. Las simulaciones no son envíos oficiales. Las reglas pueden cambiar. Cuando se necesita un proceso oficial, la aplicación dirige al cliente al sitio oficial correspondiente."

def is_cuba_route(origin:str="",destination:str="")->bool:
    text=_norm(origin)+" "+_norm(destination)
    return any(x in text for x in ["cuba","havana","habana","holguin","varadero","santiago de cuba","camaguey","cayo coco","cayo largo","santa clara","matanzas","cub"])

class CubaEngine:
    version=VERSION
    official_sources=OFFICIAL_SOURCES
    charter_sources=CHARTER_SOURCES
    commercial_baggage=COMMERCIAL_BAGGAGE
    def public_config(self,language="es"):return public_config(language)
    def disclaimer(self,language="es"):return disclaimer(language)
    def official_information(self,language="es"):return official_information(language)
    def get_charter_sources(self,language="es"):return get_charter_sources(language)
    def get_commercial_baggage(self,language="es"):return get_commercial_baggage(language)
    def baggage_guide(self,language="es"):return baggage_guide(language)
    def evaluate_visa(self,data,language="es"):return evaluate_visa(data,language)
    def evaluate_dviajeros(self,data,language="es"):return evaluate_dviajeros(data,language)
    def simulation(self,mode="booking",language="es"):return simulation(mode,language)
    def is_cuba_route(self,origin="",destination=""):return is_cuba_route(origin,destination)

engine=CubaEngine()

__all__=["VERSION","COUNTRY","OFFICIAL_VISA_URL","OFFICIAL_DVIAJEROS_URL","OFFICIAL_CUSTOMS_URL","OFFICIAL_MITRANS_URL","OFFICIAL_MINREX_URL","CubaSource","OFFICIAL_SOURCES","CHARTER_SOURCES","COMMERCIAL_BAGGAGE","get_charter_sources","get_commercial_baggage","baggage_guide","official_information","evaluate_visa","evaluate_dviajeros","simulation","public_config","disclaimer","is_cuba_route","CubaEngine","engine"]
