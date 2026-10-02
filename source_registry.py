# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.1
from dataclasses import asdict,dataclass
from typing import Any,Dict,List,Optional
from urllib.parse import quote_plus

VERSION="8.0.1"
VERIFICATION_DATE="2026-10-01"

@dataclass
class Source:
    id:str
    name:str
    url:str
    source_type:str="official"
    country:str=""
    airline:str=""
    destination:str=""
    scope:str=""
    official:bool=True
    verified:bool=False
    verification_date:str=""
    notes:str=""
    def to_dict(self)->Dict[str,Any]:
        return asdict(self)

class SourceRegistry:
    def __init__(self):
        self._sources:Dict[str,Source]={}
        self._load_defaults()

    def add(self,source:Source)->Source:
        if not source.id:
            raise ValueError("Source id is required")
        self._sources[source.id]=source
        return source

    def get(self,source_id:str)->Optional[Source]:
        return self._sources.get(str(source_id or "").strip())

    def all(self)->List[Source]:
        return list(self._sources.values())

    def list_dicts(self)->List[Dict[str,Any]]:
        return [s.to_dict() for s in self.all()]

    def to_dict(self)->Dict[str,Any]:
        return {"version":VERSION,"sources":self.list_dicts()}

    def verified(self)->List[Source]:
        return [s for s in self.all() if s.verified]

    def official(self)->List[Source]:
        return [s for s in self.all() if s.official]

    def search(self,query:str="",country:str="",airline:str="",destination:str="",source_type:str="")->List[Source]:
        q=self._norm(query)
        c=self._norm(country)
        a=self._norm(airline)
        d=self._norm(destination)
        t=self._norm(source_type)
        out=[]
        for s in self.all():
            hay=self._norm(" ".join([s.id,s.name,s.scope,s.notes,s.airline,s.destination,s.country]))
            if q and q not in hay:
                continue
            if c and c not in self._norm(s.country):
                continue
            if a and a not in self._norm(s.airline):
                continue
            if d and not self._destination_match(s.destination,d):
                continue
            if t and t!=self._norm(s.source_type):
                continue
            out.append(s)
        return out

    def route_sources(self,origin:str="",destination:str="",airline:str="",include_search:bool=True)->List[Source]:
        o=self._norm(origin)
        d=self._norm(destination)
        a=self._norm(airline)
        out=[]
        for s in self.all():
            if s.source_type=="search" and not include_search:
                continue
            if a and self._norm(s.airline) and not self._airline_match(s.airline,a):
                continue
            if o and not self._origin_match(s,o):
                continue
            if d and not self._destination_match(s.destination,d):
                continue
            out.append(s)
        return self._unique(out)

    def baggage_sources(self,origin:str="",destination:str="",airline:str="")->List[Source]:
        a=self._norm(airline)
        out=[]
        for s in self.all():
            if "baggage" not in self._norm(s.scope) and "equipaje" not in self._norm(s.scope):
                continue
            if a and self._norm(s.airline) and not self._airline_match(s.airline,a):
                continue
            if origin and s.country and self._norm(origin) not in self._norm(s.country) and self._norm(s.country) not in self._norm(origin):
                if "united states" in self._norm(origin) and "united states" not in self._norm(s.country):
                    continue
            if destination and s.destination and not self._destination_match(s.destination,self._norm(destination)):
                continue
            out.append(s)
        return self._unique(out)

    def official_for_airline(self,airline:str)->List[Source]:
        a=self._norm(airline)
        if not a:
            return []
        return [s for s in self.all() if s.official and s.airline and self._airline_match(s.airline,a)]

    def source_for_id(self,source_id:str)->Optional[Dict[str,Any]]:
        s=self.get(source_id)
        return s.to_dict() if s else None

    def _airline_match(self,value:str,target:str)->bool:
        v=self._norm(value)
        t=self._norm(target)
        if not v or not t:
            return False
        aliases={
            "american":["american airlines","american"],
            "southwest":["southwest airlines","southwest"],
            "delta":["delta air lines","delta airlines","delta"],
            "cubazul":["cubazul","cuba azul"],
            "xael":["xael"],
        }
        for key,vals in aliases.items():
            if any(x in v for x in vals) and any(x in t for x in vals):
                return True
        return v==t or v in t or t in v

    def _origin_match(self,source:Source,origin:str)->bool:
        if not origin:
            return True
        text=self._norm(origin)
        if not source.country:
            return True
        country=self._norm(source.country)
        if country in text or text in country:
            return True
        aliases=self._origin_aliases(text)
        return any(x in country or country in x for x in aliases)

    def _destination_match(self,destination:str,target:str)->bool:
        if not destination or not target:
            return True
        d=self._norm(destination)
        t=self._norm(target)
        if d in t or t in d:
            return True
        da=self._destination_aliases(d)
        ta=self._destination_aliases(t)
        return bool(set(da)&set(ta))

    def _origin_aliases(self,value:str)->List[str]:
        v=self._norm(value)
        out=[v] if v else []
        if v in {"us","usa","u s","united states","united states of america","estados unidos","eeuu"}:
            out+=["united states","usa","us","estados unidos"]
        if v in {"miami","mia","miami florida","miami fl"}:
            out+=["miami","mia","florida","united states"]
        if v in {"fort lauderdale","fll","fort lauderdale florida","fort lauderdale fl"}:
            out+=["fort lauderdale","fll","florida","united states"]
        return self._unique_strings(out)

    def _destination_aliases(self,value:str)->List[str]:
        v=self._norm(value)
        out=[v] if v else []
        cuba={"cuba","havana","habana","hav","varadero","vra","camaguey","cmw","santiago de cuba","scu"}
        if v in cuba or any(x in v for x in cuba):
            out+=list(cuba)
        if v in {"havana","habana","hav"}:
            out+=["cuba","havana","habana","hav"]
        return self._unique_strings(out)

    def _is_us_origin(self,value:str)->bool:
        return bool(set(self._origin_aliases(value))&{"united states","usa","us","estados unidos","miami","mia","fort lauderdale","fll"})

    def _destination_is_cuba(self,value:str)->bool:
        return bool(set(self._destination_aliases(value))&{"cuba","havana","habana","hav","varadero","vra","camaguey","cmw","santiago de cuba","scu"})

    def _unique(self,items:List[Source])->List[Source]:
        seen=set()
        out=[]
        for item in items:
            if item.id not in seen:
                seen.add(item.id)
                out.append(item)
        return out

    def _unique_strings(self,items:List[str])->List[str]:
        seen=set()
        out=[]
        for item in items:
            n=self._norm(item)
            if n and n not in seen:
                seen.add(n)
                out.append(n)
        return out

    def _norm(self,value:Any)->str:
        return " ".join(str(value or "").strip().lower().replace("_"," ").split())

    def _load_defaults(self):
        self.add(Source("american_airlines","American Airlines","https://www.aa.com/","airline","United States","American Airlines","","Flights and baggage information",True,True,VERIFICATION_DATE,"Official airline website. Confirm conditions for the actual itinerary."))
        self.add(Source("southwest_airlines","Southwest Airlines","https://www.southwest.com/","airline","United States","Southwest Airlines","","Flights and baggage information",True,True,VERIFICATION_DATE,"Official airline website. Confirm conditions for the actual itinerary."))
        self.add(Source("delta_air_lines","Delta Air Lines","https://www.delta.com/","airline","United States","Delta Air Lines","","Flights and baggage information",True,True,VERIFICATION_DATE,"Official airline website. Confirm conditions for the actual itinerary."))
        self.add(Source("cubazul","Cubazul","https://cubazulairlines.com/","airline","United States","Cubazul","Cuba","Airline information",True,True,VERIFICATION_DATE,"Official airline source when available. Confirm current route and conditions directly."))
        self.add(Source("xael","XAEL","https://www.xaelairlines.com/","airline","United States","XAEL","Cuba","Airline information",True,False,"","Source listed for discovery; current conditions require direct confirmation."))
        self.add(Source("google_flights","Google Flights","https://www.google.com/travel/flights","search","","","","Flight search and itinerary discovery",False,False,"","Search/discovery source. It is not the airline and does not replace airline confirmation."))
        self.add(Source("tsa","TSA","https://www.tsa.gov/travel/security-screening/whatcanibring/all","security","United States","","","Airport security and permitted/prohibited items",True,True,VERIFICATION_DATE,"Security screening source for travel from the United States. Destination import rules may differ."))
        self.add(Source("faa_packsafe","FAA PackSafe","https://www.faa.gov/hazmat/packsafe","baggage","United States","","","Hazardous materials and baggage safety",True,True,VERIFICATION_DATE,"FAA guidance for hazardous materials and air transportation."))
        self.add(Source("faa_batteries","FAA Batteries","https://www.faa.gov/hazmat/resources/lithium_batteries","baggage","United States","","","Lithium batteries and battery safety",True,True,VERIFICATION_DATE,"FAA battery guidance. Confirm airline-specific requirements too."))
        self.add(Source("faa_lithium_baggage","FAA Lithium Batteries","https://www.faa.gov/hazmat/packsafe/lithium-batteries","baggage","United States","","","Lithium batteries in baggage",True,True,VERIFICATION_DATE,"FAA guidance for lithium batteries."))
        self.add(Source("dviajeros","D'Viajeros","https://dviajeros.mitrans.gob.cu/","government","Cuba","","Cuba","Cuban traveler information and required travel declaration",True,False,"","Official Cuban government domain; current requirements must be confirmed directly."))
        self.add(Source("evisa_cuba","eVisa Cuba","https://evisacuba.cu/","government","Cuba","","Cuba","Cuban electronic visa information",True,False,"","Official Cuban eVisa source; eligibility and current requirements must be confirmed directly."))

REGISTRY=SourceRegistry()
source_registry=REGISTRY

def get_source(source_id:str)->Optional[Source]:
    return REGISTRY.get(source_id)

def get_sources()->List[Dict[str,Any]]:
    return REGISTRY.list_dicts()

def search_sources(query:str="",**kwargs)->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.search(query,**kwargs)]

def route_sources(origin:str="",destination:str="",airline:str="",include_search:bool=True)->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.route_sources(origin,destination,airline,include_search)]

def baggage_sources(origin:str="",destination:str="",airline:str="")->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.baggage_sources(origin,destination,airline)]

def google_flights_url(origin:str="",destination:str="",departure_date:str="",return_date:str="")->str:
    query=f"{origin or ''} to {destination or ''}".strip()
    if departure_date:
        query+=f" {departure_date}"
    if return_date:
        query+=f" {return_date}"
    return "https://www.google.com/travel/flights?q="+quote_plus(query.strip())
