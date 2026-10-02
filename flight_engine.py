# flight_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.2
from dataclasses import asdict,dataclass
from typing import Any,Dict,List,Optional
from source_registry import REGISTRY,Source,google_flights_url

VERSION="8.0.2"

@dataclass
class FlightQuery:
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    passengers:int=1
    cabin:str=""
    airline:str=""
    nonstop:Optional[bool]=None
    language:str="es"

@dataclass
class FlightOption:
    id:str
    airline:str=""
    flight_number:str=""
    origin:str=""
    destination:str=""
    departure:str=""
    arrival:str=""
    date:str=""
    direct:bool=False
    stops:int=0
    connection:bool=False
    connection_airport:str=""
    connection_duration:str=""
    passengers:int=1
    cabin:str=""
    fare:str=""
    currency:str="USD"
    baggage_summary:str=""
    source:str=""
    source_name:str=""
    verified:bool=False
    verified_at:str=""
    official_source:bool=False
    conditions:Optional[List[str]]=None
    def to_dict(self)->Dict[str,Any]:
        d=asdict(self)
        d["conditions"]=self.conditions or []
        return d

class FlightEngine:
    VERSION=VERSION
    AIRPORTS={
        "miami":"MIA","mia":"MIA",
        "havana":"HAV","habana":"HAV","hav":"HAV",
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
        "camaguey":"CMW","camagüey":"CMW","camaguey cuba":"CMW","cmw":"CMW",
    }
    CUBA_AIRPORTS={"HAV","VRA","SCU","CMW"}
    CUBA_TERMS={
        "cuba","havana","habana","hav","varadero","vra",
        "santiago de cuba","santiago","scu","camaguey","camagüey","cmw"
    }
    CHARTER_IDS={
        "cubazul_air_charter",
        "xael_charters",
        "cuballama_viajes",
        "ibc_airways"
    }

    def normalize(self,value:Any)->str:
        return " ".join(str(value or "").strip().lower().replace("_"," ").split())

    def airport_code(self,value:Any)->str:
        v=self.normalize(value)
        return self.AIRPORTS.get(v,v.upper() if len(v)==3 else "")

    def display_place(self,value:Any)->str:
        code=self.airport_code(value)
        if code:
            for name,c in self.AIRPORTS.items():
                if c==code and len(name)>3:
                    return name.title()
            return code
        return str(value or "").strip()

    def is_cuba(self,value:Any)->bool:
        v=self.normalize(value)
        code=self.airport_code(value)
        return code in self.CUBA_AIRPORTS or any(term==v or term in v for term in self.CUBA_TERMS)

    def is_cuba_route(self,origin:Any,destination:Any)->bool:
        return self.is_cuba(origin) or self.is_cuba(destination)

    def build_query(self,data:Any=None,**kwargs)->FlightQuery:
        if isinstance(data,FlightQuery):
            return data
        if isinstance(data,dict):
            src=dict(data)
            src.update({k:v for k,v in kwargs.items() if v is not None})
        else:
            src=dict(kwargs)
        try:
            passengers=max(1,int(src.get("passengers") or 1))
        except Exception:
            passengers=1
        return FlightQuery(
            origin=str(src.get("origin") or ""),
            destination=str(src.get("destination") or ""),
            departure_date=str(src.get("departure_date") or ""),
            return_date=str(src.get("return_date") or ""),
            passengers=passengers,
            cabin=str(src.get("cabin") or ""),
            airline=str(src.get("airline") or ""),
            nonstop=src.get("nonstop"),
            language="en" if str(src.get("language") or "es").lower()=="en" else "es"
        )

    def validate_query(self,query:Any)->List[str]:
        q=self.build_query(query)
        errors=[]
        if not self.airport_code(q.origin):
            errors.append("origin" if q.language=="en" else "origen")
        if not self.airport_code(q.destination):
            errors.append("destination" if q.language=="en" else "destino")
        if q.passengers<1 or q.passengers>20:
            errors.append("passengers" if q.language=="en" else "pasajeros")
        return errors

    def source_cards(self,origin:str="",destination:str="",airline:str="",language:str="es")->List[Dict[str,Any]]:
        sources=REGISTRY.route_sources(origin,destination,airline,include_search=True)
        if self.is_cuba_route(origin,destination):
            sources=self._ensure_charter_sources(sources)
        out=[self._source_card(s,language) for s in sources]
        if not any(x.get("id")=="google_flights" for x in out):
            s=REGISTRY.get("google_flights")
            if s:
                out.append(self._source_card(s,language))
        return self._unique_dicts(out)

    def charter_sources(self,language:str="es")->List[Dict[str,Any]]:
        sources=[]
        try:
            sources=REGISTRY.charter_sources()
        except Exception:
            sources=[]
        if not sources:
            for sid in (
                "cubazul_air_charter",
                "xael_charters",
                "cuballama_viajes",
                "ibc_airways"
            ):
                s=REGISTRY.get(sid)
                if s:
                    sources.append(s)
        return [self._source_card(s,language,charter=True) for s in self._unique(sources)]

    def official_charter_sources(self,language:str="es")->List[Dict[str,Any]]:
        try:
            sources=REGISTRY.official_charter_sources()
        except Exception:
            sources=[]
        if not sources:
            return self.charter_sources(language)
        return [self._source_card(s,language,charter=True) for s in self._unique(sources)]

    def airline_sources(self,airline:str="",language:str="es")->List[Dict[str,Any]]:
        sources=REGISTRY.official_for_airline(airline)
        return [self._source_card(s,language) for s in sources]

    def search_sources(self,origin:str="",destination:str="",airline:str="",language:str="es")->List[Dict[str,Any]]:
        return self.source_cards(origin,destination,airline,language)

    def _ensure_charter_sources(self,sources:List[Source])->List[Source]:
        out=list(sources or [])
        ids={s.id for s in out}
        try:
            charter=REGISTRY.charter_sources()
        except Exception:
            charter=[]
        if not charter:
            charter=[
                REGISTRY.get("cubazul_air_charter"),
                REGISTRY.get("xael_charters"),
                REGISTRY.get("cuballama_viajes"),
                REGISTRY.get("ibc_airways")
            ]
            charter=[s for s in charter if s]
        for source in charter:
            if source.id not in ids:
                out.append(source)
                ids.add(source.id)
        return out

    def _source_card(self,source:Source,language:str="es",charter:bool=False)->Dict[str,Any]:
        en=str(language or "es").lower()=="en"
        note=source.notes or ""
        if source.id=="google_flights":
            note=(
                "Flight search and discovery. Confirm the final itinerary with the airline."
                if en else
                "Búsqueda y descubrimiento de vuelos. Confirma el itinerario final con la aerolínea."
            )
        elif source.id=="cubazul_air_charter":
            note=(
                "Official Cubazul Air Charter source. Check current Cuba routes, dates, availability, baggage and ticket conditions directly."
                if en else
                "Fuente oficial de Cubazul Air Charter. Consulta directamente las rutas a Cuba, fechas, disponibilidad, equipaje y condiciones del boleto."
            )
        elif source.id=="xael_charters":
            note=(
                "Official Xael Charters source. Check current Cuba destinations, dates, availability, baggage and ticket conditions directly."
                if en else
                "Fuente oficial de Xael Charters. Consulta directamente los destinos a Cuba, fechas, disponibilidad, equipaje y condiciones del boleto."
            )
        elif source.id=="cuballama_viajes":
            note=(
                "Official Cuballama Viajes charter section. Confirm the current route, date, availability, baggage and ticket conditions directly."
                if en else
                "Sección oficial de vuelos chárter de Cuballama Viajes. Confirma directamente la ruta, fecha, disponibilidad, equipaje y condiciones del boleto."
            )
        elif source.id=="ibc_airways":
            note=(
                "Official IBC Airways source. Passenger and cargo services are listed by the company; do not assume a Cuba route or availability. Confirm directly."
                if en else
                "Fuente oficial de IBC Airways. La compañía informa servicios de pasajeros y carga; no se debe asumir una ruta a Cuba ni disponibilidad. Confirma directamente."
            )
        elif charter and not note:
            note=(
                "Official charter/travel source. Confirm current availability and conditions directly."
                if en else
                "Fuente oficial de vuelos chárter/servicios de viaje. Confirma directamente la disponibilidad y las condiciones actuales."
            )
        return {
            "id":source.id,
            "name":source.name,
            "url":source.url,
            "alternate_url":getattr(source,"alternate_url","") or "",
            "source_type":source.source_type,
            "country":source.country,
            "airline":source.airline,
            "destination":source.destination,
            "scope":source.scope,
            "official":source.official,
            "verified":source.verified,
            "verification_date":source.verification_date,
            "notes":note
        }

    def search(self,query:Any=None,**kwargs)->Dict[str,Any]:
        q=self.build_query(query,**kwargs)
        errors=self.validate_query(q)
        sources=self.source_cards(q.origin,q.destination,q.airline,q.language)
        charter=self.charter_sources(q.language) if self.is_cuba_route(q.origin,q.destination) else []
        google_url=google_flights_url(q.origin,q.destination,q.departure_date,q.return_date)
        en=q.language=="en"
        if errors:
            message=(
                "Please provide a valid origin and destination airport or city."
                if en else
                "Indica un origen y un destino válidos."
            )
            next_action=(
                "Review the origin and destination."
                if en else
                "Revisa el origen y el destino."
            )
        else:
            message=(
                "The app does not invent or publish flight availability. Use the listed official sources to search and confirm the actual itinerary."
                if en else
                "La aplicación no inventa ni publica disponibilidad de vuelos. Usa las fuentes oficiales mostradas para buscar y confirmar el itinerario real."
            )
            next_action=(
                "Open a source and confirm the actual flight, baggage conditions and itinerary."
                if en else
                "Abre una fuente y confirma el vuelo real, las condiciones de equipaje y el itinerario."
            )
        return {
            "results":[],
            "sources":sources,
            "charter_sources":charter,
            "message":message,
            "source":"official_sources" if any(s.get("official") for s in sources) else "source_registry",
            "verified":False,
            "official_source":False,
            "next_action":next_action,
            "route":{
                "origin":q.origin,
                "destination":q.destination,
                "departure_date":q.departure_date,
                "return_date":q.return_date
            },
            "google_flights_url":google_url,
            "airline_sources":self.airline_sources(q.airline,q.language) if q.airline else [],
            "is_cuba_route":self.is_cuba_route(q.origin,q.destination),
            "important":self._important(q.language),
            "errors":errors
        }

    def understand(self,data:Any,language:str="es")->Dict[str,Any]:
        if not isinstance(data,dict):
            data={}
        lang="en" if str(language or "es").lower()=="en" else "es"
        origin=str(data.get("origin") or "")
        destination=str(data.get("destination") or "")
        airline=str(data.get("airline") or "")
        baggage=data.get("baggage") or {}
        baggage_summary=str(data.get("baggage_summary") or (baggage.get("summary") if isinstance(baggage,dict) else "") or "")
        if not baggage_summary and isinstance(baggage,dict):
            parts=[]
            for k,v in baggage.items():
                if v not in (None,"",False,0):
                    parts.append(f"{k}: {v}")
            baggage_summary=", ".join(parts)
        missing=[]
        if not origin:
            missing.append("origin" if lang=="en" else "origen")
        if not destination:
            missing.append("destination" if lang=="en" else "destino")
        if not airline:
            missing.append("airline" if lang=="en" else "aerolínea")
        if not baggage_summary:
            missing.append("baggage information" if lang=="en" else "información de equipaje")
        explanation=self._explanation(lang,origin,destination,airline,baggage_summary)
        return {
            "success":True,
            "origin":origin,
            "destination":destination,
            "airline":airline,
            "baggage":baggage if isinstance(baggage,dict) else {},
            "baggage_summary":baggage_summary,
            "missing_information":missing,
            "explanation":explanation,
            "steps":self._understanding_steps(lang),
            "next_action":(
                "Provide the missing information before applying a specific baggage interpretation."
                if lang=="en" else
                "Completa la información que falta antes de aplicar una interpretación específica del equipaje."
            ),
            "verified":False,
            "official_source":False,
            "legal_notice":self._message("legal",lang)
        }

    def _understanding_steps(self,lang:str)->List[str]:
        if lang=="en":
            return [
                "Identify the actual airline and route.",
                "Identify the baggage type and relevant article.",
                "Check the airline's current conditions.",
                "Check government or security requirements when applicable.",
                "Confirm the final condition before traveling."
            ]
        return [
            "Identifica la aerolínea y la ruta real.",
            "Identifica el tipo de equipaje y el artículo.",
            "Revisa las condiciones actuales de la aerolínea.",
            "Revisa los requisitos de seguridad o gubernamentales cuando correspondan.",
            "Confirma la condición final antes de viajar."
        ]

    def _explanation(self,lang:str,origin:str,destination:str,airline:str,baggage:str)->str:
        if lang=="en":
            base="Flight and baggage conditions depend on the actual itinerary, airline, fare, baggage type and applicable authorities."
            if origin and destination:
                base+=f" The route entered is {origin} → {destination}."
            if airline:
                base+=f" The airline entered is {airline}."
            if baggage:
                base+=f" The available baggage information is: {baggage}."
            return base+" The app does not guess missing conditions."
        base="Las condiciones del vuelo y del equipaje dependen del itinerario real, la aerolínea, la tarifa, el tipo de equipaje y las autoridades aplicables."
        if origin and destination:
            base+=f" La ruta indicada es {origin} → {destination}."
        if airline:
            base+=f" La aerolínea indicada es {airline}."
        if baggage:
            base+=f" La información de equipaje disponible es: {baggage}."
        return base+" La aplicación no adivina condiciones que faltan."

    def baggage_source_for_flight(self,flight:Any,language:str="es")->Optional[Dict[str,Any]]:
        if isinstance(flight,FlightOption):
            origin,destination,airline=flight.origin,flight.destination,flight.airline
        elif isinstance(flight,dict):
            origin=str(flight.get("origin") or "")
            destination=str(flight.get("destination") or "")
            airline=str(flight.get("airline") or "")
        else:
            return None
        sources=REGISTRY.baggage_sources(origin,destination,airline)
        if sources:
            return self._source_card(sources[0],language)
        if airline:
            source=REGISTRY.official_for_airline(airline)
            if source:
                return self._source_card(source[0],language)
        return None

    def source_for_airline(self,airline:str,language:str="es")->Optional[Dict[str,Any]]:
        sources=REGISTRY.official_for_airline(airline)
        return self._source_card(sources[0],language) if sources else None

    def cuba_sources(self,origin:str="",destination:str="",airline:str="",language:str="es")->List[Dict[str,Any]]:
        sources=REGISTRY.route_sources(
            origin or "United States",
            destination or "Cuba",
            airline,
            include_search=False
        )
        sources=self._ensure_charter_sources(sources)
        existing={s.id for s in sources}
        for sid in ("dviajeros","evisa_cuba"):
            s=REGISTRY.get(sid)
            if s and sid not in existing:
                sources.append(s)
                existing.add(sid)
        return [self._source_card(s,language,charter=s.id in self.CHARTER_IDS) for s in self._unique(sources)]

    def build_selected_flight(self,data:Any)->FlightOption:
        d=data if isinstance(data,dict) else {}
        try:
            passengers=max(1,int(d.get("passengers") or 1))
        except Exception:
            passengers=1
        try:
            stops=max(0,int(d.get("stops") or 0))
        except Exception:
            stops=0
        return FlightOption(
            id=str(d.get("id") or "selected-flight"),
            airline=str(d.get("airline") or ""),
            flight_number=str(d.get("flight_number") or ""),
            origin=str(d.get("origin") or ""),
            destination=str(d.get("destination") or ""),
            departure=str(d.get("departure") or ""),
            arrival=str(d.get("arrival") or ""),
            date=str(d.get("date") or d.get("departure_date") or ""),
            direct=bool(d.get("direct") or d.get("nonstop")),
            stops=stops,
            connection=bool(d.get("connection")),
            connection_airport=str(d.get("connection_airport") or ""),
            connection_duration=str(d.get("connection_duration") or ""),
            passengers=passengers,
            cabin=str(d.get("cabin") or ""),
            fare=str(d.get("fare") or ""),
            currency=str(d.get("currency") or "USD").upper(),
            baggage_summary=str(d.get("baggage_summary") or ""),
            source=str(d.get("source") or ""),
            source_name=str(d.get("source_name") or ""),
            verified=bool(d.get("verified")),
            verified_at=str(d.get("verified_at") or ""),
            official_source=bool(d.get("official_source")),
            conditions=d.get("conditions") if isinstance(d.get("conditions"),list) else []
        )

    def no_fake_results_message(self,language:str="es")->str:
        return self._message("no_results",language)

    def _message(self,key:str,lang:str)->str:
        if lang=="en":
            return {
                "no_results":"No live flight result is published here. Search the actual itinerary through the airline, charter provider or flight-search source and confirm it directly.",
                "legal":"The app organizes and explains information but does not replace the airline, charter provider, airport, government or other competent authority."
            }.get(key,"")
        return {
            "no_results":"Aquí no se publica un resultado de vuelo en vivo. Busca el itinerario real mediante la aerolínea, el proveedor chárter o una fuente de búsqueda y confírmalo directamente.",
            "legal":"La aplicación organiza y explica información, pero no sustituye a la aerolínea, al proveedor chárter, al aeropuerto, al gobierno ni a otra autoridad competente."
        }.get(key,"")

    def _next_action(self,language:str)->str:
        return (
            "Confirm the actual itinerary with the airline or charter provider and the applicable official sources."
            if language=="en" else
            "Confirma el itinerario real con la aerolínea o proveedor chárter y las fuentes oficiales aplicables."
        )

    def _important(self,language:str)->List[str]:
        if language=="en":
            return [
                "Flight availability is not invented by the app.",
                "Search results are not a ticket or reservation.",
                "Airline, charter-provider and official government requirements can change.",
                "Confirm the final conditions before traveling."
            ]
        return [
            "La aplicación no inventa disponibilidad de vuelos.",
            "Un resultado de búsqueda no es un boleto ni una reserva.",
            "Las condiciones de la aerolínea, del proveedor chárter y los requisitos oficiales pueden cambiar.",
            "Confirma las condiciones finales antes de viajar."
        ]

    def _unique(self,items:List[Source])->List[Source]:
        seen=set()
        out=[]
        for item in items:
            if not item:
                continue
            key=item.id or item.url or item.name
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    def _unique_dicts(self,items:List[Dict[str,Any]])->List[Dict[str,Any]]:
        seen=set()
        out=[]
        for item in items:
            key=item.get("id") or item.get("url") or item.get("name")
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

engine=FlightEngine()
flight_engine=engine
