# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.2.0
from __future__ import annotations
import base64
import io
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime,timezone
from pathlib import Path
from typing import Any,Dict,Optional

from fastapi import FastAPI,HTTPException,Request,UploadFile,File
from fastapi.responses import FileResponse,JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Preformatted
from reportlab.lib.units import inch

from cuba_engine import engine as cuba_engine
from source_registry import SOURCES,AIRLINES,get_sources,get_airlines,official_url

APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="12.2.0"
COMPANY="May Roga LLC"
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash").strip()
GEMINI_URL=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
MAX_BODY=5_000_000

app=FastAPI(title=APP_NAME,version=APP_VERSION)
if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

def now_iso()->str:
    return datetime.now(timezone.utc).isoformat()

def clean(v:Any)->str:
    return str(v or "").strip()

async def read_json(request:Request)->Dict[str,Any]:
    try:
        raw=await request.body()
        if len(raw)>MAX_BODY:
            raise HTTPException(413,"La información enviada es demasiado grande.")
        if not raw:
            return {}
        data=json.loads(raw.decode("utf-8"))
        return data if isinstance(data,dict) else {}
    except HTTPException:
        raise
    except Exception:
        return {}

def source_dict(s:Any)->Dict[str,Any]:
    if hasattr(s,"__dataclass_fields__"):
        try:
            from dataclasses import asdict
            return asdict(s)
        except Exception:
            pass
    if isinstance(s,dict):
        return dict(s)
    out={}
    for k in ("id","name","publisher","url","type","topics","what_it_covers","limitations","verified","country","category"):
        if hasattr(s,k):
            out[k]=getattr(s,k)
    return out

def all_source_dicts()->list:
    return [source_dict(x) for x in SOURCES]

def airline_dicts()->list:
    try:
        return [source_dict(x) for x in get_airlines()]
    except Exception:
        return [source_dict(x) for x in AIRLINES]

def find_source_by_id(source_id:str)->Optional[Dict[str,Any]]:
    sid=clean(source_id)
    if not sid:
        return None
    for s in SOURCES:
        d=source_dict(s)
        if clean(d.get("id"))==sid:
            return d
    return None

def official_sources_for(text:str="")->list:
    q=clean(text).lower()
    result=[]
    for s in SOURCES:
        d=source_dict(s)
        if d.get("category") not in ("official","airline"):
            continue
        if not q:
            result.append(d)
            continue
        blob=" ".join(str(d.get(k,"")) for k in ("id","name","publisher","topics","what_it_covers","country")).lower()
        if any(x in blob for x in q.split() if len(x)>1):
            result.append(d)
    return result

def cuba_sources()->list:
    try:
        return cuba_engine.official_information()
    except Exception:
        return []

def charter_sources()->list:
    try:
        return cuba_engine.get_charter_sources()
    except Exception:
        return []

def baggage_sources()->list:
    try:
        return cuba_engine.get_commercial_baggage()
    except Exception:
        return []

def cuba_config()->Dict[str,Any]:
    try:
        return cuba_engine.public_config()
    except Exception:
        return {
            "official_sources":cuba_sources(),
            "charters":charter_sources(),
            "commercial_baggage":baggage_sources()
        }

def is_cuba(data:Dict[str,Any])->bool:
    text=json.dumps(data,ensure_ascii=False).lower()
    return any(x in text for x in ("cuba","cuban","habana","havana","holguin","varadero","santiago de cuba","camaguey"))

def safe_url(url:str)->str:
    u=clean(url)
    return u if u.startswith(("https://","http://")) else ""

def airline_links()->list:
    result=[]
    for a in airline_dicts():
        u=safe_url(a.get("url",""))
        if u:
            result.append({
                "id":a.get("id",""),
                "name":a.get("name",""),
                "url":u,
                "publisher":a.get("publisher",""),
                "country":a.get("country","")
            })
    return result

def gemini_request(prompt:str)->Dict[str,Any]:
    if not GEMINI_API_KEY:
        return {"ok":False,"reason":"GEMINI_API_KEY no configurada."}
    body={
        "contents":[{"parts":[{"text":prompt}]}],
        "generationConfig":{
            "temperature":0.1,
            "maxOutputTokens":1200,
            "responseMimeType":"application/json"
        }
    }
    req=urllib.request.Request(
        GEMINI_URL+"?key="+GEMINI_API_KEY,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type":"application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req,timeout=35) as r:
            data=json.loads(r.read().decode("utf-8"))
        text=""
        for c in data.get("candidates",[]):
            for p in c.get("content",{}).get("parts",[]):
                if p.get("text"):
                    text+=p["text"]
        if not text:
            return {"ok":False,"reason":"Gemini no devolvió contenido."}
        text=text.strip()
        if text.startswith("```"):
            text=re.sub(r"^```(?:json)?","",text).strip()
            text=re.sub(r"```$","",text).strip()
        try:
            obj=json.loads(text)
            return {"ok":True,"data":obj if isinstance(obj,dict) else {"answer":text}}
        except Exception:
            return {"ok":True,"data":{"answer":text}}
    except urllib.error.HTTPError as e:
        return {"ok":False,"reason":f"Error HTTP de Gemini: {e.code}"}
    except Exception as e:
        return {"ok":False,"reason":f"No fue posible consultar Gemini: {e}"}

def item_prompt(question:str,data:Dict[str,Any],language:str)->str:
    official=official_sources_for("TSA baggage batteries food customs Cuba")
    urls=[x.get("url") for x in official if x.get("url")]
    if is_cuba(data):
        for x in cuba_sources():
            if isinstance(x,dict) and x.get("url"):
                urls.append(x["url"])
    urls=list(dict.fromkeys(urls))
    return f"""
You are the item-permission assistant inside "{APP_NAME}" by May Roga LLC.
Your ONLY task is to help interpret whether a specific physical item may be carried in carry-on baggage or checked baggage.
Do not answer general travel questions.
Do not invent airline rules, airport rules, customs rules, visa rules, fees, allowances, or availability.
Do not claim legal certainty.
If the information is uncertain, say that clearly and direct the traveler to the appropriate official source.
Use plain language.
Language: {language or "es"}.
Question: {question}
Traveler context: {json.dumps(data,ensure_ascii=False)}
Relevant official sources:
{json.dumps(urls,ensure_ascii=False)}
Return JSON with:
status,answer,reason,carry_on,checked_bag,needs_confirmation,official_source,official_url,next_action.
Allowed status values: "allowed","not_allowed","conditional","unknown".
carry_on and checked_bag must be true,false,or null.
"""

def local_item_fallback(question:str,data:Dict[str,Any],language:str)->Dict[str,Any]:
    q=question.lower()
    source=official_sources_for("baggage batteries food")
    src=source[0] if source else {}
    if any(x in q for x in ("gasolina","gasoline","petroleo","petroleum")):
        answer="Este artículo requiere revisión de las reglas oficiales de materiales peligrosos. No lo presentes como permitido sin verificar."
        status="unknown"
    elif any(x in q for x in ("bateria","battery","power bank","litio","lithium")):
        answer="Las baterías tienen reglas específicas según su tipo y capacidad. Verifica la regla oficial antes de viajar."
        status="conditional"
    elif any(x in q for x in ("comida","food","carne","meat","jamon","ham","yogurt","agua","water","uvas","grapes","guayaba","guava","semillas","seeds")):
        answer="Los alimentos pueden estar sujetos a reglas distintas de seguridad aérea y de entrada al país. Verifica ambas fuentes oficiales."
        status="conditional"
    else:
        answer="No tengo una confirmación suficientemente segura para este artículo. Consulta la fuente oficial antes de llevarlo."
        status="unknown"
    return {
        "status":status,
        "answer":answer,
        "reason":"La regla puede depender del tipo exacto del artículo, cantidad, empaque, equipaje y destino.",
        "carry_on":None,
        "checked_bag":None,
        "needs_confirmation":True,
        "official_source":src.get("name","Fuente oficial"),
        "official_url":safe_url(src.get("url","")),
        "next_action":"Abre la fuente oficial y verifica el artículo antes de empacarlo."
    }

def build_pdf(state:Dict[str,Any],language:str="es")->bytes:
    buf=io.BytesIO()
    doc=SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=.55*inch,
        leftMargin=.55*inch,
        topMargin=.55*inch,
        bottomMargin=.55*inch
    )
    styles=getSampleStyleSheet()
    title=ParagraphStyle(
        "AppTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=17,
        leading=21,
        spaceAfter=12
    )
    h=ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=5
    )
    body=ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
        spaceAfter=4
    )
    small=ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9
    )
    story=[]
    story.append(Paragraph(APP_NAME,title))
    story.append(Paragraph("Mi resumen de preparación",h))
    story.append(Paragraph(f"May Roga LLC · versión {APP_VERSION}",body))
    story.append(Paragraph(f"Generado: {now_iso()}",body))
    story.append(Spacer(1,8))
    story.append(Paragraph(
        "<b>IMPORTANTE / IMPORTANT:</b> Este documento es una guía personal de preparación. "
        "NO es una visa, permiso de entrada, reserva, boleto, autorización de equipaje, decisión de aduana "
        "ni documento emitido por una aerolínea, gobierno, aeropuerto, consulado o autoridad.",
        body
    ))
    story.append(Paragraph(
        "Los datos contenidos aquí fueron proporcionados por el usuario y se incluyen para recuperar su preparación. "
        "May Roga LLC no utiliza este PDF como almacenamiento permanente del usuario.",
        body
    ))
    story.append(Spacer(1,8))

    def add_section(title_text:str,value:Any):
        story.append(Paragraph(title_text,h))
        if isinstance(value,(dict,list)):
            txt=json.dumps(value,ensure_ascii=False,indent=2)
        else:
            txt=str(value)
        txt=txt.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        for part in txt.splitlines() or [""]:
            story.append(Paragraph(part.replace(" ","&nbsp;"),small))

    preferred=[
        ("Viaje / Trip",state.get("trip")),
        ("Vuelo / Flight",state.get("flight")),
        ("Aerolínea / Airline",state.get("airline")),
        ("Reserva de práctica / Booking Practice",state.get("booking")),
        ("Conexiones / Connections",state.get("connections")),
        ("Equipaje / Baggage",state.get("baggage")),
        ("Artículos consultados / Items",state.get("items")),
        ("Cuba",state.get("cuba")),
        ("Visa / eVisa",state.get("visa")),
        ("D'Viajeros",state.get("dviajeros")),
        ("Documentos / Documents",state.get("documents")),
        ("Prácticas / Practice Progress",state.get("practice")),
        ("Diagnóstico / Preparation Status",state.get("diagnosis")),
        ("Datos adicionales / Additional Data",state.get("data"))
    ]
    used=False
    for title_text,value in preferred:
        if value not in (None,"",{},[]):
            add_section(title_text,value)
            used=True
    if not used:
        add_section("Estado / State",state)

    story.append(PageBreak())
    story.append(Paragraph("Fuentes oficiales de referencia",h))
    for s in all_source_dicts():
        if s.get("url"):
            name=s.get("name") or s.get("publisher") or s.get("id")
            story.append(Paragraph(
                f"{name}: {safe_url(s.get('url',''))}",
                small
            ))
    for s in cuba_sources():
        if isinstance(s,dict) and s.get("url"):
            story.append(Paragraph(
                f"{s.get('name','Cuba')}: {safe_url(s.get('url',''))}",
                small
            ))

    payload=json.dumps(state,ensure_ascii=True,separators=(",",":")).encode("utf-8")
    encoded=base64.b64encode(payload).decode("ascii")
    story.append(Spacer(1,10))
    story.append(Paragraph("Marcador de recuperación de la aplicación",h))
    story.append(Paragraph(
        "Este marcador permite que la aplicación recupere los datos generados por ella misma cuando el usuario vuelva a importar este PDF.",
        small
    ))
    story.append(Preformatted(
        "APP_STATE_JSON_BEGIN\n"+encoded+"\nAPP_STATE_JSON_END",
        ParagraphStyle("Machine",fontName="Courier",fontSize=3.5,leading=4)
    ))
    doc.build(story)
    return buf.getvalue()

def extract_state_from_pdf(raw:bytes)->Dict[str,Any]:
    text=""
    errors=[]
    try:
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(raw))
        text="\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        errors.append(str(e))
        try:
            from PyPDF2 import PdfReader
            reader=PdfReader(io.BytesIO(raw))
            text="\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e2:
            errors.append(str(e2))
    match=re.search(r"APP_STATE_JSON_BEGIN\s*(.*?)\s*APP_STATE_JSON_END",text,re.S)
    if not match:
        raise ValueError("Este PDF no contiene datos de recuperación generados por la aplicación.")
    encoded=re.sub(r"\s+","",match.group(1))
    try:
        decoded=base64.b64decode(encoded,validate=True)
        state=json.loads(decoded.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"No se pudo recuperar el estado del PDF: {e}")
    if not isinstance(state,dict):
        raise ValueError("El contenido recuperado no tiene un estado válido.")
    return state

@app.get("/")
async def root():
    index=STATIC_DIR/"index.html"
    if not index.exists():
        return JSONResponse({
            "app":APP_NAME,
            "version":APP_VERSION,
            "message":"Archivo static/index.html no encontrado."
        },status_code=200)
    return FileResponse(str(index))

@app.get("/api/v1/health")
async def health():
    return {
        "ok":True,
        "app":APP_NAME,
        "version":APP_VERSION,
        "free":True,
        "login_required":False,
        "payment_required":False,
        "server_storage":False,
        "timestamp":now_iso()
    }

@app.get("/api/v1/config")
async def config():
    return {
        "ok":True,
        "app":APP_NAME,
        "version":APP_VERSION,
        "company":COMPANY,
        "language_default":"es",
        "languages":["es","en"],
        "free":True,
        "login_required":False,
        "payment_required":False,
        "server_storage":False,
        "gemini_item_only":bool(GEMINI_API_KEY),
        "airlines":airline_links(),
        "official_sources":all_source_dicts(),
        "cuba":cuba_config(),
        "charters":charter_sources(),
        "commercial_baggage":baggage_sources()
    }

@app.post("/api/v1/session")
async def session(request:Request):
    data=await read_json(request)
    return {
        "ok":True,
        "local_only":True,
        "server_storage":False,
        "login_required":False,
        "payment_required":False,
        "language":clean(data.get("language")) or "es",
        "message":"La aplicación funciona sin cuenta ni contraseña. El progreso personal permanece en el dispositivo."
    }

@app.get("/api/v1/airlines")
async def airlines():
    return {"ok":True,"airlines":airline_links()}

@app.get("/api/v1/sources")
async def sources(topic:str="",query:str=""):
    q=clean(query or topic)
    return {"ok":True,"sources":official_sources_for(q)}

@app.get("/api/v1/official")
async def official(topic:str="",query:str=""):
    return {"ok":True,"sources":official_sources_for(clean(query or topic))}

@app.get("/api/v1/legal")
async def legal():
    return {
        "ok":True,
        "company":COMPANY,
        "app":APP_NAME,
        "notice_es":(
            "May Roga LLC ofrece preparación y orientación independiente. "
            "No es gobierno, aerolínea, aeropuerto, aduana, inmigración, consulado, agencia de viajes, "
            "procesador de pagos ni autoridad que tome decisiones oficiales."
        ),
        "notice_en":(
            "May Roga LLC provides independent preparation and guidance. "
            "It is not a government agency, airline, airport, customs authority, immigration authority, "
            "consulate, travel agency, payment processor, or official decision-maker."
        ),
        "free":True,
        "payment_required":False,
        "login_required":False,
        "server_storage":False
    }

@app.get("/api/v1/cuba/guide")
async def cuba_guide():
    return {
        "ok":True,
        "guide":cuba_config(),
        "notice":cuba_engine.disclaimer()
    }

@app.get("/api/v1/cuba/config")
async def cuba_configuration():
    return {
        "ok":True,
        "config":cuba_config(),
        "notice":cuba_engine.disclaimer()
    }

@app.post("/api/v1/cuba/visa")
async def cuba_visa(request:Request):
    data=await read_json(request)
    try:
        result=cuba_engine.evaluate_visa(data)
    except Exception as e:
        raise HTTPException(400,str(e))
    return {"ok":True,"result":result,"official_sources":cuba_sources()}

@app.post("/api/v1/cuba/dviajeros")
async def cuba_dviajeros(request:Request):
    data=await read_json(request)
    try:
        result=cuba_engine.evaluate_dviajeros(data)
    except Exception as e:
        raise HTTPException(400,str(e))
    return {"ok":True,"result":result,"official_sources":cuba_sources()}

@app.post("/api/v1/cuba/simulation")
async def cuba_simulation(request:Request):
    data=await read_json(request)
    mode=clean(data.get("mode") or data.get("scenario") or "dviajeros")
    try:
        result=cuba_engine.simulation(mode)
    except Exception as e:
        raise HTTPException(400,str(e))
    return {
        "ok":True,
        "simulation":result,
        "official_submission":False,
        "notice":"Esto es una práctica. No envía información a Cuba ni crea un trámite real.",
        "official_sources":cuba_sources()
    }

@app.post("/api/v1/practice")
async def practice(request:Request):
    data=await read_json(request)
    scenario=clean(data.get("scenario") or data.get("mode") or "general")
    step=data.get("step",0)
    try:
        step=int(step)
    except Exception:
        step=0
    steps=[
        {"step":0,"title":"Preparar","instruction":"Reúne la información que ya tienes antes de continuar.","next":"Continuar"},
        {"step":1,"title":"Revisar","instruction":"Comprueba los datos conocidos y completa únicamente lo que falte.","next":"Continuar"},
        {"step":2,"title":"Practicar","instruction":"Realiza la simulación paso a paso. No se enviará información real.","next":"Continuar"},
        {"step":3,"title":"Confirmar","instruction":"Revisa el resultado de la práctica y anota la próxima acción.","next":"Finalizar"}
    ]
    current=steps[min(max(step,0),len(steps)-1)]
    return {
        "ok":True,
        "mode":"simulation",
        "scenario":scenario,
        "official_submission":False,
        "notice":"Esta práctica no envía formularios ni realiza reservas reales.",
        "completed":current["step"]>=3,
        "pending":current["step"]<3,
        "progress":current["step"],
        "current_step":current,
        "steps":steps,
        "simulation_id":clean(data.get("simulation_id")) or f"local-{scenario}",
        "sources":cuba_sources() if is_cuba(data) else official_sources_for(scenario)
    }

@app.post("/api/v1/flight/search-external")
async def flight_search_external(request:Request):
    data=await read_json(request)
    origin=clean(data.get("origin") or data.get("from"))
    destination=clean(data.get("destination") or data.get("to"))
    date=clean(data.get("date"))
    q=" ".join(x for x in (origin,destination,date) if x)
    links=[]
    if q:
        links.append({
            "name":"Google Flights",
            "url":"https://www.google.com/travel/flights?q="+urllib.parse.quote_plus(q) if False else "https://www.google.com/travel/flights"
        })
    airline_name=clean(data.get("airline"))
    for a in airline_links():
        if airline_name and airline_name.lower() not in a["name"].lower():
            continue
        links.append(a)
    return {
        "ok":True,
        "search":data,
        "results":[],
        "official_links":links,
        "notice":"La aplicación no inventa disponibilidad ni precios. Usa los enlaces oficiales para realizar la búsqueda real."
    }

@app.post("/api/v1/flight")
async def flight(request:Request):
    data=await read_json(request)
    airline=clean(data.get("airline"))
    matches=[]
    if airline:
        for a in airline_links():
            if airline.lower() in a["name"].lower() or airline.lower() in a["id"].lower():
                matches.append(a)
    return {
        "ok":True,
        "request":data,
        "airline":airline,
        "airlines":matches or airline_links(),
        "notice":"La información de vuelos reales debe verificarse directamente con la aerolínea o fuente oficial.",
        "next_action":"Elige la aerolínea y abre su sitio oficial para consultar vuelos actuales."
    }

@app.post("/api/v1/booking")
async def booking(request:Request):
    data=await read_json(request)
    airline=clean(data.get("airline"))
    fields=[
        "origen","destino","fecha","pasajeros","equipaje","asiento",
        "información del pasajero","revisión final"
    ]
    return {
        "ok":True,
        "mode":"simulation",
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "official_submission":False,
        "airline":airline,
        "fields":fields,
        "steps":[
            "Seleccionar vuelo",
            "Revisar datos del viaje",
            "Elegir equipaje",
            "Revisar datos del pasajero",
            "Revisar el precio mostrado por la aerolínea",
            "Finalizar la práctica"
        ],
        "notice":"Esta práctica se parece al proceso real, pero nunca compra un boleto ni envía una reserva.",
        "next_action":"Cuando termines la práctica, abre el sitio oficial de la aerolínea para hacer la operación real."
    }

@app.post("/api/v1/connection")
async def connection(request:Request):
    data=await read_json(request)
    return {
        "ok":True,
        "request":data,
        "simulation":True,
        "steps":[
            "Identificar aeropuerto de llegada",
            "Identificar siguiente vuelo",
            "Revisar terminal y tiempo disponible",
            "Comprobar documentos y equipaje",
            "Confirmar instrucciones con las fuentes oficiales"
        ],
        "notice":"Los tiempos, terminales y requisitos reales deben verificarse para el vuelo concreto."
    }

@app.post("/api/v1/baggage")
async def baggage(request:Request):
    data=await read_json(request)
    airline=clean(data.get("airline"))
    result=[]
    for s in baggage_sources():
        d=s if isinstance(s,dict) else source_dict(s)
        if not airline or airline.lower() in json.dumps(d,ensure_ascii=False).lower():
            result.append(d)
    if not result:
        result=baggage_sources()
    return {
        "ok":True,
        "airline":airline,
        "guidance":result,
        "notice":"Las dimensiones, peso y restricciones pueden cambiar. Verifica siempre la regla oficial de la aerolínea y, cuando corresponda, la autoridad de seguridad o aduana."
    }

@app.post("/api/v1/item")
async def item(request:Request):
    data=await read_json(request)
    question=clean(data.get("question") or data.get("item") or data.get("text"))
    language=clean(data.get("language")) or "es"
    if not question:
        return {
            "ok":False,
            "status":"missing",
            "answer":"Escribe el nombre del artículo que quieres consultar.",
            "next_action":"Ejemplo: ¿Puedo llevar agua en mi equipaje?"
        }
    prompt=item_prompt(question,data,language)
    result=gemini_request(prompt)
    if result.get("ok"):
        answer=result.get("data",{})
        if isinstance(answer,dict):
            answer.setdefault("needs_confirmation",True)
            answer.setdefault("next_action","Verifica la fuente oficial antes de empacar.")
            return {"ok":True,"item":question,"ai_assisted":True,"result":answer}
    return {
        "ok":True,
        "item":question,
        "ai_assisted":False,
        "result":local_item_fallback(question,data,language),
        "gemini_reason":result.get("reason","")
    }

@app.post("/api/v1/consultar-articulo")
async def consultar_articulo(request:Request):
    return await item(request)

@app.post("/api/v1/item/teach")
async def item_teach(request:Request):
    data=await read_json(request)
    term=clean(data.get("term") or data.get("item") or data.get("question"))
    language=clean(data.get("language")) or "es"
    common={
        "carry-on":("Equipaje de mano","La pieza que llevas contigo en la cabina."),
        "personal item":("Artículo personal","Una pieza pequeña que normalmente va debajo del asiento, según las reglas de la aerolínea."),
        "checked baggage":("Equipaje facturado","La maleta que entregas a la aerolínea para viajar en la bodega."),
        "connection":("Conexión","Cuando tu viaje incluye más de un vuelo para llegar al destino."),
        "visa":("Visa","Un documento o autorización que puede ser necesaria según el país, nacionalidad y propósito del viaje."),
        "d'viajeros":("D'Viajeros","Formulario oficial relacionado con el viaje a Cuba.")
    }
    key=term.lower()
    title,definition=common.get(key,(term,"Este término debe entenderse según el contexto específico del viaje y la fuente oficial correspondiente."))
    return {
        "ok":True,
        "language":language,
        "term":term,
        "title":title,
        "definition":definition,
        "next_action":"Continúa con el siguiente paso de tu preparación."
    }

@app.post("/api/v1/documents")
async def documents(request:Request):
    data=await read_json(request)
    return {
        "ok":True,
        "request":data,
        "documents":[
            "Pasaporte o documento de viaje aplicable",
            "Documentos requeridos por el destino",
            "Información de vuelo",
            "Documentos de entrada cuando correspondan",
            "Documentación adicional indicada por las autoridades oficiales"
        ],
        "notice":"La lista final depende de la nacionalidad, destino, tránsito y motivo del viaje. Verifica cada requisito con la fuente oficial."
    }

@app.post("/api/v1/guide")
async def guide(request:Request):
    data=await read_json(request)
    missing=[]
    for key,label in (
        ("origin","origen"),
        ("destination","destino"),
        ("date","fecha"),
        ("airline","aerolínea")
    ):
        if not clean(data.get(key)):
            missing.append(label)
    if is_cuba(data):
        next_action="Revisa primero los requisitos oficiales de entrada a Cuba, D’Viajeros, visa/eVisa y documentación."
    elif missing:
        next_action=f"Completa primero: {', '.join(missing)}."
    else:
        next_action="Continúa con la práctica de vuelo, equipaje y documentos."
    return {
        "ok":True,
        "diagnosis":{
            "type":"preparation_status",
            "known":data,
            "missing":missing,
            "next_action":next_action,
            "official_decision":False
        },
        "notice":"Esto es una evaluación de preparación, no una decisión oficial de inmigración, visa, aduana o aerolínea."
    }

@app.post("/api/v1/solve")
async def solve(request:Request):
    data=await read_json(request)
    question=clean(data.get("question"))
    if not question:
        return {
            "ok":False,
            "answer":"Escribe una pregunta concreta sobre un artículo que quieres llevar.",
            "next_action":"Usa la consulta de artículo para revisar equipaje."
        }
    return await item(request)

@app.post("/api/v1/pdf")
async def pdf(request:Request):
    data=await read_json(request)
    state=data.get("state")
    if not isinstance(state,dict):
        state=data
    language=clean(data.get("language")) or "es"
    pdf=build_pdf(state,language)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":'attachment; filename="mi_resumen_que_quieres_llevar.pdf"',
            "Cache-Control":"no-store"
        }
    )

@app.post("/api/v1/pdf/export")
async def pdf_export(request:Request):
    return await pdf(request)

@app.post("/api/v1/pdf/import")
async def pdf_import(file:UploadFile=File(...)):
    raw=await file.read()
    if len(raw)>MAX_BODY:
        raise HTTPException(413,"El PDF es demasiado grande.")
    if not raw.startswith(b"%PDF"):
        raise HTTPException(400,"El archivo enviado no parece ser un PDF válido.")
    try:
        state=extract_state_from_pdf(raw)
    except Exception as e:
        raise HTTPException(
            400,
            "No se pudo recuperar este PDF. Importa el PDF generado por ¿QUÉ QUIERES LLEVAR?."
        )
    return {
        "ok":True,
        "recovered":True,
        "local_only":True,
        "server_storage":False,
        "filename":file.filename or "",
        "state":state,
        "next_action":"Revisa los datos recuperados y cambia solamente lo que haya cambiado."
    }

@app.post("/api/v1/data/delete")
async def data_delete():
    return {
        "ok":True,
        "clear_local":True,
        "server_storage":False,
        "message":"La aplicación no guarda permanentemente los datos del cliente en el servidor. Borra el estado local de este dispositivo para eliminarlo de la aplicación.",
        "next_action":"Confirma la eliminación en la aplicación y limpia su almacenamiento local."
    }

@app.post("/api/v1/local-data/delete")
async def local_data_delete():
    return await data_delete()

@app.get("/api/v1/cuba/sources")
async def cuba_sources_endpoint():
    return {
        "ok":True,
        "official_sources":cuba_sources(),
        "charters":charter_sources(),
        "commercial_baggage":baggage_sources()
    }

@app.exception_handler(404)
async def not_found(request:Request,exc:Exception):
    return JSONResponse(
        status_code=404,
        content={
            "ok":False,
            "error":"Ruta no encontrada.",
            "path":request.url.path,
            "app":APP_NAME
        }
    )

@app.exception_handler(Exception)
async def generic_error(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "ok":False,
            "error":"Ocurrió un error interno.",
            "detail":str(exc),
            "app":APP_NAME
        }
    )
