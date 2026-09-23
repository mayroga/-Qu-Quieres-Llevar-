# legal_disclaimer.py - Módulo de Explicación Previa y Avisos Legales (May Roga LLC)
class LegalNoticeManager:
    VERSION = "3.0"

    @staticmethod
    def get_intro_explanation() -> dict:
        return {
            "what_is_it": "¿QUÉ QUIERES LLEVAR? es una aplicación independiente desarrollada por May Roga LLC.",
            "what_it_does": "Ayuda al pasajero a comprender de forma sencilla las reglas y restricciones aplicables a su equipaje y artículos antes de llegar al aeropuerto.",
            "problem_solved": "Reduce la incertidumbre, evita confusiones y previene sorpresas con el equipaje o artículos prohibidos.",
            "core_message": "Dime qué quieres llevar y te ayudaremos a revisar si puede viajar contigo según los datos de tu vuelo y las reglas que podamos verificar."
        }

    @staticmethod
    def get_official_disclaimer() -> dict:
        return {
            "version": LegalNoticeManager.VERSION,
            "owner": "May Roga LLC",
            "content": (
                "Esta aplicación proporciona información orientativa basada en fuentes verificadas. "
                "No sustituye a la aerolínea, TSA, DOT, CBP, FAA ni a ninguna autoridad competente. "
                "La decisión final de aceptación corresponde exclusivamente al operador del vuelo o autoridad con jurisdicción. "
                "No garantizamos la aceptación absoluta ni la ausencia de inspecciones o cargos."
            )
        }
