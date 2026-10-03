# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v14.0.0
from __future__ import annotations
from datetime import date,datetime
from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict

VERSION="14.0.0"

class AppModel(BaseModel):
    model_config=ConfigDict(extra="allow",populate_by_name=True)

class FlightSegment(AppModel):
    origin_country:str=""
    origin_city:str=""
    origin_airport:str=""
    origin_iata:str=""
    destination_country:str=""
    destination_city:str=""
    destination_airport:str=""
    destination_iata:str=""
    departure_date:str=""
    departure_time:str=""
    arrival_date:str=""
    arrival_time:str=""
    airline:str=""
    airline_code:str=""
    flight_number:str=""
    cabin:str=""
    fare:str=""
    baggage:str=""
    stops:int=0
    connection_airports:List[str]=Field(default_factory=list)

class FlightRequest(AppModel):
    origin:str=""
    destination:str=""
    origin_country:str=""
    origin_city:str=""
    origin_airport:str=""
    origin_iata:str=""
    destination_country:str=""
    destination_city:str=""
    destination_airport:str=""
    destination_iata:str=""
    trip_type:str="one_way"
    departure_date:str=""
    return_date:str=""
    departure_time:str=""
    passengers:int=1
    adults:int=1
    children:int=0
    infants:int=0
    direct:Optional[bool]=None
    connections:Optional[bool]=None
    unknown:bool=False
    cabin:str=""
    airline:str=""
    airline_code:str=""
    flight_number:str=""
    fare:str=""
    baggage:str=""
    stops:int=0
    connection_airports:List[str]=Field(default_factory=list)
    segments:List[FlightSegment]=Field(default_factory=list)
    currency:str="USD"
    already_booked:bool=False
    booking_reference:str=""
    official_airline_url:str=""
    language:str="es"
    step:str=""
    completed_steps:List[str]=Field(default_factory=list)

class BookingRequest(FlightRequest):
    action:str="practice"
    payment_started:bool=False
    payment_completed:bool=False
    booking_completed:bool=False

class ConnectionRequest(AppModel):
    origin:str=""
    destination:str=""
    airline:str=""
    flight_number:str=""
    arrival_airport:str=""
    departure_airport:str=""
    same_ticket:Optional[bool]=None
    baggage_checked:Optional[bool]=None
    country_change:Optional[bool]=None
    connection_time_minutes:Optional[int]=None
    terminal_change:Optional[bool]=None
    passenger_has_checked_bag:Optional[bool]=None
    language:str="es"

class BaggageRequest(AppModel):
    airline:str=""
    airline_code:str=""
    origin:str=""
    destination:str=""
    origin_country:str=""
    destination_country:str=""
    departure_date:str=""
    trip_type:str=""
    fare:str=""
    cabin:str=""
    baggage_type:str=""
    quantity:Optional[int]=None
    weight:Optional[float]=None
    weight_unit:str="lb"
    length:Optional[float]=None
    width:Optional[float]=None
    height:Optional[float]=None
    dimensions_unit:str="in"
    item_name:str=""
    items:List[Dict[str,Any]]=Field(default_factory=list)
    official_airline_url:str=""
    language:str="es"

class ItemRequest(AppModel):
    item:str=""
    item_name:str=""
    category:str=""
    origin:str=""
    destination:str=""
    origin_country:str=""
    destination_country:str=""
    airline:str=""
    airline_code:str=""
    baggage_type:str=""
    quantity:Optional[int]=None
    weight:Optional[float]=None
    weight_unit:str="lb"
    dimensions:Dict[str,Any]=Field(default_factory=dict)
    carry_on:Optional[bool]=None
    checked_bag:Optional[bool]=None
    battery_type:str=""
    battery_wh:Optional[float]=None
    liquid_ml:Optional[float]=None
    medication:Optional[bool]=None
    food:Optional[bool]=None
    animal:Optional[bool]=None
    language:str="es"

class IdentityData(AppModel):
    given_names:str=""
    first_name:str=""
    middle_name:str=""
    surname:str=""
    second_surname:str=""
    birth_date:str=""
    gender:str=""
    sex:str=""
    country_of_birth:str=""
    nationality:str=""
    residence_country:str=""
    passport_country:str=""
    passport_number:str=""
    passport_type:str=""
    passport_issuing_country:str=""
    passport_issuing_authority:str=""
    passport_issue_date:str=""
    passport_expiry:str=""
    email:str=""
    phone:str=""
    other_phone:str=""
    address:str=""
    city:str=""
    state_province:str=""
    country:str=""

class CubaRequest(AppModel):
    origin:str=""
    destination:str="Cuba"
    origin_country:str=""
    destination_country:str="CU"
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    residence_country:str=""
    passport_expiry:str=""
    airline:str=""
    airline_code:str=""
    flight_number:str=""
    flight_type:str=""
    purpose:str=""
    arrival_date:str=""
    departure_date:str=""
    Cuban_nationality:Optional[bool]=None
    cuban_nationality:Optional[bool]=None
    dual_nationality:Optional[bool]=None
    dual_citizen:Optional[bool]=None
    Cuban_passport:Optional[bool]=None
    cuban_passport:Optional[bool]=None
    other_passport:Optional[bool]=None
    dviajeros_done:bool=False
    visa_checked:bool=False
    customs_checked:bool=False
    baggage_checked:bool=False
    documents_checked:bool=False
    language:str="es"
    step:str=""
    completed_steps:List[str]=Field(default_factory=list)

class CubaEntryRequest(CubaRequest):
    entry_point:str=""
    entry_airport:str=""
    accommodation_type:str=""
    accommodation_name:str=""
    accommodation_place:str=""
    province:str=""
    municipality:str=""
    address:str=""
    visa_number:str=""
    dviajeros_number:str=""
    has_customs_declaration:Optional[bool]=None
    cash_currency:str=""
    cash_amount:Optional[float]=None

class DViajeroRequest(AppModel):
    language:str="es"
    create_form:bool=False

    first_name:str=""
    middle_name:str=""
    surname:str=""
    second_surname:str=""
    given_names:str=""
    birth_date:str=""
    gender:str=""
    sex:str=""
    country_of_birth:str=""
    nationality:str=""
    document_type:str="passport"
    document_issuing_country:str=""
    passport_country:str=""
    passport_number:str=""
    passport_issue_date:str=""
    passport_expiry:str=""
    residence_country:str=""
    email:str=""
    phone:str=""
    other_phone:str=""

    arrival_date:str=""
    flight_number:str=""
    airline_name:str=""
    airline:str=""
    airline_code:str=""
    seat_number:str=""
    point_of_entry:str=""
    entry_airport:str=""
    traveler_country_origin:str=""
    origin_country:str=""
    travel_reason:str=""
    purpose:str=""
    organism:str=""
    visa_number:str=""
    evisa_number:str=""

    province:str=""
    municipality:str=""
    accommodation_type:str=""
    accommodation_place:str=""
    accommodation_name:str=""
    address:str=""

    countries_last_15_days:List[str]=Field(default_factory=list)
    recent_countries:str=""
    symptoms_last_15_days:List[str]=Field(default_factory=list)
    symptoms:str=""
    questionnaire:Dict[str,Any]=Field(default_factory=dict)
    vaccination:Optional[bool]=None
    vaccine:str=""
    vaccination_scheme:str=""
    pcr_rt_test:Dict[str,Any]=Field(default_factory=dict)

    has_customs_declaration:Optional[bool]=None
    customs_declaration:Optional[bool]=None
    cash_currency:str=""
    cash_amount:Optional[float]=None
    cash_amount_currency:str=""
    goods:List[Dict[str,Any]]=Field(default_factory=list)
    goods_description:str=""
    unaccompanied_luggage:Optional[bool]=None
    unaccompanied_luggage_details:str=""

    truthful_confirmation:Optional[bool]=None
    captcha:str=""
    submitted:bool=False
    qr_generated:bool=False
    official_pdf:bool=False
    step:str=""
    completed_steps:List[str]=Field(default_factory=list)
    answers:Dict[str,Any]=Field(default_factory=dict)
    extra:Dict[str,Any]=Field(default_factory=dict)

class VisaRequest(AppModel):
    language:str="es"

    given_names:str=""
    first_name:str=""
    middle_name:str=""
    surname:str=""
    second_surname:str=""
    gender:str=""
    sex:str=""
    nationality:str=""
    country_of_nationality:str=""
    birth_date:str=""
    place_of_birth:str=""
    birth_city:str=""
    birth_state_province:str=""
    birth_country:str=""

    email:str=""
    phone:str=""
    current_address:str=""
    address:str=""
    city:str=""
    state_province:str=""
    country:str=""
    postal_code:str=""

    passport_type:str="regular"
    passport_number:str=""
    issuing_country:str=""
    passport_issuing_country:str=""
    issuing_authority:str=""
    passport_issue_date:str=""
    passport_expiry:str=""

    arrival_date:str=""
    departure_date:str=""
    length_of_stay:Optional[int]=None
    flight_number:str=""
    airline:str=""
    origin:str=""
    destination:str="Cuba"
    purpose:str=""
    travel_purpose:str=""
    accommodation:str=""
    accommodation_type:str=""
    accommodation_address:str=""

    additional_information:str=""
    application_confirmation:Optional[bool]=None
    official_url:str=""
    submitted:bool=False
    payment_completed:bool=False
    application_number:str=""
    visa_number:str=""
    step:str=""
    completed_steps:List[str]=Field(default_factory=list)
    answers:Dict[str,Any]=Field(default_factory=dict)
    extra:Dict[str,Any]=Field(default_factory=dict)

class DocumentRequest(AppModel):
    origin:str=""
    destination:str=""
    origin_country:str=""
    destination_country:str=""
    nationality:str=""
    residence_country:str=""
    passport_country:str=""
    passport_number:str=""
    passport_expiry:str=""
    passport_issue_date:str=""
    purpose:str=""
    departure_date:str=""
    return_date:str=""
    arrival_date:str=""
    visa_required:Optional[bool]=None
    visa_type:str=""
    visa_number:str=""
    entry_authorization:str=""
    health_requirement:str=""
    vaccination_requirement:str=""
    additional_documents:List[str]=Field(default_factory=list)
    language:str="es"
    step:str=""
    completed_steps:List[str]=Field(default_factory=list)

class AirportRequest(AppModel):
    query:str=""
    country:str=""
    city:str=""
    iata:str=""
    language:str="es"

class AirlineRequest(AppModel):
    query:str=""
    airline_id:str=""
    name:str=""
    country:str=""
    language:str="es"

class SourceRequest(AppModel):
    process:str=""
    category:str=""
    source_ids:List[str]=Field(default_factory=list)
    query:str=""
    official_only:bool=True
    language:str="es"

class PracticeRequest(AppModel):
    scenario:str=""
    language:str="es"
    step:int=1
    data:Dict[str,Any]=Field(default_factory=dict)
    answers:Dict[str,Any]=Field(default_factory=dict)
    completed_steps:List[str]=Field(default_factory=list)
    reset:bool=False

class SimulationField(AppModel):
    id:str=""
    name:str=""
    label_es:str=""
    label_en:str=""
    type:str="text"
    required:bool=False
    explanation_es:str=""
    explanation_en:str=""
    options:List[Dict[str,Any]]=Field(default_factory=list)
    placeholder_es:str=""
    placeholder_en:str=""
    source_id:str=""
    value:Any=None

class SimulationStep(AppModel):
    id:str=""
    title:str=""
    question:str=""
    explanation:str=""
    fields:List[str]=Field(default_factory=list)
    field_specs:List[SimulationField]=Field(default_factory=list)
    required_fields:List[str]=Field(default_factory=list)
    help_text:str=""
    next_action:str=""
    official_url:str=""
    progress:int=0
    total_steps:int=0

class SimulationResponse(AppModel):
    ok:bool=True
    scenario:str=""
    title:str=""
    message:str=""
    step:int=1
    total_steps:int=0
    progress:int=0
    steps:List[SimulationStep]=Field(default_factory=list)
    current:Optional[SimulationStep]=None
    data:Dict[str,Any]=Field(default_factory=dict)
    result:Dict[str,Any]=Field(default_factory=dict)
    next_action:str=""
    official_url:str=""
    pdf_type:str=""
    pdf_ready:bool=False
    completed:bool=False
    language:str="es"

class TripState(AppModel):
    version:str=VERSION
    language:str="es"
    current_step:str=""
    current_process:str=""
    origin:str=""
    destination:str=""
    trip_type:str="one_way"
    departure_date:str=""
    return_date:str=""
    passengers:int=1
    adults:int=1
    children:int=0
    infants:int=0
    airline:str=""
    airline_code:str=""
    flight_number:str=""
    cabin:str=""
    fare:str=""
    baggage:str=""
    already_booked:bool=False
    booking_reference:str=""
    origin_country:str=""
    destination_country:str=""
    origin_airport:str=""
    destination_airport:str=""
    origin_iata:str=""
    destination_iata:str=""
    nationality:str=""
    residence_country:str=""
    passport_country:str=""
    passport_number:str=""
    passport_expiry:str=""
    passport_issue_date:str=""
    Cuban_nationality:Optional[bool]=None
    dual_nationality:Optional[bool]=None
    cuban_nationality:Optional[bool]=None
    dual_citizen:Optional[bool]=None
    dviajeros:Dict[str,Any]=Field(default_factory=dict)
    visa:Dict[str,Any]=Field(default_factory=dict)
    documents:Dict[str,Any]=Field(default_factory=dict)
    baggage_data:Dict[str,Any]=Field(default_factory=dict)
    items:List[Dict[str,Any]]=Field(default_factory=list)
    practice:Dict[str,Any]=Field(default_factory=dict)
    cuba:Dict[str,Any]=Field(default_factory=dict)
    progress:Dict[str,Any]=Field(default_factory=dict)
    completed_processes:List[str]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    next_action:str=""
    updated_at:str=""

class TripExportRequest(AppModel):
    trip:TripState=Field(default_factory=TripState)
    language:str="es"
    include_documents:bool=True
    include_sensitive:bool=False

class GuideRequest(AppModel):
    trip:TripState=Field(default_factory=TripState)
    language:str="es"
    title:str="Mi preparación de viaje"
    include_flight:bool=True
    include_baggage:bool=True
    include_items:bool=True
    include_documents:bool=True
    include_cuba:bool=True
    include_dviajeros:bool=True
    include_visa:bool=True
    include_customs:bool=True
    include_sources:bool=True

class PDFRequest(AppModel):
    data:Dict[str,Any]=Field(default_factory=dict)
    trip:Optional[TripState]=None
    language:str="es"
    title:str="Mi preparación de viaje"
    pdf_type:str="guide"
    process:str=""
    include_sources:bool=True

class PDFImportRequest(AppModel):
    filename:str=""
    text:str=""
    recovery_data:Dict[str,Any]=Field(default_factory=dict)
    process:str=""
    language:str="es"

class DeleteLocalRequest(AppModel):
    confirm:bool=False
    scope:str="trip"
    language:str="es"

class SolveRequest(AppModel):
    process:str=""
    question:str=""
    data:Dict[str,Any]=Field(default_factory=dict)
    language:str="es"

class GenericResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    message:str=""
    result:Dict[str,Any]=Field(default_factory=dict)
    data:Dict[str,Any]=Field(default_factory=dict)
    next_action:str=""
    official_url:str=""
    pdf_ready:bool=False
    pdf_type:str=""
    language:str="es"

class SourceResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    process:str=""
    language:str="es"

class FlightResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    title:str="Mi vuelo"
    message:str=""
    result:Dict[str,Any]=Field(default_factory=dict)
    data:Dict[str,Any]=Field(default_factory=dict)
    segments:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""
    official_url:str=""
    pdf_ready:bool=False
    language:str="es"

class BookingResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    title:str="Practicar búsqueda de vuelo"
    message:str=""
    result:Dict[str,Any]=Field(default_factory=dict)
    data:Dict[str,Any]=Field(default_factory=dict)
    steps:List[SimulationStep]=Field(default_factory=list)
    current:Optional[SimulationStep]=None
    next_action:str=""
    official_url:str=""
    pdf_ready:bool=False
    completed:bool=False
    language:str="es"

class ItemResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    item:str=""
    category:str=""
    decision:str=""
    message:str=""
    result:Dict[str,Any]=Field(default_factory=dict)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    verify_with:List[Dict[str,Any]]=Field(default_factory=list)
    next_action:str=""
    pdf_ready:bool=False
    language:str="es"

class BaggageResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    message:str=""
    result:Dict[str,Any]=Field(default_factory=dict)
    rules:Dict[str,Any]=Field(default_factory=dict)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:str=""
    next_action:str=""
    pdf_ready:bool=False
    language:str="es"

class CubaResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    message:str=""
    profile:Dict[str,Any]=Field(default_factory=dict)
    result:Dict[str,Any]=Field(default_factory=dict)
    status:str=""
    progress:int=0
    pending:List[str]=Field(default_factory=list)
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    dviajeros:Dict[str,Any]=Field(default_factory=dict)
    visa:Dict[str,Any]=Field(default_factory=dict)
    documents:Dict[str,Any]=Field(default_factory=dict)
    customs:Dict[str,Any]=Field(default_factory=dict)
    baggage:Dict[str,Any]=Field(default_factory=dict)
    pdf_ready:bool=False
    language:str="es"

class DocumentResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    message:str=""
    result:Dict[str,Any]=Field(default_factory=dict)
    requirements:List[Dict[str,Any]]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    pending:List[str]=Field(default_factory=list)
    next_action:str=""
    pdf_ready:bool=False
    language:str="es"

class HealthResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    status:str="ok"
    app:str="¿QUÉ QUIERES LLEVAR?"
    checks:Dict[str,Any]=Field(default_factory=dict)

class AirlineResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    airlines:List[Dict[str,Any]]=Field(default_factory=list)
    official_url:str=""
    language:str="es"

class LegalResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    title:str="Aviso importante"
    message:str=""
    points:List[str]=Field(default_factory=list)
    language:str="es"

class ConfigResponse(AppModel):
    ok:bool=True
    version:str=VERSION
    app:str="¿QUÉ QUIERES LLEVAR?"
    features:Dict[str,bool]=Field(default_factory=dict)
    processes:List[str]=Field(default_factory=list)
    languages:List[str]=Field(default_factory=lambda:["es","en"])
    official_sources_only:bool=True

__all__=[
"VERSION","FlightSegment","FlightRequest","BookingRequest","ConnectionRequest",
"BaggageRequest","ItemRequest","IdentityData","CubaRequest","CubaEntryRequest",
"DViajeroRequest","VisaRequest","DocumentRequest","AirportRequest","AirlineRequest",
"SourceRequest","PracticeRequest","SimulationField","SimulationStep",
"SimulationResponse","TripState","TripExportRequest","GuideRequest","PDFRequest",
"PDFImportRequest","DeleteLocalRequest","SolveRequest","GenericResponse",
"SourceResponse","FlightResponse","BookingResponse","ItemResponse","BaggageResponse",
"CubaResponse","DocumentResponse","HealthResponse","AirlineResponse","LegalResponse",
"ConfigResponse"
]
