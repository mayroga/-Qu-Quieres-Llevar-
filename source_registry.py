from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Any,Dict,List,Optional
from urllib.parse import quote_plus
VERSION="8.2.0"
VERIFICATION_DATE="2026-10-02"

@dataclass
class Source:
    id:str
    name:str
    url:str
    category:str=""
    description:str=""
    authority_type:str="reference"
    official_for:str=""
    country:str=""
    airline:str=""
    verified:bool=True
    verified_date:Optional[str]=VERIFICATION_DATE
    alternate_url:Optional[str]=None
    def to_dict(self)->Dict[str,Any]:return asdict(self)

class SourceRegistry:
    def __init__(self):
        self.sources:Dict[str,Source]={}
        self._load_defaults()

    def add(self,s:Source):
        if s and s.id:self.sources[s.id]=s
        return s

    def get(self,id:str)->Optional[Source]:return self.sources.get(id)

    def all(self)->List[Source]:return list(self.sources.values())

    def _load_defaults(self):
        items=[
Source("tsa_all","TSA — What Can I Bring?","https://www.tsa.gov/travel/security-screening/whatcanibring/all","security","TSA information about items at the U.S. security checkpoint.","government","U.S. security screening","US"),
Source("tsa_batteries","TSA — Batteries","https://www.tsa.gov/travel/security-screening/whatcanibring/all","security","TSA battery and checkpoint information.","government","U.S. security screening","US"),
Source("tsa_sharp","TSA — Sharp Objects","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=knife&field_item_category_value=All&page=0","security","TSA information for knives and sharp objects.","government","U.S. security screening","US"),
Source("tsa_firearms","TSA — Firearms","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=firearm&field_item_category_value=All&page=0","security","TSA information for firearms and ammunition.","government","U.S. security screening","US"),
Source("tsa_explosives","TSA — Explosives","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=explosive&field_item_category_value=All&page=0","security","TSA information for explosives and prohibited items.","government","U.S. security screening","US"),
Source("tsa_lighters","TSA — Lighters","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=lighter&field_item_category_value=All&page=0","security","TSA information for lighters.","government","U.S. security screening","US"),
Source("tsa_food","TSA — Food","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=food&field_item_category_value=All&page=0","security","TSA information for food at the security checkpoint.","government","U.S. security screening","US"),
Source("tsa_medical","TSA — Medical","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=medicine&field_item_category_value=All&page=0","security","TSA information for medical items and medications.","government","U.S. security screening","US"),
Source("tsa_electronics","TSA — Electronics","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=electronics&field_item_category_value=All&page=0","security","TSA information for electronic devices.","government","U.S. security screening","US"),
Source("tsa_tools","TSA — Tools","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=tools&field_item_category_value=All&page=0","security","TSA information for tools and household items.","government","U.S. security screening","US"),
Source("tsa_vape","TSA — Electronic Smoking Devices","https://www.tsa.gov/travel/security-screening/whatcanibring/all?combine=vape&field_item_category_value=All&page=0","security","TSA information for electronic smoking devices.","government","U.S. security screening","US"),
Source("tsa_alcohol","TSA — Alcoholic Beverages","https://www.tsa.gov/travel/security-screening/whatcanibring/items/alcoholic-beverages","security","TSA information for alcoholic beverages.","government","U.S. security screening","US"),
Source("faa_packsafe","FAA PackSafe","https://www.faa.gov/hazmat/packsafe","hazmat","FAA passenger guidance for hazardous materials and baggage.","government","U.S. aviation hazardous materials","US"),
Source("faa_batteries","FAA — Airline Passengers and Batteries","https://www.faa.gov/hazmat/packsafe/airline-passengers-and-batteries","hazmat","FAA passenger guidance for lithium and other batteries.","government","U.S. aviation hazardous materials","US"),
Source("faa_power_tools","FAA PackSafe — Power Tools","https://www.faa.gov/hazmat/packsafe/power-tools","hazmat","FAA guidance for power tools and their batteries.","government","U.S. aviation hazardous materials","US"),
Source("faa_electronics","FAA PackSafe — Portable Electronic Devices","https://www.faa.gov/hazmat/packsafe/portable-electronic-devices-with-batteries","hazmat","FAA guidance for portable electronic devices containing batteries.","government","U.S. aviation hazardous materials","US"),
Source("faa_vape","FAA PackSafe — Electronic Cigarettes","https://www.faa.gov/hazmat/packsafe/e-cigarettes-vaping","hazmat","FAA guidance for electronic cigarettes and vaping devices.","government","U.S. aviation hazardous materials","US"),
Source("faa_lighters","FAA PackSafe — Lighters","https://www.faa.gov/hazmat/packsafe/lighters","hazmat","FAA guidance for lighters.","government","U.S. aviation hazardous materials","US"),
Source("cbp_travel","CBP — Travel","https://www.cbp.gov/travel","entry","U.S. Customs and Border Protection traveler information.","government","U.S. customs and border entry","US"),
Source("cbp_food","CBP — Bringing Food into the United States","https://www.cbp.gov/travel/clearing-cbp/bringing-food-into-united-states","entry","CBP information concerning food and agricultural products entering the United States.","government","U.S. customs and agriculture","US"),
Source("state_travel","U.S. Department of State — International Travel","https://travel.state.gov/content/travel/en/international-travel.html","entry","U.S. Department of State international travel information.","government","U.S. international travel","US"),
Source("american_airlines","American Airlines","https://www.aa.com/","airline","Official American Airlines website. Use it for the airline's own flight, baggage and travel requirements.","airline","American Airlines","US","American Airlines"),
Source("delta_air_lines","Delta Air Lines","https://www.delta.com/","airline","Official Delta Air Lines website. Use it for Delta's own flight, baggage and travel requirements.","airline","Delta Air Lines","US","Delta Air Lines"),
Source("southwest_airlines","Southwest Airlines","https://www.southwest.com/","airline","Official Southwest Airlines website. Use it for Southwest's own flight, baggage and travel requirements.","airline","Southwest Airlines","US","Southwest Airlines"),
Source("united_airlines","United Airlines","https://www.united.com/","airline","Official United Airlines website. Use it for United's own flight, baggage and travel requirements.","airline","United Airlines","US","United Airlines"),
Source("jetblue","JetBlue","https://www.jetblue.com/","airline","Official JetBlue website. Use it for JetBlue's own flight, baggage and travel requirements.","airline","JetBlue","US","JetBlue"),
Source("spirit_airlines","Spirit Airlines","https://www.spirit.com/","airline","Official Spirit Airlines website. Use it for Spirit's own flight, baggage and travel requirements.","airline","Spirit Airlines","US","Spirit Airlines"),
Source("frontier_airlines","Frontier Airlines","https://www.flyfrontier.com/","airline","Official Frontier Airlines website. Use it for Frontier's own flight, baggage and travel requirements.","airline","Frontier Airlines","US","Frontier Airlines"),
Source("alaska_airlines","Alaska Airlines","https://www.alaskaair.com/","airline","Official Alaska Airlines website. Use it for Alaska Airlines' own flight, baggage and travel requirements.","airline","Alaska Airlines","US","Alaska Airlines"),
Source("hawaiian_airlines","Hawaiian Airlines","https://www.hawaiianairlines.com/","airline","Official Hawaiian Airlines website. Use it for Hawaiian Airlines' own flight, baggage and travel requirements.","airline","Hawaiian Airlines","US","Hawaiian Airlines"),
Source("ibc_airways","IBC Airways","https://ibcairways.com/","charter","Commercial airline/provider source. Confirm directly whether the requested Cuba service exists for the date and route.","commercial_provider","Provider's own service information","US","IBC Airways"),
Source("cubazul_air_charter","Cubazul Air Charter","https://cubazulaircharter.com/","charter","Commercial charter provider. Confirm route, date, price and availability directly.","commercial_provider","Provider's own service information","US","Cubazul Air Charter"),
Source("xael_charters","Xael Charters","https://www.xaelcharter.com/","charter","Commercial charter provider. Confirm route, date, price and availability directly.","commercial_provider","Provider's own service information","US","Xael Charters"),
Source("cuballama_viajes","Cuballama Viajes","https://www.cuballama.com/viajes/vuelos/charters","charter","Commercial travel provider. Confirm route, date, price and availability directly.","commercial_provider","Provider's own service information","US","Cuballama Viajes"),
Source("google_flights","Google Flights","https://www.google.com/travel/flights","search","Flight search service. It is not an airline, government authority or guarantee of availability.","search_engine","Flight search",""),
Source("dviajeros","D’Viajeros","https://dviajeros.mitrans.gob.cu/","cuba","Official Cuban D’Viajeros portal.","government","Cuban travel form","CU"),
Source("evisa_cuba","eVisa Cuba","https://evisacuba.cu/","cuba","Official Cuba eVisa information/application portal.","government","Cuba electronic visa","CU"),
Source("cuba_travel","Cuba — Official Travel Information","https://www.cubaminrex.cu/","cuba","Cuban Ministry of Foreign Affairs source for official information. Confirm the applicable authority for the traveler's case.","government","Cuban foreign affairs","CU")
        ]
        for x in items:self.add(x)

    def _norm(self,v:str)->str:
        s=str(v or "").lower()
        for a,b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ü","u"),("ñ","n")):s=s.replace(a,b)
        return " ".join(s.split())

    def airline_alias(self,airline:str)->str:
        n=self._norm(airline)
        aliases={
"american":"american_airlines","american airlines":"american_airlines","aa":"american_airlines",
"delta":"delta_air_lines","delta airlines":"delta_air_lines","delta air lines":"delta_air_lines",
"southwest":"southwest_airlines","southwest airlines":"southwest_airlines","wn":"southwest_airlines",
"united":"united_airlines","united airlines":"united_airlines","ua":"united_airlines",
"jetblue":"jetblue","jet blue":"jetblue","b6":"jetblue",
"spirit":"spirit_airlines","spirit airlines":"spirit_airlines",
"frontier":"frontier_airlines","frontier airlines":"frontier_airlines",
"alaska":"alaska_airlines","alaska airlines":"alaska_airlines",
"hawaiian":"hawaiian_airlines","hawaiian airlines":"hawaiian_airlines",
"cubazul":"cubazul_air_charter","cubazul air charter":"cubazul_air_charter",
"xael":"xael_charters","xael charters":"xael_charters",
"cuballama":"cuballama_viajes","cuballama viajes":"cuballama_viajes",
"ibc":"ibc_airways","ibc airways":"ibc_airways"
}
        return aliases.get(n,"")

    def destination_alias(self,destination:str)->str:
        n=self._norm(destination)
        aliases={"cuba":"cuba","havana":"havana","habana":"havana","varadero":"varadero","camaguey":"camaguey","camagüey":"camaguey","santiago":"santiago de cuba","santiago de cuba":"santiago de cuba","holguin":"holguin","holguín":"holguin","santa clara":"santa clara"}
        return aliases.get(n,n)

    def is_cuba(self,origin:str="",destination:str="")->bool:
        text=self._norm(f"{origin} {destination}")
        aliases=("cuba","havana","habana","varadero","camaguey","santiago de cuba","holguin","santa clara")
        return any(re.search(rf"\b{re.escape(x)}\b",text) for x in aliases)

    def official_for_airline(self,airline:str="")->List[Source]:
        aid=self.airline_alias(airline)
        return [self.sources[aid]] if aid and aid in self.sources else []

    def get_charter_sources(self)->List[Source]:
        ids=["cubazul_air_charter","xael_charters","cuballama_viajes","ibc_airways"]
        return [self.sources[i] for i in ids if i in self.sources]

    def charter_sources(self)->List[Source]:return self.get_charter_sources()

    def cuba_sources(self)->List[Source]:
        ids=["dviajeros","evisa_cuba","cuba_travel"]
        return [self.sources[i] for i in ids if i in self.sources]

    def official_sources(self)->List[Source]:
        return [x for x in self.all() if x.authority_type=="government" or x.authority_type=="airline"]

    def baggage_sources(self,origin:str="",destination:str="",airline:str="")->List[Source]:
        out=[]
        if airline:out.extend(self.official_for_airline(airline))
        for i in ["tsa_all","tsa_batteries","faa_packsafe","faa_batteries","faa_electronics"]:
            s=self.sources.get(i)
            if s and s not in out:out.append(s)
        return out

    def security_sources(self)->List[Source]:
        ids=["tsa_all","faa_packsafe","faa_batteries"]
        return [self.sources[i] for i in ids if i in self.sources]

    def entry_sources(self,destination:str="")->List[Source]:
        out=[]
        d=self._norm(destination)
        if d in {"us","usa","united states","estados unidos","eeuu"}:
            for i in ["cbp_travel","cbp_food","state_travel"]:
                if i in self.sources:out.append(self.sources[i])
        if "cuba" in d:
            out.extend(self.cuba_sources())
        return out

    def route_sources(self,origin:str="",destination:str="",airline:str="")->List[Source]:
        out=[]
        if airline:out.extend(self.official_for_airline(airline))
        out.extend(self.security_sources())
        d=self._norm(destination)
        if self.is_cuba(origin,destination):
            for s in self.cuba_sources()+self.get_charter_sources():
                if s not in out:out.append(s)
        elif d in {"us","usa","united states","estados unidos","eeuu"}:
            for s in self.entry_sources(destination):
                if s not in out:out.append(s)
        return out

    def search(self,query:str="",country:str="",airline:str="",destination:str="",source_type:str="",authority_type:str="",limit:int=50)->List[Source]:
        q=self._norm(query);c=self._norm(country);a=self._norm(airline);d=self._norm(destination);t=self._norm(source_type);at=self._norm(authority_type);out=[]
        for s in self.all():
            hay=self._norm(f"{s.id} {s.name} {s.description} {s.category} {s.authority_type} {s.official_for} {s.airline} {s.country}")
            if q and q not in hay:continue
            if c and c not in hay:continue
            if a:
                aid=self.airline_alias(a)
                if s.id!=aid and a not in hay:continue
            if d and d not in hay and d not in self._norm(s.description):continue
            if t and t!=self._norm(s.category):continue
            if at and at!=self._norm(s.authority_type):continue
            out.append(s)
            if len(out)>=limit:break
        return out

    def google_flights_url(self,origin:str,destination:str,departure_date:str="",return_date:str="")->str:
        q=f"{origin} to {destination}"
        if departure_date:q+=f" {departure_date}"
        if return_date:q+=f" return {return_date}"
        return f"https://www.google.com/travel/flights?q={quote_plus(q)}"

    def to_dicts(self,items:Optional[List[Source]]=None)->List[Dict[str,Any]]:
        return [x.to_dict() for x in (items if items is not None else self.all())]

REGISTRY=SourceRegistry()

def google_flights_url(origin:str,destination:str,departure_date:str="",return_date:str="")->str:return REGISTRY.google_flights_url(origin,destination,departure_date,return_date)
def get_official_sources()->List[Dict[str,Any]]:return REGISTRY.to_dicts(REGISTRY.official_sources())
def get_charter_sources()->List[Dict[str,Any]]:return REGISTRY.to_dicts(REGISTRY.get_charter_sources())
