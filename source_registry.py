# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v15.0.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional
import re

VERSION="15.0.0"
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
S("dviajeros","D'Viajeros","República de Cuba","https://dviajeros.mitrans.gob.cu/","cuba,dviajeros,entry,documents,form,simulation","Formulario oficial de entrada a Cuba","La presentación real se hace únicamente en el sitio oficial","CU","cuba",fixed=True,priority=1),
S("evisa_cuba","Cuba eVisa","MINREX","https://evisacuba.cu/","cuba,visa,evisa,entry,documents,form,simulation","Información y proceso oficial de e-Visa de Cuba","La solicitud real se realiza únicamente en el sitio oficial","CU","visa",fixed=True,priority=2),
S("cuba_aduana","Aduana General de la República de Cuba","Aduana de Cuba","https://www.aduana.gob.cu/","cuba,customs,baggage,item,entry,exit,food,medication","Información oficial de aduana, equipaje y artículos","Las reglas pueden cambiar y dependen del caso","CU","customs",fixed=True,priority=3),
S("cuba_minrex","MINREX","Ministerio de Relaciones Exteriores de Cuba","https://cubaminrex.cu/","cuba,visa,documents,entry,exit,consular","Información oficial sobre asuntos consulares y entrada","Los requisitos dependen del caso y nacionalidad","CU","cuba",fixed=True,priority=4),
S("cuba_mitrans","MITRANS","Ministerio de Transporte de Cuba","https://www.mitrans.gob.cu/","cuba,transport,aviation,travel,airports,dviajeros","Información oficial de transporte y aviación","Verificar avisos vigentes","CU","transport",fixed=True,priority=5),
S("state_cuba","Cuba Travel Information","U.S. Department of State","https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html","cuba,travel,documents,entry,visa,security","Información del Departamento de Estado de EE.UU. sobre Cuba","No sustituye a las autoridades cubanas","US/CU","travel",priority=10),
S("tsa","TSA","Transportation Security Administration","https://www.tsa.gov/","security,baggage,item,travel,airport","Seguridad y control de pasajeros en EE.UU.","No sustituye las reglas de la aerolínea o del destino","US","security",priority=20),
S("tsa_bring","What Can I Bring","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring","baggage,item,security,carry_on,checked,food,medicine,electronics","Consulta de artículos permitidos en el control TSA","La decisión final en el control corresponde a TSA","US","security",priority=21),
S("tsa_liquids","Liquids Rule","TSA","https://www.tsa.gov/travel/security-screening/liquids-rule","liquids,baggage,security,item,carry_on","Reglas TSA para líquidos","También pueden aplicar reglas de aerolínea y destino","US","security",priority=22),
S("tsa_medication","Medication","TSA","https://www.tsa.gov/travel/secure-flight/traveling-medication","medication,baggage,security,item,medicine","Información TSA para medicamentos","El país de destino puede tener reglas adicionales","US","security",priority=23),
S("tsa_batteries","Batteries","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring/all","battery,batteries,electronics,baggage,item","Información TSA sobre baterías y electrónicos","También pueden aplicar límites de la aerolínea y otras autoridades","US","security",priority=24),
S("cbp","CBP","U.S. Customs and Border Protection","https://www.cbp.gov/","customs,entry,travel,baggage,food,agriculture","Información oficial de aduanas y entrada a EE.UU.","No determina las reglas de entrada a Cuba","US","customs",priority=25),
S("cbp_travel","CBP Travelers","U.S. Customs and Border Protection","https://www.cbp.gov/travel","customs,entry,baggage,travel","Información para viajeros que entran a EE.UU.","Aplica a procesos de entrada a EE.UU.","US","customs",priority=26),
S("state_travel","Travel.State.Gov","U.S. Department of State","https://travel.state.gov/","travel,documents,entry,visa,passport","Información general de viajes y destinos","Verificar siempre el caso concreto","US/INT","travel",priority=27),
S("iata","IATA","International Air Transport Association","https://www.iata.org/","aviation,flight,baggage,travel","Información general de aviación y transporte aéreo","No sustituye las condiciones de una aerolínea","INT","aviation",priority=30),
S("iata_travel","IATA Travel Centre","IATA","https://www.iatatravelcentre.com/","travel,documents,visa,entry,passport","Herramienta de referencia para documentos de viaje","Confirmar siempre con la autoridad oficial correspondiente","INT","travel",priority=31),
S("faa","FAA","Federal Aviation Administration","https://www.faa.gov/","aviation,flight,battery,baggage,electronics","Información de seguridad aérea de EE.UU.","No determina la franquicia individual de equipaje","US","aviation",priority=32),
S("icao","ICAO","International Civil Aviation Organization","https://www.icao.int/","aviation,flight,safety,travel","Información internacional de aviación civil","No determina reglas particulares de aerolíneas","INT","aviation",priority=33),

S("american","American Airlines","American Airlines","https://www.aa.com/","airline,flight,baggage,booking,cuba,miami","Sitio oficial para vuelos, reservas y equipaje","Consultar condiciones del itinerario y tarifa","US","airline",fixed=True,priority=40),
S("delta","Delta Air Lines","Delta Air Lines","https://www.delta.com/","airline,flight,baggage,booking,cuba","Sitio oficial de vuelos, reservas y equipaje","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=41),
S("southwest","Southwest Airlines","Southwest Airlines","https://www.southwest.com/","airline,flight,baggage,booking,cuba","Sitio oficial de vuelos y reservas","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=42),
S("united","United Airlines","United Airlines","https://www.united.com/","airline,flight,baggage,booking,cuba","Sitio oficial de vuelos, reservas y equipaje","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=43),
S("jetblue","JetBlue","JetBlue","https://www.jetblue.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=44),
S("frontier","Frontier Airlines","Frontier Airlines","https://www.flyfrontier.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=45),
S("spirit","Spirit Airlines","Spirit Airlines","https://www.spirit.com/","airline,flight,baggage,booking,cuba","Sitio oficial de la aerolínea","Consultar disponibilidad y condiciones actuales","US","airline",fixed=True,priority=46),
S("copa","Copa Airlines","Copa Airlines","https://www.copaair.com/","airline,flight,baggage,booking,cuba,connection","Puede servir para itinerarios con conexión; verificar ruta actual","Consultar ruta, conexión y condiciones actuales","PA","airline",fixed=True,priority=47),
S("avianca","Avianca","Avianca","https://www.avianca.com/","airline,flight,baggage,booking,cuba,connection","Sitio oficial de la aerolínea","Verificar rutas y condiciones actuales","CO","airline",fixed=True,priority=48),
S("latam","LATAM Airlines","LATAM Airlines","https://www.latamairlines.com/","airline,flight,baggage,booking,cuba,connection","Sitio oficial de la aerolínea","Verificar rutas y condiciones actuales","CL","airline",fixed=True,priority=49),
S("aeromexico","Aeroméxico","Aeroméxico","https://www.aeromexico.com/","airline,flight,baggage,booking,cuba,connection","Sitio oficial de la aerolínea","Verificar rutas y condiciones actuales","MX","airline",fixed=True,priority=50),
S("volaris","Volaris","Volaris","https://www.volaris.com/","airline,flight,baggage,booking,cuba,connection","Sitio oficial de la aerolínea","Verificar rutas y condiciones actuales","MX","airline",fixed=True,priority=51),
S("viva","Viva Aerobus","Viva Aerobus","https://www.vivaaerobus.com/","airline,flight,baggage,booking,cuba,connection","Sitio oficial de la aerolínea","Verificar rutas y condiciones actuales","MX","airline",fixed=True,priority=52),

S("xael","Xael Charters","Xael Charters","https://www.xaelcharter.com/","charter,cuba,flight,booking","Sitio oficial del operador charter","Disponibilidad, rutas y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=60),
S("aerocuba","Aerocuba","Cuba Charter Services / Aerocuba","https://www.aerocuba.com/","charter,cuba,flight,booking","Sitio oficial del operador charter","Disponibilidad, rutas y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=61),
S("cubazul","Cubazul Air Charter","Cubazul Air Charter","https://cubazulaircharter.com/","charter,cuba,flight,booking","Sitio oficial del operador charter","Disponibilidad, rutas y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=62),
S("cuballama_viajes","Cuballama Viajes","Cuballama","https://www.cuballama.com/viajes/vuelos/charters","charter,cuba,flight,booking","Página oficial de viajes y charters de Cuballama","Disponibilidad y condiciones deben confirmarse directamente","US/CU","charter",fixed=True,priority=63),

S("mexico","Gobierno de México","Gobierno de México","https://www.gob.mx/","mexico,entry,documents,travel","Información oficial mexicana","Consultar la autoridad correspondiente","MX","destination"),
S("guatemala","Gobierno de Guatemala","Gobierno de Guatemala","https://guatemala.gob.gt/","guatemala,entry,documents,travel","Información oficial guatemalteca","Consultar la autoridad correspondiente","GT","destination"),
S("honduras","Gobierno de Honduras","Gobierno de Honduras","https://www.gob.hn/","honduras,entry,documents,travel","Información oficial hondureña","Consultar la autoridad correspondiente","HN","destination"),
S("elsalvador","Gobierno de El Salvador","Gobierno de El Salvador","https://www.presidencia.gob.sv/","elsalvador,entry,documents,travel","Información oficial salvadoreña","Consultar la autoridad correspondiente","SV","destination"),
S("dominican_republic","Gobierno de República Dominicana","Gobierno de República Dominicana","https://www.gob.do/","dominican_republic,entry,documents,travel","Información oficial dominicana","Consultar la autoridad correspondiente","DO","destination")
]

SOURCES_BY_ID={s.id:s for s in SOURCES}
AIRLINES=tuple(s for s in SOURCES if s.category=="airline")
CHARTERS=tuple(s for s in SOURCES if s.category=="charter")

def _dict(s:Source)->Dict[str,Any]:
    return asdict(s)

def all_sources()->List[Dict[str,Any]]:
    return [_dict(s) for s in sorted(SOURCES,key=lambda x:x.priority)]

def source_by_id(source_id:str)->Optional[Dict[str,Any]]:
    s=SOURCES_BY_ID.get(_s(source_id))
    return _dict(s) if s else None

def _s(v:Any)->str:
    return str(v or "").strip().lower()

def _tokens(q:str)->List[str]:
    return [x for x in re.findall(r"[a-záéíóúñü0-9]+",_s(q)) if len(x)>1]

def _match_text(s:Source,q:str)->bool:
    words=_tokens(q)
    if not words:return True
    hay=_s(" ".join([s.id,s.name,s.publisher,s.what_it_covers,s.country,s.category,*s.topics]))
    return all(w in hay for w in words)

def _topic_match(s:Source,t:str)->bool:
    t=_s(t)
    if not t or t in ("all","official"):return True
    if t in s.topics or t==_s(s.category):return True
    return t in _s(s.id) or t in _s(s.name)

def _country_match(s:Source,c:str)->bool:
    c=_s(c)
    if not c:return True
    aliases={"cuba":"cu","cu":"cu","usa":"us","united states":"us","eeuu":"us"}
    c=aliases.get(c,c)
    values={_s(s.country),_s(s.id),_s(s.name)}
    return c in values or c in _s(s.country) or c in _s(s.id) or c in _s(s.name)

def _airline_match(s:Source,a:str)->bool:
    a=_s(a)
    if not a:return True
    return a in _s(s.name) or a in _s(s.id)

def get_sources(topic:str="official",query:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    out=[]
    for s in sorted(SOURCES,key=lambda x:x.priority):
        if _topic_match(s,topic) and _country_match(s,country) and _airline_match(s,airline) and _match_text(s,query):
            out.append(_dict(s))
    return out

def sources_for(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official","",country,airline)

def find_sources(query:str="",topic:str="",country:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official",query,country)

def official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return [_dict(s) for s in sorted(SOURCES,key=lambda x:x.priority) if s.verified and s.type=="official" and _topic_match(s,topic or "official") and _country_match(s,country) and _airline_match(s,airline)]

def get_official_sources(topic:str="",country:str="",airline:str="")->List[Dict[str,Any]]:
    return official_sources(topic,country,airline)

def fixed_sources()->List[Dict[str,Any]]:
    return [_dict(s) for s in sorted(SOURCES,key=lambda x:x.priority) if s.fixed]

def get_airlines(query:str="")->List[Dict[str,Any]]:
    q=_s(query)
    return [_dict(s) for s in sorted(AIRLINES,key=lambda x:x.priority) if not q or q in _s(s.name) or q in _s(s.id)]

def airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def find_airlines(query:str="")->List[Dict[str,Any]]:
    return get_airlines(query)

def airline_list()->List[Dict[str,Any]]:
    return get_airlines()

def get_charters(query:str="")->List[Dict[str,Any]]:
    q=_s(query)
    return [_dict(s) for s in sorted(CHARTERS,key=lambda x:x.priority) if not q or q in _s(s.name) or q in _s(s.id)]

def get_charter_sources(query:str="")->List[Dict[str,Any]]:
    return get_charters(query)

def official_url(name_or_id:str)->str:
    q=_s(name_or_id)
    if not q:return ""
    exact=SOURCES_BY_ID.get(q)
    if exact:return exact.url
    for s in SOURCES:
        if q==_s(s.name) or q in _s(s.name) or q in _s(s.id):
            return s.url
    return ""

def answer_sources(question:str="",item:str="",airline:str="",country:str="")->List[Dict[str,Any]]:
    q=f"{question} {item}".strip()
    found=[]
    seen=set()
    def add(items):
        for x in items:
            if x["id"] not in seen:
                seen.add(x["id"]);found.append(x)
    if airline:add(get_sources("airline","",country,airline))
    if item or any(x in _s(q) for x in ("llevar","equipaje","articulo","artículo","permitido","puedo")):
        add(get_sources("item",q,country,airline))
        add(get_sources("baggage","",country,airline))
        add(get_sources("security","",country,airline))
        add(get_sources("customs",q,country,airline))
    if "cuba" in _s(q) or _s(country) in ("cuba","cu"):
        add(get_sources("cuba","",country,airline))
    if not found:add(official_sources("",country,airline))
    return found

__all__=["VERSION","VERIFICATION_DATE","Source","SOURCES","AIRLINES","CHARTERS","all_sources","source_by_id","get_sources","sources_for","find_sources","official_sources","get_official_sources","fixed_sources","get_airlines","airlines","find_airlines","airline_list","get_charters","get_charter_sources","official_url","answer_sources"]
