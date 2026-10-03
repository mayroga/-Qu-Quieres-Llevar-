# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v13.0.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Iterable,Optional
import re

VERSION="13.0.0"
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
    verified:bool=True
    country:str=""
    category:str="official"

def S(id:str,name:str,publisher:str,url:str,topics:Any=(),what_it_covers:str="",limitations:str="",country:str="",category:str="official",type:str="official",verified:bool=True)->Source:
    if isinstance(topics,str):
        topics=(topics,)
    else:
        topics=tuple(topics or ())
    return Source(id=id,name=name,publisher=publisher,url=url,type=type,topics=topics,what_it_covers=what_it_covers,limitations=limitations,verified=verified,country=country,category=category)

SOURCES=[
S("tsa","TSA","Transportation Security Administration","https://www.tsa.gov/","security","Security screening and passenger preparation","Does not replace airline or destination rules","US","security"),
S("tsa_bring","What Can I Bring","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring","baggage,item,security","Carry-on and checked-baggage item guidance","Final screening decision is made by TSA","US","security"),
S("tsa_liquids","Liquids Rule","TSA","https://www.tsa.gov/travel/security-screening/liquids-rule","liquids,baggage,security","Liquids and screening information","Airline and destination rules may also apply","US","security"),
S("tsa_medication","Medication","TSA","https://www.tsa.gov/travel/secure-flight/traveling-medication","medication,baggage,security","Medication screening information","Destination entry rules may differ","US","security"),
S("tsa_batteries","Batteries","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring/all","battery,electronics,baggage","Battery and electronic screening information","Battery limits can also depend on airline and destination","US","security"),
S("faa","FAA","Federal Aviation Administration","https://www.faa.gov/","aviation,flight,battery","U.S. aviation safety information","Not an individual airline baggage contract","US","aviation"),
S("cbp","CBP","U.S. Customs and Border Protection","https://www.cbp.gov/","customs,entry,travel","U.S. customs and entry information","Destination-country rules remain separate","US","customs"),
S("cbp_travel","CBP Travelers","U.S. Customs and Border Protection","https://www.cbp.gov/travel","customs,entry,baggage","Traveler and customs information","Applies to U.S. entry processes","US","customs"),
S("state_travel","Travel.State.Gov","U.S. Department of State","https://travel.state.gov/","travel,documents,entry","Travel and destination information","Official guidance should be checked for the specific trip","US","travel"),
S("state_cuba","Cuba Travel Information","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html","cuba,travel,documents","U.S. government Cuba travel information","Does not replace Cuban authorities","US/CU","cuba"),
S("cuba_dviajeros","D'Viajeros","República de Cuba","https://dviajeros.mitrans.gob.cu/","cuba,dviajeros,entry,documents","Official traveler information/form access","Use the official site for real submission","CU","cuba"),
S("cuba_aduana","Aduana General de la República de Cuba","Aduana de Cuba","https://www.aduana.gob.cu/","cuba,customs,baggage,item,entry,exit","Cuban customs information","Specific restrictions can change","CU","customs"),
S("cuba_mitrans","MITRANS","Ministerio de Transporte de Cuba","https://www.mitrans.gob.cu/","cuba,transport,aviation,travel","Transportation information","Check current official notices","CU","cuba"),
S("cuba_minrex","MINREX","Ministerio de Relaciones Exteriores de Cuba","https://cubaminrex.cu/","cuba,visa,documents,entry,exit","Cuban foreign-affairs information","Specific consular requirements may depend on nationality","CU","cuba"),
S("cuba_evisa","Cuba eVisa","MINREX","https://evisacuba.cu/","cuba,visa,evisa,entry,documents","Official Cuba eVisa information","Eligibility and procedures must be checked for the traveler","CU","visa"),
S("icao","ICAO","International Civil Aviation Organization","https://www.icao.int/","aviation,flight","International aviation information","Does not determine individual airline baggage allowances","INT","aviation"),
S("iata","IATA","International Air Transport Association","https://www.iata.org/","aviation,flight,baggage","Air transport industry information","Not a substitute for the airline's conditions","INT","aviation"),
S("iata_travel","IATA Travel Centre","IATA","https://www.iatatravelcentre.com/","travel,documents,visa,entry","Travel-document information tool","Always verify with official destination authorities","INT","travel"),

S("american","American Airlines","American Airlines","https://www.aa.com/","airline,flight,baggage,booking","Official airline site for flights, booking and baggage","Rules depend on itinerary and fare","US","airline"),
S("delta","Delta Air Lines","Delta Air Lines","https://www.delta.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","US","airline"),
S("united","United Airlines","United Airlines","https://www.united.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","US","airline"),
S("southwest","Southwest Airlines","Southwest Airlines","https://www.southwest.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary","US","airline"),
S("jetblue","JetBlue","JetBlue","https://www.jetblue.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","US","airline"),
S("spirit","Spirit Airlines","Spirit Airlines","https://www.spirit.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","US","airline"),
S("frontier","Frontier Airlines","Frontier Airlines","https://www.flyfrontier.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","US","airline"),
S("copa","Copa Airlines","Copa Airlines","https://www.copaair.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","PA","airline"),
S("avianca","Avianca","Avianca","https://www.avianca.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","CO","airline"),
S("latam","LATAM Airlines","LATAM Airlines","https://www.latamairlines.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","CL","airline"),
S("aeromexico","Aeroméxico","Aeroméxico","https://www.aeromexico.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","MX","airline"),
S("volaris","Volaris","Volaris","https://www.volaris.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","MX","airline"),
S("viva","Viva","Viva Aerobus","https://www.vivaaerobus.com/","airline,flight,baggage,booking","Official airline site","Rules depend on itinerary and fare","MX","airline"),

S("xael","Xael Charters","Xael Charters","https://www.xaelcharter.com/","charter,cuba,flight,booking","Official charter operator website","Availability, routes and conditions must be checked directly","US/CU","charter"),
S("aerocuba","Aerocuba","Aerocuba","https://www.aerocuba.com/","charter,cuba,flight,booking","Official charter operator website","Availability, routes and conditions must be checked directly","US/CU","charter"),
S("cubazul","Cubazul Air Charter","Cubazul Air Charter","https://cubazulaircharter.com/","charter,cuba,flight,booking","Official charter operator website","Availability, routes and conditions must be checked directly","US/CU","charter"),
S("cuballama_viajes","Cuballama Viajes","Cuballama","https://www.cuballama.com/viajes/vuelos/charters","charter,cuba,flight,booking","Official Cuballama charter-travel page","Availability, routes and conditions must be checked directly","US/CU","charter"),

S("mexico","Gobierno de México","Gobierno de México","https://www.gob.mx/","mexico,entry,documents","Official Mexican government information","Specific immigration requirements depend on traveler","MX","destination"),
S("guatemala","Gobierno de Guatemala","Gobierno de Guatemala","https://guatemala.gob.gt/","guatemala,entry,documents","Official government information","Check the responsible immigration authority","GT","destination"),
S("honduras","Gobierno de Honduras","Gobierno de Honduras","https://www.gob.hn/","honduras,entry,documents","Official government information","Check current immigration requirements","HN","destination"),
S("elsalvador","Gobierno de El Salvador","Gobierno de El Salvador","https://www.presidencia.gob.sv/","elsalvador,entry,documents","Official government information","Check current immigration requirements","SV","destination"),
S("dominican_republic","Gobierno de República Dominicana","Gobierno de República Dominicana","https://www.gob.do/","dominican_republic,entry,documents","Official government information","Check current immigration requirements","DO","destination"),
]

SOURCES_BY_ID={s.id:s for s in SOURCES}
AIRLINES=[s for s in SOURCES if s.category=="airline"]
CHARTERS=[s for s in SOURCES if s.category=="charter"]

def _dict(s:Source)->Dict[str,Any]:
    return asdict(s)

def all_sources()->List[Dict[str,Any]]:
    return [_dict(s) for s in SOURCES]

def source_by_id(source_id:str)->Optional[Dict[str,Any]]:
    s=SOURCES_BY_ID.get(str(source_id or "").strip())
    return _dict(s) if s else None

def _match_text(s:Source,q:str)->bool:
    q=str(q or "").strip().lower()
    if not q:return True
    hay=" ".join([s.id,s.name,s.publisher,s.what_it_covers,s.country,s.category,*s.topics]).lower()
    words=[w for w in re.findall(r"[a-záéíóúñü0-9]+",q) if len(w)>1]
    return not words or all(w in hay for w in words)

def get_sources(topic:str="official",query:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    t=str(topic or "").strip().lower()
    c=str(country or "").strip().lower()
    a=str(airline or "").strip().lower()
    out=[]
    for s in SOURCES:
        topic_ok=t in ("","official","all") or t in s.topics or t==s.category or t in s.id.lower() or t in s.name.lower()
        country_ok=not c or c in s.country.lower() or c in s.name.lower() or c in s.id.lower()
        airline_ok=not a or a in s.name.lower() or a in s.id.lower()
        if topic_ok and country_ok and airline_ok and _match_text(s,query):
            out.append(_dict(s))
    return out

def sources_for(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official","",country,airline)

def find_sources(query:str="",topic:str="",country:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official",query,country)

def official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return [x for x in get_sources(topic or "official","",country,airline) if x.get("verified") and x.get("type")=="official"]

def get_official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return official_sources(topic,country,airline)

def get_airlines(query:str="")->List[Dict[str,Any]]:
    q=str(query or "").strip().lower()
    return [_dict(s) for s in AIRLINES if not q or q in s.name.lower() or q in s.id.lower()]

def airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def find_airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def airline_list()->List[Dict[str,Any]]:
    return get_airlines()

def get_charters(query:str="")->List[Dict[str,Any]]:
    q=str(query or "").strip().lower()
    return [_dict(s) for s in CHARTERS if not q or q in s.name.lower() or q in s.id.lower()]

def get_charter_sources(query:str="")->List[Dict[str,Any]]:
    return get_charters(query)

def official_url(name_or_id:str)->str:
    q=str(name_or_id or "").strip().lower()
    if not q:return ""
    for s in SOURCES:
        if q in (s.id.lower(),s.name.lower()) or q in s.name.lower() or q in s.id.lower():
            return s.url
    return ""

__all__=["VERSION","VERIFICATION_DATE","Source","SOURCES","AIRLINES","CHARTERS","all_sources","get_sources","sources_for","find_sources","official_sources","get_official_sources","get_airlines","airlines","find_airlines","airline_list","get_charters","get_charter_sources","source_by_id","official_url"]
