# cuba_engine.py
# QQL | ¿QUÉ QUIERES LLEVAR?
# Motor autónomo para Cuba. Sin dependencia de source_registry.py.

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Any

VERSION = "17.0.0"
APP = "¿QUÉ QUIERES LLEVAR?"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ============================================================
# FUENTES OFICIALES
# ============================================================

SOURCES = [
    {
        "id": "dviajeros",
        "name": "D'Viajeros",
        "title": "Formulario de entrada a Cuba",
        "url": "https://dviajeros.mitrans.gob.cu/",
        "official": True,
        "type": "entrada",
    },
    {
        "id": "evisa",
        "name": "eVisa Cuba",
        "title": "Visa electrónica para Cuba",
        "url": "https://evisacuba.cu/",
        "official": True,
        "type": "visa",
    },
    {
        "id": "cubaminrex",
        "name": "Ministerio de Relaciones Exteriores de Cuba",
        "title": "Información consular",
        "url": "https://misiones.cubaminrex.cu/",
        "official": True,
        "type": "consular",
    },
    {
        "id": "google_flights",
        "name": "Google Flights",
        "title": "Búsqueda de vuelos",
        "url": "https://www.google.com/travel/flights",
        "official": False,
        "type": "vuelos",
    },
    {
        "id": "tsa",
        "name": "TSA",
        "title": "Información sobre artículos y equipaje",
        "url": "https://www.tsa.gov/travel/security-screening/whatcanibring/all",
        "official": True,
        "type": "equipaje",
    },
    {
        "id": "faa",
        "name": "FAA",
        "title": "Baterías y seguridad aérea",
        "url": "https://www.faa.gov/hazmat/packsafe",
        "official": True,
        "type": "equipaje",
    },
    {
        "id": "iata",
        "name": "IATA",
        "title": "Información general de aerolíneas",
        "url": "https://www.iata.org/",
        "official": True,
        "type": "vuelos",
    },
    {
        "id": "aa",
        "name": "American Airlines",
        "title": "American Airlines",
        "url": "https://www.aa.com/",
        "official": True,
        "type": "airline",
    },
    {
        "id": "delta",
        "name": "Delta",
        "title": "Delta Air Lines",
        "url": "https://www.delta.com/",
        "official": True,
        "type": "airline",
    },
    {
        "id": "southwest",
        "name": "Southwest",
        "title": "Southwest Airlines",
        "url": "https://www.southwest.com/",
        "official": True,
        "type": "airline",
    },
    {
        "id": "jetblue",
        "name": "JetBlue",
        "title": "JetBlue",
        "url": "https://www.jetblue.com/",
        "official": True,
        "type": "airline",
    },
    {
        "id": "united",
        "name": "United",
        "title": "United Airlines",
        "url": "https://www.united.com/",
        "official": True,
        "type": "airline",
    },
    {
        "id": "spirit",
        "name": "Spirit",
        "title": "Spirit Airlines",
        "url": "https://www.spirit.com/",
        "official": True,
        "type": "airline",
    },
]

# Datos orientativos de compañías.
# La aplicación NO afirma que una compañía opere una ruta en una
# fecha concreta sin comprobación del usuario en la página oficial.
AIRLINES = [
    {
        "id": "american",
        "name": "American Airlines",
        "url": "https://www.aa.com/",
        "source_id": "aa",
    },
    {
        "id": "delta",
        "name": "Delta Air Lines",
        "url": "https://www.delta.com/",
        "source_id": "delta",
    },
    {
        "id": "southwest",
        "name": "Southwest Airlines",
        "url": "https://www.southwest.com/",
        "source_id": "southwest",
    },
    {
        "id": "jetblue",
        "name": "JetBlue",
        "url": "https://www.jetblue.com/",
        "source_id": "jetblue",
    },
    {
        "id": "united",
        "name": "United Airlines",
        "url": "https://www.united.com/",
        "source_id": "united",
    },
    {
        "id": "spirit",
        "name": "Spirit Airlines",
        "url": "https://www.spirit.com/",
        "source_id": "spirit",
    },
]

# Se mantienen como estructura separada para que main.py conserve
# /api/charters y /api/airlines-cuba sin romperse.
# No se presenta ninguno como operador actual confirmado sin
# comprobación de la ruta/fecha.
CHARTERS = [
    {
        "id": "charter_general",
        "name": "Vuelos chárter a Cuba",
        "description": "Consulta el operador y la fecha antes de comprar.",
        "url": "https://www.google.com/travel/flights",
        "source_id": "google_flights",
    }
]

OFFICIAL_URLS = {
    "dviajeros": "https://dviajeros.mitrans.gob.cu/",
    "visa": "https://evisacuba.cu/",
    "evisa": "https://evisacuba.cu/",
    "consular": "https://misiones.cubaminrex.cu/",
    "flights": "https://www.google.com/travel/flights",
    "tsa": "https://www.tsa.gov/travel/security-screening/whatcanibring/all",
    "faa": "https://www.faa.gov/hazmat/packsafe",
    "iata": "https://www.iata.org/",
}

# ============================================================
# UTILIDADES
# ============================================================

def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _lang(data: Any = None) -> str:
    if isinstance(data, dict):
        value = _text(data.get("language") or data.get("lang"), "es").lower()
    else:
        value = "es"
    return "en" if value.startswith("en") else "es"


def _source(source_id: str) -> dict:
    for item in SOURCES:
        if item["id"] == source_id:
            return dict(item)
    return {
        "id": source_id,
        "name": source_id,
        "title": source_id,
        "url": "",
        "official": False,
        "type": "general",
    }


def source_by_id(source_id: str) -> dict:
    return _source(_text(source_id))


def get_sources(*args, **kwargs) -> list:
    return [dict(x) for x in SOURCES]


def all_sources(*args, **kwargs) -> list:
    return get_sources()


def official_sources(*args, **kwargs) -> list:
    return [dict(x) for x in SOURCES if x.get("official")]


def answer_sources(*args, **kwargs) -> list:
    return official_sources()


def official_url(name: str = "") -> str:
    key = _text(name).lower()
    return OFFICIAL_URLS.get(key, "")


def get_airlines(*args, **kwargs) -> list:
    return [dict(x) for x in AIRLINES]


def get_charters(*args, **kwargs) -> list:
    return [dict(x) for x in CHARTERS]


def _sources(ids: list[str]) -> list:
    result = []
    seen = set()
    for source_id in ids:
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        item = _source(source_id)
        if item.get("url"):
            result.append(item)
    return result


def _response(
    ok: bool = True,
    message: str = "",
    data: Any = None,
    language: str = "es",
    **extra,
) -> dict:
    result = {
        "ok": bool(ok),
        "success": bool(ok),
        "message": message,
        "language": language,
        "version": VERSION,
    }
    if data is not None:
        if isinstance(data, dict):
            result.update(data)
        else:
            result["data"] = data
    result.update(extra)
    return result


def _step(
    number: int,
    title_es: str,
    text_es: str,
    title_en: str,
    text_en: str,
    url: str = "",
) -> dict:
    return {
        "step": number,
        "number": number,
        "title": title_es,
        "text": text_es,
        "title_es": title_es,
        "text_es": text_es,
        "title_en": title_en,
        "text_en": text_en,
        "url": url,
    }


def _localized(language: str, es: str, en: str) -> str:
    return en if language == "en" else es


# ============================================================
# D'VIAJEROS
# ============================================================

DVIAJEROS_STEPS = [
    _step(
        1,
        "Entra al sitio oficial",
        "Abre D'Viajeros antes de tu viaje.",
        "Open the official site",
        "Open D'Viajeros before your trip.",
        OFFICIAL_URLS["dviajeros"],
    ),
    _step(
        2,
        "Completa tus datos",
        "Escribe los datos que el formulario oficial te solicita.",
        "Enter your information",
        "Enter the information requested by the official form.",
        OFFICIAL_URLS["dviajeros"],
    ),
    _step(
        3,
        "Revisa lo escrito",
        "Mira cada dato antes de continuar y corrige cualquier error.",
        "Review your information",
        "Check each detail before continuing and correct any mistake.",
        OFFICIAL_URLS["dviajeros"],
    ),
    _step(
        4,
        "Termina el formulario",
        "Sigue las instrucciones que aparecen en el sitio oficial.",
        "Finish the form",
        "Follow the instructions shown on the official site.",
        OFFICIAL_URLS["dviajeros"],
    ),
    _step(
        5,
        "Guarda el resultado",
        "Conserva el comprobante o código que te entregue el sitio.",
        "Save the result",
        "Keep the confirmation or code provided by the site.",
        OFFICIAL_URLS["dviajeros"],
    ),
]


def dviajeros_simulation(data: Any = None, **kwargs) -> dict:
    language = _lang(data)
    steps = []

    for item in DVIAJEROS_STEPS:
        steps.append(
            {
                **item,
                "title": item["title_en"] if language == "en" else item["title_es"],
                "text": item["text_en"] if language == "en" else item["text_es"],
            }
        )

    if language == "en":
        message = "Here is the simple sequence to complete D'Viajeros on the official website."
    else:
        message = "Aquí tienes la secuencia sencilla para hacer D'Viajeros en el sitio oficial."

    return _response(
        True,
        message,
        language=language,
        steps=steps,
        simulation=steps,
        official_url=OFFICIAL_URLS["dviajeros"],
        source=_source("dviajeros"),
    )


# ============================================================
# VISA CUBA
# ============================================================

VISA_ROUTES = [
    {
        "id": "evisa",
        "name": "Visa electrónica",
        "title_es": "Visa electrónica",
        "title_en": "Electronic visa",
        "description_es": "Consulta y realiza el proceso desde el sitio oficial de eVisa Cuba.",
        "description_en": "Check and complete the process through the official eVisa Cuba website.",
        "url": OFFICIAL_URLS["evisa"],
    },
    {
        "id": "consular",
        "name": "Consulado",
        "title_es": "Consulado",
        "title_en": "Consulate",
        "description_es": "Si necesitas hacer el trámite por vía consular, consulta las instrucciones del consulado correspondiente.",
        "description_en": "If you need the consular route, check the instructions from the appropriate consulate.",
        "url": OFFICIAL_URLS["consular"],
    },
    {
        "id": "airport",
        "name": "Aeropuerto",
        "title_es": "Aeropuerto",
        "title_en": "Airport",
        "description_es": "Cuando esta opción esté disponible para tu viaje, confirma directamente con la aerolínea antes de viajar.",
        "description_en": "When this option is available for your trip, confirm directly with the airline before traveling.",
        "url": "https://www.miami-airport.com/",
    },
]


def visa_simulation(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    steps_es = [
        _step(
            1,
            "Primero revisa qué opción tienes",
            "La forma de obtener la visa puede depender de tu situación y del viaje.",
            "First check which option applies",
            "The way to obtain the visa can depend on your situation and trip.",
            OFFICIAL_URLS["evisa"],
        ),
        _step(
            2,
            "Visa electrónica",
            "Abre el sitio oficial y sigue las instrucciones que aparecen allí.",
            "Electronic visa",
            "Open the official site and follow the instructions shown there.",
            OFFICIAL_URLS["evisa"],
        ),
        _step(
            3,
            "Vía consular",
            "Si corresponde al consulado, usa sus instrucciones actuales antes de preparar documentos o pagos.",
            "Consular route",
            "If the consular route applies, use its current instructions before preparing documents or payment.",
            OFFICIAL_URLS["consular"],
        ),
        _step(
            4,
            "Opción en aeropuerto",
            "Si tu aerolínea ofrece esta posibilidad, confirma antes del viaje cómo funciona y qué debes llevar.",
            "Airport option",
            "If your airline offers this option, confirm before the trip how it works and what you need.",
            "https://www.miami-airport.com/",
        ),
        _step(
            5,
            "Guarda tu comprobante",
            "Cuando termines, conserva el resultado que te entregue el proceso.",
            "Save your confirmation",
            "When finished, keep the result provided by the process.",
            OFFICIAL_URLS["evisa"],
        ),
    ]

    steps = []
    for item in steps_es:
        steps.append(
            {
                **item,
                "title": item["title_en"] if language == "en" else item["title_es"],
                "text": item["text_en"] if language == "en" else item["text_es"],
            }
        )

    routes = []
    for route in VISA_ROUTES:
        routes.append(
            {
                **route,
                "title": route["title_en"] if language == "en" else route["title_es"],
                "description": (
                    route["description_en"]
                    if language == "en"
                    else route["description_es"]
                ),
            }
        )

    message = (
        "These are the main visa routes. Confirm the current requirements on the official site."
        if language == "en"
        else "Estas son las principales vías de visa. Confirma los requisitos actuales en el sitio oficial."
    )

    return _response(
        True,
        message,
        language=language,
        steps=steps,
        simulation=steps,
        routes=routes,
        official_url=OFFICIAL_URLS["evisa"],
        source=_source("evisa"),
        sources=_sources(["evisa", "cubaminrex"]),
    )


# ============================================================
# PRÁCTICA / SIMULACIÓN
# ============================================================

def practice_scenario(data: Any = None, **kwargs) -> dict:
    language = _lang(data)
    scenario = "dviajeros"

    if isinstance(data, dict):
        scenario = _text(
            data.get("scenario")
            or data.get("type")
            or data.get("kind"),
            "dviajeros",
        ).lower()

    if scenario in ("visa", "evisa"):
        return visa_simulation(data)

    return dviajeros_simulation(data)


# ============================================================
# DOCUMENTOS
# ============================================================

def document_analysis(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    documents = [
        {
            "id": "passport",
            "name": "Pasaporte",
            "title_es": "Pasaporte",
            "title_en": "Passport",
            "description_es": "Revisa que tengas tu pasaporte y que cumpla las condiciones aplicables a tu viaje.",
            "description_en": "Make sure you have your passport and that it meets the conditions applicable to your trip.",
        },
        {
            "id": "dviajeros",
            "name": "D'Viajeros",
            "title_es": "D'Viajeros",
            "title_en": "D'Viajeros",
            "description_es": "Completa el formulario oficial cuando corresponda.",
            "description_en": "Complete the official form when applicable.",
        },
        {
            "id": "visa",
            "name": "Visa",
            "title_es": "Visa para Cuba",
            "title_en": "Visa for Cuba",
            "description_es": "Confirma qué vía de visa corresponde a tu situación.",
            "description_en": "Confirm which visa route applies to your situation.",
        },
    ]

    for item in documents:
        item["title"] = item["title_en"] if language == "en" else item["title_es"]
        item["description"] = (
            item["description_en"]
            if language == "en"
            else item["description_es"]
        )

    return _response(
        True,
        "Document guidance" if language == "en" else "Guía de documentos",
        language=language,
        documents=documents,
        sources=_sources(["dviajeros", "evisa", "cubaminrex"]),
    )


# ============================================================
# EQUIPAJE
# ============================================================

def baggage_rules(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    result = {
        "carry_on": {
            "title": _localized(language, "Equipaje de mano", "Carry-on baggage"),
            "text": _localized(
                language,
                "Las medidas, peso y cantidad permitidos dependen de la aerolínea y del boleto.",
                "Size, weight and quantity depend on the airline and ticket.",
            ),
        },
        "checked": {
            "title": _localized(language, "Equipaje facturado", "Checked baggage"),
            "text": _localized(
                language,
                "El peso, tamaño y cantidad dependen de la aerolínea y del boleto.",
                "Weight, size and quantity depend on the airline and ticket.",
            ),
        },
        "important": _localized(
            language,
            "Para saber exactamente cuánto puedes llevar, revisa las condiciones de tu aerolínea.",
            "To know exactly how much you can bring, check your airline's conditions.",
        ),
    }

    return _response(
        True,
        result["important"],
        language=language,
        **result,
        sources=_sources(["tsa", "faa"]),
    )


# Compatibilidad con nombres usados en versiones anteriores.
def baggage_analysis(data: Any = None, **kwargs) -> dict:
    return baggage_rules(data, **kwargs)


# ============================================================
# ARTÍCULOS
# ============================================================

def _fallback_item(item: str, language: str) -> dict:
    item = _text(item)

    if language == "en":
        return {
            "item": item,
            "answer": "Check the official baggage rules and your airline before traveling.",
            "allowed": None,
            "carry_on": None,
            "checked": None,
            "reason": "The exact rule depends on the item and current requirements.",
            "sources": _sources(["tsa", "faa"]),
        }

    return {
        "item": item,
        "answer": "Revisa las reglas oficiales de equipaje y las condiciones de tu aerolínea antes de viajar.",
        "allowed": None,
        "carry_on": None,
        "checked": None,
        "reason": "La regla exacta depende del artículo y de los requisitos vigentes.",
        "sources": _sources(["tsa", "faa"]),
    }


def _gemini_prompt(item: str, language: str) -> str:
    if language == "en":
        return f"""
You are assisting a travel orientation application.
The user asks whether they can travel with this item: {item}

Do not invent rules.
Do not claim certainty when the official rule is unclear.
Give a short plain-language answer.
Official deterministic rules have priority.
Explain carry-on and checked baggage separately when possible.
Mention that the airline may have additional conditions.
Return JSON with:
item, answer, allowed, carry_on, checked, reason
""".strip()

    return f"""
Ayudas a una aplicación de orientación para viajeros.
El usuario pregunta si puede viajar con este artículo: {item}

No inventes reglas.
No afirmes certeza cuando la regla oficial no sea clara.
Da una respuesta corta y en lenguaje sencillo.
Las reglas oficiales tienen prioridad.
Explica por separado equipaje de mano y equipaje facturado cuando sea posible.
Indica que la aerolínea puede tener condiciones adicionales.
Devuelve JSON con:
item, answer, allowed, carry_on, checked, reason
""".strip()


def _gemini_item(item: str, language: str) -> dict | None:
    if not GEMINI_API_KEY:
        return None

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + GEMINI_MODEL
        + ":generateContent?key="
        + GEMINI_API_KEY
    )

    body = {
        "contents": [
            {
                "parts": [
                    {
                        "text": _gemini_prompt(item, language),
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    try:
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")

        payload = json.loads(raw)
        candidates = payload.get("candidates") or []
        if not candidates:
            return None

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )

        text = ""
        for part in parts:
            if part.get("text"):
                text += part["text"]

        text = text.strip()
        text = re.sub(r"^```json\s*", "", text, flags=re.I)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        result = json.loads(text)

        if not isinstance(result, dict):
            return None

        result["item"] = item
        result["sources"] = _sources(["tsa", "faa"])
        return result

    except Exception:
        return None


def item_analysis(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    item = ""
    if isinstance(data, dict):
        item = _text(
            data.get("item")
            or data.get("name")
            or data.get("question")
        )
    elif data is not None:
        item = _text(data)

    if not item:
        return _response(
            False,
            "Write the item you want to check."
            if language == "en"
            else "Escribe el artículo que quieres consultar.",
            language=language,
        )

    ai = _gemini_item(item, language)

    if ai:
        return _response(
            True,
            ai.get("answer", ""),
            language=language,
            item=item,
            result=ai,
            sources=ai.get("sources", _sources(["tsa", "faa"])),
        )

    fallback = _fallback_item(item, language)

    return _response(
        True,
        fallback["answer"],
        language=language,
        item=item,
        result=fallback,
        **fallback,
    )


def item_check(data: Any = None, **kwargs) -> dict:
    return item_analysis(data, **kwargs)


# ============================================================
# VUELOS
# ============================================================

def analyze_flight(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    origin = ""
    destination = "Cuba"
    date = ""

    if isinstance(data, dict):
        origin = _text(data.get("origin") or data.get("from"))
        destination = _text(
            data.get("destination") or data.get("to"),
            "Cuba",
        )
        date = _text(
            data.get("date")
            or data.get("departure_date")
            or data.get("departure"),
        )

    return _response(
        True,
        _localized(
            language,
            "Usa la búsqueda de vuelos y confirma la ruta directamente con la aerolínea.",
            "Use flight search and confirm the route directly with the airline.",
        ),
        language=language,
        origin=origin,
        destination=destination,
        date=date,
        search_url=OFFICIAL_URLS["flights"],
        airlines=get_airlines(),
        charters=get_charters(),
        sources=_sources(["google_flights"]),
    )


def flight_analysis(data: Any = None, **kwargs) -> dict:
    return analyze_flight(data, **kwargs)


# ============================================================
# RESERVA / PRÁCTICA
# ============================================================

def booking_simulation(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    steps_es = [
        _step(
            1,
            "Busca el vuelo",
            "Compara las opciones que aparecen para tu ruta.",
            "Search for the flight",
            "Compare the options shown for your route.",
            OFFICIAL_URLS["flights"],
        ),
        _step(
            2,
            "Abre la página de la aerolínea",
            "Antes de pagar, revisa la información directamente con la aerolínea.",
            "Open the airline website",
            "Before paying, review the information directly with the airline.",
            "",
        ),
        _step(
            3,
            "Revisa el vuelo",
            "Comprueba fecha, horario, pasajeros y equipaje.",
            "Review the flight",
            "Check the date, time, passengers and baggage.",
            "",
        ),
        _step(
            4,
            "Si compras, hazlo en el sitio que corresponda",
            "La aplicación no compra ni paga vuelos.",
            "If you buy, use the appropriate website",
            "This application does not buy or pay for flights.",
            "",
        ),
    ]

    steps = []
    for item in steps_es:
        steps.append(
            {
                **item,
                "title": item["title_en"] if language == "en" else item["title_es"],
                "text": item["text_en"] if language == "en" else item["text_es"],
            }
        )

    return _response(
        True,
        _localized(
            language,
            "Simulación de preparación. No es una compra real.",
            "Preparation simulation. This is not a real purchase.",
        ),
        language=language,
        steps=steps,
        simulation=steps,
        official=False,
        sources=_sources(["google_flights"]),
    )


def booking_analysis(data: Any = None, **kwargs) -> dict:
    return booking_simulation(data, **kwargs)


def connection_analysis(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    return _response(
        True,
        _localized(
            language,
            "Revisa cada tramo, la fecha y el tiempo entre vuelos directamente con la aerolínea.",
            "Check each flight segment, date and connection time directly with the airline.",
        ),
        language=language,
        sources=_sources(["google_flights"]),
    )


# ============================================================
# CUBA
# ============================================================

def cuba_check(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    return _response(
        True,
        _localized(
            language,
            "Para viajar a Cuba, revisa primero D'Viajeros, la visa que corresponda y tu vuelo.",
            "For travel to Cuba, first check D'Viajeros, the applicable visa and your flight.",
        ),
        language=language,
        dviajeros={
            "url": OFFICIAL_URLS["dviajeros"],
            "steps": dviajeros_simulation(data).get("steps", []),
        },
        visa={
            "url": OFFICIAL_URLS["evisa"],
            "routes": VISA_ROUTES,
        },
        flights={
            "url": OFFICIAL_URLS["flights"],
            "airlines": get_airlines(),
            "charters": get_charters(),
        },
        sources=_sources(["dviajeros", "evisa", "cubaminrex"]),
    )


def cuba_entry(data: Any = None, **kwargs) -> dict:
    language = _lang(data)
    return dviajeros_simulation(data, **kwargs)


def cuba_analysis(data: Any = None, **kwargs) -> dict:
    return cuba_check(data, **kwargs)


# ============================================================
# GUÍA
# ============================================================

def build_guide(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    dviajeros = dviajeros_simulation(data)
    visa = visa_simulation(data)

    return _response(
        True,
        _localized(
            language,
            "Guía básica para preparar un viaje a Cuba.",
            "Basic guide for preparing a trip to Cuba.",
        ),
        language=language,
        sections=[
            {
                "id": "dviajeros",
                "title": _localized(language, "D'Viajeros", "D'Viajeros"),
                "url": OFFICIAL_URLS["dviajeros"],
                "steps": dviajeros.get("steps", []),
            },
            {
                "id": "visa",
                "title": _localized(language, "Visa para Cuba", "Visa for Cuba"),
                "url": OFFICIAL_URLS["evisa"],
                "routes": visa.get("routes", []),
                "steps": visa.get("steps", []),
            },
            {
                "id": "flights",
                "title": _localized(language, "Vuelos a Cuba", "Flights to Cuba"),
                "url": OFFICIAL_URLS["flights"],
                "airlines": get_airlines(),
                "charters": get_charters(),
            },
        ],
        sources=_sources(["dviajeros", "evisa", "cubaminrex", "google_flights"]),
    )


def solve(data: Any = None, **kwargs) -> dict:
    language = _lang(data)

    question = ""
    if isinstance(data, dict):
        question = _text(
            data.get("question")
            or data.get("query")
            or data.get("message")
        )

    if not question:
        return build_guide(data, **kwargs)

    lower = question.lower()

    if "dviajero" in lower or "d'viajero" in lower:
        return dviajeros_simulation(data)

    if "visa" in lower:
        return visa_simulation(data)

    if any(x in lower for x in ("vuelo", "volar", "aerolínea", "aerolinea", "flight")):
        return analyze_flight(data)

    if any(x in lower for x in ("llevar", "equipaje", "maleta", "batería", "bateria")):
        return item_analysis(
            {
                "language": language,
                "item": question,
            }
        )

    return _response(
        True,
        _localized(
            language,
            "Revisa D'Viajeros, la visa y el vuelo en los sitios correspondientes.",
            "Check D'Viajeros, the visa and the flight on the corresponding websites.",
        ),
        language=language,
        sources=_sources(["dviajeros", "evisa", "google_flights"]),
    )


def answer(data: Any = None, **kwargs) -> dict:
    return solve(data, **kwargs)


# ============================================================
# SALUD DEL MOTOR
# ============================================================

def health(*args, **kwargs) -> dict:
    return {
        "ok": True,
        "success": True,
        "status": "ok",
        "engine": "cuba_engine",
        "version": VERSION,
        "source_registry_dependency": False,
        "gemini_configured": bool(GEMINI_API_KEY),
    }


# ============================================================
# COMPATIBILIDAD
# ============================================================

def dviajeros_analysis(data: Any = None, **kwargs) -> dict:
    return dviajeros_simulation(data, **kwargs)


def visa_analysis(data: Any = None, **kwargs) -> dict:
    return visa_simulation(data, **kwargs)


def airport_analysis(data: Any = None, **kwargs) -> dict:
    return analyze_flight(data, **kwargs)


def sources(data: Any = None, **kwargs) -> list:
    return get_sources()


# ============================================================
# EXPORTACIONES
# ============================================================

__all__ = [
    "VERSION",
    "APP",
    "SOURCES",
    "AIRLINES",
    "CHARTERS",
    "OFFICIAL_URLS",
    "source_by_id",
    "get_sources",
    "all_sources",
    "official_sources",
    "answer_sources",
    "official_url",
    "get_airlines",
    "get_charters",
    "dviajeros_simulation",
    "dviajeros_analysis",
    "visa_simulation",
    "visa_analysis",
    "practice_scenario",
    "document_analysis",
    "baggage_rules",
    "baggage_analysis",
    "item_analysis",
    "item_check",
    "analyze_flight",
    "flight_analysis",
    "booking_simulation",
    "booking_analysis",
    "connection_analysis",
    "cuba_check",
    "cuba_entry",
    "cuba_analysis",
    "build_guide",
    "solve",
    "answer",
    "health",
    "airport_analysis",
    "sources",
]
