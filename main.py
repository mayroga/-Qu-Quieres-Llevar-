# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v14.0.0
from __future__ import annotations
import io,os,re
from pathlib import Path
from typing import Any,Dict
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from schemas import *
import cuba_engine as engine

VERSION="14.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"

app=FastAPI(title=APP_NAME,version=VERSION,docs_url="/docs",redoc_url="/redoc")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

def model_dict(x:Any)->Dict[str,Any]:
    if hasattr(x,"model_dump"):return x.model_dump(exclude_none=False)
    if hasattr(x,"dict"):return x.dict()
    return x if isinstance(x,dict) else {}

def registry():
    try:
        import source_registry as sr
        return sr
    except Exception:
        return None

def source_list(topic:str="official",query:str="",country:str="",airline:str="")->list:
    sr=registry()
    if not sr:return []
    try:return sr.get_sources(topic or "official",query,country,airline)
    except Exception:return []

def official_list(topic:str="",country:str="",airline:str="")->list:
    sr=registry()
    if not sr:return []
    try:return sr.official_sources(topic,country,airline)
    except Exception:return []

def airlines_list(query:str="")->list:
    sr=registry()
    if not sr:return []
    try:return sr.get_airlines(query)
    except Exception:return []

def charters_list(query:str="")->list:
    sr=registry()
    if not sr:return []
    try:return sr.get_charters(query)
    except Exception:return []

def normalize_result(result:Any)->Dict[str,Any]:
    d=model_dict(result)
    if "version" not in d:d["version"]=VERSION
    if "sources" not in d or not d.get("sources"):
        d["sources"]=official_list()
    return d

def engine_call(names:list,data:Dict[str,Any],*args)->Any:
    for name in names:
        fn=getattr(engine,name,None)
        if callable(fn):
            try:
                return fn(*args,data) if args else fn(data)
            except TypeError:
                try:return fn(data)
                except Exception:pass
            except Exception as e:
                raise HTTPException(status_code=500,detail=str(e))
    raise HTTPException(status_code=404,detail="Función no disponible.")

@app.get("/",response_class=FileResponse)
async def home():
    p=STATIC_DIR/"index.html"
    if not p.exists():raise HTTPException(status_code=404,detail="index.html no encontrado")
    return FileResponse(str(p))

@app.get("/health",response_model=HealthResponse)
async def health():
    return {
        "status":"ok","version":VERSION,"app":APP_NAME,"ready":True,
        "free":True,"login_required":False,"payment_required":False,
        "server_storage":False,
        "gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY"))
    }

@app.get("/api/config",response_model=ConfigResponse)
async def config():
    return {
        "status":"ok",
        "app":APP_NAME,
        "version":VERSION,
        "language":"es",
        "free":True,
        "login_required":False,
        "payment_required":False,
        "stripe_enabled":False,
        "server_storage":False,
        "features":{
            "flight":True,
            "booking_simulation":False,
            "baggage":True,
            "item_advisor":True,
            "gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY")),
            "cuba":True,
            "documents":True,
            "practice":True,
            "dviajeros":True,
            "visa":True,
            "sources":True,
            "airlines":True,
            "charters":True,
            "guide":True,
            "pdf":True,
            "pdf_import":True,
            "local_delete":True,
            "english":True
        },
        "official_sources":official_list()
    }

@app.post("/api/flight",response_model=FlightResponse)
async def flight(req:FlightRequest):
    return normalize_result(engine_call(["analyze_flight","flight_analysis"],model_dict(req)))

@app.post("/api/booking",response_model=BookingResponse)
async def booking(req:BookingRequest):
    d=model_dict(req)
    r=engine_call(["booking_simulation","booking_guide","booking_analysis"],d)
    return normalize_result(r)

@app.post("/api/connection",response_model=GenericResponse)
async def connection(req:ConnectionRequest):
    return normalize_result(engine_call(["connection_analysis"],model_dict(req)))

@app.post("/api/baggage",response_model=BaggageResponse)
async def baggage(req:BaggageRequest):
    return normalize_result(engine_call(["baggage_rules","baggage_analysis"],model_dict(req)))

@app.post("/api/item",response_model=ItemResponse)
async def item(req:ItemRequest):
    d=model_dict(req)
    r=engine_call(["item_analysis","analyze_item","item_advisor"],d)
    result=normalize_result(r)
    if not result.get("sources"):
        result["sources"]=official_list("item",d.get("destination",""),d.get("airline",""))
    return result

@app.post("/api/cuba",response_model=CubaResponse)
async def cuba(req:CubaRequest):
    return normalize_result(engine_call(["cuba_check","cuba_analysis"],model_dict(req)))

@app.post("/api/cuba/entry",response_model=CubaResponse)
async def cuba_entry(req:CubaEntryRequest):
    return normalize_result(engine_call(["cuba_entry_check","cuba_check","cuba_analysis"],model_dict(req)))

@app.post("/api/documents",response_model=DocumentResponse)
async def documents(req:DocumentRequest):
    return normalize_result(engine_call(["document_analysis","documents_analysis"],model_dict(req)))

@app.post("/api/practice",response_model=PracticeResponse)
async def practice(req:PracticeRequest):
    d=model_dict(req)
    state=dict(d.get("data") or {})
    state.update({k:v for k,v in d.items() if k!="data"})
    r=engine_call(["practice_scenario","practice"],state,d.get("scenario","airport"))
    return normalize_result(r)

@app.post("/api/dviajeros",response_model=SimulationResponse)
async def dviajeros(req:DViajeroRequest):
    d=model_dict(req)
    r=engine_call(["dviajeros_simulation","dviajeros_guide","dviajeros"],d)
    result=normalize_result(r)
    result["simulation"]=True
    result["official_submission"]=False
    result["notice"]="GUÍA DE PREPARACIÓN — EL ENVÍO REAL SE HACE ÚNICAMENTE EN EL SITIO OFICIAL."
    if not result.get("sources"):
        result["sources"]=official_list("dviajeros","CU")
    return result

@app.post("/api/visa",response_model=SimulationResponse)
async def visa(req:VisaRequest):
    d=model_dict(req)
    r=engine_call(["visa_simulation","visa_guide","visa"],d)
    result=normalize_result(r)
    result["simulation"]=True
    result["official_submission"]=False
    result["notice"]="GUÍA DE PREPARACIÓN — LA SOLICITUD REAL SE HACE ÚNICAMENTE EN EL SITIO OFICIAL."
    if not result.get("sources"):
        result["sources"]=official_list("visa","CU")
    return result

@app.get("/api/sources",response_model=SourceResponse)
async def sources_get(topic:str="official",query:str="",country:str="",airline:str=""):
    return {
        "status":"ok",
        "topic":topic,
        "sources":source_list(topic,query,country,airline),
        "next_action":"Abre el sitio oficial correspondiente para realizar o comprobar el proceso."
    }

@app.post("/api/sources",response_model=SourceResponse)
async def sources_post(req:SourceRequest):
    d=model_dict(req)
    topic=d.get("topic","official")
    return {
        "status":"ok",
        "topic":topic,
        "sources":source_list(topic,d.get("query",""),d.get("country",""),d.get("airline","")),
        "next_action":"Abre el sitio oficial correspondiente para realizar o comprobar el proceso."
    }

@app.get("/api/official")
async def official(topic:str="",country:str="",airline:str=""):
    return {
        "status":"ok",
        "sources":official_list(topic,country,airline)
    }

@app.get("/api/airlines")
async def airlines_get(query:str=""):
    return {
        "status":"ok",
        "airlines":airlines_list(query),
        "charters":charters_list(query)
    }

@app.post("/api/airlines",response_model=AirlineResponse)
async def airlines(req:AirlineRequest):
    d=model_dict(req)
    q=d.get("name") or d.get("airline") or ""
    return {
        "status":"ok",
        "airlines":airlines_list(q),
        "charters":charters_list(q),
        "next_action":"Selecciona el sitio oficial de la aerolínea u operador que corresponda a tu viaje."
    }

@app.get("/api/charters")
async def charters(query:str=""):
    return {
        "status":"ok",
        "charters":charters_list(query)
    }

@app.get("/api/cuba-official")
async def cuba_official():
    return {
        "status":"ok",
        "sources":{
            "dviajeros":official_list("dviajeros","CU"),
            "visa":official_list("visa","CU"),
            "customs":official_list("customs","CU"),
            "transport":official_list("transport","CU"),
            "travel":official_list("travel","CU")
        }
    }

@app.get("/api/airlines-cuba")
async def airlines_cuba():
    all_airlines=airlines_list()
    all_charters=charters_list()
    return {
        "status":"ok",
        "airlines":all_airlines,
        "charters":all_charters,
        "next_action":"Consulta siempre las condiciones directamente en el sitio oficial del operador."
    }

@app.post("/api/solve",response_model=GenericResponse)
async def solve(req:SolveRequest):
    d=model_dict(req)
    q=d.get("question","")
    data=d.get("data") or {}
    try:
        r=engine.solve(q,data)
    except Exception:
        try:r=engine.answer(q,data)
        except Exception:
            r={
                "status":"ok",
                "message":"Puedo ayudarte a revisar qué puedes llevar y dónde comprobarlo.",
                "next_action":"Indica el artículo y, si lo sabes, la aerolínea.",
                "sources":official_list("item")
            }
    result=normalize_result(r)
    if not result.get("sources"):
        result["sources"]=official_list("item",data.get("destination",""),data.get("airline",""))
    return result

@app.post("/api/guide",response_model=GuideResponse)
async def guide(req:GuideRequest):
    return normalize_result(engine_call(["build_guide","guide"],model_dict(req)))

def _safe(v:Any)->str:
    s=str(v if v is not None else "")
    s=re.sub(r"<[^>]+>","",s)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _pdf_lines(data:Dict[str,Any],lang:str="es")->list:
    labels={
        "es":{
            "title":"¿QUÉ QUIERES LLEVAR?",
            "subtitle":"Mi preparación de viaje",
            "notice":"DOCUMENTO DE PREPARACIÓN — NO ES UN DOCUMENTO OFICIAL.",
            "trip":"MI VIAJE",
            "flight":"MI VUELO",
            "identity":"MIS DATOS",
            "cuba":"MI PREPARACIÓN PARA CUBA",
            "baggage":"MI EQUIPAJE",
            "items":"LO QUE QUIERO LLEVAR",
            "pending":"LO QUE ME FALTA",
            "next":"MI SIGUIENTE PASO",
            "sources":"SITIOS OFICIALES"
        },
        "en":{
            "title":"WHAT DO YOU WANT TO BRING?",
            "subtitle":"My travel preparation",
            "notice":"PREPARATION DOCUMENT — NOT AN OFFICIAL DOCUMENT.",
            "trip":"MY TRIP",
            "flight":"MY FLIGHT",
            "identity":"MY INFORMATION",
            "cuba":"MY CUBA PREPARATION",
            "baggage":"MY BAGGAGE",
            "items":"WHAT I WANT TO BRING",
            "pending":"WHAT I STILL NEED",
            "next":"MY NEXT STEP",
            "sources":"OFFICIAL SITES"
        }
    }
    l=labels.get(lang,labels["es"])
    story=[
        Paragraph(_safe(l["title"]),ParagraphStyle("TitleQ",fontSize=20,leading=24,alignment=TA_CENTER)),
        Spacer(1,8),
        Paragraph(_safe(l["subtitle"]),ParagraphStyle("SubQ",fontSize=12,leading=16,alignment=TA_CENTER)),
        Spacer(1,10),
        Paragraph(_safe(l["notice"]),ParagraphStyle("NoticeQ",fontSize=9,leading=12,alignment=TA_CENTER)),
        Spacer(1,18)
    ]
    def section(title,rows):
        story.append(Paragraph(_safe(title),ParagraphStyle("H",fontSize=13,leading=16,spaceBefore=8,spaceAfter=6)))
        if rows:
            rows2=[]
            for a,b in rows:
                if b is None:b=""
                rows2.append([_safe(str(a)),_safe(str(b))])
            t=Table(rows2,colWidths=[155,350])
            t.setStyle(TableStyle([
                ("GRID",(0,0),(-1,-1),.3,colors.grey),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("FONTNAME",(0,0),(-1,-1),"Helvetica"),
                ("FONTSIZE",(0,0),(-1,-1),9),
                ("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),
                ("LEFTPADDING",(0,0),(-1,-1),6),
                ("RIGHTPADDING",(0,0),(-1,-1),6),
                ("TOPPADDING",(0,0),(-1,-1),5),
                ("BOTTOMPADDING",(0,0),(-1,-1),5)
            ]))
            story.append(t)

    section(l["trip"],[
        ("Origen",data.get("origin","")),
        ("Destino",data.get("destination","")),
        ("Fecha de salida",data.get("departure") or data.get("departure_date","")),
        ("Fecha de regreso",data.get("return_date","")),
        ("Pasajeros",data.get("passengers","")),
        ("Motivo",data.get("purpose",""))
    ])
    section(l["flight"],[
        ("Aerolínea",data.get("airline","")),
        ("Número de vuelo",data.get("flight_number","")),
        ("Tipo de vuelo",data.get("flight_type","")),
        ("Escalas",data.get("stops","")),
        ("Cabina",data.get("cabin","")),
        ("Tarifa",data.get("fare",""))
    ])
    section(l["identity"],[
        ("Nacionalidad",data.get("nationality","")),
        ("País del pasaporte",data.get("passport_country","")),
        ("País de residencia",data.get("country_of_residence","")),
        ("Vigencia del pasaporte",data.get("passport_valid_until","")),
        ("Nacionalidad cubana",data.get("cuban_nationality","")),
        ("Doble nacionalidad",data.get("dual_citizen",""))
    ])
    section(l["cuba"],[
        ("D’Viajeros",data.get("dviajeros_done","")),
        ("Visa / eVisa",data.get("visa_checked","")),
        ("Aduana",data.get("customs_checked","")),
        ("Documentos",data.get("documents_checked","")),
        ("Equipaje",data.get("baggage_checked","")),
        ("Llegada",data.get("arrival_date","")),
        ("Salida",data.get("departure_date",""))
    ])
    b=data.get("baggage") or {}
    if isinstance(b,dict):
        section(l["baggage"],[(str(k),v) for k,v in b.items()])
    items=data.get("items") or []
    if items:
        rows=[]
        for i,x in enumerate(items,1):
            if isinstance(x,dict):
                rows.append((f"Artículo {i}",", ".join(f"{k}: {v}" for k,v in x.items())))
            else:
                rows.append((f"Artículo {i}",x))
        section(l["items"],rows)
    pending=data.get("pending") or data.get("current_pending") or []
    if isinstance(pending,str):pending=[pending]
    section(l["pending"],[("Pendiente",x) for x in pending] or [("Estado","No hay pendientes registrados")])
    section(l["next"],[("Acción",data.get("next_action","Revisar el sitio oficial correspondiente antes de realizar el proceso."))])
    sources=data.get("sources") or official_list()
    if sources:
        rows=[]
        for x in sources[:30]:
            if isinstance(x,dict):
                rows.append((x.get("name","Sitio oficial"),x.get("url","")))
        section(l["sources"],rows)
    story.extend([
        Spacer(1,15),
        Paragraph("May Roga LLC — servicio independiente de preparación y orientación. No es gobierno, aerolínea, aeropuerto, aduana, inmigración, consulado ni agencia de viajes.",ParagraphStyle("Foot",fontSize=8,leading=11)),
        Paragraph("Las simulaciones y guías de esta aplicación sirven para preparar al viajero. Los procesos oficiales se realizan únicamente en los sitios de las autoridades, aerolíneas u operadores correspondientes.",ParagraphStyle("Foot2",fontSize=8,leading=11)),
        Paragraph("Los requisitos pueden cambiar. Verifica la información final antes de viajar.",ParagraphStyle("Foot3",fontSize=8,leading=11))
    ])
    return story

@app.post("/api/pdf")
async def pdf(req:PDFRequest):
    d=model_dict(req)
    data=d.get("data") or {}
    lang=d.get("lang") or "es"
    buf=io.BytesIO()
    doc=SimpleDocTemplate(
        buf,pagesize=LETTER,rightMargin=35,leftMargin=35,
        topMargin=35,bottomMargin=35,title=APP_NAME,
        author="May Roga LLC"
    )
    doc.build(_pdf_lines(data,lang))
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition":"attachment; filename=mi-guia-que-quieres-llevar.pdf"}
    )

@app.post("/api/pdf/import")
async def pdf_import(req:PDFImportRequest):
    d=model_dict(req)
    recovery=d.get("recovery_data") or {}
    if recovery:
        return {
            "status":"ok",
            "recovered":True,
            "data":recovery,
            "next_action":"Los datos fueron recuperados. Revisa y continúa."
        }
    text=d.get("text","")
    if not text:
        return {
            "status":"incomplete",
            "recovered":False,
            "data":{},
            "message":"No se recibieron datos de recuperación.",
            "next_action":"Selecciona un documento compatible con los datos guardados."
        }
    result={}
    patterns={
        "origin":r"Origen\s*[:\-]\s*(.+)",
        "destination":r"Destino\s*[:\-]\s*(.+)",
        "airline":r"Aerolínea\s*[:\-]\s*(.+)",
        "flight_number":r"Número de vuelo\s*[:\-]\s*(.+)",
        "departure_date":r"(?:Fecha de salida|Salida)\s*[:\-]\s*(.+)",
        "return_date":r"(?:Fecha de regreso|Regreso)\s*[:\-]\s*(.+)",
        "nationality":r"Nacionalidad\s*[:\-]\s*(.+)",
        "passport_country":r"País del pasaporte\s*[:\-]\s*(.+)",
        "country_of_residence":r"País de residencia\s*[:\-]\s*(.+)",
        "purpose":r"Motivo\s*[:\-]\s*(.+)",
        "arrival_date":r"Llegada\s*[:\-]\s*(.+)"
    }
    for k,p in patterns.items():
        m=re.search(p,text,re.I)
        if m:result[k]=m.group(1).strip()
    return {
        "status":"ok" if result else "incomplete",
        "recovered":bool(result),
        "data":result,
        "next_action":"Revisa los datos recuperados y continúa." if result else "No se encontraron datos recuperables."
    }

@app.post("/api/export")
async def export_trip(req:TripExportRequest):
    d=model_dict(req)
    return {
        "status":"ok",
        "format":"local-recovery-data",
        "server_storage":False,
        "data":d.get("data",{}),
        "next_action":"Conserva este archivo o PDF para continuar después."
    }

@app.delete("/api/local-data")
async def delete_local_data(req:DeleteLocalRequest):
    if not req.confirm:
        return {
            "status":"confirmation_required",
            "message":"Los datos locales se eliminan desde el navegador o dispositivo.",
            "server_storage":False
        }
    return {
        "status":"ok",
        "server_storage":False,
        "message":"El servidor no conserva los datos locales del cliente.",
        "next_action":"El almacenamiento local debe eliminarse desde el navegador o dispositivo."
    }

@app.get("/api/legal",response_model=LegalResponse)
async def legal():
    return {
        "status":"ok",
        "title":"Aviso legal",
        "message":"¿QUÉ QUIERES LLEVAR? es una herramienta independiente de preparación y orientación de May Roga LLC.",
        "points":[
            "No es gobierno ni una autoridad oficial.",
            "No es aerolínea, aeropuerto, aduana, inmigración ni consulado.",
            "No es agencia de viajes ni operador charter.",
            "No vende ni compra boletos de avión.",
            "No reserva vuelos en nombre del cliente.",
            "No procesa pagos de aerolíneas, visas ni autoridades.",
            "No presenta solicitudes oficiales por el cliente.",
            "D’Viajeros y Visa se presentan como procesos de preparación y práctica.",
            "El envío oficial se realiza únicamente en el sitio oficial correspondiente.",
            "La información sobre equipaje y artículos debe contrastarse con la aerolínea, autoridad o sitio oficial correspondiente.",
            "Las decisiones finales corresponden a las autoridades y proveedores oficiales.",
            "El cliente conserva el control de sus datos y de cualquier presentación oficial."
        ]
    }

@app.get("/api/ping")
async def ping():
    return {
        "status":"ok",
        "version":VERSION,
        "app":APP_NAME,
        "free":True,
        "login_required":False,
        "payment_required":False
    }

@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status":"error",
            "message":"Ocurrió un error interno al procesar la solicitud.",
            "details":{"type":exc.__class__.__name__}
        }
    )
