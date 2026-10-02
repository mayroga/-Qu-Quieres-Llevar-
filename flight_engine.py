# flight_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.1.0
from __future__ import annotations
from typing import Any,Dict,List,Optional
from urllib.parse import quote_plus
from source_registry import REGISTRY,Source,google_flights_url

VERSION="8.1.0"
CHARTER_IDS={"cubazul_air_charter","xael_charters","cuballama_viajes","ibc_airways"}

def _text(v:Any)->str:
    return str(v or "").strip()

def _int(v:Any,default:int=0)->int:
    try:return int(v)
    except:return default

class FlightEngine:
    def __init__(self,registry=REGISTRY):
        self.registry=registry
        self.version=VERSION

    def _source_card(self,s:Any,language:str="es")->Dict[str,Any]:
        if isinstance(s,dict):
            d=dict(s)
        else:
            d={
                "id":getattr(s,"id",""),
                "name":getattr(s,"name",""),
                "url":getattr(s,"url",""),
                "alternate_url":getattr(s,"alternate_url",None),
                "category":getattr(s,"category",""),
                "description":getattr(s,"description",""),
                "official":bool(getattr(s,"official",True)),
                "verified":bool(getattr(s,"verified",True))
            }
        return {
            "id":d.get("id",""),
            "name":d.get("name",""),
            "url":d.get("url",""),
            "alternate_url":d.get("alternate_url"),
            "category":d.get("category",""),
            "description":d.get("description",""),
            "official":bool(d.get("official",True)),
            "verified":bool(d.get("verified",d.get("verified_date",False)))
        }

    def _cards(self,items:Any,language:str="es")->List[Dict[str,Any]]:
        if isinstance(items,dict):
            items=items.get("sources") or items.get("charter_sources") or items.get("official_sources") or []
        if not items:return []
        return [self._source_card(x,language) for x in items]

    def _is_cuba(self,origin:str="",destination:str="")->bool:
        text=f"{origin} {destination}".lower()
        aliases=("cuba","havana","habana","varadero","camaguey","camagüey","santiago","santiago de cuba","holguin","holguín","santa clara")
        return any(x in text for x in aliases)

    def is_cuba_route(self,origin:str="",destination:str="")->bool:
        return self._is_cuba(origin,destination)

    def _ensure_charter_sources(self,items:Any)->List[Any]:
        out=[]
        seen=set()
        for x in items or []:
            i=_text(x.get("id") if isinstance(x,dict) else getattr(x,"id","")).lower()
            if i and i in seen:continue
            if i:seen.add(i)
            out.append(x)
        try:extra=self.registry.get_charter_sources()
        except Exception:extra=[]
        for x in extra or []:
            i=_text(x.get("id") if isinstance(x,dict) else getattr(x,"id","")).lower()
            if i and i in seen:continue
            if i:seen.add(i)
            out.append(x)
        return out

    def charter_sources(self,language:str="es")->List[Dict[str,Any]]:
        try:
            return self._cards(self.registry.get_charter_sources(),language)
        except Exception:
            try:return self._cards(self.registry.charter_sources(),language)
            except Exception:return []

    def official_charter_sources(self,language:str="es")->List[Dict[str,Any]]:
        return self.charter_sources(language)

    def airline_sources(self,airline:str="",language:str="es")->List[Dict[str,Any]]:
        try:return self._cards(self.registry.official_for_airline(airline),language)
        except Exception:return []

    def source_cards(self,origin:str="",destination:str="",airline:str="",language:str="es")->List[Dict[str,Any]]:
        return self.sources_for_route(origin,destination,airline,language).get("sources",[])

    def official_sources(self,airline:str="",origin:str="",destination:str="",language:str="es")->List[Dict[str,Any]]:
        out=self.airline_sources(airline,language) if airline else []
        if self._is_cuba(origin,destination):
            out=self._ensure_charter_sources(out)
            try:
                cuba=self.registry.cuba_sources()
            except Exception:
                try:cuba=self.registry.search("Cuba","cuba",50)
                except Exception:cuba=[]
            out=self._ensure_charter_sources(list(cuba or [])+out)
        return self._cards(out,language)

    def search(self,origin:str="",destination:str="",departure_date:Optional[str]=None,
               return_date:Optional[str]=None,airline:str="",cabin:str="",fare:str="",
               passengers:int=1,stops:Optional[int]=None,language:str="es",**kwargs)->Dict[str,Any]:
        origin=_text(origin)
        destination=_text(destination)
        departure_date=_text(departure_date)
        return_date=_text(return_date)
        airline=_text(airline)
        cabin=_text(cabin)
        fare=_text(fare)
        language=_text(language) or "es"
        passengers=max(1,_int(passengers,1))
        stops=None if stops in ("",None) else max(0,_int(stops,0))
        cuba=self._is_cuba(origin,destination)
        sources=self.official_sources(airline,origin,destination,language)
        charter=self.charter_sources(language) if cuba else []
        airline_cards=self.airline_sources(airline,language) if airline else []
        if not airline_cards and airline:airline_cards=sources
        url=""
        if origin and destination:
            try:url=google_flights_url(origin,destination,departure_date,return_date)
            except Exception:url=f"https://www.google.com/travel/flights?q={quote_plus(origin+' to '+destination)}"
        msg_es="No se muestran vuelos confirmados dentro de ¿QUÉ QUIERES LLEVAR? sin una fuente de disponibilidad verificable."
        msg_en="No confirmed flights are displayed within ¿QUÉ QUIERES LLEVAR? without a verifiable availability source."
        next_es="Abrir una fuente oficial o proveedor de vuelos y verificar directamente fecha, ruta, precio y disponibilidad."
        next_en="Open an official source or flight provider and verify the date, route, price and availability directly."
        return {
            "success":True,
            "version":VERSION,
            "origin":origin,
            "destination":destination,
            "departure_date":departure_date,
            "return_date":return_date,
            "airline":airline,
            "cabin":cabin,
            "fare":fare,
            "passengers":passengers,
            "stops":stops,
            "language":language,
            "is_cuba_route":cuba,
            "confirmed_flights":[],
            "flights":[],
            "results":[],
            "live_results_available":False,
            "message":msg_en if language=="en" else msg_es,
            "next_action":next_en if language=="en" else next_es,
            "google_flights_url":url,
            "sources":sources,
            "charter_sources":charter,
            "airline_sources":airline_cards
        }

    def search_external(self,*args,**kwargs)->Dict[str,Any]:
        return self.search(*args,**kwargs)

    def understand(self,origin:Any="",destination:str="",departure_date:Optional[str]=None,
                   return_date:Optional[str]=None,airline:str="",cabin:str="",fare:str="",
                   passengers:int=1,stops:Optional[int]=None,language:str="es",**kwargs)->Dict[str,Any]:
        if isinstance(origin,dict):
            data=dict(origin)
            language=_text(data.get("language")) or language
            origin=data.get("origin","")
            destination=data.get("destination","")
            departure_date=data.get("departure_date")
            return_date=data.get("return_date")
            airline=data.get("airline","")
            cabin=data.get("cabin","")
            fare=data.get("fare","")
            passengers=data.get("passengers",1)
            stops=data.get("stops")
        data=self.search(origin,destination,departure_date,return_date,airline,cabin,fare,passengers,stops,language)
        data["understood"]={
            "origin":data["origin"],
            "destination":data["destination"],
            "departure_date":data["departure_date"],
            "return_date":data["return_date"],
            "airline":data["airline"],
            "cabin":data["cabin"],
            "fare":data["fare"],
            "passengers":data["passengers"],
            "stops":data["stops"]
        }
        if data["is_cuba_route"]:
            data["next_action"]=(
                "Review official charter flight options and official Cuba entry sources."
                if language=="en" else
                "Revisa las opciones oficiales de vuelos chárter y las fuentes oficiales de entrada a Cuba."
            )
        return data

    def cuba_sources(self,origin:str="",destination:str="Cuba",airline:str="",language:str="es")->Dict[str,Any]:
        charters=self.charter_sources(language)
        try:official=self._cards(self.registry.cuba_sources(),language)
        except Exception:official=[]
        ids={x.get("id") for x in official}
        for x in charters:
            if x.get("id") not in ids:
                official.append(x)
                ids.add(x.get("id"))
        return {
            "success":True,
            "version":VERSION,
            "language":language or "es",
            "origin":origin,
            "destination":destination,
            "sources":official,
            "official_sources":official,
            "charter_sources":charters,
            "is_cuba_route":True
        }

    def sources_for_route(self,origin:str="",destination:str="",airline:str="",language:str="es")->Dict[str,Any]:
        cuba=self._is_cuba(origin,destination)
        sources=self.official_sources(airline,origin,destination,language)
        charters=self.charter_sources(language) if cuba else []
        airline_cards=self.airline_sources(airline,language) if airline else []
        return {
            "success":True,
            "version":VERSION,
            "language":language or "es",
            "origin":origin,
            "destination":destination,
            "is_cuba_route":cuba,
            "sources":sources,
            "charter_sources":charters,
            "airline_sources":airline_cards
        }

engine=FlightEngine()
flight_engine=engine
