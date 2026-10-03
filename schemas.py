# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
from typing import Any,Dict,List,Literal,Optional
from pydantic import BaseModel,ConfigDict,Field

VERSION="12.1.0"
Language=Literal["es","en"]

class BaseRequest(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)

class FlightRequest(BaseRequest):
    language:Language="es"
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:str=""
    fare:str=""
    flight_number:str=""
    natural_query:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class BookingRequest(BaseRequest):
    language:Language="es"
    airline:str=""
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:str=""
    fare:str=""
    passenger:Dict[str,Any]=Field(default_factory=dict)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    step:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class ConnectionRequest(BaseRequest):
    language:Language="es"
    origin:str=""
    destination:str=""
    connection:str=""
    connection_airport:str=""
    flight_number:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class BaggageRequest(BaseRequest):
    language:Language="es"
    airline:str=""
    route:str=""
    cabin:str=""
    fare:str=""
    personal_item:Dict[str,Any]=Field(default_factory=dict)
    carry_on:Dict[str,Any]=Field(default_factory=dict)
    checked_baggage:Dict[str,Any]=Field(default_factory=dict)
    special_items:List[Dict[str,Any]]=Field(default_factory=list)
    data:Dict[str,Any]=Field(default_factory=dict)

class ItemRequest(BaseRequest):
    language:Language="es"
    item:str=""
    item_name:str=""
    quantity:int=Field(default=1,ge=1)
    description:str=""
    airline:str=""
    destination:str=""
    baggage_type:str=""
    route:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class CubaRequest(BaseRequest):
    language:Language="es"
    nationality:str=""
    country_of_residence:str=""
    passport_country:str=""
    travel_purpose:str=""
    entry_type:str=""
    airline:str=""
    charter_operator:str=""
    arrival_date:str=""
    departure_date:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class CubaEntryRequest(CubaRequest):
    first_name:str=""
    last_name:str=""
    date_of_birth:str=""
    passport_number:str=""
    passport_valid:bool=False
    dual_nationality:bool=False
    accommodation:str=""
    address_in_cuba:str=""

class VisaRequest(BaseRequest):
    language:Language="es"
    nationality:str=""
    country_of_residence:str=""
    passport_country:str=""
    passport_number:str=""
    travel_purpose:str=""
    entry_type:str=""
    has_passport:bool=False
    passport_valid:bool=False
    email:str=""
    dual_nationality:bool=False
    arrival_date:str=""
    departure_date:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class DViajeroRequest(BaseRequest):
    language:Language="es"
    first_name:str=""
    last_name:str=""
    nationality:str=""
    date_of_birth:str=""
    passport_number:str=""
    passport_country:str=""
    arrival_date:str=""
    flight_number:str=""
    airline:str=""
    accommodation:str=""
    address_in_cuba:str=""
    purpose_of_trip:str=""
    health_information:Dict[str,Any]=Field(default_factory=dict)
    customs_information:Dict[str,Any]=Field(default_factory=dict)
    data:Dict[str,Any]=Field(default_factory=dict)

class DocumentRequest(BaseRequest):
    language:Language="es"
    document_type:str=""
    nationality:str=""
    destination:str=""
    purpose:str=""
    expiration_date:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class PracticeRequest(BaseRequest):
    language:Language="es"
    scenario:str=""
    item:str=""
    state:str=""
    step:str=""
    answer:str=""
    data:Dict[str,Any]=Field(default_factory=dict)
    airline:str=""
    charter_operator:str=""
    simulation_id:str=""

class AirportRequest(BaseRequest):
    language:Language="es"
    airport:str=""
    country:str=""
    query:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class AirlineRequest(BaseRequest):
    language:Language="es"
    airline:str=""
    query:str=""
    origin:str=""
    destination:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class CharterRequest(BaseRequest):
    language:Language="es"
    charter_operator:str=""
    query:str=""
    origin:str=""
    destination:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class SourceRequest(BaseRequest):
    language:Language="es"
    topic:str=""
    query:str=""
    source_id:str=""

class SolveRequest(BaseRequest):
    language:Language="es"
    question:str=""
    item:str=""
    airline:str=""
    baggage_type:str=""
    destination:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class GuideRequest(BaseRequest):
    language:Language="es"
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    passengers:int=Field(default=1,ge=1,le=20)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    cuba:Dict[str,Any]=Field(default_factory=dict)
    visa:Dict[str,Any]=Field(default_factory=dict)
    dviajeros:Dict[str,Any]=Field(default_factory=dict)
    state:Dict[str,Any]=Field(default_factory=dict)
    data:Dict[str,Any]=Field(default_factory=dict)

class TripState(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)
    language:Language="es"
    version:str=VERSION
    first_name:str=""
    last_name:str=""
    nationality:str=""
    country_of_residence:str=""
    passport_country:str=""
    passport_number:str=""
    date_of_birth:str=""
    email:str=""
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    flight_number:str=""
    passengers:int=1
    accommodation:str=""
    address_in_cuba:str=""
    travel_purpose:str=""
    entry_type:str=""
    dual_nationality:bool=False
    passport_valid:bool=False
    baggage:Dict[str,Any]=Field(default_factory=dict)
    item_checks:List[Dict[str,Any]]=Field(default_factory=list)
    flight:Dict[str,Any]=Field(default_factory=dict)
    booking:Dict[str,Any]=Field(default_factory=dict)
    connection:Dict[str,Any]=Field(default_factory=dict)
    visa:Dict[str,Any]=Field(default_factory=dict)
    dviajeros:Dict[str,Any]=Field(default_factory=dict)
    cuba:Dict[str,Any]=Field(default_factory=dict)
    practice:Dict[str,Any]=Field(default_factory=dict)
    guide:Dict[str,Any]=Field(default_factory=dict)
    completed_steps:List[str]=Field(default_factory=list)
    updated_at:str=""

class TripExportRequest(BaseRequest):
    language:Language="es"
    state:Dict[str,Any]=Field(default_factory=dict)
    include_pdf:bool=True
    data:Dict[str,Any]=Field(default_factory=dict)

class PDFRequest(BaseRequest):
    language:Language="es"
    state:Dict[str,Any]=Field(default_factory=dict)
    trip_state:Dict[str,Any]=Field(default_factory=dict)
    include_practice:bool=True
    include_visa:bool=True
    include_dviajeros:bool=True
    include_baggage:bool=True
    data:Dict[str,Any]=Field(default_factory=dict)

class GenericResponse(BaseModel):
    success:bool=True
    message:Optional[str]=None
    data:Dict[str,Any]=Field(default_factory=dict)
    next_action:Optional[str]=None

class SourceResponse(GenericResponse):
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class FlightResponse(GenericResponse):
    flight:Dict[str,Any]=Field(default_factory=dict)
    official_url:Optional[str]=None
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class BookingResponse(GenericResponse):
    simulation:bool=True
    real_booking:bool=False
    payment:bool=False
    notice:str=""
    search:Dict[str,Any]=Field(default_factory=dict)
    fields:List[Dict[str,Any]]=Field(default_factory=list)
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:Optional[str]=None
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:Optional[str]=None

class ItemResponse(GenericResponse):
    item:str=""
    status:str=""
    category:str=""
    placement:str=""
    explanation:str=""
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:Optional[str]=None
    ai_assisted:bool=False

class BaggageResponse(GenericResponse):
    baggage:Dict[str,Any]=Field(default_factory=dict)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:Optional[str]=None

class CubaResponse(GenericResponse):
    cuba:Dict[str,Any]=Field(default_factory=dict)
    visa:Dict[str,Any]=Field(default_factory=dict)
    dviajeros:Dict[str,Any]=Field(default_factory=dict)
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:Optional[str]=None

class DocumentResponse(GenericResponse):
    document:Dict[str,Any]=Field(default_factory=dict)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:Optional[str]=None

class PracticeResponse(GenericResponse):
    mode:str=""
    official_submission:bool=False
    notice:str=""
    completed:bool=False
    pending:List[str]=Field(default_factory=list)
    progress:Dict[str,Any]=Field(default_factory=dict)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    scenarios:List[Dict[str,Any]]=Field(default_factory=list)
    current_step:Dict[str,Any]=Field(default_factory=dict)
    official_url:Optional[str]=None
    simulation_id:str=""
    ai_assisted:bool=False

class GuideResponse(GenericResponse):
    guide:Dict[str,Any]=Field(default_factory=dict)
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    completed:List[str]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class AccessResponse(BaseModel):
    success:bool=True
    free:bool=True
    access:bool=True
    message:Optional[str]=None

class CheckoutResponse(BaseModel):
    success:bool=False
    enabled:bool=False
    message:str="La aplicación es gratuita y no utiliza pagos."

class HealthResponse(BaseModel):
    status:str="ok"
    app:str="¿QUÉ QUIERES LLEVAR?"
    version:str=VERSION
    free:bool=True
    stripe_enabled:bool=False
    login_required:bool=False
    server_storage_of_personal_data:bool=False

class ErrorResponse(BaseModel):
    success:bool=False
    message:str
    detail:Optional[str]=None

class SimulationStep(BaseModel):
    id:str=""
    title:str=""
    instruction:str=""
    explanation:str=""
    field:str=""
    value:Any=None
    required:bool=False
    completed:bool=False
    official_note:Optional[str]=None

class SimulationResponse(BaseModel):
    success:bool=True
    simulation_id:str=""
    mode:str=""
    title:str=""
    notice:str=""
    steps:List[SimulationStep]=Field(default_factory=list)
    current_step:int=0
    completed:bool=False
    official_submission:bool=False
    official_url:Optional[str]=None
    next_action:Optional[str]=None
    data:Dict[str,Any]=Field(default_factory=dict)

class AirlineResponse(GenericResponse):
    airline:Dict[str,Any]=Field(default_factory=dict)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:Optional[str]=None

class CharterResponse(GenericResponse):
    charter:Dict[str,Any]=Field(default_factory=dict)
    charters:List[Dict[str,Any]]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:Optional[str]=None

__all__=["VERSION","Language","BaseRequest","FlightRequest","BookingRequest","ConnectionRequest","BaggageRequest","ItemRequest","CubaRequest","CubaEntryRequest","VisaRequest","DViajeroRequest","DocumentRequest","PracticeRequest","AirportRequest","AirlineRequest","CharterRequest","SourceRequest","SolveRequest","GuideRequest","TripState","TripExportRequest","PDFRequest","GenericResponse","SourceResponse","FlightResponse","BookingResponse","ItemResponse","BaggageResponse","CubaResponse","DocumentResponse","PracticeResponse","GuideResponse","AccessResponse","CheckoutResponse","HealthResponse","ErrorResponse","SimulationStep","SimulationResponse","AirlineResponse","CharterResponse"]
