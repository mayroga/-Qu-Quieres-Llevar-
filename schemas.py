# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v6.0.0
from typing import Any,Dict,List,Literal,Optional
from pydantic import BaseModel,ConfigDict,Field,field_validator
from enum import Enum

Language=Literal["es","en"]

class StrictModel(BaseModel):
    model_config=ConfigDict(extra="ignore",str_strip_whitespace=True,validate_assignment=True)

class CategoryVisualEnum(str,Enum):
    ALLOW="PUEDES LLEVARLO"
    ALLOW_WITH_CONDITION="PUEDES LLEVARLO, PERO..."
    NOT_ALLOWED="NO PUEDES LLEVARLO"
    REVIEW="REVISA ESTO ANTES DE VIAJAR"

class BaggageTypeEnum(str,Enum):
    PERSONAL_ITEM="personal_item"
    CARRY_ON="carry_on"
    CHECKED="checked"
    UNKNOWN="unknown"

class RuleStatusEnum(str,Enum):
    ACTIVE="active"
    PENDING="pending"
    EXPIRED="expired"

class FlightSearchRequest(StrictModel):
    origin:Optional[str]=Field(default=None,min_length=2,max_length=120)
    destination:Optional[str]=Field(default=None,min_length=2,max_length=120)
    departure_date:Optional[str]=Field(default=None,max_length=30)
    return_date:Optional[str]=Field(default=None,max_length=30)
    passengers:int=Field(default=1,ge=1,le=20)
    cabin:Optional[str]=Field(default=None,max_length=50)
    language:Language="es"

class FlightResult(StrictModel):
    id:str=Field(min_length=1,max_length=150)
    airline:Optional[str]=Field(default=None,max_length=150)
    flight_number:Optional[str]=Field(default=None,max_length=50)
    origin:Optional[str]=Field(default=None,max_length=120)
    destination:Optional[str]=Field(default=None,max_length=120)
    departure:Optional[str]=Field(default=None,max_length=80)
    arrival:Optional[str]=Field(default=None,max_length=80)
    date:Optional[str]=Field(default=None,max_length=30)
    direct:Optional[bool]=None
    stops:Optional[int]=Field(default=None,ge=0,le=20)
    connection:Optional[bool]=None
    connection_airport:Optional[str]=Field(default=None,max_length=150)
    connection_duration:Optional[str]=Field(default=None,max_length=80)
    passengers:Optional[int]=Field(default=None,ge=1,le=20)
    cabin:Optional[str]=Field(default=None,max_length=80)
    fare:Optional[str]=Field(default=None,max_length=120)
    currency:Optional[str]=Field(default=None,max_length=3)
    baggage_summary:Optional[str]=Field(default=None,max_length=1000)
    source:Optional[str]=Field(default=None,max_length=1000)
    verified:bool=False
    verified_at:Optional[str]=None
    official_source:bool=False
    conditions:List[str]=Field(default_factory=list)

    @field_validator("currency")
    @classmethod
    def currency_upper(cls,v):
        return v.upper() if v else v

class FlightSearchResponse(StrictModel):
    success:bool=True
    results:List[FlightResult]=Field(default_factory=list)
    message:Optional[str]=None
    source:Optional[str]=None
    verified:bool=False
    official_source:bool=False
    next_action:Optional[str]=None

class FlightContext(StrictModel):
    airline:Optional[str]=Field(default=None,max_length=150)
    flight_number:Optional[str]=Field(default=None,max_length=50)
    origin:Optional[str]=Field(default=None,max_length=120)
    destination:Optional[str]=Field(default=None,max_length=120)
    departure_date:Optional[str]=Field(default=None,max_length=30)
    departure_time:Optional[str]=Field(default=None,max_length=50)
    arrival_time:Optional[str]=Field(default=None,max_length=50)
    direct:Optional[bool]=None
    stops:Optional[int]=Field(default=None,ge=0,le=20)
    connection:Optional[bool]=None
    connection_airport:Optional[str]=Field(default=None,max_length=150)
    connection_duration:Optional[str]=Field(default=None,max_length=80)
    passengers:Optional[int]=Field(default=None,ge=1,le=20)
    cabin:Optional[str]=Field(default=None,max_length=80)
    fare:Optional[str]=Field(default=None,max_length=120)
    baggage:Optional[Dict[str,Any]]=None
    source:Optional[str]=None
    verified:bool=False
    verified_at:Optional[str]=None

class ItemCheckInput(StrictModel):
    item:str=Field(min_length=1,max_length=300)
    category:Optional[str]=Field(default=None,max_length=100)
    quantity:Optional[int]=Field(default=None,ge=1,le=100)
    weight:Optional[float]=Field(default=None,ge=0,le=1000)
    weight_unit:Optional[str]=Field(default=None,max_length=10)
    dimensions:Optional[str]=Field(default=None,max_length=100)
    description:Optional[str]=Field(default=None,max_length=1000)

class ItemCheckRequest(StrictModel):
    item:str=Field(min_length=1,max_length=300)
    language:Language="es"
    flight:Optional[FlightContext]=None
    baggage_type:Optional[BaggageTypeEnum]=None
    quantity:Optional[int]=Field(default=None,ge=1,le=100)
    weight:Optional[float]=Field(default=None,ge=0,le=1000)
    weight_unit:Optional[str]=Field(default=None,max_length=10)
    dimensions:Optional[str]=Field(default=None,max_length=100)
    category:Optional[str]=Field(default=None,max_length=100)
    description:Optional[str]=Field(default=None,max_length=1000)

class OfficialLink(StrictModel):
    name:str=Field(min_length=1,max_length=150)
    url:str=Field(min_length=1,max_length=2000)
    description:Optional[str]=Field(default=None,max_length=1000)
    authority:Optional[str]=Field(default=None,max_length=150)
    country:Optional[str]=Field(default=None,max_length=100)
    verified:bool=False
    verified_at:Optional[str]=None

class ItemCheckResponse(StrictModel):
    success:bool=True
    item:str
    category:CategoryVisualEnum
    explanation:str
    baggage_place:Optional[str]=None
    conditions:List[str]=Field(default_factory=list)
    missing_information:List[str]=Field(default_factory=list)
    source:Optional[str]=None
    source_name:Optional[str]=None
    verified:bool=False
    verification_date:Optional[str]=None
    official_link:Optional[OfficialLink]=None
    next_action:Optional[str]=None
    legal_notice:Optional[str]=None

class TeachTermRequest(StrictModel):
    term:str=Field(min_length=1,max_length=150)
    language:Language="es"

class TeachTermResponse(StrictModel):
    success:bool=True
    term:str
    explanation:str
    example:Optional[str]=None
    next_action:Optional[str]=None

class GuideRequest(StrictModel):
    language:Language="es"
    topic:Optional[str]=Field(default=None,max_length=150)
    flight:Optional[FlightContext]=None

class GuideResponse(StrictModel):
    success:bool=True
    title:str
    steps:List[str]=Field(default_factory=list)
    next_action:Optional[str]=None
    official_links:List[OfficialLink]=Field(default_factory=list)

class SessionStatusResponse(StrictModel):
    active:bool
    token:Optional[str]=None
    remaining_seconds:int=Field(default=0,ge=0)
    expires_at:Optional[str]=None
    message:Optional[str]=None

class AdminLoginRequest(StrictModel):
    username:str=Field(min_length=1,max_length=150)
    password:str=Field(min_length=1,max_length=300)

class AdminLoginResponse(StrictModel):
    success:bool
    token:Optional[str]=None
    message:Optional[str]=None

class CreateCheckoutRequest(StrictModel):
    language:Language="es"
    return_path:Optional[str]=Field(default=None,max_length=500)

class CreateCheckoutResponse(StrictModel):
    success:bool
    checkout_url:Optional[str]=None
    session_id:Optional[str]=None
    message:Optional[str]=None

class PaymentVerifyRequest(StrictModel):
    session_id:str=Field(min_length=1,max_length=300)

class PaymentVerifyResponse(StrictModel):
    success:bool
    paid:bool=False
    service_token:Optional[str]=None
    expires_at:Optional[str]=None
    message:Optional[str]=None

class LegalResponse(StrictModel):
    success:bool=True
    version:str
    owner:str
    app_name:str
    notice:str
    short_notice:Optional[str]=None
    source_notice:Optional[str]=None

class AppMetaResponse(StrictModel):
    app_name:str
    version:str
    owner:str
    session_minutes:int=Field(ge=1)
    payment_type:str
    price_usd:Optional[float]=Field(default=None,ge=0)
    ai_rule_authority:str
    rules_are_verified:bool=False
    legal_version:str
    independent_service:bool=True
    booking_enabled:bool=False
    ticket_sales_enabled:bool=False

class OfficialSourcesResponse(StrictModel):
    success:bool=True
    sources:List[OfficialLink]=Field(default_factory=list)

class ErrorResponse(StrictModel):
    success:bool=False
    message:str
    code:Optional[str]=None
    next_action:Optional[str]=None
