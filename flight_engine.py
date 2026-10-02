# flight_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.0
from dataclasses import dataclass,asdict
from datetime import datetime
from typing import Any,Dict,List,Optional
from source_registry import REGISTRY,google_flights_url

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
    verified:bool=False
    verified_at:Optional[str]=None
    official_source:bool=False
    conditions:List[str]=None
    def to_dict(self)->Dict[str,Any]:
        d=asdict(self)
        d["conditions"]=self.conditions or []
        return d

class FlightEngine:
    VERSION="8.0.0"

    AIRPORTS={
        "miami":"MIA","mia":"MIA","miami international":"MIA",
        "la habana":"HAV","habana":"HAV","havana":"HAV","hav":"HAV",
        "fort lauderdale":"FLL","fll":"FLL",
        "tampa":"TPA","tpa":"TPA",
        "orlando":"MCO","mco":"MCO",
        "atlanta":"ATL","atl":"ATL",
        "new york":"JFK","jfk":"JFK",
        "houston":"IAH","iah":"IAH",
        "los angeles":"LAX","lax":"LAX",
        "new orleans":"MSY","msy":"MSY",
        "baltimore":"BWI","bwi":"BWI",
        "santiago de cuba":"SCU","scu":"SCU",
        "varadero":"VRA","vra":"VRA",
        "camaguey":"CMW","camagüey":"CMW",
    }

    CUBA_AIRPORTS={"HAV","SCU","VRA","CMW"}

    def __init__(self,registry=REGISTRY):
        self.registry=registry

    def normalize(self,value:Any)->str:
        import unicodedata
        s=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode("ascii").lower()
        return " ".join(s.split())

    def airport_code(self,value:Optional[str])->Optional[str]:
        if not value:return None
        n=self.normalize(value)
        if len(n)==3 and n.upper() in set(self.AIRPORTS.values()):return n.upper()
        return self.AIRPORTS.get(n)

    def display_place(self,value:Optional[str])->str:
        code=self.airport_code(value)
        names={"MIA":"Miami (MIA)","HAV":"La Habana (HAV)","FLL":"Fort Lauderdale (FLL)","TPA":"Tampa (TPA)","MCO":"Orlando (MCO)","ATL":"Atlanta (ATL)","JFK":"New York (JFK)","IAH":"Houston (IAH)","LAX":"Los Ángeles (LAX)","MSY":"New Orleans (MSY)","BWI":"Baltimore/Washington (BWI)","SCU":"Santiago de Cuba (SCU)","VRA":"Varadero (VRA)","CMW":"Camagüey (CMW)"}
        return names.get(code,str(value or ""))

    def is_cuba(self,value:Optional[str])->bool:
        return self.airport_code(value) in self.CUBA_AIRPORTS or "cuba" in self.normalize(value) or "havana" in self.normalize(value) or "habana" in self.normalize(value)

    def is_cuba_route(self,origin:Optional[str],destination:Optional[str])->bool:
        return self.is_cuba(origin) or self.is_cuba(destination)

    def build_query(self,origin=None,destination=None,departure_date=None,return_date=None,passengers=1,cabin=None,airline=None,nonstop=None,language="es",**kwargs)->FlightQuery:
        if isinstance(origin,dict):
            data=origin
            return FlightQuery(
                origin=data.get("origin"),
                destination=data.get("destination"),
                departure_date=data.get("departure_date"),
                return_date=data.get("return_date"),
                passengers=int(data.get("passengers") or 1),
                cabin=data.get("cabin"),
                airline=data.get("airline"),
                nonstop=data.get("nonstop"),
                language=data.get("language") or "es")
        return FlightQuery(origin,destination,departure_date,return_date,int(passengers or 1),cabin,airline,nonstop,language or "es")

    def validate_query(self,q:FlightQuery)->List[str]:
        errors=[]
        if not q.origin:errors.append("Falta el lugar desde donde sales.")
        if not q.destination:errors.append("Falta el lugar al que vas.")
        if q.origin and not self.airport_code(q.origin):errors.append("No reconocemos todavía ese aeropuerto o ciudad. Puedes escribir también el código de tres letras.")
        if q.destination and not self.airport_code(q.destination) and not self.is_cuba(q.destination):errors.append("No reconocemos todavía ese destino. Puedes escribir la ciudad o el código del aeropuerto.")
        if q.passengers<1 or q.passengers>20:errors.append("La cantidad de pasajeros debe estar entre 1 y 20.")
        return errors

    def source_cards(self,origin=None,destination=None,airline=None)->List[Dict[str,Any]]:
        sources=self.registry.route_sources(origin,destination,airline,include_search=True)
        return [self._source_card(s) for s in sources]

    def airline_sources(self,origin=None,destination=None,airline=None)->List[Dict[str,Any]]:
        sources=self.registry.route_sources(origin,destination,airline,include_search=False)
        return [self._source_card(s) for s in sources if s.source_type in ("airline","charter")]

    def search_sources(self,origin=None,destination=None,airline=None)->List[Dict[str,Any]]:
        return self.source_cards(origin,destination,airline)

    def _source_card(self,s)->Dict[str,Any]:
        return {
            "id":s.id,"name":s.name,"url":s.url,"source_type":s.source_type,
            "country":s.country,"airline":s.airline,"destination":s.destination,
            "scope":s.scope,"official":s.official,"verified":s.verified,
            "verification_date":s.verification_date,"notes":s.notes
        }

    def search(self,origin=None,destination=None,departure_date=None,return_date=None,passengers=1,cabin=None,airline=None,nonstop=None,language="es",**kwargs)->Dict[str,Any]:
        q=self.build_query(origin,destination,departure_date,return_date,passengers,cabin,airline,nonstop,language,**kwargs)
        errors=self.validate_query(q)
        url=google_flights_url(q.origin,q.destination,q.departure_date,q.return_date)
        sources=self.source_cards(q.origin,q.destination,q.airline)
        airline_sources=self.airline_sources(q.origin,q.destination,q.airline)
        cuba=self.is_cuba_route(q.origin,q.destination)
        if errors:
            return {
                "success":False,"results":[],"sources":sources,"airline_sources":airline_sources,
                "route":{"origin":q.origin,"destination":q.destination,"origin_code":self.airport_code(q.origin),"destination_code":self.airport_code(q.destination)},
                "google_flights_url":url,"is_cuba_route":cuba,
                "message":self._message("errors",q.language,errors),
                "important":self._important(q.language)
            }
        return {
            "success":True,
            "results":[],
            "sources":sources,
            "airline_sources":airline_sources,
            "route":{
                "origin":q.origin,"destination":q.destination,
                "origin_code":self.airport_code(q.origin),
                "destination_code":self.airport_code(q.destination),
                "departure_date":q.departure_date,
                "return_date":q.return_date,
                "passengers":q.passengers,
                "cabin":q.cabin,
                "airline_filter":q.airline,
                "nonstop":q.nonstop
            },
            "google_flights_url":url,
            "is_cuba_route":cuba,
            "message":self._message("search",q.language,[]),
            "important":self._important(q.language),
            "next_action":self._next_action(q.language)
        }

    def understand(self,flight:Any=None,language="es",**kwargs)->Dict[str,Any]:
        if flight is None:flight=kwargs
        if hasattr(flight,"model_dump"):data=flight.model_dump()
        elif hasattr(flight,"dict"):data=flight.dict()
        elif isinstance(flight,FlightOption):data=flight.to_dict()
        elif isinstance(flight,dict):data=dict(flight)
        else:data={}
        lang=data.get("language") or language or "es"
        airline=data.get("airline")
        origin=data.get("origin")
        destination=data.get("destination")
        direct=data.get("direct")
        stops=data.get("stops")
        connection=data.get("connection")
        connection_airport=data.get("connection_airport")
        connection_duration=data.get("connection_duration")
        if connection is None:
            connection=(stops is not None and stops>0) or bool(connection_airport)
        if direct is None and stops is not None:direct=stops==0
        missing=[]
        if not airline:missing.append("la aerolínea")
        if not data.get("fare"):missing.append("la tarifa")
        if not data.get("cabin"):missing.append("la cabina")
        if not data.get("baggage"):missing.append("las condiciones de equipaje")
        if direct is None and stops is None:missing.append("si es directo o tiene escala")
        steps=self._understanding_steps(data,lang)
        sources=self.airline_sources(origin,destination,airline) if airline else self.source_cards(origin,destination)
        return {
            "success":True,
            "airline":airline,
            "flight_number":data.get("flight_number"),
            "origin":origin,
            "destination":destination,
            "direct":direct,
            "stops":stops,
            "connection":connection,
            "connection_airport":connection_airport,
            "connection_duration":connection_duration,
            "fare":data.get("fare"),
            "cabin":data.get("cabin"),
            "baggage_summary":data.get("baggage_summary"),
            "explanation":self._explanation(data,lang),
            "steps":steps,
            "missing_information":missing,
            "next_action":self._next_action(lang,missing),
            "sources":sources,
            "verified":bool(data.get("verified")),
            "official_source":bool(data.get("official_source"))
        }

    def _understanding_steps(self,data,lang)->List[str]:
        if lang=="en":
            steps=["Check the airline name.","Check whether the itinerary is nonstop or has a connection.","Check the fare and cabin.","Open the baggage conditions for this exact itinerary.","Confirm missing details on the official airline site."]
            if data.get("connection") or (data.get("stops") or 0)>0:steps.insert(2,"If you have a connection, check whether you change aircraft and what happens to your baggage.")
            return steps
        steps=["Mira el nombre de la aerolínea.","Comprueba si el viaje es directo o tiene una conexión.","Mira la tarifa y la cabina.","Abre las condiciones de equipaje de este viaje concreto.","Confirma lo que falte en el sitio oficial de la aerolínea."]
        if data.get("connection") or (data.get("stops") or 0)>0:steps.insert(2,"Si tienes una conexión, revisa si cambias de avión y qué ocurre con tu equipaje.")
        return steps

    def _explanation(self,data,lang):
        direct=data.get("direct")
        stops=data.get("stops")
        connection=data.get("connection")
        if lang=="en":
            if direct is True:return "This itinerary is marked as nonstop."
            if connection or (stops is not None and stops>0):return "This itinerary has a connection or stop. The exact procedure depends on the airports, airline and ticket."
            return "We can explain the itinerary, but some details still need to be confirmed."
        if direct is True:return "Este viaje aparece como directo: no se indica una conexión entre el origen y el destino."
        if connection or (stops is not None and stops>0):return "Este viaje tiene una escala o conexión. Lo que debes hacer depende de los aeropuertos, la aerolínea y tu boleto."
        return "Podemos explicar el viaje, pero todavía hay datos que deben confirmarse."

    def baggage_source_for_flight(self,flight:Any)->List[Dict[str,Any]]:
        if hasattr(flight,"model_dump"):d=flight.model_dump()
        elif hasattr(flight,"dict"):d=flight.dict()
        elif isinstance(flight,dict):d=flight
        else:d={}
        return [self._source_card(s) for s in self.registry.baggage_sources(d.get("airline"),d.get("origin"),d.get("destination"))]

    def source_for_airline(self,airline:str)->List[Dict[str,Any]]:
        return [self._source_card(s) for s in self.registry.official_for_airline(airline)]

    def cuba_sources(self,airline:Optional[str]=None)->List[Dict[str,Any]]:
        sources=[]
        for s in self.registry.route_sources("United States","Cuba",airline,include_search=False):
            if s not in sources:sources.append(s)
        for sid in ("dviajeros","evisa_cuba"):
            s=self.registry.get(sid)
            if s and s not in sources:sources.append(s)
        return [self._source_card(s) for s in sources]

    def build_selected_flight(self,data:Dict[str,Any],source:Optional[str]=None,source_name:Optional[str]=None,verified:bool=False,official_source:bool=False)->FlightOption:
        source_obj=self.registry.get(source) if source else None
        return FlightOption(
            id=str(data.get("id") or data.get("flight_id") or "selected-flight"),
            airline=data.get("airline"),
            flight_number=data.get("flight_number"),
            origin=data.get("origin"),
            destination=data.get("destination"),
            departure=data.get("departure") or data.get("departure_time"),
            arrival=data.get("arrival") or data.get("arrival_time"),
            date=data.get("date") or data.get("departure_date"),
            direct=data.get("direct"),
            stops=data.get("stops"),
            connection=data.get("connection"),
            connection_airport=data.get("connection_airport"),
            connection_duration=data.get("connection_duration"),
            passengers=data.get("passengers"),
            cabin=data.get("cabin"),
            fare=data.get("fare"),
            currency=data.get("currency"),
            baggage_summary=data.get("baggage_summary"),
            source=source or data.get("source") or (source_obj.url if source_obj else None),
            source_name=source_name or data.get("source_name") or (source_obj.name if source_obj else None),
            verified=verified or bool(data.get("verified")),
            verified_at=data.get("verified_at") or (source_obj.verification_date if source_obj and source_obj.verified else None),
            official_source=official_source or bool(data.get("official_source")) or bool(source_obj and source_obj.official),
            conditions=data.get("conditions") or []
        )

    def no_fake_results_message(self,language="es")->str:
        if language=="en":
            return "We do not invent flight results. Select or enter the flight you found, and we will help you understand it and prepare your baggage."
        return "No inventamos vuelos. Selecciona o escribe el vuelo que encontraste y te ayudamos a entenderlo y a preparar tu equipaje."

    def _message(self,kind,language,errors):
        if language=="en":
            if kind=="errors":return "Before we continue, fix this: "+" ".join(errors)
            return "First find or select your flight. Then we will help you understand the route, connection, fare and baggage."
        if kind=="errors":return "Antes de continuar, corrige esto: "+" ".join(errors)
        return "Primero encuentra o selecciona tu vuelo. Después te ayudamos a entender la ruta, la conexión, la tarifa y el equipaje."

    def _next_action(self,language="es",missing=None):
        if missing:
            if language=="en":return "Find the missing information in the flight details and then continue with baggage preparation."
            return "Busca esos datos en los detalles del vuelo y después continúa con la preparación del equipaje."
        if language=="en":return "Select the flight you will actually take so we can review it without inventing information."
        return "Selecciona el vuelo que realmente vas a tomar para poder revisarlo sin inventar información."

    def _important(self,language="es"):
        if language=="en":return "A source being listed does not mean that you selected that airline or that a flight is confirmed. Final flight, baggage and travel conditions must be confirmed with the applicable official source."
        return "Que una fuente aparezca en la lista no significa que hayas seleccionado esa aerolínea ni que exista un vuelo confirmado. El vuelo, el equipaje y las condiciones del viaje deben confirmarse con la fuente oficial correspondiente."

ENGINE=FlightEngine()
flight_engine=ENGINE
search_flights=ENGINE.search
understand_flight=ENGINE.understand

__all__=["FlightQuery","FlightOption","FlightEngine","ENGINE","flight_engine","search_flights","understand_flight","google_flights_url"]
