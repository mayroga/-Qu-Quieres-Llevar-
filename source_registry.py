# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v13.0.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional
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
    fixed:bool=False
    priority:int=50

def S(id:str,name:str,publisher:str,url:str,topics:Any=(),what_it_covers:str="",limitations:str="",country:str="",category:str="official",type:str="official",verified:bool=True,fixed:bool=False,priority:int=50)->Source:
    if isinstance(topics,str):topics=(topics,)
    else:topics=tuple(topics or ())
    return Source(id=id,name=name,publisher=publisher,url=url,type=type,topics=topics,what_it_covers=what_it_covers,limitations=limitations,country=country,category=category,verified=verified,fixed=fixed,priority=priority)

SOURCES=[
S("dviajeros","D'Viajeros","República de Cuba","https://dviajeros.mitrans.gob.cu/","cuba,dviajeros,entry,documents,form","Formulario oficial de entrada a Cuba","La presentación real se hace en el sitio oficial","CU","cuba",fixed=True,priority=1),
S("evisa_cuba","Cuba eVisa","MINREX","https://evisacuba.cu/","cuba,visa,evisa,entry,documents,form","Información y proceso oficial de e-Visa de Cuba","La solicitud real se realiza en el sitio oficial","CU","visa",fixed=True,priority=2),
S("cuba_aduana","Aduana General de la República de Cuba","Aduana de Cuba","https://www.aduana.gob.cu/","cuba,customs,baggage,item,entry,exit","Información oficial de aduana y equipaje","Las reglas pueden cambiar","CU","customs",fixed=True,priority=3),
S("cuba_minrex","MINREX","Ministerio de Relaciones Exteriores de Cuba","https://cubaminrex.cu/","cuba,visa,documents,entry,exit","Información oficial sobre asuntos consulares y entrada","Los requisitos dependen del caso y nacionalidad","CU","cuba",fixed=True,priority=4),
S("cuba_mitrans","MITRANS","Ministerio de Transporte de Cuba","https://www.mitrans.gob.cu/","cuba,transport,aviation,travel","Información oficial de transporte","Verificar avisos vigentes","CU","cuba",fixed=True,priority=5),
S("state_cuba","Cuba Travel Information","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html","cuba,travel,documents,entry","Información del Departamento de Estado de EE.UU.","No sustituye a las autoridades cubanas","US/CU","cuba",priority=10),
S("tsa","TSA","Transportation Security Administration","https://www.tsa.gov/","security,baggage,item,travel","Seguridad y control de pasajeros en EE.UU.","No sustituye las reglas de la aerolínea o destino","US","security",priority=20),
S("tsa_bring","What Can I Bring","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring","baggage,item,security","Consulta de artículos permitidos","La decisión final en el control corresponde a TSA","US","security",priority=21),
S("tsa_liquids","Liquids Rule","TSA","https://www.tsa.gov/travel/security-screening/liquids-rule","liquids,baggage,security,item","Reglas de líquidos","También pueden aplicar reglas de aerolínea y destino","US","security",priority=22),
S("tsa_medication","Medication","TSA","https://www.tsa.gov/travel/secure-flight/traveling-medication","medication,baggage,security,item","Información de medicamentos durante el control","El país de destino puede tener reglas adicionales","US","security",priority=23),
S("tsa_batteries","Batteries","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring/all","battery,electronics,baggage,item","Información de baterías y electrónicos","También pueden aplicar límites de aerolínea","US","security",priority=24),
S("cbp","CBP","U.S. Customs and Border Protection","https://www.cbp.gov/","customs,entry,travel,baggage","Información oficial de aduanas y entrada a EE.UU.","No determina las reglas de Cuba","US","customs",priority=25),
S("cbp_travel","CBP Travelers","U.S. Customs and Border Protection","https://www.cbp.gov/travel","customs,entry,baggage","Información para viajeros","Aplica a procesos de entrada a EE.UU.","US","customs",priority=26),
S("state_travel","Travel.State.Gov","U.S. Department of State","https://travel.state.gov/","travel,documents,entry,visa","Información de viajes y destinos","Verificar siempre el caso concreto","US/INT","travel",priority=27),
S("iata","IATA","International Air Transport Association","https://www.iata.org/","aviation,flight,baggage","Información general de aviación","No sustituye las condiciones de una aerolínea","INT","aviation",priority=30),
S("iata_travel","IATA Travel Centre","IATA","https://www.iatatravelcentre.com/","travel,documents,visa,entry","Herramienta de información de documentos de viaje","Confirmar siempre con la autoridad oficial","INT","travel",priority=31),
S("faa","FAA","Federal Aviation Administration","https://www.faa.gov/","aviation,flight,battery","Información de seguridad aérea de EE.UU.","No determina la franquicia individual de equipaje","US","aviation",priority=32),
S("icao","ICAO","International Civil Aviation Organization","https://www.icao.int/","aviation,flight","Información internacional de aviación","No determina reglas particulares de aerolíneas","INT","aviation",priority=33),

S("american","American Airlines","American Airlines","https://www.aa.com/","airline,flight,baggage,booking,cuba","Sitio oficial para vuelos, reservas y equipaje","Consultar condiciones del itinerario y tarifa","US","airline",fixed=True,priority=40),
S("delta","Delta Air Lines","Delta Air Lines","https://www.delta.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=41),
S("southwest","Southwest Airlines","Southwest Airlines","https://www.southwest.com/","airline,flight,baggage,booking,cuba","Sitio oficial de vuelos y reservas","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=42),
S("united","United Airlines","United Airlines","https://www.united.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=43),
S("jetblue","JetBlue","JetBlue","https://www.jetblue.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=44),
S("frontier","Frontier Airlines","Frontier Airlines","https://www.flyfrontier.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=45),
S("spirit","Spirit Airlines","Spirit Airlines","https://www.spirit.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=46),
S("copa","Copa Airlines","Copa Airlines","https://www.copaair.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Puede servir para itinerarios con conexión; verificar ruta actual","PA","airline",fixed=True,priority=47),
S("avianca","Avianca","Avianca","https://www.avianca.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Verificar rutas actuales","CO","airline",fixed=True,priority=48),
S("latam","LATAM Airlines","LATAM Airlines","https://www.latamairlines.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Verificar rutas actuales","CL","airline",fixed=True,priority=49),
S("aeromexico","Aeroméxico","Aeroméxico","https://www.aeromexico.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Verificar rutas actuales","MX","airline",fixed=True,priority=50),
S("volaris","Volaris","Volaris","https://www.volaris.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Verificar rutas actuales","MX","airline",fixed=True,priority=51),
S("viva","Viva Aerobus","Viva Aerobus","https://www.vivaaerobus.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Verificar rutas actuales","MX","airline",fixed=True,priority=52),

S("xael","Xael Charters","Xael Charters","https://www.xaelcharter.com/","charter,cuba,flight,booking","Sitio oficial del operador charter","Disponibilidad, rutas y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=60),
S("aerocuba","Aerocuba","Cuba Charter Services / Aerocuba","https://www.aerocuba.com/","charter,cuba,flight,booking","Sitio oficial del operador charter","Disponibilidad, rutas y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=61),
S("cubazul","Cubazul Air Charter","Cubazul Air Charter","https://cubazulaircharter.com/","charter,cuba,flight,booking","Sitio oficial del operador charter","Disponibilidad, rutas y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=62),
S("cuballama_viajes","Cuballama Viajes","Cuballama","https://www.cuballama.com/viajes/vuelos/charters","charter,cuba,flight,booking","Página oficial de viajes y charters de Cuballama","Disponibilidad y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=63),

S("mexico","Gobierno de México","Gobierno de México","https://www.gob.mx/","mexico,entry,documents","Información oficial mexicana","Consultar autoridad correspondiente","MX","destination"),
S("guatemala","Gobierno de Guatemala","Gobierno de Guatemala","https://guatemala.gob.gt/","guatemala,entry,documents","Información oficial guatemalteca","Consultar autoridad correspondiente","GT","destination"),
S("honduras","Gobierno de Honduras","Gobierno de Honduras","https://www.gob.hn/","honduras,entry,documents","Información oficial hondureña","Consultar autoridad correspondiente","HN","destination"),
S("elsalvador","Gobierno de El Salvador","Gobierno de El Salvador","https://www.presidencia.gob.sv/","elsalvador,entry,documents","Información oficial salvadoreña","Consultar autoridad correspondiente","SV","destination"),
S("dominican_republic","Gobierno de República Dominicana","Gobierno de República Dominicana","https://www.gob.do/","dominican_republic,entry,documents","Información oficial dominicana","Consultar autoridad correspondiente","DO","destination")
]

SOURCES_BY_ID={s.id:s for s in SOURCES}
AIRLINES=[s for s in SOURCES if s.category=="airline"]
CHARTERS=[s for s in SOURCES if s.category=="charter"]

def _dict(s:Source)->Dict[str,Any]:
    return asdict(s)

def all_sources()->List[Dict[str,Any]]:
    return [_dict(s) for s in sorted(SOURCES,key=lambda x:x.priority)]

def source_by_id(source_id:str)->Optional[Dict[str,Any]]:
    s=SOURCES_BY_ID.get(str(source_id or "").strip().lower())
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
    for s in sorted(SOURCES,key=lambda x:x.priority):
        topic_ok=t in ("","official","all") or t in s.topics or t==s.category or t in s.id.lower() or t in s.name.lower()
        country_ok=not c or c in s.country.lower() or c in s.name.lower() or c in s.id.lower()
        airline_ok=not a or a in s.name.lower() or a in s.id.lower()
        if topic_ok and country_ok and airline_ok and _match_text(s,query):out.append(_dict(s))
    return out

def sources_for(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official","",country,airline)

def find_sources(query:str="",topic:str="",country:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official",query,country)

def official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return [x for x in get_sources(topic or "official","",country,airline) if x.get("verified") and x.get("type")=="official"]

def get_official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return official_sources(topic,country,airline)

def fixed_sources()->List[Dict[str,Any]]:
    return [_dict(s) for s in sorted(SOURCES,key=lambda x:x.priority) if s.fixed]

def get_airlines(query:str="")->List[Dict[str,Any]]:
    q=str(query or "").strip().lower()
    return [_dict(s) for s in sorted(AIRLINES,key=lambda x:x.priority) if not q or q in s.name.lower() or q in s.id.lower()]

def airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def find_airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def airline_list()->List[Dict[str,Any]]:
    return get_airlines()

def get_charters(query:str="")->List[Dict[str,Any]]:
    q=str(query or "").strip().lower()
    return [_dict(s) for s in sorted(CHARTERS,key=lambda x:x.priority) if not q or q in s.name.lower() or q in s.id.lower()]

def get_charter_sources(query:str="")->List[Dict[str,Any]]:
    return get_charters(query)

def official_url(name_or_id:str)->str:
    q=str(name_or_id or "").strip().lower()
    if not q:return ""
    for s in SOURCES:
        if q==s.id.lower() or q==s.name.lower() or q in s.name.lower() or q in s.id.lower():return s.url
    return ""

def answer_sources(question:str="",item:str="",airline:str="",country:str="")->List[Dict[str,Any]]:
    q=f"{question} {item}".strip()
    found=[]
    if airline:found.extend(get_sources("airline",q,country,airline))
    if item or "llevar" in q.lower() or "equipaje" in q.lower():
        found.extend(get_sources("item",q,country))
        found.extend(get_sources("baggage",q,country,airline))
    if "cuba" in q.lower() or country.lower() in ("cuba","cu"):
        found.extend(get_sources("cuba","",country,airline))
    if not found:found=official_sources("official",country,airline)
    seen=set();out=[]
    for x in found:
        if x["id"] not in seen:
            seen.add(x["id"]);out.append(x)
    return out

__all__=["VERSION","VERIFICATION_DATE","Source","SOURCES","AIRLINES","CHARTERS","all_sources","source_by_id","get_sources","sources_for","find_sources","official_sources","get_official_sources","fixed_sources","get_airlines","airlines","find_airlines","airline_list","get_charters","get_charter_sources","official_url","answer_sources"]
