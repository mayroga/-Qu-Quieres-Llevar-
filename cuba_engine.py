# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v11.0.0
from __future__ import annotations
from typing import Any,Dict,List
import re

VERSION="11.0.0"

CUBA_TERMS={
    "cuba","cu","republica de cuba","república de cuba",
    "havana","habana","la habana"
}

def s(v:Any)->str:
    return str(v or "").strip()

def low(v:Any)->str:
    return s(v).lower()

def truth(v:Any)->bool:
    if isinstance(v,bool):
        return v
    return low(v) in {"1","true","yes","si","sí","y","on"}

def is_cuba(v:Any)->bool:
    x=low(v)
    return x in CUBA_TERMS or "cuba" in x

def unique(items:List[str])->List[str]:
    out=[]
    for x in items:
        if x and x not in out:
            out.append(x)
    return out

def _sources(topic:str="",query:str="")->List[Dict[str,Any]]:
    try:
        import source_registry as SR
        for name in ("get_sources","sources_for","find_sources","official_sources"):
            fn=getattr(SR,name,None)
            if callable(fn):
                try:
                    r=fn(topic,query)
                    if isinstance(r,dict):
                        r=r.get("sources") or r.get("official") or []
                    if isinstance(r,list):
                        return r
                except Exception:
                    pass
    except Exception:
        pass
    return []

def _source(topic:str,query:str="")->List[Dict[str,Any]]:
    return _sources(topic,query)

def cuba_profile(data:Dict[str,Any])->str:
    cuban=truth(data.get("cuban_nationality"))
    dual=truth(data.get("dual_citizen"))
    nationality=s(data.get("nationality"))
    passport=s(data.get("passport_country"))
    if cuban and dual:
        return "Ciudadano cubano con doble nacionalidad"
    if cuban:
        return "Ciudadano cubano"
    if dual:
        return "Viajero con doble nacionalidad"
    if nationality:
        return f"Viajero de nacionalidad {nationality}"
    if passport:
        return f"Viajero con pasaporte de {passport}"
    return "Perfil de viajero pendiente de confirmar"

def cuba_check(data:Dict[str,Any])->Dict[str,Any]:
    nationality=s(data.get("nationality"))
    passport=s(data.get("passport_country"))
    origin=s(data.get("origin"))
    airline=s(data.get("airline"))
    flight_type=s(data.get("flight_type"))
    cuban=truth(data.get("cuban_nationality"))
    dual=truth(data.get("dual_citizen"))
    checklist=[
        {
            "id":"identity",
            "title":"Nacionalidad y pasaporte",
            "status":"done" if nationality or passport else "pending",
            "explanation":"Primero debemos saber qué nacionalidad tienes y con qué documento viajarás."
        },
        {
            "id":"passport",
            "title":"Documento de viaje",
            "status":"done" if passport else "pending",
            "explanation":"Revisa el documento con el que realizarás el viaje y las condiciones oficiales que le correspondan."
        },
        {
            "id":"entry",
            "title":"Entrada a Cuba",
            "status":"pending",
            "explanation":"La necesidad de determinados documentos depende de la situación concreta del viajero y de las reglas oficiales vigentes."
        },
        {
            "id":"visa",
            "title":"Visa/eVisa cuando corresponda",
            "status":"done" if truth(data.get("visa_checked")) else "pending",
            "explanation":"No se debe asumir que todos los viajeros tienen el mismo requisito."
        },
        {
            "id":"dviajeros",
            "title":"D’Viajeros",
            "status":"done" if truth(data.get("dviajeros_done")) else "pending",
            "explanation":"La aplicación puede ayudarte a practicar y entender la información antes de utilizar el sitio oficial."
        },
        {
            "id":"customs",
            "title":"Aduana y artículos",
            "status":"done" if truth(data.get("customs_checked")) else "pending",
            "explanation":"Lo que puedes transportar y lo que puedes introducir en el país no siempre es exactamente la misma pregunta."
        }
    ]
    details=[
        "Cuba no se debe tratar como una sola pregunta. Hay que separar documentación, entrada, vuelo, equipaje, artículos, D’Viajeros y aduana.",
        "La nacionalidad y el documento con el que viajas pueden cambiar qué información necesitas comprobar.",
        "Si tienes nacionalidad cubana o doble nacionalidad, revisa específicamente la información oficial aplicable a tu situación.",
        "La aerolínea también puede tener condiciones propias para aceptar pasajeros y equipaje.",
        "La aplicación organiza las verificaciones; no sustituye la decisión de una autoridad."
    ]
    if origin:
        details.append(f"Origen indicado: {origin}.")
    if airline:
        details.append(f"Aerolínea indicada: {airline}.")
    if flight_type:
        details.append(f"Tipo de vuelo indicado: {flight_type}.")
    if nationality:
        details.append(f"Nacionalidad indicada: {nationality}.")
    if passport:
        details.append(f"Pasaporte indicado: {passport}.")
    if cuban or dual:
        details.append("Tu situación incluye nacionalidad cubana o doble nacionalidad; no conviene aplicar automáticamente las reglas de otro viajero.")
    pending=[x["title"] for x in checklist if x["status"]=="pending"]
    return {
        "ok":True,
        "title":"Preparación para Cuba",
        "message":"Vamos a separar tu viaje en pasos pequeños para que puedas saber exactamente qué revisar.",
        "status":"verify" if pending else "ready",
        "traveler_profile":cuba_profile(data),
        "details":details,
        "checklist":checklist,
        "questions":[
            "¿Con qué pasaporte viajarás?",
            "¿Tienes nacionalidad cubana?",
            "¿Tienes doble nacionalidad?",
            "¿Necesitas verificar visa/eVisa?",
            "¿Ya revisaste D’Viajeros?",
            "¿Ya revisaste qué artículos llevarás?"
        ],
        "next_action":pending[0] if pending else "Confirma nuevamente las fuentes oficiales antes del viaje.",
        "sources":_source("cuba")
    }

analyze_cuba=cuba_check
cuba_analysis=cuba_check
cuba_entry_check=cuba_check

def baggage_type_name(value:str)->str:
    x=low(value)
    if any(k in x for k in ["personal","artículo personal","articulo personal","personal item"]):
        return "Artículo personal"
    if any(k in x for k in ["carry","cabina","mano","hand"]):
        return "Equipaje de cabina"
    if any(k in x for k in ["checked","documentado","facturado","registrado","bodega"]):
        return "Equipaje documentado"
    return "Tipo de equipaje no confirmado"

def baggage_type_explanation(value:str)->str:
    name=baggage_type_name(value)
    if name=="Artículo personal":
        return "Es el objeto pequeño que la aerolínea permite llevar como artículo personal. No debe confundirse con una maleta de cabina."
    if name=="Equipaje de cabina":
        return "Es la maleta o pieza que la aerolínea permite llevar contigo en la cabina, si tu tarifa y sus condiciones la incluyen."
    if name=="Equipaje documentado":
        return "Es la maleta que entregas a la aerolínea antes de pasar a la zona de embarque y que viaja en la bodega del avión."
    return "Primero necesitamos saber si hablas de una pieza que llevas contigo o de una que entregas a la aerolínea."

def baggage_rules(data:Dict[str,Any])->Dict[str,Any]:
    typ=baggage_type_name(s(data.get("type")))
    item=s(data.get("item"))
    airline=s(data.get("airline"))
    fare=s(data.get("fare"))
    cabin=s(data.get("cabin"))
    destination=s(data.get("destination"))
    details=[
        baggage_type_explanation(s(data.get("type"))),
        "El nombre del equipaje no determina por sí solo cuántas piezas puedes llevar.",
        "La cantidad, peso y medidas pueden depender de la aerolínea, tarifa, cabina y ruta.",
        "Una regla de la aerolínea no sustituye las reglas de seguridad.",
        "Las reglas para transportar un artículo y las reglas para introducirlo en otro país pueden ser diferentes."
    ]
    missing=[]
    if not airline:
        missing.append("Aerolínea")
    if not fare:
        missing.append("Tarifa")
    if not cabin:
        missing.append("Cabina")
    if not destination:
        missing.append("Destino")
    if item:
        details.append(f"Artículo asociado: {item}.")
    if fare:
        details.append(f"Tarifa indicada: {fare}.")
    if cabin:
        details.append(f"Cabina indicada: {cabin}.")
    if data.get("weight") not in (None,""):
        details.append(f"Peso indicado: {data.get('weight')}. Debe compararse con el límite oficial aplicable.")
    if s(data.get("dimensions")):
        details.append(f"Medidas indicadas: {s(data.get('dimensions'))}. Deben compararse con las medidas oficiales.")
    return {
        "ok":True,
        "title":"Entiende tu equipaje",
        "message":"Antes de empacar, necesitamos separar tres preguntas: qué tipo de equipaje tienes, qué permite tu tarifa y si el artículo tiene reglas especiales.",
        "status":"verify" if missing else "verify",
        "baggage_type":typ,
        "human_explanation":baggage_type_explanation(s(data.get("type"))),
        "placement":"Según el tipo seleccionado, puede ir contigo en cabina o entregarse antes del embarque. La ubicación exacta debe confirmarse con la aerolínea.",
        "details":details,
        "questions":[
            "¿Es una mochila pequeña o una maleta?",
            "¿La quieres llevar contigo dentro del avión?",
            "¿La vas a entregar antes de subir?",
            "¿Tu tarifa incluye esa pieza?",
            "¿Cuánto pesa y cuánto mide?"
        ],
        "authorities":["Aerolínea","Seguridad del transporte","Autoridad del destino cuando corresponda"],
        "missing_information":missing,
        "sources":_source("baggage",airline),
        "next_action":"Busca la sección oficial de equipaje de tu aerolínea y compara tu tarifa, piezas, peso y medidas."
    }

analyze_baggage=baggage_rules
baggage_analysis=baggage_rules
check_baggage=baggage_rules
baggage_check=baggage_rules

def _contains(text:str,words:List[str])->bool:
    x=low(text)
    return any(w in x for w in words)

def item_analysis(data:Dict[str,Any])->Dict[str,Any]:
    item=s(data.get("item"))
    description=s(data.get("description"))
    airline=s(data.get("airline"))
    destination=s(data.get("destination"))
    baggage=s(data.get("baggage_type"))
    text=f"{item} {description}".lower()
    if not item:
        return {
            "ok":False,
            "title":"Dime qué quieres llevar",
            "message":"Escribe el artículo con palabras sencillas.",
            "next_action":"Por ejemplo: perfume, medicamentos, comida, laptop, batería, cámara o herramienta."
        }
    category="Artículo por verificar"
    status="verify"
    placement="Debe determinarse después de revisar las reglas aplicables."
    authorities=["Aerolínea"]
    details=[]
    missing=[]
    if _contains(text,["medic","medicine","pill","pastilla","tableta","fármaco","farmaco"]):
        category="Medicamentos"
        authorities+=["Seguridad del transporte","Reglas de entrada del destino"]
        placement="No decidas todavía si va en cabina o documentado solo por el tamaño. Primero revisa las reglas aplicables al medicamento y al transporte."
        details=[
            "No todos los medicamentos deben tratarse de la misma manera.",
            "El transporte y la entrada al país son preguntas diferentes.",
            "Si existe una condición especial para el medicamento, debes confirmarla antes del viaje."
        ]
        missing+=["Nombre exacto del medicamento","Destino","Regla oficial del destino"]
    elif _contains(text,["power bank","bater","batería","litio","lithium"]):
        category="Baterías"
        authorities+=["Seguridad del transporte"]
        placement="La ubicación de una batería depende del tipo y de las reglas aplicables. No la coloques automáticamente en el equipaje documentado."
        details=[
            "Las baterías requieren una revisión específica.",
            "El tamaño o capacidad puede ser relevante.",
            "La regla puede distinguir entre una batería instalada y una batería de repuesto."
        ]
        missing+=["Tipo de batería","Capacidad o especificación","Aerolínea"]
    elif _contains(text,["líquido","liquido","liquid","perfume","shampoo","champú","gel","aerosol","spray"]):
        category="Líquidos/aerosoles"
        authorities+=["Seguridad del transporte"]
        placement="La respuesta depende del producto, cantidad, recipiente y reglas de seguridad aplicables."
        details=[
            "No confundas la regla de seguridad con la regla de equipaje de la aerolínea.",
            "Un producto puede tener condiciones diferentes según cantidad y forma de transporte."
        ]
        missing+=["Cantidad","Tipo de producto","Tipo de equipaje"]
    elif _contains(text,["comida","food","carne","meat","fruta","fruit","vegetal","vegetable","queso","cheese","semilla","seed"]):
        category="Alimentos/productos de origen"
        authorities+=["Seguridad del transporte","Aduana/autoridad del destino"]
        placement="Que un alimento pueda viajar en el avión no significa automáticamente que pueda entrar al país."
        details=[
            "Primero revisa si puede transportarse.",
            "Después revisa si puede introducirse en el destino.",
            "Los alimentos y productos de origen animal o vegetal pueden tener controles adicionales."
        ]
        missing+=["País de destino","Tipo exacto de alimento","Cantidad"]
    elif _contains(text,["animal","perro","gato","mascota","pet"]):
        category="Animal/mascota"
        authorities+=["Seguridad del transporte","Aerolínea","Autoridad de entrada del destino"]
        placement="No decidas el transporte del animal sin revisar primero las condiciones de la aerolínea y del destino."
        details=[
            "Puede haber requisitos de transporte y requisitos de entrada separados.",
            "La aerolínea puede exigir procedimientos previos."
        ]
        missing+=["Tipo de animal","Destino","Aerolínea"]
    elif _contains(text,["arma","weapon","munición","munition","cuchillo","knife","explosivo"]):
        category="Artículo restringido"
        authorities+=["Seguridad del transporte","Autoridades competentes"]
        status="review"
        placement="No lo coloques en ningún equipaje hasta comprobar la regla específica."
        details=[
            "No se debe asumir que un artículo restringido puede transportarse simplemente porque cabe en una maleta.",
            "Las reglas pueden variar según el objeto, país y situación."
        ]
    elif _contains(text,["laptop","computadora","ordenador","tablet","teléfono","telefono","phone","cámara","camara","camera"]):
        category="Electrónico"
        authorities+=["Seguridad del transporte"]
        placement="Puede requerir una revisión específica según el equipo, batería y procedimiento de seguridad."
        details=[
            "El equipo y su batería deben considerarse por separado cuando corresponda.",
            "Revisa las instrucciones de seguridad del aeropuerto y la aerolínea."
        ]
    elif _contains(text,["herramienta","tool","taladro","drill","martillo","hammer","tijera","scissors"]):
        category="Herramienta/objeto especial"
        authorities+=["Seguridad del transporte","Aerolínea"]
        placement="No decidas el tipo de equipaje únicamente por el tamaño."
        details=[
            "Las herramientas pueden tener restricciones específicas.",
            "La seguridad aeroportuaria determina si un objeto puede pasar al área de embarque."
        ]
    elif _contains(text,["dinero","cash","efectivo"]):
        category="Dinero/efectivo"
        authorities+=["Aduana/autoridad del destino"]
        details=[
            "Transportar dinero y declararlo cuando corresponda son cuestiones diferentes.",
            "Los requisitos pueden depender del país de salida, tránsito y destino."
        ]
        missing+=["Cantidad aproximada","Países de la ruta"]
    else:
        details=[
            "Primero identifica qué tipo de objeto es.",
            "Después determina si la pregunta es sobre transporte aéreo, seguridad o entrada al destino.",
            "No todas las reglas se aplican a todos los artículos.",
            "Si falta un dato que cambia la respuesta, la aplicación debe pedirlo antes de dar una conclusión."
        ]
    if not destination:
        missing.append("Destino")
    if not baggage:
        missing.append("Tipo de equipaje")
    if not airline:
        missing.append("Aerolínea")
    authorities=unique(authorities)
    details.insert(0,f"Artículo: {item}.")
    if baggage:
        details.append(f"Tipo de equipaje indicado: {baggage_type_name(baggage)}.")
    if destination:
        details.append(f"Destino indicado: {destination}.")
    if airline:
        details.append(f"Aerolínea indicada: {airline}.")
    return {
        "ok":True,
        "title":f"Revisemos: {item}",
        "item":item,
        "category":category,
        "status":status,
        "placement":placement,
        "message":"La aplicación no inventa una autorización. Primero identifica qué regla controla tu artículo y después te indica qué debes confirmar.",
        "details":details,
        "authorities":authorities,
        "missing_information":unique(missing),
        "sources":_source("items",item),
        "next_action":"Confirma la regla específica antes de empacar."
    }

analyze_item=item_analysis
check_item=item_analysis
item_check=item_analysis

def connection_analysis(data:Dict[str,Any])->Dict[str,Any]:
    airport=s(data.get("airport"))
    same=data.get("same_ticket")
    bag=data.get("baggage")
    recheck=data.get("bag_recheck")
    country_change=data.get("country_change")
    details=[
        "Una conexión significa que tu viaje continúa en otro tramo.",
        "Lo primero es identificar el siguiente vuelo y su puerta.",
        "Después debes saber si cambias de avión o permaneces en el mismo.",
        "También debes confirmar qué ocurre con tu equipaje.",
        "Si existe un cambio de país, pueden existir controles adicionales.",
        "No todas las conexiones requieren los mismos pasos."
    ]
    questions=[
        "¿Cambio de avión?",
        "¿Cambio de terminal?",
        "¿Dónde está la puerta del siguiente vuelo?",
        "¿Tengo que pasar seguridad nuevamente?",
        "¿Tengo que recoger mi equipaje?",
        "¿Los vuelos están en el mismo boleto?"
    ]
    if same is True:
        details.append("Indicaste que los vuelos están en el mismo boleto. Aun así, confirma con la aerolínea cómo se manejará el equipaje y la conexión concreta.")
    elif same is False:
        details.append("Indicaste que los vuelos no están en el mismo boleto. Confirma especialmente la responsabilidad sobre equipaje y cambios entre vuelos.")
    if bag is True:
        details.append("Indicaste que llevas equipaje.")
    if recheck is True:
        details.append("Indicaste que debes volver a entregar el equipaje. Confírmalo con la aerolínea.")
    if country_change is True:
        details.append("Indicaste un cambio de país. Revisa qué controles aplican en ese punto concreto.")
    return {
        "ok":True,
        "title":"Entiende tu conexión",
        "message":"No necesitas memorizar procedimientos. La clave es saber qué vuelo tomas después, dónde debes ir y qué debes hacer con tu equipaje.",
        "details":details,
        "questions":questions,
        "next_action":"Confirma cada punto con la información oficial de tu itinerario.",
        "sources":_source("connection",airport)
    }

analyze_connection=connection_analysis

def analyze_flight(data:Dict[str,Any])->Dict[str,Any]:
    origin=s(data.get("origin"))
    destination=s(data.get("destination"))
    airline=s(data.get("airline"))
    number=s(data.get("flight_number"))
    stops=data.get("stops","")
    route=[]
    if isinstance(stops,list):
        route=[origin]+[s(x) for x in stops if s(x)]+[destination]
    elif s(stops):
        parts=[x.strip() for x in re.split(r"[,;>→]+",s(stops)) if x.strip()]
        route=[origin]+parts+[destination]
    else:
        route=[origin,destination]
    route=[x for i,x in enumerate(route) if x and x not in route[:i]]
    connections=max(0,len(route)-2)
    segments=[]
    for i in range(len(route)-1):
        segments.append({
            "number":i+1,
            "from":route[i],
            "to":route[i+1],
            "airline":airline,
            "flight_number":number if i==0 else ""
        })
    details=[]
    if connections:
        details.append(f"Tu ruta tiene {connections} punto(s) intermedio(s) indicado(s).")
        details.append("Una escala no significa automáticamente que tengas que recoger tu maleta ni pasar inmigración.")
        details.append("Eso depende del aeropuerto, ruta, boleto, aerolíneas y controles aplicables.")
    else:
        details.append("Has indicado una ruta sin escala intermedia.")
    if airline:
        details.append(f"Aerolínea indicada: {airline}.")
    if number:
        details.append(f"Número de vuelo indicado: {number}.")
    return {
        "ok":True,
        "title":"Así funciona tu itinerario",
        "route":" → ".join(route),
        "segments":segments,
        "connections":connections,
        "has_connection":connections>0,
        "message":"Vamos a convertir tu itinerario en pasos humanos: dónde empiezas, qué avión tomas, dónde bajas y qué debes confirmar antes de continuar.",
        "details":details,
        "questions":[
            "¿Es el mismo avión?",
            "¿Tengo que cambiar de avión?",
            "¿Tengo que cambiar de terminal?",
            "¿Qué pasa con mi equipaje?",
            "¿Dónde encuentro la siguiente puerta?"
        ],
        "next_action":"Revisa ahora equipaje y conexión.",
        "sources":_source("flight",airline)
    }

flight_analysis=analyze_flight
understand_flight=analyze_flight

def booking_simulation(data:Dict[str,Any])->Dict[str,Any]:
    return {
        "ok":True,
        "title":"Practicar una búsqueda de vuelo",
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "message":"Esta práctica enseña qué mirar antes de comprar un vuelo. No vende, reserva ni cobra.",
        "fields":[
            {"id":"origin","title":"¿Desde dónde sales?","help":"Escribe la ciudad o aeropuerto.","why":"Necesitamos conocer el punto de salida."},
            {"id":"destination","title":"¿A dónde vas?","help":"Escribe la ciudad o aeropuerto.","why":"Determina la ruta que debes revisar."},
            {"id":"departure","title":"¿Cuándo viajas?","help":"Selecciona la fecha.","why":"Las opciones dependen de la fecha."},
            {"id":"passengers","title":"¿Cuántas personas viajan?","help":"Indica la cantidad.","why":"Puede cambiar la búsqueda y el precio mostrado por el sitio oficial."},
            {"id":"cabin","title":"¿Qué cabina buscas?","help":"Por ejemplo, económica.","why":"Las condiciones pueden cambiar según la cabina."},
            {"id":"bags","title":"¿Llevas equipaje?","help":"Indica qué necesitas llevar.","why":"La tarifa puede tratar el equipaje de forma diferente."}
        ],
        "search":data,
        "next_action":"Cuando practiques, revisa especialmente tarifa, equipaje, cambios y conexiones.",
        "sources":_source("airlines")
    }

flight_search_simulation=booking_simulation
simulate_booking=booking_simulation

def document_analysis(data:Dict[str,Any])->Dict[str,Any]:
    destination=s(data.get("destination"))
    nationality=s(data.get("nationality"))
    passport=s(data.get("passport_country"))
    docs=[
        {
            "name":"Pasaporte/documento de viaje",
            "status":"pending" if not passport else "review",
            "why":"Debes identificar el documento con el que viajarás y comprobar las condiciones oficiales aplicables."
        },
        {
            "name":"Requisitos de entrada",
            "status":"pending",
            "why":"Dependen del destino y pueden depender de la nacionalidad."
        },
        {
            "name":"Condiciones de la aerolínea",
            "status":"pending",
            "why":"La aerolínea puede exigir condiciones de viaje y documentación propias."
        }
    ]
    if is_cuba(destination):
        docs.extend([
            {
                "name":"Visa/eVisa cuando corresponda",
                "status":"done" if truth(data.get("visa_checked")) else "pending",
                "why":"La necesidad depende de la situación del viajero y la información oficial vigente."
            },
            {
                "name":"D’Viajeros",
                "status":"done" if truth(data.get("dviajeros_done")) else "pending",
                "why":"La aplicación puede ayudarte a practicar antes de utilizar el sitio oficial."
            },
            {
                "name":"Aduana",
                "status":"done" if truth(data.get("customs_checked")) else "pending",
                "why":"Revisa qué artículos y declaraciones pueden corresponder."
            }
        ])
    if nationality:
        docs.append({
            "name":"Reglas específicas de tu nacionalidad",
            "status":"pending",
            "why":f"Confirma las condiciones aplicables a viajeros con nacionalidad {nationality}."
        })
    return {
        "ok":True,
        "title":"Tus documentos",
        "message":"Esta lista no certifica que puedas viajar. Te ayuda a descubrir qué necesitas comprobar.",
        "documents":docs,
        "next_action":"Revisa cada documento en su fuente oficial.",
        "sources":_source("documents",destination)
    }

document_check=document_analysis
documents_check=document_analysis

def practice_scenario(data:Dict[str,Any])->Dict[str,Any]:
    scenario=low(data.get("scenario")) or "airport"
    scenarios={
        "airport":{
            "title":"Estoy en el aeropuerto",
            "steps":[
                "Busca tu número de vuelo en las pantallas.",
                "Confirma destino y hora.",
                "Busca la puerta indicada.",
                "Si la puerta cambia, vuelve a comprobarla.",
                "Si tienes una duda, pregunta al personal correspondiente."
            ]
        },
        "connection":{
            "title":"Tengo una conexión",
            "steps":[
                "Localiza el siguiente vuelo.",
                "Confirma la puerta.",
                "Confirma la terminal.",
                "Averigua qué ocurre con tu equipaje.",
                "Sigue las señales de conexiones."
            ]
        },
        "baggage":{
            "title":"Mi maleta no aparece",
            "steps":[
                "Comprueba la pantalla de equipaje.",
                "Confirma que estás en la zona correcta.",
                "Busca el mostrador de equipaje de la aerolínea.",
                "Conserva el comprobante de equipaje.",
                "Sigue las instrucciones oficiales."
            ]
        },
        "gate":{
            "title":"No encuentro mi puerta",
            "steps":[
                "Busca el número de vuelo.",
                "Confirma la puerta en las pantallas.",
                "Mira si cambió la terminal.",
                "Sigue las señales del aeropuerto."
            ]
        },
        "dviajeros":{
            "title":"Practicar D’Viajeros",
            "steps":[
                "Prepara tus datos personales.",
                "Prepara los datos del viaje.",
                "Identifica vuelo y aeropuerto.",
                "Revisa antes de enviar cualquier información.",
                "La práctica de May Roga no envía datos al sitio oficial."
            ]
        },
        "baggage_item":{
            "title":"No sé dónde poner algo",
            "steps":[
                "Identifica el artículo.",
                "Pregunta qué tipo de equipaje quieres utilizar.",
                "Revisa la aerolínea.",
                "Revisa seguridad.",
                "Revisa el destino cuando corresponda."
            ]
        }
    }
    if "escala" in scenario or "conex" in scenario:
        key="connection"
    elif "maleta" in scenario or "equipaje" in scenario:
        key="baggage"
    elif "puerta" in scenario:
        key="gate"
    elif "dviajero" in scenario:
        key="dviajeros"
    elif "llevar" in scenario or "artículo" in scenario:
        key="baggage_item"
    else:
        key=scenario if scenario in scenarios else "airport"
    obj=scenarios[key]
    step=int(data.get("step") or 0)
    completed=obj["steps"][:step]
    pending=obj["steps"][step:]
    progress=int((len(completed)/len(obj["steps"]))*100)
    return {
        "ok":True,
        "title":obj["title"],
        "mode":"practice",
        "official_submission":False,
        "message":"Esta es una práctica educativa. No realiza el procedimiento real.",
        "next_action":pending[0] if pending else "Terminaste esta práctica. Ahora confirma la información en la fuente oficial.",
        "completed":completed,
        "pending":pending,
        "progress":progress,
        "current_step":{"number":step+1,"total":len(obj["steps"]),"instruction":pending[0] if pending else "Práctica completada"},
        "scenarios":[
            {"id":k,"title":v["title"]}
            for k,v in scenarios.items()
        ],
        "sources":_source("practice")
    }

practice=practice_scenario
run_practice=practice_scenario

def build_guide(data:Dict[str,Any])->Dict[str,Any]:
    pending=[]
    completed=[]
    origin=s(data.get("origin"))
    destination=s(data.get("destination"))
    if origin:
        completed.append("Origen identificado")
    else:
        pending.append("Completar origen")
    if destination:
        completed.append("Destino identificado")
    else:
        pending.append("Completar destino")
    if s(data.get("airline")):
        completed.append("Aerolínea identificada")
    else:
        pending.append("Identificar aerolínea")
    if s(data.get("nationality")):
        completed.append("Nacionalidad revisada")
    else:
        pending.append("Revisar nacionalidad")
    if s(data.get("passport_country")):
        completed.append("Pasaporte identificado")
    else:
        pending.append("Identificar pasaporte")
    if data.get("items"):
        completed.append("Artículos revisados")
    else:
        pending.append("Revisar qué quieres llevar")
    if data.get("baggage"):
        completed.append("Equipaje revisado")
    else:
        pending.append("Revisar equipaje")
    if is_cuba(destination):
        if truth(data.get("visa_checked")):
            completed.append("Visa/eVisa revisada")
        else:
            pending.append("Verificar visa/eVisa cuando corresponda")
        if truth(data.get("dviajeros_done")):
            completed.append("D’Viajeros revisado")
        else:
            pending.append("Practicar/revisar D’Viajeros")
        if truth(data.get("customs_checked")):
            completed.append("Aduana revisada")
        else:
            pending.append("Revisar aduana")
    next_action=pending[0] if pending else "Confirmar nuevamente las fuentes oficiales antes de viajar."
    return {
        "ok":True,
        "title":"Mi guía",
        "trip":{
            k:data.get(k,"")
            for k in [
                "origin","destination","airline","flight_number",
                "flight_type","stops","nationality","passport_country",
                "country_of_residence","cuban_nationality","dual_citizen",
                "purpose","arrival_date","departure_date","current_state"
            ]
        },
        "flight":{
            "airline":s(data.get("airline")),
            "flight_number":s(data.get("flight_number")),
            "stops":data.get("stops","")
        },
        "baggage":data.get("baggage") or {},
        "documents":{
            "dviajeros":truth(data.get("dviajeros_done")),
            "visa":truth(data.get("visa_checked")),
            "customs":truth(data.get("customs_checked")),
            "documents_checked":truth(data.get("documents_checked"))
        },
        "items_reviewed":[
            {"name":s(x),"status":"reviewed"}
            for x in (data.get("items") or [])
            if s(x)
        ],
        "pending":pending,
        "completed":completed,
        "next_action":next_action,
        "message":"Esta guía organiza tu preparación. La confirmación final siempre debe hacerse con las fuentes oficiales.",
        "sources":_source("guide")
    }

make_guide=build_guide
guide=build_guide

def dviajeros_simulation(data:Dict[str,Any]=None)->Dict[str,Any]:
    return {
        "ok":True,
        "id":"dviajeros",
        "title":"Practicar D’Viajeros",
        "notice":"PRÁCTICA DE MAY ROGA — NO SE ENVÍA INFORMACIÓN A D’VIAJEROS",
        "purpose":"Aprender qué información debes preparar y entender el orden general del proceso antes de entrar al sitio oficial.",
        "steps":[
            {
                "id":"traveler",
                "title":"Datos del viajero",
                "fields":["given_names","surnames","birth_date","nationality","sex"],
                "help":"Prepara los datos personales que el formulario pueda solicitar.",
                "why":"Identificar al viajero."
            },
            {
                "id":"passport",
                "title":"Documento de viaje",
                "fields":["passport_number","passport_country"],
                "help":"Usa datos de práctica dentro de esta simulación.",
                "why":"Relacionar el viaje con el documento utilizado."
            },
            {
                "id":"trip",
                "title":"Datos del viaje",
                "fields":["arrival_date","flight","arrival_airport"],
                "help":"Busca estos datos en tu reserva o información de vuelo.",
                "why":"Identificar el viaje."
            },
            {
                "id":"contact",
                "title":"Información adicional",
                "fields":["email","phone","address_destination"],
                "help":"La información concreta que se solicite debe comprobarse en el sitio oficial.",
                "why":"Preparar la información requerida."
            },
            {
                "id":"review",
                "title":"Revisión",
                "fields":[],
                "help":"Comprueba que entiendes cada dato antes de utilizar el sitio oficial.",
                "why":"Evitar errores antes de continuar."
            }
        ],
        "official_url":None
    }

simulate_dviajeros=dviajeros_simulation

def visa_simulation(data:Dict[str,Any]=None)->Dict[str,Any]:
    return {
        "ok":True,
        "id":"visa",
        "title":"Practicar visa/eVisa",
        "notice":"PRÁCTICA DE MAY ROGA — NO SE ENVÍA NINGUNA SOLICITUD REAL",
        "purpose":"Aprender qué información puede ser necesaria y cómo revisar una solicitud antes de utilizar el sitio oficial.",
        "steps":[
            {
                "id":"nationality",
                "title":"Nacionalidad",
                "fields":["nationality","country_of_residence"],
                "help":"La nacionalidad puede cambiar el requisito aplicable.",
                "why":"Determinar qué información oficial debes comprobar."
            },
            {
                "id":"identity",
                "title":"Identidad",
                "fields":["given_names","surname","birth_date","sex"],
                "help":"Utiliza datos de práctica.",
                "why":"Preparar la identificación del viajero."
            },
            {
                "id":"passport",
                "title":"Pasaporte",
                "fields":["passport_country","passport_number"],
                "help":"No introduzcas aquí credenciales ni códigos de seguridad.",
                "why":"Relacionar el trámite con el documento."
            },
            {
                "id":"trip",
                "title":"Datos del viaje",
                "fields":["purpose","arrival_date","departure_date","destination"],
                "help":"Usa los datos que aparecen en tu planificación.",
                "why":"Identificar el propósito y viaje."
            },
            {
                "id":"review",
                "title":"Revisión",
                "fields":[],
                "help":"La práctica termina aquí y no presenta una solicitud real.",
                "why":"Prepararte para utilizar la fuente oficial."
            }
        ],
        "official_url":None
    }

simulate_visa=visa_simulation

def create_travel_pdf(data:Dict[str,Any])->Dict[str,Any]:
    return {
        "ok":False,
        "message":"El generador PDF se ejecuta desde main.py para mantener la creación del archivo separada del motor de reglas."
    }

generate_pdf=create_travel_pdf
travel_pdf=create_travel_pdf

__all__=[
    "VERSION",
    "cuba_profile","cuba_check","cuba_analysis","analyze_cuba","cuba_entry_check",
    "baggage_type_name","baggage_type_explanation","baggage_rules",
    "analyze_baggage","baggage_analysis","check_baggage","baggage_check",
    "item_analysis","analyze_item","check_item","item_check",
    "connection_analysis","analyze_connection",
    "analyze_flight","flight_analysis","understand_flight",
    "booking_simulation","flight_search_simulation","simulate_booking",
    "document_analysis","document_check","documents_check",
    "practice_scenario","practice","run_practice",
    "build_guide","make_guide","guide",
    "dviajeros_simulation","simulate_dviajeros",
    "visa_simulation","simulate_visa",
    "create_travel_pdf","generate_pdf","travel_pdf"
]
