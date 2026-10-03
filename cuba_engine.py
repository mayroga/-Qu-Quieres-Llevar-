# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | CUBA
from typing import Any,Dict,List

VERSION="1.0.0"

OFFICIAL={
"dv":"https://dviajeros.mitrans.gob.cu/",
"visa":"https://evisacuba.cu/",
"minrex":"https://www.cubaminrex.cu/",
"aduana":"https://www.aduana.gob.cu/"
}

def _s(v):
    return str(v or "").strip()

def _l(v):
    return "en" if _s(v).lower().startswith("en") else "es"

def official_sources()->List[Dict[str,str]]:
    return [
        {"id":"dviajeros","name":"D'Viajeros","url":OFFICIAL["dv"],"topic":"Declaración de viajeros"},
        {"id":"visa_cuba","name":"eVisa Cuba","url":OFFICIAL["visa"],"topic":"Visa electrónica"},
        {"id":"minrex","name":"MINREX Cuba","url":OFFICIAL["minrex"],"topic":"Información oficial"},
        {"id":"aduana_cuba","name":"Aduana de Cuba","url":OFFICIAL["aduana"],"topic":"Equipaje y aduana"}
    ]

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    l=_l(data.get("language"))
    nationality=_s(data.get("nationality"))
    cuban=bool(data.get("cuban_nationality"))
    passport=_s(data.get("passport"))
    arrival=_s(data.get("arrival_by"))
    topic=_s(data.get("topic")) or "general"

    if l=="en":
        steps=[
            "Confirm the passport and nationality requirements that apply to you.",
            "Check whether your travel situation requires a Cuban visa or eVisa.",
            "Complete D'Viajeros when applicable before your trip.",
            "Check current baggage and customs rules.",
            "Confirm every requirement on the official source before traveling."
        ]
    else:
        steps=[
            "Confirma los requisitos de pasaporte y nacionalidad que te corresponden.",
            "Comprueba si tu situación de viaje requiere visa o eVisa de Cuba.",
            "Completa D'Viajeros cuando corresponda antes del viaje.",
            "Revisa las reglas vigentes de equipaje y aduana.",
            "Confirma cada requisito en la fuente oficial antes de viajar."
        ]

    if cuban:
        nationality_note=(
            "Si tienes nacionalidad cubana, revisa específicamente las reglas aplicables a ciudadanos cubanos."
            if l=="es" else
            "If you have Cuban nationality, specifically check the rules applicable to Cuban citizens."
        )
    else:
        nationality_note=(
            "La nacionalidad puede cambiar los requisitos de entrada. Verifica tu caso concreto."
            if l=="es" else
            "Nationality can change entry requirements. Verify your specific situation."
        )

    return {
        "version":VERSION,
        "language":l,
        "topic":topic,
        "nationality":nationality,
        "cuban_nationality":cuban,
        "passport":passport,
        "arrival_by":arrival,
        "nationality_note":nationality_note,
        "steps":steps,
        "official_sources":official_sources(),
        "warning":(
            "Esta pantalla es orientación y práctica. No presenta una autorización de entrada ni sustituye a las autoridades cubanas."
            if l=="es" else
            "This screen provides guidance and practice. It is not an entry authorization and does not replace Cuban authorities."
        )
    }

def practice(topic:str="general",language:str="es",step:int=1)->Dict[str,Any]:
    l=_l(language)
    t=_s(topic).lower() or "general"

    es={
        "visa":(
            "Estás practicando una solicitud de visa/eVisa. Selecciona primero tu nacionalidad y después revisa los requisitos que muestra la fuente oficial.",
            ["Nacionalidad","Tipo de viaje","Pasaporte","Requisitos","Confirmación"]
        ),
        "dviajeros":(
            "Estás practicando D'Viajeros. La simulación te ayuda a entender qué información debes preparar antes de utilizar el sitio oficial.",
            ["Datos del viajero","Información del viaje","Declaración","Revisión","Confirmación"]
        ),
        "baggage":(
            "Estás practicando una revisión de equipaje. La decisión real debe confirmarse con las reglas oficiales correspondientes.",
            ["Equipaje","Artículo","Cantidad","Regla aplicable","Verificación"]
        ),
        "general":(
            "Esta es una práctica. No se envía información real ni se completa ningún trámite oficial.",
            ["Identificar","Revisar","Practicar","Verificar","Ir a la fuente oficial"]
        )
    }

    text,steps=es.get(t,es["general"])
    if l=="en":
        text={
            "visa":"You are practicing a visa/eVisa process. This simulation does not submit a real application.",
            "dviajeros":"You are practicing D'Viajeros. This simulation does not submit real information.",
            "baggage":"You are practicing a baggage review. Confirm the real rule with the applicable official source.",
            "general":"This is a practice simulation. No real information is submitted."
        }.get(t,es["general"][0])
    return {
        "version":VERSION,
        "simulation":True,
        "real_submission":False,
        "topic":t,
        "step":max(1,int(step or 1)),
        "message":text,
        "steps":steps if l=="es" else ["Identify","Review","Practice","Verify","Open official source"],
        "official_sources":official_sources()
    }

def item_check(item:str,language:str="es")->Dict[str,Any]:
    l=_l(language)
    value=_s(item)
    if l=="en":
        return {
            "item":value,
            "message":"Check the airline, security and Cuban customs rules that apply to this item.",
            "categories":["Airline","Security","Customs"],
            "official_sources":official_sources()
        }
    return {
        "item":value,
        "message":"Comprueba las reglas de la aerolínea, seguridad y aduana de Cuba que correspondan a este artículo.",
        "categories":["Aerolínea","Seguridad","Aduana"],
        "official_sources":official_sources()
    }

def baggage_check(language:str="es")->Dict[str,Any]:
    l=_l(language)
    if l=="en":
        message="Baggage rules can depend on the airline, route and Cuban customs requirements. Verify current rules before traveling."
    else:
        message="Las reglas de equipaje pueden depender de la aerolínea, la ruta y los requisitos de la aduana cubana. Verifica las reglas vigentes antes de viajar."
    return {
        "language":l,
        "message":message,
        "types":["Equipaje de mano","Equipaje facturado","Artículos especiales"],
        "official_sources":official_sources()
    }
