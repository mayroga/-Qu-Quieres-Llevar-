# rules_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.0
from dataclasses import dataclass,asdict
from enum import Enum
from typing import Any,Dict,List,Optional
import unicodedata

VERSION="8.0.0"

class VisualStatus(str,Enum):
    ALLOW="PUEDES LLEVARLO"
    ALLOW_WITH_CONDITION="PUEDES LLEVARLO, PERO..."
    NOT_ALLOWED="NO PUEDES LLEVARLO"
    REVIEW="REVISA ESTO ANTES DE VIAJAR"

class RuleStatus(str,Enum):
    ACTIVE="active"
    PENDING="pending"
    EXPIRED="expired"

@dataclass
class Rule:
    id:str
    term:str
    keywords:List[str]
    status:str=RuleStatus.PENDING.value
    visual_status:str=VisualStatus.REVIEW.value
    explanation_es:str=""
    explanation_en:str=""
    place_es:str=""
    place_en:str=""
    conditions_es:List[str]=None
    conditions_en:List[str]=None
    missing_information_es:List[str]=None
    missing_information_en:List[str]=None
    source:str=""
    source_name:str=""
    verified:bool=False
    verification_date:Optional[str]=None
    airline:Optional[str]=None
    destination:Optional[str]=None
    baggage_types:List[str]=None
    notes_es:str=""
    notes_en:str=""
    def __post_init__(self):
        self.conditions_es=self.conditions_es or []
        self.conditions_en=self.conditions_en or []
        self.missing_information_es=self.missing_information_es or []
        self.missing_information_en=self.missing_information_en or []
        self.baggage_types=self.baggage_types or []
    def to_dict(self)->Dict[str,Any]:
        return asdict(self)

class RuleRepository:
    VERSION=VERSION
    def __init__(self,rules:Optional[List[Rule]]=None):
        self._rules={}
        for rule in rules or self._default_rules():self.add(rule)

    def add(self,rule:Rule)->Rule:
        self._rules[rule.id]=rule
        return rule

    def get(self,rule_id:str)->Optional[Rule]:
        return self._rules.get(rule_id)

    def all(self)->List[Rule]:
        return list(self._rules.values())

    def to_dicts(self,status:Optional[str]=None)->List[Dict[str,Any]]:
        if status:
            status=str(status).lower()
            return [r.to_dict() for r in self.all() if str(r.status).lower()==status]
        return [r.to_dict() for r in self.all()]

    def count(self,status:Optional[str]=None):
        if status is None:return len(self._rules)
        return sum(1 for r in self.all() if str(r.status).lower()==str(status).lower())

    def search(self,text:str)->List[Rule]:
        q=_norm(text)
        if not q:return []
        out=[]
        for r in self.all():
            hay=" ".join([r.id,r.term,r.explanation_es,r.explanation_en,*r.keywords])
            if q in _norm(hay) or any(q in _norm(k) for k in r.keywords):out.append(r)
        return out

    def _default_rules(self)->List[Rule]:
        return [
            Rule(
                "power_bank","POWER BANK",["power bank","bateria externa","batería externa","cargador portatil","cargador portátil","portable charger"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Un power bank es una batería de repuesto. Su forma de transporte depende de las reglas vigentes, la capacidad de la batería, la aerolínea y el itinerario.",
                "A power bank is a spare battery. How it must travel depends on current rules, battery capacity, the airline and the itinerary.",
                "Normalmente requiere una revisión específica antes de viajar.","It normally requires a specific review before travel.",
                ["Confirma la capacidad de la batería.","Confirma dónde debe transportarse.","Confirma la regla de tu aerolínea para este viaje."],
                ["Confirm the battery capacity.","Confirm where it must be carried.","Confirm your airline's rule for this trip."],
                ["la capacidad de la batería","la aerolínea","el itinerario"],
                ["battery capacity","airline","itinerary"],
                "https://www.faa.gov/hazmat/packsafe/airline-passengers-and-batteries",
                "FAA — Airline Passengers and Batteries",True,"2026-10-01",
                notes_es="La regla general no debe sustituir una condición más restrictiva de la aerolínea.",
                notes_en="The general rule must not replace a more restrictive airline condition."
            ),
            Rule(
                "spare_lithium_battery","BATERÍA DE REPUESTO",["bateria de repuesto","batería de repuesto","spare battery","lithium battery","bateria litio","batería litio"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Una batería de repuesto puede estar sujeta a reglas especiales. Hay que conocer el tipo y la capacidad antes de decidir cómo transportarla.",
                "A spare battery may have special transportation rules. The type and capacity must be known before deciding how to carry it.",
                "Requiere revisión según tipo y capacidad.","Requires review based on type and capacity.",
                ["Identifica el tipo de batería.","Busca la capacidad indicada en la batería o documentación.","Confirma la regla de la aerolínea."],
                ["Identify the battery type.","Find the capacity shown on the battery or documentation.","Confirm the airline rule."],
                ["tipo de batería","capacidad","aerolínea"],
                ["battery type","capacity","airline"],
                "https://www.faa.gov/hazmat/packsafe/airline-passengers-and-batteries",
                "FAA — Airline Passengers and Batteries",True,"2026-10-01"
            ),
            Rule(
                "medications","MEDICAMENTOS",["medicamento","medicamentos","medicine","medication","pills","pastillas","prescription","receta"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Los medicamentos pueden tener condiciones distintas según el país, el tipo de medicamento, la cantidad y la documentación.",
                "Medication may have different conditions depending on the country, medicine type, quantity and documentation.",
                "Lleva los medicamentos de forma que puedas identificarlos y revisa los requisitos del viaje.","Carry medication so it can be identified and review the trip requirements.",
                ["Confirma las reglas del país de destino.","Revisa si el medicamento necesita documentación especial.","Confirma las condiciones de seguridad y de la aerolínea."],
                ["Confirm destination-country rules.","Check whether the medicine requires special documentation.","Confirm security and airline conditions."],
                ["país de destino","tipo de medicamento","cantidad"],
                ["destination country","medicine type","quantity"],
                "https://www.tsa.gov/travel/security-screening/whatcanibring/all-list",
                "TSA — What Can I Bring",True,"2026-10-01"
            ),
            Rule(
                "liquids","LÍQUIDOS",["liquido","líquidos","liquids","gel","geles","crema","creams","shampoo","champu","champú"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Los líquidos, geles y productos similares pueden tener condiciones específicas según el tipo de artículo, el control de seguridad y el viaje.",
                "Liquids, gels and similar products may have specific conditions depending on the item, security screening and trip.",
                "Revisa la regla aplicable antes de preparar la bolsa.","Review the applicable rule before packing.",
                ["Identifica exactamente qué líquido es.","Confirma el tamaño del recipiente permitido para tu situación.","Revisa si existe una excepción aplicable."],
                ["Identify exactly what the liquid is.","Confirm the permitted container size for your situation.","Check whether an applicable exception exists."],
                ["tipo de líquido","cantidad","envase"],
                ["liquid type","quantity","container"],
                "https://www.tsa.gov/travel/security-screening/whatcanibring/all-list",
                "TSA — What Can I Bring",True,"2026-10-01"
            ),
            Rule(
                "aerosols","AEROSOLES",["aerosol","aerosoles","spray","sprays","desodorante spray","hairspray"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Los aerosoles pueden tener restricciones que dependen del producto y de dónde se transporte.",
                "Aerosols may have restrictions depending on the product and where it is transported.",
                "Revisa el producto concreto antes de empacarlo.","Review the exact product before packing it.",
                ["Identifica el producto.","Comprueba si es inflamable u otro material regulado.","Revisa la regla de seguridad y de la aerolínea."],
                ["Identify the product.","Check whether it is flammable or another regulated material.","Review security and airline rules."],
                ["tipo de producto","contenido","ubicación en el equipaje"],
                ["product type","contents","baggage location"],
                "https://www.faa.gov/hazmat/packsafe",
                "FAA — PackSafe",True,"2026-10-01"
            ),
            Rule(
                "food","ALIMENTOS",["comida","alimento","alimentos","food","foods","carne","meat","queso","cheese","fruta","fruit"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Que un alimento pueda pasar el control de seguridad no significa necesariamente que pueda entrar al país de destino.",
                "An item passing security does not necessarily mean it may be imported into the destination country.",
                "Hay que revisar seguridad y también las reglas de entrada del destino.","Security and destination-entry rules must both be reviewed.",
                ["Identifica el alimento.","Revisa la regla de seguridad.","Revisa las reglas de entrada del país de destino."],
                ["Identify the food.","Review the security rule.","Review destination-country entry rules."],
                ["tipo de alimento","país de destino","cantidad"],
                ["food type","destination country","quantity"],
                "https://www.tsa.gov/travel/security-screening/whatcanibring/all-list",
                "TSA — What Can I Bring",True,"2026-10-01"
            ),
            Rule(
                "pets","ANIMALES",["animal","animales","mascota","mascotas","pet","pets","perro","dog","gato","cat"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Viajar con un animal puede requerir reglas de aerolínea, aeropuerto y país de destino.",
                "Traveling with an animal may require airline, airport and destination-country rules.",
                "No debe asumirse que una mascota puede viajar simplemente porque existe una opción de transporte.","Do not assume a pet can travel simply because a transport option exists.",
                ["Identifica el animal.","Confirma la política de la aerolínea.","Confirma los requisitos del país de destino."],
                ["Identify the animal.","Confirm the airline policy.","Confirm destination-country requirements."],
                ["animal","aerolínea","destino"],
                ["animal","airline","destination"],
                "https://www.tsa.gov/travel/security-screening/whatcanibring/all-list",
                "TSA — What Can I Bring",True,"2026-10-01"
            ),
            Rule(
                "medical_equipment","EQUIPO MÉDICO",["equipo medico","equipo médico","medical equipment","medical device","cpap","wheelchair","silla de ruedas"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Los equipos médicos pueden tener reglas especiales y algunas condiciones dependen de la aerolínea y del dispositivo.",
                "Medical equipment may have special rules, with some conditions depending on the airline and device.",
                "Requiere identificar el equipo y confirmar las condiciones del viaje.","The equipment must be identified and the trip conditions confirmed.",
                ["Identifica el equipo.","Revisa si usa baterías.","Confirma las condiciones de la aerolínea."],
                ["Identify the equipment.","Check whether it uses batteries.","Confirm airline conditions."],
                ["tipo de equipo","batería","aerolínea"],
                ["equipment type","battery","airline"],
                "https://www.faa.gov/hazmat/packsafe",
                "FAA — PackSafe",True,"2026-10-01"
            ),
            Rule(
                "documents","DOCUMENTOS",["documento","documentos","passport","pasaporte","visa","identificacion","identificación","id"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Los documentos de viaje dependen de la persona, destino, nacionalidad, ruta y propósito del viaje.",
                "Travel documents depend on the traveler, destination, nationality, route and purpose of travel.",
                "Los documentos deben revisarse con la autoridad correspondiente.","Documents must be reviewed with the applicable authority.",
                ["Identifica el destino.","Determina qué documento tienes.","Confirma los requisitos oficiales de entrada."],
                ["Identify the destination.","Determine which document you have.","Confirm official entry requirements."],
                ["destino","nacionalidad o situación de viaje","documento"],
                ["destination","nationality or travel situation","document"],
                "",
                "Fuente oficial correspondiente",False,None
            ),
            Rule(
                "cash","DINERO EN EFECTIVO",["dinero","efectivo","cash","money","currency","moneda"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "El transporte y la declaración de dinero pueden depender del país de salida, tránsito y destino y de la cantidad transportada.",
                "Transport and declaration requirements for cash may depend on the departure, transit and destination countries and amount carried.",
                "Debe revisarse la regla del itinerario completo.","The rule for the complete itinerary must be reviewed.",
                ["Identifica la cantidad aproximada.","Revisa los países del itinerario.","Confirma si existe una obligación de declaración."],
                ["Identify the approximate amount.","Review the countries on the itinerary.","Confirm whether a declaration is required."],
                ["cantidad","países del itinerario"],
                ["amount","itinerary countries"],
                "",
                "Autoridad oficial correspondiente",False,None
            ),
            Rule(
                "electronics","EQUIPOS ELECTRÓNICOS",["electronico","electrónico","electronics","computer","computadora","laptop","telefono","teléfono","phone","tablet"],
                RuleStatus.PENDING.value,VisualStatus.REVIEW.value,
                "Los dispositivos electrónicos pueden viajar con el pasajero, pero las condiciones pueden cambiar según el dispositivo, sus baterías, el equipaje y la aerolínea.",
                "Electronic devices may travel with the passenger, but conditions can vary by device, batteries, baggage and airline.",
                "Revisa el dispositivo y especialmente si contiene baterías.","Review the device, especially whether it contains batteries.",
                ["Identifica el dispositivo.","Comprueba si contiene batería de litio.","Confirma la regla de la aerolínea si corresponde."],
                ["Identify the device.","Check whether it contains a lithium battery.","Confirm the airline rule when applicable."],
                ["dispositivo","batería","aerolínea"],
                ["device","battery","airline"],
                "https://www.faa.gov/hazmat/packsafe/airline-passengers-and-batteries",
                "FAA — Airline Passengers and Batteries",True,"2026-10-01"
            )
        ]

rule_repo=RuleRepository()

def _norm(value:Any)->str:
    s=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode("ascii").lower()
    return " ".join(s.split())

def _contains(text:str,*terms:str)->bool:
    n=_norm(text)
    return any(_norm(x) in n for x in terms)

class BaggageAdvisor:
    VERSION=VERSION

    TERM_EXPLANATIONS_ES={
        "equipaje de mano":"Es la maleta o bolsa que llevas contigo dentro del avión, siempre que tu tarifa y aerolínea permitan llevarla.",
        "equipaje de cabina":"Es el equipaje que viaja contigo en la cabina del avión. Las medidas, peso y cantidad dependen de la aerolínea y tarifa.",
        "articulo personal":"Es una pieza pequeña que puede viajar contigo cuando la tarifa y aerolínea la permiten. El tamaño exacto depende de la regla aplicable.",
        "equipaje documentado":"Es la maleta que entregas antes de subir al avión para que viaje en la bodega.",
        "equipaje facturado":"Es otra forma de referirse al equipaje que entregas a la aerolínea para viajar en la bodega.",
        "carry on":"Es el equipaje que llevas contigo en la cabina. La cantidad y medidas dependen de la aerolínea y tarifa.",
        "checked baggage":"Es el equipaje que entregas a la aerolínea para que viaje en la bodega.",
        "escala":"Es una parada durante el viaje antes de llegar al destino final.",
        "conexion":"Es cuando tu viaje continúa hacia otro vuelo. Puede implicar cambiar de avión y debes revisar qué ocurre con tu equipaje.",
        "stop":"Es una parada o escala indicada en el itinerario. El significado exacto depende de cómo aparezca en el viaje.",
        "estancia":"Es un tiempo en el que permaneces en un lugar antes de continuar el viaje, según las condiciones del itinerario.",
        "tarifa":"Es el tipo de precio o producto del boleto que determina, entre otras cosas, qué condiciones y servicios están incluidos.",
        "cabina":"Es la clase de servicio del vuelo, por ejemplo económica o ejecutiva. Las condiciones dependen de la aerolínea y tarifa."
    }

    TERM_EXPLANATIONS_EN={
        "carry on":"It is baggage you take with you into the aircraft cabin. The airline and fare determine whether it is included and its limits.",
        "personal item":"It is a small item that may travel with you when the airline and fare allow it. Exact size depends on the applicable rule.",
        "checked baggage":"It is baggage you hand to the airline before boarding so it travels in the aircraft hold.",
        "connection":"It means your journey continues on another flight. You may change aircraft and must check what happens to your baggage.",
        "stop":"It is a stop during the itinerary. Its exact meaning depends on how it is shown in the itinerary.",
        "fare":"It is the ticket product or price type that determines included services and conditions.",
        "cabin":"It is the service class of the flight. Conditions depend on the airline and fare.",
        "liquids":"Liquids and gels may have specific security conditions depending on the item and travel situation.",
        "power bank":"A power bank is a spare battery and may have special rules based on capacity, airline and itinerary."
    }

    def explain_term(self,text:str,language="es")->Dict[str,Any]:
        n=_norm(text)
        if language=="en":
            for key,value in self.TERM_EXPLANATIONS_EN.items():
                if n==_norm(key) or _contains(n,key):
                    return {"term":text,"explanation":value,"example":None,"next_action":"Check the exact baggage rule for your airline and fare."}
            return {"term":text,"explanation":"This term describes a travel or baggage condition that may depend on the airline, fare, route or item.","example":None,"next_action":"Find the term in your flight details and confirm the applicable official rule."}
        for key,value in self.TERM_EXPLANATIONS_ES.items():
            if n==_norm(key) or _contains(n,key):
                return {"term":text,"explanation":value,"example":None,"next_action":"Ahora revisemos la regla exacta de tu aerolínea y tarifa."}
        return {"term":text,"explanation":"Este término describe una condición de viaje o equipaje que puede depender de la aerolínea, tarifa, ruta o artículo.","example":None,"next_action":"Busca este término en los detalles de tu vuelo y confirma la regla oficial que corresponde."}

    def item_category(self,item:str)->str:
        n=_norm(item)
        if _contains(n,"power bank","bateria externa","bateria de repuesto","spare battery","lithium battery","bateria litio"):return "battery"
        if _contains(n,"medicamento","medicamentos","medicine","medication","pastilla","prescription","receta"):return "medication"
        if _contains(n,"liquido","liquidos","liquid","gel","crema","shampoo","champu","champú"):return "liquid"
        if _contains(n,"aerosol","spray","desodorante spray","hairspray"):return "aerosol"
        if _contains(n,"comida","alimento","alimentos","food","carne","meat","queso","cheese","fruta","fruit"):return "food"
        if _contains(n,"mascota","mascotas","animal","perro","gato","pet","pets"):return "pet"
        if _contains(n,"equipo medico","equipo médico","medical equipment","medical device","cpap","silla de ruedas","wheelchair"):return "medical"
        if _contains(n,"pasaporte","passport","visa","documento","documentos","identificacion","identificación","id"):return "document"
        if _contains(n,"dinero","efectivo","cash","money","currency","moneda"):return "cash"
        if _contains(n,"computadora","computer","laptop","telefono","teléfono","phone","tablet","electronico","electrónico"):return "electronics"
        if _contains(n,"mochila","backpack","maleta","suitcase","equipaje","baggage","carry on","carry-on","checked baggage"):return "baggage"
        return "general"

    def _flight_values(self,flight:Any)->Dict[str,Any]:
        if hasattr(flight,"model_dump"):return flight.model_dump()
        if hasattr(flight,"dict"):return flight.dict()
        if isinstance(flight,dict):return dict(flight)
        return {}

    def _find_rule(self,item:str)->Optional[Rule]:
        n=_norm(item)
        category=self.item_category(item)
        mapping={
            "battery":["power_bank","spare_lithium_battery"],
            "medication":["medications"],
            "liquid":["liquids"],
            "aerosol":["aerosols"],
            "food":["food"],
            "pet":["pets"],
            "medical":["medical_equipment"],
            "document":["documents"],
            "cash":["cash"],
            "electronics":["electronics"]
        }
        for rid in mapping.get(category,[]):
            r=rule_repo.get(rid)
            if r:return r
        matches=rule_repo.search(n)
        return matches[0] if matches else None

    def advise(self,item:Any,flight:Any=None,baggage_type:Any=None,language="es",**kwargs)->Dict[str,Any]:
        if isinstance(item,dict):
            data=dict(item)
            text=data.get("item") or data.get("name") or ""
            flight=data.get("flight",flight)
            baggage_type=data.get("baggage_type",baggage_type)
            language=data.get("language",language)
        else:
            text=str(item or "")
        if not text.strip():
            return self._review_empty(language)

        f=self._flight_values(flight)
        rule=self._find_rule(text)
        if not rule:
            return self._review_unknown(text,f,baggage_type,language)

        airline=f.get("airline")
        destination=f.get("destination")
        cabin=f.get("cabin")
        fare=f.get("fare")
        verified_rule=bool(rule.verified and rule.status==RuleStatus.ACTIVE.value)

        category=rule.visual_status
        missing=list(rule.missing_information_en if language=="en" else rule.missing_information_es)
        conditions=list(rule.conditions_en if language=="en" else rule.conditions_es)
        source=rule.source or None
        source_name=rule.source_name or None
        verification_date=rule.verification_date if rule.verified else None

        if airline and rule.airline and _norm(airline)!=_norm(rule.airline):
            missing.append("airline-specific rule")
            category=VisualStatus.REVIEW.value
        if destination and rule.destination and _norm(destination)!=_norm(rule.destination):
            missing.append("destination-specific rule")
            category=VisualStatus.REVIEW.value

        if not airline and category!=VisualStatus.NOT_ALLOWED.value:
            missing.append("la aerolínea" if language=="es" else "the airline")
            category=VisualStatus.REVIEW.value

        if not fare and category!=VisualStatus.NOT_ALLOWED.value:
            missing.append("la tarifa" if language=="es" else "the fare")
            category=VisualStatus.REVIEW.value

        if rule.status!=RuleStatus.ACTIVE.value:
            category=VisualStatus.REVIEW.value

        if not verified_rule:
            category=VisualStatus.REVIEW.value

        place=self._place(text,baggage_type,language)
        explanation=self._explanation(rule,text,language,category)
        next_action=self._next_action(text,rule,language,missing)

        return {
            "success":True,
            "item":text,
            "category":category,
            "explanation":explanation,
            "baggage_place":place,
            "conditions":_unique_strings(conditions),
            "missing_information":_unique_strings(missing),
            "source":source,
            "source_name":source_name,
            "verified":verified_rule,
            "verification_date":verification_date,
            "official_link":self._official_link(rule),
            "next_action":next_action,
            "legal_notice":self._legal(language)
        }

    def advise_item(self,item:str,**kwargs)->Dict[str,Any]:
        return self.advise(item,**kwargs)

    def _place(self,item,baggage_type,language):
        b=_norm(str(baggage_type or ""))
        if language=="en":
            if b in ("checked","checked baggage"):return "Checked baggage / aircraft hold, if the airline allows the item there."
            if b in ("carry_on","carry-on","carry on"):return "Cabin baggage, if the airline allows the item there."
            if b in ("personal_item","personal item"):return "Personal item, only if the airline and fare allow it."
            if self.item_category(item)=="battery":return "Usually needs a specific baggage-location check before travel."
            return "The correct location depends on the item and the applicable airline/security rule."
        if b in ("checked","checked baggage"):return "Equipaje documentado, si la aerolínea permite llevar allí el artículo."
        if b in ("carry_on","carry-on","carry on"):return "Equipaje de cabina, si la aerolínea permite llevar allí el artículo."
        if b in ("personal_item","personal item"):return "Artículo personal, solamente si la aerolínea y tarifa lo permiten."
        if self.item_category(item)=="battery":return "Necesita revisar específicamente dónde debe viajar antes de preparar el equipaje."
        return "El lugar correcto depende del artículo y de la regla de seguridad o aerolínea aplicable."

    def _explanation(self,rule,item,language,category):
        if language=="en":
            base=rule.explanation_en
            if category==VisualStatus.REVIEW.value:return base+" We do not want to guess: the missing condition must be confirmed before you travel."
            if category==VisualStatus.ALLOW_WITH_CONDITION.value:return base+" Follow every listed condition."
            return base
        base=rule.explanation_es
        if category==VisualStatus.REVIEW.value:return base+" No queremos adivinar: falta confirmar la condición que puede cambiar la respuesta antes de viajar."
        if category==VisualStatus.ALLOW_WITH_CONDITION.value:return base+" Debes cumplir todas las condiciones indicadas."
        return base

    def _next_action(self,item,rule,language,missing):
        if language=="en":
            if missing:return "Open the official source and look for the item name or the baggage section. Confirm: "+", ".join(missing)+"."
            return "Confirm the current official rule for this exact flight before packing."
        if missing:return "Abre la fuente oficial y busca el nombre del artículo o la sección de equipaje. Confirma: "+", ".join(missing)+"."
        return "Confirma la regla oficial vigente para este vuelo concreto antes de preparar el equipaje."

    def _official_link(self,rule):
        if not rule.source:return None
        return {
            "name":rule.source_name or "Fuente oficial",
            "url":rule.source,
            "description":"Fuente utilizada para orientar esta revisión. Confirma la condición vigente antes de viajar.",
            "authority":rule.source_name or None,
            "country":"United States" if "faa.gov" in rule.source or "tsa.gov" in rule.source else None,
            "verified":rule.verified,
            "verified_at":rule.verification_date
        }

    def _review_empty(self,language):
        if language=="en":
            text="Tell me the item you want to carry. For example: power bank, medicine, shampoo, food or laptop."
            action="Write the item you want to review."
        else:
            text="Dime qué artículo quieres llevar. Por ejemplo: power bank, medicamento, champú, comida o computadora."
            action="Escribe el artículo que quieres revisar."
        return {"success":True,"item":"","category":VisualStatus.REVIEW.value,"explanation":text,"baggage_place":None,"conditions":[],"missing_information":["artículo" if language=="es" else "item"],"source":None,"source_name":None,"verified":False,"verification_date":None,"official_link":None,"next_action":action,"legal_notice":self._legal(language)}

    def _review_unknown(self,item,flight,baggage_type,language):
        airline=flight.get("airline")
        destination=flight.get("destination")
        if language=="en":
            explanation=f"We recognize that you want to carry “{item}”, but we do not have a confirmed rule for this exact item yet. Instead of guessing, we will help you identify the rule that applies."
            missing=["exact item description"]
            if not airline:missing.append("airline")
            if not destination:missing.append("destination")
            action="Check the airline baggage or restricted-items section and search for the exact item name. If you tell us the airline and destination, we can narrow the guidance."
        else:
            explanation=f"Entendemos que quieres llevar “{item}”, pero todavía no tenemos una regla confirmada para ese artículo exacto. En lugar de adivinar, te ayudamos a identificar la regla que corresponde."
            missing=["descripción exacta del artículo"]
            if not airline:missing.append("la aerolínea")
            if not destination:missing.append("el destino")
            action="Busca en la sección de equipaje o artículos restringidos de la aerolínea el nombre exacto del artículo. Si nos dices la aerolínea y el destino, podemos hacer la orientación más precisa."
        return {"success":True,"item":item,"category":VisualStatus.REVIEW.value,"explanation":explanation,"baggage_place":self._place(item,baggage_type,language),"conditions":[],"missing_information":missing,"source":None,"source_name":None,"verified":False,"verification_date":None,"official_link":None,"next_action":action,"legal_notice":self._legal(language)}

    def _legal(self,language):
        if language=="en":return "This is independent educational guidance from May Roga LLC. Confirm current requirements with the applicable official airline, government, airport or authority."
        return "Esta es una orientación educativa e independiente de May Roga LLC. Confirma los requisitos vigentes con la aerolínea, gobierno, aeropuerto o autoridad oficial correspondiente."

advisor=BaggageAdvisor()

__all__=["VERSION","VisualStatus","RuleStatus","Rule","RuleRepository","rule_repo","BaggageAdvisor","advisor"]
