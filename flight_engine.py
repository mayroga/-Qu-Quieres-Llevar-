# flight_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.2
from __future__ import annotations
from datetime import date
from typing import Any,Dict,List,Optional
from urllib.parse import quote_plus
from source_registry import REGISTRY,Source,google_flights_url

VERSION="8.0.2"
CHARTER_IDS={"cubazul_air_charter","xael_charters","cuballama_viajes","ibc_airways"}

def _text(v:Any)->str:
    return str(v or "").strip()

def _int(v:Any,default:int=0)->int:
    try:return int(v)
    except:return default

def _bool(v:Any)->bool:
    if isinstance(v,bool):return v
    return _text(v).lower() in {"1","true","yes","si","sí"}

class FlightEngine:
    def __init__(self,registry=REGISTRY):
        self.registry=registry
        self.version=VERSION

    def _source_card(self,s:Any)->Dict[str,Any]:
        if isinstance(s,dict):
            return {
                "id":s.get("id",""),
                "name":s.get("name",""),
                "url":s.get("url",""),
                "alternate_url":s.get("alternate_url"),
                "category":s.get("category",""),
                "description":s.get("description",""),
                "official":bool(s.get("official",True))
            }
        return {
            "id":getattr(s,"id",""),
            "name":getattr(s,"name",""),
            "url":getattr(s,"url",""),
            "alternate_url":getattr(s,"alternate_url",None),
            "category":getattr(s,"category",""),
            "description":getattr(s,"description",""),
            "official":bool(getattr(s,"official",True))
        }

    def _cards(self,items:Any)->List[Dict[str,Any]]:
        if not items:return []
        return [self._source_card(x) for x in items]

    def _is_cuba(self,origin:str,destination:str)->bool:
        a=f"{origin} {destination}".lower()
        aliases=("cuba","havana","habana","varadero","camaguey","camagüey","santiago","holguin","holguín","santa clara")
        return any(x in a for x in aliases)

    def _ensure_charter_sources(self,items:List[Any])->List[Any]:
        seen=set()
        out=[]
        for x in items or []:
            i=_text(getattr(x,"id",None) if not isinstance(x,dict) else x.get("id")).lower()
            if i:
                seen.add(i)
            out.append(x)
        try:
            extra=self.registry.get_charter_sources()
        except Exception:
            extra=[]
        for x in extra or []:
            i=_text(getattr(x,"id",None) if not isinstance(x,dict) else x.get("id")).lower()
            if i and i not in seen:
                out.append(x)
                seen.add(i)
        return out

    def charter_sources(self)->List[Dict[str,Any]]:
        try:
            return self._cards(self.registry.get_charter_sources())
        except Exception:
            try:return self._cards(self.registry.charter_sources())
            except Exception:return []

    def official_charter_sources(self)->List[Dict[str,Any]]:
        return self.charter_sources()

    def airline_sources(self,airline:str="")->List[Dict[str,Any]]:
        try:return self._cards(self.registry.official_for_airline(airline))
        except Exception:return []

    def official_sources(self,airline:str="",origin:str="",destination:str="")->List[Dict[str,Any]]:
        out=[]
        try:
            out=self.airline_sources(airline)
        except Exception:
            out=[]
        if self._is_cuba(origin,destination):
            out=self._ensure_charter_sources(out)
            try:
                cuba=self.registry.search(destination or "Cuba")
                out=self._ensure_charter_sources(list(cuba or [])+out)
            except Exception:
                pass
            ids={x.get("id") for x in out}
            for x in self.charter_sources():
                if x.get("id") not in ids:
                    out.append(x)
        return out

    def search(self,origin:str="",destination:str="",departure_date:Optional[str]=None,
               return_date:Optional[str]=None,airline:str="",cabin:str="",fare:str="",
               passengers:int=1,stops:Optional[int]=None,language:str="es")->Dict[str,Any]:
        origin=_text(origin)
        destination=_text(destination)
        departure_date=_text(departure_date)
        return_date=_text(return_date)
        airline=_text(airline)
        cabin=_text(cabin)
        fare=_text(fare)
        language=_text(language) or "es"
        passengers=max(1,_int(passengers,1))
        if stops is not None:stops=max(0,_int(stops,0))
        cuba=self._is_cuba(origin,destination)
        sources=self.official_sources(airline,origin,destination)
        charter=self.charter_sources() if cuba else []
        airline_cards=self.airline_sources(airline) if airline else []
        if not airline_cards and airline:
            airline_cards=sources
        url=""
        if origin and destination and departure_date:
            try:url=google_flights_url(origin,destination,departure_date,return_date or "")
            except Exception:url=f"https://www.google.com/travel/flights?q={quote_plus(origin+' to '+destination)}"
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
            "message":"No se muestran vuelos confirmados dentro de REMESAS/May Roga sin una fuente de disponibilidad verificable.",
            "next_action":"Abrir una fuente oficial o proveedor de vuelos y verificar directamente fecha, ruta, precio y disponibilidad.",
            "google_flights_url":url,
            "sources":sources,
            "charter_sources":charter,
            "airline_sources":airline_cards
        }

    def search_external(self,*args,**kwargs)->Dict[str,Any]:
        return self.search(*args,**kwargs)

    def understand(self,origin:str="",destination:str="",departure_date:Optional[str]=None,
                   return_date:Optional[str]=None,airline:str="",cabin:str="",fare:str="",
                   passengers:int=1,stops:Optional[int]=None,language:str="es",**kwargs)->Dict[str,Any]:
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
        data["next_action"]=(
            "Revisa las opciones oficiales de vuelo chárter y las fuentes oficiales de entrada a Cuba."
            if data["is_cuba_route"] else
            "Revisa la fuente oficial de la aerolínea o buscador de vuelos correspondiente."
        )
        return data

    def cuba_sources(self,language:str="es")->Dict[str,Any]:
        charters=self.charter_sources()
        official=[]
        try:official=self._cards(self.registry.search("Cuba"))
        except Exception:official=[]
        ids={x.get("id") for x in official}
        for x in charters:
            if x.get("id") not in ids:official.append(x)
        return {
            "success":True,
            "version":VERSION,
            "language":language or "es",
            "sources":official,
            "charter_sources":charters,
            "is_cuba_route":True
        }

    def sources_for_route(self,origin:str="",destination:str="",airline:str="",language:str="es")->Dict[str,Any]:
        cuba=self._is_cuba(origin,destination)
        return {
            "success":True,
            "version":VERSION,
            "language":language or "es",
            "origin":origin,
            "destination":destination,
            "is_cuba_route":cuba,
            "sources":self.official_sources(airline,origin,destination),
            "charter_sources":self.charter_sources() if cuba else [],
            "airline_sources":self.airline_sources(airline) if airline else []
        }

engine=FlightEngine()
flight_engine=engine
