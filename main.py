# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v15.0.0
from __future__ import annotations
import os,json,re,io,datetime,traceback
from typing import Any,Dict
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

import cuba_engine as engine
from schemas import *
from source_registry import (
    VERSION as SOURCE_VERSION,SOURCES,all_sources,source_by_id,
    get_sources,official_sources,get_airlines,get_charters,
    official_url,answer_sources
)

VERSION="15.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
STATIC_DIR="static"

app=FastAPI(title=APP_NAME,version=VERSION)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

def now():
    return datetime.datetime.now().isoformat(timespec="seconds")

def model_dict(x):
    if x is None:return {}
    if isinstance(x,dict):return x
    if hasattr(x,"model_dump"):return x.model_dump(exclude_none=False)
    if hasattr(x,"dict"):return x.dict()
    return dict(x)

def clean(v):
    if isinstance(v,str):return v.strip()
    return v

def normalize_result(result:Any,default_sources=None)->Dict[str,Any]:
    if result is None:result={}
    if hasattr(result,"model_dump"):result=result.model_dump()
    elif not isinstance(result,dict):
        result={"message":str(result)}
    result=dict(result)
    if "sources" not in result or not isinstance(result.get("sources"),list):
        result["sources"]=default_sources or official_sources()
    if not result.get("next_action"):
        result["next_action"]="Comprueba el dato final en la fuente oficial correspondiente."
    return result

def call_engine(name,*args,data=None):
    fn=getattr(engine,name,None)
    if not fn:
        return {"status":"error","message":f"Función no disponible: {name}","next_action":"Revisa la instalación de la aplicación."}
    d=model_dict(data)
    try:
        return normalize_result(fn(*args,d))
    except TypeError:
        try:return normalize_result(fn(d))
        except Exception as e:return {"status":"error","message":str(e),"next_action":"Inténtalo nuevamente."}
    except Exception as e:
        return {"status":"error","message":str(e),"next_action":"Inténtalo nuevamente."}

@app.get("/",response_class=HTMLResponse)
async def home():
    path=os.path.join(STATIC_DIR,"index.html")
    try:
        with open(path,"r",encoding="utf-8") as f:return HTMLResponse(f.read())
    except Exception:return HTMLResponse("<h1>¿QUÉ QUIERES LLEVAR?</h1><p>No se pudo cargar la aplicación.</p>",status_code=500)

@app.get("/health")
async def health():
    gemini=bool(os.getenv("GEMINI_API_KEY","").strip())
    return {
        "status":"ok","version":VERSION,"source_version":SOURCE_VERSION,
        "app":APP_NAME,"ready":True,"free":True,
        "login_required":False,"payment_required":False,
        "server_storage":False,"gemini_item_assistant":gemini
    }

@app.get("/api/config")
async def config():
    return {
        "status":"ok","app":APP_NAME,"version":VERSION,
        "language":"es","free":True,"login_required":False,
        "payment_required":False,"stripe_enabled":False,
        "server_storage":False,
        "features":{
            "dviajeros":True,"visa":True,"items":True,"flights":True,
            "airlines":True,"charters":True,"baggage":True,
            "documents":True,"practice":True,"booking_simulation":True,
            "pdf":True,"local_data":True,"official_sources":True,
            "gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY","").strip()),
            "english":False
        },
        "official_sources":official_sources()
    }

@app.post("/api/flight")
async def flight(data:FlightRequest):
    return call_engine("analyze_flight",data=data)

@app.post("/api/booking")
async def booking(data:BookingRequest):
    return call_engine("booking_simulation",data=data)

@app.post("/api/connection")
async def connection(data:ConnectionRequest):
    return call_engine("connection_analysis",data=data)

@app.post("/api/baggage")
async def baggage(data:BaggageRequest):
    return call_engine("baggage_rules",data=data)

@app.post("/api/item")
async def item(data:ItemRequest):
    return call_engine("item_analysis",data=data)

@app.post("/api/cuba")
async def cuba(data:CubaRequest):
    return call_engine("cuba_check",data=data)

@app.post("/api/cuba/entry")
async def cuba_entry(data:CubaEntryRequest):
    return call_engine("cuba_entry",data=data)

@app.post("/api/documents")
async def documents(data:DocumentRequest):
    return call_engine("document_analysis",data=data)

@app.post("/api/practice")
async def practice(data:PracticeRequest):
    return call_engine("practice_scenario",data=data)

@app.post("/api/dviajeros")
async def dviajeros(data:DViajeroRequest):
    return call_engine("dviajeros_simulation",data=data)

@app.post("/api/visa")
async def visa(data:VisaRequest):
    return call_engine("visa_simulation",data=data)

@app.get("/api/sources")
async def sources_get(topic:str="official",query:str="",country:str="",airline:str=""):
    return {
        "status":"ok","topic":topic,
        "sources":get_sources(topic,query,country,airline),
        "next_action":"Abre la fuente oficial que corresponda a tu trámite."
    }

@app.post("/api/sources")
async def sources_post(data:SourceRequest):
    return {
        "status":"ok","topic":data.topic,
        "sources":get_sources(data.topic,data.query,data.country,data.airline),
        "next_action":"Comprueba el dato final directamente en la fuente oficial."
    }

@app.get("/api/official")
async def official(topic:str="",country:str="",airline:str=""):
    return {
        "status":"ok","topic":topic,
        "sources":official_sources(topic,country,airline),
        "next_action":"Usa estas fuentes para confirmar la información."
    }

@app.get("/api/airlines")
async def airlines_get(query:str=""):
    return {
        "status":"ok",
        "airlines":get_airlines(query),
        "charters":get_charters(query),
        "next_action":"Selecciona el proveedor y continúa en su sitio oficial."
    }

@app.post("/api/airlines")
async def airlines_post(data:AirlineRequest):
    q=data.query if hasattr(data,"query") else (data.name or data.airline)
    return {
        "status":"ok",
        "airlines":get_airlines(q),
        "charters":get_charters(q),
        "next_action":"Comprueba la ruta y disponibilidad directamente con el proveedor."
    }

@app.get("/api/charters")
async def charters(query:str=""):
    return {
        "status":"ok",
        "charters":get_charters(query),
        "next_action":"Comprueba disponibilidad y condiciones directamente con el operador."
    }

@app.get("/api/cuba-official")
async def cuba_official():
    return {
        "status":"ok",
        "sources":official_sources("cuba"),
        "next_action":"Comprueba los requisitos actuales en las fuentes oficiales."
    }

@app.get("/api/airlines-cuba")
async def airlines_cuba():
    return {
        "status":"ok",
        "airlines":get_airlines(),
        "charters":get_charters(),
        "next_action":"Consulta directamente al proveedor para ruta, fecha y disponibilidad."
    }

@app.post("/api/solve")
async def solve(data:SolveRequest):
    return call_engine("solve",data=data)

@app.post("/api/guide")
async def guide(data:GuideRequest):
    return call_engine("build_guide",data=data)

def pdf_text(v):
    if v is None:return ""
    if isinstance(v,(dict,list)):
        return json.dumps(v,ensure_ascii=False)
    return str(v)

def pdf_line(label,value):
    if value in ("",None,False,[],{}):return None
    return Paragraph(f"<b>{label}:</b> {pdf_text(value)}",STYLE)

def make_pdf(data:Dict[str,Any],lang="es",title=None):
    buffer=io.BytesIO()
    doc=SimpleDocTemplate(
        buffer,pagesize=letter,
        rightMargin=.55*inch,leftMargin=.55*inch,
        topMargin=.55*inch,bottomMargin=.55*inch
    )
    styles=getSampleStyleSheet()
    title_style=styles["Title"]
    title_style.alignment=TA_CENTER
    story=[]
    story.append(Paragraph(title or APP_NAME,title_style))
    story.append(Spacer(1,8))
    story.append(Paragraph(
        "Resumen de preparación independiente. No es un documento oficial y no sustituye a las autoridades, aerolíneas, aeropuertos ni proveedores.",
        STYLE
    ))
    story.append(Spacer(1,10))

    labels={
        "given_names":"Nombres","surnames":"Apellidos",
        "nationality":"Nacionalidad","passport_number":"Pasaporte",
        "country_of_residence":"País de residencia","origin":"Origen",
        "destination":"Destino","airline":"Aerolínea",
        "flight_number":"Número de vuelo","flight_type":"Tipo de vuelo",
        "arrival_date":"Fecha de entrada","departure_date":"Fecha de salida",
        "arrival_airport":"Aeropuerto de llegada",
        "departure_airport":"Aeropuerto de salida",
        "purpose":"Motivo del viaje","email":"Correo electrónico",
        "phone":"Teléfono","address_destination":"Alojamiento",
        "visa_number":"Número/referencia de visa",
        "evisa_number":"Referencia e-Visa",
        "accommodation_type":"Tipo de alojamiento",
        "province":"Provincia","municipality":"Municipio",
        "accommodation_name":"Alojamiento",
        "passport_valid_until":"Pasaporte válido hasta",
        "dviajeros_done":"D'Viajeros preparado",
        "visa_checked":"Visa revisada",
        "documents_checked":"Documentos revisados",
        "baggage_checked":"Equipaje revisado",
        "customs_checked":"Aduana revisada",
        "next_action":"Próxima acción"
    }

    story.append(Paragraph("MI PREPARACIÓN",styles["Heading2"]))
    for k,v in data.items():
        if k in ("items","baggage","practice","sources","updated_at"):continue
        if k not in labels:continue
        line=pdf_line(labels[k],v)
        if line:story.append(line);story.append(Spacer(1,3))

    baggage=data.get("baggage") or {}
    if baggage:
        story.append(Spacer(1,8))
        story.append(Paragraph("EQUIPAJE",styles["Heading2"]))
        for k,v in baggage.items():
            line=pdf_line(k.replace("_"," ").capitalize(),v)
            if line:story.append(line);story.append(Spacer(1,3))

    items=data.get("items") or []
    if items:
        story.append(Spacer(1,8))
        story.append(Paragraph("CONSULTAS DE ARTÍCULOS",styles["Heading2"]))
        rows=[["Artículo","Resultado","Próxima acción"]]
        for x in items:
            if not isinstance(x,dict):continue
            rows.append([
                pdf_text(x.get("item","")),
                pdf_text(x.get("message",x.get("status",""))),
                pdf_text(x.get("next_action",""))
            ])
        if len(rows)>1:
            t=Table(rows,colWidths=[1.45*inch,3.05*inch,2.15*inch],repeatRows=1)
            t.setStyle(TableStyle([
                ("GRID",(0,0),(-1,-1),.5,colors.grey),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("FONTSIZE",(0,0),(-1,-1),8),
                ("LEFTPADDING",(0,0),(-1,-1),5),
                ("RIGHTPADDING",(0,0),(-1,-1),5),
                ("TOPPADDING",(0,0),(-1,-1),5),
                ("BOTTOMPADDING",(0,0),(-1,-1),5)
            ]))
            story.append(t)

    practice=data.get("practice") or {}
    if practice:
        story.append(Spacer(1,8))
        story.append(Paragraph("PRÁCTICA / SIMULACIÓN",styles["Heading2"]))
        for k,v in practice.items():
            line=pdf_line(k.replace("_"," ").capitalize(),v)
            if line:story.append(line);story.append(Spacer(1,3))

    story.append(Spacer(1,12))
    story.append(Paragraph(
        f"Generado: {now()} — {APP_NAME} | May Roga LLC",
        styles["Normal"]
    ))
    story.append(Spacer(1,5))
    story.append(Paragraph(
        "La información puede cambiar. Verifica siempre el dato final en el sitio oficial correspondiente.",
        styles["Normal"]
    ))
    doc.build(story)
    buffer.seek(0)
    return buffer

STYLE=getSampleStyleSheet()["BodyText"]

@app.post("/api/pdf")
async def pdf(data:PDFRequest):
    payload=model_dict(data.data)
    payload["updated_at"]=now()
    buffer=make_pdf(payload,data.lang,data.title)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition":"attachment; filename=mi-guia-que-quieres-llevar.pdf"}
    )

def extract_recovery(text):
    text=str(text or "")
    out={}
    patterns={
        "given_names":r"(?:Nombres|Given names)\s*:\s*(.+)",
        "surnames":r"(?:Apellidos|Surnames)\s*:\s*(.+)",
        "nationality":r"(?:Nacionalidad|Nationality)\s*:\s*(.+)",
        "passport_number":r"(?:Pasaporte|Passport)\s*:\s*(.+)",
        "airline":r"Aerolínea\s*:\s*(.+)",
        "flight_number":r"Número de vuelo\s*:\s*(.+)",
        "origin":r"Origen\s*:\s*(.+)",
        "destination":r"Destino\s*:\s*(.+)",
        "arrival_date":r"Fecha de entrada\s*:\s*(.+)",
        "departure_date":r"Fecha de salida\s*:\s*(.+)",
        "email":r"Correo electrónico\s*:\s*(.+)",
        "next_action":r"Próxima acción\s*:\s*(.+)"
    }
    for k,p in patterns.items():
        m=re.search(p,text,re.I)
        if m:out[k]=m.group(1).strip()
    return out

@app.post("/api/pdf/import")
async def pdf_import(data:PDFImportRequest):
    recovery=model_dict(data.recovery_data)
    if recovery:
        return {"status":"ok","recovered":True,"data":recovery,"next_action":"Revisa los datos recuperados antes de continuar."}
    recovered=extract_recovery(data.text)
    return {
        "status":"ok" if recovered else "verify",
        "recovered":bool(recovered),
        "data":recovered,
        "next_action":"Revisa los datos recuperados antes de continuar." if recovered else "No se encontraron datos recuperables."
    }

@app.post("/api/export")
async def export_trip(data:TripExportRequest):
    payload=model_dict(data.data)
    payload["updated_at"]=now()
    return {
        "status":"ok","data":payload,
        "next_action":"Guarda este contenido localmente si deseas conservar una copia de tu preparación."
    }

@app.post("/api/local-data")
async def local_data(data:DeleteLocalRequest):
    if data.confirm:
        return {
            "status":"ok",
            "message":"La aplicación no conserva tus datos personales en el servidor. Puedes borrar los datos del navegador desde 'Mis datos'.",
            "next_action":"Borra los datos locales desde la aplicación cuando quieras."
        }
    return {
        "status":"ok",
        "message":"No se realizó ninguna acción.",
        "next_action":"Usa 'Borrar datos' si deseas eliminar la información guardada en este dispositivo."
    }

@app.get("/api/legal")
async def legal():
    return {
        "status":"ok",
        "title":"Aviso legal",
        "message":"¿QUÉ QUIERES LLEVAR? es una herramienta independiente de preparación y orientación de May Roga LLC.",
        "points":[
            "No es una agencia de viajes.",
            "No es una aerolínea ni operador charter.",
            "No es gobierno, aduana, inmigración, consulado, aeropuerto, TSA, CBP, IATA, FAA o ICAO.",
            "No vende ni emite boletos.",
            "No realiza pagos oficiales.",
            "No presenta trámites oficiales en nombre del usuario.",
            "No garantiza aprobación de visa, entrada, embarque, equipaje o admisión de artículos.",
            "Las autoridades y proveedores oficiales toman las decisiones finales.",
            "El usuario debe verificar siempre la información vigente."
        ]
    }

@app.get("/api/ping")
async def ping():
    return {"status":"ok","version":VERSION,"time":now()}

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status":"error",
            "message":"Faltan o no son válidos algunos datos.",
            "next_action":"Revisa los campos e inténtalo nuevamente.",
            "details":exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_error(request:Request,exc:Exception):
    if os.getenv("DEBUG","").lower()=="true":
        detail=str(exc)
    else:
        detail="Error interno."
    return JSONResponse(
        status_code=500,
        content={
            "status":"error",
            "message":"La operación no pudo completarse.",
            "next_action":"Inténtalo nuevamente o utiliza la fuente oficial correspondiente.",
            "details":{"error":detail}
        }
    )

__all__=["app"]
