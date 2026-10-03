# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
import json,os,re,time,urllib.error,urllib.request
from pathlib import Path
from typing import Any,Dict,Optional
from urllib.parse import quote_plus
from fastapi import FastAPI,HTTPException,Request,UploadFile,File
from fastapi.responses import FileResponse,JSONResponse,Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from cuba_engine import engine as cuba_engine
from source_registry import SOURCES,AIRLINES,get_sources,get_airlines,get_charters,get_official_sources,official_url

APP_NAME="¿QUÉ QUIERES LLEVAR?"
APP_VERSION="12.1.0"
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash").strip()

app=FastAPI(title=APP_NAME,version=APP_VERSION)
app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

class AnyRequest(BaseModel):
    data:Dict[str,Any]={}
    language:str="es"
    question:str=""
    scenario:str=""
    item:str=""
    state:Dict[str,Any]={}
    step:int=0
    answer:Any=None
    airline:str=""
    charter_operator:str=""
    simulation_id:str=""
    origin:str=""
    destination:str=""
    date:str=""
    mode:str=""
    topic:str=""
    query:str=""
    period:str=""
    baggage:Dict[str,Any]={}
    trip:Dict[str,Any]={}

def lang(v:str="es")->str:
    return "en" if str(v or "").lower().strip()=="en" else "es"

def body_data(x:Any)->Dict[str,Any]:
    if isinstance(x,dict):return dict(x.get("data") or x)
    try:return x.model_dump()
    except Exception:return {}

def merge_data(*items:Any)->Dict[str,Any]:
    out={}
    for x in items:
        if isinstance(x,dict):
            for k,v in x.items():
                if v is not None and str(v).strip()!="":out[k]=v
    return out

def normalize_state(data:Dict[str,Any])->Dict[str,Any]:
    d=dict(data or {})
    aliases={
        "first_name":["first_name","given_names","name"],
        "last_name":["last_name","surnames","family_name"],
        "nationality":["nationality","country"],
        "date_of_birth":["date_of_birth","birth_date"],
        "passport_country":["passport_country","passport_nationality"],
        "passport_number":["passport_number","passport_no"],
        "arrival_date":["arrival_date","travel_date","date"],
        "airline":["airline","airline_name"],
        "accommodation":["accommodation","lodging","hotel"],
        "purpose_of_trip":["purpose_of_trip","travel_purpose","purpose"],
        "origin":["origin","from","departure"],
        "destination":["destination","to","arrival"],
        "flight_date":["flight_date","travel_date","date"],
        "charter_operator":["charter_operator","charter","operator"],
        "carry_on":["carry_on","hand_baggage"],
        "personal_item":["personal_item","personal_bag"],
        "checked_baggage":["checked_baggage","checked_bag"],
        "travel_purpose":["travel_purpose","purpose_of_trip","purpose"]
    }
    for target,keys in aliases.items():
        if str(d.get(target,"")).strip()=="": 
            for k in keys:
                if str(d.get(k,"")).strip()!="":
                    d[target]=d[k];break
    return d

def official_for_item(item:str,language:str="es")->List[Dict[str,Any]]:
    q=str(item or "").lower()
    ids=["tsa_what_can_i_bring","tsa_liquids","tsa_batteries","tsa_medication"]
    if any(x in q for x in ["carne","meat","jamon","ham","fruta","fruit","semilla","seed","comida","food","agua","water","yogur","yogurt","gasolina","gasoline","petroleo","petroleum","aceite","oil"]):
        ids+=["cuba_aduana"]
    out=[]
    for x in SOURCES:
        if x.id in ids:
            d=dict(x.__dict__)
            d["topics"]=list(d.get("topics",()))
            out.append(d)
    return out

def gemini_item(item:str,language:str="es")->Dict[str,Any]:
    item=str(item or "").strip()
    if not item:return {"ok":False,"answer":"","sources":[],"notice":"Indica primero qué artículo quieres llevar." if language!="en" else "First tell me which item you want to bring."}
    if not GEMINI_API_KEY:
        return {"ok":False,"answer":"","sources":official_for_item(item,language),"notice":"Consulta la fuente oficial correspondiente para confirmar este artículo." if language!="en" else "Check the applicable official source to confirm this item."}
    if language=="en":
        prompt=f"""You are part of ¿QUÉ QUIERES LLEVAR? by May Roga LLC. The customer asks whether this travel item may be carried: "{item}". Answer ONLY for travel baggage/security guidance. Do not invent laws, limits, fees, airline rules, customs rules or destination requirements. Clearly distinguish carry-on and checked baggage when possible. If you cannot reliably determine the answer, say that official confirmation is required. Do not give general travel advice. Do not ask for passwords, account credentials, payment information or security codes."""
    else:
        prompt=f"""Eres parte de ¿QUÉ QUIERES LLEVAR? de May Roga LLC. El cliente pregunta si puede llevar este artículo durante un viaje: "{item}". Responde ÚNICAMENTE sobre orientación de equipaje/seguridad. No inventes leyes, límites, tarifas, reglas de aerolíneas, aduana ni requisitos del destino. Distingue equipaje de mano y facturado cuando sea posible. Si no puedes determinarlo con seguridad, indica que debe confirmarse en la fuente oficial. No des consejos generales ajenos al artículo. No pidas contraseñas, credenciales, información de pago ni códigos de seguridad."""
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{quote_plus(GEMINI_MODEL)}:generateContent?key={quote_plus(GEMINI_API_KEY)}"
    payload={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.1,"maxOutputTokens":700}}
    try:
        req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(req,timeout=25) as r:
            obj=json.loads(r.read().decode("utf-8"))
        answer=""
        try:answer=obj["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:answer=""
        if not answer:raise ValueError("empty")
        return {"ok":True,"answer":answer,"sources":official_for_item(item,language),"notice":"Confirma siempre la condición aplicable en la fuente oficial antes de viajar." if language!="en" else "Always confirm the applicable condition on the official source before traveling."}
    except Exception:
        return {"ok":False,"answer":"","sources":official_for_item(item,language),"notice":"No pude confirmar este artículo automáticamente. Abre la fuente oficial indicada para verificarlo." if language!="en" else "I could not confirm this item automatically. Open the indicated official source to verify it."}

def booking_steps(language:str="es",data:Optional[Dict[str,Any]]=None)->List[Dict[str,Any]]:
    d=normalize_state(data or {})
    en=language=="en"
    labels=[
        ("Datos del pasajero","Passenger information",["first_name","last_name"]),
        ("Ruta","Route",["origin","destination"]),
        ("Fecha y vuelo","Date and flight",["flight_date","airline"]),
        ("Equipaje","Baggage",["carry_on","personal_item","checked_baggage"]),
        ("Revisión","Review",[]),
        ("Confirmación simulada","Practice confirmation",[])
    ]
    out=[]
    for i,(es,enx,keys) in enumerate(labels,1):
        vals=[d.get(k) for k in keys]
        complete=all(str(v or "").strip() for v in vals) if keys else False
        out.append({"step":i,"title":enx if en else es,"completed":complete})
    return out

def flight_search_url(origin:str="",destination:str="",date:str="")->str:
    q=" ".join(x for x in [origin,destination,date] if x)
    return "https://www.google.com/travel/flights?q="+quote_plus(q)

def legal_text(language:str="es")->str:
    if language=="en":
        return "¿QUÉ QUIERES LLEVAR? is an independent preparation and orientation service of May Roga LLC. It is not an airline, airport, government, customs authority, immigration authority, consulate, travel agency or official processing platform. Practices do not submit official applications, reservations, payments, visas or D’Viajeros forms. Official requirements and decisions belong to the responsible authorities, airlines and providers."
    return "¿QUÉ QUIERES LLEVAR? es un servicio independiente de preparación y orientación de May Roga LLC. No es una aerolínea, aeropuerto, gobierno, autoridad aduanera, autoridad migratoria, consulado, agencia de viajes ni plataforma oficial de trámites. Las prácticas no presentan solicitudes oficiales, reservas, pagos, visas ni formularios D’Viajeros. Los requisitos y decisiones oficiales corresponden a las autoridades, aerolíneas y proveedores responsables."

@app.get("/")
async def home():
    return FileResponse(STATIC_DIR/"index.html")

@app.get("/health")
async def health():
    return {"ok":True,"app":APP_NAME,"version":APP_VERSION,"free":True,"login":False}

@app.get("/api/v1/config")
async def config(language:str="es"):
    l=lang(language)
    return {
        "name":APP_NAME,
        "version":APP_VERSION,
        "language":l,
        "free":True,
        "login":False,
        "payment":False,
        "gemini_item_only":True,
        "cuba":cuba_engine.public_config(l),
        "airlines":get_airlines(),
        "charters":get_charters(""),
        "sources":get_sources("all",""),
        "legal":legal_text(l)
    }

@app.get("/api/v1/session")
async def session(language:str="es"):
    l=lang(language)
    return {"ok":True,"free":True,"login":False,"authenticated":False,"language":l,"message":"Uso libre de la aplicación." if l=="es" else "Free use of the application."}

@app.post("/api/v1/flight")
async def flight(req:AnyRequest):
    d=normalize_state(body_data(req))
    return {
        "ok":True,
        "flight":d,
        "search":flight_search_url(d.get("origin",""),d.get("destination",""),d.get("flight_date","")),
        "steps":booking_steps(req.language,d),
        "simulation":True,
        "official_submission":False,
        "next_action":"Practica con tu aerolínea o abre la búsqueda para continuar." if lang(req.language)=="es" else "Practice with your airline or open the search to continue."
    }

@app.post("/api/v1/booking")
async def booking(req:AnyRequest):
    d=normalize_state(body_data(req))
    l=lang(req.language)
    return {
        "ok":True,
        "simulation":True,
        "real_booking":False,
        "payment":False,
        "notice":"PRÁCTICA: no se reserva ni se paga un boleto." if l=="es" else "PRACTICE: no ticket is booked or paid.",
        "search":flight_search_url(d.get("origin",""),d.get("destination",""),d.get("flight_date","")),
        "fields":d,
        "steps":booking_steps(l,d),
        "next_action":"Cuando termines la práctica, continúa en el sitio oficial de la aerolínea." if l=="es" else "When you finish the practice, continue on the airline's official website.",
        "official_url":next((x["url"] for x in get_airlines(d.get("airline","")) if x.get("name","").lower()==str(d.get("airline","")).lower()),"")
    }

@app.post("/api/v1/flight/search-external")
async def flight_search_external(req:AnyRequest):
    d=normalize_state(body_data(req))
    return {"ok":True,"url":flight_search_url(d.get("origin",""),d.get("destination",""),d.get("date") or d.get("flight_date","")),"query":d}

@app.post("/api/v1/consultar-articulo")
async def consultar_articulo(req:AnyRequest):
    d=body_data(req)
    item=req.item or d.get("item") or req.question or d.get("question","")
    return gemini_item(item,lang(req.language))

@app.post("/api/v1/item")
async def item(req:AnyRequest):
    d=body_data(req)
    item=req.item or d.get("item") or req.question or d.get("question","")
    return gemini_item(item,lang(req.language))

@app.post("/api/v1/item/teach")
async def item_teach(req:AnyRequest):
    d=body_data(req)
    item=req.item or d.get("item") or req.question or d.get("question","")
    l=lang(req.language)
    result=gemini_item(item,l)
    result["title"]="Qué llevar" if l=="es" else "What to bring"
    return result

@app.post("/api/v1/baggage")
async def baggage(req:AnyRequest):
    d=normalize_state(body_data(req))
    l=lang(req.language)
    cuba=cuba_engine.is_cuba_route(d.get("origin",""),d.get("destination",""))
    return {
        "ok":True,
        "data":d,
        "cuba_route":cuba,
        "guide":cuba_engine.baggage_guide(l) if cuba else {"title":"Guía de equipaje" if l=="es" else "Baggage guide","sources":get_sources("baggage",""),"next_action":"Confirma siempre la franquicia de tu boleto en la fuente oficial." if l=="es" else "Always confirm your ticket allowance on the official source."}
    }

@app.post("/api/v1/cuba")
async def cuba(req:AnyRequest):
    d=normalize_state(body_data(req))
    l=lang(req.language)
    return {"ok":True,"route":cuba_engine.is_cuba_route(d.get("origin",""),d.get("destination","")),"config":cuba_engine.public_config(l),"data":d}

@app.post("/api/v1/cuba/guide")
async def cuba_guide(req:AnyRequest):
    return cuba_engine.baggage_guide(lang(req.language))

@app.get("/api/v1/cuba/guide")
async def cuba_guide_get(language:str="es"):
    return cuba_engine.baggage_guide(lang(language))

@app.post("/api/v1/cuba/visa")
async def cuba_visa(req:AnyRequest):
    d=normalize_state(body_data(req))
    return cuba_engine.evaluate_visa(d,lang(req.language))

@app.post("/api/v1/cuba/dviajeros")
async def cuba_dviajeros(req:AnyRequest):
    d=normalize_state(body_data(req))
    return cuba_engine.evaluate_dviajeros(d,lang(req.language))

@app.post("/api/v1/practice")
async def practice(req:AnyRequest):
    d=normalize_state(body_data(req))
    l=lang(req.language)
    mode=req.mode or req.scenario or d.get("mode") or "booking"
    if mode=="visa":result=cuba_engine.evaluate_visa(d,l)
    elif mode in ("dviajeros","dviajero"):result=cuba_engine.evaluate_dviajeros(d,l)
    else:
        result=cuba_engine.simulation(mode,l)
        result["fields"]=d
        result["steps"]=booking_steps(l,d) if mode=="booking" else result["steps"]
    result["simulation"]=True
    result["official_submission"]=False
    result["data"]=d
    return result

@app.post("/api/v1/practice/visa")
async def practice_visa(req:AnyRequest):
    d=normalize_state(body_data(req))
    return cuba_engine.evaluate_visa(d,lang(req.language))

@app.post("/api/v1/practice/dviajeros")
async def practice_dviajeros(req:AnyRequest):
    d=normalize_state(body_data(req))
    return cuba_engine.evaluate_dviajeros(d,lang(req.language))

@app.post("/api/v1/airlines")
async def airlines(req:AnyRequest):
    q=req.query or req.airline
    return {"ok":True,"airlines":get_airlines(q)}

@app.get("/api/v1/airlines")
async def airlines_get(query:str="",language:str="es"):
    return {"ok":True,"airlines":get_airlines(query)}

@app.post("/api/v1/charters")
async def charters(req:AnyRequest):
    return {"ok":True,"charters":get_charters("")}

@app.get("/api/v1/charters")
async def charters_get(language:str="es"):
    return {"ok":True,"charters":cuba_engine.get_charter_sources(lang(language))}

@app.post("/api/v1/sources")
async def sources(req:AnyRequest):
    return {"ok":True,"sources":get_sources(req.topic or "all",req.query)}

@app.get("/api/v1/official")
async def official(language:str="es",topic:str="",query:str=""):
    return {"ok":True,"sources":get_sources(topic or "official",query),"cuba":cuba_engine.official_information(lang(language))}

@app.post("/api/v1/official")
async def official_post(req:AnyRequest):
    return {"ok":True,"sources":get_sources(req.topic or "official",req.query),"cuba":cuba_engine.official_information(lang(req.language))}

@app.post("/api/v1/guide")
async def guide(req:AnyRequest):
    d=normalize_state(body_data(req))
    l=lang(req.language)
    cuba=cuba_engine.is_cuba_route(d.get("origin",""),d.get("destination",""))
    return {
        "ok":True,
        "title":"Mi guía" if l=="es" else "My guide",
        "data":d,
        "cuba":cuba,
        "baggage":cuba_engine.baggage_guide(l) if cuba else None,
        "official":cuba_engine.official_information(l),
        "next_action":"Continúa con el paso que aparezca como pendiente." if l=="es" else "Continue with the step shown as pending."
    }

@app.post("/api/v1/solve")
async def solve(req:AnyRequest):
    d=body_data(req)
    item=req.item or d.get("item","")
    question=req.question or d.get("question","")
    if item or any(x in question.lower() for x in ["llevar","llevo","carry","bring"]):
        return gemini_item(item or question,lang(req.language))
    l=lang(req.language)
    return {
        "ok":True,
        "answer":"La aplicación organiza la información y te dirige al proceso oficial correspondiente." if l=="es" else "The app organizes the information and directs you to the applicable official process.",
        "sources":get_sources("official",question)
    }

@app.get("/api/v1/legal")
async def legal(language:str="es"):
    return {"ok":True,"text":legal_text(lang(language))}

@app.post("/api/v1/legal")
async def legal_post(req:AnyRequest):
    return {"ok":True,"text":legal_text(lang(req.language))}

def pdf_payload(data:Dict[str,Any],language:str="es")->Dict[str,Any]:
    d=normalize_state(data)
    l=lang(language)
    return {
        "app":APP_NAME,
        "version":APP_VERSION,
        "created_at":time.strftime("%Y-%m-%d %H:%M:%S"),
        "language":l,
        "official":False,
        "document_type":"may_roga_travel_preparation",
        "state":d,
        "notice":"Documento de preparación y guía. No es un documento oficial." if l=="es" else "Preparation and guide document. This is not an official document.",
        "continuity":"Este archivo puede volver a importarse en ¿QUÉ QUIERES LLEVAR? para recuperar los datos." if l=="es" else "This file can be imported again into ¿QUÉ QUIERES LLEVAR? to recover the data."
    }

def make_pdf(data:Dict[str,Any],language:str="es")->bytes:
    try:
        from reportlab.lib.pagesizes import LETTER
        from reportlab.lib.styles import getSampleStyleSheet,Paragraph
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Table,TableStyle
        from reportlab.lib import colors
        from io import BytesIO
    except Exception as e:
        raise HTTPException(500,"PDF no disponible: "+str(e))
    l=lang(language)
    p=pdf_payload(data,l)
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=LETTER,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
    styles=getSampleStyleSheet()
    title=styles["Title"];title.alignment=TA_CENTER
    story=[Paragraph(APP_NAME,title),Spacer(1,12),Paragraph(p["notice"],styles["Heading2"]),Spacer(1,10)]
    state=p["state"]
    labels={
        "first_name":"Nombre","last_name":"Apellido","nationality":"Nacionalidad","date_of_birth":"Fecha de nacimiento",
        "passport_country":"País del pasaporte","passport_number":"Número de pasaporte","origin":"Origen",
        "destination":"Destino","flight_date":"Fecha del viaje","arrival_date":"Fecha de llegada",
        "airline":"Aerolínea","accommodation":"Alojamiento","purpose_of_trip":"Motivo del viaje",
        "travel_purpose":"Motivo del viaje","charter_operator":"Operador chárter","carry_on":"Equipaje de mano",
        "personal_item":"Artículo personal","checked_baggage":"Equipaje facturado"
    }
    rows=[["Dato","Información"]]
    for k,v in state.items():
        if isinstance(v,(dict,list)):continue
        if str(v).strip()=="" or k in ("password","token","access_token"):continue
        rows.append([labels.get(k,k.replace("_"," ").title()),str(v)])
    if len(rows)>1:
        t=Table(rows,colWidths=[170,300])
        t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,colors.grey),("BACKGROUND",(0,0),(-1,0),colors.lightgrey),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story+=[Paragraph("Resumen de preparación" if l=="es" else "Preparation summary",styles["Heading2"]),t,PageBreak()]
    story+=[Paragraph("Continuidad" if l=="es" else "Continuity",styles["Heading2"]),Paragraph(p["continuity"],styles["BodyText"]),Spacer(1,12),Paragraph("La aplicación no guarda permanentemente este documento en el servidor. El cliente decide dónde conservarlo y cuándo volver a importarlo." if l=="es" else "The application does not permanently store this document on the server. The customer decides where to keep it and when to import it again.",styles["BodyText"]),PageBreak()]
    story+=[Paragraph("Aviso" if l=="es" else "Notice",styles["Heading2"]),Paragraph(legal_text(l),styles["BodyText"])]
    doc.build(story)
    return buf.getvalue()

@app.post("/api/v1/pdf")
async def pdf(req:AnyRequest):
    d=merge_data(req.data,req.state,req.trip,req.baggage)
    pdf=make_pdf(d,lang(req.language))
    return Response(content=pdf,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=que-quieres-llevar-resumen.pdf","Cache-Control":"no-store"})

@app.post("/api/v1/pdf/import")
async def pdf_import(file:UploadFile=File(...),language:str="es"):
    raw=await file.read()
    if not raw:raise HTTPException(400,"El archivo está vacío.")
    text=""
    try:
        from pypdf import PdfReader
        import io
        reader=PdfReader(io.BytesIO(raw))
        text="\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception as e:
        raise HTTPException(400,"No se pudo leer el PDF generado por la aplicación.")
    if "¿QUÉ QUIERES LLEVAR?" not in text and "QUÉ QUIERES LLEVAR" not in text:
        raise HTTPException(400,"Este PDF no parece ser un resumen generado por ¿QUÉ QUIERES LLEVAR?.")
    labels={
        "Nombre":"first_name","Apellido":"last_name","Nacionalidad":"nationality","Fecha de nacimiento":"date_of_birth",
        "País del pasaporte":"passport_country","Número de pasaporte":"passport_number","Origen":"origin",
        "Destino":"destination","Fecha del viaje":"flight_date","Fecha de llegada":"arrival_date",
        "Aerolínea":"airline","Alojamiento":"accommodation","Motivo del viaje":"purpose_of_trip",
        "Operador chárter":"charter_operator","Equipaje de mano":"carry_on","Artículo personal":"personal_item",
        "Equipaje facturado":"checked_baggage"
    }
    data={}
    for label,key in labels.items():
        m=re.search(r"(?m)^"+re.escape(label)+r"\s+(.+?)\s*$",text)
        if m:data[key]=m.group(1).strip()
    return {
        "ok":True,
        "imported":True,
        "language":lang(language),
        "data":normalize_state(data),
        "message":"Datos recuperados. Revisa y actualiza solamente lo que haya cambiado." if lang(language)=="es" else "Data recovered. Review and update only what has changed.",
        "next_action":"Continúa con la práctica que necesites." if lang(language)=="es" else "Continue with the practice you need."
    }

@app.post("/api/v1/pdf/import-data")
async def pdf_import_data(file:UploadFile=File(...),language:str="es"):
    return await pdf_import(file,language)

@app.post("/api/v1/data/clear")
async def data_clear():
    return {"ok":True,"clear_local":True,"server_storage":False,"message":"Los datos locales deben ser eliminados por la aplicación en el dispositivo del cliente."}

@app.get("/api/v1/access/check")
async def access_check():
    return {"ok":True,"free":True,"login":False,"payment":False,"allowed":True}

@app.get("/api/v1/admin/status")
async def admin_status():
    return {"ok":True,"admin_login":False,"message":"La aplicación no utiliza login de cliente ni acceso pagado."}

@app.post("/api/v1/admin/login")
async def admin_login():
    return {"ok":False,"enabled":False,"message":"No existe login de cliente ni sistema de acceso pagado."}

@app.get("/api/v1/cuba/official")
async def cuba_official(language:str="es"):
    return cuba_engine.official_information(lang(language))

@app.get("/api/v1/cuba/charters")
async def cuba_charters(language:str="es"):
    return {"ok":True,"charters":cuba_engine.get_charter_sources(lang(language))}

@app.get("/api/v1/cuba/baggage")
async def cuba_baggage(language:str="es"):
    return cuba_engine.baggage_guide(lang(language))
