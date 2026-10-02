# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.2
from dataclasses import asdict,dataclass
from typing import Any,Dict,List,Optional
from urllib.parse import quote_plus

VERSION="8.0.2"
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
    alternate_url:str=""
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

    def charter_sources(self)->List[Source]:
        return [s for s in self.all() if s.source_type=="charter"]

    def official_charter_sources(self)->List[Source]:
        return [s for s in self.charter_sources() if s.official]

    def search(self,query:str="",country:str="",airline:str="",destination:str="",source_type:str="")->List[Source]:
        q=self._norm(query)
        c=self._norm(country)
        a=self._norm(airline)
        d=self._norm(destination)
        t=self._norm(source_type)
        out=[]
        for s in self.all():
            hay=self._norm(" ".join([s.id,s.name,s.scope,s.notes,s.airline,s.destination,s.country,s.source_type]))
            if q and q not in hay:
                continue
            if c and c not in self._norm(s.country):
                continue
            if a and not self._airline_match(s.airline,a):
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
            if d and s.destination and not self._destination_match(s.destination,d):
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
                if self._is_us_origin(origin) and "united states" not in self._norm(s.country):
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
            "cubazul":["cubazul","cubazul air charter","cuba azul"],
            "xael":["xael","xael charters","xael charter"],
            "cuballama":["cuballama","cuballama viajes"],
            "ibc":["ibc airways","ibc air","ibc"]
        }
        for vals in aliases.values():
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
        if v in {"tampa","tpa","tampa florida","tampa fl"}:
            out+=["tampa","tpa","florida","united states"]
        return self._unique_strings(out)

    def _destination_aliases(self,value:str)->List[str]:
        v=self._norm(value)
        out=[v] if v else []
        cuba={"cuba","havana","habana","hav","varadero","vra","camaguey","cmw","santiago de cuba","scu","holguin","hog","santa clara","snu"}
        if v in cuba or any(x in v for x in cuba):
            out+=list(cuba)
        if v in {"havana","habana","hav"}:
            out+=["cuba","havana","habana","hav"]
        if v in {"varadero","vra"}:
            out+=["cuba","varadero","vra"]
        if v in {"camaguey","cmw"}:
            out+=["cuba","camaguey","cmw"]
        if v in {"santiago de cuba","scu"}:
            out+=["cuba","santiago de cuba","scu"]
        if v in {"holguin","hog"}:
            out+=["cuba","holguin","hog"]
        if v in {"santa clara","snu"}:
            out+=["cuba","santa clara","snu"]
        return self._unique_strings(out)

    def _is_us_origin(self,value:str)->bool:
        return bool(set(self._origin_aliases(value))&{"united states","usa","us","estados unidos","miami","mia","fort lauderdale","fll","tampa","tpa"})

    def _destination_is_cuba(self,value:str)->bool:
        return bool(set(self._destination_aliases(value))&{"cuba","havana","habana","hav","varadero","vra","camaguey","cmw","santiago de cuba","scu","holguin","hog","santa clara","snu"})

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
        self.add(Source(
            "american_airlines",
            "American Airlines",
            "https://www.aa.com/",
            "airline",
            "United States",
            "American Airlines",
            "",
            "Flights and baggage information",
            True,
            True,
            VERIFICATION_DATE,
            "Official airline website. Confirm conditions for the actual itinerary."
        ))
        self.add(Source(
            "southwest_airlines",
            "Southwest Airlines",
            "https://www.southwest.com/",
            "airline",
            "United States",
            "Southwest Airlines",
            "",
            "Flights and baggage information",
            True,
            True,
            VERIFICATION_DATE,
            "Official airline website. Confirm conditions for the actual itinerary."
        ))
        self.add(Source(
            "delta_air_lines",
            "Delta Air Lines",
            "https://www.delta.com/",
            "airline",
            "United States",
            "Delta Air Lines",
            "",
            "Flights and baggage information",
            True,
            True,
            VERIFICATION_DATE,
            "Official airline website. Confirm conditions for the actual itinerary."
        ))

        self.add(Source(
            "cubazul_air_charter",
            "Cubazul Air Charter",
            "https://cubazulaircharter.com/",
            "charter",
            "United States",
            "Cubazul Air Charter",
            "Cuba",
            "Official charter flight booking and travel services",
            True,
            True,
            VERIFICATION_DATE,
            "Official Cubazul Air Charter website. The site provides flight search and reservation functions. Confirm current routes, dates, availability, baggage and ticket conditions directly.",
            ""
        ))

        self.add(Source(
            "xael_charters",
            "Xael Charters",
            "https://www.xaelcharter.com/",
            "charter",
            "United States",
            "Xael Charters",
            "Cuba",
            "Official charter flight and travel services",
            True,
            True,
            VERIFICATION_DATE,
            "Official Xael Charters website. The site currently provides flight-to-Cuba information and booking access. Confirm current routes, dates, availability, baggage and ticket conditions directly.",
            ""
        ))

        self.add(Source(
            "cuballama_viajes",
            "Cuballama Viajes",
            "https://www.cuballama.com/viajes/vuelos/charters",
            "charter",
            "United States",
            "Cuballama Viajes",
            "Cuba",
            "Official charter flight booking and travel services",
            True,
            True,
            VERIFICATION_DATE,
            "Official Cuballama Viajes charter section. The site currently lists charter flights to Cuba and provides online/contact booking options. Confirm current routes, dates, availability, baggage and ticket conditions directly.",
            "https://www.cuballama.com/viajes/"
        ))

        self.add(Source(
            "ibc_airways",
            "IBC Airways",
            "https://ibcairways.com/",
            "charter",
            "United States",
            "IBC Airways",
            "Caribbean",
            "Official passenger, cargo and charter airline services",
            True,
            True,
            VERIFICATION_DATE,
            "Official IBC Airways website. IBC identifies itself as a Part 135 airline based in Miami providing passenger and cargo services in the Caribbean. Do not assume a Cuba route or ticket availability; confirm directly with IBC.",
            "https://flyibc.com/"
        ))

        self.add(Source(
            "google_flights",
            "Google Flights",
            "https://www.google.com/travel/flights",
            "search",
            "",
            "",
            "",
            "Flight search and itinerary discovery",
            False,
            True,
            VERIFICATION_DATE,
            "Search and discovery source. It is not the airline or charter operator and does not replace direct provider confirmation."
        ))

        self.add(Source(
            "tsa",
            "TSA",
            "https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            "security",
            "United States",
            "",
            "",
            "Airport security and permitted or prohibited items",
            True,
            True,
            VERIFICATION_DATE,
            "Security screening source for travel from the United States. Destination import rules may differ."
        ))

        self.add(Source(
            "faa_packsafe",
            "FAA PackSafe",
            "https://www.faa.gov/hazmat/packsafe",
            "baggage",
            "United States",
            "",
            "",
            "Hazardous materials and baggage safety",
            True,
            True,
            VERIFICATION_DATE,
            "FAA guidance for hazardous materials and air transportation."
        ))

        self.add(Source(
            "faa_batteries",
            "FAA Batteries",
            "https://www.faa.gov/hazmat/resources/lithium_batteries",
            "baggage",
            "United States",
            "",
            "",
            "Lithium batteries and battery safety",
            True,
            True,
            VERIFICATION_DATE,
            "FAA battery guidance. Confirm airline or charter-specific requirements too."
        ))

        self.add(Source(
            "faa_lithium_baggage",
            "FAA Lithium Batteries",
            "https://www.faa.gov/hazmat/packsafe/lithium-batteries",
            "baggage",
            "United States",
            "",
            "",
            "Lithium batteries in baggage",
            True,
            True,
            VERIFICATION_DATE,
            "FAA guidance for lithium batteries."
        ))

        self.add(Source(
            "dviajeros",
            "D'Viajeros",
            "https://dviajeros.mitrans.gob.cu/",
            "government",
            "Cuba",
            "",
            "Cuba",
            "Cuban traveler information and required travel declaration",
            True,
            False,
            "",
            "Official Cuban government domain; current requirements must be confirmed directly."
        ))

        self.add(Source(
            "evisa_cuba",
            "eVisa Cuba",
            "https://evisacuba.cu/",
            "government",
            "Cuba",
            "",
            "Cuba",
            "Cuban electronic visa information",
            True,
            False,
            "",
            "Official Cuban eVisa source; eligibility and current requirements must be confirmed directly."
        ))

REGISTRY=SourceRegistry()
source_registry=REGISTRY

def get_source(source_id:str)->Optional[Source]:
    return REGISTRY.get(source_id)

def get_sources()->List[Dict[str,Any]]:
    return REGISTRY.list_dicts()

def get_charter_sources()->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.official_charter_sources()]

def search_sources(query:str="",**kwargs)->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.search(query,**kwargs)]

def route_sources(origin:str="",destination:str="",airline:str="",include_search:bool=True)->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.route_sources(origin,destination,airline,include_search)]

def baggage_sources(origin:str="",destination:str="",airline:str="")->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.baggage_sources(origin,destination,airline)]

def official_for_airline(airline:str)->List[Dict[str,Any]]:
    return [s.to_dict() for s in REGISTRY.official_for_airline(airline)]

def google_flights_url(origin:str="",destination:str="",departure_date:str="",return_date:str="")->str:
    query=f"{origin or ''} to {destination or ''}".strip()
    if departure_date:
        query+=f" {departure_date}"
    if return_date:
        query+=f" {return_date}"
    return "https://www.google.com/travel/flights?q="+quote_plus(query.strip())
