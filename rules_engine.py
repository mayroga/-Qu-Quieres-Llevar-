from __future__ import annotations
import re
from typing import Any,Dict,List,Optional
VERSION="8.2.0"
VERIFICATION_DATE="2026-10-02"

ES={
"unknown":"No pude identificar el artículo con suficiente precisión. No asumas que está permitido o prohibido.",
"conditional":"Puede estar permitido, pero depende del artículo exacto, la forma de transporte, la cantidad, la aerolínea o el destino.",
"prohibited":"No está permitido en la modalidad indicada por la regla aplicable.",
"allowed":"La fuente consultada indica que puede transportarse en esta modalidad, sujeto a las condiciones indicadas.",
"check":"Debes confirmar esta condición con la fuente oficial correspondiente antes de viajar.",
"next":"Comprueba la fuente indicada y la regla específica de tu aerolínea y destino.",
"need_baggage":"Necesito saber dónde quieres llevarlo: equipaje de mano o equipaje facturado.",
"need_wh":"Necesito conocer la capacidad de la batería en Wh para determinar la regla aplicable.",
"need_airline":"La aerolínea puede tener restricciones adicionales. Indica la aerolínea para comprobarla.",
"need_destination":"La entrada de alimentos, medicamentos, plantas y otros artículos puede depender del país de destino.",
"need_quantity":"La cantidad puede cambiar la regla aplicable.",
"cabin":"Equipaje de mano",
"checked":"Equipaje facturado",
"both":"Equipaje de mano y facturado",
"not_allowed":"No permitido"
}
EN={
"unknown":"I could not identify the item precisely enough. Do not assume that it is allowed or prohibited.",
"conditional":"It may be allowed, but this depends on the exact item, transport method, quantity, airline or destination.",
"prohibited":"It is not allowed under the applicable rule for the indicated transport method.",
"allowed":"The consulted source indicates that it may be transported in this way, subject to the stated conditions.",
"check":"Confirm this condition with the applicable official source before traveling.",
"next":"Check the listed source and the specific rule of your airline and destination.",
"need_baggage":"I need to know where you want to carry it: carry-on or checked baggage.",
"need_wh":"I need the battery capacity in Wh to determine the applicable rule.",
"need_airline":"The airline may have additional restrictions. Enter the airline to check it.",
"need_destination":"Import rules for food, medication, plants and other items may depend on the destination country.",
"need_quantity":"Quantity can change the applicable rule.",
"cabin":"Carry-on baggage",
"checked":"Checked baggage",
"both":"Carry-on and checked baggage",
"not_allowed":"Not allowed"
}

def _t(v:Any)->str:return str(v or "").strip()
def _norm(v:Any)->str:
    s=_t(v).lower()
    for a,b in (("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ü","u"),("ñ","n")):s=s.replace(a,b)
    return re.sub(r"\s+"," ",s)
def _num(v:Any,default:float=0)->float:
    try:return float(v)
    except:return default
def _lang(language:str)->Dict[str,str]:return EN if _norm(language)=="en" else ES
def _english(language:str)->bool:return _norm(language)=="en"

class RulesRepository:
    def __init__(self,rules:List[Dict[str,Any]]):self.rules=rules
    def to_dicts(self)->List[Dict[str,Any]]:return [dict(x) for x in self.rules]
    def all(self)->List[Dict[str,Any]]:return self.to_dicts()
    def get(self,rule_id:str)->Optional[Dict[str,Any]]:
        rid=_norm(rule_id)
        for r in self.rules:
            if _norm(r.get("id"))==rid:return dict(r)
        return None

class RulesEngine:
    def __init__(self):
        self.version=VERSION
        self.verification_date=VERIFICATION_DATE
        self.rules=self._rules()
        self.repo=RulesRepository(self.rules)

    def _rules(self)->List[Dict[str,Any]]:
        return [
{"id":"power_bank","terms":["power bank","powerbank","portable charger","portable charging bank","external battery","bateria externa","batería externa","cargador portatil","cargador portátil","portable charger battery"],"status":"conditional","category":"battery","title_es":"Power bank / batería externa","title_en":"Power bank / external battery","reason_es":"Los power banks son baterías de repuesto y deben ir en el equipaje de mano. La capacidad en Wh y las reglas de la aerolínea pueden cambiar lo permitido.","reason_en":"Power banks are spare batteries and must be carried in carry-on baggage. The Wh capacity and airline rules can change what is allowed.","source_ids":["faa_batteries","tsa_batteries"],"needs":["wh","airline"],"carry_on":"required","checked":"no","verification_date":VERIFICATION_DATE},
{"id":"lithium_battery","terms":["lithium battery","lithium batteries","bateria de litio","batería de litio","baterias de litio","baterías de litio","li ion","li-ion","ion litio","ion-litio"],"status":"conditional","category":"battery","title_es":"Batería de litio","title_en":"Lithium battery","reason_es":"La regla depende de si está instalada en un dispositivo o es una batería de repuesto, además de su capacidad en Wh y las condiciones de la aerolínea.","reason_en":"The rule depends on whether it is installed in a device or is a spare battery, as well as its Wh capacity and airline conditions.","source_ids":["faa_batteries","tsa_batteries"],"needs":["wh","airline"],"verification_date":VERIFICATION_DATE},
{"id":"lithium_device","terms":["laptop","laptop computer","telefono","teléfono","celular","mobile phone","smartphone","tablet","camera","camara","cámara","watch","reloj","gaming system","video game console","computadora","computer"],"status":"conditional","category":"electronics","title_es":"Dispositivo electrónico con batería","title_en":"Battery-powered electronic device","reason_es":"Los dispositivos con baterías de litio pueden tener reglas distintas según la capacidad, si la batería está instalada y cómo se transporta.","reason_en":"Lithium battery-powered devices can have different rules depending on capacity, whether the battery is installed and how the device is transported.","source_ids":["faa_batteries","tsa_electronics"],"needs":["airline"],"verification_date":VERIFICATION_DATE},
{"id":"firearms","terms":["firearm","firearms","gun","pistol","pistola","rifle","revolver","arma de fuego","armas de fuego","municion","munición","ammunition","ammo","municiones"],"status":"conditional","category":"firearms","title_es":"Armas y municiones","title_en":"Firearms and ammunition","reason_es":"No debe tratarse como una prohibición universal. Las reglas dependen del tipo de arma o munición, la modalidad de transporte, la aerolínea y la jurisdicción.","reason_en":"This should not be treated as a universal prohibition. Rules depend on the firearm or ammunition, transport method, airline and jurisdiction.","source_ids":["tsa_firearms","faa_packsafe"],"needs":["baggage","airline","destination"],"verification_date":VERIFICATION_DATE},
{"id":"explosives","terms":["explosive","explosives","dynamite","dinamita","grenade","granada","explosivo","explosivos"],"status":"prohibited","category":"hazmat","title_es":"Explosivos","title_en":"Explosives","reason_es":"Los explosivos no deben transportarse en equipaje de pasajeros salvo que una regla específica y aplicable establezca una excepción.","reason_en":"Explosives must not be carried in passenger baggage unless a specific applicable rule provides an exception.","source_ids":["faa_packsafe","tsa_explosives"],"needs":["destination"],"verification_date":VERIFICATION_DATE},
{"id":"torch_lighter","terms":["torch lighter","torch lighters","jet lighter","jet flame lighter","encendedor torch","encendedor de soplete","encendedor jet"],"status":"prohibited","category":"flammable","title_es":"Encendedor tipo torch","title_en":"Torch lighter","reason_es":"La FAA indica que los encendedores torch no están permitidos en cabina ni en equipaje facturado bajo las reglas aplicables a pasajeros.","reason_en":"FAA guidance states that torch lighters are not allowed in the cabin or checked baggage under the applicable passenger rules.","source_ids":["faa_lighters","tsa_lighters"],"needs":["airline"],"verification_date":VERIFICATION_DATE},
{"id":"lighter","terms":["lighter","lighters","encendedor","encendedores","zippo","butane lighter","encendedor butano"],"status":"conditional","category":"flammable","title_es":"Encendedor","title_en":"Lighter","reason_es":"El tipo de encendedor determina la regla. Algunos encendedores comunes tienen condiciones específicas y los torch lighters tienen una regla diferente.","reason_en":"The lighter type determines the rule. Some common lighters have specific conditions, while torch lighters have a different rule.","source_ids":["faa_lighters","tsa_lighters"],"needs":["baggage","airline"],"verification_date":VERIFICATION_DATE},
{"id":"sharp","terms":["knife","knives","pocket knife","utility knife","box cutter","razor blade","razor blades","blade","blades","cuchillo","cuchillos","navaja","navajas","cuchilla","cuchillas","hoja de afeitar","tijeras","scissors","sword","swords","espada","espadas"],"status":"conditional","category":"sharp","title_es":"Objeto cortante","title_en":"Sharp object","reason_es":"Las reglas pueden cambiar según el objeto y el tipo de equipaje. TSA generalmente no permite cuchillos y muchos objetos cortantes en el equipaje de mano, mientras que algunos pueden ir facturados con protección adecuada.","reason_en":"Rules can vary by item and baggage type. TSA generally does not allow knives and many sharp objects in carry-on baggage, while some may be checked when properly protected.","source_ids":["tsa_sharp"],"needs":["baggage","airline"],"carry_on":"often_no","checked":"often_yes","verification_date":VERIFICATION_DATE},
{"id":"power_tool","terms":["power tool","power tools","drill","electric drill","saw","power saw","herramienta electrica","herramienta eléctrica","taladro","sierra electrica","sierra eléctrica"],"status":"conditional","category":"tools","title_es":"Herramienta eléctrica","title_en":"Power tool","reason_es":"La herramienta y especialmente su batería determinan la regla. Las baterías de repuesto deben tratarse como baterías de repuesto.","reason_en":"The tool and especially its battery determine the rule. Spare batteries must be handled as spare batteries.","source_ids":["faa_power_tools","faa_batteries","tsa_tools"],"needs":["baggage","wh","airline"],"verification_date":VERIFICATION_DATE},
{"id":"vape","terms":["vape","vapes","vape pen","vaping device","e-cigarette","e-cigarettes","electronic cigarette","electronic cigarettes","cigarrillo electronico","cigarrillo electrónico","cigarrillos electronicos","cigarrillos electrónicos","vaporizador","vaporizadores"],"status":"conditional","category":"battery","title_es":"Dispositivo de vapeo","title_en":"Vaping device","reason_es":"Los dispositivos electrónicos para fumar deben ir en la persona o en equipaje de mano y deben protegerse contra activación accidental. La aerolínea puede imponer límites adicionales.","reason_en":"Electronic smoking devices must be carried on one's person or in carry-on baggage and protected against accidental activation. The airline may impose additional limits.","source_ids":["faa_vape","tsa_vape"],"needs":["airline"],"carry_on":"required","checked":"no","verification_date":VERIFICATION_DATE},
{"id":"alcohol","terms":["alcohol","liquor","whiskey","whisky","vodka","rum","ron","wine","vino","beer","cerveza","licor","licores"],"status":"conditional","category":"alcohol","title_es":"Bebida alcohólica","title_en":"Alcoholic beverage","reason_es":"Las reglas dependen del porcentaje de alcohol, cantidad, equipaje, empaque y aerolínea. También pueden existir reglas de importación del destino.","reason_en":"Rules depend on alcohol percentage, quantity, baggage, packaging and airline. Destination import rules may also apply.","source_ids":["tsa_alcohol","faa_packsafe"],"needs":["baggage","quantity","airline","destination"],"verification_date":VERIFICATION_DATE},
{"id":"aerosol","terms":["aerosol","aerosols","spray","perfume","perfume spray","deodorant","desodorante","hairspray","laca","shaving foam","espuma de afeitar"],"status":"conditional","category":"liquid","title_es":"Aerosol o líquido presurizado","title_en":"Aerosol or pressurized liquid","reason_es":"Puede haber límites de cantidad y diferencias entre equipaje de mano y facturado. También importa qué sustancia contiene el envase.","reason_en":"Quantity limits and differences between carry-on and checked baggage may apply. The substance inside the container also matters.","source_ids":["tsa_all","faa_packsafe"],"needs":["baggage","quantity","airline"],"verification_date":VERIFICATION_DATE},
{"id":"food","terms":["food","foods","comida","alimento","alimentos","meat","carne","chicken","pollo","pork","cerdo","beef","res","cheese","queso","fruit","fruta","fruits","vegetable","vegetables","vegetales","verduras","fresh food","comida fresca"],"status":"conditional","category":"food","title_es":"Alimento","title_en":"Food","reason_es":"Que un alimento pueda pasar el control de seguridad no significa que pueda entrar al país de destino. Las reglas de importación pueden ser diferentes.","reason_en":"An item passing airport security does not mean it may enter the destination country. Import rules can be different.","source_ids":["tsa_food","cbp_food"],"needs":["baggage","destination"],"verification_date":VERIFICATION_DATE},
{"id":"medicine","terms":["medicine","medication","medicines","medications","medicina","medicamento","medicamentos","pills","pastillas","tablets","tabletas"],"status":"conditional","category":"medical","title_es":"Medicamento","title_en":"Medication","reason_es":"El control de seguridad y la entrada del medicamento al país son cuestiones diferentes. Puede haber reglas especiales según el medicamento, cantidad y destino.","reason_en":"Airport security and importing medication into a country are different issues. Special rules may apply depending on the medication, quantity and destination.","source_ids":["tsa_medical","cbp_travel"],"needs":["destination","quantity"],"verification_date":VERIFICATION_DATE},
{"id":"liquid","terms":["liquid","liquids","liquido","líquido","liquidos","líquidos","gel","gels","cream","crema","lotion","locion","loción","shampoo","champu","champú","toothpaste","pasta dental"],"status":"conditional","category":"liquid","title_es":"Líquido, gel o crema","title_en":"Liquid, gel or cream","reason_es":"La cantidad y la forma de transporte importan. Para el control TSA existen límites y excepciones específicas; la aerolínea y el destino pueden añadir otras condiciones.","reason_en":"Quantity and transport method matter. TSA has specific limits and exceptions; the airline and destination may add other conditions.","source_ids":["tsa_all","faa_packsafe"],"needs":["baggage","quantity"],"verification_date":VERIFICATION_DATE},
{"id":"plant","terms":["plant","plants","planta","plantas","seed","seeds","semilla","semillas"],"status":"conditional","category":"agriculture","title_es":"Planta o semilla","title_en":"Plant or seed","reason_es":"Puede pasar el control de seguridad y aun así estar restringida para entrar al país. Debe verificarse la regla de importación del destino.","reason_en":"It may pass security screening and still be restricted from entering the destination country. Check the destination's import rule.","source_ids":["tsa_food","cbp_food"],"needs":["destination"],"verification_date":VERIFICATION_DATE},
{"id":"electronics","terms":["electronics","electronic device","electronica","electrónica","dispositivo electronico","dispositivo electrónico","phone","telefono","teléfono","laptop","tablet","camera","camara","cámara","computer","computadora"],"status":"conditional","category":"electronics","title_es":"Equipo electrónico","title_en":"Electronic device","reason_es":"Los dispositivos electrónicos pueden transportarse en diferentes modalidades, pero las baterías, el tamaño y las reglas de la aerolínea pueden cambiar las condiciones.","reason_en":"Electronic devices may be transported in different ways, but batteries, size and airline rules can change the conditions.","source_ids":["faa_electronics","tsa_electronics"],"needs":["airline"],"verification_date":VERIFICATION_DATE}
        ]

    def _find(self,item:str)->Optional[Dict[str,Any]]:
        n=_norm(item)
        if not n:return None
        exact=[]
        partial=[]
        for r in self.rules:
            for term in r.get("terms",[]):
                t=_norm(term)
                if n==t:
                    exact.append(r);break
                if re.search(rf"\b{re.escape(t)}\b",n):
                    partial.append(r);break
        return (exact or partial or [None])[0]

    def _sources(self,rule:Optional[Dict[str,Any]],registry=None)->List[Dict[str,Any]]:
        if not rule or not registry:return []
        out=[]
        for sid in rule.get("source_ids",[]):
            try:
                s=registry.get(sid)
                if s:
                    out.append(s.to_dict() if hasattr(s,"to_dict") else dict(s))
            except Exception:
                pass
        return out

    def battery_wh(self,wh:Any=None,volts:Any=None,ah:Any=None,mah:Any=None)->Optional[float]:
        if wh not in (None,""):
            x=_num(wh,-1)
            return round(x,2) if x>=0 else None
        v=_num(volts,-1)
        if mah not in (None,"") and v>=0:
            m=_num(mah,-1)
            return round(v*(m/1000),2) if m>=0 else None
        a=_num(ah,-1)
        if v>=0 and a>=0:return round(v*a,2)
        return None

    def battery_result(self,wh:Any=None,baggage_type:str="",airline:str="",language:str="es",spare:bool=True)->Dict[str,Any]:
        lang=_lang(language);english=_english(language);x=self.battery_wh(wh=wh)
        base={"success":True,"version":VERSION,"language":"en" if english else "es","category":"battery","verification_date":VERIFICATION_DATE,"requires_official_check":True}
        if x is None:
            base.update({"status":"unknown","title":"Battery capacity needed" if english else "Necesitamos la capacidad de la batería","message":lang["need_wh"],"next_action":lang["need_wh"],"conditions":["Find the Wh value on the battery label." if english else "Busca el valor Wh en la etiqueta de la batería.","If only mAh and V are shown, Wh can be calculated as V × Ah." if english else "Si solo aparecen mAh y V, los Wh se pueden calcular como V × Ah."]})
            return base
        base["wh"]=x
        if x>160:
            status="prohibited"
            msg="A lithium-ion battery over 160 Wh is not permitted on passenger aircraft." if english else "Una batería de ion-litio de más de 160 Wh no está permitida en aeronaves de pasajeros."
            next_action="Do not pack it in passenger baggage. Confirm the applicable transport alternative with the carrier." if english else "No la coloques en el equipaje de pasajeros. Confirma con el transportista la alternativa de transporte que corresponda."
        elif x>100:
            status="conditional"
            msg="A 101–160 Wh lithium-ion battery requires airline approval and has additional limits." if english else "Una batería de ion-litio de 101–160 Wh requiere aprobación de la aerolínea y tiene límites adicionales."
            next_action="Ask the airline for approval before traveling. Spare batteries in this range have additional quantity limits." if english else "Pide aprobación a la aerolínea antes de viajar. Las baterías de repuesto de este rango tienen límites adicionales de cantidad."
        else:
            status="allowed"
            msg="A lithium-ion battery of 100 Wh or less is within the general FAA passenger limit." if english else "Una batería de ion-litio de 100 Wh o menos está dentro del límite general de pasajeros de la FAA."
            next_action="If it is a spare battery or power bank, carry it in the cabin and protect it from damage and short circuit." if english else "Si es una batería de repuesto o power bank, llévala en la cabina y protégela contra daños y cortocircuitos."
        if spare and x<=160:
            base["carry_on"]="required"
            base["checked"]="no"
        base.update({"status":status,"title":"Lithium battery" if english else "Batería de litio","message":msg,"next_action":next_action,"source_ids":["faa_batteries"],"airline_check":bool(airline)})
        return base

    def advise(self,item:str="",quantity:Any=1,description:str="",language:str="es",baggage_type:str="",airline:str="",destination:str="",origin:str="",cabin:str="",fare:str="",wh:Any=None,volts:Any=None,ah:Any=None,mah:Any=None,spare:Any=None,registry=None,**kwargs)->Dict[str,Any]:
        lang=_lang(language);english=_english(language);item=_t(item);description=_t(description);qty=max(0,_num(quantity,1));bt=_norm(baggage_type);rule=self._find(item)
        if rule and rule["id"] in {"power_bank","lithium_battery"}:
            x=self.battery_wh(wh=wh,volts=volts,ah=ah,mah=mah)
            if x is not None:
                result=self.battery_result(x,baggage_type,airline,language,spare=True if spare in (None,"") else bool(spare))
                result.update({"item":item,"quantity":qty,"description":description,"airline":_t(airline),"destination":_t(destination),"origin":_t(origin),"baggage_type":_t(baggage_type)})
                result["official_sources"]=self._sources(self.repo.get("power_bank"),registry) if registry else []
                return result
        base={"success":True,"version":VERSION,"language":"en" if english else "es","item":item,"quantity":qty,"description":description,"baggage_type":_t(baggage_type),"airline":_t(airline),"destination":_t(destination),"origin":_t(origin),"cabin":_t(cabin),"fare":_t(fare),"verification_date":VERIFICATION_DATE,"requires_official_check":True}
        if not rule:
            base.update({"status":"unknown","title":"Unknown item" if english else "Artículo no identificado","message":lang["unknown"],"reason":lang["next"],"source":lang["next"],"next_action":lang["next"],"needs":["baggage","airline","destination"],"official_sources":[]})
            return base
        status=rule["status"]
        if status=="prohibited":
            message=lang["prohibited"]
        elif status=="allowed":
            message=lang["allowed"]
        else:
            message=lang["conditional"]
        needs=list(rule.get("needs",[]))
        if bt in {"carry_on","checked","personal_item"} and "baggage" in needs:needs.remove("baggage")
        if airline and "airline" in needs:needs.remove("airline")
        if destination and "destination" in needs:needs.remove("destination")
        title=rule["title_en"] if english else rule["title_es"]
        reason=rule["reason_en"] if english else rule["reason_es"]
        base.update({"status":status,"title":title,"message":message,"reason":reason,"rule_id":rule["id"],"source":", ".join(rule.get("source_ids",[])),"source_ids":rule.get("source_ids",[]),"needs":needs,"official_sources":self._sources(rule,registry)})
        if rule.get("carry_on"):base["carry_on"]=rule["carry_on"]
        if rule.get("checked"):base["checked"]=rule["checked"]
        if needs:
            names={"baggage":lang["need_baggage"],"wh":lang["need_wh"],"airline":lang["need_airline"],"destination":lang["need_destination"],"quantity":lang["need_quantity"]}
            base["next_action"]=names.get(needs[0],lang["next"])
        else:
            base["next_action"]=lang["next"]
        return base

    def advise_item(self,*args,**kwargs)->Dict[str,Any]:return self.advise(*args,**kwargs)

    def explain_term(self,term:str="",language:str="es",registry=None,**kwargs)->Dict[str,Any]:
        lang=_lang(language);english=_english(language);rule=self._find(term)
        if not rule:return {"success":True,"version":VERSION,"language":"en" if english else "es","term":_t(term),"title":"Term not identified" if english else "Término no identificado","message":lang["unknown"],"next_action":lang["next"],"requires_official_check":True}
        return {"success":True,"version":VERSION,"language":"en" if english else "es","term":_t(term),"title":rule["title_en"] if english else rule["title_es"],"message":rule["reason_en"] if english else rule["reason_es"],"reason":rule["reason_en"] if english else rule["reason_es"],"status":rule["status"],"source_ids":rule.get("source_ids",[]),"official_sources":self._sources(rule,registry),"next_action":lang["next"],"requires_official_check":True,"verification_date":VERIFICATION_DATE}

    def list_rules(self,language:str="es")->List[Dict[str,Any]]:
        english=_english(language)
        return [{"id":r["id"],"title":r["title_en"] if english else r["title_es"],"status":r["status"],"category":r["category"],"reason":r["reason_en"] if english else r["reason_es"],"source_ids":r.get("source_ids",[]),"verification_date":r.get("verification_date")} for r in self.rules]

    def to_dicts(self)->List[Dict[str,Any]]:return self.repo.to_dicts()

advisor=RulesEngine()
rules_engine=advisor
repo=advisor.repo
