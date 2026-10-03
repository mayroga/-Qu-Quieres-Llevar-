# legal_disclaimer.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v9.0.0
from typing import Any,Dict

VERSION="9.0.0"

def _lang(value:Any)->str:
    return "en" if str(value or "").strip().lower()=="en" else "es"

def legal(language:str="es")->Dict[str,Any]:
    lang=_lang(language)
    if lang=="en":
        return {
            "ok":True,
            "version":VERSION,
            "language":"en",
            "title":"Legal notice",
            "text":[
                "¿QUÉ QUIERES LLEVAR? is an independent preparation and orientation service provided by May Roga LLC.",
                "May Roga LLC is not an airline, airport, government agency, immigration authority, customs authority, travel agency or transportation provider.",
                "The application does not issue visas, approve entry, issue airline tickets, control flights, determine baggage allowances or submit official applications on behalf of the traveler.",
                "Information shown by the application is intended to help the traveler understand what should be checked before traveling.",
                "Travel requirements, baggage rules, fees, schedules, documents and other conditions may change. The traveler must confirm current requirements with the appropriate official source.",
                "Links to official sources are provided to help the traveler continue the process directly with the responsible authority or provider.",
                "Practice activities are simulations only. They do not submit applications, purchase tickets, request visas or complete official procedures.",
                "The application should not be used to enter passwords, banking credentials, payment security codes or other sensitive credentials.",
                "Use of this application does not create an agency, representation, legal advice, immigration advice or transportation contract between May Roga LLC and the traveler."
            ],
            "next_action":"Confirm important travel information with the appropriate official source."
        }
    return {
        "ok":True,
        "version":VERSION,
        "language":"es",
        "title":"Aviso legal",
        "text":[
            "¿QUÉ QUIERES LLEVAR? es un servicio independiente de preparación y orientación ofrecido por May Roga LLC.",
            "May Roga LLC no es una aerolínea, aeropuerto, agencia gubernamental, autoridad migratoria, autoridad aduanera, agencia de viajes ni proveedor de transporte.",
            "La aplicación no emite visas, aprueba entradas, emite boletos de avión, controla vuelos, determina las franquicias de equipaje ni presenta solicitudes oficiales en nombre del viajero.",
            "La información mostrada por la aplicación tiene como finalidad ayudar al viajero a entender qué debe revisar antes de viajar.",
            "Los requisitos de viaje, reglas de equipaje, cargos, horarios, documentos y demás condiciones pueden cambiar. El viajero debe confirmar los requisitos vigentes con la fuente oficial correspondiente.",
            "Los enlaces a fuentes oficiales permiten continuar directamente el proceso con la autoridad o proveedor responsable.",
            "Las prácticas son únicamente simulaciones. No presentan solicitudes, no compran boletos, no solicitan visas ni completan trámites oficiales.",
            "La aplicación no debe utilizarse para introducir contraseñas, credenciales bancarias, códigos de seguridad de pagos ni otras credenciales sensibles.",
            "El uso de esta aplicación no crea una relación de agencia, representación, asesoría legal, asesoría migratoria ni contrato de transporte entre May Roga LLC y el viajero."
        ],
        "next_action":"Confirma la información importante de tu viaje con la fuente oficial correspondiente."
    }

def get_legal(language:str="es")->Dict[str,Any]:
    return legal(language)

def legal_text(language:str="es")->str:
    result=legal(language)
    return "\n\n".join(result.get("text",[]))

def version()->str:
    return VERSION
