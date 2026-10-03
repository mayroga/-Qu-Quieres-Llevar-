# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field

class AccessRequest(BaseModel):
    username:str
    password:str

class FlightRequest(BaseModel):
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    connection:str=""
    language:str="es"

class ItemRequest(BaseModel):
    item:str=Field(default="",max_length=300)
    language:str="es"

class CubaRequest(BaseModel):
    nationality:str=""
    cuban_nationality:bool=False
    passport:str=""
    arrival_by:str=""
    topic:str="general"
    language:str="es"

class PracticeRequest(BaseModel):
    topic:str="general"
    step:int=1
    answer:Optional[str]=None
    language:str="es"

class GuideRequest(BaseModel):
    language:str="es"
    flight:Dict[str,Any]={}
    baggage:Dict[str,Any]={}
    items:List[Dict[str,Any]]=[]
    documents:List[Dict[str,Any]]=[]
    cuba:Dict[str,Any]={}
