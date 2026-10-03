# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v13.0.0
from __future__ import annotations
import io,json,os,re
from pathlib import Path
from typing import Any,Dict
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from schemas import *
import cuba_engine as engine

VERSION="13.0.0"
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
    if isinstance(x,dict):return x
    return {}

def source_list(topic:str="",query:str="",country:str="",airline:str="")->list:
    try:
        import source_registry as sr
        return sr.get_sources(topic or "official",query,country,airline)
    except Exception:
        return []

def call_engine(names:list,data:Dict[str,Any],*args)->Any:
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

def normalize_result(result:Any)->Dict[str,Any]:
    d=model_dict(result)
    if "version" not in d:d["version"]=VERSION
    if "sources" not in d or not d.get("sources"):
        d["sources"]=source_list("official")
    return d

@app.get("/",response_class=FileResponse)
async def home():
    p=STATIC_DIR/"index.html"
    if not p.exists():raise HTTPException(status_code=404,detail="index.html no encontrado")
    return FileResponse(str(p))

@app.get("/health",response_model=HealthResponse)
async def health():
    return {"status":"ok","version":VERSION,"app":APP_NAME,"ready":True,"free":True,"login_required":False,"payment_required":False,"server_storage":False,"gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY"))}

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
            "booking_simulation":True,
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
        "official_sources":source_list("official")
    }

@app.post("/api/flight",response_model=FlightResponse)
async def flight(req:FlightRequest):
    return normalize_result(engine.analyze_flight(model_dict(req)))

@app.post("/api/booking",response_model=BookingResponse)
async def booking(req:BookingRequest):
    return normalize_result(engine.booking_simulation(model_dict(req)))

@app.post("/api/connection",response_model=GenericResponse)
async def connection(req:ConnectionRequest):
    return normalize_result(engine.connection_analysis(model_dict(req)))

@app.post("/api/baggage",response_model=BaggageResponse)
async def baggage(req:BaggageRequest):
    return normalize_result(engine.baggage_rules(model_dict(req)))

@app.post("/api/item",response_model=ItemResponse)
async def item(req:ItemRequest):
    return normalize_result(engine.item_analysis(model_dict(req)))

@app.post("/api/cuba",response_model=CubaResponse)
async def cuba(req:CubaRequest):
    return normalize_result(engine.cuba_check(model_dict(req)))

@app.post("/api/cuba/entry",response_model=CubaResponse)
async def cuba_entry(req:CubaEntryRequest):
    return normalize_result(engine.cuba_check(model_dict(req)))

@app.post("/api/documents",response_model=DocumentResponse)
async def documents(req:DocumentRequest):
    return normalize_result(engine.document_analysis(model_dict(req)))

@app.post("/api/practice",response_model=PracticeResponse)
async def practice(req:PracticeRequest):
    d=model_dict(req)
    state=dict(d.get("data") or {})
    state.update({k:v for k,v in d.items() if k not in ("data",)})
    return normalize_result(engine.practice_scenario(d.get("scenario","airport"),state))

@app.post("/api/dviajeros",response_model=SimulationResponse)
async def dviajeros(req:DViajeroRequest):
    return normalize_result(engine.dviajeros_simulation(model_dict(req)))

@app.post("/api/visa",response_model=SimulationResponse)
async def visa(req:VisaRequest):
    return normalize_result(engine.visa_simulation(model_dict(req)))

@app.get("/api/sources",response_model=SourceResponse)
async def sources_get(topic:str="official",query:str="",country:str="",airline:str=""):
    return {"status":"ok","topic":topic,"sources":source_list(topic,query,country,airline),"next_action":"Abre la fuente oficial correspondiente y verifica la información actual."}

@app.post("/api/sources",response_model=SourceResponse)
async def sources_post(req:SourceRequest):
    d=model_dict(req)
    return {"status":"ok","topic":d.get("topic","official"),"sources":source_list(d.get("topic","official"),d.get("query",""),d.get("country",""),d.get("airline","")),"next_action":"Abre la fuente oficial correspondiente y verifica la información actual."}

@app.post("/api/airlines",response_model=AirlineResponse)
async def airlines(req:AirlineRequest):
    q=model_dict(req).get("name") or model_dict(req).get("airline") or ""
    try:
        import source_registry as sr
        al=sr.get_airlines(q)
        ch=sr.get_charters(q)
    except Exception:
        al=[]
        ch=[]
    return {"status":"ok","airlines":al,"charters":ch,"next_action":"Selecciona la aerolínea u operador y abre su sitio oficial antes de realizar una operación real."}

@app.get("/api/charters")
async def charters(query:str=""):
    try:
        import source_registry as sr
        return {"status":"ok","charters":sr.get_charters(query)}
    except Exception:
        return {"status":"ok","charters":[]}

@app.get("/api/airlines")
async def airlines_get(query:str=""):
    try:
        import source_registry as sr
        return {"status":"ok","airlines":sr.get_airlines(query),"charters":sr.get_charters(query)}
    except Exception:
        return {"status":"ok","airlines":[],"charters":[]}

@app.post("/api/solve",response_model=GenericResponse)
async def solve(req:SolveRequest):
    d=model_dict(req)
    q=d.get("question","")
    data=d.get("data") or {}
    try:
        r=engine.solve(q,data)
    except Exception:
        r=engine.answer(q,data)
    return normalize_result(r)

@app.post("/api/guide",response_model=GuideResponse)
async def guide(req:GuideRequest):
    return normalize_result(engine.build_guide(model_dict(req)))

def _safe(v:Any)->str:
    s=str(v if v is not None else "")
    s=re.sub(r"<[^>]+>","",s)
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _pdf_lines(data:Dict[str,Any],lang:str="es")->list:
    labels={
        "es":{
            "title":"¿QUÉ QUIERES LLEVAR?",
            "subtitle":"Guía personal de preparación",
            "notice":"DOCUMENTO DE PREPARACIÓN — NO ES UN DOCUMENTO OFICIAL.",
            "trip":"Mi viaje",
            "flight":"Mi vuelo",
            "identity":"Identidad y documentos",
            "cuba":"Cuba",
            "baggage":"Equipaje",
            "items":"Artículos",
            "pending":"Pendientes",
            "next":"Siguiente acción",
            "sources":"Fuentes"
        },
        "en":{
            "title":"WHAT DO YOU WANT TO BRING?",
            "subtitle":"Personal preparation guide",
            "notice":"PREPARATION DOCUMENT — NOT AN OFFICIAL DOCUMENT.",
            "trip":"My trip",
            "flight":"My flight",
            "identity":"Identity and documents",
            "cuba":"Cuba",
            "baggage":"Baggage",
            "items":"Items",
            "pending":"Pending",
            "next":"Next action",
            "sources":"Sources"
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
            t=Table([[ _safe(str(a)),_safe(str(b))] for a,b in rows],colWidths=[155,350])
            t.setStyle(TableStyle([("GRID",(0,0),(-1,-1),.3,colors.grey),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTNAME",(0,0),(-1,-1),"Helvetica"),("FONTSIZE",(0,0),(-1,-1),9),("BACKGROUND",(0,0),(0,-1),colors.whitesmoke),("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
            story.append(t)
    section(l["trip"],[
        ("Origen",data.get("origin","")),
        ("Destino",data.get("destination","")),
        ("Aerolínea",data.get("airline","")),
        ("Número de vuelo",data.get("flight_number","")),
        ("Salida",data.get("departure") or data.get("departure_date","")),
        ("Regreso",data.get("return_date","")),
        ("Pasajeros",data.get("passengers",""))
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
        ("Motivo",data.get("purpose","")),
        ("Llegada",data.get("arrival_date","")),
        ("Salida",data.get("departure_date","")),
        ("D’Viajeros",data.get("dviajeros_done","")),
        ("Visa/eVisa",data.get("visa_checked","")),
        ("Aduana",data.get("customs_checked","")),
        ("Documentos",data.get("documents_checked",""))
    ])
    b=data.get("baggage") or {}
    section(l["baggage"],[(str(k),v) for k,v in b.items()])
    items=data.get("items") or []
    if items:
        rows=[]
        for i,x in enumerate(items,1):
            if isinstance(x,dict):
                rows.append((f"Artículo {i}",", ".join(f"{k}: {v}" for k,v in x.items())))
            else:rows.append((f"Artículo {i}",x))
        section(l["items"],rows)
    pending=data.get("pending") or data.get("current_pending") or []
    if isinstance(pending,str):pending=[pending]
    section(l["pending"],[("Pendiente",x) for x in pending] or [("Estado","No hay pendientes registrados")])
    section(l["next"],[("Acción",data.get("next_action","Revisar fuentes oficiales antes del viaje."))])
    try:
        import source_registry as sr
        sources=sr.official_sources()
    except Exception:
        sources=[]
    if sources:
        rows=[(x.get("name",""),x.get("url","")) for x in sources[:20]]
        section(l["sources"],rows)
    story.extend([
        Spacer(1,15),
        Paragraph("May Roga LLC — servicio independiente de preparación y orientación. No es gobierno, aerolínea, aeropuerto, aduana, inmigración, consulado ni agencia de viajes.",ParagraphStyle("Foot",fontSize=8,leading=11)),
        Paragraph("Los requisitos pueden cambiar. Verifica siempre la información final con las autoridades, aerolínea u operador oficial correspondiente.",ParagraphStyle("Foot2",fontSize=8,leading=11))
    ])
    return story

@app.post("/api/pdf")
async def pdf(req:PDFRequest):
    d=model_dict(req)
    data=d.get("data") or {}
    lang=d.get("lang") or "es"
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=LETTER,rightMargin=35,leftMargin=35,topMargin=35,bottomMargin=35,title=APP_NAME,author="May Roga LLC")
    doc.build(_pdf_lines(data,lang))
    buf.seek(0)
    return StreamingResponse(buf,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=mi-guia-que-quieres-llevar.pdf"})

@app.post("/api/pdf/import")
async def pdf_import(req:PDFImportRequest):
    d=model_dict(req)
    recovery=d.get("recovery_data") or {}
    if recovery:
        return {"status":"ok","recovered":True,"data":recovery,"next_action":"Continúa con tu preparación."}
    text=d.get("text","")
    if not text:
        return {"status":"incomplete","recovered":False,"data":{},"message":"Este endpoint necesita los datos recuperados del documento para reconstruir la preparación.","next_action":"Selecciona un archivo compatible con datos de recuperación."}
    result={}
    patterns={
        "origin":r"Origen\s*[:\-]\s*(.+)",
        "destination":r"Destino\s*[:\-]\s*(.+)",
        "airline":r"Aerolínea\s*[:\-]\s*(.+)",
        "flight_number":r"Número de vuelo\s*[:\-]\s*(.+)",
        "nationality":r"Nacionalidad\s*[:\-]\s*(.+)",
        "passport_country":r"País del pasaporte\s*[:\-]\s*(.+)",
        "country_of_residence":r"País de residencia\s*[:\-]\s*(.+)",
        "purpose":r"Motivo\s*[:\-]\s*(.+)",
        "arrival_date":r"Llegada\s*[:\-]\s*(.+)",
        "departure_date":r"Salida\s*[:\-]\s*(.+)"
    }
    for k,p in patterns.items():
        m=re.search(p,text,re.I)
        if m:result[k]=m.group(1).strip()
    return {"status":"ok" if result else "incomplete","recovered":bool(result),"data":result,"next_action":"Revisa los datos recuperados y continúa con la práctica." if result else "No se encontraron datos recuperables."}

@app.post("/api/export")
async def export_trip(req:TripExportRequest):
    d=model_dict(req)
    return {"status":"ok","format":"local-recovery-data","server_storage":False,"data":d.get("data",{}),"next_action":"Puedes conservar estos datos localmente para continuar después."}

@app.delete("/api/local-data")
async def delete_local_data(req:DeleteLocalRequest):
    if not req.confirm:
        return {"status":"confirmation_required","message":"La aplicación no puede borrar el almacenamiento del navegador desde el servidor. Confirma y utiliza el botón de borrar datos de la aplicación.","server_storage":False}
    return {"status":"ok","server_storage":False,"message":"El servidor no conserva los datos locales del cliente.","next_action":"El almacenamiento local debe eliminarse desde el navegador/dispositivo."}

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
            "No reserva ni compra vuelos.",
            "No procesa pagos.",
            "No presenta solicitudes oficiales.",
            "Las prácticas de visa y D’Viajeros son simulaciones.",
            "Las decisiones finales corresponden a las autoridades y proveedores oficiales.",
            "El usuario debe verificar la información vigente antes de viajar."
        ]
    }

@app.get("/api/ping")
async def ping():
    return {"status":"ok","version":VERSION,"app":APP_NAME,"free":True,"login_required":False,"payment_required":False}

@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"status":"error","message":"Ocurrió un error interno al procesar la solicitud.","details":{"type":exc.__class__.__name__}})
