# rules_engine.py - Repositorio de reglas y avisos legales
from enum import Enum
from typing import Optional, List

class RuleStatus(Enum):
    ACTIVA = "activa"
    PENDIENTE = "pendiente"

class CargoRule:
    def __init__(self, airline: str, keyword: str, category_visual: str, short_answer: str, details: str, source_name: str, verification_date: str, status: RuleStatus = RuleStatus.ACTIVA):
        self.airline = airline.lower()
        self.keyword = keyword.lower()
        self.category_visual = category_visual
        self.short_answer = short_answer
        self.details = details
        self.source_name = source_name
        self.verification_date = verification_date
        self.status = status

class RuleRepository:
    def __init__(self):
        self.rules: List[CargoRule] = [
            CargoRule(
                airline="general",
                keyword="bateria de litio",
                category_visual="RESTRINGIDO / EQUIPAJE DE MANO",
                short_answer="Las baterías de litio sueltas deben ir obligatoriamente en el equipaje de mano.",
                details="No se permite su transporte en el equipaje facturado (bodega) por normativas de seguridad operacional.",
                source_name="Directrices Internacionales de Transporte Seguro",
                verification_date="2026-01-01"
            ),
            CargoRule(
                airline="avianca",
                keyword="medicamentos",
                category_visual="PERMITIDO",
                short_answer="Los medicamentos esenciales están permitidos en cabina.",
                details="Se recomienda llevar la receta médica correspondiente en caso de cantidades inusuales o líquidos recetados.",
                source_name="Manual de Atención y Carga Avianca",
                verification_date="2026-01-15"
            )
        ]

    def find_rule(self, airline: str, item_description: str) -> Optional[CargoRule]:
        item_lower = item_description.lower()
        airline_lower = airline.lower()
        
        # Buscar coincidencia exacta por aerolínea y palabra clave
        for r in self.rules:
            if r.airline in (airline_lower, "general") and r.keyword in item_lower:
                return r
        return None

class LegalNoticeManager:
    @staticmethod
    def get_intro_explanation() -> str:
        return "Asesoría especializada en condiciones de carga, restricciones y normativas aplicables de forma clara, directa y fundamentada."

    @staticmethod
    def get_official_disclaimer() -> dict:
        return {
            "title": "Aviso de Orientación Profesional",
            "content": "Esta herramienta ofrece orientación basada en normativas públicas y estándares de la industria. No constituye una resolución gubernamental ni sustituye la validación final de la aerolínea u autoridad competente en counter."
        }
