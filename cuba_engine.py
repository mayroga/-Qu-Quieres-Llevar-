# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.0.0
from __future__ import annotations
from typing import Any,Dict,List
import re

VERSION="12.0.0"

def _text(v):
    return str(v or "").strip()

def _low(v):
    return _text(v).lower()

def _sources(topic="",query=""):
    try:
        import source_registry as r
        for n in ("get_sources","sources_for","find_sources","official_sources"):
            f=getattr(r,n,None)
            if callable(f):
                try:
                    x=f(topic=topic,query=query)
                except TypeError:
                    try:x=f(topic,query)
                    except Exception:continue
                except Exception:continue
                if isinstance(x,dict): x=x.get("sources",[])
                if isinstance(x,list): return x
    except Exception:
        pass
    return []

def _base(title,message="",**kw):
    d={"ok":True,"title":title,"message":message}
    d.update(kw)
    return d

def cuba_profile(data:Dict[str,Any]):
    cuban=bool(data.get("cuban_nationality"))
    dual=bool(data.get("dual_citizen"))
    if cuban and dual:
        return "Persona con nacionalidad cubana y otra nacionalidad"
    if cuban:
        return "Persona con nacionalidad cubana"
    return "Persona que viaja a Cuba con otra nacionalidad"

def cuba_check(data:Dict[str,Any]):
    profile=cuba_profile(data)
    checks=[
        ("Identidad y nacionalidad",bool(data.get("nationality") or data.get("passport_country")),"Indica la nacionalidad y el país del pasaporte que usarás."),
        ("Pasaporte",bool(data.get("passport_country")),"Comprueba la vigencia y las condiciones aplicables en la fuente oficial."),
        ("Entrada a Cuba",bool(data.get("origin")),"Indica desde qué país viajas para revisar qué requisitos pueden depender de tu origen."),
        ("Visa o autorización de entrada",bool(data.get("visa_checked")),"Comprueba si tu nacionalidad y motivo de viaje requieren visa u otra autorización."),
        ("D’Viajeros",bool(data.get("dviajeros_done")),"Practica el formulario y después completa el proceso en el sitio oficial."),
        ("Aduana y equipaje",bool(data.get("customs_checked") and data.get("baggage_checked")),"Revisa qué debes declarar y las reglas aplicables a tus artículos."),
        ("Documentos",bool(data.get("documents_checked")),"Revisa tu lista personalizada antes de viajar.")
    ]
    checklist=[]
    pending=[]
    completed=[]
    for name,ok,action in checks:
        status="COMPLETADO" if ok else "PENDIENTE"
        checklist.append({"name":name,"status":status,"action":action})
        (completed if ok else pending).append(name)
    sources=_sources("cuba",_text(data.get("origin")))
    return _base(
        "Viajo a Cuba",
        f"Perfil: {profile}. Esta revisión organiza lo que debes comprobar; no certifica que puedas entrar ni sustituye a una autoridad.",
        status="review" if pending else "ready",
        traveler_profile=profile,
        details=[
            "Las condiciones pueden depender de nacionalidad, pasaporte, motivo del viaje y país desde el que viajas.",
            "Si tienes doble nacionalidad, comprueba específicamente qué documento corresponde a tu situación.",
            "No damos por confirmado ningún requisito que no esté respaldado por una fuente oficial."
        ],
        checklist=checklist,
        questions=pending,
        next_action=("Completa primero: "+pending[0]) if pending else "Haz una última comprobación en las fuentes oficiales antes de viajar.",
        sources=sources
    )

analyze_cuba=cuba_check
cuba_analysis=cuba_check
cuba_entry_check=cuba_check

def baggage_type_name(t):
    m={
        "personal_item":"Artículo personal",
        "personal":"Artículo personal",
        "carry_on":"Equipaje de mano",
        "cabin":"Equipaje de mano",
        "checked":"Maleta facturada",
        "checked_bag":"Maleta facturada",
        "special":"Equipaje especial"
    }
    return m.get(_low(t),_text(t) or "Equipaje")

def baggage_type_explanation(t):
    k=_low(t)
    if k in ("personal_item","personal"):
        return "Es el objeto pequeño que la aerolínea permite llevar contigo en la cabina y que normalmente debe colocarse en el espacio indicado por la aerolínea."
    if k in ("carry_on","cabin"):
        return "Es la maleta que llevas contigo durante el embarque y que debe cumplir las condiciones de la aerolínea y de tu tarifa."
    if k in ("checked","checked_bag"):
        return "Es la maleta que entregas a la aerolínea antes de pasar al área de embarque; la aerolínea determina sus condiciones según el vuelo y la tarifa."
    return "La forma de transportar este equipaje depende del artículo, la aerolínea, la ruta y las reglas aplicables."

def baggage_rules(data:Dict[str,Any]):
    typ=baggage_type_name(data.get("type"))
    airline=_text(data.get("airline"))
    fare=_text(data.get("fare"))
    destination=_text(data.get("destination"))
    missing=[]
    if not airline: missing.append("aerolínea")
    if not destination: missing.append("destino")
    if not fare: missing.append("tarifa")
    if not _text(data.get("type")): missing.append("tipo de equipaje")
    details=[
        baggage_type_explanation(data.get("type")),
        "El peso, las dimensiones y el número de piezas no deben inventarse: deben comprobarse para tu vuelo y tarifa.",
        "Si hay conexión, también debes revisar si el equipaje continúa al destino o si existe un paso adicional indicado por la aerolínea o las autoridades."
    ]
    status="verify" if missing else "review"
    label="REVISA ESTO ANTES DE VIAJAR"
    if missing:
        next_action="Completa primero: "+", ".join(missing)+"."
    else:
        next_action="Busca en la página oficial de equipaje de tu aerolínea las condiciones de tu tarifa y vuelo."
    return _base(
        "Mi equipaje",
        f"{typ}: {baggage_type_explanation(data.get('type'))}",
        status=status,
        status_label=label,
        baggage_type=typ,
        human_explanation=baggage_type_explanation(data.get("type")),
        placement="Consulta la condición específica de tu aerolínea y tarifa antes de preparar la maleta.",
        details=details,
        questions=missing,
        authorities=["Aerolínea","Seguridad aeroportuaria","Aduana cuando corresponda"],
        missing_information=missing,
        pieces=data.get("pieces"),
        weight=data.get("weight"),
        dimensions=_text(data.get("dimensions")),
        sources=_sources("baggage",airline),
        next_action=next_action
    )

analyze_baggage=baggage_rules
baggage_analysis=baggage_rules
check_baggage=baggage_rules
baggage_check=baggage_rules

def item_analysis(data:Dict[str,Any]):
    item=_text(data.get("item")) or _text(data.get("description"))
    q=_low(item)
    category="OTRO"
    authorities=[]
    missing=[]
    status="verify"
    label="REVISA ESTO ANTES DE VIAJAR"
    placement="No determines el lugar del artículo hasta comprobar las reglas aplicables."

    if any(x in q for x in ("medicina","medicamento","medicine","pill","pastilla","prescription")):
        category="MEDICAMENTOS"
        authorities=["Seguridad aeroportuaria","Aerolínea","País de origen","País de destino"]
        placement="Conserva los medicamentos de forma que puedas identificarlos y lleva la documentación que corresponda a tu caso."
        missing.append("tipo y cantidad del medicamento")
    elif any(x in q for x in ("power bank","batería externa","bateria externa","lithium","litio","battery","batería")):
        category="BATERÍAS"
        authorities=["Seguridad aeroportuaria","Aerolínea"]
        placement="Comprueba específicamente si debe viajar contigo en cabina o si tiene una condición especial."
        missing.append("tipo/capacidad de la batería")
    elif any(x in q for x in ("perfume","liquid","líquido","shampoo","champú","aerosol","spray")):
        category="LÍQUIDOS O AEROSOLES"
        authorities=["Seguridad aeroportuaria","Aerolínea","País de destino"]
        placement="La forma permitida depende del producto, cantidad, recipiente, equipaje y ruta."
        missing.append("cantidad y tipo de producto")
    elif any(x in q for x in ("comida","food","carne","meat","queso","cheese","fruta","fruit","vegetal","vegetable")):
        category="ALIMENTOS"
        authorities=["Seguridad aeroportuaria","Aduana","País de destino"]
        placement="Aunque un artículo pueda pasar seguridad, el país de destino puede tener reglas distintas de entrada."
        missing.append("tipo exacto y destino")
    elif any(x in q for x in ("animal","perro","gato","dog","cat","mascota","pet")):
        category="ANIMALES"
        authorities=["Aerolínea","País de origen","País de destino"]
        placement="No prepares el viaje del animal hasta comprobar los requisitos específicos de la aerolínea y de entrada."
        missing.append("especie y país de destino")
    elif any(x in q for x in ("taladro","drill","herramienta","tool","knife","cuchillo","martillo","hammer")):
        category="HERRAMIENTAS"
        authorities=["Seguridad aeroportuaria","Aerolínea"]
        placement="Comprueba si el artículo puede viajar en equipaje facturado o si existe una prohibición."
        missing.append("tipo exacto de herramienta")
    elif any(x in q for x in ("laptop","computadora","ordenador","phone","teléfono","tablet","electrónico","electronic")):
        category="ELECTRÓNICOS"
        authorities=["Seguridad aeroportuaria","Aerolínea"]
        placement="Comprueba las reglas para dispositivos y baterías antes de decidir dónde colocarlo."
        missing.append("si contiene batería de litio")
    elif any(x in q for x in ("dinero","cash","efectivo","money")):
        category="DINERO"
        authorities=["País de salida","País de destino","Aduana cuando corresponda"]
        placement="Las obligaciones de declaración pueden depender del importe y de la ruta."
        missing.append("importe y moneda")

    if not item:
        missing=["artículo que quieres llevar"]
        message="Escribe el artículo y te indicaré qué reglas debes comprobar."
    else:
        message=f"Has indicado: {item}. La categoría detectada es {category}. La aplicación no convierte esta orientación en una autorización automática."

    if missing:
        next_action="Necesito comprobar: "+", ".join(missing)+"."
    else:
        next_action="Comprueba las reglas de la autoridad indicada y la página oficial de tu aerolínea."

    return _base(
        "¿Qué quiero llevar?",
        message,
        item=item,
        category=category,
        status=status,
        status_label=label,
        placement=placement,
        details=[
            "Una regla puede depender de la aerolínea, seguridad, aduana, país de salida o país de destino.",
            "No uses una regla general como si fuera universal.",
            "Si una fuente oficial contradice una orientación general, sigue la fuente oficial aplicable."
        ],
        authorities=authorities,
        missing_information=missing,
        sources=_sources("items",f"{category} {item}"),
        next_action=next_action
    )

analyze_item=item_analysis
check_item=item_analysis
item_check=item_analysis

def connection_analysis(data:Dict[str,Any]):
    airport=_text(data.get("airport"))
    next_flight=_text(data.get("next_flight"))
    same=data.get("same_ticket")
    baggage=data.get("baggage")
    details=[
        "Una escala significa que tu viaje continúa después de llegar al primer aeropuerto.",
        "Una conexión puede implicar buscar otra puerta, revisar seguridad o seguir instrucciones de inmigración/aduana según el itinerario.",
        "No todas las conexiones funcionan igual; depende del aeropuerto, países involucrados, billete y equipaje."
    ]
    missing=[]
    if not airport: missing.append("aeropuerto de conexión")
    if not next_flight: missing.append("siguiente vuelo")
    if same is None: missing.append("si los vuelos están en la misma reserva")
    if baggage is None: missing.append("cómo aparece indicado el equipaje en la reserva")
    return _base(
        "Mi escala",
        "Tu escala debe entenderse paso a paso. La aplicación no inventará un procedimiento específico del aeropuerto.",
        status="verify" if missing else "review",
        details=details,
        questions=missing,
        next_action=("Completa: "+", ".join(missing)+".") if missing else "Comprueba las instrucciones del aeropuerto y de la aerolínea para tu conexión.",
        sources=_sources("connections",airport)
    )

analyze_connection=connection_analysis

def _segments(data):
    origin=_text(data.get("origin"))
    destination=_text(data.get("destination"))
    raw=data.get("stops")
    stops=[]
    if isinstance(raw,list):
        stops=[_text(x) for x in raw if _text(x)]
    elif isinstance(raw,str):
        stops=[x.strip() for x in re.split(r"[,;>→]+",raw) if x.strip()]
    points=[origin]+stops+[destination]
    points=[x for i,x in enumerate(points) if x and (i==0 or x!=points[i-1])]
    return [{"number":i+1,"from":points[i],"to":points[i+1],"kind":"connection" if i<len(points)-2 else "final"} for i in range(len(points)-1)]

def analyze_flight(data:Dict[str,Any]):
    seg=_segments(data)
    conn=max(0,len(seg)-1)
    route=" → ".join([x["from"] for x in seg]+([seg[-1]["to"]] if seg else []))
    if not route:
        route="Indica origen y destino"
    details=["Este análisis organiza el itinerario introducido por ti; no verifica en tiempo real que el vuelo exista o esté operando."]
    if conn:
        details.append(f"El itinerario contiene {conn} conexión(es). Revisa la puerta, siguiente vuelo y las instrucciones del aeropuerto.")
    else:
        details.append("Con los datos introducidos no aparece una conexión intermedia.")
    missing=[]
    if not _text(data.get("origin")): missing.append("origen")
    if not _text(data.get("destination")): missing.append("destino")
    return _base(
        "Mi vuelo",
        "Así se entiende el itinerario que introdujiste.",
        route=route,
        segments=seg,
        connections=conn,
        has_connection=bool(conn),
        details=details,
        questions=missing,
        next_action=("Completa "+", ".join(missing)+".") if missing else "Comprueba el itinerario en la reserva o sitio oficial de la aerolínea.",
        sources=_sources("flight",_text(data.get("airline")))
    )

flight_analysis=analyze_flight
understand_flight=analyze_flight

def booking_simulation(data:Dict[str,Any]):
    fields=[
        {"id":"origin","label":"Origen","example":"Miami","required":True},
        {"id":"destination","label":"Destino","example":"La Habana","required":True},
        {"id":"departure","label":"Fecha de salida","example":"MM/DD/AAAA","required":True},
        {"id":"passengers","label":"Pasajeros","example":"1","required":True},
        {"id":"cabin","label":"Cabina","example":"Economy","required":True},
        {"id":"airline","label":"Aerolínea","example":"Selecciona una aerolínea","required":False},
        {"id":"fare","label":"Tarifa","example":"Revisa qué incluye","required":False}
    ]
    return _base(
        "Práctica de búsqueda de vuelo",
        "Esta pantalla reproduce el proceso de búsqueda para enseñarte qué datos debes revisar. No compra, reserva ni cobra un vuelo.",
        simulation=True,
        real_booking=False,
        payment=False,
        search=data,
        fields=fields,
        steps=[
            {"step":1,"title":"Introduce origen y destino"},
            {"step":2,"title":"Elige la fecha y pasajeros"},
            {"step":3,"title":"Revisa aerolínea, horario y escalas"},
            {"step":4,"title":"Revisa tarifa y equipaje"},
            {"step":5,"title":"Confirma los datos en el sitio oficial"}
        ],
        next_action="Completa los campos de práctica y después verifica la información directamente con la aerolínea.",
        sources=_sources("booking",_text(data.get("airline")))
    )

flight_search_simulation=booking_simulation
simulate_booking=booking_simulation

def document_analysis(data:Dict[str,Any]):
    docs=[
        {"name":"Pasaporte","status":"COMPLETADO" if data.get("passport_country") else "PENDIENTE"},
        {"name":"Requisitos de entrada","status":"REVISAR"},
        {"name":"Visa o autorización","status":"COMPLETADO" if data.get("purpose") and data.get("destination") else "REVISAR"},
        {"name":"D’Viajeros","status":"COMPLETADO" if data.get("destination","").lower()=="cuba" and data.get("dviajeros_done") else ("REVISAR" if data.get("destination","").lower()=="cuba" else "NO APLICA AUTOMÁTICAMENTE")},
        {"name":"Equipaje","status":"COMPLETADO" if data.get("airline") else "PENDIENTE"},
        {"name":"Documentos adicionales","status":"REVISAR"}
    ]
    pending=[x["name"] for x in docs if x["status"] in ("PENDIENTE","REVISAR")]
    return _base(
        "Mis documentos",
        "Esta lista es una preparación orientativa y no certifica que tengas derecho a viajar o entrar a un país.",
        documents=docs,
        next_action=("Revisa: "+", ".join(pending[:2])+".") if pending else "Haz una comprobación final en las fuentes oficiales.",
        sources=_sources("documents",_text(data.get("destination")))
    )

document_check=document_analysis
documents_check=document_analysis

def practice_scenario(data:Dict[str,Any]):
    scenario=_low(data.get("scenario")) or "airport"
    step=int(data.get("step") or 0)
    answer=_text(data.get("answer"))
    scenarios={
        "airport":[
            {"id":"1","title":"Encuentra tu vuelo","help":"Busca en las pantallas el número de vuelo y destino.","why":"Te permite saber dónde continuar.","options":["Número de vuelo","Destino","Puerta"]},
            {"id":"2","title":"Comprueba la puerta","help":"Compara la puerta de tu tarjeta de embarque con la pantalla.","why":"La puerta puede cambiar.","options":["Puerta","Terminal","Hora"]},
            {"id":"3","title":"Prepárate para embarcar","help":"Ten listos los documentos que la aerolínea indique.","why":"El embarque depende de los requisitos de tu viaje.","options":["Documentos","Equipaje","Ambos"]}
        ],
        "connection":[
            {"id":"1","title":"Baja del primer avión","help":"Busca las señales de conexiones o el siguiente vuelo.","why":"No todas las conexiones usan el mismo recorrido.","options":["Connections","Baggage","Exit"]},
            {"id":"2","title":"Busca el siguiente vuelo","help":"Comprueba número de vuelo, destino y puerta.","why":"Tu siguiente avión puede salir de otra zona.","options":["Vuelo","Puerta","Ambos"]},
            {"id":"3","title":"Comprueba el equipaje","help":"Mira las instrucciones de tu reserva y aeropuerto.","why":"No todas las conexiones manejan el equipaje igual.","options":["Confirmarlo","Suponerlo"]}
        ],
        "baggage":[
            {"id":"1","title":"Identifica tu equipaje","help":"Distingue artículo personal, equipaje de mano y maleta facturada.","why":"Cada uno puede tener reglas diferentes.","options":["Personal","Mano","Facturado"]},
            {"id":"2","title":"Comprueba tu tarifa","help":"Busca qué equipaje incluye tu tarifa.","why":"La tarifa puede cambiar las condiciones.","options":["En la reserva","En redes sociales","Suponerlo"]},
            {"id":"3","title":"Confirma la regla","help":"Usa la página oficial de equipaje de tu aerolínea.","why":"Las condiciones pueden cambiar.","options":["Fuente oficial","Un comentario","Una regla antigua"]}
        ],
        "dviajeros":[
            {"id":"1","title":"Datos personales","help":"Practica cómo identificar nombre, apellidos y nacionalidad.","why":"Debes reconocer cada campo antes de completar el formulario real.","options":["Nombre","Apellidos","Nacionalidad"]},
            {"id":"2","title":"Datos del viaje","help":"Identifica vuelo, fecha y aeropuerto.","why":"Estos datos relacionan el formulario con el viaje.","options":["Vuelo","Fecha","Aeropuerto"]},
            {"id":"3","title":"Revisión final","help":"Antes de enviar, revisa que los datos coincidan con tus documentos.","why":"Una diferencia puede requerir corrección.","options":["Revisar","Enviar sin revisar"]}
        ],
        "visa":[
            {"id":"1","title":"Identifica tu nacionalidad","help":"Practica dónde aparece la nacionalidad y el pasaporte.","why":"Los requisitos pueden depender de la nacionalidad.","options":["Nacionalidad","Pasaporte"]},
            {"id":"2","title":"Motivo del viaje","help":"Identifica el propósito que corresponde a tu viaje.","why":"El propósito puede cambiar el trámite.","options":["Turismo","Otro","No sé"]},
            {"id":"3","title":"Revisión","help":"Comprueba la información en el sitio oficial antes de realizar cualquier trámite.","why":"La simulación no es una solicitud oficial.","options":["Revisar fuente","Enviar simulación"]}
        ]
    }
    key=next((k for k in scenarios if k in scenario), "airport")
    steps=scenarios[key]
    idx=min(step,len(steps)-1)
    completed=[x["title"] for x in steps[:idx]]
    if answer and idx<len(steps):
        completed.append(steps[idx]["title"])
        idx=min(idx+1,len(steps)-1)
    progress=round((len(completed)/len(steps))*100)
    current=steps[idx] if completed.__len__()<len(steps) else None
    return _base(
        "Práctica: "+key.title(),
        "SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL.",
        mode="practice",
        official_submission=False,
        notice="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL.",
        completed=completed,
        pending=[x["title"] for x in steps if x["title"] not in completed],
        progress=progress,
        current_step=current,
        scenarios=steps,
        next_action="Responde el paso actual." if current else "Terminaste la práctica. Ahora comprueba el proceso real en la fuente oficial.",
        sources=_sources(key,key)
    )

practice=practice_scenario
run_practice=practice_scenario

def dviajeros_simulation(data:Dict[str,Any]):
    return {
        "ok":True,"id":"dviajeros","title":"Práctica D’Viajeros",
        "notice":"SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL.",
        "purpose":"Aprender qué información debes tener preparada antes de completar el proceso real.",
        "steps":[
            {"id":"personal","title":"Datos personales","fields":["given_names","surnames","birth_date","nationality","sex"],"help":"Practica con los datos de tu documento.","why":"Estos campos identifican al viajero.","example":"Usa tus datos reales solamente en el sitio oficial."},
            {"id":"passport","title":"Pasaporte","fields":["passport_number","passport_country"],"help":"Identifica el número y país del pasaporte.","why":"El documento debe coincidir con tu viaje.","example":"No compartas el número aquí si no es necesario."},
            {"id":"trip","title":"Viaje","fields":["arrival_date","departure_date","flight","arrival_airport","departure_airport"],"help":"Practica identificando estos datos en tu reserva.","why":"Relacionan el formulario con el viaje.","example":"Comprueba la reserva."},
            {"id":"contact","title":"Contacto y destino","fields":["email","phone","address_destination"],"help":"Practica qué información debes tener preparada.","why":"El formulario puede solicitar datos adicionales.","example":"Revisa la fuente oficial para confirmar los campos actuales."}
        ],
        "official_url":(_sources("dviajeros","")[0].get("url") if _sources("dviajeros","") and isinstance(_sources("dviajeros","")[0],dict) else None)
    }

simulate_dviajeros=dviajeros_simulation

def visa_simulation(data:Dict[str,Any]):
    return {
        "ok":True,"id":"visa","title":"Práctica de visa",
        "notice":"SIMULACIÓN DE PRÁCTICA — NO ES UNA SOLICITUD OFICIAL.",
        "purpose":"Aprender qué información debes preparar y qué debes comprobar antes de iniciar un trámite real.",
        "steps":[
            {"id":"identity","title":"Identidad","fields":["surname","given_names","birth_date","sex","nationality"],"help":"Practica con los datos de tu documento.","why":"La identidad debe coincidir con tus documentos.","example":"No envíes esta práctica como solicitud."},
            {"id":"passport","title":"Pasaporte","fields":["passport_number","passport_country"],"help":"Identifica el documento que usarás.","why":"El trámite real puede depender del documento."},
            {"id":"travel","title":"Viaje","fields":["purpose","arrival_date","departure_date","country_of_residence"],"help":"Practica los datos básicos del viaje.","why":"El propósito y las fechas pueden afectar el trámite."},
            {"id":"contact","title":"Contacto","fields":["email","phone"],"help":"Prepara los datos solicitados por el sitio oficial.","why":"Los datos de contacto dependen del trámite real."}
        ],
        "official_url":(_sources("visa","Cuba")[0].get("url") if _sources("visa","Cuba") and isinstance(_sources("visa","Cuba")[0],dict) else None)
    }

simulate_visa=visa_simulation

def build_guide(data:Dict[str,Any]):
    trip=dict(data)
    completed=[]
    pending=[]
    if data.get("origin") and data.get("destination"): completed.append("Datos básicos del viaje")
    else: pending.append("Completar origen y destino")
    if data.get("airline"): completed.append("Aerolínea")
    else: pending.append("Seleccionar o confirmar aerolínea")
    if data.get("flight_number"): completed.append("Número de vuelo")
    else: pending.append("Confirmar número de vuelo")
    if data.get("baggage_checked"): completed.append("Equipaje revisado")
    else: pending.append("Revisar equipaje")
    if data.get("documents_checked"): completed.append("Documentos revisados")
    else: pending.append("Revisar documentos")
    if data.get("destination","").lower()=="cuba":
        if data.get("dviajeros_done"): completed.append("D’Viajeros practicado/completado")
        else: pending.append("Practicar y comprobar D’Viajeros")
        if data.get("visa_checked"): completed.append("Visa revisada")
        else: pending.append("Comprobar visa o autorización aplicable")
    if data.get("items"):
        completed.append("Artículos revisados")
    else:
        pending.append("Revisar lo que quieres llevar")
    next_action=pending[0] if pending else "Haz una comprobación final en las fuentes oficiales."
    return _base(
        "Mi guía",
        "Esta guía reúne la preparación que has realizado y los puntos que todavía debes comprobar.",
        trip=trip,
        flight={"origin":data.get("origin",""),"destination":data.get("destination",""),"airline":data.get("airline",""),"flight_number":data.get("flight_number",""),"flight_type":data.get("flight_type",""),"stops":data.get("stops","")},
        baggage=data.get("baggage",{}),
        documents={"dviajeros_done":data.get("dviajeros_done",False),"visa_checked":data.get("visa_checked",False),"documents_checked":data.get("documents_checked",False)},
        items_reviewed=[{"item":x,"status":"REVISADO"} for x in data.get("items",[])],
        pending=pending,
        completed=completed,
        next_action=next_action,
        sources=_sources("guide",_text(data.get("destination")))
    )

make_guide=build_guide
guide=build_guide

def create_travel_pdf(data:Dict[str,Any]):
    return {"ok":False,"message":"El PDF se genera desde main.py.","data":data}

generate_pdf=create_travel_pdf
travel_pdf=create_travel_pdf
