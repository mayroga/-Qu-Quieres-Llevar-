# rules_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v7.0.0
from dataclasses import dataclass,field
from enum import Enum
from typing import Any,Dict,List,Optional
import re,unicodedata

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

class VisualStatus(str,Enum):
    ALLOW="PUEDES LLEVARLO"
    ALLOW_WITH_CONDITION="PUEDES LLEVARLO, PERO..."
    NOT_ALLOWED="NO PUEDES LLEVARLO"
    REVIEW="REVISA ESTO ANTES DE VIAJAR"

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
        q=_norm(text)
        key=_norm(self.keyword)
        if not key or not _contains(q,key):
            return False
        if self.airline and _norm(self.airline)!="general":
            if not airline or not _contains(_norm(airline),_norm(self.airline)):
                return False
        if self.route_origin:
            if not origin or not _contains(_norm(origin),_norm(self.route_origin)):
                return False
        if self.route_destination:
            if not destination or not _contains(_norm(destination),_norm(self.route_destination)):
                return False
        if self.cabin:
            if not cabin or _norm(cabin)!=_norm(self.cabin):
                return False
        if self.fare:
            if not fare or _norm(fare)!=_norm(self.fare):
                return False
        return True

def _norm(value:Any)->str:
    value=str(value or "").strip().lower()
    value=unicodedata.normalize("NFD",value)
    value="".join(c for c in value if unicodedata.category(c)!="Mn")
    value=re.sub(r"[-_/]+"," ",value)
    value=re.sub(r"\s+"," ",value)
    return value.strip()

def _contains(text:str,term:str)->bool:
    text=_norm(text)
    term=_norm(term)
    if not term:
        return False
    return term in text

def _first(*values):
    for value in values:
        if value not in (None,"",[],{}):
            return value
    return None

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
                answer=VisualStatus.REVIEW.value,
                details="Las baterías de litio pueden tener condiciones especiales según su tipo, capacidad, cantidad y lugar de transporte. La condición exacta debe verificarse con la fuente aplicable.",
                conditions=["Tipo de batería","Capacidad","Cantidad","Lugar donde se transporta"]
            ),
            CargoRule(
                id="power_bank_general_pending",
                airline="general",
                keyword="power bank",
                category=RuleCategory.BATTERY.value,
                status=RuleStatus.PENDING,
                answer=VisualStatus.REVIEW.value,
                details="Un power bank puede estar sujeto a reglas específicas. Deben revisarse su capacidad, cantidad y ubicación permitida según la aerolínea y la autoridad aplicable.",
                conditions=["Capacidad","Cantidad","Equipaje permitido"]
            ),
            CargoRule(
                id="medicine_general_pending",
                airline="general",
                keyword="medicamentos",
                category=RuleCategory.MEDICINE.value,
                status=RuleStatus.PENDING,
                answer=VisualStatus.REVIEW.value,
                details="Los medicamentos pueden tener reglas diferentes según el medicamento, el país, la aerolínea y el tipo de viaje.",
                conditions=["Tipo de medicamento","País de destino","Documentación si corresponde"]
            ),
            CargoRule(
                id="liquid_general_pending",
                airline="general",
                keyword="liquidos",
                category=RuleCategory.LIQUID.value,
                status=RuleStatus.PENDING,
                answer=VisualStatus.REVIEW.value,
                details="Los líquidos pueden estar sujetos a condiciones diferentes según el aeropuerto, la autoridad, el tipo de equipaje y el producto.",
                conditions=["Tipo de líquido","Cantidad","Tipo de equipaje","Control de seguridad"]
            ),
            CargoRule(
                id="aerosol_general_pending",
                airline="general",
                keyword="aerosol",
                category=RuleCategory.AEROSOL.value,
                status=RuleStatus.PENDING,
                answer=VisualStatus.REVIEW.value,
                details="Los aerosoles pueden tener restricciones específicas según el producto y el lugar donde se transporten.",
                conditions=["Tipo de aerosol","Cantidad","Tipo de equipaje"]
            ),
            CargoRule(
                id="food_general_pending",
                airline="general",
                keyword="comida",
                category=RuleCategory.FOOD.value,
                status=RuleStatus.PENDING,
                answer=VisualStatus.REVIEW.value,
                details="La posibilidad de llevar alimentos puede depender tanto de las reglas de transporte como de las reglas de entrada del país de destino.",
                conditions=["Tipo de alimento","País de destino","Forma de transporte"]
            ),
            CargoRule(
                id="animal_general_pending",
                airline="general",
                keyword="mascota",
                category=RuleCategory.ANIMAL.value,
                status=RuleStatus.PENDING,
                answer=VisualStatus.REVIEW.value,
                details="Los animales y mascotas requieren revisar las condiciones de la aerolínea y las autoridades del origen y destino.",
                conditions=["Tipo de animal","Aerolínea","País de destino","Documentación"]
            ),
            CargoRule(
                id="medical_equipment_general_pending",
                airline="general",
                keyword="equipo medico",
                category=RuleCategory.MEDICAL.value,
                status=RuleStatus.PENDING,
                answer=VisualStatus.REVIEW.value,
                details="Los equipos médicos pueden tener condiciones especiales según el dispositivo, sus baterías, la aerolínea y el destino.",
                conditions=["Tipo de equipo","Batería","Aerolínea","Destino"]
            )
        ]

    def add_rule(self,rule:CargoRule)->None:
        if not isinstance(rule,CargoRule):
            raise TypeError("rule debe ser CargoRule")
        self.rules.append(rule)

    def add_rules(self,rules:List[CargoRule])->None:
        for rule in rules:
            self.add_rule(rule)

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
        matches.sort(
            key=lambda r:self._specificity(
                r,airline,origin,destination,cabin,fare
            ),
            reverse=True
        )
        return matches[0]

    def find_pending(
        self,
        text:str,
        airline:Optional[str]=None,
        category:Optional[str]=None
    )->Optional[CargoRule]:
        q=_norm(text)
        a=_norm(airline)
        c=_norm(category)
        candidates=[]
        for rule in self.rules:
            if rule.status!=RuleStatus.PENDING:
                continue
            if rule.keyword and not _contains(q,rule.keyword):
                continue
            if a and _norm(rule.airline)!="general" and not _contains(a,rule.airline):
                continue
            if c and _norm(rule.category)!=c:
                continue
            candidates.append(rule)
        if not candidates:
            return None
        candidates.sort(key=lambda r:len(_norm(r.keyword)),reverse=True)
        return candidates[0]

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
        if rule.airline and _norm(rule.airline)!="general":
            score+=100
        if rule.route_origin and origin:
            score+=30
        if rule.route_destination and destination:
            score+=30
        if rule.cabin and cabin:
            score+=15
        if rule.fare and fare:
            score+=15
        score+=min(len(_norm(rule.keyword)),30)
        return score

    def search(
        self,
        text:str,
        airline:Optional[str]=None,
        category:Optional[str]=None
    )->List[CargoRule]:
        q=_norm(text)
        a=_norm(airline)
        c=_norm(category)
        result=[]
        for rule in self.rules:
            if rule.status!=RuleStatus.ACTIVE:
                continue
            if rule.keyword and not _contains(q,rule.keyword):
                continue
            if a and _norm(rule.airline)!="general" and not _contains(a,rule.airline):
                continue
            if c and _norm(rule.category)!=c:
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
            "verification_date":rule.verification_date or (rule.source.verified_date if rule.source else None),
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

    def expired_rules(self)->List[CargoRule]:
        return [r for r in self.rules if r.status==RuleStatus.EXPIRED]

    def count(self,status:Optional[str]=None)->Any:
        counts={
            "total":len(self.rules),
            "active":len(self.active_rules()),
            "pending":len(self.pending_rules()),
            "expired":len(self.expired_rules())
        }
        if status:
            key=str(status).lower()
            return counts.get(key,0)
        return counts

    def clear(self)->None:
        self.rules.clear()

class BaggageAdvisor:
    PERSONAL_TERMS=(
        "articulo personal","personal item","mochila pequeña",
        "mochila pequena","bolso personal","bolso"
    )
    CARRY_TERMS=(
        "equipaje de mano","equipaje de cabina","carry on",
        "carry-on","carryon","maleta de cabina","cabina"
    )
    CHECKED_TERMS=(
        "equipaje documentado","equipaje facturado",
        "maleta documentada","maleta facturada",
        "checked baggage","checked bag","maleta registrada"
    )
    CONNECTION_TERMS=(
        "escala","conexion","stop","estancia","connection"
    )

    @classmethod
    def explain_term(cls,text:str,language:str="es")->Optional[Dict[str,str]]:
        q=_norm(text)
        en=_norm(language)=="en"
        if any(_contains(q,x) for x in cls.PERSONAL_TERMS):
            return {
                "term":"PERSONAL ITEM" if en else "ARTÍCULO PERSONAL",
                "simple":"It is the small bag or personal item allowed by the airline." if en else "Es el bolso o artículo pequeño que la aerolínea permite llevar contigo.",
                "next":"Check the exact dimensions and conditions for your airline and fare." if en else "Revisa las medidas exactas y las condiciones de tu aerolínea y tarifa."
            }
        if any(_contains(q,x) for x in cls.CARRY_TERMS):
            return {
                "term":"CARRY-ON BAG" if en else "EQUIPAJE DE MANO",
                "simple":"It is the bag you carry with you into the aircraft." if en else "Es la maleta que llevas contigo dentro del avión.",
                "next":"Check the exact weight, dimensions and quantity allowed by your airline and fare." if en else "Revisa peso, medidas y cantidad permitida por tu aerolínea y tarifa."
            }
        if any(_contains(q,x) for x in cls.CHECKED_TERMS):
            return {
                "term":"CHECKED BAG" if en else "EQUIPAJE DOCUMENTADO",
                "simple":"It is the bag you give to the airline before boarding." if en else "Es la maleta que entregas a la aerolínea antes de subir al avión.",
                "next":"Check quantity, weight, dimensions and possible charges for your fare." if en else "Revisa cantidad, peso, medidas y posible costo según tu tarifa."
            }
        if any(_contains(q,x) for x in cls.CONNECTION_TERMS):
            return {
                "term":"CONNECTION" if en else "ESCALA O CONEXIÓN",
                "simple":"It is a stop before reaching your final destination." if en else "Es una parada antes de llegar a tu destino final.",
                "next":"Check whether you change aircraft, connection time and baggage handling." if en else "Revisa si cambias de avión, cuánto dura la conexión y qué ocurre con tu equipaje."
            }
        return None

    @classmethod
    def item_category(cls,text:str)->str:
        q=_norm(text)
        groups={
            RuleCategory.BATTERY.value:(
                "bateria","baterias","power bank","litio","lithium",
                "bateria externa","bateria portatil","pila","pilas"
            ),
            RuleCategory.LIQUID.value:(
                "liquido","liquidos","liquid","shampoo","perfume",
                "crema","gel","gel de cabello"
            ),
            RuleCategory.AEROSOL.value:(
                "aerosol","spray","desodorante aerosol"
            ),
            RuleCategory.MEDICINE.value:(
                "medicina","medicamento","medicamentos","medicine",
                "medication","pastillas"
            ),
            RuleCategory.FOOD.value:(
                "comida","alimento","alimentos","food","carne",
                "queso","fruta","frutas"
            ),
            RuleCategory.ELECTRONICS.value:(
                "telefono","telefono celular","celular","computadora",
                "laptop","tablet","electronico","electronica",
                "camera","camara","reloj inteligente"
            ),
            RuleCategory.MEDICAL.value:(
                "equipo medico","medical equipment","concentrador",
                "oxigeno","oxygen","dispositivo medico"
            ),
            RuleCategory.ANIMAL.value:(
                "animal","mascota","pet","perro","gato"
            ),
            RuleCategory.SPORTS.value:(
                "bicicleta","bicicletas","deporte","sports",
                "equipo deportivo"
            ),
            RuleCategory.DOCUMENT.value:(
                "pasaporte","documento","documentos","visa",
                "identificacion","identificacion personal"
            )
        }
        for category,terms in groups.items():
            if any(_contains(q,term) for term in terms):
                return category
        return RuleCategory.OTHER.value

    @classmethod
    def _flight_values(cls,flight:Optional[Dict[str,Any]])->Dict[str,Any]:
        flight=flight or {}
        return {
            "airline":_first(
                flight.get("airline"),
                flight.get("airline_name")
            ),
            "origin":_first(
                flight.get("origin"),
                flight.get("departure_airport"),
                flight.get("route_origin")
            ),
            "destination":_first(
                flight.get("destination"),
                flight.get("arrival_airport"),
                flight.get("route_destination")
            ),
            "cabin":flight.get("cabin"),
            "fare":flight.get("fare")
        }

    @classmethod
    def advise(
        cls,
        repository_or_item,
        item:Optional[str]=None,
        airline:Optional[str]=None,
        origin:Optional[str]=None,
        destination:Optional[str]=None,
        cabin:Optional[str]=None,
        fare:Optional[str]=None,
        flight:Optional[Dict[str,Any]]=None,
        baggage_type:Optional[str]=None,
        language:str="es",
        **kwargs
    )->Dict[str,Any]:
        repository=repository_or_item if isinstance(repository_or_item,RuleRepository) else DEFAULT_RULE_REPOSITORY
        if isinstance(repository_or_item,RuleRepository):
            text=item or ""
        else:
            text=str(repository_or_item or "")

        values=cls._flight_values(flight)
        airline=_first(airline,values["airline"])
        origin=_first(origin,values["origin"])
        destination=_first(destination,values["destination"])
        cabin=_first(cabin,values["cabin"])
        fare=_first(fare,values["fare"])

        q=_norm(text)
        category=cls.item_category(q)
        explanation=cls.explain_term(q,language)

        rule=repository.find_rule(
            q,airline,origin,destination,cabin,fare
        )

        pending=repository.find_pending(
            q,airline,category
        )

        lang_en=_norm(language)=="en"

        response={
            "category":category,
            "visual_status":VisualStatus.REVIEW.value,
            "title":"REVIEW YOUR ITEM" if lang_en else "REVISEMOS TU ARTÍCULO",
            "simple_explanation":explanation,
            "rule":None,
            "source":None,
            "source_name":None,
            "verified":False,
            "verification_date":None,
            "baggage_place":baggage_type,
            "conditions":[],
            "missing_information":[],
            "next_action":{
                "title":"CONFIRM OFFICIAL INFORMATION" if lang_en else "CONFIRMA LA INFORMACIÓN OFICIAL",
                "message":(
                    "Confirm the rule for this item, airline, route and fare on the applicable official source."
                    if lang_en else
                    "Confirma la regla de este artículo, aerolínea, ruta y tarifa en la fuente oficial aplicable."
                )
            }
        }

        if airline:
            response["conditions"].append(
                "Airline: "+str(airline)
            )
        else:
            response["missing_information"].append(
                "airline" if lang_en else "aerolínea"
            )

        if origin:
            response["conditions"].append(
                "Origin: "+str(origin) if lang_en else "Origen: "+str(origin)
            )
        else:
            response["missing_information"].append(
                "origin" if lang_en else "origen"
            )

        if destination:
            response["conditions"].append(
                "Destination: "+str(destination) if lang_en else "Destino: "+str(destination)
            )
        else:
            response["missing_information"].append(
                "destination" if lang_en else "destino"
            )

        if baggage_type:
            response["conditions"].append(
                "Baggage type: "+str(baggage_type) if lang_en else "Tipo de equipaje: "+str(baggage_type)
            )

        if rule:
            data=repository.to_dict(rule) or {}
            response["rule"]=data
            response["visual_status"]=data.get("answer") or VisualStatus.REVIEW.value
            response["verified"]=data.get("status")=="ACTIVE"
            response["verification_date"]=data.get("verification_date")
            response["baggage_place"]=data.get("baggage_place") or baggage_type
            response["conditions"].extend(data.get("conditions") or [])
            if data.get("source"):
                response["source"]=data["source"].get("url")
                response["source_name"]=data["source"].get("name")
            if data.get("details"):
                response["details"]=data["details"]
            response["next_action"]={
                "title":"CONTINÚA CON TU PREPARACIÓN" if not lang_en else "CONTINUE PREPARING",
                "message":(
                    "Esta respuesta procede de una regla registrada y verificada. Revisa siempre la fuente antes de viajar."
                    if not lang_en else
                    "This response comes from a registered and verified rule. Always review the source before traveling."
                )
            }
            return response

        if pending:
            data=repository.to_dict(pending) or {}
            response["rule"]=data
            response["visual_status"]=VisualStatus.REVIEW.value
            response["conditions"].extend(data.get("conditions") or [])
            response["details"]=data.get("details","")
            response["missing_information"].append(
                "official verified rule" if lang_en else "regla oficial verificada"
            )
            return response

        response["details"]=(
            "No hay una regla específica verificada en el registro actual para esta consulta. La aplicación no inventa una respuesta. Primero identifica la aerolínea, ruta, tipo de equipaje y condiciones aplicables y después confirma la fuente oficial."
            if not lang_en else
            "There is no specific verified rule currently registered for this request. The application does not invent an answer. First identify the airline, route, baggage type and applicable conditions, then confirm the official source."
        )
        return response

    @classmethod
    def advise_item(
        cls,
        item:str,
        airline:Optional[str]=None,
        origin:Optional[str]=None,
        destination:Optional[str]=None,
        cabin:Optional[str]=None,
        fare:Optional[str]=None,
        flight:Optional[Dict[str,Any]]=None,
        baggage_type:Optional[str]=None,
        language:str="es"
    )->Dict[str,Any]:
        return cls.advise(
            DEFAULT_RULE_REPOSITORY,
            item=item,
            airline=airline,
            origin=origin,
            destination=destination,
            cabin=cabin,
            fare=fare,
            flight=flight,
            baggage_type=baggage_type,
            language=language
        )

DEFAULT_RULE_REPOSITORY=RuleRepository()
rule_repo=DEFAULT_RULE_REPOSITORY
rules_engine=DEFAULT_RULE_REPOSITORY
advisor=BaggageAdvisor()

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
    fare:Optional[str]=None,
    flight:Optional[Dict[str,Any]]=None,
    baggage_type:Optional[str]=None,
    language:str="es"
)->Dict[str,Any]:
    return BaggageAdvisor.advise_item(
        item=item,
        airline=airline,
        origin=origin,
        destination=destination,
        cabin=cabin,
        fare=fare,
        flight=flight,
        baggage_type=baggage_type,
        language=language
    )

__all__=[
    "RuleStatus",
    "RuleCategory",
    "VisualStatus",
    "SourceRecord",
    "CargoRule",
    "RuleRepository",
    "BaggageAdvisor",
    "DEFAULT_RULE_REPOSITORY",
    "rule_repo",
    "rules_engine",
    "advisor",
    "find_rule",
    "advise_item"
]
