# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.2
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional
from urllib.parse import quote_plus

VERSION="8.0.2"
VERIFICATION_DATE="2026-10-01"

@dataclass
class Source:
    id:str
    name:str
    url:str
    category:str=""
    description:str=""
    official:bool=True
    alternate_url:Optional[str]=None
    verified_date:Optional[str]=VERIFICATION_DATE

    def to_dict(self)->Dict[str,Any]:
        return asdict(self)

class SourceRegistry:
    def __init__(self):
        self.sources:Dict[str,Source]={}
        self._load_defaults()

    def add(self,s:Source):
        if s and s.id:self.sources[s.id]=s
        return s

    def get(self,id:str)->Optional[Source]:
        return self.sources.get(id)

    def all(self)->List[Source]:
        return list(self.sources.values())

    def _load_defaults(self):
        items=[
            Source("american_airlines","American Airlines","https://www.aa.com/","airline","Sitio oficial de American Airlines."),
            Source("southwest_airlines","Southwest Airlines","https://www.southwest.com/","airline","Sitio oficial de Southwest Airlines."),
            Source("delta_air_lines","Delta Air Lines","https://www.delta.com/","airline","Sitio oficial de Delta Air Lines."),
            Source("cubazul_air_charter","Cubazul Air Charter","https://cubazulaircharter.com/","charter","Proveedor de vuelos chárter; verificar directamente ruta, fecha, precio y disponibilidad."),
            Source("xael_charters","Xael Charters","https://www.xaelcharter.com/","charter","Proveedor de vuelos chárter a Cuba; verificar directamente ruta, fecha, precio y disponibilidad."),
            Source("cuballama_viajes","Cuballama Viajes","https://www.cuballama.com/viajes/vuelos/charters","charter","Servicio de viajes con vuelos chárter a Cuba.",alternate_url="https://www.cuballama.com/viajes/"),
            Source("ibc_airways","IBC Airways","https://ibcairways.com/","charter","Aerolínea con servicios en el Caribe; confirmar directamente si existe servicio Cuba para la fecha consultada.",alternate_url="https://flyibc.com/"),
            Source("google_flights","Google Flights","https://www.google.com/travel/flights","search","Buscador de vuelos; no sustituye la confirmación del proveedor."),
            Source("tsa","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring/all","security","Fuente oficial de seguridad para artículos en equipaje."),
            Source("faa_packsafe","FAA PackSafe","https://www.faa.gov/hazmat/packsafe","security","Información oficial sobre materiales peligrosos y equipaje."),
            Source("faa_batteries","FAA Batteries","https://www.faa.gov/hazmat/resources/lithium_batteries","security","Información oficial sobre baterías de litio."),
            Source("faa_lithium","FAA Lithium Batteries","https://www.faa.gov/hazmat/packsafe/lithium-batteries","security","Orientación oficial sobre baterías de litio."),
            Source("dviajeros","D'Viajeros","https://dviajeros.mitrans.gob.cu/","cuba","Portal oficial cubano para el formulario D'Viajeros."),
            Source("evisa_cuba","eVisa Cuba","https://evisacuba.cu/","cuba","Portal oficial para información y gestión de visa electrónica de Cuba.")
        ]
        for x in items:self.add(x)

    def _norm(self,v:str)->str:
        s=str(v or "").lower()
        for a,b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ü","u"),("ñ","n")):s=s.replace(a,b)
        return " ".join(s.split())

    def search(self,query:str="",category:str="",limit:int=50)->List[Source]:
        q=self._norm(query)
        c=self._norm(category)
        out=[]
        for s in self.all():
            hay=self._norm(f"{s.id} {s.name} {s.description} {s.category}")
            if q and q not in hay:continue
            if c and c!=self._norm(s.category):continue
            out.append(s)
            if len(out)>=limit:break
        return out

    def airline_alias(self,airline:str)->str:
        n=self._norm(airline)
        aliases={
            "american":"american_airlines","american airlines":"american_airlines","aa":"american_airlines",
            "southwest":"southwest_airlines","southwest airlines":"southwest_airlines",
            "delta":"delta_air_lines","delta airlines":"delta_air_lines","delta air lines":"delta_air_lines",
            "cubazul":"cubazul_air_charter","cubazul air charter":"cubazul_air_charter",
            "xael":"xael_charters","xael charters":"xael_charters",
            "cuballama":"cuballama_viajes","cuballama viajes":"cuballama_viajes",
            "ibc":"ibc_airways","ibc airways":"ibc_airways"
        }
        return aliases.get(n,"")

    def destination_alias(self,destination:str)->str:
        n=self._norm(destination)
        aliases={
            "cuba":"cuba","cuba":"cuba","havana":"havana","habana":"havana",
            "varadero":"varadero","camaguey":"camaguey","camagüey":"camaguey",
            "santiago":"santiago de cuba","santiago de cuba":"santiago de cuba",
            "holguin":"holguin","holguín":"holguin","santa clara":"santa clara"
        }
        return aliases.get(n,n)

    def get_charter_sources(self)->List[Source]:
        ids={"cubazul_air_charter","xael_charters","cuballama_viajes","ibc_airways"}
        return [self.sources[i] for i in ids if i in self.sources]

    def charter_sources(self)->List[Source]:
        return self.get_charter_sources()

    def official_charter_sources(self)->List[Source]:
        return self.get_charter_sources()

    def official_for_airline(self,airline:str="")->List[Source]:
        aid=self.airline_alias(airline)
        if aid and aid in self.sources:return [self.sources[aid]]
        return []

    def cuba_sources(self)->List[Source]:
        ids=["dviajeros","evisa_cuba"]
        out=[self.sources[i] for i in ids if i in self.sources]
        for s in self.get_charter_sources():
            if s not in out:out.append(s)
        return out

    def official_sources(self)->List[Source]:
        return [x for x in self.all() if x.official]

    def route_sources(self,origin:str="",destination:str="",airline:str="")->List[Source]:
        out=[]
        if airline:out.extend(self.official_for_airline(airline))
        text=self._norm(f"{origin} {destination}")
        cuba=any(x in text for x in ["cuba","havana","habana","varadero","camaguey","camaguey","santiago de cuba","holguin","santa clara"])
        if cuba:
            for s in self.get_charter_sources()+self.cuba_sources():
                if s not in out:out.append(s)
        return out

    def google_flights_url(self,origin:str,destination:str,departure_date:str="",return_date:str="")->str:
        q=f"{origin} to {destination}"
        if departure_date:q+=f" {departure_date}"
        if return_date:q+=f" return {return_date}"
        return f"https://www.google.com/travel/flights?q={quote_plus(q)}"

REGISTRY=SourceRegistry()

def google_flights_url(origin:str,destination:str,departure_date:str="",return_date:str="")->str:
    return REGISTRY.google_flights_url(origin,destination,departure_date,return_date)

def get_official_sources()->List[Dict[str,Any]]:
    return [x.to_dict() for x in REGISTRY.official_sources()]

def get_charter_sources()->List[Dict[str,Any]]:
    return [x.to_dict() for x in REGISTRY.get_charter_sources()]
