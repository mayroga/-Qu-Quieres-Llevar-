# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List
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

def S(id,name,publisher,url,topics=(),covers="",limitations="",country="",category="official",type="official"):
    return Source(id,name,publisher,url,type,tuple(topics),covers,limitations,VERIFICATION_DATE,country,category)

SOURCES=[
S("tsa","Transportation Security Administration (TSA)","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening","baggage","security screening,carry-on,checked baggage,items","TSA rules do not replace airline or destination-country rules.","United States","security"),
S("tsa_what_can_i_bring","TSA — What Can I Bring?","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening/whatcanibring","items,baggage","searchable guidance for many travel items","Use the exact item and check the result; airline and destination rules may also apply.","United States","items"),
S("tsa_liquids","TSA — Liquids Rule","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening/liquids-rule","liquids,baggage","security screening of liquids","Security rules are separate from destination import rules.","United States","security"),
S("tsa_medication","TSA — Medication","U.S. Transportation Security Administration","https://www.tsa.gov/travel/tsa-cares/traveling-medication","medication,items","screening information for medication","Medication legality/import requirements can also depend on destination authorities.","United States","medication"),
S("tsa_batteries","TSA — Batteries","U.S. Transportation Security Administration","https://www.tsa.gov/travel/security-screening/whatcanibring/all","batteries,electronics","screening information for batteries and electronics","Check the airline and applicable dangerous-goods restrictions as well.","United States","security"),
S("cbp","U.S. Customs and Border Protection","U.S. Customs and Border Protection","https://www.cbp.gov/","customs,entry,documents","U.S. entry and customs information","Applies to U.S. customs and border matters, not every destination.","United States","customs"),
S("cbp_travel","CBP — Travelers","U.S. Customs and Border Protection","https://www.cbp.gov/travel","customs,documents","traveler information and entry/customs guidance","Check the applicable port and current official guidance.","United States","customs"),
S("state_travel","U.S. Department of State — Travel","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel.html","travel,documents,entry","international travel and destination information","Information is for U.S. travelers and does not replace destination authority instructions.","United States","travel"),
S("state_cuba","U.S. Department of State — Cuba","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html","cuba,travel,documents","U.S. traveler information concerning Cuba","Destination authorities may have additional requirements.","Cuba","cuba"),
S("cuba_dviajeros","D'Viajeros","Republic of Cuba — official travel declaration portal","https://dviajeros.mitrans.gob.cu/","cuba,dviajeros,documents","official Cuban traveler information/declaration process","Use the current official portal and follow its current instructions.","Cuba","cuba"),
S("cuba_aduana","Aduana General de la República de Cuba","Aduana General de la República de Cuba","https://www.aduana.gob.cu/","cuba,customs,baggage,items","Cuban customs requirements and traveler information","Customs rules can depend on the item, quantity and traveler circumstances.","Cuba","cuba"),
S("cuba_mitrans","Ministerio de Transporte de Cuba","Ministerio de Transporte de Cuba","https://www.mitrans.gob.cu/","cuba,transport,travel","Cuban transportation information","Use the specific current publication applicable to the journey.","Cuba","cuba"),
S("cuba_minrex","Ministerio de Relaciones Exteriores de Cuba","MINREX","https://cubaminrex.cu/","cuba,visa,documents","Cuban foreign-affairs and consular information","Visa/entry requirements can depend on nationality and purpose.","Cuba","cuba"),
S("cuba_evisa","Cuba eVisa","Cuba eVisa — official portal","https://evisacuba.cu/","cuba,visa,evisa,documents","official Cuba eVisa information and process","Confirm the currently applicable process for the traveler's nationality.","Cuba","visa"),
S("icao","International Civil Aviation Organization","ICAO","https://www.icao.int/","aviation,travel","international aviation framework and information","ICAO does not replace an airline's passenger conditions or a country's specific entry rules.","International","aviation"),
S("iata","International Air Transport Association","IATA","https://www.iata.org/","aviation,airlines,baggage","industry aviation information","IATA is not the passenger's airline and does not itself confirm a specific booking.","International","aviation"),
S("iata_travelcentre","IATA Travel Centre","IATA","https://www.iatatravelcentre.com/","documents,entry,visa,travel","travel-document and entry information","Use it as an orientation source and confirm with the destination authority.","International","travel"),
S("faa","Federal Aviation Administration","FAA","https://www.faa.gov/","aviation,safety","U.S. aviation safety information","FAA is not the authority for every international destination rule.","United States","aviation"),

S("aa","American Airlines","American Airlines","https://www.aa.com/","airline,flight,baggage","official airline booking, itinerary and baggage information","Conditions depend on route, fare, cabin and other circumstances.","United States","airline"),
S("aa_bags","American Airlines — Baggage","American Airlines","https://www.aa.com/i18n/travel-info/baggage/baggage.jsp","airline,baggage","official baggage information","Verify the baggage allowance attached to the specific reservation.","United States","airline"),
S("delta","Delta Air Lines","Delta Air Lines","https://www.delta.com/","airline,flight,baggage","official airline information","Schedules, fares and baggage conditions can change.","United States","airline"),
S("delta_bags","Delta — Baggage","Delta Air Lines","https://www.delta.com/us/en/baggage/overview","airline,baggage","official baggage information","Check the reservation-specific allowance.","United States","airline"),
S("united","United Airlines","United Airlines","https://www.united.com/","airline,flight,baggage","official airline information","Schedules and conditions can change.","United States","airline"),
S("united_bags","United — Baggage","United Airlines","https://www.united.com/en/us/fly/baggage.html","airline,baggage","official baggage information","Check the exact itinerary and fare.","United States","airline"),
S("southwest","Southwest Airlines","Southwest Airlines","https://www.southwest.com/","airline,flight,baggage","official airline information","Rules depend on current policy and itinerary.","United States","airline"),
S("jetblue","JetBlue","JetBlue Airways","https://www.jetblue.com/","airline,flight,baggage","official airline information","Check current baggage and fare conditions.","United States","airline"),
S("spirit","Spirit Airlines","Spirit Airlines","https://www.spirit.com/","airline,flight,baggage","official airline information","Baggage and fare conditions can vary.","United States","airline"),
S("frontier","Frontier Airlines","Frontier Airlines","https://www.flyfrontier.com/","airline,flight,baggage","official airline information","Check the purchased bundle/fare and itinerary.","United States","airline"),
S("copa","Copa Airlines","Copa Airlines","https://www.copaair.com/","airline,flight,baggage","official airline information","Check the specific route, fare and reservation.","Panama","airline"),
S("avianca","Avianca","Avianca","https://www.avianca.com/","airline,flight,baggage","official airline information","Conditions vary by fare and itinerary.","Colombia","airline"),
S("latam","LATAM Airlines","LATAM Airlines","https://www.latamairlines.com/","airline,flight,baggage","official airline information","Check the exact itinerary and fare.","Chile","airline"),
S("aeromexico","Aeroméxico","Aeroméxico","https://www.aeromexico.com/","airline,flight,baggage","official airline information","Check the current fare and itinerary conditions.","Mexico","airline"),
S("volaris","Volaris","Volaris","https://www.volaris.com/","airline,flight,baggage","official airline information","Check current baggage conditions for the reservation.","Mexico","airline"),
S("viva","Viva","Viva Aerobus","https://www.vivaaerobus.com/","airline,flight,baggage","official airline information","Check the current fare and route conditions.","Mexico","airline"),
S("southwest_cuba","Southwest — Cuba information","Southwest Airlines","https://www.southwest.com/","cuba,airline,baggage","official airline information when applicable","Do not infer current Cuba service from this registry; verify the current itinerary.","United States","airline"),
S("jetblue_cuba","JetBlue — Cuba information","JetBlue Airways","https://www.jetblue.com/","cuba,airline,baggage","official airline information when applicable","Do not infer current Cuba service from this registry; verify the current itinerary.","United States","airline"),
S("aa_cuba","American Airlines — Cuba information","American Airlines","https://www.aa.com/","cuba,airline,baggage","official airline information when applicable","Do not infer current service from this registry; verify the current itinerary.","United States","airline"),
S("copa_cuba","Copa Airlines — Cuba information","Copa Airlines","https://www.copaair.com/","cuba,airline,baggage","official airline information when applicable","Do not infer current service from this registry; verify the current itinerary.","Panama","airline"),
S("aeromexico_bags","Aeroméxico — Baggage","Aeroméxico","https://www.aeromexico.com/en-us/travel-information/baggage/carry-on-baggage","airline,baggage,cuba","official carry-on and baggage information","Verify the exact fare, route and current reservation conditions.","Mexico","airline"),
S("southwest_cuba_bags","Southwest — Cuba baggage restrictions","Southwest Airlines","https://support.southwest.com/helpcenter/article/baggage-embargo-for-checked-bags","cuba,baggage,airline","official baggage restriction information","Verify current Cuba restrictions before travel.","United States","airline"),
S("delta_cuba_bags","Delta — baggage restrictions","Delta Air Lines","https://es.delta.com/us/es/baggage/checked-baggage/embargoes-restrictions","cuba,baggage,airline","official baggage restriction information","Verify current route and seasonal restrictions.","United States","airline"),

S("mexico_gob","Gobierno de México","Gobierno de México","https://www.gob.mx/","mexico,entry,documents,customs","official Mexican government information","Use the agency-specific page for the exact requirement.","Mexico","destination"),
S("mexico_migracion","Instituto Nacional de Migración","Gobierno de México","https://www.gob.mx/inm","mexico,entry,documents","Mexican immigration information","Requirements depend on nationality and circumstances.","Mexico","destination"),
S("guatemala_gob","Gobierno de Guatemala","Gobierno de Guatemala","https://guatemala.gob.gt/","guatemala,travel,documents","official Guatemalan government information","Use the responsible agency's current instructions.","Guatemala","destination"),
S("honduras_gob","Gobierno de Honduras","Gobierno de Honduras","https://www.gob.hn/","honduras,travel,documents","official Honduran government information","Use the applicable immigration/customs authority.","Honduras","destination"),
S("elsalvador_gob","Gobierno de El Salvador","Gobierno de El Salvador","https://www.presidencia.gob.sv/","elsalvador,travel,documents","official Salvadoran government information","Use the applicable authority's current instructions.","El Salvador","destination"),
S("dominican_gob","Gobierno de República Dominicana","Gobierno de República Dominicana","https://www.gob.do/","dominican republic,travel,documents","official Dominican government information","Confirm immigration and customs requirements through the responsible authority.","Dominican Republic","destination"),

S("xael_charter","Xael Charters","Xael Charters","https://www.xaelcharter.com/","cuba,charter,flight,baggage","official charter operator information for Cuba travel","Verify current route, ticket, baggage allowance and conditions directly with the operator.","Cuba","charter"),
S("aerocuba","Aerocuba","Aerocuba","https://www.aerocuba.com/","cuba,charter,flight,baggage","official charter operator information for Cuba travel","Verify current route, ticket, baggage allowance and conditions directly with the operator.","Cuba","charter"),
S("cubazul","Cubazul Air Charter","Cubazul Air Charter","https://cubazulaircharter.com/","cuba,charter,flight,baggage","official charter operator information for Cuba travel","Verify current route, ticket, baggage allowance and conditions directly with the operator.","Cuba","charter"),
S("cuballama_charters","Cuballama Viajes — Charters","Cuballama Viajes","https://www.cuballama.com/viajes/vuelos/charters","cuba,charter,flight,baggage","official charter booking/operator information","Verify current route, ticket, baggage allowance and conditions directly with the operator.","Cuba","charter"),
]

AIRLINES=[x for x in SOURCES if x.category=="airline" and not x.id.endswith("_bags") and not x.id.endswith("_cuba")]
CHARTERS=[x for x in SOURCES if x.category=="charter"]

def _dict(s):
    d=asdict(s)
    d["topics"]=list(d["topics"])
    return d

def all_sources():
    return [_dict(x) for x in SOURCES]

def get_sources(topic:str="official",query:str=""):
    t=(topic or "official").lower().strip()
    q=(query or "").lower().strip()
    words=set(re.findall(r"[a-z0-9áéíóúñü'-]+",q))
    out=[]
    for s in SOURCES:
        blob=" ".join([s.id,s.name,s.publisher,s.url,s.type,s.country,s.category,s.what_it_covers,s.limitations," ".join(s.topics)]).lower()
        topic_match=t in ("","official","all") or t in s.topics or t in s.category or t in s.id
        query_match=not words or any(w in blob for w in words)
        if topic_match and query_match:
            out.append(_dict(s))
    if not out and q:
        for s in SOURCES:
            blob=(s.name+" "+s.what_it_covers+" "+" ".join(s.topics)).lower()
            if q in blob:
                out.append(_dict(s))
    return out[:30]

def sources_for(topic="",query=""):
    return get_sources(topic,query)

def find_sources(topic="",query=""):
    return get_sources(topic,query)

def official_sources(topic="",query=""):
    return get_sources(topic,query)

def get_airlines(query=""):
    q=(query or "").lower().strip()
    if not q:
        return [_dict(x) for x in AIRLINES]
    return [_dict(x) for x in AIRLINES if q in (x.name+" "+x.publisher+" "+x.country).lower() or any(q in t.lower() for t in x.topics)]

def airlines(query=""):
    return get_airlines(query)

def find_airlines(query=""):
    return get_airlines(query)

def airline_list(query=""):
    return get_airlines(query)

def get_charters(query=""):
    q=(query or "").lower().strip()
    if not q:
        return [_dict(x) for x in CHARTERS]
    return [_dict(x) for x in CHARTERS if q in (x.name+" "+x.publisher+" "+x.country).lower() or any(q in t.lower() for t in x.topics)]

def charters(query=""):
    return get_charters(query)

def find_charters(query=""):
    return get_charters(query)

def charter_list(query=""):
    return get_charters(query)

def get_cuba_official_sources(query=""):
    q=(query or "").lower().strip()
    out=[x for x in SOURCES if x.category in ("cuba","visa") and x.country=="Cuba"]
    if not q:
        return [_dict(x) for x in out]
    return [_dict(x) for x in out if q in (x.name+" "+x.publisher+" "+x.what_it_covers+" "+" ".join(x.topics)).lower()]

def cuba_official_sources(query=""):
    return get_cuba_official_sources(query)

def source_by_id(source_id:str):
    for s in SOURCES:
        if s.id==source_id:
            return _dict(s)
    return None

def official_url(source_id:str):
    x=source_by_id(source_id)
    return x.get("url") if x else ""

def source_url(source_id:str):
    return official_url(source_id)

__all__=["VERSION","VERIFICATION_DATE","Source","SOURCES","AIRLINES","CHARTERS","all_sources","get_sources","sources_for","find_sources","official_sources","get_airlines","airlines","find_airlines","airline_list","get_charters","charters","find_charters","charter_list","get_cuba_official_sources","cuba_official_sources","source_by_id","official_url","source_url"]
