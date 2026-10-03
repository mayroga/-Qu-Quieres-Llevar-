# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v11.0.0
from __future__ import annotations
from datetime import date
from typing import Any,Dict,List
import re

VERSION="11.0.0"
TODAY=str(date.today())

def _src(id,name,publisher,url,topic,what,limitations="",country="",official=True,keywords=None,verified=None):
    return {
        "id":id,
        "name":name,
        "publisher":publisher,
        "url":url,
        "topic":topic,
        "what_it_covers":what,
        "description":what,
        "limitations":limitations or "Esta fuente no sustituye las reglas de otra autoridad o de la aerolínea cuando corresponda.",
        "country":country,
        "official":official,
        "verification_status":"verified_url" if verified else "verify_before_use",
        "last_verified":verified,
        "keywords":keywords or []
    }

SOURCES=[
_src(
"tsa_home","Transportation Security Administration","U.S. Transportation Security Administration",
"https://www.tsa.gov/","security",
"Seguridad en los puntos de control de transporte en Estados Unidos y orientación para pasajeros.",
"Aplica principalmente a los controles de seguridad bajo jurisdicción TSA; no determina por sí sola las reglas de entrada de otro país.",
"United States",True,["tsa","security","airport","screening","seguridad"],TODAY),
_src(
"tsa_bring","What Can I Bring?","U.S. Transportation Security Administration",
"https://www.tsa.gov/travel/security-screening/whatcanibring",
"items",
"Consulta de artículos para saber cómo se tratan determinados objetos en equipaje de cabina y documentado durante el control de seguridad.",
"No sustituye las condiciones de la aerolínea ni las reglas aduaneras o de importación del destino.",
"United States",True,["items","carry-on","checked","liquids","batteries","food"],TODAY),
_src(
"tsa_travel_tips","TSA Travel Tips","U.S. Transportation Security Administration",
"https://www.tsa.gov/news/press/factsheets/tsa-travel-tips",
"baggage",
"Preparación para seguridad, artículos prohibidos, líquidos, medicamentos e identificación.",
"No es una autorización universal para transportar o importar un artículo.",
"United States",True,["baggage","liquids","medication","screening"],TODAY),
_src(
"tsa_checklist","TSA Travel Checklist","U.S. Transportation Security Administration",
"https://www.tsa.gov/sites/default/files/tsa-travel-checklist.pdf",
"packing",
"Lista práctica para preparar equipaje y revisar artículos antes de llegar al aeropuerto.",
"Las reglas pueden depender de la situación concreta y deben confirmarse con las fuentes correspondientes.",
"United States",True,["packing","checklist","liquids","electronics"],TODAY),
_src(
"faa_batteries","PackSafe — Batteries","Federal Aviation Administration",
"https://www.faa.gov/hazmat/packsafe/batteries",
"batteries",
"Orientación sobre baterías y artículos con baterías para transporte aéreo.",
"Las condiciones pueden incluir requisitos de la aerolínea y características concretas de la batería.",
"United States",True,["battery","lithium","power bank","wh"],TODAY),
_src(
"faa_packsafe","PackSafe","Federal Aviation Administration",
"https://www.faa.gov/hazmat/packsafe",
"dangerous_goods",
"Información sobre materiales peligrosos y artículos que pueden transportarse por vía aérea.",
"No sustituye la confirmación de la aerolínea ni las reglas del país de destino.",
"United States",True,["hazmat","dangerous goods","batteries","flammable"],TODAY),
_src(
"cbp_travel","Travel","U.S. Customs and Border Protection",
"https://www.cbp.gov/travel",
"customs",
"Información oficial de entrada, salida, declaraciones y controles aduaneros de Estados Unidos.",
"Aplica a asuntos bajo jurisdicción estadounidense; no determina las reglas de entrada de Cuba u otro país.",
"United States",True,["cbp","customs","entry","declaration"],TODAY),
_src(
"cbp_clearing","Clearing Customs","U.S. Customs and Border Protection",
"https://www.cbp.gov/travel/clearing-customs",
"customs",
"Información sobre cuándo y cómo los viajeros pasan por CBP al entrar a Estados Unidos.",
"No debe utilizarse para inferir automáticamente los procedimientos de otros países.",
"United States",True,["customs","port of entry","connection"],TODAY),
_src(
"state_travel","Travel","U.S. Department of State",
"https://travel.state.gov/content/travel.html",
"documents",
"Información del Gobierno de Estados Unidos sobre viajes internacionales, pasaportes y asuntos consulares.",
"No determina por sí sola las reglas de entrada del país extranjero.",
"United States",True,["passport","travel","visa","consular"],TODAY),
_src(
"state_cuba","Cuba International Travel Information","U.S. Department of State",
"https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html",
"cuba",
"Información estadounidense relacionada con viajes a Cuba.",
"No sustituye las autoridades cubanas, la aerolínea ni las autoridades de tránsito.",
"Cuba",True,["cuba","travel","passport","entry"],TODAY),
_src(
"cuba_dviajeros","D’Viajeros","Ministerio de Transporte / República de Cuba",
"https://dviajeros.mitrans.gob.cu/",
"dviajeros",
"Portal oficial relacionado con la información del viajero para entrada a Cuba.",
"La aplicación May Roga solo puede enseñar y practicar; no debe presentarse como el portal oficial ni enviar el formulario por el usuario.",
"Cuba",True,["dviajeros","traveler","cuba","entry"],None),
_src(
"cuba_evisa","eVisa Cuba","República de Cuba",
"https://evisacuba.cu/",
"visa",
"Portal oficial utilizado para información y gestión relacionada con visas electrónicas de Cuba.",
"La necesidad y procedimiento aplicable dependen de la nacionalidad y situación del viajero; confirmar siempre en la fuente oficial.",
"Cuba",True,["visa","evisa","cuba"],None),
_src(
"cuba_evisa_manual","Manual del portal de visas","eVisa Cuba",
"https://evisacuba.cu/doc/es/info.pdf",
"visa",
"Manual del portal oficial de visas que ayuda a entender el funcionamiento de la plataforma.",
"No significa que el viajero reúna los requisitos; sirve para comprender el procedimiento.",
"Cuba",True,["visa","manual","evisa"],None),
_src(
"cuba_minrex","Ministerio de Relaciones Exteriores de Cuba","MINREX",
"https://www.minrex.gob.cu/",
"cuba",
"Información oficial del Ministerio de Relaciones Exteriores de Cuba.",
"Las condiciones concretas pueden depender del trámite y de la representación correspondiente.",
"Cuba",True,["minrex","visa","consular","cuba"],None),
_src(
"cuba_aduana","Aduana General de la República de Cuba","Aduana de Cuba",
"https://www.aduana.gob.cu/",
"customs",
"Información oficial de aduana de Cuba para viajeros y mercancías.",
"Una autorización de transporte aéreo no significa automáticamente autorización de entrada al país.",
"Cuba",True,["aduana","customs","cuba","travelers"],None),
_src(
"iata_travel","Travel Centre","International Air Transport Association",
"https://www.iatatravelcentre.com/",
"documents",
"Información de requisitos de viaje recopilada para planificación internacional.",
"IATA es una asociación de la industria, no una autoridad gubernamental. Para una decisión final debe revisarse la fuente oficial correspondiente.",
"International",False,["iata","travel requirements","documents"],None),
_src(
"iata_main","IATA","International Air Transport Association",
"https://www.iata.org/",
"airlines",
"Información general de la asociación internacional de aerolíneas.",
"No sustituye a una aerolínea, autoridad migratoria, aduanera o de seguridad.",
"International",False,["iata","airlines"],None)
]

AIRLINES=[
{"id":"american","name":"American Airlines","aliases":["american","aa"],"url":"https://www.aa.com/","type":"commercial","country":"United States"},
{"id":"delta","name":"Delta Air Lines","aliases":["delta"],"url":"https://www.delta.com/","type":"commercial","country":"United States"},
{"id":"united","name":"United Airlines","aliases":["united"],"url":"https://www.united.com/","type":"commercial","country":"United States"},
{"id":"jetblue","name":"JetBlue","aliases":["jetblue"],"url":"https://www.jetblue.com/","type":"commercial","country":"United States"},
{"id":"southwest","name":"Southwest Airlines","aliases":["southwest"],"url":"https://www.southwest.com/","type":"commercial","country":"United States"},
{"id":"spirit","name":"Spirit Airlines","aliases":["spirit"],"url":"https://www.spirit.com/","type":"commercial","country":"United States"},
{"id":"frontier","name":"Frontier Airlines","aliases":["frontier"],"url":"https://www.flyfrontier.com/","type":"commercial","country":"United States"},
{"id":"copa","name":"Copa Airlines","aliases":["copa"],"url":"https://www.copaair.com/","type":"commercial","country":"Panama"},
{"id":"avianca","name":"Avianca","aliases":["avianca"],"url":"https://www.avianca.com/","type":"commercial","country":"Colombia"},
{"id":"latam","name":"LATAM Airlines","aliases":["latam"],"url":"https://www.latamairlines.com/","type":"commercial","country":"Chile"},
{"id":"iberia","name":"Iberia","aliases":["iberia"],"url":"https://www.iberia.com/","type":"commercial","country":"Spain"},
{"id":"air_europa","name":"Air Europa","aliases":["air europa"],"url":"https://www.aireuropa.com/","type":"commercial","country":"Spain"},
{"id":"air_canada","name":"Air Canada","aliases":["air canada"],"url":"https://www.aircanada.com/","type":"commercial","country":"Canada"},
{"id":"interjet","name":"Interjet","aliases":["interjet"],"url":"https://www.interjet.com/","type":"commercial","country":"Mexico"},
{"id":"aeromexico","name":"Aeromexico","aliases":["aeromexico","aeroméxico"],"url":"https://www.aeromexico.com/","type":"commercial","country":"Mexico"},
{"id":"volaris","name":"Volaris","aliases":["volaris"],"url":"https://www.volaris.com/","type":"commercial","country":"Mexico"},
{"id":"viva_aerobus","name":"Viva Aerobus","aliases":["viva aerobus","viva"],"url":"https://www.vivaaerobus.com/","type":"commercial","country":"Mexico"},
{"id":"charter","name":"Operador chárter","aliases":["charter","chárter"],"url":"","type":"charter","country":"International"}
]

ITEM_TOPIC_MAP={
"liquid":"items",
"liquids":"items",
"liquido":"items",
"líquido":"items",
"aerosol":"items",
"spray":"items",
"battery":"batteries",
"batería":"batteries",
"bateria":"batteries",
"power bank":"batteries",
"lithium":"batteries",
"litio":"batteries",
"medicine":"medical",
"medication":"medical",
"medicamento":"medical",
"medicina":"medical",
"food":"food",
"comida":"food",
"animal":"animals",
"pet":"animals",
"mascota":"animals",
"tool":"tools",
"herramienta":"tools",
"electronic":"electronics",
"electronics":"electronics",
"electronico":"electronics",
"electrónico":"electronics",
"laptop":"electronics",
"computer":"electronics",
"phone":"electronics",
"telefono":"electronics",
"teléfono":"electronics",
"cash":"customs",
"money":"customs",
"dinero":"customs",
"document":"documents",
"documento":"documents"
}

def _norm(v:Any)->str:
    x=str(v or "").strip().lower()
    x=re.sub(r"\s+"," ",x)
    return x

def _copy(src:Dict[str,Any])->Dict[str,Any]:
    return dict(src)

def get_sources(topic:str="official",query:str="")->List[Dict[str,Any]]:
    t=_norm(topic)
    q=_norm(query)
    if t in {"","official","all","general"}:
        pool=SOURCES
    else:
        aliases={
            "equipaje":"baggage",
            "bag":"baggage",
            "maleta":"baggage",
            "articulo":"items",
            "artículos":"items",
            "articulos":"items",
            "seguridad":"security",
            "documentos":"documents",
            "cuba":"cuba",
            "aduana":"customs",
            "visa":"visa",
            "dviajero":"dviajeros",
            "dviajeros":"dviajeros",
            "aerolinea":"airlines",
            "aerolínea":"airlines",
            "vuelos":"flight",
            "vuelo":"flight",
            "conexion":"connection",
            "conexión":"connection",
            "practica":"practice",
            "práctica":"practice"
        }
        t=aliases.get(t,t)
        if t=="airlines":
            return [_copy(_airline_source(a)) for a in AIRLINES if a["url"]]
        pool=[x for x in SOURCES if _norm(x["topic"])==t or t in [_norm(k) for k in x.get("keywords",[])]]
    if q:
        terms=[z for z in re.split(r"[\s,;/]+",q) if z]
        scored=[]
        for x in pool:
            blob=" ".join([
                x.get("name",""),x.get("publisher",""),x.get("topic",""),
                x.get("what_it_covers",""),x.get("description",""),
                " ".join(x.get("keywords",[]))
            ]).lower()
            score=sum(1 for z in terms if z in blob)
            if score:
                scored.append((score,x))
        scored.sort(key=lambda a:-a[0])
        pool=[x for _,x in scored]
    return [_copy(x) for x in pool]

def sources_for(topic:str="",query:str="")->List[Dict[str,Any]]:
    return get_sources(topic,query)

def official_sources(topic:str="official",query:str="")->List[Dict[str,Any]]:
    return [x for x in get_sources(topic,query) if x.get("official")]

def find_sources(query:str="",topic:str="")->List[Dict[str,Any]]:
    return get_sources(topic or "official",query)

def sources_for_item(item:str="",airline:str="")->List[Dict[str,Any]]:
    x=_norm(item)
    topic="items"
    for key,val in ITEM_TOPIC_MAP.items():
        if key in x:
            topic=val
            break
    result=get_sources(topic,item)
    tsa=get_sources("items",item)
    seen={x.get("id") for x in result}
    for z in tsa:
        if z.get("id") not in seen:
            result.append(z)
            seen.add(z.get("id"))
    if airline:
        result.extend(airlines_for(airline))
    return result

def item_sources(item:str="",airline:str="")->List[Dict[str,Any]]:
    return sources_for_item(item,airline)

def get_item_sources(item:str="",airline:str="")->List[Dict[str,Any]]:
    return sources_for_item(item,airline)

def _airline_source(a:Dict[str,Any])->Dict[str,Any]:
    return {
        "id":"airline_"+a["id"],
        "name":a["name"],
        "publisher":a["name"],
        "url":a["url"],
        "topic":"airlines",
        "what_it_covers":"Sitio oficial de la aerolínea para consultar itinerario, tarifa, equipaje, cambios y condiciones.",
        "description":"Sitio oficial de la aerolínea para consultar itinerario, tarifa, equipaje, cambios y condiciones.",
        "limitations":"No demuestra que la aerolínea opere actualmente una ruta concreta. La ruta debe comprobarse para las fechas y aeropuerto del viajero.",
        "country":a["country"],
        "official":True,
        "verification_status":"official_domain",
        "last_verified":None,
        "keywords":a["aliases"],
        "airline_type":a["type"]
    }

def find_airlines(query:str="",origin:str="",destination:str="")->List[Dict[str,Any]]:
    q=_norm(query)
    out=[]
    for a in AIRLINES:
        blob=" ".join([a["name"]]+a["aliases"]).lower()
        if not q or q in blob or any(part in blob for part in q.split()):
            z=dict(a)
            z["official_url"]=a["url"]
            z["service_status"]="verify_for_route_and_date"
            z["note"]="La presencia en este registro no confirma una ruta actual."
            out.append(z)
    return out

def search_airlines(query:str="",origin:str="",destination:str="")->List[Dict[str,Any]]:
    return find_airlines(query,origin,destination)

def airlines_for(query:str="",origin:str="",destination:str="")->List[Dict[str,Any]]:
    return [_airline_source(x) for x in find_airlines(query,origin,destination) if x.get("url")]

def destination_sources(destination:str="")->List[Dict[str,Any]]:
    d=_norm(destination)
    if "cuba" in d or d in {"cu","habana","la habana","havana"}:
        return official_sources("cuba")
    return official_sources("documents",destination)

def source_explanation(topic:str)->Dict[str,Any]:
    t=_norm(topic)
    explanations={
        "baggage":"La aerolínea determina condiciones comerciales como piezas, peso y medidas de acuerdo con la tarifa; la seguridad puede imponer restricciones adicionales.",
        "items":"Hay que distinguir entre seguridad aeroportuaria, transporte aéreo, reglas de la aerolínea y entrada al país.",
        "customs":"Aduana trata la entrada o salida de mercancías y declaraciones; una autorización de seguridad no equivale a autorización aduanera.",
        "documents":"Los requisitos documentales dependen del viajero, nacionalidad, destino, tránsito, propósito y circunstancias.",
        "cuba":"Para Cuba deben revisarse por separado documentos, entrada, visa/eVisa cuando corresponda, D’Viajeros, equipaje y aduana.",
        "dviajeros":"La aplicación May Roga puede enseñar y practicar el proceso, pero el envío real corresponde al portal oficial.",
        "visa":"La aplicación puede explicar y simular pasos, pero la solicitud real debe realizarse en el canal oficial correspondiente.",
        "connection":"Una conexión depende del aeropuerto, itinerario, boleto, aerolínea, equipaje y controles del punto de tránsito.",
        "flight":"La aplicación puede interpretar un itinerario proporcionado por el usuario, pero no inventa vuelos ni confirma disponibilidad.",
        "airlines":"El sitio oficial de la aerolínea es la referencia para su propio itinerario, tarifa y condiciones."
    }
    return {
        "topic":t,
        "explanation":explanations.get(t,"La fuente debe consultarse según el tema específico."),
        "rule":"Si dos autoridades regulan aspectos diferentes, deben revisarse ambas; no se debe convertir una regla en otra."
    }

def get_source_registry()->Dict[str,Any]:
    return {
        "version":VERSION,
        "last_registry_build":TODAY,
        "sources":SOURCES,
        "airlines":AIRLINES
    }

__all__=[
"VERSION","TODAY","SOURCES","AIRLINES",
"get_sources","sources_for","official_sources","find_sources",
"sources_for_item","item_sources","get_item_sources",
"find_airlines","search_airlines","airlines_for",
"destination_sources","source_explanation","get_source_registry"
]
