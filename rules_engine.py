# rules_engine.py — QU-QUIERES-LLEVAR | May Roga LLC | v6.0.0
from dataclasses import dataclass,field
from enum import Enum
from typing import Any,Dict,List,Optional
import re

class RuleStatus(str,Enum):
    ACTIVE="ACTIVE"
    PENDING="PENDING"
    EXPIRED="EXPIRED"

class RuleCategory(str,Enum):
    BAGGAGE="baggage"
    PERSONAL_ITEM="personal_item"
    CARRY_ON="carry_on"
    CHECKED="checked"
    BATTERY="battery"
    LIQUID="liquid"
    AEROSOL="aerosol"
    MEDICINE="medicine"
    FOOD="food"
    ELECTRONICS="electronics"
    MEDICAL="medical"
    ANIMAL="animal"
    SPORTS="sports"
    SPECIAL="special"
    DOCUMENT="document"
    FLIGHT="flight"
    CONNECTION="connection"
    DESTINATION="destination"
    OTHER="other"

@dataclass
class SourceRecord:
    name:str
    url:str
    verified_date:Optional[str]=None
    scope:str=""
    notes:str=""

@dataclass
class CargoRule:
    id:str
    airline:str
    keyword:str
    category:str
    status:RuleStatus
    answer:str
    details:str=""
    source:Optional[SourceRecord]=None
    verification_date:Optional[str]=None
    baggage_place:Optional[str]=None
    route_origin:Optional[str]=None
    route_destination:Optional[str]=None
    cabin:Optional[str]=None
    fare:Optional[str]=None
    conditions:List[str]=field(default_factory=list)

    def matches(
        self,
        text:str,
        airline:Optional[str]=None,
        origin:Optional[str]=None,
        destination:Optional[str]=None,
        cabin:Optional[str]=None,
        fare:Optional[str]=None
    )->bool:
        if self.status!=RuleStatus.ACTIVE:
            return False
        text=_norm(text)
        key=_norm(self.keyword)
        if not key or key not in text:
            return False
        if self.airline and _norm(self.airline)!="general":
            if not airline or _norm(self.airline) not in _norm(airline):
                return False
        if self.route_origin and (not origin or _norm(self.route_origin) not in _norm(origin)):
            return False
        if self.route_destination and (not destination or _norm(self.route_destination) not in _norm(destination)):
            return False
        if self.cabin and (not cabin or _norm(self.cabin)!=_norm(cabin)):
            return False
        if self.fare and (not fare or _norm(self.fare)!=_norm(fare)):
            return False
        return True

def _norm(value:Any)->str:
    value=str(value or "").strip().lower()
    value=re.sub(r"\s+"," ",value)
    return value

class RuleRepository:
    def __init__(self,rules:Optional[List[CargoRule]]=None):
        self.rules=rules if rules is not None else self._default_rules()

    def _default_rules(self)->List[CargoRule]:
        return [
            CargoRule(
                id="battery_general_pending",
                airline="general",
                keyword="bateria de litio",
                category=RuleCategory.BATTERY.value,
                status=RuleStatus.PENDING,
                answer="REVISA ESTO ANTES DE VIAJAR",
                details="Las baterías de litio pueden tener condiciones especiales según su tipo, capacidad, cantidad y dónde viajan.",
                source=None
            ),
            CargoRule(
                id="power_bank_general_pending",
                airline="general",
                keyword="power bank",
                category=RuleCategory.BATTERY.value,
                status=RuleStatus.PENDING,
                answer="REVISA ESTO ANTES DE VIAJAR",
                details="Un power bank puede estar sujeto a reglas específicas. Confirma la capacidad y la ubicación permitida con la aerolínea y la autoridad aplicable.",
                source=None
            ),
            CargoRule(
                id="medicine_general_pending",
                airline="general",
                keyword="medicamentos",
                category=RuleCategory.MEDICINE.value,
                status=RuleStatus.PENDING,
                answer="REVISA ESTO ANTES DE VIAJAR",
                details="Los medicamentos pueden tener reglas diferentes según el país, la aerolínea, el tipo de medicamento y el viaje.",
                source=None
            ),
            CargoRule(
                id="liquid_general_pending",
                airline="general",
                keyword="liquidos",
                category=RuleCategory.LIQUID.value,
                status=RuleStatus.PENDING,
                answer="REVISA ESTO ANTES DE VIAJAR",
                details="Los líquidos pueden estar sujetos a límites y condiciones según el aeropuerto, la autoridad, la ruta y dónde se transporten.",
                source=None
            ),
            CargoRule(
                id="aerosol_general_pending",
                airline="general",
                keyword="aerosol",
                category=RuleCategory.AEROSOL.value,
                status=RuleStatus.PENDING,
                answer="REVISA ESTO ANTES DE VIAJAR",
                details="Los aerosoles pueden tener restricciones específicas. Debe revisarse el tipo de producto y la regla oficial aplicable.",
                source=None
            )
        ]

    def add_rule(self,rule:CargoRule)->None:
        if not isinstance(rule,CargoRule):
            raise TypeError("rule debe ser CargoRule")
        self.rules.append(rule)

    def find_rule(
        self,
        text:str,
        airline:Optional[str]=None,
        origin:Optional[str]=None,
        destination:Optional[str]=None,
        cabin:Optional[str]=None,
        fare:Optional[str]=None
    )->Optional[CargoRule]:
        matches=[
            r for r in self.rules
            if r.matches(text,airline,origin,destination,cabin,fare)
        ]
        if not matches:
            return None
        matches.sort(key=lambda r:self._specificity(r,airline,origin,destination,cabin,fare),reverse=True)
        return matches[0]

    def _specificity(
        self,
        rule:CargoRule,
        airline:Optional[str],
        origin:Optional[str],
        destination:Optional[str],
        cabin:Optional[str],
        fare:Optional[str]
    )->int:
        score=0
        if rule.airline and _norm(rule.airline)!="general": score+=10
        if rule.route_origin and origin: score+=5
        if rule.route_destination and destination: score+=5
        if rule.cabin and cabin: score+=3
        if rule.fare and fare: score+=3
        score+=min(len(_norm(rule.keyword)),20)
        return score

    def search(
        self,
        text:str,
        airline:Optional[str]=None,
        category:Optional[str]=None
    )->List[CargoRule]:
        text=_norm(text)
        airline=_norm(airline)
        category=_norm(category)
        result=[]
        for rule in self.rules:
            if rule.status!=RuleStatus.ACTIVE:
                continue
            if rule.keyword and _norm(rule.keyword) not in text:
                continue
            if airline and _norm(rule.airline)!="general" and _norm(rule.airline) not in airline:
                continue
            if category and _norm(rule.category)!=category:
                continue
            result.append(rule)
        return result

    def find_rule_data(self,*args,**kwargs)->Optional[Dict[str,Any]]:
        rule=self.find_rule(*args,**kwargs)
        return self.to_dict(rule) if rule else None

    def to_dict(self,rule:Optional[CargoRule])->Optional[Dict[str,Any]]:
        if not rule:
            return None
        source=None
        if rule.source:
            source={
                "name":rule.source.name,
                "url":rule.source.url,
                "verified_date":rule.source.verified_date,
                "scope":rule.source.scope,
                "notes":rule.source.notes
            }
        return {
            "id":rule.id,
            "airline":rule.airline,
            "keyword":rule.keyword,
            "category":rule.category,
            "status":rule.status.value,
            "answer":rule.answer,
            "details":rule.details,
            "source":source,
            "verification_date":rule.verification_date,
            "baggage_place":rule.baggage_place,
            "route_origin":rule.route_origin,
            "route_destination":rule.route_destination,
            "cabin":rule.cabin,
            "fare":rule.fare,
            "conditions":list(rule.conditions)
        }

    def active_rules(self)->List[CargoRule]:
        return [r for r in self.rules if r.status==RuleStatus.ACTIVE]

    def pending_rules(self)->List[CargoRule]:
        return [r for r in self.rules if r.status==RuleStatus.PENDING]

    def clear(self)->None:
        self.rules.clear()

    def count(self)->Dict[str,int]:
        return {
            "total":len(self.rules),
            "active":len(self.active_rules()),
            "pending":len(self.pending_rules()),
            "expired":len([r for r in self.rules if r.status==RuleStatus.EXPIRED])
        }

class BaggageAdvisor:
    """
    Capa de explicación humana.
    No inventa límites ni transforma una regla pendiente en una regla confirmada.
    """

    PERSONAL_TERMS=("articulo personal","artículo personal","personal item","mochila pequeña")
    CARRY_TERMS=("equipaje de mano","equipaje de cabina","carry on","carry-on","carryon","maleta de cabina")
    CHECKED_TERMS=("equipaje documentado","equipaje facturado","maleta documentada","maleta facturada","checked baggage","checked bag","maleta registrada")
    CONNECTION_TERMS=("escala","conexion","conexión","stop","estancia","connection")

    @classmethod
    def explain_term(cls,text:str)->Optional[Dict[str,str]]:
        q=_norm(text)
        if any(x in q for x in cls.PERSONAL_TERMS):
            return {
                "term":"ARTÍCULO PERSONAL",
                "simple":"Es el bolso o mochila pequeña que la aerolínea permite llevar contigo.",
                "next":"Revisa las medidas exactas de tu aerolínea y de tu tarifa."
            }
        if any(x in q for x in cls.CARRY_TERMS):
            return {
                "term":"EQUIPAJE DE MANO",
                "simple":"Es la maleta que llevas contigo dentro del avión.",
                "next":"Revisa peso, medidas y cantidad permitida por tu aerolínea y tarifa."
            }
        if any(x in q for x in cls.CHECKED_TERMS):
            return {
                "term":"EQUIPAJE DOCUMENTADO",
                "simple":"Es la maleta que entregas a la aerolínea antes de subir al avión y que viaja en la bodega.",
                "next":"Revisa cantidad, peso, medidas y posible costo según tu tarifa."
            }
        if any(x in q for x in cls.CONNECTION_TERMS):
            return {
                "term":"ESCALA O CONEXIÓN",
                "simple":"Es una parada antes de llegar a tu destino final.",
                "next":"Debes revisar si cambias de avión, cuánto dura la conexión y qué ocurre con tu equipaje."
            }
        return None

    @classmethod
    def item_category(cls,text:str)->str:
        q=_norm(text)
        groups={
            RuleCategory.BATTERY.value:("bateria","batería","power bank","litio","lithium"),
            RuleCategory.LIQUID.value:("liquido","líquido","liquids"),
            RuleCategory.AEROSOL.value:("aerosol","spray"),
            RuleCategory.MEDICINE.value:("medicina","medicamento","medicamentos","medicine"),
            RuleCategory.FOOD.value:("comida","alimento","alimentos","food"),
            RuleCategory.ELECTRONICS.value:("telefono","teléfono","computadora","laptop","tablet","electrónico"),
            RuleCategory.MEDICAL.value:("equipo medico","equipo médico","medical equipment"),
            RuleCategory.ANIMAL.value:("animal","mascota","pet"),
            RuleCategory.SPORTS.value:("bicicleta","bicicletas","deporte","sports"),
        }
        for category,terms in groups.items():
            if any(term in q for term in terms):
                return category
        return RuleCategory.OTHER.value

    @classmethod
    def advise(
        cls,
        repository:RuleRepository,
        item:str,
        airline:Optional[str]=None,
        origin:Optional[str]=None,
        destination:Optional[str]=None,
        cabin:Optional[str]=None,
        fare:Optional[str]=None
    )->Dict[str,Any]:
        item=_norm(item)
        term=cls.explain_term(item)
        category=cls.item_category(item)
        rule=repository.find_rule(item,airline,origin,destination,cabin,fare)

        response={
            "category":category,
            "visual_status":"NECESITO MÁS INFORMACIÓN",
            "title":"REVISEMOS TU ARTÍCULO",
            "simple_explanation":term,
            "rule":None,
            "source":None,
            "next_action":{
                "title":"CONFIRMA LA INFORMACIÓN OFICIAL",
                "message":"Busca la regla de tu aerolínea para este artículo, tu vuelo y tu tarifa."
            }
        }

        if rule:
            response["rule"]=repository.to_dict(rule)
            response["visual_status"]=rule.answer or "REVISA ESTO ANTES DE VIAJAR"
            if rule.source:
                response["source"]=repository.to_dict(rule)["source"]
            return response

        return response

DEFAULT_RULE_REPOSITORY=RuleRepository()
rule_repo=DEFAULT_RULE_REPOSITORY
rules_engine=DEFAULT_RULE_REPOSITORY

def find_rule(
    text:str,
    airline:Optional[str]=None,
    origin:Optional[str]=None,
    destination:Optional[str]=None,
    cabin:Optional[str]=None,
    fare:Optional[str]=None
)->Optional[CargoRule]:
    return DEFAULT_RULE_REPOSITORY.find_rule(
        text,airline,origin,destination,cabin,fare
    )

def advise_item(
    item:str,
    airline:Optional[str]=None,
    origin:Optional[str]=None,
    destination:Optional[str]=None,
    cabin:Optional[str]=None,
    fare:Optional[str]=None
)->Dict[str,Any]:
    return BaggageAdvisor.advise(
        DEFAULT_RULE_REPOSITORY,
        item,
        airline,
        origin,
        destination,
        cabin,
        fare
    )

__all__=[
    "RuleStatus",
    "RuleCategory",
    "SourceRecord",
    "CargoRule",
    "RuleRepository",
    "BaggageAdvisor",
    "DEFAULT_RULE_REPOSITORY",
    "rule_repo",
    "rules_engine",
    "find_rule",
    "advise_item"
]
