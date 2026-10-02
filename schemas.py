# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.1
from datetime import date
from typing import Any,Dict,List,Literal,Optional
from pydantic import BaseModel,ConfigDict,Field,field_validator

Language=Literal["es","en"]

class StrictModel(BaseModel):
    model_config=ConfigDict(extra="ignore",str_strip_whitespace=True,validate_assignment=True)

class CategoryVisualEnum:
    ALLOW="ALLOW"
    ALLOW_WITH_CONDITION="ALLOW_WITH_CONDITION"
    NOT_ALLOWED="NOT_ALLOWED"
    REVIEW="REVIEW"

class BaggageTypeEnum:
    CARRY_ON="carry_on"
    CHECKED="checked"
    PERSONAL_ITEM="personal_item"

class RuleStatusEnum:
    ACTIVE="ACTIVE"
    PENDING="PENDING"
    EXPIRED="EXPIRED"

class SourceTypeEnum:
    OFFICIAL="official"
    AIRLINE="airline"
    SECURITY="security"
    BAGGAGE="baggage"
    GOVERNMENT="government"
    SEARCH="search"

class FlightSearchRequest(StrictModel):
    origin:Optional[str]=Field("",min_length=0,max_length=120)
    destination:Optional[str]=Field("",min_length=0,max_length=120)
    departure_date:Optional[date]=None
    return_date:Optional[date]=None
    passengers:int=Field(1,ge=1,le=20)
    cabin:Optional[str]=Field("",max_length=80)
    airline:Optional[str]=Field("",max_length=120)
    nonstop:Optional[bool]=None
    language:Language="es"

class FlightResult(StrictModel):
    id:str=""
    airline:str=""
    flight_number:str=""
    origin:str=""
    destination:str=""
    departure:str=""
    arrival:str=""
    date:str=""
    direct:bool=False
    stops:int=0
    connection:bool=False
    connection_airport:str=""
    connection_duration:str=""
    passengers:int=1
    cabin:str=""
    fare:str=""
    currency:str="USD"
    baggage_summary:str=""
    source:str=""
    source_name:str=""
    verified:bool=False
    verified_at:str=""
    official_source:bool=False
    conditions:List[str]=Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls,v):
        return str(v or "USD").upper()[:10]

class FlightSourceCard(StrictModel):
    id:str=""
    name:str=""
    url:str=""
    source_type:str=""
    country:str=""
    airline:str=""
    destination:str=""
    scope:str=""
    official:bool=False
    verified:bool=False
    verification_date:str=""
    notes:str=""

class FlightSearchResponse(StrictModel):
    success:bool=True
    results:List[FlightResult]=Field(default_factory=list)
    sources:List[FlightSourceCard]=Field(default_factory=list)
    message:str=""
    source:str=""
    verified:bool=False
    official_source:bool=False
    next_action:str=""
    route:Dict[str,Any]=Field(default_factory=dict)
    google_flights_url:str=""
    airline_sources:List[FlightSourceCard]=Field(default_factory=list)
    is_cuba_route:bool=False
    important:List[str]=Field(default_factory=list)
    errors:List[str]=Field(default_factory=list)

class FlightContext(StrictModel):
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    flight_number:str=""
    baggage:Dict[str,Any]=Field(default_factory=dict)
    baggage_summary:str=""
    source:str=""
    source_name:str=""
    verified:bool=False
    verified_at:str=""
    official_source:bool=False
    cabin:str=""
    fare:str=""
    currency:str="USD"
    language:Language="es"

    @field_validator("currency")
    @classmethod
    def currency_upper(cls,v):
        return str(v or "USD").upper()[:10]

class SelectedFlightRequest(StrictModel):
    flight:Dict[str,Any]=Field(default_factory=dict)
    language:Language="es"

class ItemCheckInput(StrictModel):
    item:str=""
    baggage_type:Optional[str]=""
    airline:Optional[str]=""
    destination:Optional[str]=""
    origin:Optional[str]=""
    cabin:Optional[str]=""
    fare:Optional[str]=""
    language:Language="es"

class ItemCheckRequest(ItemCheckInput):
    pass

class OfficialLink(StrictModel):
    id:str=""
    name:str=""
    url:str=""
    source_type:str=""
    official:bool=False
    verified:bool=False
    verification_date:str=""
    notes:str=""

class SourceRecord(StrictModel):
    id:str=""
    name:str=""
    url:str=""
    source_type:str=""
    country:str=""
    airline:str=""
    destination:str=""
    scope:str=""
    official:bool=False
    verified:bool=False
    verification_date:str=""
    notes:str=""

class ItemCheckResponse(StrictModel):
    success:bool=True
    item:str=""
    category:str="REVIEW"
    visual_status:str="REVIEW"
    rule_status:str="PENDING"
    explanation:str=""
    baggage_place:str=""
    conditions:List[str]=Field(default_factory=list)
    missing_information:List[str]=Field(default_factory=list)
    source:str=""
    source_name:str=""
    verified:bool=False
    verification_date:str=""
    official_link:str=""
    next_action:str=""
    legal_notice:str=""
    airline:str=""
    origin:str=""
    destination:str=""
    cabin:str=""
    fare:str=""

class TeachTermRequest(StrictModel):
    term:str=Field("",max_length=200)
    language:Language="es"

class TeachTermResponse(StrictModel):
    success:bool=True
    term:str=""
    explanation:str=""
    language:Language="es"

class GuideRequest(StrictModel):
    language:Language="es"
    topic:Optional[str]=""
    flight:Dict[str,Any]=Field(default_factory=dict)

class GuideStep(StrictModel):
    id:str=""
    title:str=""
    text:str=""

class GuideResponse(StrictModel):
    success:bool=True
    language:Language="es"
    topic:str=""
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    cuba_steps:List[str]=Field(default_factory=list)
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)
    legal_notice:str=""
    next_action:str=""

class SessionStatusResponse(StrictModel):
    success:bool=True
    active:bool=False
    expires_at:str=""
    minutes_remaining:int=0

class AdminLoginRequest(StrictModel):
    username:str=Field("",min_length=1,max_length=300)
    password:str=Field("",min_length=1,max_length=300)

class AdminLoginResponse(StrictModel):
    success:bool=True
    token:str=""
    expires_at:str=""
    message:str=""

class CreateCheckoutRequest(StrictModel):
    return_path:str="/"
    language:Language="es"

class CreateCheckoutResponse(StrictModel):
    success:bool=True
    session_id:str=""
    url:str=""

class PaymentVerifyRequest(StrictModel):
    session_id:str=Field("",min_length=1,max_length=500)

class PaymentVerifyResponse(StrictModel):
    success:bool=True
    token:str=""
    expires_at:str=""
    minutes:int=15

class LegalResponse(StrictModel):
    version:str=""
    owner:str=""
    app_name:str=""
    price_usd:float=15.99
    session_minutes:int=15
    independent_service:bool=True
    booking:bool=False
    ticket_sales:bool=False
    independence:str=""
    purpose:str=""
    flight_scope:str=""
    no_booking:str=""
    baggage_scope:str=""
    ai_limits:str=""
    official_source_rule:str=""
    simulation_rule:str=""
    final_authority:str=""
    no_guarantee:str=""
    privacy:str=""
    payment:str=""

class AppMetaResponse(StrictModel):
    success:bool=True
    app_name:str=""
    owner:str=""
    version:str=""
    price_usd:float=15.99
    session_minutes:int=15
    payment_type:str="one_time"
    stripe_enabled:bool=False
    stripe_publishable_key:str=""
    rules_are_verified:bool=False
    language:Language="es"
    independent_service:bool=True

class OfficialSourcesResponse(StrictModel):
    success:bool=True
    sources:List[Dict[str,Any]]=Field(default_factory=list)

class RulesResponse(StrictModel):
    success:bool=True
    version:str=""
    rules:List[Dict[str,Any]]=Field(default_factory=list)
    verified:bool=False
    language:Language="es"

class SourceSearchResponse(StrictModel):
    success:bool=True
    sources:List[SourceRecord]=Field(default_factory=list)

class FlightSourcesResponse(StrictModel):
    success:bool=True
    sources:List[FlightSourceCard]=Field(default_factory=list)
    airline_sources:List[FlightSourceCard]=Field(default_factory=list)
    is_cuba_route:bool=False

class ErrorResponse(StrictModel):
    success:bool=False
    error:str="error"
    message:str=""
