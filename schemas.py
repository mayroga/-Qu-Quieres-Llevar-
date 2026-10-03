# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict,AliasChoices

VERSION="12.1.0"

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
    return_:str=Field(default="",validation_alias=AliasChoices("return","return_","return_date"))
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:str="Economy"
    fare:str=""
    ticket_type:str=""
    same_ticket:Optional[bool]=None
    checked_bags:int=Field(default=0,ge=0,le=20)
    carry_on:Optional[bool]=None

class BookingRequest(BaseRequest):
    origin:str=""
    destination:str=""
    departure:str=""
    return_date:str=""
    return_:str=Field(default="",validation_alias=AliasChoices("return","return_","return_date"))
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:str="Economy"
    fare:str=""
    bags:int=Field(default=0,ge=0,le=20)
    nonstop:Optional[bool]=None
    flight_type:str=""
    airline:str=""

class ConnectionRequest(BaseRequest):
    origin:str=""
    destination:str=""
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
    next_airline:str=""
    connection_minutes:Optional[int]=Field(default=None,ge=0,le=10000)

class BaggageRequest(BaseRequest):
    type:str=""
    item:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    flight_number:str=""
    flight_type:str=""
    fare:str=""
    cabin:str=""
    weight:Optional[float]=Field(default=None,ge=0,le=1000)
    dimensions:str=""
    pieces:Optional[int]=Field(default=None,ge=0,le=50)
    personal_item:Optional[bool]=None
    carry_on:Optional[bool]=None
    checked:Optional[bool]=None
    international:Optional[bool]=None
    country_of_departure:str=""
    country_of_destination:str=""

class ItemRequest(BaseRequest):
    item:str=""
    description:str=""
    airline:str=""
    destination:str=""
    origin:str=""
    baggage_type:str=""
    purpose:str=""
    quantity:Optional[int]=Field(default=None,ge=0,le=1000)
    weight:Optional[float]=Field(default=None,ge=0,le=1000)
    size:str=""
    contains_battery:Optional[bool]=None
    contains_liquid:Optional[bool]=None
    contains_food:Optional[bool]=None
    is_medication:Optional[bool]=None
    is_animal:Optional[bool]=None
    is_electronic:Optional[bool]=None

class CubaRequest(BaseRequest):
    origin:str=""
    destination:str="Cuba"
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    country_of_residence:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    flight_type:str=""
    airline:str=""
    flight_number:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    passport_valid_until:str=""
    has_cuban_passport:Optional[bool]=None
    has_other_passport:Optional[bool]=None
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    baggage_checked:bool=False
    documents_checked:bool=False

class CubaEntryRequest(CubaRequest):
    entry_airport:str=""
    residence_country:str=""
    return_ticket:Optional[bool]=None
    travel_insurance:Optional[bool]=None

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
    departure_date:str=""
    destination:str="Cuba"
    country_of_residence:str=""

class DViajeroRequest(BaseRequest):
    given_names:str=""
    surnames:str=""
    birth_date:str=""
    nationality:str=""
    sex:str=""
    passport_number:str=""
    passport_country:str=""
    country_of_residence:str=""
    arrival_date:str=""
    departure_date:str=""
    flight:str=""
    arrival_airport:str=""
    departure_airport:str=""
    email:str=""
    phone:str=""
    address_destination:str=""

class DocumentRequest(BaseRequest):
    origin:str=""
    destination:str=""
    nationality:str=""
    passport_country:str=""
    country_of_residence:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    airline:str=""
    flight_type:str=""
    flight_number:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    passport_valid_until:str=""

class PracticeRequest(BaseRequest):
    scenario:str=""
    item:str=""
    state:str=""
    step:int=Field(default=0,ge=0,le=100)
    answer:str=""
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
    arrival_time:str=""
    next_flight:str=""

class AirlineRequest(BaseRequest):
    name:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    country:str=""
    topic:str=""

class SourceRequest(BaseRequest):
    topic:str="official"
    query:str=""
    country:str=""
    airline:str=""

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
    country_of_residence:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    purpose:str=""
    items:List[str]=Field(default_factory=list)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    documents_checked:bool=False
    baggage_checked:bool=False
    arrival_date:str=""
    departure_date:str=""
    current_state:str=""
    last_item:str=""
    next_action:str=""

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
    country_of_residence:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    purpose:str=""
    items:List[str]=Field(default_factory=list)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    arrival_date:str=""
    departure_date:str=""
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    documents_checked:bool=False
    baggage_checked:bool=False
    current_state:str=""
    last_item:str=""
    next_action:str=""

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
    details:List[str]=Field(default_factory=list)
    questions:List[str]=Field(default_factory=list)
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
    fields:List[Dict[str,Any]]=Field(default_factory=list)
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class ItemResponse(BaseModel):
    ok:bool=True
    title:str=""
    item:str=""
    category:str=""
    status:str="verify"
    status_label:str=""
    placement:str=""
    message:str=""
    details:List[str]=Field(default_factory=list)
    authorities:List[str]=Field(default_factory=list)
    missing_information:List[str]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class BaggageResponse(BaseModel):
    ok:bool=True
    title:str=""
    message:str=""
    status:str="verify"
    status_label:str=""
    baggage_type:str=""
    human_explanation:str=""
    placement:str=""
    details:List[str]=Field(default_factory=list)
    questions:List[str]=Field(default_factory=list)
    authorities:List[str]=Field(default_factory=list)
    missing_information:List[str]=Field(default_factory=list)
    pieces:Optional[int]=None
    weight:Optional[float]=None
    dimensions:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class CubaResponse(BaseModel):
    ok:bool=True
    title:str=""
    message:str=""
    status:str="verify"
    traveler_profile:str=""
    details:List[str]=Field(default_factory=list)
    checklist:List[Dict[str,Any]]=Field(default_factory=list)
    questions:List[str]=Field(default_factory=list)
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
    notice:str="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
    message:str=""
    next_action:str=""
    completed:List[str]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    progress:int=Field(default=0,ge=0,le=100)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    scenarios:List[Dict[str,Any]]=Field(default_factory=list)
    current_step:Optional[Dict[str,Any]]=None

class GuideResponse(BaseModel):
    ok:bool=True
    title:str="Mi guía"
    trip:Dict[str,Any]=Field(default_factory=dict)
    flight:Dict[str,Any]=Field(default_factory=dict)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    documents:Dict[str,Any]=Field(default_factory=dict)
    items_reviewed:List[Dict[str,Any]]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    completed:List[str]=Field(default_factory=list)
    next_action:str=""
    message:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

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
    why:str=""
    example:Optional[str]=None
    options:List[str]=Field(default_factory=list)
    required:bool=True

class SimulationResponse(BaseModel):
    ok:bool=True
    id:str=""
    title:str=""
    notice:str="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
    purpose:str=""
    steps:List[SimulationStep]=Field(default_factory=list)
    official_url:Optional[str]=None

class AirlineResponse(BaseModel):
    ok:bool=True
    query:str=""
    matches:List[Dict[str,Any]]=Field(default_factory=list)
    message:str=""
    next_action:str=""

class PDFRequest(BaseRequest):
    trip:Dict[str,Any]=Field(default_factory=dict)
    flight:Dict[str,Any]=Field(default_factory=dict)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    items:List[Dict[str,Any]]=Field(default_factory=list)
    documents:List[Dict[str,Any]]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    completed:List[str]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

__all__=[k for k in globals() if not k.startswith("_")]
