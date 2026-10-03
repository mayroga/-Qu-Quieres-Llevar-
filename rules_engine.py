# rules_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v9.0.0
from typing import Any,Dict,List

VERSION="9.0.0"

def _s(v:Any)->str:
    return str(v or "").strip()

def _l(v:Any)->str:
    return _s(v).lower()

def _lang(v:Any)->str:
    return "en" if _l(v)=="en" else "es"

def _cuba(v:Any)->bool:
    x=_l(v)
    return x in {"cuba","cu","hav","havana","la habana"} or "cuba" in x

def _contains(text:str,words:List[str])->bool:
    t=_l(text)
    return any(w in t for w in words)

def check_item(data:Dict[str,Any])->Dict[str,Any]:
    lang=_lang(data.get("language"))
    item=_s(data.get("item_name"))
    description=_s(data.get("description"))
    baggage=_s(data.get("baggage_type"))
    airline=_s(data.get("airline"))
    destination=_s(data.get("destination"))
    quantity=data.get("quantity")
    if not item:
        return {
            "ok":False,
            "version":VERSION,
            "language":lang,
            "missing":["item_name"],
            "title":"Falta el artículo" if lang=="es" else "Item required",
            "message":"Escribe qué artículo quieres llevar." if lang=="es" else "Enter the item you want to carry.",
            "result":None,
            "sources":[]
        }
    text=f"{item} {description}".lower()
    flags=[]
    if _contains(text,["battery","batería","lithium","litio","power bank","powerbank","battery pack"]):
        flags.append("battery")
    if _contains(text,["liquid","líquido","gel","aerosol","spray","perfume","perfume"]):
        flags.append("liquid")
    if _contains(text,["medicine","medicina","medicamento","drug","medicación"]):
        flags.append("medicine")
    if _contains(text,["food","comida","alimento","meat","carne","fruit","fruta","vegetable","vegetal"]):
        flags.append("food")
    if _contains(text,["weapon","arma","knife","cuchillo","firearm","pistola","gun","munición","ammunition"]):
        flags.append("restricted")
    if _contains(text,["flammable","inflamable","gas","fuel","combustible","explosive","explosivo"]):
        flags.append("dangerous")
    steps=[]
    if baggage:
        steps.append({
            "id":"baggage",
            "title":"Equipaje" if lang=="es" else "Baggage",
            "text":f"Indicaste: {baggage}. Confirma que ese artículo puede viajar en ese tipo de equipaje." if lang=="es" else f"You selected: {baggage}. Confirm that the item is allowed in that type of baggage."
        })
    if "battery" in flags:
        steps.append({
            "id":"battery",
            "title":"Batería" if lang=="es" else "Battery",
            "text":"Si contiene batería o litio, revisa las condiciones actuales de la aerolínea y las autoridades de seguridad antes de viajar." if lang=="es" else "If it contains a battery or lithium, check the airline and security authorities' current requirements before traveling."
        })
    if "liquid" in flags:
        steps.append({
            "id":"liquid",
            "title":"Líquido" if lang=="es" else "Liquid",
            "text":"Si es líquido, gel o aerosol, confirma las restricciones aplicables al tipo de equipaje y al aeropuerto." if lang=="es" else "If it is a liquid, gel or aerosol, confirm the restrictions that apply to the baggage type and airport."
        })
    if "medicine" in flags:
        steps.append({
            "id":"medicine",
            "title":"Medicamento" if lang=="es" else "Medicine",
            "text":"Si es un medicamento, verifica las reglas de transporte de la aerolínea y las autoridades del destino." if lang=="es" else "If it is medicine, check the airline and destination authorities' transportation rules."
        })
    if "food" in flags:
        steps.append({
            "id":"food",
            "title":"Alimento" if lang=="es" else "Food",
            "text":"Los alimentos pueden tener reglas adicionales de seguridad o entrada al país. Confirma las reglas del destino." if lang=="es" else "Food may have additional security or entry rules. Confirm the destination's requirements."
        })
    if "restricted" in flags or "dangerous" in flags:
        steps.append({
            "id":"restricted",
            "title":"Artículo restringido" if lang=="es" else "Restricted item",
            "text":"No determines su autorización únicamente con esta aplicación. Debes verificar la regla oficial antes de viajar." if lang=="es" else "Do not determine authorization using this app alone. Verify the official rule before traveling.",
        })
    if not steps:
        steps.append({
            "id":"verify",
            "title":"Verificación" if lang=="es" else "Verification",
            "text":"No puedo confirmar que un artículo esté permitido solamente por su nombre. Verifica la regla vigente con la fuente oficial." if lang=="es" else "I cannot confirm that an item is allowed based only on its name. Verify the current rule with the official source."
        })
    if _cuba(destination):
        steps.append({
            "id":"cuba",
            "title":"Destino Cuba" if lang=="es" else "Cuba destination",
            "text":"Además de las reglas de seguridad aérea, revisa las condiciones de entrada y aduanas de Cuba." if lang=="es" else "In addition to air-safety rules, check Cuba's entry and customs requirements."
        })
    return {
        "ok":True,
        "version":VERSION,
        "language":lang,
        "title":"Revisión del artículo" if lang=="es" else "Item check",
        "message":"Esto es una orientación para saber qué debes verificar; no sustituye la regla oficial." if lang=="es" else "This is guidance to help you know what to verify; it does not replace the official rule.",
        "result":{
            "item_name":item,
            "quantity":quantity,
            "baggage_type":baggage,
            "airline":airline,
            "destination":destination,
            "flags":flags,
            "steps":steps
        },
        "sources":[
            {
                "id":"tsa",
                "name":"TSA",
                "url":"https://www.tsa.gov/travel/security-screening/whatcanibring/all",
                "description":"Consulta oficial sobre artículos que pueden o no pasar por el control de seguridad."
            },
            {
                "id":"faa_baggage",
                "name":"FAA",
                "url":"https://www.faa.gov/hazmat/packsafe",
                "description":"Consulta oficial sobre materiales peligrosos y artículos relacionados con el transporte aéreo."
            }
        ]
    }

def baggage_check(data:Dict[str,Any])->Dict[str,Any]:
    lang=_lang(data.get("language"))
    airline=_s(data.get("airline"))
    destination=_s(data.get("destination"))
    baggage=_s(data.get("bag_type") or data.get("baggage_type"))
    if not baggage:
        return {
            "ok":False,
            "version":VERSION,
            "language":lang,
            "missing":["bag_type"],
            "title":"Selecciona el equipaje" if lang=="es" else "Select baggage",
            "message":"Indica qué tipo de equipaje quieres revisar." if lang=="es" else "Select the type of baggage you want to check.",
            "result":None
        }
    names={
        "personal_item":("Artículo personal","Personal item"),
        "carry_on":("Equipaje de mano","Carry-on baggage"),
        "checked_bag":("Equipaje facturado","Checked baggage")
    }
    es,en=names.get(baggage,(baggage,baggage))
    return {
        "ok":True,
        "version":VERSION,
        "language":lang,
        "title":es if lang=="es" else en,
        "message":"El peso, tamaño, cantidad y posibles cargos dependen de la aerolínea, tarifa y ruta. Confirma los datos actuales antes de viajar." if lang=="es" else "Weight, size, quantity and possible fees depend on the airline, fare and route. Confirm the current details before traveling.",
        "result":{
            "baggage_type":baggage,
            "airline":airline,
            "destination":destination,
            "check":["peso","dimensiones","cantidad","restricciones","cargos"]
        }
    }

def teach_term(term:str,language:str="es")->Dict[str,Any]:
    lang=_lang(language)
    t=_l(term)
    terms={
        "escala":{
            "es":"Una escala ocurre cuando tu viaje incluye una parada antes de llegar al destino final.",
            "en":"A connection occurs when your trip includes a stop before reaching the final destination."
        },
        "conexión":{
            "es":"Una conexión es el proceso de continuar el viaje desde un vuelo hacia otro vuelo.",
            "en":"A connection is the process of continuing your trip from one flight to another."
        },
        "equipaje de mano":{
            "es":"Es el equipaje que viaja contigo en la cabina, sujeto a las condiciones de la aerolínea.",
            "en":"It is baggage that travels with you in the cabin, subject to the airline's conditions."
        },
        "equipaje facturado":{
            "es":"Es el equipaje que entregas a la aerolínea para viajar en la bodega del avión.",
            "en":"It is baggage you give to the airline to travel in the aircraft hold."
        },
        "artículo personal":{
            "es":"Es un artículo pequeño que algunas aerolíneas permiten llevar además del equipaje de mano, según sus condiciones.",
            "en":"It is a small item some airlines allow in addition to carry-on baggage, subject to their conditions."
        },
        "visa":{
            "es":"Una visa es una autorización o documento que puede ser requerido para entrar a determinados países, según la nacionalidad y las circunstancias.",
            "en":"A visa is an authorization or document that may be required to enter certain countries, depending on nationality and circumstances."
        },
        "evisa":{
            "es":"Una eVisa es una visa o autorización gestionada electrónicamente cuando el país ofrece ese sistema.",
            "en":"An eVisa is a visa or authorization handled electronically when a country offers that system."
        },
        "d’viajeros":{
            "es":"D’Viajeros es el sistema cubano de información anticipada para viajeros.",
            "en":"D’Viajeros is Cuba's advance traveler information system."
        },
        "puerta de embarque":{
            "es":"Es el lugar del aeropuerto desde donde se organiza el embarque de tu vuelo.",
            "en":"It is the airport area where boarding for your flight is organized."
        },
        "tarjeta de embarque":{
            "es":"Es el documento o pase que identifica al pasajero y permite realizar el proceso de embarque según la aerolínea.",
            "en":"It is the document or pass that identifies the passenger and is used for the airline's boarding process."
        }
    }
    if not t:
        return {"ok":False,"version":VERSION,"language":lang,"message":"Escribe un término." if lang=="es" else "Enter a term."}
    value=terms.get(t)
    if not value:
        return {
            "ok":True,
            "version":VERSION,
            "language":lang,
            "term":term,
            "definition":"No tengo una definición específica para ese término. Verifica su significado en la fuente oficial relacionada con tu viaje." if lang=="es" else "I do not have a specific definition for that term. Verify its meaning with the official source related to your trip."
        }
    return {
        "ok":True,
        "version":VERSION,
        "language":lang,
        "term":term,
        "definition":value[lang]
    }

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    lang=_lang(data.get("language"))
    topic=_l(data.get("topic"))
    topics={
        "visa":("Visa / eVisa","Visa / eVisa","https://evisacuba.cu/"),
        "evisa":("Visa / eVisa","Visa / eVisa","https://evisacuba.cu/"),
        "dviajeros":("D’Viajeros","D’Viajeros","https://dviajeros.mitrans.gob.cu/"),
        "official":("Fuentes oficiales","Official sources","https://www.cubaminrex.cu/"),
        "customs":("Aduanas","Customs","https://www.aduana.gob.cu/")
    }
    es,en,url=topics.get(topic,topics["official"])
    return {
        "ok":True,
        "version":VERSION,
        "language":lang,
        "title":es if lang=="es" else en,
        "message":"La información de Cuba debe confirmarse en la fuente oficial correspondiente antes del viaje." if lang=="es" else "Cuba travel information must be confirmed with the corresponding official source before travel.",
        "source":{"name":es if lang=="es" else en,"url":url}
    }
