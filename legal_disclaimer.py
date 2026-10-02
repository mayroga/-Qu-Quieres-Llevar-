# legal_disclaimer.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.0.0
from datetime import datetime,timezone

class LegalNoticeManager:
    VERSION="8.0.0"
    OWNER="May Roga LLC"
    APP_NAME="¿QUÉ QUIERES LLEVAR?"
    PRICE_USD=15.99
    SESSION_MINUTES=15
    INDEPENDENCE="¿QUÉ QUIERES LLEVAR? es un servicio independiente de May Roga LLC."
    PURPOSE="La aplicación orienta y enseña al viajero a preparar su viaje, comprender su vuelo, revisar su equipaje, practicar procesos y encontrar la fuente oficial que corresponde."
    FLIGHT_SCOPE="La aplicación puede ayudar a interpretar información de vuelos proporcionada o encontrada por el usuario y fuentes disponibles, pero no vende, reserva, emite, modifica ni cobra boletos."
    NO_BOOKING="La aplicación no es una aerolínea, agencia de viajes, vendedor de boletos, banco, gobierno, aeropuerto, consulado ni autoridad."
    BAGGAGE_SCOPE="Las recomendaciones de equipaje dependen del artículo, tipo de equipaje, aerolínea, vuelo, ruta, tarifa, país y otras condiciones aplicables. No se debe tratar una regla específica como una regla universal."
    AI_LIMITS="La inteligencia artificial puede ayudar a interpretar, organizar y explicar información, pero no sustituye una regla oficial ni decide por una aerolínea, aeropuerto, gobierno o autoridad."
    OFFICIAL_SOURCE_RULE="Cuando una condición necesita confirmación oficial, la aplicación debe enseñar al usuario qué buscar, dónde buscarlo, qué significa y llevarlo a la fuente correspondiente."
    SIMULATION_RULE="Las simulaciones de May Roga son prácticas educativas. No son formularios, aplicaciones, páginas ni sistemas oficiales de aerolíneas, gobiernos, aeropuertos o autoridades."
    FINAL_AUTHORITY="La decisión final sobre transporte, equipaje, seguridad, documentación, entrada a un país o cualquier requisito corresponde a la aerolínea, aeropuerto, gobierno o autoridad competente."
    NO_GUARANTEE="Las políticas, horarios, tarifas, rutas, requisitos y condiciones pueden cambiar. Una fuente consultada en una fecha anterior no garantiza que una condición permanezca igual el día del viaje."
    PRIVACY="La aplicación debe solicitar y conservar solamente la información necesaria para prestar el servicio. No solicita contraseñas bancarias, CVV, códigos de seguridad, credenciales de aerolíneas ni credenciales gubernamentales."
    PAYMENT="El pago corresponde al servicio de orientación y preparación de May Roga LLC. No es pago por un boleto, reserva, tarifa aeroportuaria, trámite gubernamental ni servicio de una aerolínea."
    def __init__(self,language="es"):
        self.language="en" if str(language).lower()=="en" else "es"

    def metadata(self):
        return {"version":self.VERSION,"owner":self.OWNER,"app_name":self.APP_NAME,"price_usd":self.PRICE_USD,"session_minutes":self.SESSION_MINUTES,"independent_service":True,"booking_enabled":False,"ticket_sales_enabled":False}

    def intro(self):
        if self.language=="en":
            return "¿QUÉ QUIERES LLEVAR? is an independent May Roga LLC travel-preparation service. It helps you understand your trip, baggage and travel steps in simple language."
        return "¿QUÉ QUIERES LLEVAR? es un servicio independiente de May Roga LLC que te ayuda a preparar tu viaje, entender tu vuelo, revisar tu equipaje y aprender qué debes hacer."

    def short_notice(self):
        if self.language=="en":
            return "Independent educational service. We do not sell or reserve flights. Airline, government and authority rules must be confirmed with the applicable official source."
        return "Servicio independiente y educativo. No vendemos ni reservamos vuelos. Las reglas de la aerolínea, gobierno o autoridad correspondiente deben confirmarse en la fuente oficial aplicable."

    def user_guidance(self):
        if self.language=="en":
            return "If a detail cannot be confirmed, we will explain what to look for, where to look, what the wording means and what to confirm before you travel."
        return "Si un dato no puede confirmarse directamente, te explicamos qué debes buscar, dónde buscarlo, qué significa y qué debes confirmar antes de viajar."

    def source_notice(self):
        if self.language=="en":
            return "A source being shown does not mean that a flight, fare or condition is confirmed. The source must match your airline, route, trip and situation."
        return "Que una fuente aparezca no significa que un vuelo, tarifa o condición esté confirmado. La fuente debe corresponder a tu aerolínea, ruta, viaje y situación."

    def confirmation_message(self):
        if self.language=="en":
            return "Before traveling, confirm the current requirement with the official airline, government, airport or authority that has final responsibility."
        return "Antes de viajar, confirma el requisito vigente con la aerolínea, gobierno, aeropuerto o autoridad oficial que tenga la decisión final."

    def session_expired_message(self):
        if self.language=="en":
            return "Your May Roga preparation session has ended. You can start another service session when you are ready."
        return "Tu sesión de preparación de May Roga terminó. Puedes iniciar otra sesión de servicio cuando estés listo."

    def full_notice(self):
        if self.language=="en":
            return (
                f"{self.intro()} {self.FLIGHT_SCOPE} {self.NO_BOOKING} "
                f"{self.BAGGAGE_SCOPE} {self.AI_LIMITS} {self.SIMULATION_RULE} "
                f"{self.FINAL_AUTHORITY} {self.NO_GUARANTEE} {self.PRIVACY} {self.PAYMENT}"
            )
        return (
            f"{self.intro()} {self.FLIGHT_SCOPE} {self.NO_BOOKING} "
            f"{self.BAGGAGE_SCOPE} {self.AI_LIMITS} {self.SIMULATION_RULE} "
            f"{self.FINAL_AUTHORITY} {self.NO_GUARANTEE} {self.PRIVACY} {self.PAYMENT}"
        )

    def to_dict(self):
        return {
            "version":self.VERSION,
            "owner":self.OWNER,
            "app_name":self.APP_NAME,
            "price_usd":self.PRICE_USD,
            "session_minutes":self.SESSION_MINUTES,
            "independence":self.INDEPENDENCE,
            "purpose":self.PURPOSE,
            "flight_scope":self.FLIGHT_SCOPE,
            "no_booking":self.NO_BOOKING,
            "baggage_scope":self.BAGGAGE_SCOPE,
            "ai_limits":self.AI_LIMITS,
            "official_source_rule":self.OFFICIAL_SOURCE_RULE,
            "simulation_rule":self.SIMULATION_RULE,
            "final_authority":self.FINAL_AUTHORITY,
            "no_guarantee":self.NO_GUARANTEE,
            "privacy":self.PRIVACY,
            "payment":self.PAYMENT
        }

def legal_notice(language="es"):
    return LegalNoticeManager(language).full_notice()

def short_legal_notice(language="es"):
    return LegalNoticeManager(language).short_notice()

def legal_metadata():
    return LegalNoticeManager().metadata()

manager=LegalNoticeManager()

__all__=["LegalNoticeManager","legal_notice","short_legal_notice","legal_metadata","manager"]
