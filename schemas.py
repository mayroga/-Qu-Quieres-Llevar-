# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v13.0.0
from __future__ import annotations
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict,AliasChoices

VERSION="13.0.0"

class BaseRequest(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)

class FlightRequest(BaseRequest):
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    stops:Any=0
    departure:str=""
    return_date:str=""
    return_:str=Field("",validation_alias=AliasChoices("return_date","return"))
    passengers:Any=1
    cabin:str=""
    fare:str=""
    ticket_type:str=""
    same_ticket:bool=False
    checked_bags:Any=0
    carry_on:Any=0
    segments:List[Dict[str,Any]]=Field(default_factory=list)

class BookingRequest(BaseRequest):
    origin:str=""
    destination:str=""
    departure:str=""
    return_date:str=""
    return_:str=Field("",validation_alias=AliasChoices("return_date","return"))
    passengers:Any=1
    cabin:str=""
    fare:str=""
    bags:Any=0
    nonstop:bool=False
    flight_type:str=""
    airline:str=""
    flight_number:str=""
    same_ticket:bool=False

class ConnectionRequest(BaseRequest):
    origin:str=""
    destination:str=""
    airport:str=""
    terminal:str=""
    gate:str=""
    arrival_gate:str=""
    boarding_gate:str=""
    next_flight:str=""
    next_gate:str=""
    next_terminal:str=""
    same_ticket:bool=False
    baggage:str=""
    bag_recheck:bool=False
    country_change:bool=False
    airline:str=""
    next_airline:str=""
    connection_minutes:Any=None

class BaggageRequest(BaseRequest):
    type:str=""
    baggage_type:str=""
    item:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    flight_number:str=""
    flight_type:str=""
    fare:str=""
    cabin:str=""
    weight:str=""
    dimensions:str=""
    pieces:Any=0
    personal_item:Any=""
    carry_on:Any=""
    checked:Any=""
    international:bool=False
    country_of_departure:str=""
    country_of_destination:str=""

class ItemRequest(BaseRequest):
    item:str=""
    description:str=""
    airline:str=""
    destination:str=""
    origin:str=""
    baggage_type:str=""
    type:str=""
    purpose:str=""
    quantity:str=""
    weight:str=""
    size:str=""
    contains_battery:bool=False
    contains_liquid:bool=False
    contains_food:bool=False
    is_medication:bool=False
    is_animal:bool=False
    is_electronic:bool=False

class CubaRequest(BaseRequest):
    origin:str=""
    destination:str="Cuba"
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    country_of_residence:str=""
    residence_country:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    flight_type:str=""
    airline:str=""
    flight_number:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    passport_valid_until:str=""
    has_cuban_passport:bool=False
    has_other_passport:bool=False
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    baggage_checked:bool=False
    documents_checked:bool=False

class CubaEntryRequest(CubaRequest):
    entry_airport:str=""
    return_ticket:bool=False
    travel_insurance:bool=False

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
    step:Any=0
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
    connection:str=""
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
    stops:Any=0
    nationality:str=""
    passport_country:str=""
    country_of_residence:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    purpose:str=""
    items:List[Any]=Field(default_factory=list)
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
    model_config=ConfigDict(extra="allow")
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    stops:Any=0
    departure:str=""
    return_date:str=""
    passengers:Any=1
    cabin:str=""
    fare:str=""
    ticket_type:str=""
    same_ticket:bool=False
    checked_bags:Any=0
    carry_on:Any=0
    nationality:str=""
    passport_country:str=""
    country_of_residence:str=""
    cuban_nationality:bool=False
    dual_citizen:bool=False
    passport_valid_until:str=""
    has_cuban_passport:bool=False
    has_other_passport:bool=False
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    documents_checked:bool=False
    baggage_checked:bool=False
    items:List[Any]=Field(default_factory=list)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    current_state:str=""
    last_item:str=""
    next_action:str=""
    practice:Dict[str,Any]=Field(default_factory=dict)
    updated_at:str=""

class TripExportRequest(BaseRequest):
    data:TripState

class PDFRequest(BaseRequest):
    data:Dict[str,Any]=Field(default_factory=dict)
    lang:str="es"
    title:str="¿QUÉ QUIERES LLEVAR?"

class PDFImportRequest(BaseRequest):
    filename:str=""
    text:str=""
    recovery_data:Dict[str,Any]=Field(default_factory=dict)

class DeleteLocalRequest(BaseRequest):
    confirm:bool=False

class GenericResponse(BaseModel):
    status:str="ok"
    message:str=""
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    data:Dict[str,Any]=Field(default_factory=dict)

class SourceResponse(BaseModel):
    status:str="ok"
    topic:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class FlightResponse(BaseModel):
    status:str="ok"
    version:str=VERSION
    message:str=""
    search:Dict[str,Any]=Field(default_factory=dict)
    missing:List[str]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class BookingResponse(BaseModel):
    status:str="ok"
    simulation:bool=True
    real_booking:bool=False
    payment:bool=False
    official_submission:bool=False
    notice:str="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
    message:str=""
    search:Dict[str,Any]=Field(default_factory=dict)
    fields:List[Any]=Field(default_factory=list)
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class ItemResponse(BaseModel):
    status:str="verify"
    item:str=""
    category:str=""
    baggage_type:str=""
    message:str=""
    gemini_used:bool=False
    final_decision:bool=False
    verify_with:List[Any]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class BaggageResponse(BaseModel):
    status:str="review"
    type:str=""
    type_name:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    fare:str=""
    message:str=""
    do_not_assume:List[str]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class CubaResponse(BaseModel):
    status:str="incomplete"
    profile:Dict[str,Any]=Field(default_factory=dict)
    checklist:List[Dict[str,Any]]=Field(default_factory=list)
    completed:int=0
    total:int=0
    progress:float=0
    pending:List[str]=Field(default_factory=list)
    details:Dict[str,Any]=Field(default_factory=dict)
    message:str=""
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class DocumentResponse(BaseModel):
    status:str="incomplete"
    checks:List[Dict[str,Any]]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class PracticeResponse(BaseModel):
    mode:str="practice"
    scenario:str=""
    official_submission:bool=False
    notice:str="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
    message:str=""
    next_action:str=""
    completed:int=0
    pending:int=0
    progress:float=0
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    scenarios:List[Any]=Field(default_factory=list)
    current_step:Dict[str,Any]=Field(default_factory=dict)
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    step:int=0

class GuideResponse(BaseModel):
    status:str="incomplete"
    guide:Dict[str,Any]=Field(default_factory=dict)
    pending:List[str]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class HealthResponse(BaseModel):
    status:str="ok"
    version:str=VERSION
    app:str="¿QUÉ QUIERES LLEVAR?"
    ready:bool=True
    free:bool=True
    login_required:bool=False
    payment_required:bool=False
    server_storage:bool=False
    gemini_item_assistant:bool=False

class ErrorResponse(BaseModel):
    status:str="error"
    message:str=""
    next_action:str=""
    details:Dict[str,Any]=Field(default_factory=dict)

class SimulationStep(BaseModel):
    step:int=0
    title:str=""
    instruction:str=""
    fields:List[str]=Field(default_factory=list)
    options:List[str]=Field(default_factory=list)
    completed:bool=False

class SimulationResponse(BaseModel):
    status:str="ok"
    scenario:str=""
    simulation:bool=True
    official_submission:bool=False
    notice:str="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
    message:str=""
    step:int=0
    progress:float=0
    current_step:Dict[str,Any]=Field(default_factory=dict)
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class AirlineResponse(BaseModel):
    status:str="ok"
    airlines:List[Dict[str,Any]]=Field(default_factory=list)
    charters:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class LegalResponse(BaseModel):
    status:str="ok"
    title:str="Aviso legal"
    message:str=""
    points:List[str]=Field(default_factory=list)

class ConfigResponse(BaseModel):
    status:str="ok"
    app:str="¿QUÉ QUIERES LLEVAR?"
    version:str=VERSION
    language:str="es"
    free:bool=True
    login_required:bool=False
    payment_required:bool=False
    stripe_enabled:bool=False
    server_storage:bool=False
    features:Dict[str,bool]=Field(default_factory=dict)
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)

__all__=[k for k in globals() if not k.startswith("_")]
