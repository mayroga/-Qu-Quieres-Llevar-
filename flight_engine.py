# flight_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v7.0.0
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional
from urllib.parse import quote
from datetime import datetime
import re,unicodedata

from source_registry import (
    Source,SourceRegistry,REGISTRY
)

@dataclass
class FlightQuery:
    origin:Optional[str]=None
    destination:Optional[str]=None
    departure_date:Optional[str]=None
    return_date:Optional[str]=None
    passengers:int=1
    cabin:Optional[str]=None
    airline:Optional[str]=None
    nonstop:Optional[bool]=None
    language:str="es"

@dataclass
class FlightOption:
    id:str
    airline:Optional[str]=None
    flight_number:Optional[str]=None
    origin:Optional[str]=None
    destination:Optional[str]=None
    departure:Optional[str]=None
    arrival:Optional[str]=None
    date:Optional[str]=None
    direct:Optional[bool]=None
    stops:Optional[int]=None
    connection:Optional[bool]=None
    connection_airport:Optional[str]=None
    connection_duration:Optional[str]=None
    passengers:Optional[int]=None
    cabin:Optional[str]=None
    fare:Optional[str]=None
    currency:Optional[str]=None
    baggage_summary:Optional[str]=None
    source:Optional[str]=None
    source_name:Optional[str]=None
    source_type:Optional[str]=None
    verified:bool=False
    official_source:bool=False
    verification_date:Optional[str]=None
    conditions:List[str]=None

    def __post_init__(self):
        if self.conditions is None:
            self.conditions=[]

class FlightEngine:
    VERSION="7.0.0"

    AIRPORTS={
        "miami":"MIA",
        "mia":"MIA",
        "miami international":"MIA",
        "havana":"HAV",
        "habana":"HAV",
        "hav":"HAV",
        "jose marti":"HAV",
        "jose marti international":"HAV",
        "fort lauderdale":"FLL",
        "fll":"FLL",
        "tampa":"TPA",
        "tpa":"TPA",
        "atlanta":"ATL",
        "atl":"ATL",
        "new york":"JFK",
        "jfk":"JFK",
        "houston":"IAH",
        "iah":"IAH",
        "orlando":"MCO",
        "mco":"MCO",
        "santiago de cuba":"SCU",
        "scu":"SCU",
        "camaguey":"CMW",
        "cmw":"CMW",
        "varadero":"VRA",
        "vra":"VRA"
    }

    DESTINATIONS={
        "cuba":"Cuba",
        "havana":"Cuba",
        "habana":"Cuba",
        "hav":"Cuba",
        "santiago de cuba":"Cuba",
        "varadero":"Cuba",
        "camaguey":"Cuba"
    }

    def __init__(self,registry:SourceRegistry=REGISTRY):
        self.registry=registry

    @staticmethod
    def norm(value:Any)->str:
        value=str(value or "").strip().lower()
        value=unicodedata.normalize("NFD",value)
        value="".join(c for c in value if unicodedata.category(c)!="Mn")
        value=re.sub(r"[-_/]+"," ",value)
        value=re.sub(r"\s+"," ",value)
        return value.strip()

    @classmethod
    def airport_code(cls,value:Optional[str])->Optional[str]:
        q=cls.norm(value)
        if not q:
            return None
        if re.fullmatch(r"[a-z]{3}",q):
            return q.upper()
        return cls.AIRPORTS.get(q)

    @classmethod
    def country_for_destination(cls,value:Optional[str])->Optional[str]:
        q=cls.norm(value)
        if q in cls.DESTINATIONS:
            return cls.DESTINATIONS[q]
        code=cls.airport_code(value)
        if code in ("HAV","VRA","SCU","CMW"):
            return "Cuba"
        return None

    @classmethod
    def normalize_query(cls,query:FlightQuery)->FlightQuery:
        query.origin=(query.origin or "").strip() or None
        query.destination=(query.destination or "").strip() or None
        query.departure_date=(query.departure_date or "").strip() or None
        query.return_date=(query.return_date or "").strip() or None
        query.airline=(query.airline or "").strip() or None
        query.cabin=(query.cabin or "").strip() or None
        query.language="en" if cls.norm(query.language)=="en" else "es"
        query.passengers=max(1,min(int(query.passengers or 1),20))
        return query

    @classmethod
    def validate_query(cls,query:FlightQuery)->List[str]:
        missing=[]
        if not query.origin:
            missing.append("origin")
        if not query.destination:
            missing.append("destination")
        if query.departure_date:
            try:
                datetime.strptime(query.departure_date,"%Y-%m-%d")
            except ValueError:
                missing.append("departure_date_invalid")
        if query.return_date:
            try:
                datetime.strptime(query.return_date,"%Y-%m-%d")
            except ValueError:
                missing.append("return_date_invalid")
        return missing

    @classmethod
    def google_flights_url(cls,query:FlightQuery)->str:
        origin=cls.airport_code(query.origin) or query.origin or ""
        destination=cls.airport_code(query.destination) or query.destination or ""
        url="https://www.google.com/travel/flights"
        params=[]
        if origin and destination:
            params.append("q="+quote(f"{origin} {destination}"))
        if query.departure_date:
            params.append("departure="+quote(query.departure_date))
        if query.return_date:
            params.append("return="+quote(query.return_date))
        if params:
            url+="?"+"&".join(params)
        return url

    @classmethod
    def human_route(cls,query:FlightQuery)->str:
        origin=cls.airport_code(query.origin) or query.origin or ""
        destination=cls.airport_code(query.destination) or query.destination or ""
        return f"{origin} → {destination}"

    def search_sources(self,query:FlightQuery)->List[Dict[str,Any]]:
        query=self.normalize_query(query)
        sources=self.registry.route_sources(
            query.origin,
            query.destination,
            query.airline
        )
        result=[]
        seen=set()

        google=self.registry.get("google_flights")
        if google:
            result.append(self._source_card(
                google,
                query,
                priority=1
            ))
            seen.add(google.id)

        for source in sources:
            if source.id in seen:
                continue
            result.append(self._source_card(
                source,
                query,
                priority=len(result)+1
            ))
            seen.add(source.id)

        return result

    def _source_card(
        self,
        source:Source,
        query:FlightQuery,
        priority:int
    )->Dict[str,Any]:
        url=source.url

        if source.id=="google_flights":
            url=self.google_flights_url(query)

        return {
            "id":source.id,
            "name":source.name,
            "url":url,
            "source_type":source.source_type,
            "airline":source.airline,
            "destination":source.destination,
            "official":source.official,
            "verified":source.verified,
            "verification_date":source.verification_date,
            "priority":priority,
            "scope":source.scope,
            "notes":source.notes
        }

    def _is_cuba_query(self,query:FlightQuery)->bool:
        return (
            self.country_for_destination(query.destination)=="Cuba"
            or self.norm(query.destination)=="cuba"
        )

    def cuba_sources(self,query:FlightQuery)->List[Dict[str,Any]]:
        if not self._is_cuba_query(query):
            return []

        result=[]
        for source in self.search_sources(query):
            result.append(source)

        return result

    def search(self,query:FlightQuery)->Dict[str,Any]:
        query=self.normalize_query(query)
        errors=self.validate_query(query)

        if errors:
            return {
                "success":False,
                "status":"needs_information",
                "query":asdict(query),
                "results":[],
                "sources":[],
                "google_flights":None,
                "message":self._message(
                    query.language,
                    "Indica origen y destino. Si quieres resultados concretos, también necesitamos la fecha.",
                    "Enter the origin and destination. For concrete results, we also need the date."
                ),
                "missing_information":errors,
                "verified":False,
                "next_action":self._message(
                    query.language,
                    "Completa los datos del viaje.",
                    "Complete the trip details."
                )
            }

        sources=self.search_sources(query)
        google=next(
            (x for x in sources if x["id"]=="google_flights"),
            None
        )

        airline_sources=[
            x for x in sources
            if x["id"]!="google_flights"
            and x.get("source_type") in (
                "flight_search","charter"
            )
        ]

        return {
            "success":True,
            "status":"sources_ready",
            "query":asdict(query),
            "route":self.human_route(query),
            "results":[],
            "sources":sources,
            "google_flights":google,
            "airline_sources":airline_sources,
            "cuba":self._is_cuba_query(query),
            "verified":False,
            "message":self._message(
                query.language,
                "Primero puedes buscar el vuelo en Google Flights. Después puedes abrir las fuentes de las aerolíneas o chárteres aplicables y confirmar el vuelo directamente con ellos.",
                "You can first search the flight on Google Flights. Then open the applicable airline or charter sources and confirm the flight directly with them."
            ),
            "important":self._message(
                query.language,
                "No mostramos vuelos, horarios, precios ni disponibilidad como confirmados si no fueron obtenidos de una fuente que los publique para esa consulta.",
                "We do not show flights, schedules, prices or availability as confirmed unless they were obtained from a source that publishes them for that query."
            ),
            "next_action":self._message(
                query.language,
                "Elige una fuente y confirma tu vuelo.",
                "Choose a source and confirm your flight."
            )
        }

    def understand(
        self,
        query:FlightQuery,
        selected:Optional[Dict[str,Any]]=None
    )->Dict[str,Any]:
        query=self.normalize_query(query)
        selected=selected or {}

        airline=selected.get("airline")
        flight_number=selected.get("flight_number")
        direct=selected.get("direct")
        stops=selected.get("stops")
        connection=selected.get("connection")

        if selected and not airline:
            airline=None

        result={
            "success":True,
            "query":asdict(query),
            "flight":{
                "airline":airline,
                "flight_number":flight_number,
                "origin":selected.get("origin") or query.origin,
                "destination":selected.get("destination") or query.destination,
                "departure":selected.get("departure"),
                "arrival":selected.get("arrival"),
                "date":selected.get("date") or query.departure_date,
                "direct":direct,
                "stops":stops,
                "connection":connection,
                "connection_airport":selected.get("connection_airport"),
                "connection_duration":selected.get("connection_duration"),
                "passengers":selected.get("passengers") or query.passengers,
                "cabin":selected.get("cabin") or query.cabin,
                "fare":selected.get("fare"),
                "baggage_summary":selected.get("baggage_summary"),
                "source":selected.get("source"),
                "verified":bool(selected.get("verified",False))
            },
            "what_it_means":[],
            "missing_information":[],
            "next_action":None
        }

        if direct is True:
            result["what_it_means"].append(
                self._message(
                    query.language,
                    "Tu vuelo aparece como directo.",
                    "Your flight appears to be nonstop."
                )
            )
        elif connection is True or (stops is not None and stops>0):
            result["what_it_means"].append(
                self._message(
                    query.language,
                    "Tu viaje tiene una escala o conexión.",
                    "Your trip has a stop or connection."
                )
            )
            result["what_it_means"].append(
                self._message(
                    query.language,
                    "Hay que revisar si cambias de avión, qué ocurre con el equipaje y qué controles debes realizar.",
                    "Check whether you change aircraft, what happens to your baggage, and which controls you must complete."
                )
            )
        else:
            result["missing_information"].append(
                self._message(
                    query.language,
                    "si el vuelo es directo o tiene escala",
                    "whether the flight is nonstop or has a connection"
                )
            )

        if not airline:
            result["missing_information"].append(
                self._message(
                    query.language,
                    "aerolínea",
                    "airline"
                )
            )

        if not selected.get("fare"):
            result["missing_information"].append(
                self._message(
                    query.language,
                    "tarifa",
                    "fare"
                )
            )

        if not selected.get("baggage_summary"):
            result["missing_information"].append(
                self._message(
                    query.language,
                    "condiciones de equipaje",
                    "baggage conditions"
                )
            )

        result["next_action"]=self._message(
            query.language,
            "Confirma primero los datos del vuelo en la fuente que lo publica.",
            "First confirm the flight details on the source that publishes the flight."
        )

        return result

    def source_for_airline(
        self,
        airline:str,
        destination:Optional[str]=None
    )->List[Dict[str,Any]]:
        sources=self.registry.search(
            airline=airline,
            destination=destination
        )
        return self.registry.list_dicts(sources)

    def baggage_source_for_flight(
        self,
        airline:Optional[str],
        destination:Optional[str]
    )->List[Dict[str,Any]]:
        return self.registry.list_dicts(
            self.registry.baggage_sources(
                airline=airline,
                destination=destination
            )
        )

    def build_selected_flight(
        self,
        query:FlightQuery,
        data:Dict[str,Any]
    )->FlightOption:
        source=data.get("source")
        source_name=data.get("source_name")
        source_type=data.get("source_type")

        verified=bool(data.get("verified",False))
        official=bool(data.get("official_source",False))

        return FlightOption(
            id=str(data.get("id") or ""),
            airline=data.get("airline"),
            flight_number=data.get("flight_number"),
            origin=data.get("origin") or query.origin,
            destination=data.get("destination") or query.destination,
            departure=data.get("departure"),
            arrival=data.get("arrival"),
            date=data.get("date") or query.departure_date,
            direct=data.get("direct"),
            stops=data.get("stops"),
            connection=data.get("connection"),
            connection_airport=data.get("connection_airport"),
            connection_duration=data.get("connection_duration"),
            passengers=data.get("passengers") or query.passengers,
            cabin=data.get("cabin") or query.cabin,
            fare=data.get("fare"),
            currency=data.get("currency"),
            baggage_summary=data.get("baggage_summary"),
            source=source,
            source_name=source_name,
            source_type=source_type,
            verified=verified,
            official_source=official,
            verification_date=data.get("verification_date"),
            conditions=list(data.get("conditions") or [])
        )

    def no_fake_results_message(self,language:str="es")->str:
        return self._message(
            language,
            "No tenemos un resultado de vuelo confirmado para esta consulta. En lugar de inventarlo, te mostramos dónde buscarlo y qué debes confirmar.",
            "We do not have a confirmed flight result for this request. Instead of inventing one, we show you where to search and what to confirm."
        )

    @staticmethod
    def _message(language:str,es:str,en:str)->str:
        return en if str(language).lower()=="en" else es

ENGINE=FlightEngine()
flight_engine=ENGINE

def search_flights(
    origin:Optional[str]=None,
    destination:Optional[str]=None,
    departure_date:Optional[str]=None,
    return_date:Optional[str]=None,
    passengers:int=1,
    cabin:Optional[str]=None,
    airline:Optional[str]=None,
    nonstop:Optional[bool]=None,
    language:str="es"
)->Dict[str,Any]:
    return ENGINE.search(
        FlightQuery(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            passengers=passengers,
            cabin=cabin,
            airline=airline,
            nonstop=nonstop,
            language=language
        )
    )

def understand_flight(
    query:FlightQuery,
    selected:Optional[Dict[str,Any]]=None
)->Dict[str,Any]:
    return ENGINE.understand(query,selected)

def google_flights_url(
    origin:Optional[str]=None,
    destination:Optional[str]=None,
    departure_date:Optional[str]=None,
    return_date:Optional[str]=None
)->str:
    return ENGINE.google_flights_url(
        FlightQuery(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date
        )
    )

__all__=[
    "FlightQuery",
    "FlightOption",
    "FlightEngine",
    "ENGINE",
    "flight_engine",
    "search_flights",
    "understand_flight",
    "google_flights_url"
]
