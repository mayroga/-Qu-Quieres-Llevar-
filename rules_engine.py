# rules_engine.py - Motor de Reglas Verificadas para May Roga LLC
from typing import List, Optional

class RuleStatus:
    ACTIVA = "ACTIVA"
    NO_VERIFICADA = "NO_VERIFICADA"
    VENCIDA = "VENCIDA"
    REEMPLAZADA = "REEMPLAZADA"
    SUSPENDIDA = "SUSPENDIDA"

class VerifiedRule:
    def __init__(self, rule_id: str, airline: str, keyword: str, category_visual: str, short_answer: str, status: str, source_name: str, verification_date: str, details: str):
        self.rule_id = rule_id
        self.airline = airline
        self.keyword = keyword
        self.category_visual = category_visual
        self.short_answer = short_answer
        self.status = status
        self.source_name = source_name
        self.verification_date = verification_date
        self.details = details

class RuleRepository:
    def __init__(self):
        # Base de reglas estrictamente verificadas (Principio: Si no está verificado, no se presenta como hecho)
        self.rules: List[VerifiedRule] = [
            VerifiedRule(
                rule_id="R-001",
                airline="American Airlines",
                keyword="power bank",
                category_visual="PUEDES LLEVARLO, PERO...",
                short_answer="Solo puedes llevar power banks y baterías de litio en tu EQUIPAJE DE MANO.",
                status=RuleStatus.ACTIVA,
                source_name="IATA Dangerous Goods & American Airlines Guidelines",
                verification_date="2026-01-15",
                details="Prohibido en equipaje documentado (bodega). Los terminales deben estar protegidos contra cortocircuitos."
            ),
            VerifiedRule(
                rule_id="R-002",
                airline="General",
                keyword="generador",
                category_visual="NO PUEDES LLEVARLO",
                short_answer="Los generadores de energía con motor o tanque de combustible NO se pueden transportar.",
                status=RuleStatus.ACTIVA,
                source_name="FAA / TSA Hazardous Materials Prohibition",
                verification_date="2026-01-10",
                details="Constituyen mercancías peligrosas prohibidas por riesgo de inflamabilidad y residuos de combustible."
            )
        ]

    def find_rule(self, airline: str, item_query: str) -> Optional[VerifiedRule]:
        for rule in self.rules:
            if rule.keyword in item_query:
                if rule.airline.lower() == airline.lower() or rule.airline.lower() == "general":
                    if rule.status == RuleStatus.ACTIVA:
                        return rule
        return None
