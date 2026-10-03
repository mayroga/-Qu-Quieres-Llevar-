# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v10.0.0
from __future__ import annotations
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict

VERSION="10.0.0"

class BaseRequest(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)

class AccessRequest(BaseRequest):
    username:str=Field(default="",max_length=200)
    password:str=Field(default="",max_length=500)

class CheckoutRequest(BaseRequest):
    success_url:Optional[str]=None
    cancel_url:Optional[str]=None

class FlightRequest(BaseRequest):
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    stops:Any=""
    departure:str=""
    return_date:str=""
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:str="Economy"

class BookingRequest(BaseRequest):
    origin:str=""
    destination:str=""
    departure:str=""
    return_date:str=""
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:str="Economy"
    bags:int=Field(default=0,ge=0,le=20)
    nonstop:Optional[bool]=None

class ConnectionRequest(BaseRequest):
    airport:str=""
    terminal:str=""
    arrival_gate:str=""
    next_flight:str=""
    next_gate:str=""
    next_terminal:str=""
    same_ticket:Optional[bool]=None
    baggage:Optional[bool]=None
    bag_recheck:Optional[bool]=None
    country_change:Optional[bool]=None
    airline:str=""
    destination:str=""

class BaggageRequest(BaseRequest):
    type:str=""
    item:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    weight:Optional[float]=Field(default=None,ge=0)
    dimensions:str=""

class ItemRequest(BaseRequest):
    item:str=""
    airline:str=""
    destination:str=""
    origin:str=""
    baggage_type:str=""
    purpose:str=""

class CubaRequest(BaseRequest):
    origin:str=""
    destination:str="Cuba"
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    flight_type:str=""
    airline:str=""
    flight_number:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False

class CubaEntryRequest(CubaRequest):
    country_of_residence:str=""
    passport_valid_until:str=""
    has_cuban_passport:Optional[bool]=None
    has_other_passport:Optional[bool]=None

class VisaRequest(BaseRequest):
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    surname:str=""
    given_names:str=""
    birth_date:str=""
    sex:str=""
    email:str=""
    phone:str=""
    purpose:str=""
    arrival_date:str=""
    destination:str="Cuba"

class DViajeroRequest(BaseRequest):
    given_names:str=""
    surnames:str=""
    birth_date:str=""
    nationality:str=""
    sex:str=""
    passport_number:str=""
    passport_country:str=""
    arrival_date:str=""
    flight:str=""
    arrival_airport:str=""
    email:str=""
    phone:str=""

class DocumentRequest(BaseRequest):
    origin:str=""
    destination:str=""
    nationality:str=""
    passport_country:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    airline:str=""
    flight_type:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""

class PracticeRequest(BaseRequest):
    scenario:str=""
    item:str=""
    state:str=""
    step:int=Field(default=0,ge=0,le=50)
    data:Dict[str,Any]=Field(default_factory=dict)

class AirportRequest(BaseRequest):
    state:str=""
    airport:str=""
    terminal:str=""
    gate:str=""
    boarding_time:str=""
    flight:str=""
    destination:str=""
    connection:bool=False

class AirlineRequest(BaseRequest):
    name:str=""
    airline:str=""
    origin:str=""
    destination:str=""

class SourceRequest(BaseRequest):
    topic:str="official"
    query:str=""

class SolveRequest(BaseRequest):
    question:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class GuideRequest(BaseRequest):
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    stops:Any=""
    nationality:str=""
    passport_country:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    purpose:str=""
    items:List[str]=Field(default_factory=list)
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    arrival_date:str=""
    departure_date:str=""
    current_state:str=""
    last_item:str=""

class TripState(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    stops:Any=""
    nationality:str=""
    passport_country:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    purpose:str=""
    items:List[str]=Field(default_factory=list)
    arrival_date:str=""
    departure_date:str=""
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    current_state:str=""
    last_item:str=""

class TripExportRequest(BaseRequest):
    data:TripState=Field(default_factory=TripState)

class GenericResponse(BaseModel):
    ok:bool=True
    message:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class SourceResponse(BaseModel):
    ok:bool=True
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    topic:str="official"

class FlightResponse(BaseModel):
    ok:bool=True
    title:str=""
    route:str=""
    segments:List[Dict[str,Any]]=Field(default_factory=list)
    connections:int=0
    has_connection:bool=False
    message:str=""
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class BookingResponse(BaseModel):
    ok:bool=True
    title:str=""
    simulation:bool=True
    real_booking:bool=False
    payment:bool=False
    message:str=""
    search:Dict[str,Any]=Field(default_factory=dict)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class ItemResponse(BaseModel):
    ok:bool=True
    title:str=""
    item:str=""
    category:str=""
    status:str="verify"
    message:str=""
    details:List[str]=Field(default_factory=list)
    authorities:List[str]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class BaggageResponse(BaseModel):
    ok:bool=True
    title:str=""
    message:str=""
    status:str="verify"
    details:List[str]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class CubaResponse(BaseModel):
    ok:bool=True
    title:str=""
    message:str=""
    status:str="verify"
    details:List[str]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class DocumentResponse(BaseModel):
    ok:bool=True
    title:str=""
    message:str=""
    documents:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class PracticeResponse(BaseModel):
    ok:bool=True
    title:str=""
    mode:str="practice"
    official_submission:bool=False
    message:str=""
    next_action:str=""
    completed:List[str]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    progress:int=Field(default=0,ge=0,le=100)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    scenarios:List[Dict[str,Any]]=Field(default_factory=list)

class GuideResponse(BaseModel):
    ok:bool=True
    title:str="Mi guía"
    trip:Dict[str,Any]=Field(default_factory=dict)
    flight:Dict[str,Any]=Field(default_factory=dict)
    documents:Dict[str,Any]=Field(default_factory=dict)
    items_reviewed:List[Dict[str,Any]]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    next_action:str=""
    message:str=""

class AccessResponse(BaseModel):
    ok:bool=True
    authorized:bool=False
    token:Optional[str]=None
    message:str=""

class CheckoutResponse(BaseModel):
    ok:bool=True
    url:Optional[str]=None
    session_id:Optional[str]=None
    message:str=""

class HealthResponse(BaseModel):
    ok:bool=True
    app:str="¿QUÉ QUIERES LLEVAR?"
    version:str=VERSION
    status:str="ready"

class ErrorResponse(BaseModel):
    ok:bool=False
    error:str=""
    message:str=""
    details:Optional[Any]=None

class SimulationStep(BaseModel):
    id:str
    title:str
    fields:List[str]=Field(default_factory=list)
    help:str=""

class SimulationResponse(BaseModel):
    ok:bool=True
    id:str=""
    title:str=""
    notice:str=""
    steps:List[SimulationStep]=Field(default_factory=list)

class AirlineResponse(BaseModel):
    ok:bool=True
    query:str=""
    matches:List[Dict[str,Any]]=Field(default_factory=list)
    message:str=""
    next_action:str=""

__all__=[
"VERSION","BaseRequest","AccessRequest","CheckoutRequest","FlightRequest",
"BookingRequest","ConnectionRequest","BaggageRequest","ItemRequest",
"CubaRequest","CubaEntryRequest","VisaRequest","DViajeroRequest",
"DocumentRequest","PracticeRequest","AirportRequest","AirlineRequest",
"SourceRequest","SolveRequest","GuideRequest","TripState","TripExportRequest",
"GenericResponse","SourceResponse","FlightResponse","BookingResponse",
"ItemResponse","BaggageResponse","CubaResponse","DocumentResponse",
"PracticeResponse","GuideResponse","AccessResponse","CheckoutResponse",
"HealthResponse","ErrorResponse","SimulationStep","SimulationResponse",
"AirlineResponse"
]
