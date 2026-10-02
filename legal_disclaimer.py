# legal_disclaimer.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.1.0
from typing import Any,Dict

VERSION="8.1.0"

class LegalNoticeManager:
    VERSION=VERSION
    OWNER="May Roga LLC"
    APP_NAME="¿QUÉ QUIERES LLEVAR?"
    PRICE_USD=15.99
    SESSION_MINUTES=15

    INDEPENDENCE_ES="¿QUÉ QUIERES LLEVAR? es un servicio independiente de May Roga LLC."
    PURPOSE_ES="La aplicación orienta al viajero para preparar su viaje, comprender información de vuelos, revisar equipaje, practicar procesos, organizar información de viaje y encontrar la fuente oficial correspondiente."
    FLIGHT_SCOPE_ES="La aplicación puede ayudar a interpretar información de vuelos proporcionada o encontrada por el usuario y fuentes disponibles, pero no vende, reserva, emite, modifica ni cobra boletos."
    NO_BOOKING_ES="La aplicación no es una aerolínea, agencia de viajes, vendedor de boletos, banco, gobierno, aeropuerto, consulado ni autoridad."
    BAGGAGE_SCOPE_ES="Las condiciones del equipaje pueden depender del artículo, tipo de equipaje, aerolínea, vuelo, ruta, tarifa, país y otras condiciones aplicables. Una regla específica no debe tratarse como una regla universal."
    DOCUMENT_SCOPE_ES="La aplicación puede ayudar a organizar y explicar información sobre documentos, formularios, visas, autorizaciones, requisitos de entrada y salida y procesos de viaje, pero no emite documentos, visas, autorizaciones ni decisiones oficiales."
    CUBA_SCOPE_ES="Para viajes a Cuba, la aplicación puede explicar y practicar procesos relacionados con documentación, D’Viajeros, visa o eVisa, equipaje, requisitos de entrada y otras condiciones disponibles en fuentes oficiales. Los requisitos finales corresponden a las autoridades y fuentes oficiales aplicables."
    AI_LIMITS_ES="La inteligencia artificial puede ayudar a interpretar, organizar y explicar información, pero no sustituye una regla oficial ni decide por una aerolínea, aeropuerto, gobierno o autoridad."
    OFFICIAL_SOURCE_RULE_ES="Cuando una condición necesita confirmación oficial, la aplicación debe indicar qué debe buscar el usuario, dónde buscarlo, qué significa y dirigirlo a la fuente correspondiente."
    SIMULATION_RULE_ES="Las simulaciones de May Roga son prácticas de orientación. No son formularios, solicitudes, páginas ni sistemas oficiales de aerolíneas, gobiernos, aeropuertos o autoridades."
    FINAL_AUTHORITY_ES="La decisión final sobre transporte, equipaje, seguridad, documentación, entrada o salida de un país o cualquier requisito corresponde a la aerolínea, aeropuerto, gobierno o autoridad competente."
    NO_GUARANTEE_ES="Las políticas, horarios, tarifas, rutas, requisitos y condiciones pueden cambiar. Una fuente consultada anteriormente no garantiza que una condición permanezca igual el día del viaje."
    PRIVACY_ES="La aplicación debe solicitar y conservar solamente la información necesaria para prestar el servicio. No solicita contraseñas bancarias, CVV, códigos de seguridad, credenciales de aerolíneas ni credenciales gubernamentales."
    PAYMENT_ES="El pago corresponde al servicio de orientación y preparación de May Roga LLC. No es pago por un boleto, reserva, tarifa aeroportuaria, trámite gubernamental ni servicio de una aerolínea."

    INDEPENDENCE_EN="¿QUÉ QUIERES LLEVAR? is an independent service of May Roga LLC."
    PURPOSE_EN="The application helps travelers prepare for a trip, understand flight information, review baggage, practice processes, organize travel information and find the appropriate official source."
    FLIGHT_SCOPE_EN="The application may help interpret flight information provided or found by the user and available sources, but it does not sell, book, issue, modify or charge for tickets."
    NO_BOOKING_EN="The application is not an airline, travel agency, ticket seller, bank, government, airport, consulate or authority."
    BAGGAGE_SCOPE_EN="Baggage conditions may depend on the item, baggage type, airline, flight, route, fare, country and other applicable conditions. A specific rule should not be treated as a universal rule."
    DOCUMENT_SCOPE_EN="The application may help organize and explain information about documents, forms, visas, authorizations, entry and exit requirements and travel processes, but it does not issue documents, visas, authorizations or official decisions."
    CUBA_SCOPE_EN="For travel to Cuba, the application may explain and practice processes related to documentation, D’Viajeros, visas or eVisas, baggage, entry requirements and other conditions available from official sources. Final requirements are determined by the applicable authorities and official sources."
    AI_LIMITS_EN="Artificial intelligence may help interpret, organize and explain information, but it does not replace an official rule or make decisions for an airline, airport, government or authority."
    OFFICIAL_SOURCE_RULE_EN="When a condition requires official confirmation, the application should tell the user what to look for, where to look, what it means and direct the user to the applicable source."
    SIMULATION_RULE_EN="May Roga simulations are practice and orientation tools. They are not official forms, applications, pages or systems of airlines, governments, airports or authorities."
    FINAL_AUTHORITY_EN="The final decision regarding transportation, baggage, security, documentation, entry into or exit from a country or any requirement belongs to the applicable airline, airport, government or competent authority."
    NO_GUARANTEE_EN="Policies, schedules, fares, routes, requirements and conditions may change. A source consulted earlier does not guarantee that a condition will remain the same on the day of travel."
    PRIVACY_EN="The application should request and retain only the information necessary to provide the service. It does not request banking passwords, CVV numbers, security codes, airline credentials or government credentials."
    PAYMENT_EN="Payment is for May Roga LLC's orientation and travel-preparation service. It is not payment for a ticket, reservation, airport fee, government procedure or airline service."

    def _lang(self,language:str)->str:
        return "en" if str(language or "es").lower()=="en" else "es"

    def _texts(self,language:str)->Dict[str,str]:
        if self._lang(language)=="en":
            return {
                "independence":self.INDEPENDENCE_EN,
                "purpose":self.PURPOSE_EN,
                "flight_scope":self.FLIGHT_SCOPE_EN,
                "no_booking":self.NO_BOOKING_EN,
                "baggage_scope":self.BAGGAGE_SCOPE_EN,
                "document_scope":self.DOCUMENT_SCOPE_EN,
                "cuba_scope":self.CUBA_SCOPE_EN,
                "ai_limits":self.AI_LIMITS_EN,
                "official_source_rule":self.OFFICIAL_SOURCE_RULE_EN,
                "simulation_rule":self.SIMULATION_RULE_EN,
                "final_authority":self.FINAL_AUTHORITY_EN,
                "no_guarantee":self.NO_GUARANTEE_EN,
                "privacy":self.PRIVACY_EN,
                "payment":self.PAYMENT_EN
            }
        return {
            "independence":self.INDEPENDENCE_ES,
            "purpose":self.PURPOSE_ES,
            "flight_scope":self.FLIGHT_SCOPE_ES,
            "no_booking":self.NO_BOOKING_ES,
            "baggage_scope":self.BAGGAGE_SCOPE_ES,
            "document_scope":self.DOCUMENT_SCOPE_ES,
            "cuba_scope":self.CUBA_SCOPE_ES,
            "ai_limits":self.AI_LIMITS_ES,
            "official_source_rule":self.OFFICIAL_SOURCE_RULE_ES,
            "simulation_rule":self.SIMULATION_RULE_ES,
            "final_authority":self.FINAL_AUTHORITY_ES,
            "no_guarantee":self.NO_GUARANTEE_ES,
            "privacy":self.PRIVACY_ES,
            "payment":self.PAYMENT_ES
        }

    def metadata(self,language:str="es")->Dict[str,Any]:
        return {
            "version":self.VERSION,
            "owner":self.OWNER,
            "app_name":self.APP_NAME,
            "price_usd":self.PRICE_USD,
            "session_minutes":self.SESSION_MINUTES,
            "independent_service":True,
            "booking":False,
            "ticket_sales":False,
            "documents_issued":False,
            "government_service":False,
            "texts":self._texts(language)
        }

    def intro(self,language:str="es")->str:
        t=self._texts(language)
        return t["independence"]+" "+t["purpose"]

    def short_notice(self,language:str="es")->str:
        t=self._texts(language)
        return t["independence"]+" "+t["no_booking"]

    def user_guidance(self,language:str="es")->str:
        t=self._texts(language)
        return t["official_source_rule"]+" "+t["final_authority"]

    def source_notice(self,language:str="es")->str:
        t=self._texts(language)
        return t["no_guarantee"]+" "+t["official_source_rule"]

    def confirmation_message(self,language:str="es")->str:
        if self._lang(language)=="en":
            return "Before traveling, confirm the final flight, baggage, documentation, entry and exit requirements with the applicable official sources."
        return "Antes de viajar, confirma el vuelo, el equipaje, la documentación y los requisitos finales de entrada y salida con las fuentes oficiales correspondientes."

    def session_expired_message(self,language:str="es")->str:
        if self._lang(language)=="en":
            return "Your 15-minute service session has expired. Start a new session to continue."
        return "Tu sesión de servicio de 15 minutos terminó. Inicia una nueva sesión para continuar."

    def full_notice(self,language:str="es")->str:
        t=self._texts(language)
        return "\n\n".join([
            t["independence"],
            t["purpose"],
            t["flight_scope"],
            t["no_booking"],
            t["baggage_scope"],
            t["document_scope"],
            t["cuba_scope"],
            t["ai_limits"],
            t["official_source_rule"],
            t["simulation_rule"],
            t["final_authority"],
            t["no_guarantee"],
            t["privacy"],
            t["payment"]
        ])

    def to_dict(self,language:str="es")->Dict[str,Any]:
        t=self._texts(language)
        return {
            "version":self.VERSION,
            "owner":self.OWNER,
            "app_name":self.APP_NAME,
            "price_usd":self.PRICE_USD,
            "session_minutes":self.SESSION_MINUTES,
            "independent_service":True,
            "booking":False,
            "ticket_sales":False,
            "documents_issued":False,
            "government_service":False,
            "independence":t["independence"],
            "purpose":t["purpose"],
            "flight_scope":t["flight_scope"],
            "no_booking":t["no_booking"],
            "baggage_scope":t["baggage_scope"],
            "document_scope":t["document_scope"],
            "cuba_scope":t["cuba_scope"],
            "ai_limits":t["ai_limits"],
            "official_source_rule":t["official_source_rule"],
            "simulation_rule":t["simulation_rule"],
            "final_authority":t["final_authority"],
            "no_guarantee":t["no_guarantee"],
            "privacy":t["privacy"],
            "payment":t["payment"]
        }

    def legal_notice(self,language:str="es")->str:
        return self.full_notice(language)

    def short_legal_notice(self,language:str="es")->str:
        return self.short_notice(language)

    def legal_metadata(self,language:str="es")->Dict[str,Any]:
        return self.metadata(language)

manager=LegalNoticeManager()

def legal_notice(language:str="es")->str:
    return manager.full_notice(language)

def short_legal_notice(language:str="es")->str:
    return manager.short_notice(language)

def legal_metadata(language:str="es")->Dict[str,Any]:
    return manager.metadata(language)
