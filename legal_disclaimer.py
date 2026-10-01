# legal_disclaimer.py — QU-QUIERES-LLEVAR | May Roga LLC | v6.0.0
from datetime import datetime,timezone

class LegalNoticeManager:
    VERSION="6.0"
    OWNER="May Roga LLC"
    APP_NAME="¿QUÉ QUIERES LLEVAR?"
    PRICE_USD=15.99
    SESSION_MINUTES=15

    INDEPENDENCE=(
        "May Roga LLC es un servicio privado e independiente. "
        "¿QUÉ QUIERES LLEVAR? no es una aerolínea, agencia de viajes, "
        "aeropuerto, gobierno, consulado, autoridad migratoria, TSA, FAA, "
        "DOT, CBP ni representante oficial de ninguna de esas entidades."
    )

    PURPOSE=(
        "La aplicación ayuda al viajero a comprender su viaje, preparar su "
        "equipaje, entender términos de viaje, practicar procesos y localizar "
        "información oficial. No vende, reserva ni emite boletos de avión."
    )

    FLIGHT_SCOPE=(
        "La información de vuelos se utiliza únicamente para orientación y "
        "comprensión del viaje. La aplicación puede ayudar a identificar "
        "origen, destino, fecha, horario, vuelo directo, escalas, conexiones, "
        "cambios de avión, estancia, cabina, tarifa y equipaje cuando esos "
        "datos estén disponibles y respaldados por una fuente."
    )

    NO_BOOKING=(
        "La aplicación no cobra, vende, reserva, emite ni modifica boletos "
        "de avión y no actúa como intermediario de una aerolínea."
    )

    BAGGAGE_SCOPE=(
        "La orientación de equipaje puede incluir artículo personal, "
        "equipaje de mano o cabina, equipaje documentado o facturado, "
        "peso, medidas, cantidad, baterías, líquidos, aerosoles, alimentos, "
        "medicamentos, electrónicos, equipos médicos, animales, artículos "
        "especiales y otras categorías relacionadas."
    )

    AI_LIMITS=(
        "La inteligencia artificial puede ayudar a interpretar, organizar, "
        "explicar y localizar información. No puede crear una política de "
        "aerolínea, inventar una restricción, convertir una suposición en "
        "una regla ni presentar como confirmado un dato que no esté respaldado."
    )

    OFFICIAL_SOURCE_RULE=(
        "Cuando la aplicación no pueda confirmar una información, no debe "
        "presentar una respuesta inventada ni detener al usuario. Debe "
        "explicarle de forma sencilla qué debe buscar, qué palabra o sección "
        "debe localizar, qué significa y, cuando sea posible, practicarlo "
        "mediante una simulación educativa; después debe enviarlo a la fuente "
        "oficial para que el usuario confirme la información."
    )

    SIMULATION_RULE=(
        "Las simulaciones pertenecen a May Roga LLC. Son educativas y no son "
        "aplicaciones oficiales de aerolíneas, gobiernos, aeropuertos o "
        "autoridades. Cuando el proceso oficial esté documentado, la "
        "simulación debe respetar su orden, campos y lógica sin copiar "
        "marcas, diseños protegidos ni presentarse como oficial."
    )

    FINAL_AUTHORITY=(
        "La decisión final sobre embarque, equipaje, documentación, admisión, "
        "seguridad, transporte de artículos o cumplimiento de requisitos "
        "corresponde a la aerolínea o autoridad competente."
    )

    NO_GUARANTEE=(
        "La información y las políticas pueden cambiar. El uso de la "
        "aplicación no garantiza embarque, admisión al país, aceptación de "
        "equipaje, aprobación de documentos, visa, autorización de artículos "
        "ni disponibilidad de un vuelo."
    )

    PRIVACY=(
        "May Roga LLC debe solicitar únicamente la información necesaria para "
        "la función solicitada. No debe pedir contraseñas bancarias, CVV, "
        "códigos de seguridad, credenciales de aerolíneas, credenciales "
        "gubernamentales ni datos innecesarios. Cuando sea posible, la "
        "información de preparación debe permanecer en el dispositivo del "
        "usuario o mantenerse únicamente durante la sesión."
    )

    PAYMENT=(
        "El precio del servicio de orientación de esta aplicación es de "
        "$15.99 USD por una sesión de hasta 15 minutos, cuando el servicio "
        "requiera pago. El pago no corresponde a la compra de un boleto, "
        "reserva, tarifa de aerolínea ni servicio gubernamental."
    )

    @classmethod
    def metadata(cls):
        return {
            "app_name":cls.APP_NAME,
            "owner":cls.OWNER,
            "version":cls.VERSION,
            "session_minutes":cls.SESSION_MINUTES,
            "price_usd":cls.PRICE_USD,
            "payment_type":"one_time",
            "ai_rule_authority":False,
            "rules_are_verified":False,
            "generated_at":datetime.now(timezone.utc).isoformat()
        }

    @classmethod
    def intro(cls):
        return (
            f"{cls.APP_NAME} ayuda a preparar el viaje de forma sencilla. "
            "Te enseñamos qué significa cada cosa, cómo revisar tu vuelo, "
            "qué debes mirar en tu equipaje y dónde encontrar la información "
            "oficial antes de viajar."
        )

    @classmethod
    def short_notice(cls):
        return (
            "Servicio privado e independiente de May Roga LLC. "
            "No vende ni reserva vuelos. La información debe confirmarse "
            "con la aerolínea o autoridad oficial cuando corresponda."
        )

    @classmethod
    def user_guidance(cls):
        return (
            "Si falta una información, la aplicación debe enseñar al usuario "
            "cómo encontrarla y enviarlo a la fuente oficial en lugar de "
            "inventar una respuesta."
        )

    @classmethod
    def full_notice(cls):
        return " ".join([
            cls.INDEPENDENCE,
            cls.PURPOSE,
            cls.FLIGHT_SCOPE,
            cls.NO_BOOKING,
            cls.BAGGAGE_SCOPE,
            cls.AI_LIMITS,
            cls.OFFICIAL_SOURCE_RULE,
            cls.SIMULATION_RULE,
            cls.FINAL_AUTHORITY,
            cls.NO_GUARANTEE,
            cls.PRIVACY,
            cls.PAYMENT
        ])

    @classmethod
    def source_notice(cls,source_name="",source_url=""):
        if source_name and source_url:
            return (
                f"Fuente de referencia: {source_name}. "
                f"Confirma la información directamente en: {source_url}"
            )
        return (
            "Consulta siempre la fuente oficial correspondiente antes de viajar."
        )

    @classmethod
    def confirmation_message(cls):
        return (
            "Antes de viajar, confirma los detalles finales directamente con "
            "la aerolínea, aeropuerto o autoridad correspondiente."
        )

    @classmethod
    def session_expired_message(cls):
        return (
            "Tu sesión terminó. Puedes iniciar una nueva sesión para "
            "continuar preparando tu viaje."
        )
