# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Union
import re

VERSION="12.1.0"
VERIFICATION_DATE="2026-10-03"

@dataclass(frozen=True)
class Source:
    id:str
    name:str
    publisher:str
    url:str
    type:str="official"
    topics:tuple=()
    what_it_covers:str=""
    limitations:str=""
    verified:str=VERIFICATION_DATE
    country:str=""
    category:str="official"

def _topics(value:Union[str,List[str],tuple,set,None])->tuple:
    if value is None:return ()
    if isinstance(value,str):return tuple(x.strip() for x in value.split(",") if x.strip())
    return tuple(str(x).strip() for x in value if str(x).strip())

def S(id,name,publisher,url,topics=(),covers="",limitations="",country="",category="official",type="official"):
    return Source(str(id),str(name),str(publisher),str(url),str(type),_topics(topics),str(covers),str(limitations),VERIFICATION_DATE,str(country),str(category))

SOURCES=[
S("tsa","TSA","Transportation Security Administration","https://www.tsa.gov/travel/security-screening/whatcanibring",["baggage","items","security","carry-on","checked"],"Qué artículos pueden pasar por seguridad y reglas de equipaje.","Las reglas de la aerolínea y del país de destino también pueden aplicar.","USA","government"),
S("tsa_food","TSA What Can I Bring","Transportation Security Administration","https://www.tsa.gov/travel/security-screening/whatcanibring/food",["food","items","carry-on","checked"],"Alimentos y artículos relacionados con comida.","Las reglas de agricultura, aduana y destino pueden ser adicionales.","USA","government"),
S("faa","FAA","Federal Aviation Administration","https://www.faa.gov/hazmat/packsafe",["hazmat","dangerous-goods","batteries","fuel","items"],"Artículos peligrosos y materiales relacionados con aviación.","No sustituye las reglas específicas de la aerolínea ni del destino.","USA","government"),
S("cbp","CBP","U.S. Customs and Border Protection","https://www.cbp.gov/travel",["customs","entry","food","agriculture","travel"],"Información general de entrada, aduana y viajes.","El destino extranjero tiene sus propias reglas.","USA","government"),
S("state","U.S. Department of State","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel.html",["travel","documents","passport","cuba"],"Información oficial para viajeros estadounidenses y documentación.","Los requisitos del país de destino pueden cambiar.","USA","government"),
S("iata","IATA","International Air Transport Association","https://www.iata.org/en/programs/cargo/dgr/",["dangerous-goods","baggage","airline"],"Referencia internacional sobre mercancías peligrosas y aviación.","La decisión operativa final corresponde a la aerolínea y autoridades competentes.","INTERNATIONAL","aviation"),
S("icao","ICAO","International Civil Aviation Organization","https://www.icao.int/safety/airnavigation/OPS/CABINSAFETY/Pages/default.aspx",["aviation","safety","international"],"Información internacional de seguridad operacional.","No sustituye instrucciones de una aerolínea concreta.","INTERNATIONAL","aviation"),

S("aa","American Airlines","American Airlines","https://www.aa.com/",["airline","american","aa","cuba","baggage"],"Sitio oficial para vuelos, reservas, equipaje y requisitos de American Airlines.","La información depende del boleto, ruta, temporada y reglas vigentes.","USA","airline"),
S("aa_bags","American Airlines — Equipaje","American Airlines","https://www.aa.com/web/i18n/travel-info/baggage/checked-baggage-policy.html?locale=es_US",["airline","american","baggage","checked","cuba"],"Política oficial de equipaje facturado.","Verificar siempre la ruta, tarifa, fecha y excepciones.","USA","airline"),
S("aa_cuba","American Airlines — Cuba","American Airlines","https://www.aa.com/i18n/travel-info/international-travel/international-travel.jsp",["airline","american","cuba"],"Información oficial relacionada con viajes internacionales y Cuba.","La disponibilidad y restricciones pueden cambiar.","USA","airline"),

S("delta","Delta Air Lines","Delta Air Lines","https://www.delta.com/",["airline","delta","cuba","baggage"],"Sitio oficial de Delta para reservas y equipaje.","La franquicia depende de ruta, tarifa, clase y fecha.","USA","airline"),
S("delta_bags","Delta — Restricciones de equipaje","Delta Air Lines","https://es.delta.com/us/es/baggage/checked-baggage/embargoes-restrictions",["airline","delta","baggage","cuba","havana"],"Restricciones y embargos de equipaje.","Puede haber límites específicos por temporada y destino.","USA","airline"),
S("delta_cuba_bags","Delta — Cuba","Delta Air Lines","https://www.delta.com/us/en/baggage/checked-baggage/embargoes-restrictions",["airline","delta","cuba","baggage"],"Restricciones oficiales aplicables a destinos determinados.","Confirmar antes del viaje.","USA","airline"),

S("united","United Airlines","United Airlines","https://www.united.com/",["airline","united","baggage","cuba"],"Sitio oficial de United para vuelos y equipaje.","Las condiciones dependen de boleto y ruta.","USA","airline"),
S("southwest","Southwest Airlines","Southwest Airlines","https://www.southwest.com/",["airline","southwest","baggage","cuba"],"Sitio oficial de Southwest.","Verificar reglas específicas para Cuba.","USA","airline"),
S("southwest_bags","Southwest — Cuba / equipaje","Southwest Airlines","https://support.southwest.com/helpcenter/article/baggage-embargo-for-checked-bags",["airline","southwest","cuba","baggage","embargo"],"Restricciones oficiales de equipaje para Cuba.","Las restricciones pueden aplicarse por destino y condiciones vigentes.","USA","airline"),

S("jetblue","JetBlue","JetBlue Airways","https://www.jetblue.com/",["airline","jetblue","baggage","cuba"],"Sitio oficial de JetBlue.","Confirmar condiciones actuales de la ruta.","USA","airline"),
S("spirit","Spirit Airlines","Spirit Airlines","https://www.spirit.com/",["airline","spirit","baggage"],"Sitio oficial de Spirit.","Las condiciones dependen del boleto y ruta.","USA","airline"),
S("frontier","Frontier Airlines","Frontier Airlines","https://www.flyfrontier.com/",["airline","frontier","baggage"],"Sitio oficial de Frontier.","Las condiciones dependen del boleto y ruta.","USA","airline"),
S("copa","Copa Airlines","Copa Airlines","https://www.copaair.com/",["airline","copa","baggage","cuba"],"Sitio oficial de Copa Airlines.","Verificar reglas de ruta y conexión.","PANAMA","airline"),
S("copa_cuba","Copa — Cuba","Copa Airlines","https://www.copaair.com/en-gs/travel-information/baggage/",["airline","copa","cuba","baggage"],"Información oficial de equipaje.","Confirmar condiciones del boleto.","PANAMA","airline"),
S("avianca","Avianca","Avianca","https://www.avianca.com/",["airline","avianca","baggage"],"Sitio oficial de Avianca.","Las condiciones dependen de tarifa y ruta.","COLOMBIA","airline"),
S("latam","LATAM Airlines","LATAM Airlines","https://www.latamairlines.com/",["airline","latam","baggage"],"Sitio oficial de LATAM.","Las condiciones dependen de tarifa y ruta.","LATAM","airline"),
S("aeromexico","Aeroméxico","Aeroméxico","https://www.aeromexico.com/",["airline","aeromexico","baggage","cuba"],"Sitio oficial de Aeroméxico.","Verificar la franquicia correspondiente al boleto.","MEXICO","airline"),
S("aeromexico_bags","Aeroméxico — Equipaje de mano","Aeroméxico","https://www.aeromexico.com/en-us/travel-information/baggage/carry-on-baggage",["airline","aeromexico","baggage","carry-on"],"Equipaje de mano y condiciones según tarifa.","El peso y piezas pueden cambiar según tarifa y ruta.","MEXICO","airline"),
S("volaris","Volaris","Volaris","https://www.volaris.com/",["airline","volaris","baggage"],"Sitio oficial de Volaris.","Verificar condiciones del boleto.","MEXICO","airline"),
S("viva","Viva","Viva Aerobus","https://www.vivaaerobus.com/",["airline","viva","vivaaerobus","baggage"],"Sitio oficial de Viva Aerobus.","Verificar condiciones del boleto.","MEXICO","airline"),

S("cuba_dviajeros","D’Viajeros","Ministerio de Transporte de Cuba","https://dviajeros.mitrans.gob.cu/",["cuba","dviajeros","entry","documents","qr"],"Formulario oficial D’Viajeros y proceso de entrada.","El formulario oficial debe completarse según las instrucciones vigentes.","CUBA","cuba"),
S("cuba_aduana","Aduana General de la República de Cuba","Aduana de Cuba","https://www.aduana.gob.cu/",["cuba","customs","baggage","items","import"],"Normas oficiales de aduana, equipaje, artículos y mercancías.","Las reglas pueden cambiar y deben verificarse antes de viajar.","CUBA","cuba"),
S("cuba_mitrans","Ministerio de Transporte de Cuba","MITRANS","https://www.mitrans.gob.cu/",["cuba","transport","travel"],"Información oficial de transporte.","No sustituye información específica del operador aéreo.","CUBA","cuba"),
S("cuba_minrex","Ministerio de Relaciones Exteriores de Cuba","MINREX","https://cubaminrex.cu/",["cuba","visa","entry","documents","passport"],"Información oficial relacionada con entrada, documentación y relaciones consulares.","Los requisitos dependen de nacionalidad y situación del viajero.","CUBA","cuba"),
S("cuba_evisa","eVisa Cuba","Gobierno de Cuba","https://evisacuba.cu/",["cuba","visa","evisa","entry"],"Portal oficial relacionado con visa electrónica de Cuba.","El viajero debe verificar si su nacionalidad y viaje requieren visa.","CUBA","cuba"),
S("cuba_travel_regulations","Información oficial de viaje a Cuba","Gobierno de Cuba","https://www.cubaminrex.cu/",["cuba","visa","dviajeros","entry","documents","baggage"],"Referencia oficial para verificar requisitos de entrada.","La información oficial vigente prevalece sobre cualquier orientación de la aplicación.","CUBA","cuba"),

S("xael_charter","Xael Charters","Xael Charters","https://www.xaelcharter.com/",["cuba","charter","flight","baggage","florida"],"Operador/agencia de vuelos chárter a Cuba y condiciones publicadas por el operador.","La franquicia y tarifas dependen del boleto, ruta y temporada; confirmar directamente.","USA/CUBA","charter"),
S("aerocuba","Aerocuba","Aerocuba","https://www.aerocuba.com/",["cuba","charter","flight","baggage","florida"],"Información oficial del operador y sus servicios a Cuba.","Confirmar peso, piezas y tarifas antes de viajar.","USA/CUBA","charter"),
S("cubazul","Cubazul Air Charter","Cubazul Air Charter","https://cubazulaircharter.com/",["cuba","charter","flight","baggage","florida"],"Información oficial del operador chárter.","Las condiciones dependen del boleto y piezas adicionales.","USA/CUBA","charter"),
S("cuballama_charters","Cuballama Viajes — Vuelos chárter","Cuballama","https://www.cuballama.com/viajes/vuelos/charters",["cuba","charter","flight","baggage","florida"],"Información publicada por Cuballama sobre vuelos chárter.","Verificar directamente disponibilidad, ruta, boleto y equipaje.","USA/CUBA","charter"),

S("google_flights","Google Flights","Google","https://www.google.com/travel/flights",["flight","search","booking"],"Herramienta para buscar opciones de vuelos.","No es una fuente de reglas de equipaje ni sustituye el sitio oficial de la aerolínea.","INTERNATIONAL","search")
]

AIRLINES=[x for x in SOURCES if x.category=="airline" and x.id in {
    "aa","delta","united","southwest","jetblue","spirit","frontier","copa","avianca","latam","aeromexico","volaris","viva"
}]

CHARTERS=[x for x in SOURCES if x.category=="charter" and x.id in {
    "xael_charter","aerocuba","cubazul","cuballama_charters"
}]

CUBA_OFFICIAL=[x for x in SOURCES if x.id in {
    "cuba_dviajeros","cuba_aduana","cuba_mitrans","cuba_minrex","cuba_evisa","cuba_travel_regulations"
}]

CUBA_AIRLINE_SOURCES=[x for x in SOURCES if x.id in {
    "aa_bags","aa_cuba","delta_bags","delta_cuba_bags","southwest_bags","jetblue","copa_cuba","aeromexico_bags"
}]

def _dict(s:Source)->Dict[str,Any]:
    d=asdict(s)
    d["topics"]=list(d["topics"])
    return d

def all_sources()->List[Dict[str,Any]]:
    return [_dict(x) for x in SOURCES]

def _normalize(value:Any)->str:
    return str(value or "").strip().lower()

def _tokens(value:Any)->List[str]:
    return re.findall(r"[a-z0-9áéíóúñü'-]+",_normalize(value))

def _matches_query(s:Source,q:str)->bool:
    if not q:return True
    blob=" ".join([s.id,s.name,s.publisher,s.url,s.type,s.country,s.category,s.what_it_covers,s.limitations," ".join(s.topics)]).lower()
    return all(w in blob for w in _tokens(q))

def get_sources(topic:str="official",query:str="")->List[Dict[str,Any]]:
    t=_normalize(topic)
    q=_normalize(query)
    if t in {"","official","all","any"}:candidates=SOURCES
    else:candidates=[s for s in SOURCES if t in {x.lower() for x in s.topics} or t==s.category.lower() or t==s.id.lower() or t in s.name.lower()]
    out=[_dict(s) for s in candidates if _matches_query(s,q)]
    if not out and q:
        compact=q.replace(" ","")
        for s in SOURCES:
            blob=(s.name+" "+s.what_it_covers+" "+" ".join(s.topics)).lower()
            if compact in blob.replace(" ",""):out.append(_dict(s))
    return out[:50]

def sources_for(topic:str="",query:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "all",query)

def find_sources(topic:str="",query:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "all",query)

def official_sources(topic:str="",query:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official",query)

def get_official_sources(topic:str="",query:str="")->List[Dict[str,Any]]:
    if topic or query:return get_sources(topic or "official",query)
    return [_dict(x) for x in SOURCES if x.type=="official"]

def get_airlines(query:str="")->List[Dict[str,Any]]:
    q=_normalize(query)
    if not q:return [_dict(x) for x in AIRLINES]
    return [_dict(x) for x in AIRLINES if q in (x.name+" "+x.publisher+" "+x.country+" "+x.id).lower() or any(q in t.lower() for t in x.topics)]

def airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def find_airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def airline_list(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def get_charters(query:str="")->List[Dict[str,Any]]:
    q=_normalize(query)
    if not q:return [_dict(x) for x in CHARTERS]
    return [_dict(x) for x in CHARTERS if q in (x.name+" "+x.publisher+" "+x.country+" "+x.id).lower() or any(q in t.lower() for t in x.topics)]

def charters(query:str="")->List[Dict[str,Any]]:
    return get_charters(query)

def find_charters(query:str="")->List[Dict[str,Any]]:
    return get_charters(query)

def charter_list(query:str="")->List[Dict[str,Any]]:
    return get_charters(query)

def get_cuba_official_sources(query:str="")->List[Dict[str,Any]]:
    q=_normalize(query)
    if not q:return [_dict(x) for x in CUBA_OFFICIAL]
    return [_dict(x) for x in CUBA_OFFICIAL if _matches_query(x,q)]

def cuba_official_sources(query:str="")->List[Dict[str,Any]]:
    return get_cuba_official_sources(query)

def get_cuba_airline_sources(query:str="")->List[Dict[str,Any]]:
    q=_normalize(query)
    if not q:return [_dict(x) for x in CUBA_AIRLINE_SOURCES]
    return [_dict(x) for x in CUBA_AIRLINE_SOURCES if _matches_query(x,q)]

def source_by_id(source_id:str):
    sid=_normalize(source_id)
    for s in SOURCES:
        if s.id.lower()==sid:return _dict(s)
    return None

def official_url(source_id:str)->str:
    x=source_by_id(source_id)
    return x.get("url","") if x else ""

def source_url(source_id:str)->str:
    return official_url(source_id)

__all__=["VERSION","VERIFICATION_DATE","Source","S","SOURCES","AIRLINES","CHARTERS","CUBA_OFFICIAL","CUBA_AIRLINE_SOURCES","all_sources","get_sources","sources_for","find_sources","official_sources","get_official_sources","get_airlines","airlines","find_airlines","airline_list","get_charters","charters","find_charters","charter_list","get_cuba_official_sources","cuba_official_sources","get_cuba_airline_sources","source_by_id","official_url","source_url"]
