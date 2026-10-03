# flight_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v9.0.0
from typing import Any,Dict,List,Optional
from source_registry import sources_for_flight

VERSION="9.0.0"

def _s(value:Any)->str:
    return str(value or "").strip()

def _l(value:Any)->str:
    return _s(value).lower()

def _lang(value:Any)->str:
    return "en" if _l(value)=="en" else "es"

def _has(value:Any)->bool:
    return bool(_s(value))

def _destination_is_cuba(destination:str)->bool:
    d=_l(destination)
    return d in {"cuba","cu","cuban","havana","la habana","hav"} or "cuba" in d

def understand_flight(data:Dict[str,Any])->Dict[str,Any]:
    lang=_lang(data.get("language"))
    origin=_s(data.get("origin"))
    destination=_s(data.get("destination"))
    departure_date=_s(data.get("departure_date"))
    return_date=_s(data.get("return_date"))
    airline=_s(data.get("airline"))
    cabin=_s(data.get("cabin"))
    fare=_s(data.get("fare"))
    passengers=data.get("passengers")
    stops=data.get("stops")
    missing=[]
    if not origin:missing.append("origin")
    if not destination:missing.append("destination")
    if missing:
        return {
            "ok":False,
            "version":VERSION,
            "language":lang,
            "missing":missing,
            "title":"Falta información" if lang=="es" else "Information needed",
            "message":"Indica desde dónde viajas y a dónde viajas." if lang=="es" else "Tell us where you are traveling from and where you are traveling to.",
            "steps":[],
            "sources":[]
        }
    cuba=_destination_is_cuba(destination)
    steps=[]
    def add(key_es,key_en,text_es,text_en,important=False):
        steps.append({
            "id":key_es,
            "title":key_es if lang=="es" else key_en,
            "text":text_es if lang=="es" else text_en,
            "important":important
        })
    add("Ruta","Route",f"Viaje: {origin} → {destination}",f"Trip: {origin} → {destination}",True)
    if departure_date:
        add("Salida","Departure","Fecha de salida: "+departure_date,"Departure date: "+departure_date)
    else:
        add("Fecha de salida","Departure date","Confirma la fecha de salida.","Confirm your departure date.",True)
    if return_date:
        add("Regreso","Return","Fecha de regreso: "+return_date,"Return date: "+return_date)
    if airline:
        add("Aerolínea","Airline","Aerolínea indicada: "+airline,"Airline provided: "+airline,True)
    else:
        add("Aerolínea","Airline","Confirma la aerolínea de tu vuelo.","Confirm the airline for your flight.",True)
    if cabin:
        add("Cabina","Cabin","Cabina indicada: "+cabin,"Cabin provided: "+cabin)
    if fare:
        add("Tarifa","Fare","Tarifa indicada: "+fare,"Fare provided: "+fare)
    if passengers not in (None,""):
        add("Pasajeros","Passengers",f"Pasajeros: {passengers}",f"Passengers: {passengers}")
    if stops not in (None,""):
        add("Escala","Connection","Escalas indicadas: "+str(stops),"Connections indicated: "+str(stops),True)
    else:
        add("Escala","Connection","Confirma si el vuelo tiene escala y revisa qué ocurre durante la conexión.","Confirm whether the flight has a connection and check what happens during the connection.",True)
    if cuba:
        add(
            "Cuba","Cuba",
            "Si viajas a Cuba, revisa por separado los requisitos de entrada, documentación, visa o eVisa, D’Viajeros y aduanas en las fuentes oficiales.",
            "If you are traveling to Cuba, separately check entry requirements, documents, visa or eVisa, D’Viajeros and customs through the official sources.",
            True
        )
    add(
        "Confirmación oficial","Official confirmation",
        "Antes de viajar, confirma las condiciones actuales con la aerolínea y las autoridades correspondientes.",
        "Before traveling, confirm the current conditions with the airline and the relevant authorities.",
        True
    )
    sources=sources_for_flight(origin,destination,airline)
    return {
        "ok":True,
        "version":VERSION,
        "language":lang,
        "title":"Tu vuelo" if lang=="es" else "Your flight",
        "message":"Esta es una guía de preparación. Las condiciones finales deben confirmarse en las fuentes oficiales." if lang=="es" else "This is a preparation guide. Final conditions must be confirmed with official sources.",
        "trip":{
            "origin":origin,
            "destination":destination,
            "departure_date":departure_date,
            "return_date":return_date,
            "airline":airline,
            "cabin":cabin,
            "fare":fare,
            "passengers":passengers,
            "stops":stops
        },
        "steps":steps,
        "sources":sources
    }

def search_flight(data:Dict[str,Any])->Dict[str,Any]:
    lang=_lang(data.get("language"))
    origin=_s(data.get("origin"))
    destination=_s(data.get("destination"))
    airline=_s(data.get("airline"))
    if not origin or not destination:
        return {
            "ok":False,
            "version":VERSION,
            "language":lang,
            "message":"Indica origen y destino." if lang=="es" else "Enter origin and destination.",
            "results":[],
            "sources":[]
        }
    results=[{
        "origin":origin,
        "destination":destination,
        "airline":airline,
        "message":"No se inventan vuelos, horarios ni disponibilidad. Usa la aerolínea o proveedor oficial para consultar el vuelo real." if lang=="es" else "Flights, schedules and availability are not invented. Use the official airline or provider to check the real flight."
    }]
    return {
        "ok":True,
        "version":VERSION,
        "language":lang,
        "results":results,
        "sources":sources_for_flight(origin,destination,airline)
    }

def flight_sources(data:Optional[Dict[str,Any]]=None)->Dict[str,Any]:
    data=data or {}
    lang=_lang(data.get("language"))
    origin=_s(data.get("origin"))
    destination=_s(data.get("destination"))
    airline=_s(data.get("airline"))
    return {
        "ok":True,
        "version":VERSION,
        "language":lang,
        "sources":sources_for_flight(origin,destination,airline)
    }

def validate_flight(data:Dict[str,Any])->List[str]:
    missing=[]
    if not _has(data.get("origin")):missing.append("origin")
    if not _has(data.get("destination")):missing.append("destination")
    return missing
