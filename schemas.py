# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict,AliasChoices

VERSION="12.1.0"

class BaseRequest(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)

class FlightRequest(BaseRequest):
    origin:str=""
    destination:str=""
    departure_date:Optional[str]=Field(default="",validation_alias=AliasChoices("departure_date","date"))
    airline:str=""
    passengers:int=1
    language:str="es"
    query:str=""

class BookingRequest(BaseRequest):
    airline:str=""
    origin:str=""
    destination:str=""
    departure_date:Optional[str]=""
    passengers:int=1
    language:str="es"
    step:int=1
    scenario:str="booking"
    simulation_id:str=""

class ConnectionRequest(BaseRequest):
    origin:str=""
    connection:str=""
    destination:str=""
    airline:str=""
    language:str="es"

class BaggageRequest(BaseRequest):
    airline:str=""
    origin:str=""
    destination:str=""
    baggage_type:str=""
    weight:Optional[float]=None
    pieces:int=1
    item:str=""
    language:str="es"

class ItemRequest(BaseRequest):
    item:str=Field(default="",validation_alias=AliasChoices("item","item_name","name"))
    quantity:int=1
    description:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    language:str="es"

class CubaRequest(BaseRequest):
    nationality:str=""
    passport_country:str=""
    purpose:str=""
    purpose_of_trip:str=""
    travel_purpose:str=""
    entry_type:str="air"
    has_passport:bool=False
    passport_valid:bool=False
    dual_citizen:bool=False
    dual_nationality:bool=False
    cuban_nationality:bool=False
    airline:str=""
    origin:str=""
    destination:str="Cuba"
    language:str="es"

class CubaEntryRequest(BaseRequest):
    nationality:str=""
    passport_country:str=""
    given_names:str=""
    surnames:str=""
    birth_date:str=""
    date_of_birth:str=""
    arrival_date:str=""
    airline:str=""
    accommodation:str=""
    purpose_of_trip:str=""
    language:str="es"

class VisaRequest(CubaRequest):
    pass

class DViajeroRequest(CubaEntryRequest):
    pass

class DocumentRequest(BaseRequest):
    document_type:str=""
    country:str=""
    nationality:str=""
    language:str="es"

class PracticeRequest(BaseRequest):
    scenario:str="airline_booking"
    item:str=""
    state:Dict[str,Any]={}
    step:int=1
    answer:Any=None
    data:Dict[str,Any]={}
    airline:str=""
    charter_operator:str=""
    simulation_id:str=""
    language:str="es"

class AirportRequest(BaseRequest):
    airport:str=""
    origin:str=""
    destination:str=""
    airline:str=""
    language:str="es"

class AirlineRequest(BaseRequest):
    airline:str=""
    origin:str=""
    destination:str=""
    language:str="es"

class CharterRequest(BaseRequest):
    charter_operator:str=""
    origin:str=""
    destination:str=""
    language:str="es"

class SourceRequest(BaseRequest):
    topic:str="official"
    query:str=""
    language:str="es"

class SolveRequest(BaseRequest):
    question:str=""
    data:Dict[str,Any]={}
    language:str="es"

class GuideRequest(BaseRequest):
    origin:str=""
    destination:str=""
    airline:str=""
    departure_date:Optional[str]=""
    passengers:int=1
    baggage:Dict[str,Any]={}
    item:Dict[str,Any]={}
    cuba:Dict[str,Any]={}
    language:str="es"

class TripState(BaseModel):
    model_config=ConfigDict(extra="allow")
    origin:str=""
    destination:str=""
    airline:str=""
    departure_date:Optional[str]=""
    passengers:int=1
    baggage:Dict[str,Any]={}
    item:Dict[str,Any]={}
    cuba:Dict[str,Any]={}
    completed_steps:List[str]=[]

class TripExportRequest(BaseRequest):
    state:Dict[str,Any]={}
    language:str="es"
    format:str="pdf"

class GenericResponse(BaseModel):
    success:bool=True
    message:str=""
    data:Dict[str,Any]={}

class SourceResponse(BaseModel):
    success:bool=True
    sources:List[Dict[str,Any]]=[]
    next_action:str=""
    message:str=""

class FlightResponse(BaseModel):
    success:bool=True
    flight:Dict[str,Any]={}
    sources:List[Dict[str,Any]]=[]
    next_action:str=""
    official_url:str=""
    notice:str=""

class BookingResponse(BaseModel):
    success:bool=True
    simulation:bool=True
    real_booking:bool=False
    payment:bool=False
    notice:str=""
    search:Dict[str,Any]={}
    fields:List[Dict[str,Any]]=[]
    steps:List[Dict[str,Any]]=[]
    next_action:str=""
    sources:List[Dict[str,Any]]=[]
    official_url:str=""
    completed:bool=False
    progress:int=0

class ItemResponse(BaseModel):
    success:bool=True
    item:str=""
    status:str="verify"
    result:str=""
    explanation:str=""
    warnings:List[str]=[]
    sources:List[Dict[str,Any]]=[]
    official_url:str=""
    next_action:str=""

class BaggageResponse(BaseModel):
    success:bool=True
    airline:str=""
    status:str="verify"
    baggage:Dict[str,Any]={}
    explanation:str=""
    warnings:List[str]=[]
    sources:List[Dict[str,Any]]=[]
    official_url:str=""
    next_action:str=""

class CubaResponse(BaseModel):
    success:bool=True
    status:str="review"
    result:Dict[str,Any]={}
    notice:str=""
    official_url:str=""
    sources:List[Dict[str,Any]]=[]
    next_action:str=""

class DocumentResponse(BaseModel):
    success:bool=True
    document:str=""
    status:str="review"
    result:Dict[str,Any]={}
    official_url:str=""
    next_action:str=""

class PracticeResponse(BaseModel):
    success:bool=True
    mode:str="airline_booking"
    official_submission:bool=False
    notice:str=""
    completed:bool=False
    pending:List[str]=[]
    progress:int=0
    sources:List[Dict[str,Any]]=[]
    scenarios:List[Dict[str,Any]]=[]
    current_step:Dict[str,Any]={}
    official_url:str=""
    simulation_id:str=""
    ai_assisted:bool=False

class GuideResponse(BaseModel):
    success:bool=True
    guide:Dict[str,Any]={}
    steps:List[Dict[str,Any]]=[]
    completed_steps:List[str]=[]
    next_action:str=""
    sources:List[Dict[str,Any]]=[]
    official_urls:List[str]=[]

class AccessResponse(BaseModel):
    success:bool=True
    active:bool=False
    token:str=""
    expires_at:Optional[float]=None
    message:str=""

class CheckoutResponse(BaseModel):
    success:bool=True
    checkout_url:str=""
    session_id:str=""
    publishable_key:str=""
    price:float=15.99
    currency:str="USD"
    period:str="1_month"

class HealthResponse(BaseModel):
    status:str="ok"
    app:str=""
    version:str=VERSION
    brain_loaded:bool=False
    stripe_configured:bool=False

class ErrorResponse(BaseModel):
    success:bool=False
    error:str=""
    message:str=""

class SimulationStep(BaseModel):
    step:int
    id:str=""
    title:str=""
    description:str=""
    instruction:str=""
    completed:bool=False
    answer:Any=None
    next_action:str=""

class SimulationResponse(BaseModel):
    success:bool=True
    simulation:bool=True
    official_submission:bool=False
    mode:str=""
    simulation_id:str=""
    current_step:int=1
    total_steps:int=0
    progress:int=0
    completed:bool=False
    notice:str=""
    steps:List[SimulationStep]=[]
    official_url:str=""
    next_action:str=""

class AirlineResponse(BaseModel):
    success:bool=True
    airline:Dict[str,Any]={}
    sources:List[Dict[str,Any]]=[]
    official_url:str=""
    next_action:str=""

class CharterResponse(BaseModel):
    success:bool=True
    charter:Dict[str,Any]={}
    sources:List[Dict[str,Any]]=[]
    official_url:str=""
    baggage:Dict[str,Any]={}
    next_action:str=""

class PDFRequest(BaseRequest):
    state:Dict[str,Any]={}
    language:str="es"
    include_flight:bool=True
    include_booking:bool=True
    include_visa:bool=True
    include_dviajeros:bool=True
    include_baggage:bool=True

__all__=[k for k in globals() if not k.startswith("_")]
