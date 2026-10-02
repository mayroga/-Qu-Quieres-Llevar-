# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v7.0.0
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional
from urllib.parse import quote
import re,unicodedata

@dataclass(frozen=True)
class Source:
    id:str
    name:str
    url:str
    source_type:str
    country:Optional[str]=None
    airline:Optional[str]=None
    destination:Optional[str]=None
    scope:str=""
    official:bool=True
    verified:bool=False
    verification_date:Optional[str]=None
    notes:str=""

class SourceRegistry:
    VERSION="7.0.0"

    def __init__(self):
        self.sources:Dict[str,Source]={}
        self._load_defaults()

    @staticmethod
    def norm(value:Any)->str:
        value=str(value or "").strip().lower()
        value=unicodedata.normalize("NFD",value)
        value="".join(c for c in value if unicodedata.category(c)!="Mn")
        value=re.sub(r"[-_/]+"," ",value)
        value=re.sub(r"\s+"," ",value)
        return value.strip()

    def add(self,source:Source)->None:
        if not isinstance(source,Source):
            raise TypeError("source debe ser Source")
        self.sources[source.id]=source

    def get(self,source_id:str)->Optional[Source]:
        return self.sources.get(source_id)

    def all(self)->List[Source]:
        return list(self.sources.values())

    def search(
        self,
        country:Optional[str]=None,
        airline:Optional[str]=None,
        destination:Optional[str]=None,
        source_type:Optional[str]=None
    )->List[Source]:
        c=self.norm(country)
        a=self.norm(airline)
        d=self.norm(destination)
        t=self.norm(source_type)
        result=[]
        for source in self.sources.values():
            if c and c not in self.norm(source.country):
                continue
            if a and a not in self.norm(source.airline):
                continue
            if d and d not in self.norm(source.destination):
                continue
            if t and t!=self.norm(source.source_type):
                continue
            result.append(source)
        return result

    def verified(self)->List[Source]:
        return [s for s in self.sources.values() if s.verified]

    def official(self)->List[Source]:
        return [s for s in self.sources.values() if s.official]

    def to_dict(self,source:Optional[Source])->Optional[Dict[str,Any]]:
        if not source:
            return None
        return asdict(source)

    def list_dicts(self,items:Optional[List[Source]]=None)->List[Dict[str,Any]]:
        return [self.to_dict(x) for x in (items if items is not None else self.all())]

    def _load_defaults(self)->None:
        self.add(Source(
            id="google_flights",
            name="Google Flights",
            url="https://www.google.com/travel/flights",
            source_type="flight_search",
            country="US",
            scope="Búsqueda y orientación de vuelos",
            official=False,
            verified=True,
            verification_date="2026-10-01",
            notes="Se utiliza como primera puerta de búsqueda. No se presenta como fuente oficial de una aerolínea."
        ))

        self.add(Source(
            id="tsa_what_can_i_bring",
            name="TSA — What Can I Bring",
            url="https://www.tsa.gov/travel/security-screening/whatcanibring",
            source_type="security_baggage",
            country="US",
            scope="Revisión de artículos y seguridad para viajes desde Estados Unidos",
            official=True,
            verified=True,
            verification_date="2026-10-01"
        ))

        self.add(Source(
            id="faa_pack_safe",
            name="FAA — PackSafe",
            url="https://www.faa.gov/hazmat/packsafe",
            source_type="hazmat_baggage",
            country="US",
            scope="Materiales y artículos regulados para transporte aéreo",
            official=True,
            verified=True,
            verification_date="2026-10-01"
        ))

        self.add(Source(
            id="american_flights_mia_hav",
            name="American Airlines — Miami to Havana",
            url="https://www.aa.com/en-us/flights-from-miami-to-havana",
            source_type="flight_search",
            country="US",
            airline="American Airlines",
            destination="Cuba,Havana",
            scope="Consulta de vuelos publicados por American entre Miami y La Habana",
            official=True,
            verified=True,
            verification_date="2026-10-01",
            notes="La disponibilidad, horarios y tarifas deben consultarse para la fecha concreta."
        ))

        self.add(Source(
            id="american_flights_cuba",
            name="American Airlines — Flights to Cuba",
            url="https://www.aa.com/en-us/flights-to-cuba",
            source_type="flight_search",
            country="US",
            airline="American Airlines",
            destination="Cuba",
            scope="Consulta de vuelos de American hacia Cuba",
            official=True,
            verified=True,
            verification_date="2026-10-01",
            notes="No implica que una ruta concreta esté disponible para todas las fechas."
        ))

        self.add(Source(
            id="american_cuba_travel",
            name="American Airlines — Travel to Cuba",
            url="https://www.aa.com/web/i18n/travel-info/international-travel/cuba.html",
            source_type="destination_requirements",
            country="US",
            airline="American Airlines",
            destination="Cuba",
            scope="Información de viaje y preparación para Cuba",
            official=True,
            verified=True,
            verification_date="2026-10-01"
        ))

        self.add(Source(
            id="american_checked_baggage",
            name="American Airlines — Checked Baggage",
            url="https://www.aa.com/web/i18n/travel-info/baggage/checked-baggage-policy.html",
            source_type="baggage",
            country="US",
            airline="American Airlines",
            scope="Equipaje facturado y condiciones aplicables",
            official=True,
            verified=True,
            verification_date="2026-10-01"
        ))

        self.add(Source(
            id="american_baggage_limitations",
            name="American Airlines — Baggage Limitations",
            url="https://www.aa.com/i18nForward.do?p=%2Ftravel-info%2Fbaggage%2Fbaggage-limitations.jsp",
            source_type="baggage",
            country="US",
            airline="American Airlines",
            destination="Cuba",
            scope="Limitaciones de equipaje, incluyendo Cuba",
            official=True,
            verified=True,
            verification_date="2026-10-01"
        ))

        self.add(Source(
            id="american_restricted_items",
            name="American Airlines — Restricted Items",
            url="https://www.aa.com/web/i18n/travel-info/baggage/restricted-items.html",
            source_type="restricted_items",
            country="US",
            airline="American Airlines",
            scope="Artículos restringidos y condiciones de transporte",
            official=True,
            verified=True,
            verification_date="2026-10-01"
        ))

        self.add(Source(
            id="dviajeros_cuba",
            name="D'Viajeros Cuba",
            url="https://dviajeros.mitrans.gob.cu/",
            source_type="destination_requirements",
            country="Cuba",
            destination="Cuba",
            scope="Declaración y requisitos oficiales de entrada a Cuba",
            official=True,
            verified=False,
            notes="Debe verificarse nuevamente antes de presentar requisitos como actuales."
        ))

        self.add(Source(
            id="evisa_cuba",
            name="eVisa Cuba",
            url="https://evisacuba.cu/",
            source_type="visa",
            country="Cuba",
            destination="Cuba",
            scope="Información y gestión relacionada con visa electrónica de Cuba",
            official=True,
            verified=False,
            notes="La aplicación debe verificar el contenido vigente antes de presentar un requisito como confirmado."
        ))

        self.add(Source(
            id="xael",
            name="XAEL",
            url="https://www.xaelcharter.com/",
            source_type="charter",
            country="US",
            airline="XAEL",
            destination="Cuba",
            scope="Fuente oficial del operador chárter",
            official=True,
            verified=True,
            verification_date="2026-10-01",
            notes="La existencia de esta fuente no significa que exista disponibilidad para una fecha determinada."
        ))

        self.add(Source(
            id="cubazul",
            name="Cubazul Air Charter",
            url="https://cubazulaircharter.com/",
            source_type="charter",
            country="US",
            airline="Cubazul Air Charter",
            destination="Cuba",
            scope="Fuente del operador chárter",
            official=True,
            verified=False,
            notes="Verificar disponibilidad y condiciones antes de presentar información concreta."
        ))

    def google_flights_url(
        self,
        origin:Optional[str]=None,
        destination:Optional[str]=None,
        departure_date:Optional[str]=None,
        return_date:Optional[str]=None
    )->str:
        parts=[]
        if origin:
            parts.append(str(origin).strip())
        if destination:
            parts.append(str(destination).strip())
        route="+".join(quote(x,safe="") for x in parts)
        url="https://www.google.com/travel/flights"
        if route:
            url+="?q="+route
        if departure_date:
            url+=("&" if "?" in url else "?")+"departure="+quote(str(departure_date))
        if return_date:
            url+="&return="+quote(str(return_date))
        return url

    def route_sources(
        self,
        origin:Optional[str],
        destination:Optional[str],
        airline:Optional[str]=None
    )->List[Source]:
        o=self.norm(origin)
        d=self.norm(destination)
        a=self.norm(airline)
        result=[]
        for source in self.sources.values():
            sa=self.norm(source.airline)
            sd=self.norm(source.destination)
            if a and a not in sa:
                continue
            if sd and d and d not in sd:
                continue
            if source.source_type not in (
                "flight_search","charter","destination_requirements"
            ):
                continue
            if source.id=="google_flights":
                result.append(source)
                continue
            if source.country=="Cuba" and d=="cuba":
                result.append(source)
                continue
            if d in sd or "cuba" in sd and d in (
                "havana","habana","hav"
            ):
                result.append(source)
                continue
            if o=="miami" and d in ("havana","habana","hav"):
                if sa and a and a in sa:
                    result.append(source)
        seen=set()
        final=[]
        for source in result:
            if source.id not in seen:
                seen.add(source.id)
                final.append(source)
        return final

    def baggage_sources(
        self,
        airline:Optional[str]=None,
        destination:Optional[str]=None
    )->List[Source]:
        a=self.norm(airline)
        d=self.norm(destination)
        result=[]
        for source in self.sources.values():
            if source.source_type not in (
                "baggage","restricted_items","security_baggage",
                "hazmat_baggage"
            ):
                continue
            if source.airline:
                if not a or a not in self.norm(source.airline):
                    continue
            if source.destination and d:
                if d not in self.norm(source.destination):
                    continue
            result.append(source)
        return result

REGISTRY=SourceRegistry()
source_registry=REGISTRY

def get_source(source_id:str)->Optional[Source]:
    return REGISTRY.get(source_id)

def all_sources()->List[Dict[str,Any]]:
    return REGISTRY.list_dicts()

def search_sources(
    country:Optional[str]=None,
    airline:Optional[str]=None,
    destination:Optional[str]=None,
    source_type:Optional[str]=None
)->List[Dict[str,Any]]:
    return REGISTRY.list_dicts(
        REGISTRY.search(country,airline,destination,source_type)
    )

def route_sources(
    origin:Optional[str],
    destination:Optional[str],
    airline:Optional[str]=None
)->List[Dict[str,Any]]:
    return REGISTRY.list_dicts(
        REGISTRY.route_sources(origin,destination,airline)
    )

def baggage_sources(
    airline:Optional[str]=None,
    destination:Optional[str]=None
)->List[Dict[str,Any]]:
    return REGISTRY.list_dicts(
        REGISTRY.baggage_sources(airline,destination)
    )

__all__=[
    "Source",
    "SourceRegistry",
    "REGISTRY",
    "source_registry",
    "get_source",
    "all_sources",
    "search_sources",
    "route_sources",
    "baggage_sources"
]
