from __future__ import annotations
import os,json,re,io,datetime
from typing import Any,Dict
from fastapi import FastAPI,Request
from fastapi.responses import HTMLResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph,Spacer,SimpleDocTemplate,Table,TableStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
import cuba_engine as engine
from schemas import *
from source_registry import VERSION as SOURCE_VERSION,SOURCES,all_sources,source_by_id,get_sources,official_sources,get_airlines,get_charters,official_url,answer_sources

VERSION="16.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
STATIC_DIR="static"
app=FastAPI(title=APP_NAME,version=VERSION)
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")

def now():return datetime.datetime.now().isoformat(timespec="seconds")
def model_dict(x):
    if x is None:return {}
    if isinstance(x,dict):return x
    if hasattr(x,"model_dump"):return x.model_dump(exclude_none=False)
    if hasattr(x,"dict"):return x.dict()
    return dict(x)
def normalize_result(result,default_sources=None):
    if result is None:result={}
    if hasattr(result,"model_dump"):result=result.model_dump()
    elif not isinstance(result,dict):result={"message":str(result)}
    result=dict(result)
    if not isinstance(result.get("sources"),list):result["sources"]=default_sources or []
    return result
def call_engine(name,data=None):
    fn=getattr(engine,name,None)
    if not fn:return {"status":"error","message":f"Función no disponible: {name}","next_action":"Revisa la aplicación."}
    d=model_dict(data)
    try:return normalize_result(fn(d))
    except TypeError:
        try:return normalize_result(fn(**d))
        except Exception as e:return {"status":"error","message":str(e),"next_action":"Inténtalo nuevamente."}
    except Exception as e:return {"status":"error","message":str(e),"next_action":"Inténtalo nuevamente."}

@app.get("/",response_class=HTMLResponse)
async def home():
    path=os.path.join(STATIC_DIR,"index.html")
    try:
        with open(path,"r",encoding="utf-8") as f:return HTMLResponse(f.read())
    except Exception:return HTMLResponse("<h1>¿QUÉ QUIERES LLEVAR?</h1><p>No se pudo cargar la aplicación.</p>",status_code=500)

@app.get("/health")
async def health():
    return {"status":"ok","version":VERSION,"source_version":SOURCE_VERSION,"app":APP_NAME,"ready":True,"gemini_item_assistant":bool(os.getenv("GEMINI_API_KEY","").strip())}

@app.get("/api/config")
async def config():
    return {"status":"ok","app":APP_NAME,"version":VERSION,"language":"es","free":True,"login_required":False,"payment_required":False,"server_storage":False,"features":{"dviajeros":True,"visa":True,"flights":True,"airlines":True,"charters":True,"pdf":True,"official_sources":True},"official_sources":official_sources()}

@app.post("/api/flight")
async def flight(data:FlightRequest):return call_engine("analyze_flight",data)
@app.post("/api/booking")
async def booking(data:BookingRequest):return call_engine("booking_simulation",data)
@app.post("/api/connection")
async def connection(data:ConnectionRequest):return call_engine("connection_analysis",data)
@app.post("/api/baggage")
async def baggage(data:BaggageRequest):return call_engine("baggage_rules",data)
@app.post("/api/item")
async def item(data:ItemRequest):return call_engine("item_analysis",data)
@app.post("/api/cuba")
async def cuba(data:CubaRequest):return call_engine("cuba_check",data)
@app.post("/api/cuba/entry")
async def cuba_entry(data:CubaEntryRequest):return call_engine("cuba_entry",data)
@app.post("/api/documents")
async def documents(data:DocumentRequest):return call_engine("document_analysis",data)
@app.post("/api/practice")
async def practice(data:PracticeRequest):return call_engine("practice_scenario",data)
@app.post("/api/dviajeros")
async def dviajeros(data:DViajeroRequest):return call_engine("dviajeros_simulation",data)
@app.post("/api/visa")
async def visa(data:VisaRequest):return call_engine("visa_simulation",data)

@app.get("/api/sources")
async def sources_get(topic:str="official",query:str="",country:str="",airline:str=""):
    return {"status":"ok","topic":topic,"sources":get_sources(topic,query,country,airline)}
@app.post("/api/sources")
async def sources_post(data:SourceRequest):
    return {"status":"ok","topic":data.topic,"sources":get_sources(data.topic,data.query,data.country,data.airline)}
@app.get("/api/official")
async def official(topic:str="",country:str="",airline:str=""):
    return {"status":"ok","topic":topic,"sources":official_sources(topic,country,airline)}

@app.get("/api/airlines")
async def airlines_get(query:str=""):
    return {"status":"ok","airlines":get_airlines(query),"charters":get_charters(query)}
@app.post("/api/airlines")
async def airlines_post(data:AirlineRequest):
    q=getattr(data,"query","") or getattr(data,"name","") or getattr(data,"airline","")
    return {"status":"ok","airlines":get_airlines(q),"charters":get_charters(q)}
@app.get("/api/charters")
async def charters(query:str=""):
    return {"status":"ok","charters":get_charters(query)}
@app.get("/api/cuba-official")
async def cuba_official():return {"status":"ok","sources":official_sources("cuba")}
@app.get("/api/airlines-cuba")
async def airlines_cuba():return {"status":"ok","airlines":get_airlines(),"charters":get_charters()}

@app.post("/api/solve")
async def solve(data:SolveRequest):return call_engine("solve",data)
@app.post("/api/guide")
async def guide(data:GuideRequest):return call_engine("build_guide",data)

STYLES=getSampleStyleSheet()
STYLE=STYLES["BodyText"]
TITLE=STYLES["Title"]
TITLE.alignment=TA_CENTER

def add_line(story,label,value):
    if value in ("",None,False,[],{}):return
    if isinstance(value,(dict,list)):value=json.dumps(value,ensure_ascii=False)
    story.extend([Paragraph(f"<b>{label}:</b> {value}",STYLE),Spacer(1,4)])

def make_pdf(data,lang="es",title=None):
    b=io.BytesIO()
    doc=SimpleDocTemplate(b,pagesize=letter,rightMargin=.55*inch,leftMargin=.55*inch,topMargin=.55*inch,bottomMargin=.55*inch)
    story=[Paragraph(title or APP_NAME,TITLE),Spacer(1,8),Paragraph("Guía independiente de preparación. No es un documento oficial ni sustituye las instrucciones de las autoridades.",STYLE),Spacer(1,10)]
    story.append(Paragraph("D’VIAJEROS",STYLES["Heading2"]))
    dv=[
        ("1. Entrar al sitio oficial","Abre D’Viajeros y comienza el formulario."),
        ("2. Datos del viajero","Completa los datos que solicita el formulario."),
        ("3. Pasaporte","Escribe los datos exactamente como aparecen en el documento."),
        ("4. Viaje","Completa la información solicitada sobre tu entrada y estancia."),
        ("5. Revisar","Comprueba los datos antes de terminar."),
        ("6. Resultado","Conserva el resultado y el QR que entregue el sistema.")
    ]
    for a,c in dv:add_line(story,a,c)
    story.append(Spacer(1,7));story.append(Paragraph("VISA PARA CUBA",STYLES["Heading2"]))
    visa=[
        ("Visa electrónica","Consulta el portal oficial, completa la solicitud, realiza el proceso indicado y conserva el resultado recibido."),
        ("Trámite consular","Si tu caso corresponde al consulado/embajada, consulta directamente los requisitos, costo, forma de pago y tiempo vigente."),
        ("Aeropuerto","Si tu caso permite obtenerla en el aeropuerto, consulta antes del viaje el proceso vigente, el lugar y el costo correspondiente.")
    ]
    for a,c in visa:add_line(story,a,c)
    story.append(Spacer(1,7));story.append(Paragraph("ENLACES OFICIALES",STYLES["Heading2"]))
    for s in official_sources("cuba"):
        if isinstance(s,dict):
            u=s.get("exact_url") or s.get("deep_url") or s.get("section_url") or s.get("url")
            if u:add_line(story,s.get("title") or s.get("name") or "Fuente oficial",u)
    story.extend([Spacer(1,12),Paragraph(f"Generado: {now()} — {APP_NAME} | May Roga LLC",STYLE)])
    doc.build(story);b.seek(0);return b

@app.post("/api/pdf")
async def pdf(data:PDFRequest):
    b=make_pdf(model_dict(data.data),data.lang,data.title)
    return StreamingResponse(b,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=mi-guia-que-quieres-llevar.pdf"})

@app.post("/api/pdf/import")
async def pdf_import(data:PDFImportRequest):
    return {"status":"verify","recovered":False,"data":{},"next_action":"Esta versión utiliza el PDF como guía de pasos. Revisa siempre el sitio oficial."}

@app.post("/api/export")
async def export_trip(data:TripExportRequest):
    return {"status":"ok","data":model_dict(data.data),"next_action":"Puedes conservar esta información localmente."}

@app.post("/api/local-data")
async def local_data(data:DeleteLocalRequest):
    return {"status":"ok","message":"La aplicación no necesita conservar tus datos personales en el servidor."}

@app.get("/api/legal")
async def legal():
    return {"status":"ok","title":"Aviso legal","message":"¿QUÉ QUIERES LLEVAR? es una herramienta independiente de orientación y preparación de May Roga LLC.","points":["No es una agencia de viajes.","No es una aerolínea ni operador charter.","No realiza trámites oficiales en nombre del viajero.","No vende ni emite boletos.","No sustituye a las autoridades ni a los proveedores oficiales.","La información puede cambiar y debe comprobarse en la fuente oficial."]}

@app.get("/api/ping")
async def ping():return {"status":"ok","version":VERSION,"time":now()}

@app.exception_handler(RequestValidationError)
async def validation_error(request:Request,exc:RequestValidationError):
    return JSONResponse(status_code=422,content={"status":"error","message":"Faltan o no son válidos algunos datos.","next_action":"Revisa los datos e inténtalo nuevamente.","details":exc.errors()})

@app.exception_handler(Exception)
async def global_error(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"status":"error","message":"La operación no pudo completarse.","next_action":"Inténtalo nuevamente."})

__all__=["app"]
