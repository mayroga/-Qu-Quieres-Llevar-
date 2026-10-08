# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v15.0.1
from __future__ import annotations
import os,json,re,io,datetime,traceback
from typing import Any
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
import cuba_engine as engine
from schemas import *
from source_registry import VERSION as SOURCE_VERSION,SOURCES,all_sources,source_by_id,get_sources,official_sources,get_airlines,get_charters,official_url,answer_sources

VERSION="15.0.1"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
STATIC_DIR="static"
DEBUG=os.getenv("DEBUG","").lower()=="true"

app=FastAPI(title=APP_NAME,version=VERSION,docs_url="/docs" if DEBUG else None,redoc_url="/redoc" if DEBUG else None)
if os.path.isdir(STATIC_DIR):
    app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def model_dict(value:Any)->dict:
    if value is None:return {}
    if isinstance(value,dict):return value
    if hasattr(value,"model_dump"):return value.model_dump(exclude_none=False)
    if hasattr(value,"dict"):return value.dict()
    return dict(value) if hasattr(value,"__iter__") else {}

def clean(value:Any)->Any:
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,list):return [clean(v) for v in value]
    if isinstance(value,tuple):return [clean(v) for v in value]
    if isinstance(value,str):return value.strip()
    return value

def normalize_result(result:Any)->dict:
    if result is None:return {"ok":True,"version":VERSION,"sources":official_sources()}
    if isinstance(result,dict):
        result=clean(result)
        result.setdefault("ok",True)
        result.setdefault("version",VERSION)
        if "sources" not in result:
            result["sources"]=official_sources()
        return result
    return {"ok":True,"result":result,"version":VERSION,"sources":official_sources()}

def call_engine(name:str,data:Any)->dict:
    fn=getattr(engine,name,None)
    if not callable(fn):
        raise AttributeError(f"Engine function not found: {name}")
    d=clean(model_dict(data))
    try:
        return normalize_result(fn(d))
    except TypeError:
        return normalize_result(fn(**d))

@app.get("/",response_class=HTMLResponse)
async def home():
    path=os.path.join(STATIC_DIR,"index.html")
    if os.path.exists(path):
        with open(path,"r",encoding="utf-8") as f:return HTMLResponse(f.read())
    return HTMLResponse(f"<html><body><h1>{APP_NAME}</h1></body></html>")

@app.get("/health")
async def health():
    return {
        "status":"ok",
        "version":VERSION,
        "source_version":SOURCE_VERSION,
        "app":APP_NAME,
        "ready":True,
        "free":True,
        "login_required":False,
        "payment_required":False,
        "server_storage":False,
        "gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY")),
        "language_default":"es",
        "languages":["es","en"]
    }

@app.get("/api/config")
async def config():
    return {
        "ok":True,
        "version":VERSION,
        "language":"es",
        "languages":["es","en"],
        "free":True,
        "login":False,
        "payment":False,
        "stripe":False,
        "server_storage":False,
        "gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY")),
        "english":True,
        "features":{
            "dviajeros":True,
            "visa":True,
            "items":True,
            "flights":True,
            "airlines":True,
            "charters":True,
            "connections":True,
            "baggage":True,
            "documents":True,
            "practice":True,
            "booking_simulation":True,
            "pdf":True,
            "local_data":True,
            "official_sources":True,
            "gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY"))
        },
        "official_sources":official_sources()
    }

@app.post("/api/flight")
async def flight(data:FlightRequest):
    return call_engine("analyze_flight",data)

@app.post("/api/booking")
async def booking(data:BookingRequest):
    return call_engine("booking_simulation",data)

@app.post("/api/connection")
async def connection(data:ConnectionRequest):
    return call_engine("connection_analysis",data)

@app.post("/api/baggage")
async def baggage(data:BaggageRequest):
    return call_engine("baggage_rules",data)

@app.post("/api/item")
async def item(data:ItemRequest):
    result=call_engine("item_analysis",data)
    if not result.get("sources"):
        d=model_dict(data)
        result["sources"]=answer_sources(d.get("question",""),d.get("item",""),d.get("airline",""),d.get("country_of_destination",""))
    return result

@app.post("/api/cuba")
async def cuba(data:CubaRequest):
    return call_engine("cuba_check",data)

@app.post("/api/cuba/entry")
async def cuba_entry(data:CubaEntryRequest):
    return call_engine("cuba_entry",data)

@app.post("/api/documents")
async def documents(data:DocumentRequest):
    return call_engine("document_analysis",data)

@app.post("/api/practice")
async def practice(data:PracticeRequest):
    return call_engine("practice_scenario",data)

@app.post("/api/dviajeros")
async def dviajeros(data:DViajeroRequest):
    return call_engine("dviajeros_simulation",data)

@app.post("/api/visa")
async def visa(data:VisaRequest):
    return call_engine("visa_simulation",data)

@app.get("/api/sources")
async def sources(topic:str="official",query:str="",country:str="",airline:str=""):
    return {
        "ok":True,
        "version":VERSION,
        "source_version":SOURCE_VERSION,
        "sources":get_sources(topic,query,country,airline)
    }

@app.post("/api/sources")
async def sources_post(data:SourceRequest):
    d=model_dict(data)
    return {
        "ok":True,
        "version":VERSION,
        "source_version":SOURCE_VERSION,
        "sources":get_sources(d.get("topic","official"),d.get("query",""),d.get("country",""),d.get("airline",""))
    }

@app.get("/api/official")
async def official(topic:str="",country:str="",airline:str=""):
    return {
        "ok":True,
        "version":VERSION,
        "sources":official_sources(topic,country,airline)
    }

@app.get("/api/airlines")
async def airlines(query:str=""):
    return {
        "ok":True,
        "version":VERSION,
        "airlines":get_airlines(query)
    }

@app.post("/api/airlines")
async def airlines_post(data:AirlineRequest):
    d=model_dict(data)
    query=d.get("query") or d.get("airline") or d.get("name") or ""
    return {
        "ok":True,
        "version":VERSION,
        "airlines":get_airlines(query)
    }

@app.get("/api/charters")
async def charters(query:str=""):
    return {
        "ok":True,
        "version":VERSION,
        "charters":get_charters(query)
    }

@app.get("/api/cuba-official")
async def cuba_official():
    return {
        "ok":True,
        "version":VERSION,
        "sources":[s for s in all_sources() if "cuba" in " ".join([
            str(s.get("id","")),
            str(s.get("topics","")),
            str(s.get("country",""))
        ]).lower()]
    }

@app.get("/api/airlines-cuba")
async def airlines_cuba():
    airlines=get_airlines()
    return {
        "ok":True,
        "version":VERSION,
        "airlines":airlines,
        "charters":get_charters()
    }

@app.get("/api/source/{source_id}")
async def source(source_id:str):
    item=source_by_id(source_id)
    if not item:
        return JSONResponse({"ok":False,"error":"Fuente no encontrada","version":VERSION},status_code=404)
    return {"ok":True,"version":VERSION,"source":item}

@app.get("/api/url/{name}")
async def source_url(name:str):
    return {"ok":True,"name":name,"url":official_url(name)}

@app.post("/api/solve")
async def solve(data:SolveRequest):
    return call_engine("solve",data)

@app.post("/api/guide")
async def guide(data:GuideRequest):
    return call_engine("build_guide",data)

styles=getSampleStyleSheet()
STYLE_TITLE=ParagraphStyle("QQLTitle",parent=styles["Title"],alignment=TA_CENTER,fontSize=18,leading=22,spaceAfter=10)
STYLE_HEAD=ParagraphStyle("QQLHead",parent=styles["Heading2"],fontSize=12,leading=15,spaceBefore=7,spaceAfter=5)
STYLE_BODY=ParagraphStyle("QQLBody",parent=styles["BodyText"],fontSize=9,leading=12,spaceAfter=4)

def pdf_text(v:Any)->str:
    if v is None:return ""
    if isinstance(v,bool):return "Sí" if v else "No"
    if isinstance(v,(dict,list)):
        return json.dumps(v,ensure_ascii=False,indent=2)
    return str(v)

def pdf_line(label:str,value:Any):
    value=pdf_text(value)
    if not value:return None
    return Paragraph(f"<b>{label}</b> {value}",STYLE_BODY)

def make_pdf(data:dict,title:str="Mi guía de viaje"):
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=letter,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40)
    story=[Paragraph(title or "Mi guía de viaje",STYLE_TITLE)]
    story.append(Paragraph("¿QUÉ QUIERES LLEVAR? | May Roga LLC",STYLE_BODY))
    story.append(Paragraph("Guía personal de preparación. No es un documento oficial ni sustituye al sitio oficial correspondiente.",STYLE_BODY))
    story.append(Spacer(1,8))
    labels={
        "given_names":"Nombre",
        "surnames":"Apellidos",
        "nationality":"Nacionalidad",
        "passport_number":"Pasaporte",
        "passport_country":"País del pasaporte",
        "origin":"Salida",
        "destination":"Destino",
        "airline":"Aerolínea",
        "flight_number":"Vuelo",
        "departure":"Salida",
        "return_date":"Regreso",
        "arrival_date":"Llegada",
        "departure_date":"Salida del destino",
        "cabin":"Cabina",
        "fare":"Tarifa",
        "checked_bags":"Maletas registradas",
        "carry_on":"Equipaje de mano",
        "personal_item":"Artículo personal",
        "weight":"Peso",
        "dimensions":"Medidas",
        "pieces":"Cantidad",
        "item":"Artículo",
        "next_action":"Siguiente paso"
    }
    preferred=list(labels.keys())
    added=set()
    for key in preferred:
        if key in data and data.get(key) not in ("",None,[],{}):
            p=pdf_line(labels[key],data.get(key))
            if p:
                story.append(p);added.add(key)
    for key,value in data.items():
        if key in added or value in ("",None,[],{}):continue
        if key in ("sources","version","ok","updated_at"):continue
        p=pdf_line(str(key).replace("_"," ").capitalize(),value)
        if p:story.append(p)
    story.append(Spacer(1,10))
    story.append(Paragraph(f"Generado: {now()}",STYLE_BODY))
    story.append(Paragraph("Antes de viajar, confirma la información que pueda cambiar en el sitio oficial.",STYLE_BODY))
    doc.build(story)
    buf.seek(0)
    return buf

@app.post("/api/pdf")
async def pdf(data:PDFRequest):
    d=model_dict(data)
    payload=d.get("data") or {}
    if hasattr(payload,"model_dump"):payload=payload.model_dump()
    payload=clean(payload)
    payload["updated_at"]=now()
    pdf_file=make_pdf(payload,d.get("title") or "Mi guía de viaje")
    return StreamingResponse(
        pdf_file,
        media_type="application/pdf",
        headers={"Content-Disposition":"attachment; filename=mi-guia-que-quieres-llevar.pdf"}
    )

def extract_recovery(text:str)->dict:
    text=text or ""
    result={}
    patterns={
        "given_names":r"(?:nombre|names?)\s*[:\-]\s*(.+)",
        "surnames":r"(?:apellidos?|last name|surname)\s*[:\-]\s*(.+)",
        "nationality":r"(?:nacionalidad|nationality)\s*[:\-]\s*(.+)",
        "passport_number":r"(?:pasaporte|passport)\s*(?:número|numero|number|#)?\s*[:\-]\s*([A-Za-z0-9\-]+)",
        "airline":r"(?:aerolínea|aerolinea|airline)\s*[:\-]\s*(.+)",
        "flight_number":r"(?:vuelo|flight)\s*(?:número|numero|number|#)?\s*[:\-]\s*([A-Za-z0-9\-]+)",
        "origin":r"(?:origen|salida|origin)\s*[:\-]\s*(.+)",
        "destination":r"(?:destino|destination)\s*[:\-]\s*(.+)",
        "departure":r"(?:salida|departure)\s*[:\-]\s*(.+)",
        "return_date":r"(?:regreso|return)\s*[:\-]\s*(.+)",
        "email":r"(?:correo|email|e-mail)\s*[:\-]\s*([^\s]+)",
        "next_action":r"(?:siguiente paso|next step)\s*[:\-]\s*(.+)"
    }
    for key,pattern in patterns.items():
        m=re.search(pattern,text,re.I|re.M)
        if m:result[key]=m.group(1).strip()
    return result

@app.post("/api/pdf/import")
async def pdf_import(data:PDFImportRequest):
    d=model_dict(data)
    recovery=d.get("recovery_data")
    if recovery:
        if hasattr(recovery,"model_dump"):recovery=recovery.model_dump()
        return {"ok":True,"version":VERSION,"recovery_data":clean(recovery)}
    parsed=extract_recovery(d.get("text",""))
    return {
        "ok":True,
        "version":VERSION,
        "filename":d.get("filename",""),
        "recovery_data":parsed,
        "found":bool(parsed)
    }

@app.post("/api/export")
async def export(data:TripExportRequest):
    d=model_dict(data)
    return {
        "ok":True,
        "version":VERSION,
        "server_storage":False,
        "exported_at":now(),
        "data":clean(d.get("data") or {})
    }

@app.post("/api/local-data")
async def local_data(data:DeleteLocalRequest):
    d=model_dict(data)
    if not d.get("confirm"):
        return JSONResponse({"ok":False,"version":VERSION,"error":"Debes confirmar la eliminación."},status_code=400)
    return {
        "ok":True,
        "version":VERSION,
        "deleted":True,
        "message":"Los datos guardados en este navegador pueden eliminarse desde la aplicación. El servidor no conserva el viaje."
    }

@app.get("/api/legal")
async def legal():
    return {
        "ok":True,
        "version":VERSION,
        "points":[
            "¿QUÉ QUIERES LLEVAR? es una herramienta independiente de preparación.",
            "No es una agencia de viajes, aerolínea, aeropuerto ni gobierno.",
            "Las simulaciones no son trámites oficiales.",
            "La aplicación no compra vuelos, no paga visas y no presenta formularios oficiales por el usuario.",
            "Los trámites reales deben completarse en los sitios oficiales correspondientes.",
            "La información puede cambiar y debe confirmarse antes del viaje.",
            "Los datos del viaje se mantienen en el navegador y no se almacenan de forma permanente en el servidor."
        ]
    }

@app.get("/api/ping")
async def ping():
    return {"ok":True,"version":VERSION,"time":now()}

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"ok":False,"version":VERSION,"error":"Revisa los datos introducidos.","details":exc.errors()}
    )

@app.exception_handler(Exception)
async def general_error(request:Request,exc:Exception):
    if DEBUG:
        return JSONResponse(
            status_code=500,
            content={"ok":False,"version":VERSION,"error":str(exc),"traceback":traceback.format_exc()}
        )
    return JSONResponse(
        status_code=500,
        content={"ok":False,"version":VERSION,"error":"No se pudo completar esta acción. Inténtalo nuevamente."}
    )

__all__=["app"]
