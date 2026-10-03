# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC
from typing import Dict,List,Optional

VERSION="1.0.0"
VERIFICATION_DATE="2026-10-03"

SOURCES=[
{"id":"dviajeros","name":"D'Viajeros","url":"https://dviajeros.mitrans.gob.cu/","type":"official","topic":"Cuba"},
{"id":"evisa_cuba","name":"eVisa Cuba","url":"https://evisacuba.cu/","type":"official","topic":"Cuba"},
{"id":"minrex_cuba","name":"MINREX Cuba","url":"https://www.cubaminrex.cu/","type":"official","topic":"Cuba"},
{"id":"aduana_cuba","name":"Aduana de Cuba","url":"https://www.aduana.gob.cu/","type":"official","topic":"Cuba"},
{"id":"tsa","name":"TSA","url":"https://www.tsa.gov/","type":"official","topic":"Seguridad aérea"},
{"id":"cbp","name":"U.S. Customs and Border Protection","url":"https://www.cbp.gov/","type":"official","topic":"Viajes y entrada a EE.UU."},
{"id":"travel_state","name":"U.S. Department of State","url":"https://travel.state.gov/","type":"official","topic":"Viajes internacionales"},
{"id":"iata","name":"IATA Travel Centre","url":"https://www.iatatravelcentre.com/","type":"reference","topic":"Documentos y viajes"},
{"id":"american","name":"American Airlines","url":"https://www.aa.com/","type":"airline","topic":"Aerolínea"},
{"id":"delta","name":"Delta Air Lines","url":"https://www.delta.com/","type":"airline","topic":"Aerolínea"},
{"id":"united","name":"United Airlines","url":"https://www.united.com/","type":"airline","topic":"Aerolínea"},
{"id":"southwest","name":"Southwest Airlines","url":"https://www.southwest.com/","type":"airline","topic":"Aerolínea"},
{"id":"jetblue","name":"JetBlue","url":"https://www.jetblue.com/","type":"airline","topic":"Aerolínea"},
{"id":"spirit","name":"Spirit Airlines","url":"https://www.spirit.com/","type":"airline","topic":"Aerolínea"},
{"id":"frontier","name":"Frontier Airlines","url":"https://www.flyfrontier.com/","type":"airline","topic":"Aerolínea"},
{"id":"copa","name":"Copa Airlines","url":"https://www.copaair.com/","type":"airline","topic":"Aerolínea"},
{"id":"avianca","name":"Avianca","url":"https://www.avianca.com/","type":"airline","topic":"Aerolínea"},
{"id":"latam","name":"LATAM Airlines","url":"https://www.latamairlines.com/","type":"airline","topic":"Aerolínea"}
]

def registry()->Dict:
    return {"version":VERSION,"verification_date":VERIFICATION_DATE,"sources":SOURCES}

def all_sources()->List[Dict]:
    return list(SOURCES)

def official_sources()->List[Dict]:
    return [x for x in SOURCES if x["type"]=="official"]

def airline_sources()->List[Dict]:
    return [x for x in SOURCES if x["type"]=="airline"]

def cuba_sources()->List[Dict]:
    return [x for x in SOURCES if x["topic"]=="Cuba"]

def get_source(source_id:str)->Optional[Dict]:
    value=str(source_id or "").strip().lower()
    return next((x for x in SOURCES if x["id"]==value),None)

def search(name:str)->List[Dict]:
    value=str(name or "").strip().lower()
    if not value:
        return []
    return [x for x in SOURCES if value in x["name"].lower() or value in x["id"].lower()]

def airline_source(name:str)->Optional[Dict]:
    value=str(name or "").strip().lower()
    for x in airline_sources():
        if value and (value in x["name"].lower() or x["name"].lower() in value):
            return x
    return None
