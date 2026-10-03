# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v9.0.0
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional

VERSION="9.0.0"
VERIFICATION_DATE="2026-10-01"

@dataclass(frozen=True)
class Source:
    id:str
    name:str
    url:str
    description:str
    publisher:str
    verified:str=VERIFICATION_DATE
    type:str="official"

SOURCES=[
Source("tsa","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring/all","Información oficial sobre artículos permitidos y restringidos en el equipaje.","Transportation Security Administration"),
Source("faa_baggage","FAA","https://www.faa.gov/hazmat/packsafe","Información oficial sobre materiales peligrosos y artículos que pueden presentar restricciones durante el viaje aéreo.","Federal Aviation Administration"),
Source("cbp_travel","CBP","https://www.cbp.gov/travel","Información oficial para viajeros que entran o regresan a Estados Unidos.","U.S. Customs and Border Protection"),
Source("travel_state","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel.html","Información oficial sobre viajes internacionales y documentos de viaje.","U.S. Department of State"),
Source("iata_travel","IATA Travel Centre","https://www.iatatravelcentre.com/","Fuente de consulta para requisitos de documentación y viaje internacional.","International Air Transport Association","reference"),
Source("cuba_evisa","eVisa Cuba","https://evisacuba.cu/","Portal oficial para información y gestión relacionada con la visa electrónica de Cuba.","República de Cuba"),
Source("cuba_dviajeros","D'Viajeros","https://dviajeros.mitrans.gob.cu/","Portal oficial cubano para el formulario de información anticipada del viajero.","Ministerio de Transporte de Cuba"),
Source("cuba_minrex","MINREX Cuba","https://www.cubaminrex.cu/","Información oficial del Ministerio de Relaciones Exteriores de Cuba.","Ministerio de Relaciones Exteriores de Cuba"),
Source("cuba_customs","Aduana de Cuba","https://www.aduana.gob.cu/","Información oficial sobre aduanas, equipaje y artículos sujetos a control en Cuba.","Aduana General de la República de Cuba"),
]

AIRLINE_SOURCES={
"american":"https://www.aa.com/i18n/travel-info/baggage/baggage.jsp",
"delta":"https://www.delta.com/us/en/baggage/overview",
"united":"https://www.united.com/en/us/fly/baggage.html",
"southwest":"https://www.southwest.com/help/baggage",
"jetblue":"https://www.jetblue.com/baggage",
"spirit":"https://www.spirit.com/bag-details",
"frontier":"https://www.flyfrontier.com/travel/travel-info/bag-options/",
"alaska":"https://www.alaskaair.com/content/travel-info/baggage",
"air_canada":"https://www.aircanada.com/us/en/aco/home/plan/baggage.html",
"avianca":"https://www.avianca.com/en/information-and-help/baggage/",
"copa":"https://www.copaair.com/en-us/travel-information/baggage/",
"latam":"https://www.latamairlines.com/us/en/help-center/faq/baggage",
"jetblue_airways":"https://www.jetblue.com/baggage"
}

def _norm(value:Any)->str:
    return str(value or "").strip().lower()

def all_sources()->List[Dict[str,Any]]:
    return [asdict(x) for x in SOURCES]

def official_sources()->List[Dict[str,Any]]:
    return [asdict(x) for x in SOURCES if x.type=="official"]

def reference_sources()->List[Dict[str,Any]]:
    return [asdict(x) for x in SOURCES if x.type!="official"]

def get_source(source_id:str)->Optional[Dict[str,Any]]:
    sid=_norm(source_id)
    for source in SOURCES:
        if source.id==sid:return asdict(source)
    return None

def airline_source(airline:str)->Optional[Dict[str,Any]]:
    name=_norm(airline)
    if not name:return None
    aliases={
        "american airlines":"american",
        "aa":"american",
        "delta air lines":"delta",
        "delta airlines":"delta",
        "united airlines":"united",
        "southwest airlines":"southwest",
        "jetblue airways":"jetblue",
        "spirit airlines":"spirit",
        "frontier airlines":"frontier",
        "alaska airlines":"alaska",
        "air canada":"air_canada",
        "avianca airlines":"avianca",
        "copa airlines":"copa",
        "latam airlines":"latam"
    }
    key=aliases.get(name,name.replace(" ","_"))
    url=AIRLINE_SOURCES.get(key)
    if not url:return None
    return {"id":f"airline_{key}","name":airline,"url":url,"description":"Consulta oficial de equipaje y condiciones de viaje de la aerolínea.","publisher":airline,"verified":VERIFICATION_DATE,"type":"airline_official"}

def sources_for_airline(airline:str)->List[Dict[str,Any]]:
    result=[]
    source=airline_source(airline)
    if source:result.append(source)
    result.extend([asdict(x) for x in SOURCES if x.id in ("tsa","faa_baggage")])
    return result

def sources_for_flight(origin:str="",destination:str="",airline:str="")->List[Dict[str,Any]]:
    result=[]
    source=airline_source(airline)
    if source:result.append(source)
    result.extend([asdict(x) for x in SOURCES if x.id in ("tsa","travel_state","cbp_travel")])
    if _norm(destination) in ("cuba","cu","hav","havana","la habana"):
        result.extend([asdict(x) for x in SOURCES if x.id in ("cuba_minrex","cuba_customs","cuba_dviajeros","cuba_evisa")])
    return _unique(result)

def sources_for_item(airline:str="",destination:str="")->List[Dict[str,Any]]:
    result=sources_for_airline(airline)
    result.extend([asdict(x) for x in SOURCES if x.id in ("tsa","faa_baggage")])
    if _norm(destination) in ("cuba","cu","hav","havana","la habana"):
        result.extend([asdict(x) for x in SOURCES if x.id in ("cuba_customs","cuba_dviajeros")])
    return _unique(result)

def cuba_sources()->List[Dict[str,Any]]:
    return [asdict(x) for x in SOURCES if x.id in ("cuba_evisa","cuba_dviajeros","cuba_minrex","cuba_customs")]

def source_url(source_id:str)->str:
    source=get_source(source_id)
    return str(source.get("url","")) if source else ""

def _unique(items:List[Dict[str,Any]])->List[Dict[str,Any]]:
    seen=set()
    result=[]
    for item in items:
        key=item.get("id") or item.get("url")
        if key in seen:continue
        seen.add(key)
        result.append(item)
    return result

def registry()->Dict[str,Any]:
    return {
        "version":VERSION,
        "verification_date":VERIFICATION_DATE,
        "official":official_sources(),
        "reference":reference_sources(),
        "airlines":sorted(AIRLINE_SOURCES.keys()),
        "cuba":cuba_sources()
    }
