# source_registry.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v10.0.0
from __future__ import annotations
from dataclasses import dataclass,asdict
from typing import Dict,List,Optional
import unicodedata

VERSION="10.0.0"
VERIFICATION_DATE="2026-10-03"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
OWNER="May Roga LLC"

@dataclass(frozen=True)
class Source:
    id:str
    name:str
    url:str
    category:str
    country:str=""
    official:bool=True
    kind:str="official"
    description:str=""
    topics:tuple=()
    active:bool=True

def S(id,name,url,category,country="",description="",topics=(),official=True,kind="official"):
    return Source(id,name,url,category,country,official,kind,description,tuple(topics))

SOURCES:List[Source]=[
S("dviajeros","D'Viajeros","https://dviajeros.mitrans.gob.cu/","cuba","Cuba","Portal oficial relacionado con la información anticipada del viajero para Cuba.",["dviajeros","entrada","viajero","cuba"]),
S("evisa_cuba","eVisa Cuba","https://evisacuba.cu/","cuba","Cuba","Portal oficial de eVisa Cuba para consultar y realizar el proceso correspondiente.",["visa","evisa","cuba","entrada"]),
S("aduana_cuba","Aduana General de la República de Cuba","https://www.aduana.gob.cu/","cuba","Cuba","Fuente oficial para información aduanera, equipaje y mercancías.",["aduana","equipaje","articulos","cuba"]),
S("minrex_cuba","Ministerio de Relaciones Exteriores de Cuba","https://cubaminrex.cu/","cuba","Cuba","Fuente institucional para información consular y relaciones exteriores.",["visa","consular","pasaporte","cuba"]),
S("cuba_travel","Cuba Travel","https://www.cuba.travel/","cuba","Cuba","Portal oficial de turismo de Cuba con información general y contactos de servicios turísticos.",["cuba","aeropuertos","destinos"]),
S("ecasa","ECASA","https://www.ecasa.avianet.cu/","cuba","Cuba","Referencia aeroportuaria cubana; comprobar siempre disponibilidad y datos actuales.",["aeropuerto","vuelos","cuba"]),
S("cubana","Cubana de Aviación","https://www.cubana.cu/","airline","Cuba","Sitio oficial de Cubana de Aviación.",["aerolinea","cuba","vuelos"]),
S("ofac_cuba","OFAC — Cuba Sanctions","https://ofac.treasury.gov/sanctions-programs-and-country-information/cuba-sanctions","usa","Estados Unidos","Fuente oficial de Estados Unidos para las reglas sobre transacciones y viajes autorizados a Cuba.",["cuba","viajes","ofac","usa"]),
S("ofac_faq","OFAC — Cuba FAQs","https://ofac.treasury.gov/faqs/topic/1541","usa","Estados Unidos","Preguntas frecuentes oficiales sobre las autorizaciones y restricciones relacionadas con Cuba.",["cuba","ofac","viajes"]),
S("state_cuba","U.S. Department of State — Cuba","https://travel.state.gov/content/travel/en/international-travel/International-Travel-Country-Information-Pages/Cuba.html","usa","Estados Unidos","Información oficial estadounidense para viajeros sobre Cuba.",["cuba","viaje","seguridad","consular"]),
S("cbp_travel","U.S. Customs and Border Protection","https://www.cbp.gov/travel","usa","Estados Unidos","Información oficial para entrada y salida de Estados Unidos.",["aduana","entrada","salida","usa"]),
S("tsa","TSA — What Can I Bring?","https://www.tsa.gov/travel/security-screening/whatcanibring/all","security","Estados Unidos","Herramienta oficial para consultar artículos permitidos en controles de seguridad de Estados Unidos.",["equipaje","articulos","seguridad","tsa"]),
S("tsa_travel","TSA Travel Tips","https://www.tsa.gov/travel/travel-tips","security","Estados Unidos","Consejos oficiales de TSA para pasajeros.",["seguridad","aeropuerto","equipaje"]),
S("faa","FAA","https://www.faa.gov/travelers","security","Estados Unidos","Información oficial estadounidense relacionada con seguridad y transporte aéreo.",["aviacion","seguridad"]),
S("iata","IATA Travel Centre","https://www.iatatravelcentre.com/","travel","Internacional","Fuente de referencia para requisitos de viaje; comprobar siempre el dato con la autoridad o aerolínea correspondiente.",["pasaporte","visa","entrada","viaje"]),
S("travel_state","Travel.State.Gov","https://travel.state.gov/","usa","Estados Unidos","Portal oficial del Departamento de Estado de Estados Unidos.",["viaje","pasaporte","visa"]),
S("travel_advisories","U.S. Travel Advisories","https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html","usa","Estados Unidos","Avisos oficiales de viaje del Departamento de Estado.",["seguridad","viaje"]),
S("american","American Airlines","https://www.aa.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí rutas, vuelos, equipaje, check-in y cambios.",["aerolinea","vuelos","equipaje","cuba"],kind="airline"),
S("delta","Delta Air Lines","https://www.delta.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí rutas, vuelos, equipaje y conexiones.",["aerolinea","vuelos","equipaje","cuba"],kind="airline"),
S("united","United Airlines","https://www.united.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí rutas, vuelos, equipaje y conexiones.",["aerolinea","vuelos","equipaje","cuba"],kind="airline"),
S("southwest","Southwest Airlines","https://www.southwest.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí vuelos y equipaje.",["aerolinea","vuelos","equipaje","cuba"],kind="airline"),
S("jetblue","JetBlue","https://www.jetblue.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí vuelos y equipaje.",["aerolinea","vuelos","equipaje","cuba"],kind="airline"),
S("spirit","Spirit Airlines","https://www.spirit.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí vuelos y equipaje.",["aerolinea","vuelos","equipaje","cuba"],kind="airline"),
S("frontier","Frontier Airlines","https://www.flyfrontier.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí vuelos y equipaje.",["aerolinea","vuelos","equipaje","cuba"],kind="airline"),
S("alaska","Alaska Airlines","https://www.alaskaair.com/","airline","Estados Unidos","Sitio oficial. Consultar aquí vuelos y equipaje.",["aerolinea","vuelos","equipaje"],kind="airline"),
S("avelo","Avelo Airlines","https://www.aveloair.com/","airline","Estados Unidos","Sitio oficial. Verificar directamente si existe servicio aplicable a la ruta consultada.",["aerolinea","vuelos","cuba"],kind="airline"),
S("sun_country","Sun Country Airlines","https://www.suncountry.com/","airline","Estados Unidos","Sitio oficial. Verificar directamente las rutas vigentes.",["aerolinea","vuelos"],kind="airline"),
S("copa","Copa Airlines","https://www.copaair.com/","airline","Panamá","Sitio oficial. Útil para consultar conexiones por Panamá y vuelos internacionales.",["aerolinea","vuelos","conexion","cuba"],kind="airline"),
S("avianca","Avianca","https://www.avianca.com/","airline","Colombia","Sitio oficial. Consultar rutas, conexiones y equipaje.",["aerolinea","vuelos","conexion","cuba"],kind="airline"),
S("latam","LATAM Airlines","https://www.latamairlines.com/","airline","Internacional","Sitio oficial. Consultar rutas, conexiones y equipaje.",["aerolinea","vuelos","conexion"],kind="airline"),
S("air_canada","Air Canada","https://www.aircanada.com/","airline","Canadá","Sitio oficial. Consultar rutas, conexiones y equipaje.",["aerolinea","vuelos","conexion","cuba"],kind="airline"),
S("air_europa","Air Europa","https://www.aireuropa.com/","airline","España","Sitio oficial. Consultar rutas y conexiones internacionales.",["aerolinea","vuelos","conexion","cuba"],kind="airline"),
S("iberia","Iberia","https://www.iberia.com/","airline","España","Sitio oficial. Consultar rutas y conexiones.",["aerolinea","vuelos","conexion","cuba"],kind="airline"),
S("air_france","Air France","https://wwws.airfrance.us/","airline","Francia","Sitio oficial. Consultar rutas y conexiones.",["aerolinea","vuelos","conexion","cuba"],kind="airline"),
S("condor","Condor","https://www.condor.com/","airline","Alemania","Sitio oficial. Consultar rutas internacionales.",["aerolinea","vuelos","cuba"],kind="airline"),
S("aeroflot","Aeroflot","https://www.aeroflot.com/","airline","Rusia","Sitio oficial. Consultar directamente rutas vigentes.",["aerolinea","vuelos","cuba"],kind="airline"),
S("world_atlantic","World Atlantic Airlines","https://www.worldatlantic.com/","charter","Estados Unidos","Operador asociado históricamente con operaciones charter; no implica disponibilidad actual de una ruta.",["charter","cuba","vuelos"],kind="charter"),
S("globalx","Global Crossing Airlines","https://www.globalxair.com/","charter","Estados Unidos","Operador de vuelos charter; comprobar la operación actual antes de presentar una ruta.",["charter","cuba","vuelos"],kind="charter"),
S("iaero","iAero Airways","https://www.iaeroairways.com/","charter","Estados Unidos","Operador de vuelos charter; comprobar la operación actual.",["charter","cuba","vuelos"],kind="charter"),
S("havana_air","Havana Air","https://www.havana-air.com/","charter","Estados Unidos","Referencia de servicios relacionados con viajes charter a Cuba; verificar disponibilidad actual.",["charter","cuba","vuelos"],kind="charter"),
S("aerocuba","Aerocuba","https://www.aerocuba.com/","charter","Estados Unidos","Referencia histórica de operaciones/servicios charter relacionados con Cuba; verificar estado actual.",["charter","cuba","vuelos"],kind="charter"),
S("cubazul","Cubazul","https://www.cubazulair.com/","charter","Estados Unidos","Referencia de vuelos charter relacionados con Cuba; verificar operación actual.",["charter","cuba","vuelos"],kind="charter"),
S("world_air_charter","World Air Charter","https://www.worldaircharter.com/","charter","Estados Unidos","Referencia de servicios charter; no asumir una ruta vigente sin verificación.",["charter","cuba","vuelos"],kind="charter"),
]

TOPICS:Dict[str,Dict]={
"flight":{"title":"Mi vuelo","description":"Entiende tu itinerario, aerolínea, segmentos, escalas, conexiones y qué debes verificar.","sources":["iata","american","delta","united","southwest","jetblue","spirit","frontier","copa","avianca","latam","air_canada","air_europa","iberia","air_france"],"fallback":"Si no podemos confirmar un dato del vuelo, consulta directamente la aerolínea y el aeropuerto."},
"booking":{"title":"Practicar una reserva","description":"Simulación educativa de búsqueda de vuelo. No compra, no reserva y no procesa pagos de vuelos.","sources":["american","delta","united","southwest","jetblue","spirit","frontier","copa","avianca","latam"],"fallback":"Los precios, horarios, disponibilidad y condiciones cambian. Confírmalos en la aerolínea o agencia correspondiente."},
"connection":{"title":"Escalas y conexiones","description":"Ayuda para entender una escala, cambio de avión, terminal, seguridad y equipaje.","sources":["iata","cbp_travel","tsa","american","delta","united","copa","avianca"],"fallback":"La forma de realizar una conexión depende del itinerario, aeropuerto, aerolínea y controles aplicables."},
"baggage":{"title":"Equipaje","description":"Distingue equipaje de mano, artículo personal, maleta facturada y artículos especiales.","sources":["tsa","american","delta","united","southwest","jetblue","spirit","frontier","copa","avianca","latam"],"fallback":"La seguridad y la aerolínea pueden aplicar reglas distintas. Comprueba ambas cuando corresponda."},
"items":{"title":"¿Qué quiero llevar?","description":"Ayuda a identificar qué autoridad o empresa debe comprobar un artículo.","sources":["tsa","aduana_cuba","cbp_travel"],"fallback":"Si el artículo no está claramente confirmado, no se debe presentar como permitido o prohibido. Consulta la fuente oficial."},
"cuba":{"title":"Viajo a Cuba","description":"Centro de preparación para viaje a Cuba.","sources":["dviajeros","evisa_cuba","aduana_cuba","minrex_cuba","cuba_travel","ecasa","ofac_cuba","state_cuba"],"fallback":"Los requisitos de entrada, aduana y viaje pueden cambiar. Confirma el requisito vigente en la autoridad correspondiente."},
"dviajeros":{"title":"D'Viajeros","description":"Información y práctica del proceso de D'Viajeros.","sources":["dviajeros"],"fallback":"La práctica de la aplicación no envía información al sistema oficial. Para el proceso real utiliza D'Viajeros oficial."},
"visa":{"title":"Visa / eVisa Cuba","description":"Información y simulación educativa del proceso de eVisa Cuba.","sources":["evisa_cuba","minrex_cuba"],"fallback":"La simulación no solicita ni transmite una solicitud real. El trámite real debe realizarse en el sitio oficial correspondiente."},
"customs":{"title":"Aduana de Cuba","description":"Consulta de reglas aduaneras y artículos para entrada a Cuba.","sources":["aduana_cuba"],"fallback":"No inventar límites, cantidades, valores ni autorizaciones. Confirmar siempre en Aduana."},
"documents":{"title":"Mis documentos","description":"Organización personal de documentos que el viajero debe revisar.","sources":["dviajeros","evisa_cuba","minrex_cuba","state_cuba","iata"],"fallback":"La lista es una herramienta de preparación y no sustituye la revisión oficial."},
"security":{"title":"Seguridad aeroportuaria","description":"Consulta de artículos y procedimientos de seguridad.","sources":["tsa","faa"],"fallback":"Las reglas de seguridad dependen de la autoridad y del aeropuerto. Verifica la fuente oficial."},
"usa_cuba":{"title":"Viajar desde Estados Unidos a Cuba","description":"Información para personas sujetas a jurisdicción estadounidense.","sources":["ofac_cuba","ofac_faq","state_cuba","cbp_travel"],"fallback":"La aplicación no determina si un viaje está autorizado legalmente para una persona concreta. Consulta OFAC y las autoridades correspondientes."},
"airlines":{"title":"Aerolíneas","description":"Directorio de sitios oficiales para comprobar vuelos y condiciones.","sources":["american","delta","united","southwest","jetblue","spirit","frontier","copa","avianca","latam","air_canada","air_europa","iberia","air_france","condor","aeroflot","cubana"],"fallback":"La presencia de una aerolínea en este registro no significa que opere actualmente una ruta determinada."},
"charter":{"title":"Charters a Cuba","description":"Directorio de operadores y referencias de vuelos charter relacionados con Cuba.","sources":["world_atlantic","globalx","iaero","havana_air","aerocuba","cubazul","world_air_charter"],"fallback":"Charter no significa ruta disponible. La operación, fecha, operador y ciudad deben verificarse antes de viajar."},
"official":{"title":"Fuentes oficiales","description":"Acceso organizado a fuentes oficiales según la pregunta del viajero.","sources":["dviajeros","evisa_cuba","aduana_cuba","minrex_cuba","ofac_cuba","state_cuba","cbp_travel","tsa","iata"],"fallback":"Cuando un dato no esté confirmado, la fuente oficial es la referencia final."}
}

SIMULATIONS:Dict[str,Dict]={
"booking":{
"title":"PRÁCTICA — BUSCAR UN VUELO",
"notice":"Simulación educativa. No compra, no reserva y no procesa pagos.",
"steps":[
{"id":"route","title":"Ruta","fields":["origin","destination"],"help":"Introduce desde dónde quieres salir y a dónde quieres llegar."},
{"id":"dates","title":"Fechas","fields":["departure","return"],"help":"En una reserva real las fechas determinan qué vuelos y tarifas pueden aparecer."},
{"id":"passengers","title":"Pasajeros","fields":["adults","children","infants"],"help":"La cantidad y edad de los pasajeros puede modificar la búsqueda real."},
{"id":"cabin","title":"Preferencias","fields":["cabin","bags"],"help":"La clase y el equipaje pueden cambiar las condiciones del viaje."},
{"id":"results","title":"Resultados","fields":["sort","flight"],"help":"Los resultados de esta práctica son ejemplos educativos y no representan disponibilidad real."},
{"id":"review","title":"Revisión","fields":["route","dates","passengers","flight"],"help":"Antes de comprar un vuelo real debes revisar las condiciones directamente con el proveedor."}
]},
"dviajeros":{
"title":"PRÁCTICA — D'VIAJEROS",
"notice":"SIMULACIÓN. Esta pantalla no pertenece al Gobierno de Cuba y no envía datos a D'Viajeros.",
"steps":[
{"id":"traveler","title":"Datos del viajero","fields":["given_names","surnames","birth_date","nationality","sex"],"help":"La plataforma oficial solicita datos personales del viajero."},
{"id":"passport","title":"Documento","fields":["passport_number","passport_country"],"help":"En un trámite real debes utilizar el documento válido que corresponda."},
{"id":"travel","title":"Viaje","fields":["arrival_date","flight","arrival_airport"],"help":"La información del viaje debe coincidir con tu documentación y vuelo real."},
{"id":"contact","title":"Contacto","fields":["email","phone"],"help":"Los datos de contacto deben introducirse solamente en el sitio oficial cuando realices el proceso real."},
{"id":"review","title":"Revisión","fields":["traveler","passport","travel","contact"],"help":"Revisa cuidadosamente antes de completar un proceso real."}
]},
"visa":{
"title":"PRÁCTICA — eVISA CUBA",
"notice":"SIMULACIÓN. No es una solicitud real y no envía datos al sistema eVisa-Cuba.",
"steps":[
{"id":"nationality","title":"Nacionalidad","fields":["nationality"],"help":"El proceso oficial comienza identificando la nacionalidad del solicitante."},
{"id":"passport","title":"Pasaporte","fields":["passport_number","surname","given_names"],"help":"El sitio oficial de eVisa solicita información del documento y del viajero."},
{"id":"birth","title":"Datos personales","fields":["birth_date","sex"],"help":"Son datos que aparecen en el proceso oficial consultado."},
{"id":"contact","title":"Contacto","fields":["email","phone"],"help":"La plataforma oficial contempla información de contacto."},
{"id":"review","title":"Revisión","fields":["nationality","passport","birth","contact"],"help":"La práctica termina aquí. La solicitud real debe realizarse en la plataforma oficial."}
]},
"connection":{
"title":"PRÁCTICA — MI ESCALA",
"notice":"Simulación educativa de una conexión aérea.",
"steps":[
{"id":"arrival","title":"Llegas al aeropuerto","fields":["airport","terminal","arrival_gate"],"help":"Primero identifica dónde llegaste y qué información aparece en tu itinerario."},
{"id":"next","title":"Siguiente vuelo","fields":["next_flight","next_gate","terminal"],"help":"Busca el siguiente segmento y comprueba la puerta o terminal."},
{"id":"plane","title":"¿Cambio de avión?","fields":["same_aircraft"],"help":"No todos los itinerarios funcionan igual. Comprueba el itinerario y las instrucciones de la aerolínea."},
{"id":"security","title":"Controles","fields":["security","immigration","customs"],"help":"Los controles dependen del aeropuerto, país, itinerario y conexión."},
{"id":"baggage","title":"Equipaje","fields":["bag_recheck"],"help":"No debes asumir que siempre recoges o vuelves a entregar la maleta; verifica las instrucciones del itinerario."}
]},
"airport":{
"title":"PRÁCTICA — LLEGUÉ AL AEROPUERTO",
"notice":"Entrenamiento para entender qué hacer durante el viaje.",
"steps":[
{"id":"checkin","title":"Check-in","fields":["boarding_pass","bag_drop"],"help":"Comprueba si tienes tarjeta de embarque y si necesitas entregar equipaje."},
{"id":"security","title":"Seguridad","fields":["security_lane"],"help":"Sigue las instrucciones del aeropuerto y de seguridad."},
{"id":"gate","title":"Puerta","fields":["gate","boarding_time"],"help":"La puerta y el horario pueden cambiar. Comprueba las pantallas y la aerolínea."},
{"id":"boarding","title":"Embarque","fields":["group","seat"],"help":"Sigue las instrucciones de tu tarjeta de embarque y del personal."}
]}
}

ITEM_RULES:Dict[str,Dict]={
"liquidos":{"keywords":["liquido","líquido","agua","perfume","shampoo","champu","crema","gel","locion","loción"],"authority":["tsa","airline","aduana_cuba"],"message":"Primero hay que distinguir seguridad aeroportuaria, equipaje de la aerolínea y reglas de entrada al destino."},
"medicamentos":{"keywords":["medicamento","medicina","pastilla","farmaco","fármaco","jarabe","medicine"],"authority":["tsa","airline","aduana_cuba"],"message":"No basta con saber si pasa seguridad. También pueden existir requisitos del país de destino y documentación."},
"alimentos":{"keywords":["comida","alimento","carne","queso","fruta","frutas","semillas","food"],"authority":["tsa","aduana_cuba"],"message":"La seguridad del aeropuerto y las reglas de importación del destino son cuestiones diferentes."},
"baterias":{"keywords":["bateria","batería","power bank","litio","lithium","battery"],"authority":["tsa","airline"],"message":"Las baterías pueden tener reglas específicas de seguridad y de la aerolínea."},
"electronicos":{"keywords":["telefono","teléfono","tablet","laptop","computadora","camara","cámara","electronico","electrónico"],"authority":["tsa","airline","aduana_cuba"],"message":"Los controles de seguridad y las reglas del destino deben comprobarse por separado."},
"herramientas":{"keywords":["herramienta","taladro","martillo","cuchillo","knife","tool"],"authority":["tsa","airline","aduana_cuba"],"message":"Un artículo puede estar sujeto a restricciones distintas según vaya en cabina, equipaje facturado o entrada al país."}
}

AIRLINE_GROUPS={
"commercial_us":["american","delta","united","southwest","jetblue","spirit","frontier","alaska","avelo","sun_country"],
"commercial_international":["copa","avianca","latam","air_canada","air_europa","iberia","air_france","condor","aeroflot","cubana"],
"charter":["world_atlantic","globalx","iaero","havana_air","aerocuba","cubazul","world_air_charter"]
}

def _norm(value:str)->str:
    value=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode().lower()
    return " ".join(value.split())

def all_sources()->List[Dict]:
    return [asdict(x) for x in SOURCES if x.active]

def registry()->List[Dict]:
    return all_sources()

def get_source(source_id:str)->Optional[Dict]:
    for source in SOURCES:
        if source.id==source_id and source.active:return asdict(source)
    return None

def get_sources(ids:List[str])->List[Dict]:
    return [x for x in (get_source(i) for i in ids) if x]

def official_sources()->List[Dict]:
    return [asdict(x) for x in SOURCES if x.active and x.official]

def airline_sources(group:Optional[str]=None)->List[Dict]:
    ids=[]
    if group in AIRLINE_GROUPS:ids=AIRLINE_GROUPS[group]
    else:
        ids=AIRLINE_GROUPS["commercial_us"]+AIRLINE_GROUPS["commercial_international"]+AIRLINE_GROUPS["charter"]
    return get_sources(ids)

def cuba_sources()->List[Dict]:
    return get_sources(TOPICS["cuba"]["sources"])

def topic(topic_id:str)->Dict:
    t=TOPICS.get(topic_id)
    if not t:return {"id":topic_id,"title":"Información","description":"","sources":[],"fallback":"No hay información verificada disponible. Consulta la fuente oficial correspondiente."}
    return {"id":topic_id,**t,"source_data":get_sources(t["sources"])}

def topics()->List[Dict]:
    return [{"id":k,"title":v["title"],"description":v["description"]} for k,v in TOPICS.items()]

def simulation(sim_id:str)->Dict:
    sim=SIMULATIONS.get(sim_id)
    if not sim:return {"id":sim_id,"title":"Práctica","notice":"No existe esta simulación.","steps":[]}
    return {"id":sim_id,**sim}

def simulations()->List[Dict]:
    return [{"id":k,"title":v["title"],"notice":v["notice"],"steps":v["steps"]} for k,v in SIMULATIONS.items()]

def item_lookup(item:str)->Dict:
    q=_norm(item)
    for category,data in ITEM_RULES.items():
        if any(_norm(word) in q for word in data["keywords"]):
            return {"item":item,"category":category,"message":data["message"],"authorities":data["authority"],"sources":get_sources(data["authority"]),"status":"verify"}
    return {"item":item,"category":"unknown","message":"No hay una regla suficientemente específica en el registro para confirmar este artículo. No lo presentamos como permitido ni prohibido.","authorities":["airline","security","destination_customs"],"sources":[get_source("tsa"),get_source("aduana_cuba")],"status":"official_check_required"}

def source_for_question(question:str)->Dict:
    q=_norm(question)
    if any(x in q for x in ["dviajero","d viajeros","formulario de entrada"]):return topic("dviajeros")
    if any(x in q for x in ["visa","evisa","visado"]):return topic("visa")
    if any(x in q for x in ["aduana","importar","entrar con","mercancia","mercancía"]):return topic("customs")
    if any(x in q for x in ["maleta","equipaje","carry on","equipaje de mano"]):return topic("baggage")
    if any(x in q for x in ["escala","conexion","conexión","stop","cambiar avion","cambiar avión"]):return topic("connection")
    if any(x in q for x in ["cuba","cubano","cubana"]):return topic("cuba")
    if any(x in q for x in ["tsa","seguridad","checkpoint","control"]):return topic("security")
    if any(x in q for x in ["ofac","viajar desde estados unidos","viaje a cuba desde usa"]):return topic("usa_cuba")
    if any(x in q for x in ["charter","chárter"]):return topic("charter")
    if any(x in q for x in ["aerolinea","aerolínea","airline","vuelo"]):return topic("airlines")
    return topic("official")

def legal_notice()->Dict:
    return {
        "title":"Aviso importante",
        "text":"¿QUÉ QUIERES LLEVAR? es un servicio independiente de May Roga LLC. No es gobierno, aerolínea, aeropuerto, autoridad migratoria, aduana ni proveedor de reservas. Las simulaciones son educativas y no envían solicitudes reales. Los requisitos, rutas, horarios, tarifas, disponibilidad y reglas pueden cambiar. Cuando un dato no esté verificado, la aplicación debe dirigir al usuario a la fuente oficial correspondiente.",
        "simulation_notice":"Las prácticas no son trámites oficiales y no deben utilizarse para enviar información real.",
        "data_notice":"No introduzcas contraseñas, códigos de seguridad, datos bancarios, CVV ni credenciales de terceros."
    }

def source_map()->Dict:
    return {"version":VERSION,"verification_date":VERIFICATION_DATE,"topics":topics(),"simulations":simulations(),"airlines":airline_sources(),"cuba":cuba_sources(),"official":official_sources()}

__all__=[
"SOURCES","TOPICS","SIMULATIONS","ITEM_RULES","AIRLINE_GROUPS","VERSION","VERIFICATION_DATE",
"all_sources","registry","get_source","get_sources","official_sources","airline_sources",
"cuba_sources","topic","topics","simulation","simulations","item_lookup","source_for_question",
"legal_notice","source_map"
]
