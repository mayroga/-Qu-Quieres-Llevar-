# schemas.py - Modelos Pydantic | ¿QUÉ QUIERES LLEVAR?
# May Roga LLC
# Sin datos personales innecesarios.
# Gemini interpreta/busca vuelos; el motor de reglas decide equipaje.

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# CATEGORÍAS VISUALES
# ============================================================

class CategoryVisualEnum(str, Enum):
    PUEDES_LLEVARLO = "PUEDES LLEVARLO"
    PUEDES_LLEVARLO_PERO = "PUEDES LLEVARLO, PERO..."
    NO_PUEDES_LLEVARLO = "NO PUEDES LLEVARLO"
    NECESITO_MAS_INFORMACION = "NECESITO MÁS INFORMACIÓN"


# ============================================================
# BASE
# ============================================================

class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True
    )


# ============================================================
# STRIPE
# ============================================================

class CheckoutRequest(StrictModel):
    """
    El pago no necesita datos personales.
    Stripe administra la información de pago.
    """
    pass


class ActivateSessionRequest(StrictModel):
    checkout_session_id: str = Field(
        ...,
        min_length=10,
        max_length=300
    )


# ============================================================
# BÚSQUEDA DE VUELOS
# ============================================================

class FlightSearchRequest(StrictModel):
    """
    Consulta en lenguaje natural.

    Ejemplo:
    Miami a La Habana el 15 de diciembre con American Airlines.
    """
    natural_query: str = Field(
        ...,
        min_length=3,
        max_length=1200
    )

    session_token: str = Field(
        ...,
        min_length=20,
        max_length=300
    )


class FlightResult(StrictModel):
    """
    Resultado estructurado de una búsqueda.
    Los campos pueden quedar vacíos si no pudieron verificarse.
    """

    airline: str = Field(default="", max_length=150)
    flight_number: str = Field(default="", max_length=50)

    origin: str = Field(default="", max_length=100)
    destination: str = Field(default="", max_length=100)

    date: str = Field(default="", max_length=50)

    departure_time: str = Field(default="", max_length=50)
    arrival_time: str = Field(default="", max_length=50)

    stops: str = Field(default="", max_length=50)
    route: str = Field(default="", max_length=250)

    source: str = Field(default="", max_length=200)
    url: str = Field(default="", max_length=500)


class FlightSearchResponse(StrictModel):
    status: str
    flights: List[FlightResult] = Field(default_factory=list)
    notice: str = Field(default="", max_length=500)


# ============================================================
# INFORMACIÓN ESTRUCTURADA DEL VUELO
# ============================================================

class FlightContext(StrictModel):
    """
    Información que puede utilizar posteriormente el motor
    determinista de reglas.

    No significa que todos los campos estén disponibles.
    """

    airline: Optional[str] = Field(
        default=None,
        max_length=150
    )

    flight_number: Optional[str] = Field(
        default=None,
        max_length=50
    )

    origin: Optional[str] = Field(
        default=None,
        max_length=100
    )

    destination: Optional[str] = Field(
        default=None,
        max_length=100
    )

    departure_date: Optional[str] = Field(
        default=None,
        max_length=50
    )

    departure_time: Optional[str] = Field(
        default=None,
        max_length=50
    )

    arrival_time: Optional[str] = Field(
        default=None,
        max_length=50
    )

    cabin: Optional[str] = Field(
        default=None,
        max_length=50
    )

    fare: Optional[str] = Field(
        default=None,
        max_length=100
    )

    trip_type: Optional[str] = Field(
        default=None,
        max_length=50
    )

    charter: Optional[bool] = None

    source: Optional[str] = Field(
        default=None,
        max_length=200
    )

    source_url: Optional[str] = Field(
        default=None,
        max_length=500
    )


# ============================================================
# ARTÍCULO / EQUIPAJE
# ============================================================

class BaggageTypeEnum(str, Enum):
    CARRY_ON = "carry_on"
    PERSONAL_ITEM = "personal_item"
    CHECKED = "checked"
    SPECIAL = "special"
    UNKNOWN = "unknown"


class ItemCheckInput(StrictModel):
    """
    Consulta completa de un artículo.

    No exige información que el pasajero todavía no conozca.
    Cuando falta un dato necesario, el motor puede responder
    NECESITO MÁS INFORMACIÓN.
    """

    session_token: str = Field(
        ...,
        min_length=20,
        max_length=300
    )

    item_description: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    airline: Optional[str] = Field(
        default=None,
        max_length=150
    )

    destination: Optional[str] = Field(
        default=None,
        max_length=150
    )

    flight_context: Optional[FlightContext] = None

    baggage_type: BaggageTypeEnum = (
        BaggageTypeEnum.UNKNOWN
    )

    quantity: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000
    )

    weight: Optional[float] = Field(
        default=None,
        ge=0,
        le=10000
    )

    weight_unit: Optional[str] = Field(
        default=None,
        max_length=10
    )

    length: Optional[float] = Field(
        default=None,
        ge=0,
        le=10000
    )

    width: Optional[float] = Field(
        default=None,
        ge=0,
        le=10000
    )

    height: Optional[float] = Field(
        default=None,
        ge=0,
        le=10000
    )

    dimension_unit: Optional[str] = Field(
        default=None,
        max_length=10
    )

    has_battery: Optional[bool] = None

    battery_type: Optional[str] = Field(
        default=None,
        max_length=100
    )

    battery_wh: Optional[float] = Field(
        default=None,
        ge=0,
        le=100000
    )

    lithium_ion: Optional[bool] = None

    liquid: Optional[bool] = None

    liquid_quantity: Optional[float] = Field(
        default=None,
        ge=0,
        le=100000
    )

    liquid_unit: Optional[str] = Field(
        default=None,
        max_length=20
    )

    aerosol: Optional[bool] = None

    food: Optional[bool] = None

    medicine: Optional[bool] = None

    electronic: Optional[bool] = None

    animal: Optional[bool] = None

    medical_equipment: Optional[bool] = None

    dangerous_goods_possible: Optional[bool] = None

    charter: Optional[bool] = None


# ============================================================
# COMPATIBILIDAD CON EL MAIN.PY ACTUAL
# ============================================================

class ItemCheckRequest(StrictModel):
    """
    Modelo utilizado directamente por:
    POST /api/v1/consultar-articulo

    Mantiene compatibilidad con el main.py actual.
    """

    session_token: str = Field(
        ...,
        min_length=20,
        max_length=300
    )

    item_description: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    airline: Optional[str] = Field(
        default=None,
        max_length=150
    )

    destination: Optional[str] = Field(
        default=None,
        max_length=150
    )

    flight_context: Optional[Dict[str, Any]] = None


# ============================================================
# RESPUESTA DE REGLAS
# ============================================================

class OfficialLink(StrictModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=200
    )

    url: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )


class ItemCheckResponse(StrictModel):
    status_category: CategoryVisualEnum

    short_answer: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )

    details: str = Field(
        default="",
        max_length=5000
    )

    source_reference: str = Field(
        default="",
        max_length=1000
    )

    official_links: List[OfficialLink] = Field(
        default_factory=list
    )

    disclaimer: str = Field(
        default="",
        max_length=3000
    )


# ============================================================
# SESIÓN
# ============================================================

class SessionStatusResponse(StrictModel):
    active: bool

    expires_at: str

    remaining_seconds: int = Field(
        ge=0
    )


# ============================================================
# ADMINISTRACIÓN
# ============================================================

class AdminLoginRequest(StrictModel):
    username: str = Field(
        ...,
        min_length=1,
        max_length=200
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=500
    )


class AdminLoginResponse(StrictModel):
    status: str
    session_token: str
    expires_at: str


# ============================================================
# METADATOS DE LA APLICACIÓN
# ============================================================

class AppMetaResponse(StrictModel):
    app_name: str
    version: str
    owner: str
    session_minutes: int
    payment_type: str
    ai_rule_authority: bool
    rules_are_verified: bool
    legal_version: str
