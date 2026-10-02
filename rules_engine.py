# rules_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.2
from __future__ import annotations
import re
from typing import Any,Dict,List,Optional

VERSION="8.0.2"

ES={
"allowed":"Puede ser permitido, pero debe verificarse según el tipo de artículo, cantidad, transporte y reglas aplicables.",
"prohibited":"No debe transportarse cuando una regla oficial aplicable lo prohíbe.",
"conditional":"Puede estar sujeto a condiciones o restricciones. Verifica antes de viajar.",
"unknown":"El artículo no coincide con una regla específica. No se debe asumir que está permitido o prohibido.",
"next":"Revisa la aerolínea y la fuente oficial de seguridad o del destino que corresponda."
}
EN={
"allowed":"It may be permitted, but this must be verified according to the item, quantity, transport method and applicable rules.",
"prohibited":"It should not be transported when an applicable official rule prohibits it.",
"conditional":"It may be subject to conditions or restrictions. Verify before traveling.",
"unknown":"The item does not match a specific rule. Do not assume that it is allowed or prohibited.",
"next":"Check the airline and the applicable official security or destination source."
}

def _t(v:Any)->str:
    return str(v or "").strip()

def _norm(v:Any)->str:
    s=_t(v).lower()
    s=s.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ü","u").replace("ñ","n")
    return re.sub(r"\s+"," ",s)

def _num(v:Any,default:float=1)->float:
    try:return float(v)
    except:return default

class RulesEngine:
    def __init__(self):
        self.version=VERSION
        self.rules=self._rules()

    def _rules(self)->List[Dict[str,Any]]:
        return [
            {"id":"firearms","terms":["arma","armas","pistola","rifle","revolver","municion","municiones","firearm","firearms","gun","ammunition"],"status":"prohibited","title_es":"Armas y municiones","title_en":"Firearms and ammunition","reason_es":"Pueden estar prohibidas o sujetas a autorización especial.","reason_en":"They may be prohibited or subject to special authorization.","source":"FAA PackSafe / TSA / aerolínea"},
            {"id":"explosives","terms":["explosivo","explosivos","dinamita","granada","explosive","explosives","dynamite","grenade"],"status":"prohibited","title_es":"Explosivos","title_en":"Explosives","reason_es":"No deben transportarse sin una regla oficial que expresamente lo permita.","reason_en":"They should not be transported unless an official rule expressly permits them.","source":"FAA PackSafe / TSA"},
            {"id":"flammable","terms":["gasolina","gasoline","combustible","fuel","diesel","kerosene","queroseno","propano","butano","gas","gas cylinder","cilindro de gas"],"status":"conditional","title_es":"Material inflamable","title_en":"Flammable material","reason_es":"Puede estar prohibido o sujeto a condiciones específicas de transporte.","reason_en":"It may be prohibited or subject to specific transport conditions.","source":"FAA PackSafe / aerolínea"},
            {"id":"lithium_battery","terms":["bateria de litio","bateria lithium","lithium battery","power bank","powerbank","bateria externa","portable charger","cargador portatil"],"status":"conditional","title_es":"Baterías de litio","title_en":"Lithium batteries","reason_es":"Las reglas dependen del tipo, capacidad, cantidad y forma de transporte.","reason_en":"Rules depend on type, capacity, quantity and how they are transported.","source":"FAA Batteries / aerolínea"},
            {"id":"alcohol","terms":["alcohol","licor","liquor","whiskey","whisky","vodka","ron","rum","vino","wine","beer","cerveza"],"status":"conditional","title_es":"Bebidas alcohólicas","title_en":"Alcoholic beverages","reason_es":"Puede haber límites y condiciones según concentración, cantidad, equipaje y destino.","reason_en":"Limits and conditions may apply depending on concentration, quantity, baggage and destination.","source":"FAA PackSafe / aerolínea / aduana"},
            {"id":"food","terms":["comida","alimento","alimentos","food","meat","carne","pollo","chicken","pork","cerdo","queso","cheese","fruta","fruit","vegetales","vegetables","vegetales frescos"],"status":"conditional","title_es":"Alimentos","title_en":"Food","reason_es":"Las reglas pueden depender del alimento, origen, cantidad y país de destino.","reason_en":"Rules may depend on the food, origin, quantity and destination country.","source":"Destino / aduana / aerolínea"},
            {"id":"medicine","terms":["medicina","medicamento","medicamentos","medicine","medication","pills","pastillas","tabletas","tablets"],"status":"conditional","title_es":"Medicamentos","title_en":"Medication","reason_es":"Puede requerir documentación o estar sujeto a reglas del destino y del transporte.","reason_en":"Documentation may be required and destination or transport rules may apply.","source":"Destino / aerolínea / autoridad correspondiente"},
            {"id":"sharp","terms":["cuchillo","knife","navaja","razor","razor blade","blade","cuchilla","tijera","scissors"],"status":"conditional","title_es":"Objetos cortantes","title_en":"Sharp objects","reason_es":"Las condiciones pueden cambiar según el objeto y si va en equipaje de mano o facturado.","reason_en":"Conditions may vary according to the item and whether it is carry-on or checked baggage.","source":"TSA / aerolínea"},
            {"id":"aerosol","terms":["aerosol","spray","perfume","perfume spray","desodorante","deodorant","laca","hairspray"],"status":"conditional","title_es":"Aerosoles","title_en":"Aerosols","reason_es":"Puede haber límites de cantidad y condiciones de transporte.","reason_en":"Quantity limits and transport conditions may apply.","source":"TSA / FAA / aerolínea"},
            {"id":"electronics","terms":["telefono","phone","celular","laptop","computadora","computer","tablet","camara","camera","electronica","electronics"],"status":"conditional","title_es":"Equipos electrónicos","title_en":"Electronic devices","reason_es":"Generalmente dependen del tipo de dispositivo, batería y forma de transporte.","reason_en":"Rules generally depend on device type, battery and how it is transported.","source":"FAA Batteries / aerolínea"}
        ]

    def _find(self,item:str)->Optional[Dict[str,Any]]:
        n=_norm(item)
        if not n:return None
        exact=[]
        partial=[]
        for r in self.rules:
            for term in r["terms"]:
                t=_norm(term)
                if n==t or f" {t} " in f" {n} ":
                    exact.append(r);break
                if t in n or n in t:
                    partial.append(r);break
        return (exact or partial or [None])[0]

    def _lang(self,language:str)->Dict[str,str]:
        return EN if _norm(language)=="en" else ES

    def advise(self,item:str="",quantity:Any=1,description:str="",language:str="es",**kwargs)->Dict[str,Any]:
        lang=self._lang(language)
        item=_t(item)
        description=_t(description)
        quantity=max(0,_num(quantity,1))
        rule=self._find(item)

        if not rule:
            return {
                "success":True,"version":VERSION,"language":"en" if lang is EN else "es",
                "item":item,"quantity":quantity,"description":description,
                "status":"unknown","title":"Unknown item" if lang is EN else "Artículo no identificado",
                "message":lang["unknown"],"reason":"",
                "source":lang["next"],"next_action":lang["next"],
                "requires_official_check":True
            }

        key=rule["status"]
        title=rule["title_en"] if lang is EN else rule["title_es"]
        reason=rule["reason_en"] if lang is EN else rule["reason_es"]
        if key=="prohibited":message=lang["prohibited"]
        elif key=="allowed":message=lang["allowed"]
        else:message=lang["conditional"]

        return {
            "success":True,"version":VERSION,"language":"en" if lang is EN else "es",
            "item":item,"quantity":quantity,"description":description,
            "status":key,"title":title,"message":message,"reason":reason,
            "source":rule["source"],"next_action":lang["next"],
            "rule_id":rule["id"],"requires_official_check":key!="prohibited"
        }

    def advise_item(self,*args,**kwargs)->Dict[str,Any]:
        return self.advise(*args,**kwargs)

    def explain_term(self,term:str="",language:str="es",**kwargs)->Dict[str,Any]:
        lang=self._lang(language)
        term=_t(term)
        rule=self._find(term)
        if not rule:
            return {
                "success":True,"version":VERSION,
                "language":"en" if lang is EN else "es",
                "term":term,
                "message":lang["unknown"],
                "next_action":lang["next"],
                "requires_official_check":True
            }
        title=rule["title_en"] if lang is EN else rule["title_es"]
        reason=rule["reason_en"] if lang is EN else rule["reason_es"]
        return {
            "success":True,"version":VERSION,
            "language":"en" if lang is EN else "es",
            "term":term,"title":title,"message":reason,
            "status":rule["status"],"source":rule["source"],
            "next_action":lang["next"],
            "requires_official_check":rule["status"]!="prohibited"
        }

    def list_rules(self,language:str="es")->List[Dict[str,Any]]:
        en=_norm(language)=="en"
        return [{
            "id":r["id"],
            "title":r["title_en"] if en else r["title_es"],
            "status":r["status"],
            "source":r["source"]
        } for r in self.rules]

advisor=RulesEngine()
rules_engine=advisor
