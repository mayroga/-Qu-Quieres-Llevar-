# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v15.0.1
from __future__ import annotations
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict

VERSION="15.0.1"

class BaseRequest(BaseModel):
    model_config=ConfigDict(extra="allow",str_strip_whitespace=True)

class FlightRequest(BaseRequest):
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    stops:Any=None
    departure:str=""
    return_date:str=""
    passengers:int=1
    cabin:str=""
    fare:str=""
    ticket_type:str=""
    same_ticket:Any=None
    checked_bags:Any=None
    carry_on:Any=None
    segments:List[Dict[str,Any]]=Field(default_factory=list)

class BookingRequest(BaseRequest):
    origin:str=""
    destination:str=""
    departure:str=""
    return_date:str=""
    passengers:int=1
    cabin:str=""
    fare:str=""
    bags:Any=None
    nonstop:Any=None
    flight_type:str=""
    airline:str=""
    flight_number:str=""
    same_ticket:Any=None

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
    same_ticket:Any=None
    baggage:Any=None
    bag_recheck:Any=None
    country_change:Any=None
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
    weight:Any=None
    dimensions:Any=None
    pieces:Any=None
    personal_item:Any=None
    carry_on:Any=None
    checked:Any=None
    international:Any=None
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
    quantity:Any=None
    weight:Any=None
    size:Any=None
    contains_battery:Any=None
    contains_liquid:Any=None
    contains_food:Any=None
    is_medication:Any=None
    is_animal:Any=None
    is_electronic:Any=None
    country_of_departure:str=""
    country_of_destination:str=""
    cabin:str=""
    flight_number:str=""
    language:str="es"
    question:str=""

class CubaRequest(BaseRequest):
    origin:str=""
    destination:str="Cuba"
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    country_of_residence:str=""
    residence_country:str=""
    cuban_nationality:Any=None
    dual_citizen:Any=None
    flight_type:str=""
    airline:str=""
    flight_number:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    passport_valid_until:str=""
    has_cuban_passport:Any=None
    has_other_passport:Any=None
    dviajeros_done:Any=None
    visa_checked:Any=None
    customs_checked:Any=None
    baggage_checked:Any=None
    documents_checked:Any=None
    given_names:str=""
    surnames:str=""
    birth_date:str=""
    sex:str=""
    email:str=""
    phone:str=""
    arrival_airport:str=""
    departure_airport:str=""
    address_destination:str=""
    visa_number:str=""
    evisa_number:str=""

class CubaEntryRequest(CubaRequest):
    entry_airport:str=""
    return_ticket:Any=None
    travel_insurance:Any=None

class VisaRequest(BaseRequest):
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    surname:str=""
    surnames:str=""
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
    visa_number:str=""
    evisa_number:str=""

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
    flight_number:str=""
    airline:str=""
    arrival_airport:str=""
    departure_airport:str=""
    email:str=""
    phone:str=""
    address_destination:str=""
    purpose:str=""
    visa_number:str=""
    evisa_number:str=""
    accommodation_type:str=""
    province:str=""
    municipality:str=""
    accommodation_name:str=""
    medications:Any=None
    cash_over_5000:Any=None
    health_status:str=""

class DocumentRequest(BaseRequest):
    origin:str=""
    destination:str=""
    nationality:str=""
    passport_country:str=""
    country_of_residence:str=""
    cuban_nationality:Any=None
    dual_citizen:Any=None
    airline:str=""
    flight_type:str=""
    flight_number:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    passport_valid_until:str=""
    visa_checked:Any=None
    dviajeros_done:Any=None
    documents_checked:Any=None

class PracticeRequest(BaseRequest):
    scenario:str=""
    item:str=""
    state:Any=None
    step:Any=None
    answer:str=""
    language:str="es"
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
    query:str=""

class SourceRequest(BaseRequest):
    topic:str="official"
    query:str=""
    country:str=""
    airline:str=""

class SolveRequest(BaseRequest):
    question:str=""
    language:str="es"
    data:Dict[str,Any]=Field(default_factory=dict)

class GuideRequest(BaseRequest):
    origin:str=""
    destination:str="Cuba"
    nationality:str=""
    passport_country:str=""
    country_of_residence:str=""
    cuban_nationality:Any=None
    dual_citizen:Any=None
    airline:str=""
    flight_type:str=""
    flight_number:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    passport_valid_until:str=""
    given_names:str=""
    surnames:str=""
    birth_date:str=""
    sex:str=""
    email:str=""
    phone:str=""
    arrival_airport:str=""
    departure_airport:str=""
    address_destination:str=""
    visa_number:str=""
    evisa_number:str=""
    accommodation_type:str=""
    province:str=""
    municipality:str=""
    accommodation_name:str=""
    items:List[Dict[str,Any]]=Field(default_factory=list)
    baggage:List[Dict[str,Any]]=Field(default_factory=list)
    checklists:List[Dict[str,Any]]=Field(default_factory=list)
    current_state:str=""
    last_item:str=""
    next_action:str=""
    data:Dict[str,Any]=Field(default_factory=dict)

class TripState(BaseModel):
    model_config=ConfigDict(extra="allow")
    version:str=VERSION
    origin:str=""
    destination:str="Cuba"
    departure:str=""
    return_date:str=""
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    cabin:str=""
    fare:str=""
    passengers:int=1
    same_ticket:Any=None
    connection:Dict[str,Any]=Field(default_factory=dict)
    traveler:Dict[str,Any]=Field(default_factory=dict)
    cuba:Dict[str,Any]=Field(default_factory=dict)
    accommodation:Dict[str,Any]=Field(default_factory=dict)
    items:List[Dict[str,Any]]=Field(default_factory=list)
    baggage:List[Dict[str,Any]]=Field(default_factory=list)
    practice:Dict[str,Any]=Field(default_factory=dict)
    dviajeros:Dict[str,Any]=Field(default_factory=dict)
    visa:Dict[str,Any]=Field(default_factory=dict)
    documents:Dict[str,Any]=Field(default_factory=dict)
    current_state:str=""
    pending:str=""
    next_action:str=""
    updated_at:str=""

class TripExportRequest(BaseRequest):
    data:TripState

class PDFRequest(BaseRequest):
    data:Dict[str,Any]=Field(default_factory=dict)
    lang:str="es"
    title:str="Mi guía de viaje"

class PDFImportRequest(BaseRequest):
    filename:str=""
    text:str=""
    recovery_data:Optional[Dict[str,Any]]=None

class DeleteLocalRequest(BaseRequest):
    confirm:bool=False

class GenericResponse(BaseModel):
    ok:bool=True
    version:str=VERSION
    message:str=""
    data:Any=None
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class SourceResponse(BaseModel):
    ok:bool=True
    version:str=VERSION
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class FlightResponse(GenericResponse):
    pass

class BookingResponse(GenericResponse):
    pass

class ItemResponse(GenericResponse):
    decision:str=""
    decision_label:str=""
    message:str=""
    explanation:str=""
    conditions:List[str]=Field(default_factory=list)
    alternatives:List[str]=Field(default_factory=list)
    warnings:List[str]=Field(default_factory=list)
    gemini_used:bool=False
    gemini_available:bool=False
    gemini_search_used:bool=False
    confidence:Any=None
    final_decision:str=""
    official_authority:str=""
    verify_with:List[str]=Field(default_factory=list)
    next_action:str=""

class BaggageResponse(GenericResponse):
    status:str=""
    type:str=""
    type_name:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    fare:str=""
    cabin:str=""
    message:str=""
    do_not_assume:List[str]=Field(default_factory=list)
    conditions:List[str]=Field(default_factory=list)
    next_action:str=""

class CubaResponse(GenericResponse):
    status:str=""
    message:str=""
    checklist:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class DocumentResponse(GenericResponse):
    status:str=""
    message:str=""
    documents:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""

class PracticeResponse(GenericResponse):
    status:str=""
    step:Any=None
    total_steps:Any=None
    message:str=""
    next_action:str=""

class GuideResponse(GenericResponse):
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    current_state:str=""
    next_action:str=""

class HealthResponse(BaseModel):
    status:str="ok"
    version:str=VERSION
    source_version:str=""
    app:str=""
    ready:bool=True
    free:bool=True
    login_required:bool=False
    payment_required:bool=False
    server_storage:bool=False
    gemini_item_assistant:bool=False

class ErrorResponse(BaseModel):
    ok:bool=False
    version:str=VERSION
    error:str=""
    details:Any=None

class SimulationStep(BaseModel):
    step:int=0
    title:str=""
    instruction:str=""
    explanation:str=""
    example:str=""
    reference_image:str=""
    reference_type:str=""
    official_step:bool=False
    completed:bool=False

class SimulationResponse(GenericResponse):
    title:str=""
    instructions:List[str]=Field(default_factory=list)
    steps:List[SimulationStep]=Field(default_factory=list)
    reference_images:List[str]=Field(default_factory=list)
    official_url:str=""
    disclaimer:str=""

class AirlineResponse(BaseModel):
    ok:bool=True
    version:str=VERSION
    airlines:List[Dict[str,Any]]=Field(default_factory=list)

class LegalResponse(BaseModel):
    ok:bool=True
    version:str=VERSION
    points:List[str]=Field(default_factory=list)

class ConfigResponse(BaseModel):
    ok:bool=True
    version:str=VERSION
    language:str="es"
    languages:List[str]=Field(default_factory=lambda:["es","en"])
    free:bool=True
    login:bool=False
    payment:bool=False
    stripe:bool=False
    server_storage:bool=False
    english:bool=True
    gemini_item_assistant:bool=False
    features:Dict[str,bool]=Field(default_factory=dict)
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)

__all__=[k for k in globals() if not k.startswith("_")]
