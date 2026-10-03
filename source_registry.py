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
    if isinstance(value,str):
        return tuple(x.strip() for x in value.split(",") if x.strip())
    return tuple(str(x).strip() for x in value if str(x).strip())

def S(id,name,publisher,url,topics=(),covers="",limitations="",country="",category="official",type="official"):
    return Source(str(id),str(name),str(publisher),str(url),str(type),_topics(topics),str(covers),str(limitations),VERIFICATION_DATE,str(country),str(category))

SOURCES=[
S("tsa","Transportation Security Administration (TSA)","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening","baggage","security screening,carry-on,checked baggage,items","TSA rules do not replace airline or destination-country rules.","United States","security"),
S("tsa_what_can_i_bring","TSA — What Can I Bring?","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening/whatcanibring","items,baggage","searchable guidance for many travel items","Check the exact item; airline and destination rules may also apply.","United States","items"),
S("tsa_liquids","TSA — Liquids Rule","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening/liquids-rule","liquids,baggage,security","security screening of liquids","Security rules are separate from destination import rules.","United States","security"),
S("tsa_medication","TSA — Medication","U.S. Transportation Security Administration","https://www.tsa.gov/travel/tsa-cares/traveling-medication","medication,items,baggage","screening information for medication","Medication legality and import requirements may also depend on destination authorities.","United States","medication"),
S("tsa_batteries","TSA — Batteries","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening/whatcanibring/all","batteries,electronics,security","screening information for batteries and electronics","Check airline and dangerous-goods restrictions as well.","United States","security"),
S("cbp","U.S. Customs and Border Protection","U.S. Customs and Border Protection","https://www.cbp.gov/","customs,entry,documents","U.S. entry and customs information","Applies to U.S. customs and border matters.","United States","customs"),
S("cbp_travel","CBP — Travelers","U.S. Customs and Border Protection","https://www.cbp.gov/travel","customs,documents,entry","traveler information and entry/customs guidance","Check the applicable port and current instructions.","United States","customs"),
S("state_travel","U.S. Department of State — Travel","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel.html","travel,documents,entry,visa","international travel and destination information","U.S. traveler information does not replace destination authority instructions.","United States","travel"),
S("state_cuba","U.S. Department of State — Cuba","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html","cuba,travel,documents,entry","U.S. traveler information concerning Cuba","Destination authorities may have additional requirements.","Cuba","cuba"),
S("cuba_dviajeros","D'Viajeros","Republic of Cuba — official traveler declaration portal","https://dviajeros.mitrans.gob.cu/","cuba,dviajeros,documents,entry","official Cuban traveler declaration process","Use the current official portal and follow its current instructions.","Cuba","cuba"),
S("cuba_aduana","Aduana General de la República de Cuba","Aduana General de la República de Cuba","https://www.aduana.gob.cu/","cuba,customs,baggage,items,prohibited","Cuban customs requirements, baggage and traveler information","Rules can depend on item, quantity and traveler circumstances.","Cuba","cuba"),
S("cuba_mitrans","Ministerio de Transporte de Cuba","Ministerio de Transporte de Cuba","https://www.mitrans.gob.cu/","cuba,transport,travel,dviajeros","Cuban transportation information and D'Viajeros-related information","Use the specific current publication applicable to the journey.","Cuba","cuba"),
S("cuba_minrex","Ministerio de Relaciones Exteriores de Cuba","MINREX","https://cubaminrex.cu/","cuba,visa,documents,consular,entry","Cuban foreign-affairs and consular information","Visa and entry requirements can depend on nationality and purpose.","Cuba","cuba"),
S("cuba_evisa","Cuba eVisa — Official Portal","Cuba eVisa","https://evisacuba.cu/","cuba,visa,evisa,documents,entry","official electronic visa portal","Eligibility and procedure can depend on nationality, point of departure and purpose; verify the current instructions.","Cuba","visa"),
S("cuba_travel_regulations","Cuba Travel — Regulations and Formalities","Cuba Travel / Cuban tourism authorities","https://www.cuba.travel/en/useful-information/regulations-and-formalities","cuba,visa,entry,documents,customs,baggage","Cuba entry, visa and customs orientation","Confirm the final requirement with the responsible Cuban authority or official portal.","Cuba","cuba"),
S("icao","International Civil Aviation Organization","ICAO","https://www.icao.int/","aviation,travel,safety","international aviation framework and information","ICAO does not replace airline conditions or country-specific entry rules.","International","aviation"),
S("iata","International Air Transport Association","IATA","https://www.iata.org/","aviation,airlines,baggage","industry aviation information","IATA is not the passenger's airline and does not confirm a specific booking.","International","aviation"),
S("iata_travelcentre","IATA Travel Centre","IATA","https://www.iatatravelcentre.com/","documents,entry,visa,travel","travel-document and entry information","Use as orientation and confirm with the destination authority.","International","travel"),
S("faa","Federal Aviation Administration","FAA","https://www.faa.gov/","aviation,safety","U.S. aviation safety information","FAA is not the authority for every international destination rule.","United States","aviation"),

S("aa","American Airlines","American Airlines","https://www.aa.com/","airline,flight,baggage,cuba","official airline booking, itinerary and travel information","Conditions depend on route, fare, cabin, date and reservation.","United States","airline"),
S("aa_bags","American Airlines — Baggage","American Airlines","https://www.aa.com/web/i18n/travel-info/baggage/checked-baggage-policy.html","airline,baggage,cuba,checked_baggage","official baggage policy including Cuba-specific limitations","For Cuba, current published policy allows up to 2 checked bags with a maximum of 70 lb/32 kg each, plus 1 carry-on and 1 personal item; fees and seasonal exceptions may apply. Verify the reservation.","United States","airline"),
S("aa_cuba","American Airlines — Travel to Cuba","American Airlines","https://www.aa.com/web/i18n/travel-info/international-travel/cuba.html","cuba,airline,entry,documents,baggage","American Airlines Cuba travel preparation and documentation information","Requirements and policies can change; verify the current reservation and official instructions.","United States","airline"),
S("delta","Delta Air Lines","Delta Air Lines","https://www.delta.com/","airline,flight,baggage,cuba","official airline information","Schedules, fares and baggage conditions can change.","United States","airline"),
S("delta_bags","Delta — Baggage","Delta Air Lines","https://www.delta.com/us/en/baggage/overview","airline,baggage","official baggage information","Check the reservation-specific allowance.","United States","airline"),
S("delta_cuba_bags","Delta — Baggage Embargoes and Destination Restrictions","Delta Air Lines","https://es.delta.com/us/es/baggage/checked-baggage/embargoes-restrictions","cuba,airline,baggage,checked_baggage,restrictions","current destination-specific baggage restrictions including Havana","Delta publishes different Cuba limits depending on ticket purchase date and season; verify the exact itinerary before travel.","United States","airline"),
S("united","United Airlines","United Airlines","https://www.united.com/","airline,flight,baggage,cuba","official airline information","Schedules and conditions can change.","United States","airline"),
S("united_bags","United — Baggage","United Airlines","https://www.united.com/en/us/fly/baggage.html","airline,baggage","official baggage information","Check the exact itinerary and fare.","United States","airline"),
S("southwest","Southwest Airlines","Southwest Airlines","https://www.southwest.com/","airline,flight,baggage,cuba","official airline information","Rules depend on current policy and itinerary.","United States","airline"),
S("southwest_bags","Southwest — Baggage Embargoes","Southwest Airlines","https://support.southwest.com/helpcenter/article/baggage-embargo-for-checked-bags","cuba,airline,baggage,checked_baggage,restrictions","Cuba-specific checked baggage embargo information","Southwest currently states that Cuba has a year-round embargo; maximum 2 checked bags and bags over 50 lb or 62 linear inches are not accepted. Verify the current policy.","United States","airline"),
S("jetblue","JetBlue","JetBlue Airways","https://www.jetblue.com/","airline,flight,baggage,cuba","official airline information","Check current baggage and fare conditions.","United States","airline"),
S("spirit","Spirit Airlines","Spirit Airlines","https://www.spirit.com/","airline,flight,baggage","official airline information","Baggage and fare conditions can vary.","United States","airline"),
S("frontier","Frontier Airlines","Frontier Airlines","https://www.flyfrontier.com/","airline,flight,baggage","official airline information","Check the purchased bundle/fare and itinerary.","United States","airline"),
S("copa","Copa Airlines","Copa Airlines","https://www.copaair.com/","airline,flight,baggage,cuba","official airline information","Check the specific route, fare and reservation.","Panama","airline"),
S("copa_cuba","Copa Airlines — Cuba information","Copa Airlines","https://www.copaair.com/","cuba,airline,baggage,flight","official airline information when applicable","Do not infer current Cuba service from this registry; verify the current itinerary.","Panama","airline"),
S("avianca","Avianca","Avianca","https://www.avianca.com/","airline,flight,baggage","official airline information","Conditions vary by fare and itinerary.","Colombia","airline"),
S("latam","LATAM Airlines","LATAM Airlines","https://www.latamairlines.com/","airline,flight,baggage","official airline information","Check the exact itinerary and fare.","Chile","airline"),
S("aeromexico","Aeroméxico","Aeroméxico","https://www.aeromexico.com/","airline,flight,baggage,cuba","official airline information","Check the current fare, route and reservation conditions.","Mexico","airline"),
S("aeromexico_bags","Aeroméxico — Baggage","Aeroméxico","https://www.aeromexico.com/en-us/travel-information/baggage/carry-on-baggage","airline,baggage,carry_on,checked_baggage","official baggage information and fare-related baggage conditions","Allowance varies by fare, route and ticket conditions; verify the specific reservation.","Mexico","airline"),
S("volaris","Volaris","Volaris","https://www.volaris.com/","airline,flight,baggage","official airline information","Check current baggage conditions for the reservation.","Mexico","airline"),
S("viva","Viva Aerobus","Viva Aerobus","https://www.vivaaerobus.com/","airline,flight,baggage","official airline information","Check the current fare and route conditions.","Mexico","airline"),

S("mexico_gob","Gobierno de México","Gobierno de México","https://www.gob.mx/","mexico,entry,documents,customs","official Mexican government information","Use the agency-specific page for the exact requirement.","Mexico","destination"),
S("mexico_migracion","Instituto Nacional de Migración","Gobierno de México","https://www.gob.mx/inm","mexico,entry,documents","Mexican immigration information","Requirements depend on nationality and circumstances.","Mexico","destination"),
S("guatemala_gob","Gobierno de Guatemala","Gobierno de Guatemala","https://guatemala.gob.gt/","guatemala,travel,documents","official Guatemalan government information","Use the responsible agency's current instructions.","Guatemala","destination"),
S("honduras_gob","Gobierno de Honduras","Gobierno de Honduras","https://www.gob.hn/","honduras,travel,documents","official Honduran government information","Use the applicable immigration/customs authority.","Honduras","destination"),
S("elsalvador_gob","Gobierno de El Salvador","Gobierno de El Salvador","https://www.presidencia.gob.sv/","elsalvador,travel,documents","official Salvadoran government information","Use the applicable authority's current instructions.","El Salvador","destination"),
S("dominican_gob","Gobierno de República Dominicana","Gobierno de República Dominicana","https://www.gob.do/","dominican republic,travel,documents","official Dominican government information","Confirm immigration and customs requirements through the responsible authority.","Dominican Republic","destination"),

S("xael_charter","Xael Charters","Xael Charters","https://www.xaelcharter.com/","cuba,charter,flight,baggage,travel","official charter operator information for flights and travel services to Cuba","Baggage conditions can depend on the flight and current booking terms; verify the ticket. The current site advertises regular baggage pricing by pound, but this should not be treated as a universal allowance.","United States","charter"),
S("xael_charter_baggage","Xael Charters — Flights to Cuba","Xael Charters","https://www.xaelcharter.com/","cuba,charter,baggage,checked_baggage","official operator information for Cuba flights and baggage services","Current site information may change by route, date and booking; verify the exact ticket before travel.","United States","charter"),
S("aerocuba","Aerocuba","Aerocuba","https://www.aerocuba.com/","cuba,charter,flight,baggage,travel","official Aerocuba travel and charter information","Baggage allowances and charges must be confirmed for the purchased flight and route.","United States","charter"),
S("cubazul","Cubazul Air Charter","Cubazul Air Charter","https://cubazulaircharter.com/","cuba,charter,flight,baggage,travel","official Cubazul Air Charter flight and reservation information","Baggage terms, prices and capacity can change; verify the exact ticket and current operator instructions.","United States","charter"),
S("cubazul_baggage","Cubazul Air Charter — Services and Information","Cubazul Air Charter","https://cubazulaircharter.com/Contact.html?lang=en","cuba,charter,baggage,travel,documents","official operator information, terms and travel-service details","Historical or third-party baggage amounts must not be treated as current unless confirmed by the operator.","United States","charter"),
S("cuballama_charters","Cuballama Viajes — Vuelos Charters a Cuba","Cuballama Viajes","https://www.cuballama.com/viajes/vuelos/charters","cuba,charter,flight,travel,baggage","current charter search and travel information for Cuba from U.S. cities","Dates, prices, routes and baggage depend on the selected charter and booking.","United States","charter"),
S("cuballama_terms","Cuballama Viajes — Términos y condiciones","Cuballama Viajes","https://www.cuballama.com/viajes/terminos","cuba,charter,baggage,terms","travel and baggage terms published by Cuballama","Cuballama states that there is no single standard baggage policy and advises checking the selected provider or airline before travel.","United States","charter"),

S("cuba_charter_baggage_guide","Guía de Equipaje para Vuelos Chárter a Cuba","May Roga LLC — source-guided module","https://www.xaelcharter.com/","cuba,charter,baggage,checked_baggage,carry_on","orientation module for comparing charter baggage information from named operators","This is an orientation layer, not an operator tariff. Exact weight, number of pieces and price must be confirmed with the operator or ticket.","Cuba","charter_guide"),
S("cuba_commercial_baggage_guide","Políticas de Equipaje para Aerolíneas Comerciales hacia Cuba","May Roga LLC — source-guided module","https://www.aa.com/web/i18n/travel-info/baggage/checked-baggage-policy.html","cuba,airline,baggage,checked_baggage,carry_on","orientation module linking users to current airline policies for Cuba","Rules vary by airline, route, fare, ticket date, travel date and season; the airline's current official page controls.","Cuba","airline_guide"),
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
    blob=" ".join([
        s.id,s.name,s.publisher,s.url,s.type,s.country,s.category,
        s.what_it_covers,s.limitations," ".join(s.topics)
    ]).lower()
    words=_tokens(q)
    return all(w in blob for w in words)

def get_sources(topic:str="official",query:str="")->List[Dict[str,Any]]:
    t=_normalize(topic)
    q=_normalize(query)
    if t in {"","official","all","any"}:
        candidates=SOURCES
    else:
        candidates=[s for s in SOURCES if t in {x.lower() for x in s.topics} or t==s.category.lower() or t==s.id.lower() or t in s.name.lower()]
    out=[_dict(s) for s in candidates if _matches_query(s,q)]
    if not out and q:
        compact=q.replace(" ","")
        for s in SOURCES:
            blob=(s.name+" "+s.what_it_covers+" "+" ".join(s.topics)).lower()
            if compact and compact in blob.replace(" ",""):
                out.append(_dict(s))
    return out[:50]

def sources_for(topic:str="",query:str="")->List[Dict[str,Any]]:
    return get_sources(topic,query)

def find_sources(topic:str="",query:str="")->List[Dict[str,Any]]:
    return get_sources(topic,query)

def official_sources(topic:str="",query:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official",query)

def get_official_sources(topic:str="",query:str="")->List[Dict[str,Any]]:
    if topic or query:
        return get_sources(topic or "official",query)
    return [_dict(x) for x in SOURCES if x.type=="official"]

def get_airlines(query:str="")->List[Dict[str,Any]]:
    q=_normalize(query)
    if not q:return [_dict(x) for x in AIRLINES]
    return [_dict(x) for x in AIRLINES if q in (x.name+" "+x.publisher+" "+x.country).lower() or any(q in t.lower() for t in x.topics) or q in x.id.lower()]

def airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def find_airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def airline_list(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def get_charters(query:str="")->List[Dict[str,Any]]:
    q=_normalize(query)
    if not q:return [_dict(x) for x in CHARTERS]
    return [_dict(x) for x in CHARTERS if q in (x.name+" "+x.publisher+" "+x.country).lower() or any(q in t.lower() for t in x.topics) or q in x.id.lower()]

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
        if s.id.lower()==sid:
            return _dict(s)
    return None

def official_url(source_id:str)->str:
    x=source_by_id(source_id)
    return x.get("url","") if x else ""

def source_url(source_id:str)->str:
    return official_url(source_id)

__all__=[
    "VERSION","VERIFICATION_DATE","Source","S","SOURCES","AIRLINES","CHARTERS",
    "CUBA_OFFICIAL","CUBA_AIRLINE_SOURCES","all_sources","get_sources",
    "sources_for","find_sources","official_sources","get_official_sources",
    "get_airlines","airlines","find_airlines","airline_list","get_charters",
    "charters","find_charters","charter_list","get_cuba_official_sources",
    "cuba_official_sources","get_cuba_airline_sources","source_by_id",
    "official_url","source_url"
]
