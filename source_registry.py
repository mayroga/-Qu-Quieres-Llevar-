# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.0
from dataclasses import dataclass,asdict
from datetime import date
from typing import Any,Dict,List,Optional
from urllib.parse import quote_plus

VERIFICATION_DATE="2026-10-01"

@dataclass
class Source:
    id:str
    name:str
    url:str
    source_type:str="other"
    country:Optional[str]=None
    airline:Optional[str]=None
    destination:Optional[str]=None
    scope:Optional[str]=None
    official:bool=False
    verified:bool=False
    verification_date:Optional[str]=None
    notes:Optional[str]=None
    def to_dict(self)->Dict[str,Any]:
        return asdict(self)

class SourceRegistry:
    def __init__(self,sources:Optional[List[Source]]=None):
        self._sources={}
        for s in sources or self._default_sources(): self.add(s)

    def add(self,source:Source)->Source:
        self._sources[source.id]=source
        return source

    def get(self,source_id:str)->Optional[Source]:
        return self._sources.get(str(source_id).strip())

    def all(self)->List[Source]:
        return list(self._sources.values())

    def list_dicts(self)->List[Dict[str,Any]]:
        return [s.to_dict() for s in self.all()]

    def to_dict(self)->List[Dict[str,Any]]:
        return self.list_dicts()

    def verified(self)->List[Source]:
        return [s for s in self.all() if s.verified]

    def official(self)->List[Source]:
        return [s for s in self.all() if s.official]

    def search(self,query:str="",country:Optional[str]=None,airline:Optional[str]=None,destination:Optional[str]=None,source_type:Optional[str]=None,official_only:bool=False,verified_only:bool=False)->List[Source]:
        q=self._norm(query)
        out=[]
        for s in self.all():
            if official_only and not s.official: continue
            if verified_only and not s.verified: continue
            if country and self._norm(country) not in self._norm(s.country or ""): continue
            if airline and self._norm(airline) not in self._norm(s.airline or ""): continue
            if destination and not self._destination_match(s.destination,destination): continue
            if source_type and self._norm(source_type)!=self._norm(s.source_type): continue
            if q:
                hay=" ".join([s.id,s.name,s.url,s.scope or "",s.notes or "",s.airline or "",s.destination or "",s.country or ""])
                if q not in self._norm(hay): continue
            out.append(s)
        return out

    def route_sources(self,origin:Optional[str]=None,destination:Optional[str]=None,airline:Optional[str]=None,include_search:bool=True)->List[Source]:
        o=self._norm(origin)
        d=self._norm(destination)
        a=self._norm(airline)
        exact=[]
        broad=[]
        for s in self.all():
            if s.source_type=="search": continue
            if a and s.airline and a not in self._norm(s.airline): continue
            if a and not s.airline and s.source_type in ("airline","charter"): continue
            smatch=self._route_match(s,o,d)
            if smatch==2: exact.append(s)
            elif smatch==1: broad.append(s)
        out=self._unique(exact+broad)
        if include_search:
            for s in self.all():
                if s.source_type=="search" and s not in out: out.append(s)
        return out

    def baggage_sources(self,airline:Optional[str]=None,origin:Optional[str]=None,destination:Optional[str]=None)->List[Source]:
        a=self._norm(airline)
        out=[]
        if a:
            for s in self.all():
                if s.source_type in ("airline","charter") and s.airline and a in self._norm(s.airline):
                    if s.scope and any(x in self._norm(s.scope) for x in ("equipaje","baggage","bag")): out.append(s)
        for s in self.all():
            if s.id in {x.id for x in out}: continue
            if s.id in ("tsa_what_can_i_bring","faa_packsafe","faa_batteries"):
                out.append(s)
        return out

    def official_for_airline(self,airline:str)->List[Source]:
        a=self._norm(airline)
        return [s for s in self.all() if s.official and s.airline and a in self._norm(s.airline)]

    def source_for_id(self,source_id:str)->Optional[Dict[str,Any]]:
        s=self.get(source_id)
        return s.to_dict() if s else None

    def _route_match(self,s:Source,origin:str,destination:str)->int:
        d=self._norm(s.destination or "")
        scope=self._norm(s.scope or "")
        if not destination: return 0
        dest_alias=self._destination_aliases(destination)
        if d and any(x in d for x in dest_alias):
            if not origin:return 2
            if not s.scope:return 1
            if any(x in scope for x in self._origin_aliases(origin)): return 2
            if "estados unidos" in scope and self._is_us_origin(origin): return 2
            return 1
        if any(x in scope for x in dest_alias):
            if not origin:return 1
            if any(x in scope for x in self._origin_aliases(origin)): return 2
            if "estados unidos" in scope and self._is_us_origin(origin): return 2
            return 1
        return 0

    def _destination_match(self,value:Optional[str],destination:str)->bool:
        if not value:return True
        d=self._norm(value)
        return any(x in d for x in self._destination_aliases(destination))

    def _origin_aliases(self,value:str)->List[str]:
        n=self._norm(value)
        aliases=[n]
        maps={
            "miami":["miami","mia"],
            "miami international":["miami","mia"],
            "fort lauderdale":["fort lauderdale","fll"],
            "tampa":["tampa","tpa"],
            "orlando":["orlando","mco"],
            "atlanta":["atlanta","atl"],
            "new york":["new york","jfk","ewr","lga"],
            "houston":["houston","iah","hou"],
            "los angeles":["los angeles","lax"],
            "new orleans":["new orleans","msy"],
            "baltimore":["baltimore","bwi"],
        }
        for k,v in maps.items():
            if n==k or n in v: aliases+=v
        return list(dict.fromkeys(aliases))

    def _destination_aliases(self,value:str)->List[str]:
        n=self._norm(value)
        maps={
            "cuba":["cuba"],
            "la habana":["la habana","la habana","havana","hav"],
            "havana":["havana","la habana","hav"],
            "santiago de cuba":["santiago de cuba","santiago","scu"],
            "varadero":["varadero","vra"],
            "camaguey":["camaguey","camagüey","cmw"],
            "mexico":["mexico","méxico"],
            "guatemala":["guatemala"],
            "honduras":["honduras"],
            "el salvador":["el salvador"],
            "republica dominicana":["republica dominicana","república dominicana","dominican republic"],
        }
        for k,v in maps.items():
            if n==k or n in v:return v
        return [n]

    def _is_us_origin(self,value:str)->bool:
        n=self._norm(value)
        return any(x in n for x in ("mia","fll","tpa","mco","atl","jfk","ewr","lga","iah","hou","lax","msy","bwi","orlando","miami","tampa","atlanta","new york","houston","los angeles","new orleans","baltimore","estados unidos","united states"))

    def _destination_is_cuba(self,value:str)->bool:
        return any(x in self._norm(value) for x in ("cuba","havana","la habana","hav","santiago de cuba","scu","varadero","vra","camaguey","cmw"))

    def _unique(self,items:List[Source])->List[Source]:
        seen=set();out=[]
        for s in items:
            if s.id not in seen:
                seen.add(s.id);out.append(s)
        return out

    def _norm(self,value:Any)->str:
        import unicodedata
        s=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode("ascii").lower()
        return " ".join(s.split())

    def _default_sources(self)->List[Source]:
        return [
            Source("aa_mia_havana","American Airlines — Miami → Havana","https://www.aa.com/en-us/flights-from-miami-to-havana","airline","United States","American Airlines","Havana","Vuelos Miami–La Habana",True,True,VERIFICATION_DATE,"Página oficial de American; las tarifas cambian y algunas opciones pueden incluir conexiones."),
            Source("aa_us_cuba","American Airlines — United States → Cuba","https://www.aa.com/en-us/flights-from-united-states-to-cuba","airline","United States","American Airlines","Cuba","Vuelos desde Estados Unidos a Cuba",True,True,VERIFICATION_DATE,"Fuente oficial para consultar opciones actuales."),
            Source("aa_cuba","American Airlines — Cuba","https://www.aa.com/en-us/flights-to-cuba","airline","United States","American Airlines","Cuba","Vuelos a Cuba",True,True,VERIFICATION_DATE,"Fuente oficial; no se interpreta como disponibilidad garantizada."),
            Source("southwest_havana","Southwest Airlines — Havana","https://www.southwest.com/en/flights/flights-to-havana","airline","United States","Southwest Airlines","Havana","Vuelos a La Habana; página oficial de Southwest",True,True,VERIFICATION_DATE,"La ruta y disponibilidad dependen de fecha y aeropuerto de origen."),
            Source("delta_latam_caribbean","Delta Air Lines — Caribbean/Latin America","https://www.delta.com/us/en/flight-deals/flights-to-latin-america","airline","United States","Delta Air Lines","Caribbean/Latin America","Información y búsqueda de destinos del Caribe y Latinoamérica",True,True,VERIFICATION_DATE,"No se presenta como confirmación de una ruta concreta."),
            Source("cubazul","Cubazul Air Charter","https://www.cubazulaircharter.com/","charter","United States","Cubazul Air Charter","Cuba","Operador charter; consultar ruta y fecha directamente",True,True,VERIFICATION_DATE,"No se selecciona automáticamente como aerolínea del usuario."),
            Source("xael","XAEL Charter","https://www.xaelcharter.com/","charter","United States","XAEL","Cuba","Fuente del operador; disponibilidad debe confirmarse directamente",True,False,None,"Se mantiene como fuente de operador, nunca como vuelo o aerolínea seleccionada sin elección del usuario."),
            Source("google_flights","Google Flights","https://www.google.com/travel/flights","search",None,None,None,"Herramienta para localizar opciones de vuelos",False,True,VERIFICATION_DATE,"Herramienta de búsqueda; no es autoridad de reglas de equipaje."),
            Source("tsa_what_can_i_bring","TSA — What Can I Bring","https://www.tsa.gov/travel/security-screening/whatcanibring/all-list","government","United States",None,None,"Reglas y orientación de seguridad TSA para artículos en el punto de control",True,True,VERIFICATION_DATE,"La TSA puede decidir sobre el control de seguridad; la aerolínea puede imponer reglas adicionales."),
            Source("faa_packsafe","FAA — PackSafe","https://www.faa.gov/hazmat/packsafe","government","United States",None,None,"Materiales peligrosos y artículos relacionados con vuelos",True,True,VERIFICATION_DATE,"Aplicar junto con reglas específicas de aerolínea y viaje internacional."),
            Source("faa_batteries","FAA — Airline Passengers and Batteries","https://www.faa.gov/hazmat/packsafe/airline-passengers-and-batteries","government","United States",None,None,"Baterías, power banks y dispositivos electrónicos",True,True,VERIFICATION_DATE,"Las aerolíneas e itinerarios internacionales pueden tener condiciones adicionales."),
            Source("faa_baggage_batteries","FAA — Baggage Equipped with Lithium Batteries","https://www.faa.gov/hazmat/packsafe/baggage-with-lithium-batteries","government","United States",None,None,"Equipaje con baterías de litio",True,True,VERIFICATION_DATE,"Fuente oficial FAA."),
            Source("dviajeros","D'Viajeros Cuba","https://dviajeros.mitrans.gob.cu/","government","Cuba",None,"Cuba","Formulario y proceso oficial D'Viajeros",True,False,None,"Debe verificarse nuevamente antes de presentarlo como regla vigente."),
            Source("evisa_cuba","eVisa Cuba","https://evisacuba.cu/","government","Cuba",None,"Cuba","Información oficial relacionada con visa electrónica",True,False,None,"Debe verificarse nuevamente antes de presentar requisitos concretos."),
        ]

REGISTRY=SourceRegistry()
source_registry=REGISTRY

def get_source(source_id:str)->Optional[Source]:
    return REGISTRY.get(source_id)

def all_sources()->List[Source]:
    return REGISTRY.all()

def search_sources(query:str="",**kwargs)->List[Source]:
    return REGISTRY.search(query,**kwargs)

def route_sources(origin:Optional[str]=None,destination:Optional[str]=None,airline:Optional[str]=None,include_search:bool=True)->List[Source]:
    return REGISTRY.route_sources(origin,destination,airline,include_search)

def baggage_sources(airline:Optional[str]=None,origin:Optional[str]=None,destination:Optional[str]=None)->List[Source]:
    return REGISTRY.baggage_sources(airline,origin,destination)

def google_flights_url(origin:Optional[str]=None,destination:Optional[str]=None,departure_date:Optional[str]=None,return_date:Optional[str]=None)->str:
    parts=[]
    if origin:parts.append(str(origin).strip())
    if destination:parts.append(str(destination).strip())
    q=" to ".join(parts) if parts else ""
    if departure_date:q+=f" {departure_date}"
    if return_date:q+=f" {return_date}"
    return "https://www.google.com/travel/flights?q="+quote_plus(q or "flights")

__all__=["Source","SourceRegistry","REGISTRY","source_registry","get_source","all_sources","search_sources","route_sources","baggage_sources","google_flights_url"]
