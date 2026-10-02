# rules_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.1
from dataclasses import asdict,dataclass
from enum import Enum
from typing import Any,Dict,List,Optional
import unicodedata

VERSION="8.0.1"

class VisualStatus(str,Enum):
    ALLOW="ALLOW"
    ALLOW_WITH_CONDITION="ALLOW_WITH_CONDITION"
    NOT_ALLOWED="NOT_ALLOWED"
    REVIEW="REVIEW"

class RuleStatus(str,Enum):
    ACTIVE="ACTIVE"
    PENDING="PENDING"
    EXPIRED="EXPIRED"

@dataclass
class Rule:
    id:str
    term:str
    keywords:List[str]
    status:RuleStatus=RuleStatus.PENDING
    visual_status:VisualStatus=VisualStatus.REVIEW
    explanation_es:str=""
    explanation_en:str=""
    places_es:List[str]=None
    places_en:List[str]=None
    conditions_es:List[str]=None
    conditions_en:List[str]=None
    missing_information_es:List[str]=None
    missing_information_en:List[str]=None
    source:str=""
    source_name:str=""
    verified:bool=False
    verification_date:str=""
    airline:str=""
    destination:str=""
    baggage_types:List[str]=None
    notes_es:str=""
    notes_en:str=""
    def __post_init__(self):
        self.places_es=self.places_es or []
        self.places_en=self.places_en or []
        self.conditions_es=self.conditions_es or []
        self.conditions_en=self.conditions_en or []
        self.missing_information_es=self.missing_information_es or []
        self.missing_information_en=self.missing_information_en or []
        self.baggage_types=self.baggage_types or []
        if isinstance(self.status,str):
            try:self.status=RuleStatus(self.status)
            except Exception:self.status=RuleStatus.PENDING
        if isinstance(self.visual_status,str):
            try:self.visual_status=VisualStatus(self.visual_status)
            except Exception:self.visual_status=VisualStatus.REVIEW
    def to_dict(self)->Dict[str,Any]:
        d=asdict(self)
        d["status"]=self.status.value
        d["visual_status"]=self.visual_status.value
        return d

class RuleRepository:
    def __init__(self):
        self._rules:Dict[str,Rule]={}
        self._load_defaults()

    def add(self,rule:Rule)->Rule:
        self._rules[rule.id]=rule
        return rule

    def get(self,rule_id:str)->Optional[Rule]:
        return self._rules.get(str(rule_id or "").strip())

    def all(self)->List[Rule]:
        return list(self._rules.values())

    def to_dicts(self)->List[Dict[str,Any]]:
        return [r.to_dict() for r in self.all()]

    def count(self)->int:
        return len(self._rules)

    def search(self,query:str)->List[Rule]:
        q=self._norm(query)
        if not q:return []
        return [r for r in self.all() if self._contains(r.term,q) or any(self._contains(k,q) for k in r.keywords)]

    def _norm(self,value:Any)->str:
        text=str(value or "").strip().lower()
        text=unicodedata.normalize("NFD",text)
        text="".join(c for c in text if unicodedata.category(c)!="Mn")
        return " ".join(text.replace("_"," ").split())

    def _contains(self,text:str,value:str)->bool:
        return value in self._norm(text)

    def _load_defaults(self):
        self.add(Rule(
            id="power_bank",term="power bank",
            keywords=["power bank","portable charger","battery pack","cargador portatil","bateria externa"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Una batería externa puede estar sujeta a reglas específicas de capacidad, transporte y ubicación.",
            explanation_en="A power bank may be subject to specific capacity, transportation and location rules.",
            conditions_es=["Confirma la capacidad de la batería y la regla de la aerolínea.","Revisa las reglas oficiales aplicables al equipaje de mano."],
            conditions_en=["Confirm the battery capacity and airline rule.","Check the applicable official carry-on baggage rules."],
            source="https://www.faa.gov/hazmat/packsafe/lithium-batteries",
            source_name="FAA PackSafe",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on"],
            notes_es="No se debe asumir una autorización sin conocer la capacidad y las condiciones del vuelo.",
            notes_en="Do not assume authorization without knowing the capacity and flight conditions."
        ))
        self.add(Rule(
            id="spare_lithium_battery",term="spare lithium battery",
            keywords=["spare lithium battery","lithium battery","bateria de litio","bateria suelta"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Las baterías de litio de repuesto requieren revisión de las reglas de seguridad y de la aerolínea.",
            explanation_en="Spare lithium batteries require review of security and airline rules.",
            conditions_es=["Revisa la capacidad de la batería.","Confirma cómo debe transportarse."],
            conditions_en=["Check the battery capacity.","Confirm how it must be transported."],
            source="https://www.faa.gov/hazmat/packsafe/lithium-batteries",
            source_name="FAA PackSafe",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on"]
        ))
        self.add(Rule(
            id="medications",term="medications",
            keywords=["medication","medicine","medicamentos","medicina","medicina recetada"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Los medicamentos pueden estar sujetos a reglas de seguridad, transporte e importación del destino.",
            explanation_en="Medication may be subject to security, transportation and destination import rules.",
            conditions_es=["Revisa las reglas de seguridad.","Revisa también las reglas del país de destino."],
            conditions_en=["Check security rules.","Also check the destination country's rules."],
            source="https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            source_name="TSA",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on","checked"]
        ))
        self.add(Rule(
            id="liquids",term="liquids",
            keywords=["liquid","liquids","liquido","liquidos","gel","geles"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Los líquidos pueden estar sujetos a límites y condiciones diferentes según el equipaje y el aeropuerto.",
            explanation_en="Liquids may be subject to different limits and conditions depending on baggage and airport security.",
            conditions_es=["Revisa las reglas de seguridad del aeropuerto.","Verifica excepciones aplicables antes del viaje."],
            conditions_en=["Check airport security rules.","Verify applicable exceptions before traveling."],
            source="https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            source_name="TSA",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on","checked"]
        ))
        self.add(Rule(
            id="aerosols",term="aerosols",
            keywords=["aerosol","aerosols","spray","sprays","aerosoles"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Los aerosoles pueden estar sujetos a restricciones de seguridad y transporte.",
            explanation_en="Aerosols may be subject to security and transportation restrictions.",
            conditions_es=["Revisa el tipo de aerosol y su contenido.","Confirma las condiciones de seguridad y de la aerolínea."],
            conditions_en=["Check the aerosol type and contents.","Confirm security and airline conditions."],
            source="https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            source_name="TSA",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on","checked"]
        ))
        self.add(Rule(
            id="food",term="food",
            keywords=["food","foods","comida","alimentos","snacks","alimento"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Los alimentos pueden ser aceptados para el transporte pero estar sujetos a reglas de entrada del país de destino.",
            explanation_en="Food may be accepted for transportation but subject to destination-country entry rules.",
            conditions_es=["Revisa seguridad aérea.","Revisa las reglas de importación del destino."],
            conditions_en=["Check aviation security rules.","Check destination import rules."],
            source="https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            source_name="TSA",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on","checked"]
        ))
        self.add(Rule(
            id="pets",term="pets",
            keywords=["pet","pets","dog","cat","perro","gato","mascota","mascotas"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Viajar con mascotas puede requerir condiciones de la aerolínea y documentos o requisitos del destino.",
            explanation_en="Traveling with pets may require airline conditions and destination documents or requirements.",
            conditions_es=["Confirma la política de la aerolínea.","Revisa los requisitos de entrada del destino."],
            conditions_en=["Confirm the airline policy.","Check destination entry requirements."],
            source="https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            source_name="TSA",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on","checked"]
        ))
        self.add(Rule(
            id="medical_equipment",term="medical equipment",
            keywords=["medical equipment","medical device","equipo medico","dispositivo medico"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Los equipos médicos pueden tener reglas específicas de seguridad y de la aerolínea.",
            explanation_en="Medical equipment may have specific security and airline rules.",
            conditions_es=["Identifica el equipo exacto.","Confirma las condiciones con la aerolínea y la fuente oficial correspondiente."],
            conditions_en=["Identify the exact equipment.","Confirm conditions with the airline and applicable official source."],
            source="https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            source_name="TSA",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on","checked"]
        ))
        self.add(Rule(
            id="documents",term="documents",
            keywords=["document","documents","passport","visa","documentos","pasaporte","visa"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Los documentos de viaje dependen de la nacionalidad, destino, ruta y situación del viajero.",
            explanation_en="Travel documents depend on nationality, destination, route and the traveler's situation.",
            conditions_es=["Confirma los requisitos oficiales de entrada y salida.","Revisa pasaporte, vigencia, visa y formularios aplicables."],
            conditions_en=["Confirm official entry and exit requirements.","Check passport, validity, visa and applicable forms."],
            baggage_types=["carry_on"],
            notes_es="Las reglas de seguridad de Estados Unidos no sustituyen los requisitos de entrada del país de destino.",
            notes_en="United States security rules do not replace destination entry requirements."
        ))
        self.add(Rule(
            id="cash",term="cash",
            keywords=["cash","money","dinero","efectivo","currency","moneda"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="El transporte de efectivo puede estar sujeto a requisitos de declaración y reglas del país de salida o destino.",
            explanation_en="Carrying cash may be subject to declaration requirements and rules of the departure or destination country.",
            conditions_es=["Revisa los requisitos oficiales de declaración.","No introduzcas información bancaria, contraseñas o códigos de seguridad en la aplicación."],
            conditions_en=["Check official declaration requirements.","Do not enter banking information, passwords or security codes in the application."],
            baggage_types=["carry_on","checked"]
        ))
        self.add(Rule(
            id="electronics",term="electronics",
            keywords=["electronics","electronic device","laptop","tablet","phone","electronics","electronicos","electronica","telefono","computadora"],
            visual_status=VisualStatus.REVIEW,
            explanation_es="Los dispositivos electrónicos pueden tener condiciones de seguridad y de la aerolínea.",
            explanation_en="Electronic devices may have security and airline conditions.",
            conditions_es=["Revisa las reglas de seguridad.","Confirma cualquier condición específica de batería o transporte."],
            conditions_en=["Check security rules.","Confirm any battery or transportation condition."],
            source="https://www.tsa.gov/travel/security-screening/whatcanibring/all",
            source_name="TSA",
            verified=True,
            verification_date="2026-10-01",
            baggage_types=["carry_on","checked"]
        ))

class BaggageAdvisor:
    VERSION=VERSION

    TERM_EXPLANATIONS_ES={
        "equipaje de mano":"El equipaje que el pasajero lleva consigo en la cabina, sujeto a las condiciones de la aerolínea.",
        "equipaje facturado":"El equipaje que se entrega a la aerolínea para viajar en la bodega del avión.",
        "equipaje personal":"Un artículo pequeño que puede estar permitido bajo las condiciones de la aerolínea.",
        "power bank":"Batería externa utilizada para cargar dispositivos. Su capacidad y forma de transporte pueden importar.",
        "bateria de litio":"Batería que puede estar sujeta a reglas específicas de seguridad y transporte.",
        "visa":"Autorización o documento de entrada que puede ser requerido por el país de destino.",
        "evisa":"Visa electrónica solicitada o emitida mediante un sistema oficial cuando el país ofrece esa modalidad.",
        "d viajeros":"Declaración o formulario oficial de viaje utilizado por Cuba cuando corresponde."
    }
    TERM_EXPLANATIONS_EN={
        "carry on baggage":"Baggage carried by the passenger in the aircraft cabin, subject to airline conditions.",
        "checked baggage":"Baggage delivered to the airline for transportation in the aircraft hold.",
        "personal item":"A smaller item that may be allowed under the airline's conditions.",
        "power bank":"A portable battery used to charge devices. Capacity and transportation rules may matter.",
        "lithium battery":"A battery that may be subject to specific safety and transportation rules.",
        "visa":"An entry authorization or document that may be required by the destination country.",
        "evisa":"An electronic visa requested or issued through an official system when offered by a country.",
        "d viajeros":"An official travel declaration used by Cuba when applicable."
    }

    def __init__(self,repo:Optional[RuleRepository]=None):
        self.repo=repo or RuleRepository()

    def _norm(self,value:Any)->str:
        text=str(value or "").strip().lower()
        text=unicodedata.normalize("NFD",text)
        text="".join(c for c in text if unicodedata.category(c)!="Mn")
        return " ".join(text.replace("_"," ").split())

    def _contains(self,text:Any,value:Any)->bool:
        return self._norm(value) in self._norm(text)

    def explain_term(self,term:str,language:str="es")->Dict[str,Any]:
        lang="en" if str(language or "es").lower()=="en" else "es"
        q=self._norm(term)
        table=self.TERM_EXPLANATIONS_EN if lang=="en" else self.TERM_EXPLANATIONS_ES
        for key,value in table.items():
            if q==self._norm(key) or q in self._norm(key) or self._norm(key) in q:
                return {"success":True,"term":term,"explanation":value,"language":lang}
        rule=self._find_rule(q)
        if rule:
            return {
                "success":True,
                "term":term,
                "explanation":rule.explanation_en if lang=="en" else rule.explanation_es,
                "language":lang
            }
        return {
            "success":True,
            "term":term,
            "explanation":(
                "This term needs context before a specific interpretation can be given."
                if lang=="en" else
                "Este término necesita contexto antes de dar una interpretación específica."
            ),
            "language":lang
        }

    def item_category(self,item:str)->str:
        q=self._norm(item)
        for rule in self.repo.all():
            if q==self._norm(rule.term) or any(self._contains(q,k) or self._contains(k,q) for k in rule.keywords):
                return rule.id
        return ""

    def _flight_values(self,flight:Any=None,**kwargs)->Dict[str,Any]:
        data={}
        if isinstance(flight,dict):
            data.update(flight)
        elif flight is not None:
            for key in ("airline","destination","origin","cabin","fare","baggage_type","baggage","baggage_summary"):
                if hasattr(flight,key):
                    data[key]=getattr(flight,key)
        data.update({k:v for k,v in kwargs.items() if v is not None})
        return data

    def _find_rule(self,item:str)->Optional[Rule]:
        q=self._norm(item)
        if not q:return None
        exact=self.repo.get(q.replace(" ","_"))
        if exact:return exact
        matches=self.repo.search(q)
        if matches:return matches[0]
        for rule in self.repo.all():
            if self._contains(q,rule.term) or self._contains(rule.term,q):
                return rule
            if any(self._contains(q,k) or self._contains(k,q) for k in rule.keywords):
                return rule
        return None

    def advise(self,item:Any="",baggage_type:Any=None,airline:str="",destination:str="",origin:str="",cabin:str="",fare:str="",language:str="es",flight:Any=None,**kwargs)->Dict[str,Any]:
        lang="en" if str(language or "es").lower()=="en" else "es"
        if isinstance(item,dict):
            data=dict(item)
            item=data.get("item") or data.get("name") or ""
            baggage_type=data.get("baggage_type") or data.get("baggage") or baggage_type
            airline=data.get("airline") or airline
            destination=data.get("destination") or destination
            origin=data.get("origin") or origin
            cabin=data.get("cabin") or cabin
            fare=data.get("fare") or fare
        data=self._flight_values(flight,airline=airline,destination=destination,origin=origin,cabin=cabin,fare=fare,baggage_type=baggage_type,**kwargs)
        if not str(item or "").strip():
            return self._review_empty(lang)
        rule=self._find_rule(str(item))
        if not rule:
            return self._review_unknown(str(item),lang)
        baggage_type=str(data.get("baggage_type") or "")
        airline=str(data.get("airline") or "")
        destination=str(data.get("destination") or "")
        origin=str(data.get("origin") or "")
        cabin=str(data.get("cabin") or "")
        fare=str(data.get("fare") or "")
        missing=list(rule.missing_information_en if lang=="en" else rule.missing_information_es)
        conditions=list(rule.conditions_en if lang=="en" else rule.conditions_es)
        if not baggage_type:
            missing.append("baggage type" if lang=="en" else "tipo de equipaje")
        if not airline:
            missing.append("airline" if lang=="en" else "aerolínea")
        if not destination:
            missing.append("destination" if lang=="en" else "destino")
        if not fare:
            missing.append("fare or ticket conditions" if lang=="en" else "tarifa o condiciones del boleto")
        if rule.airline and airline and self._norm(rule.airline)!=self._norm(airline):
            missing.append("airline-specific rule" if lang=="en" else "regla específica de la aerolínea")
        if rule.destination and destination and self._norm(rule.destination)!=self._norm(destination):
            missing.append("destination-specific rule" if lang=="en" else "regla específica del destino")
        if rule.baggage_types and baggage_type:
            bt=self._norm(baggage_type)
            normalized=[self._norm(x) for x in rule.baggage_types]
            if bt not in normalized:
                conditions.append(
                    "The rule may differ for this baggage type."
                    if lang=="en" else
                    "La regla puede cambiar para este tipo de equipaje."
                )
        verified_source=bool(rule.verified and rule.source)
        status=rule.visual_status
        if missing or rule.status!=RuleStatus.ACTIVE or not verified_source:
            status=VisualStatus.REVIEW
        explanation=rule.explanation_en if lang=="en" else rule.explanation_es
        if rule.notes_en if lang=="en" else rule.notes_es:
            explanation+=" "+(rule.notes_en if lang=="en" else rule.notes_es)
        return {
            "success":True,
            "item":str(item),
            "category":status.value,
            "visual_status":status.value,
            "rule_status":rule.status.value,
            "explanation":self._explanation(explanation,status,lang),
            "baggage_place":self._place(baggage_type,lang),
            "conditions":conditions,
            "missing_information":self._unique_strings(missing),
            "source":rule.source,
            "source_name":rule.source_name,
            "verified":verified_source,
            "verification_date":rule.verification_date if verified_source else "",
            "official_link":rule.source if verified_source else "",
            "next_action":self._next_action(status,rule,lang),
            "legal_notice":self._legal(lang),
            "airline":airline,
            "origin":origin,
            "destination":destination,
            "cabin":cabin,
            "fare":fare
        }

    def advise_item(self,item:str="",**kwargs)->Dict[str,Any]:
        return self.advise(item=item,**kwargs)

    def _place(self,baggage_type:str,lang:str)->str:
        bt=self._norm(baggage_type)
        if bt in {"carry on","carry-on","carry_on","hand baggage","hand luggage","equipaje de mano"}:
            return "carry-on" if lang=="en" else "equipaje de mano"
        if bt in {"checked","checked baggage","checked bag","equipaje facturado"}:
            return "checked baggage" if lang=="en" else "equipaje facturado"
        if bt:
            return baggage_type
        return "Not determined" if lang=="en" else "No determinado"

    def _explanation(self,text:str,status:VisualStatus,lang:str)->str:
        if status==VisualStatus.REVIEW:
            suffix=" Confirm the specific condition with the applicable official source."
            if lang!="en":
                suffix=" Confirma la condición específica con la fuente oficial correspondiente."
            return text+suffix
        return text

    def _next_action(self,status:VisualStatus,rule:Rule,lang:str)->str:
        if lang=="en":
            if status==VisualStatus.REVIEW:
                return "Open the official source and confirm the specific condition before traveling."
            return "Review the listed conditions before traveling."
        if status==VisualStatus.REVIEW:
            return "Abre la fuente oficial y confirma la condición específica antes de viajar."
        return "Revisa las condiciones indicadas antes de viajar."

    def _legal(self,lang:str)->str:
        return (
            "The app does not replace the airline, airport, government or competent authority."
            if lang=="en" else
            "La aplicación no sustituye a la aerolínea, aeropuerto, gobierno ni autoridad competente."
        )

    def _review_empty(self,lang:str)->Dict[str,Any]:
        return {
            "success":False,
            "item":"",
            "category":VisualStatus.REVIEW.value,
            "visual_status":VisualStatus.REVIEW.value,
            "explanation":(
                "Enter the item you want to check."
                if lang=="en" else
                "Indica el artículo que quieres revisar."
            ),
            "conditions":[],
            "missing_information":["item" if lang=="en" else "artículo"],
            "source":"",
            "source_name":"",
            "verified":False,
            "verification_date":"",
            "official_link":"",
            "next_action":(
                "Enter an item."
                if lang=="en" else
                "Indica un artículo."
            ),
            "legal_notice":self._legal(lang)
        }

    def _review_unknown(self,item:str,lang:str)->Dict[str,Any]:
        return {
            "success":True,
            "item":item,
            "category":VisualStatus.REVIEW.value,
            "visual_status":VisualStatus.REVIEW.value,
            "explanation":(
                "The item was not matched to a specific rule. Do not assume that it is allowed or prohibited."
                if lang=="en" else
                "El artículo no coincide con una regla específica. No se debe asumir que está permitido o prohibido."
            ),
            "conditions":[],
            "missing_information":[],
            "source":"",
            "source_name":"",
            "verified":False,
            "verification_date":"",
            "official_link":"",
            "next_action":(
                "Check the airline and applicable official security or destination source."
                if lang=="en" else
                "Revisa la aerolínea y la fuente oficial de seguridad o del destino que corresponda."
            ),
            "legal_notice":self._legal(lang)
        }

    def _unique_strings(self,items:List[str])->List[str]:
        seen=set()
        out=[]
        for item in items:
            value=str(item or "").strip()
            key=self._norm(value)
            if key and key not in seen:
                seen.add(key)
                out.append(value)
        return out

rule_repo=RuleRepository()
advisor=BaggageAdvisor(rule_repo)
