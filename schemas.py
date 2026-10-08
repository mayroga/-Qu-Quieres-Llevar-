from typing import Any,Dict,List,Optional
from pydantic import BaseModel,Field,ConfigDict

class Base(BaseModel):
    model_config=ConfigDict(extra="allow")

class FlightRequest(Base):
    origin:str=""
    destination:str="Cuba"
    airline:str=""
    flight_number:str=""
    flight_type:str=""
    stops:Optional[int]=None
    departure:str=""
    return_date:str=""
    passengers:int=1
    cabin:str=""
    fare:str=""
    ticket_type:str=""
    same_ticket:Optional[bool]=None
    checked_bags:Optional[int]=None
    carry_on:Optional[int]=None
    segments:List[Dict[str,Any]]=Field(default_factory=list)
    language:str="es"

class BookingRequest(Base):
    origin:str=""
    destination:str="Cuba"
    departure:str=""
    return_date:str=""
    passengers:int=1
    cabin:str=""
    fare:str=""
    bags:Optional[int]=None
    nonstop:Optional[bool]=None
    flight_type:str=""
    airline:str=""
    flight_number:str=""
    same_ticket:Optional[bool]=None
    language:str="es"

class ConnectionRequest(Base):
    origin:str=""
    destination:str=""
    connection:str=""
    airline:str=""
    flight_number:str=""
    arrival_time:str=""
    departure_time:str=""
    same_ticket:Optional[bool]=None
    bags:Optional[int]=None
    language:str="es"

class BaggageRequest(Base):
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
    weight:Optional[float]=None
    weight_unit:str="lb"
    dimensions:str=""
    pieces:Optional[int]=None
    personal_item:Optional[bool]=None
    carry_on:Optional[bool]=None
    checked:Optional[bool]=None
    international:Optional[bool]=None
    country_of_departure:str=""
    country_of_destination:str=""
    language:str="es"

class ItemRequest(Base):
    item:str=""
    description:str=""
    airline:str=""
    destination:str=""
    origin:str=""
    baggage_type:str=""
    type:str=""
    purpose:str=""
    quantity:Optional[int]=None
    weight:Optional[float]=None
    weight_unit:str=""
    size:str=""
    capacity:str=""
    contains_battery:Optional[bool]=None
    contains_liquid:Optional[bool]=None
    contains_food:Optional[bool]=None
    is_medication:Optional[bool]=None
    is_animal:Optional[bool]=None
    is_electronic:Optional[bool]=None
    country_of_departure:str=""
    country_of_destination:str=""
    cabin:str=""
    flight_number:str=""
    language:str="es"

class CubaRequest(Base):
    nationality:str=""
    passport_country:str=""
    passport_number:str=""
    birth_date:str=""
    destination:str="Cuba"
    origin:str=""
    arrival_date:str=""
    departure_date:str=""
    airline:str=""
    flight_number:str=""
    airport:str=""
    dual_nationality:Optional[bool]=None
    has_return_ticket:Optional[bool]=None
    has_travel_insurance:Optional[bool]=None
    visa_number:str=""
    evisa_number:str=""
    accommodation:str=""
    province:str=""
    municipality:str=""
    language:str="es"

class CubaEntryRequest(CubaRequest):
    entry_airport:str=""
    return_ticket:Optional[bool]=None
    travel_insurance:Optional[bool]=None

class DocumentRequest(Base):
    document_type:str=""
    nationality:str=""
    destination:str="Cuba"
    passport_country:str=""
    passport_expiration:str=""
    birth_date:str=""
    airline:str=""
    language:str="es"

class PracticeRequest(Base):
    scenario:str=""
    step:int=1
    language:str="es"

class DViajeroRequest(Base):
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
    medications:str=""
    cash_over_5000:Optional[bool]=None
    health_status:str=""
    language:str="es"

class VisaRequest(Base):
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
    language:str="es"

class PDFRequest(Base):
    data:Dict[str,Any]=Field(default_factory=dict)
    lang:str="es"
    title:str="Mi guía ¿Qué quieres llevar?"

class PDFImportRequest(Base):
    filename:str=""
    text:str=""
    recovery_data:Dict[str,Any]=Field(default_factory=dict)

class TripState(Base):
    language:str="es"
    origin:str=""
    destination:str="Cuba"
    airline:str=""
    flight_number:str=""
    departure:str=""
    return_date:str=""
    passengers:int=1
    cabin:str=""
    fare:str=""
    baggage:Dict[str,Any]=Field(default_factory=dict)
    item:Dict[str,Any]=Field(default_factory=dict)
    dviajeros:Dict[str,Any]=Field(default_factory=dict)
    visa:Dict[str,Any]=Field(default_factory=dict)
    documents:Dict[str,Any]=Field(default_factory=dict)

class Source(Base):
    id:str=""
    name:str=""
    url:str=""
    title:str=""
    section:str=""
    description:str=""
    topic:str=""
    language:str="es"

class ItemResponse(Base):
    decision:str=""
    decision_label:str=""
    message:str=""
    explanation:str=""
    conditions:List[str]=Field(default_factory=list)
    alternatives:List[str]=Field(default_factory=list)
    warnings:List[str]=Field(default_factory=list)
    gemini_used:bool=False
    gemini_error:bool=False
    confidence:str=""
    final_decision:str=""
    official_authority:str=""
    verify_with:str=""
    next_action:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    version:str=""

class BaggageResponse(Base):
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
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    version:str=""

class SimulationStep(Base):
    number:int=1
    title:str=""
    text:str=""
    reference_image:str=""
    reference_type:str=""
    official_step:str=""
    link:str=""

class SimulationResponse(Base):
    title:str=""
    message:str=""
    steps:List[SimulationStep]=Field(default_factory=list)
    official_url:str=""
    official_label:str=""
    airport_steps:List[SimulationStep]=Field(default_factory=list)
    reference_images:List[str]=Field(default_factory=list)
    language:str="es"
    version:str=""

class APIMessage(Base):
    ok:bool=True
    message:str=""
    data:Dict[str,Any]=Field(default_factory=dict)
