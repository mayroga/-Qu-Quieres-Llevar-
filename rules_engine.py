# rules_engine.py
# ¿QUÉ QUIERES LLEVAR? — Repositorio determinista de reglas
# May Roga LLC
#
# PRINCIPIOS:
# 1. Gemini NO decide reglas.
# 2. Una regla debe estar identificada y verificable.
# 3. Si no existe una regla suficientemente específica -> NO INVENTAR.
# 4. Las reglas pueden depender de aerolínea, destino, tipo de equipaje,
#    fecha, cantidad, peso, dimensiones y características del artículo.
# 5. Las reglas de una aerolínea no se aplican automáticamente a otra.
# 6. Un vuelo CHARTER no utiliza automáticamente las reglas de un vuelo regular.
#
# Este archivo NO pretende contener todas las reglas mundiales.
# Es un repositorio versionado que se amplía únicamente con reglas verificadas.

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any
import re
import unicodedata


# ============================================================
# ESTADOS
# ============================================================

class RuleStatus(str, Enum):
    ACTIVA = "activa"
    PENDIENTE = "pendiente"
    RETIRADA = "retirada"


class CategoryVisualEnum(str, Enum):
    PUEDES_LLEVARLO = "PUEDES LLEVARLO"
    PUEDES_LLEVARLO_PERO = "PUEDES LLEVARLO, PERO..."
    NO_PUEDES_LLEVARLO = "NO PUEDES LLEVARLO"
    NECESITO_MAS_INFORMACION = "NECESITO MÁS INFORMACIÓN"


# ============================================================
# MODELO DE REGLA
# ============================================================

@dataclass
class CargoRule:
    airline: str
    keyword: str
    category_visual: str
    short_answer: str
    details: str

    source_name: str
    source_url: str
    verification_date: str

    status: RuleStatus = RuleStatus.ACTIVA

    # Condiciones opcionales
    destination: Optional[str] = None
    origin: Optional[str] = None
    baggage_type: Optional[str] = None
    cabin: Optional[str] = None

    # Reglas de cantidad/peso/dimensiones
    max_quantity: Optional[float] = None
    quantity_unit: Optional[str] = None

    max_weight_lb: Optional[float] = None
    max_weight_kg: Optional[float] = None

    max_dimensions_linear_in: Optional[float] = None

    # Para baterías
    min_wh: Optional[float] = None
    max_wh: Optional[float] = None

    # Metadatos
    tags: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)

    # Identificador estable
    rule_id: str = ""


# ============================================================
# NORMALIZACIÓN
# ============================================================

def normalize(value: Optional[str]) -> str:
    if not value:
        return ""

    text = str(value).strip().lower()

    text = unicodedata.normalize(
        "NFD",
        text
    )

    text = "".join(
        c for c in text
        if unicodedata.category(c) != "Mn"
    )

    text = re.sub(r"\s+", " ", text)

    return text


def contains_any(text: str, values: List[str]) -> bool:
    normalized = normalize(text)

    return any(
        normalize(value) in normalized
        for value in values
    )


def canonical_airline(value: Optional[str]) -> str:
    value = normalize(value)

    aliases = {
        "american": "american airlines",
        "american airlines": "american airlines",
        "aa": "american airlines",

        "avianca": "avianca",

        "jetblue": "jetblue",
        "jet blue": "jetblue",

        "copa": "copa airlines",
        "copa airlines": "copa airlines",

        "delta": "delta air lines",
        "delta air lines": "delta air lines",

        "united": "united airlines",
        "united airlines": "united airlines",

        "southwest": "southwest airlines",
        "southwest airlines": "southwest airlines",

        "spirit": "spirit airlines",

        "frontier": "frontier airlines",

        "latam": "latam airlines",

        "aeromexico": "aeromexico",

        "volaris": "volaris",

        "viva": "viva",
    }

    return aliases.get(value, value)


def canonical_destination(value: Optional[str]) -> str:
    value = normalize(value)

    aliases = {
        "cuba": "cuba",
        "la habana": "cuba",
        "havana": "cuba",
        "hav": "cuba",

        "miami": "united states",
        "usa": "united states",
        "us": "united states",
        "estados unidos": "united states",
    }

    return aliases.get(value, value)


# ============================================================
# REPOSITORIO
# ============================================================

class RuleRepository:

    VERSION = "2026.09.23"

    def __init__(self):

        self.rules: List[CargoRule] = [

            # ------------------------------------------------
            # AMERICAN AIRLINES — POWER BANK
            # ------------------------------------------------

            CargoRule(
                rule_id="AA-LITHIUM-POWERBANK-100WH-CARRYON",
                airline="american airlines",
                keyword="power bank",
                category_visual=(
                    CategoryVisualEnum.PUEDES_LLEVARLO_PERO.value
                ),
                short_answer=(
                    "Puedes llevar un power bank en el equipaje de mano."
                ),
                details=(
                    "American Airlines indica que los cargadores portátiles "
                    "(power banks) deben viajar en el equipaje de mano y no "
                    "en el equipaje registrado. La regla publicada indica "
                    "hasta 2 por pasajero mientras está a bordo y cada uno "
                    "no debe exceder 100 Wh."
                ),
                source_name="American Airlines — Artículos restringidos",
                source_url=(
                    "https://www.aa.com/web/i18n/travel-info/"
                    "baggage/restricted-items.html?locale=es_US"
                ),
                verification_date="2026-09-23",
                destination=None,
                baggage_type="carry_on",
                max_quantity=2,
                quantity_unit="unidad",
                max_wh=100,
                tags=[
                    "bateria",
                    "litio",
                    "powerbank",
                    "cargador_portatil"
                ],
                conditions=[
                    "Equipaje de mano",
                    "Máximo 2 cargadores portátiles por pasajero",
                    "Cada unidad hasta 100 Wh"
                ]
            ),

            # ------------------------------------------------
            # AMERICAN AIRLINES — LITHIUM SPARE BATTERY
            # ------------------------------------------------

            CargoRule(
                rule_id="AA-LITHIUM-SPARE-BATTERY-CARRYON",
                airline="american airlines",
                keyword="bateria de litio",
                category_visual=(
                    CategoryVisualEnum.PUEDES_LLEVARLO_PERO.value
                ),
                short_answer=(
                    "Las baterías de litio de repuesto deben ir en el "
                    "equipaje de mano y tienen límites específicos."
                ),
                details=(
                    "American Airlines indica que las baterías de litio "
                    "de repuesto deben transportarse en el equipaje de mano "
                    "y estar protegidas individualmente. Los límites "
                    "dependen de los Wh de la batería."
                ),
                source_name="American Airlines — Artículos restringidos",
                source_url=(
                    "https://www.aa.com/web/i18n/travel-info/"
                    "baggage/restricted-items.html?locale=es_US"
                ),
                verification_date="2026-09-23",
                baggage_type="carry_on",
                tags=[
                    "bateria",
                    "litio",
                    "bateria_de_repuesto"
                ],
                conditions=[
                    "Batería de repuesto",
                    "Equipaje de mano",
                    "Protección individual"
                ]
            ),

            # ------------------------------------------------
            # AMERICAN AIRLINES — LARGE LITHIUM POWER SOURCE
            # ------------------------------------------------

            CargoRule(
                rule_id="AA-LARGE-LITHIUM-POWER-SOURCE",
                airline="american airlines",
                keyword="generador de litio",
                category_visual=(
                    CategoryVisualEnum.NO_PUEDES_LLEVARLO.value
                ),
                short_answer=(
                    "Las baterías portátiles grandes y los generadores "
                    "con batería de ion de litio no están permitidos."
                ),
                details=(
                    "American Airlines indica que las baterías portátiles "
                    "grandes y los generadores con batería de ion de litio "
                    "no se permiten en el equipaje de mano ni en el "
                    "equipaje registrado."
                ),
                source_name="American Airlines — Artículos restringidos",
                source_url=(
                    "https://www.aa.com/web/i18n/travel-info/"
                    "baggage/restricted-items.html?locale=es_US"
                ),
                verification_date="2026-09-23",
                tags=[
                    "power_station",
                    "generador",
                    "litio",
                    "bateria"
                ]
            ),

            # ------------------------------------------------
            # AMERICAN AIRLINES — GAS GENERATOR
            # ------------------------------------------------

            CargoRule(
                rule_id="AA-GAS-GENERATOR-CHECKED",
                airline="american airlines",
                keyword="generador de gasolina",
                category_visual=(
                    CategoryVisualEnum.PUEDES_LLEVARLO_PERO.value
                ),
                short_answer=(
                    "Un generador a gasolina puede aceptarse como "
                    "equipaje registrado bajo condiciones específicas."
                ),
                details=(
                    "American Airlines indica que las herramientas y "
                    "generadores a gasolina pueden viajar como equipaje "
                    "registrado solamente si son nuevos o sin uso, están "
                    "en su empaque original en buenas condiciones y no "
                    "funcionan con baterías de ion de litio. No están "
                    "permitidos en el equipaje de mano."
                ),
                source_name="American Airlines — Artículos restringidos",
                source_url=(
                    "https://www.aa.com/web/i18n/travel-info/"
                    "baggage/restricted-items.html?locale=es_US"
                ),
                verification_date="2026-09-23",
                baggage_type="checked",
                tags=[
                    "generador",
                    "gasolina",
                    "combustible",
                    "herramienta"
                ],
                conditions=[
                    "Nuevo o sin uso",
                    "Empaque original",
                    "No funcionar con batería de ion de litio",
                    "Equipaje registrado"
                ]
            ),

            # ------------------------------------------------
            # AMERICAN AIRLINES — CUBA GENERATOR
            # ------------------------------------------------

            CargoRule(
                rule_id="AA-CUBA-GENERATOR",
                airline="american airlines",
                keyword="generador",
                category_visual=(
                    CategoryVisualEnum.PUEDES_LLEVARLO_PERO.value
                ),
                short_answer=(
                    "Para viajes a Cuba, American permite un generador "
                    "nuevo/sin uso en su empaque original como equipaje "
                    "registrado, bajo las condiciones publicadas."
                ),
                details=(
                    "American Airlines indica que para viajar a Cuba se "
                    "permite un generador de energía nuevo/sin uso en el "
                    "empaque original por reservación como artículo "
                    "registrado. Aplican los límites, franquicias y cargos "
                    "de equipaje. Los generadores no pueden llevarse a bordo."
                ),
                source_name="American Airlines — Limitaciones de equipaje",
                source_url=(
                    "https://www.aa.com/web/i18n/travel-info/"
                    "baggage/baggage-limitations.html"
                ),
                verification_date="2026-09-23",
                destination="cuba",
                baggage_type="checked",
                max_quantity=1,
                quantity_unit="generador por reservación",
                tags=[
                    "cuba",
                    "generador",
                    "equipaje_registrado"
                ],
                conditions=[
                    "Destino Cuba",
                    "Uno por reservación",
                    "Nuevo o sin uso",
                    "Empaque original",
                    "Equipaje registrado",
                    "No permitido a bordo"
                ]
            ),

            # ------------------------------------------------
            # AMERICAN AIRLINES — CUBA BAGGAGE
            # ------------------------------------------------

            CargoRule(
                rule_id="AA-CUBA-BAGGAGE-2X70",
                airline="american airlines",
                keyword="equipaje cuba",
                category_visual=(
                    CategoryVisualEnum.PUEDES_LLEVARLO_PERO.value
                ),
                short_answer=(
                    "En vuelos de American hacia/desde Cuba se permiten "
                    "hasta 2 piezas registradas de hasta 70 lb cada una, "
                    "además de 1 equipaje de mano y 1 artículo personal, "
                    "según las condiciones publicadas."
                ),
                details=(
                    "American Airlines publica para Cuba un máximo de "
                    "2 equipajes registrados por pasajero, con un máximo "
                    "de 70 lb / 32 kg por pieza, más 1 equipaje de mano "
                    "y 1 artículo personal. Existen excepciones y cargos "
                    "según fecha, tarifa y dirección del viaje."
                ),
                source_name="American Airlines — Política de equipaje",
                source_url=(
                    "https://www.aa.com/web/i18n/travel-info/"
                    "baggage/checked-baggage-policy.html"
                ),
                verification_date="2026-09-23",
                destination="cuba",
                baggage_type="checked",
                max_quantity=2,
                quantity_unit="pieza",
                max_weight_lb=70,
                max_weight_kg=32,
                tags=[
                    "cuba",
                    "equipaje",
                    "maletas",
                    "equipaje_registrado"
                ],
                conditions=[
                    "Destino u origen Cuba",
                    "Máximo 2 piezas registradas",
                    "Máximo 70 lb / 32 kg por pieza",
                    "1 equipaje de mano",
                    "1 artículo personal",
                    "Pueden existir excepciones de temporada"
                ]
            ),
        ]

    # ========================================================
    # BÚSQUEDA
    # ========================================================

    def find_rule(
        self,
        airline: str,
        item_description: str,
        destination: Optional[str] = None,
        origin: Optional[str] = None,
        baggage_type: Optional[str] = None,
        cabin: Optional[str] = None,
    ) -> Optional[CargoRule]:

        airline_normalized = canonical_airline(airline)
        item_normalized = normalize(item_description)
        destination_normalized = canonical_destination(destination)
        origin_normalized = canonical_destination(origin)
        baggage_normalized = normalize(baggage_type)
        cabin_normalized = normalize(cabin)

        candidates: List[CargoRule] = []

        for rule in self.rules:

            if rule.status != RuleStatus.ACTIVA:
                continue

            rule_airline = canonical_airline(rule.airline)

            # Una regla específica de aerolínea no se aplica a otra.
            if rule_airline not in (
                airline_normalized,
                "general"
            ):
                continue

            # La palabra clave debe aparecer realmente
            # en la descripción.
            if rule.keyword and normalize(rule.keyword) not in item_normalized:

                # Permitir tags como coincidencia.
                if not any(
                    normalize(tag) in item_normalized
                    for tag in rule.tags
                ):
                    continue

            # Destino específico.
            if rule.destination:
                if destination_normalized != normalize(
                    rule.destination
                ):
                    continue

            # Origen específico.
            if rule.origin:
                if origin_normalized != normalize(
                    rule.origin
                ):
                    continue

            # Tipo de equipaje específico.
            if rule.baggage_type and baggage_normalized:
                if baggage_normalized != normalize(
                    rule.baggage_type
                ):
                    continue

            # Si la regla exige un tipo de equipaje y el usuario
            # no lo proporcionó, no debemos inventarlo.
            if rule.baggage_type and not baggage_normalized:
                continue

            # Cabina específica.
            if rule.cabin and cabin_normalized:
                if cabin_normalized != normalize(rule.cabin):
                    continue

            if rule.cabin and not cabin_normalized:
                continue

            candidates.append(rule)

        if not candidates:
            return None

        # Preferir reglas más específicas.
        candidates.sort(
            key=lambda r: (
                1 if r.destination else 0,
                1 if r.origin else 0,
                1 if r.baggage_type else 0,
                1 if r.cabin else 0,
                len(r.tags),
                len(r.keyword)
            ),
            reverse=True
        )

        return candidates[0]

    # ========================================================
    # VALIDACIÓN DE CONDICIONES
    # ========================================================

    def evaluate(
        self,
        airline: str,
        item_description: str,
        destination: Optional[str] = None,
        origin: Optional[str] = None,
        baggage_type: Optional[str] = None,
        cabin: Optional[str] = None,
        quantity: Optional[float] = None,
        weight_lb: Optional[float] = None,
        weight_kg: Optional[float] = None,
        watt_hours: Optional[float] = None,
        charter: bool = False,
    ) -> Dict[str, Any]:

        # Nunca aplicar automáticamente una regla de vuelo regular
        # a un charter.
        if charter:
            return self._unknown(
                reason=(
                    "El vuelo fue identificado como charter. "
                    "Las reglas de un vuelo regular no se aplican "
                    "automáticamente a un charter."
                )
            )

        rule = self.find_rule(
            airline=airline,
            item_description=item_description,
            destination=destination,
            origin=origin,
            baggage_type=baggage_type,
            cabin=cabin
        )

        if not rule:
            return self._unknown(
                reason=(
                    "No existe una regla activa suficientemente "
                    "específica para los datos proporcionados."
                )
            )

        # ----------------------------------------------------
        # CANTIDAD
        # ----------------------------------------------------

        if (
            rule.max_quantity is not None
            and quantity is not None
            and quantity > rule.max_quantity
        ):
            return {
                "status_category": (
                    CategoryVisualEnum.NO_PUEDES_LLEVARLO.value
                ),
                "short_answer": (
                    f"La cantidad indicada supera el límite "
                    f"verificado de {rule.max_quantity:g} "
                    f"{rule.quantity_unit or 'unidad(es)'}."
                ),
                "details": rule.details,
                "rule_id": rule.rule_id,
                "source_reference": self.source_reference(rule),
                "official_links": [
                    {
                        "title": rule.source_name,
                        "url": rule.source_url
                    }
                ]
            }

        # ----------------------------------------------------
        # PESO
        # ----------------------------------------------------

        if (
            rule.max_weight_lb is not None
            and weight_lb is not None
            and weight_lb > rule.max_weight_lb
        ):
            return {
                "status_category": (
                    CategoryVisualEnum.NO_PUEDES_LLEVARLO.value
                ),
                "short_answer": (
                    f"El peso indicado supera el límite verificado "
                    f"de {rule.max_weight_lb:g} lb."
                ),
                "details": rule.details,
                "rule_id": rule.rule_id,
                "source_reference": self.source_reference(rule),
                "official_links": [
                    {
                        "title": rule.source_name,
                        "url": rule.source_url
                    }
                ]
            }

        if (
            rule.max_weight_kg is not None
            and weight_kg is not None
            and weight_kg > rule.max_weight_kg
        ):
            return {
                "status_category": (
                    CategoryVisualEnum.NO_PUEDES_LLEVARLO.value
                ),
                "short_answer": (
                    f"El peso indicado supera el límite verificado "
                    f"de {rule.max_weight_kg:g} kg."
                ),
                "details": rule.details,
                "rule_id": rule.rule_id,
                "source_reference": self.source_reference(rule),
                "official_links": [
                    {
                        "title": rule.source_name,
                        "url": rule.source_url
                    }
                ]
            }

        # ----------------------------------------------------
        # WH
        # ----------------------------------------------------

        if (
            rule.max_wh is not None
            and watt_hours is not None
            and watt_hours > rule.max_wh
        ):
            return {
                "status_category": (
                    CategoryVisualEnum.NO_PUEDES_LLEVARLO.value
                ),
                "short_answer": (
                    f"La batería indicada supera el límite "
                    f"verificado de {rule.max_wh:g} Wh."
                ),
                "details": rule.details,
                "rule_id": rule.rule_id,
                "source_reference": self.source_reference(rule),
                "official_links": [
                    {
                        "title": rule.source_name,
                        "url": rule.source_url
                    }
                ]
            }

        # ----------------------------------------------------
        # REGLA VERIFICADA
        # ----------------------------------------------------

        return {
            "status_category": rule.category_visual,
            "short_answer": rule.short_answer,
            "details": rule.details,
            "rule_id": rule.rule_id,
            "source_reference": self.source_reference(rule),
            "official_links": [
                {
                    "title": rule.source_name,
                    "url": rule.source_url
                }
            ],
            "conditions": rule.conditions
        }

    # ========================================================
    # RESPUESTA NO VERIFICADA
    # ========================================================

    @staticmethod
    def _unknown(reason: str) -> Dict[str, Any]:

        return {
            "status_category": (
                CategoryVisualEnum.NECESITO_MAS_INFORMACION.value
            ),
            "short_answer": (
                "No encontramos una regla verificada suficiente "
                "para darte una respuesta segura."
            ),
            "details": (
                reason
                + " La aplicación no inventará una autorización "
                "ni una prohibición."
            ),
            "rule_id": None,
            "source_reference": "Regla no verificada",
            "official_links": []
        }

    # ========================================================
    # FUENTE
    # ========================================================

    @staticmethod
    def source_reference(rule: CargoRule) -> str:

        return (
            f"{rule.source_name} "
            f"(verificado {rule.verification_date})"
        )

    # ========================================================
    # METADATOS
    # ========================================================

    def list_active_rules(self) -> List[Dict[str, Any]]:

        result = []

        for rule in self.rules:

            if rule.status != RuleStatus.ACTIVA:
                continue

            result.append(
                {
                    "rule_id": rule.rule_id,
                    "airline": rule.airline,
                    "keyword": rule.keyword,
                    "status": rule.status.value,
                    "source_name": rule.source_name,
                    "source_url": rule.source_url,
                    "verification_date": rule.verification_date
                }
            )

        return result

    def source_registry(self) -> List[Dict[str, str]]:

        seen = set()
        sources = []

        for rule in self.rules:

            key = rule.source_url

            if key in seen:
                continue

            seen.add(key)

            sources.append(
                {
                    "name": rule.source_name,
                    "url": rule.source_url,
                    "verification_date": rule.verification_date
                }
            )

        return sources
