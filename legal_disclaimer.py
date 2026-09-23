# legal_disclaimer.py
# ¿QUÉ QUIERES LLEVAR? — Explicación previa y avisos legales
# May Roga LLC
#
# IMPORTANTE:
# Este módulo proporciona textos informativos para la aplicación.
# No pretende crear una garantía absoluta ni sustituir revisión jurídica.
#
# La aceptación del aviso por parte del usuario NO convierte a la
# aplicación en una aerolínea, autoridad gubernamental, agencia de
# seguridad, agente de viajes ni operador aéreo.

from __future__ import annotations

from typing import Dict, Any, List


class LegalNoticeManager:

    VERSION = "4.0"
    OWNER = "May Roga LLC"
    APP_NAME = "¿QUÉ QUIERES LLEVAR?"
    SERVICE_PRICE = "$15.99"
    SERVICE_DURATION = "15 minutos"

    # ========================================================
    # EXPLICACIÓN PREVIA
    # ========================================================

    @staticmethod
    def get_intro_explanation() -> Dict[str, str]:

        return {
            "what_is_it": (
                "¿QUÉ QUIERES LLEVAR? es una aplicación independiente "
                "desarrollada por May Roga LLC para ayudar al viajero "
                "a revisar información sobre vuelos, equipaje y artículos "
                "antes de llegar al aeropuerto."
            ),

            "what_it_does": (
                "La aplicación recibe los datos que proporciona el usuario "
                "y utiliza información de vuelos y reglas que puedan "
                "verificarse para ayudar a identificar posibles "
                "restricciones aplicables."
            ),

            "problem_solved": (
                "Busca reducir la incertidumbre del pasajero antes del "
                "viaje y evitar que prepare su equipaje basándose "
                "únicamente en suposiciones."
            ),

            "how_it_helps": (
                "Puede ayudar a revisar, cuando la información esté "
                "disponible y verificada, la aerolínea, origen, destino, "
                "fecha, cabina, tarifa, tipo de equipaje, cantidad, peso, "
                "dimensiones, naturaleza del artículo y restricciones "
                "especiales."
            ),

            "core_message": (
                "Dime qué quieres llevar y te ayudaremos a revisar "
                "si puede viajar contigo según los datos de tu vuelo "
                "y las reglas que podamos verificar."
            )
        }

    # ========================================================
    # QUÉ PUEDE REVISAR
    # ========================================================

    @staticmethod
    def get_review_scope() -> List[str]:

        return [
            "Vuelo",
            "Aerolínea",
            "Origen",
            "Destino",
            "Fecha",
            "Cabina",
            "Tarifa",
            "Tipo de equipaje",
            "Cantidad de piezas",
            "Peso",
            "Dimensiones",
            "Naturaleza del artículo",
            "Baterías",
            "Líquidos",
            "Aerosoles",
            "Alimentos",
            "Medicamentos",
            "Equipos electrónicos",
            "Electrodomésticos",
            "Herramientas",
            "Artículos deportivos",
            "Animales",
            "Equipos médicos",
            "Mercancías especiales",
            "Restricciones del destino",
            "Otras condiciones verificables"
        ]

    # ========================================================
    # MENSAJE PRINCIPAL
    # ========================================================

    @staticmethod
    def get_user_message() -> str:

        return (
            "Dime qué quieres llevar y te ayudaremos a revisar si puede "
            "viajar contigo según los datos de tu vuelo y las reglas "
            "que podamos verificar."
        )

    # ========================================================
    # LO QUE NO PROMETE
    # ========================================================

    @staticmethod
    def get_no_guarantee_message() -> str:

        return (
            "La aplicación no promete que una aerolínea aceptará "
            "un artículo, que podrás abordar sin problemas, que no "
            "habrá una inspección, que no habrá cargos ni que una "
            "autoridad aprobará el transporte."
        )

    # ========================================================
    # SEPARACIÓN GEMINI / REGLAS
    # ========================================================

    @staticmethod
    def get_gemini_role() -> Dict[str, Any]:

        return {
            "title": "Uso de Gemini",
            "allowed": [
                "Interpretar la descripción escrita por el usuario.",
                "Ayudar a estructurar los datos necesarios para una consulta.",
                "Buscar o identificar información de vuelos.",
                "Consultar información externa disponible mediante las "
                "herramientas autorizadas."
            ],
            "not_allowed": [
                "Decidir por sí mismo que un artículo está permitido.",
                "Decidir por sí mismo que un artículo está prohibido.",
                "Crear una regla de equipaje.",
                "Inventar una política de una aerolínea.",
                "Convertir una suposición en una regla.",
                "Presentar una respuesta no verificada como hecho."
            ],
            "principle": (
                "Gemini puede ayudar a buscar y estructurar información; "
                "el motor determinista de reglas decide únicamente a "
                "partir de reglas verificadas incorporadas al sistema."
            )
        }

    # ========================================================
    # AVISO OFICIAL
    # ========================================================

    @staticmethod
    def get_official_disclaimer() -> Dict[str, Any]:

        return {
            "version": LegalNoticeManager.VERSION,
            "owner": LegalNoticeManager.OWNER,

            "title": (
                "Aviso de orientación informativa"
            ),

            "content": (
                "Esta aplicación proporciona orientación informativa "
                "y preventiva basada en información y reglas que el "
                "sistema puede verificar. No constituye una resolución "
                "gubernamental, autorización de transporte, decisión "
                "de una aerolínea ni asesoramiento legal."
            ),

            "final_decision": (
                "La decisión final sobre la aceptación de un artículo, "
                "equipaje o mercancía corresponde al operador del vuelo "
                "y/o a la autoridad competente con jurisdicción."
            ),

            "no_affiliation": (
                "¿QUÉ QUIERES LLEVAR? y May Roga LLC son independientes "
                "de las aerolíneas, aeropuertos y autoridades cuyos "
                "servicios o fuentes puedan aparecer en la aplicación, "
                "salvo que exista una afiliación o autorización expresa "
                "que se indique específicamente."
            ),

            "no_guarantee": (
                "No se garantiza que un artículo será aceptado, que "
                "el pasajero podrá abordar, que no habrá inspecciones, "
                "retrasos, cargos, cambios de política, restricciones "
                "adicionales o decisiones diferentes por parte de una "
                "aerolínea, aeropuerto o autoridad."
            ),

            "verification": (
                "Cuando una regla no pueda verificarse suficientemente "
                "para los datos proporcionados, la aplicación deberá "
                "indicar que necesita más información en lugar de "
                "inventar una respuesta."
            ),

            "third_party_services": (
                "La disponibilidad y funcionamiento de servicios de "
                "terceros, incluidos servicios de búsqueda, APIs, "
                "aerolíneas, fuentes externas y proveedores tecnológicos, "
                "pueden estar sujetos a sus propios límites, cambios, "
                "interrupciones y condiciones."
            )
        }

    # ========================================================
    # AVISO ANTES DEL PAGO
    # ========================================================

    @staticmethod
    def get_pre_payment_notice() -> Dict[str, Any]:

        return {
            "version": LegalNoticeManager.VERSION,

            "title": (
                "Antes de pagar"
            ),

            "service": (
                f"El servicio cuesta {LegalNoticeManager.SERVICE_PRICE} "
                f"y corresponde a un solo servicio de "
                f"{LegalNoticeManager.SERVICE_DURATION}."
            ),

            "subscription": (
                "Este servicio NO es una suscripción."
            ),

            "activation": (
                "El período de servicio comienza cuando el sistema "
                "confirma el pago y activa la sesión."
            ),

            "expiration": (
                "Al terminar el período de 15 minutos, el acceso "
                "al servicio termina y para iniciar un nuevo servicio "
                "se requiere un nuevo pago."
            ),

            "technical_limits": (
                "El acceso está sujeto a disponibilidad técnica y "
                "a los límites de los servicios de terceros utilizados "
                "por la aplicación."
            ),

            "information": (
                "La aplicación no solicita como requisito para utilizar "
                "el servicio datos personales innecesarios como nombre, "
                "teléfono, número de pasaporte o información de tarjeta."
            )
        }

    # ========================================================
    # ACEPTACIÓN
    # ========================================================

    @staticmethod
    def get_acceptance_text() -> str:

        return (
            "He leído y entiendo que ¿QUÉ QUIERES LLEVAR? proporciona "
            "orientación informativa basada en información que pueda "
            "verificarse; no sustituye a la aerolínea ni a una autoridad "
            "competente y no garantiza la aceptación de un artículo."
        )

    # ========================================================
    # RESUMEN CORTO PARA UI
    # ========================================================

    @staticmethod
    def get_short_notice() -> str:

        return (
            "Ayudamos a revisar qué puedes llevar según los datos "
            "de tu vuelo y las reglas que podamos verificar. "
            "No garantizamos la aceptación final."
        )

    # ========================================================
    # AVISO DE INDEPENDENCIA
    # ========================================================

    @staticmethod
    def get_independence_notice() -> str:

        return (
            "Aplicación independiente de May Roga LLC. "
            "No pertenece a una aerolínea, aeropuerto, TSA, FAA, "
            "DOT, CBP, IATA ni a otra autoridad, salvo que se indique "
            "expresamente una relación autorizada."
        )

    # ========================================================
    # RESPUESTA CUANDO NO HAY REGLA
    # ========================================================

    @staticmethod
    def get_unverified_rule_notice() -> Dict[str, str]:

        return {
            "status": "NECESITO MÁS INFORMACIÓN",

            "short_answer": (
                "No encontramos una regla verificada suficiente "
                "para darte una respuesta segura."
            ),

            "details": (
                "La aplicación no inventará una autorización ni una "
                "prohibición. Necesitamos información adicional o una "
                "fuente verificable que permita determinar la condición "
                "aplicable."
            )
        }

    # ========================================================
    # TEXTO DE FINALIZACIÓN
    # ========================================================

    @staticmethod
    def get_expiration_notice() -> Dict[str, str]:

        return {
            "title": "SERVICIO TERMINADO",

            "message": (
                "Tu servicio de 15 minutos ha terminado."
            ),

            "next_step": (
                "Para iniciar un nuevo servicio debes realizar "
                "un nuevo pago de $15.99."
            ),

            "subscription": (
                "Este servicio no crea una suscripción automática."
            )
        }

    # ========================================================
    # METADATOS
    # ========================================================

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:

        return {
            "application": cls.APP_NAME,
            "owner": cls.OWNER,
            "legal_version": cls.VERSION,
            "price": cls.SERVICE_PRICE,
            "duration_minutes": 15,
            "subscription": False,
            "gemini_decides_baggage_rules": False,
            "unverified_rules_are_presented_as_fact": False,
            "personal_customer_profiles_required": False
        }
