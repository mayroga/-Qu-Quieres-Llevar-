# schemas.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.1.0
from datetime import date
from typing import Any,Dict,List,Optional,Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator

VERSION="8.1.0"
Language=Literal["es","en"]

class StrictModel(BaseModel):
    model_config=ConfigDict(extra="ignore",validate_assignment=True,str_strip_whitespace=True)

class FlightSearchRequest(StrictModel):
    origin:str=""
    destination:str=""
    departure_date:Optional[date]=None
    return_date:Optional[date]=None
    airline:str=""
    cabin:str=""
    fare:str=""
    passengers:int=1
    stops:Optional[int]=None
    language:Language="es"

    @field_validator("origin","destination","airline","cabin","fare",mode="before")
    @classmethod
    def clean_text(cls,v):
        return "" if v is None else str(v).strip()

    @field_validator("departure_date","return_date",mode="before")
    @classmethod
    def clean_date(cls,v):
        if v in (None,"","null","None"):
            return None
        return v

    @field_validator("passengers",mode="before")
    @classmethod
    def clean_passengers(cls,v):
        try:return max(1,int(v))
        except:return 1

    @field_validator("stops",mode="before")
    @classmethod
    def clean_stops(cls,v):
        if v in (None,"","null","None"):return None
        try:return max(0,int(v))
        except:return None

class FlightContext(StrictModel):
    origin:str=""
    destination:str=""
    airline:str=""
    cabin:str=""
    fare:str=""
    passengers:int=1
    stops:Optional[int]=None
    baggage:Dict[str,Any]=Field(default_factory=dict)
    baggage_summary:str=""
    language:Language="es"

class FlightSearchResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    cabin:str=""
    fare:str=""
    passengers:int=1
    stops:Optional[int]=None
    results:List[Dict[str,Any]]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    charter_sources:List[Dict[str,Any]]=Field(default_factory=list)
    airline_sources:List[Dict[str,Any]]=Field(default_factory=list)
    google_flights_url:str=""
    messages:List[str]=Field(default_factory=list)
    errors:List[str]=Field(default_factory=list)
    legal_notice:str=""
    next_action:str=""

class FlightUnderstandResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    origin:str=""
    destination:str=""
    departure_date:str=""
    return_date:str=""
    airline:str=""
    cabin:str=""
    fare:str=""
    passengers:int=1
    stops:Optional[int]=None
    baggage:Dict[str,Any]=Field(default_factory=dict)
    baggage_summary:str=""
    is_cuba_route:bool=False
    understood:Dict[str,Any]=Field(default_factory=dict)
    message:str=""
    important:List[str]=Field(default_factory=list)
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    charter_sources:List[Dict[str,Any]]=Field(default_factory=list)
    airline_sources:List[Dict[str,Any]]=Field(default_factory=list)
    google_flights_url:str=""
    legal_notice:str=""
    next_action:str=""

class FlightSourcesResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    origin:str=""
    destination:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)
    charter_sources:List[Dict[str,Any]]=Field(default_factory=list)
    airline_sources:List[Dict[str,Any]]=Field(default_factory=list)
    is_cuba_route:bool=False
    legal_notice:str=""
    next_action:str=""

class ItemCheckRequest(StrictModel):
    item:str=""
    quantity:float=1
    description:str=""
    baggage_type:str=""
    airline:str=""
    destination:str=""
    origin:str=""
    cabin:str=""
    fare:str=""
    language:Language="es"

    @field_validator(
        "item","description","baggage_type","airline","destination",
        "origin","cabin","fare",mode="before"
    )
    @classmethod
    def clean_item_fields(cls,v):
        return "" if v is None else str(v).strip()

    @field_validator("quantity",mode="before")
    @classmethod
    def clean_quantity(cls,v):
        try:return max(0,float(v))
        except:return 1

class ItemCheckResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    item:str=""
    quantity:float=1
    description:str=""
    category:str=""
    visual_status:str=""
    rule_status:str=""
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
    term:str=""
    language:Language="es"

class TeachTermResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    term:str=""
    title:str=""
    explanation:str=""
    category:str=""
    status:str=""
    source:str=""
    next_action:str=""
    legal_notice:str=""

class GuideRequest(StrictModel):
    language:Language="es"
    flight:Dict[str,Any]=Field(default_factory=dict)
    item:str=""
    baggage_type:str=""
    airline:str=""
    destination:str=""
    origin:str=""
    cabin:str=""
    fare:str=""

    @field_validator("flight",mode="before")
    @classmethod
    def clean_flight(cls,v):
        return {} if v is None else v

class GuideResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    language:Language="es"
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    cuba_steps:List[Dict[str,Any]]=Field(default_factory=list)
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)
    legal_notice:str=""
    next_action:str=""

class AdminLoginRequest(StrictModel):
    username:str=Field(min_length=1)
    password:str=Field(min_length=1)

class AdminLoginResponse(StrictModel):
    success:bool=False
    token:str=""
    expires_in:int=0
    expires_at:Optional[str]=None
    admin:bool=False
    message:str=""

class AdminStatusResponse(StrictModel):
    success:bool=False
    active:bool=False
    admin:bool=False
    expires_at:Optional[str]=None
    message:str=""

class AdminProtectedResponse(StrictModel):
    success:bool=False
    active:bool=False
    admin:bool=False
    message:str=""

class CreateCheckoutRequest(StrictModel):
    return_path:str="/"
    language:Language="es"

class CreateCheckoutResponse(StrictModel):
    success:bool=False
    checkout_url:str=""
    url:str=""
    session_id:str=""
    payment_type:str="one_time"
    price_usd:float=15.99
    session_minutes:int=15
    message:str=""

class PaymentVerifyRequest(StrictModel):
    session_id:str=Field(min_length=1)

class PaymentVerifyResponse(StrictModel):
    success:bool=False
    paid:bool=False
    token:str=""
    service_token:str=""
    expires_in:int=0
    expires_at:Optional[str]=None
    session_minutes:int=15
    message:str=""

class SessionStatusResponse(StrictModel):
    success:bool=True
    active:bool=False
    admin:bool=False
    expires_at:Optional[str]=None
    remaining_seconds:int=0
    message:str=""

class SourceSearchResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    query:str=""
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    count:int=0

class OfficialSourcesResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    sources:List[Dict[str,Any]]=Field(default_factory=list)
    count:int=0
    legal_notice:str=""

class RulesResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    rules:List[Dict[str,Any]]=Field(default_factory=list)
    count:int=0
    legal_notice:str=""

class LegalResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    language:Language="es"
    owner:str="May Roga LLC"
    app_name:str="¿QUÉ QUIERES LLEVAR?"
    price_usd:float=15.99
    session_minutes:int=15
    intro:str=""
    short_notice:str=""
    user_guidance:str=""
    source_notice:str=""
    confirmation_message:str=""
    session_expired_message:str=""
    full_notice:str=""

class AppMetaResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    name:str="¿QUÉ QUIERES LLEVAR?"
    owner:str="May Roga LLC"
    price_usd:float=15.99
    session_minutes:int=15
    payment_type:str="one_time"
    language_default:Language="es"
    supported_languages:List[str]=Field(default_factory=lambda:["es","en"])
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)

class AppConfigResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    app_name:str="¿QUÉ QUIERES LLEVAR?"
    owner:str="May Roga LLC"
    price_usd:float=15.99
    session_minutes:int=15
    payment_type:str="one_time"
    stripe_enabled:bool=False
    language_default:Language="es"
    supported_languages:List[str]=Field(default_factory=lambda:["es","en"])
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)
    legal_notice:str=""

class CubaStep(StrictModel):
    id:str=""
    title:str=""
    description:str=""
    action:str=""
    official_url:str=""
    required:bool=True

class CubaOfficialResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    language:Language="es"
    steps:List[Dict[str,Any]]=Field(default_factory=list)
    official_sources:List[Dict[str,Any]]=Field(default_factory=list)
    legal_notice:str=""
    next_action:str=""

class DeleteSession(StrictModel):
    token:str=""

class DeleteLocal(StrictModel):
    key:str=""

class ErrorResponse(StrictModel):
    success:bool=False
    version:str=VERSION
    error:str=""
    detail:str=""
    message:str=""
    code:str=""

class HealthResponse(StrictModel):
    status:str="ok"
    version:str=VERSION
    app:str="¿QUÉ QUIERES LLEVAR?"
    owner:str="May Roga LLC"

class WebhookResponse(StrictModel):
    success:bool=False
    received:bool=False
    message:str=""
