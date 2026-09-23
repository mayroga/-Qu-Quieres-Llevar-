# rules_engine.py - Motor de Reglas Universales para May Roga LLC
from typing import List, Optional

class RuleStatus:
    ACTIVA = "ACTIVA"
    NO_VERIFICADA = "NO_VERIFICADA"
    SUSPENDIDA = "SUSPENDIDA"

class VerifiedRule:
    def __init__(self, rule_id: str, airline: str, keyword: str, category_visual: str, short_answer: str, status: str, source_name: str, verification_date: str, details: str):
        self.rule_id = rule_id
        self.airline = airline # Puede ser específica o "General" para aplicar a cualquier aerolínea
        self.keyword = keyword
        self.category_visual = category_visual
        self.short_answer = short_answer
        self.status = status
        self.source_name = source_name
        self.verification_date = verification_date
        self.details = details

class RuleRepository:
    def __init__(self):
        # Base de reglas universales que cubre cualquier aerolínea, operador o modalidad (Aérea, Marítima, Terrestre)
        self.rules: List[VerifiedRule] = [
            VerifiedRule(
                rule_id="R-GEN-001",
                airline="General",
                keyword="power bank",
                category_visual="PUEDES LLEVARLO, PERO...",
                short_answer="Las baterías de litio y power banks solo se permiten en el equipaje de mano.",
                status=RuleStatus.ACTIVA,
                source_name="IATA Dangerous Goods Regulations",
                verification_date="2026-01-15",
                details="Prohibido en equipaje documentado (bodega). Los terminales deben estar protegidos contra cortocircuitos."
            ),
            VerifiedRule(
                rule_id="R-GEN-002",
                airline="General",
                keyword="generador",
                category_visual="NO PUEDES LLEVARLO",
                short_answer="Los generadores de energía con motor o tanque de combustible no se pueden transportar como equipaje.",
                status=RuleStatus.ACTIVA,
                source_name="TSA / DOT Hazardous Materials Guidelines",
                verification_date="2026-01-10",
                details="Clasificados como mercancías peligrosas debido al riesgo de inflamabilidad y residuos de combustible."
            ),
            VerifiedRule(
                rule_id="R-AVN-001",
                airline="Avianca",
                keyword="medicamento",
                category_visual="PUEDES LLEVARLO",
                short_answer="Los medicamentos esenciales están permitidos en cabina y equipaje de mano.",
                status=RuleStatus.ACTIVA,
                source_name="Avianca & CBP Travel Guidelines",
                verification_date="2026-01-20",
                details="Se recomienda llevarlos con su respectiva receta o identificación médica visible."
            )
        ]

    def find_rule(self, airline: Optional[str], item_query: str) -> Optional[VerifiedRule]:
        item = item_query.lower()
        target_airline = (airline or "General").strip().lower()
        
        # Primero intenta buscar una regla específica para la aerolínea indicada por el usuario
        for rule in self.rules:
            if rule.keyword in item and rule.airline.lower() == target_airline and rule.status == RuleStatus.ACTIVA:
                return rule
                
        # Si no hay regla específica de aerolínea, busca en las reglas de categoría "General" que aplican a todas
        for rule in self.rules:
            if rule.keyword in item and rule.airline.lower() == "general" and rule.status == RuleStatus.ACTIVA:
                return rule
                
        return None
