# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v9.0.0
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict

class BaseRequest(BaseModel):
    model_config=ConfigDict(extra="ignore")
    session_token:Optional[str]=None
    language:str="es"

class SessionCreate(BaseModel):
    model_config=ConfigDict(extra="ignore")
    language:str="es"

class FlightRequest(BaseRequest):
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    cabin:str=""
    fare:str=""
    passengers:int=Field(default=1,ge=1,le=20)
    stops:int=Field(default=0,ge=0,le=20)

class ItemRequest(BaseRequest):
    item:str=""
    quantity:str="1"
    description:str=""
    baggage_type:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    cabin:str=""
    fare:str=""
    item_airline:str=""
    item_destination:str=""
    item_wh:str=""
    item_volts:str=""
    item_ah:str=""
    item_mah:str=""

class BaggageRequest(BaseRequest):
    baggage_type:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    cabin:str=""
    fare:str=""

class GuideRequest(BaseRequest):
    flight:Dict[str,Any]=Field(default_factory=dict)
    item:Dict[str,Any]=Field(default_factory=dict)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    cuba:Dict[str,Any]=Field(default_factory=dict)

class TeachRequest(BaseRequest):
    term:str=""

class PracticeRequest(BaseRequest):
    practice_type:str="airline"
    mode:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:str=""
    fare:str=""

class CubaRequest(BaseRequest):
    nationality:str=""
    dual_nationality:str=""
    passport_country:str=""
    passport_expiry:str=""
    travel_date:str=""
    purpose:str=""

class SourceRequest(BaseRequest):
    origin:str=""
    destination:str=""
    airline:str=""
    language:str="es"

class LegalResponse(BaseModel):
    short_notice:str=""
    full_notice:str=""
    user_guidance:str=""
    source_notice:str=""

class Source(BaseModel):
    id:Optional[str]=None
    name:str=""
    url:str=""
    description:str=""
    publisher:str=""
    verified:str=""
    type:Optional[str]=None

class SourceResponse(BaseModel):
    sources:List[Source]=Field(default_factory=list)

class StandardResponse(BaseModel):
    title:str=""
    message:str=""
    next_action:str=""
    steps:List[Any]=Field(default_factory=list)
    sources:List[Any]=Field(default_factory=list)
    status:str=""

class FlightResponse(StandardResponse):
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""

class ItemResponse(StandardResponse):
    item:str=""

class PracticeResponse(BaseModel):
    title:str=""
    steps:List[str]=Field(default_factory=list)
    sources:List[Any]=Field(default_factory=list)
    simulation:bool=True
    real_transaction:bool=False

class ConfigResponse(BaseModel):
    app:Dict[str,Any]=Field(default_factory=dict)
    service:Dict[str,Any]=Field(default_factory=dict)
    flow:List[str]=Field(default_factory=list)
    cuba:Dict[str,Any]=Field(default_factory=dict)
    official_sources:List[Any]=Field(default_factory=list)

class SessionResponse(BaseModel):
    active:bool=False
    session_token:Optional[str]=None
    language:str="es"
    session:Optional[Dict[str,Any]]=None

class PaymentResponse(BaseModel):
    checkout_url:Optional[str]=None
    url:Optional[str]=None

class DeleteLocal(BaseModel):
    key:Optional[str]=None

class HealthResponse(BaseModel):
    status:str="ok"
    app:str=""
    version:str=""
    sessions:int=0
