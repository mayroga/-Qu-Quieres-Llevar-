# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v14.0.0
from __future__ import annotations
import io,os,re,json,time,traceback
from pathlib import Path
from typing import Any,Dict,Optional
from fastapi import FastAPI,HTTPException,Request,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles

try:
    from schemas import *
except Exception:
    from schemas import TripState

try:
    import cuba_engine as engine
except Exception:
    engine=None

try:
    import source_registry as registry
except Exception:
    registry=None

try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    PDF_OK=True
except Exception:
    PDF_OK=False

BASE=Path(__file__).resolve().parent
STATIC=BASE/"static"
APP_VERSION="14.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
SIM_NOTICE="SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL."
NO_BOOKING="May Roga LLC no compra vuelos, no reserva vuelos y no envía formularios oficiales."

app=FastAPI(title=APP_NAME,version=APP_VERSION)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
if STATIC.exists(): app.mount("/static",StaticFiles(directory=str(STATIC)),name="static")

def model_dict(x:Any)->Dict[str,Any]:
    if x is None:return {}
    if isinstance(x,dict):return x
    if hasattr(x,"model_dump"):
        try:return x.model_dump(exclude_none=True)
        except Exception:pass
    if hasattr(x,"dict"):
        try:return x.dict(exclude_none=True)
        except Exception:pass
    try:return dict(x)
    except Exception:return {}

def clean(v:Any)->Any:
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,list):return [clean(x) for x in v]
    if isinstance(v,tuple):return [clean(x) for x in v]
    return v

def call_engine(name:str,data:Dict[str,Any])->Dict[str,Any]:
    if engine is None:return {"ok":False,"message":"No se pudo cargar el motor.","next_action":"Intenta nuevamente."}
    fn=getattr(engine,name,None)
    if fn is None:return {"ok":False,"message":"Esta función no está disponible.","next_action":"Regresa al menú principal."}
    try:
        r=fn(data)
        r=clean(r)
        if isinstance(r,dict):r.setdefault("ok",True);return r
        return {"ok":True,"result":r}
    except Exception:
        return {"ok":False,"message":"No pudimos completar este paso todavía.","next_action":"Revisa los datos e inténtalo nuevamente."}

def source_list(kind:Optional[str]=None)->list:
    if registry is None:return []
    try:
        if kind and hasattr(registry,"sources_for"):r=registry.sources_for(kind)
        elif hasattr(registry,"all_sources"):r=registry.all_sources()
        else:r=getattr(registry,"SOURCES",[])
        return [clean(x) for x in r]
    except Exception:return []

def official_sources(kind:Optional[str]=None)->list:
    if registry is None:return []
    try:
        fn=getattr(registry,"get_official_sources",None)
        if fn:
            r=fn(kind) if kind else fn()
            return [clean(x) for x in r]
    except Exception:pass
    return source_list(kind)

def normalize(r:Any)->Dict[str,Any]:
    if not isinstance(r,dict):r={"result":r}
    r=clean(r)
    r.setdefault("ok",True)
    r.setdefault("version",APP_VERSION)
    r.setdefault("app_name",APP_NAME)
    r.setdefault("simulation_notice",SIM_NOTICE)
    r.setdefault("no_booking",NO_BOOKING)
    return r

def trip_from(data:Dict[str,Any])->Dict[str,Any]:
    t=data.get("trip")
    if isinstance(t,dict):return clean(t)
    return clean(data)

def pdf_text(data:Dict[str,Any],title:str)->list:
    t=trip_from(data)
    lines=[title,APP_NAME,"May Roga LLC","",f"Fecha: {time.strftime('%Y-%m-%d %H:%M')}",""]
    def add(label,key):
        v=t.get(key)
        if v not in (None,"",[],{}):lines.append(f"{label}: {v}")
    add("Origen","origin")
    add("Destino","destination")
    add("Fecha de salida","departure_date")
    add("Fecha de regreso","return_date")
    add("Viajeros","passengers")
    add("Aerolínea","airline")
    add("Número de vuelo","flight_number")
    add("Tipo de vuelo","flight_type")
    add("Escalas","stops")
    add("Clase","cabin")
    add("Tarifa","fare")
    ident=t.get("identity") or {}
    for k,l in [("nationality","Nacionalidad"),("passport_country","País del pasaporte"),("residence","Residencia"),("passport_number","Pasaporte"),("given_name","Nombre"),("surname","Apellido"),("date_of_birth","Fecha de nacimiento")]:
        v=ident.get(k)
        if v not in (None,""):lines.append(f"{l}: {v}")
    cuba=t.get("cuba") or {}
    for k,l in [("cuban_nationality","Nacionalidad cubana"),("dual_nationality","Doble nacionalidad"),("passport_valid","Pasaporte vigente"),("purpose","Propósito"),("arrival_date","Entrada"),("departure_date","Salida")]:
        v=cuba.get(k)
        if v not in (None,""):lines.append(f"{l}: {v}")
    b=t.get("baggage") or {}
    if b:
        lines+=["","EQUIPAJE"]
        for k,v in b.items():
            if v not in (None,"",[],{}):lines.append(f"{k}: {v}")
    items=t.get("items") or []
    if items:
        lines+=["","ARTÍCULOS"]
        for x in items:
            lines.append(str(x))
    nxt=t.get("next_action") or data.get("next_action")
    if nxt:lines+=["","SIGUIENTE ACCIÓN",str(nxt)]
    lines+=["","Este documento es un resumen de preparación.","No sustituye decisiones ni formularios oficiales.","Verifica siempre el resultado final en el sitio oficial correspondiente."]
    return lines

def make_pdf(data:Dict[str,Any],title:str)->bytes:
    if not PDF_OK:raise RuntimeError("PDF no disponible")
    buf=io.BytesIO()
    c=canvas.Canvas(buf,pagesize=LETTER)
    w,h=LETTER
    y=h-0.65*inch
    c.setFont("Helvetica-Bold",14)
    c.drawString(0.6*inch,y,title)
    y-=0.3*inch
    c.setFont("Helvetica",9)
    for line in pdf_text(data,title):
        if y<0.65*inch:
            c.showPage();y=h-0.65*inch;c.setFont("Helvetica",9)
        text=str(line).replace("\n"," ")[:150]
        c.drawString(0.6*inch,y,text)
        y-=0.18*inch
    c.save()
    return buf.getvalue()

def safe_filename(v:str)->str:
    v=re.sub(r"[^A-Za-z0-9_-]+","_",v or "resumen").strip("_")
    return (v[:70] or "resumen")+".pdf"

@app.get("/")
async def home():
    p=STATIC/"index.html"
    if not p.exists():raise HTTPException(404,"Aplicación no disponible")
    return FileResponse(str(p))

@app.get("/health")
async def health():
    return {"ok":True,"status":"online","version":APP_VERSION,"app":APP_NAME}

@app.get("/api/config")
async def config():
    return {
        "ok":True,"version":APP_VERSION,"app_name":APP_NAME,
        "features":{
            "flight":True,"flight_guided_steps":True,"existing_flight":True,
            "booking_simulation":True,"baggage":True,"item_advisor":True,
            "documents":True,"cuba":True,"dviajeros":True,"visa":True,
            "practice":True,"sources":True,"airlines":True,"charters":True,
            "guide":True,"pdf":True,"individual_pdfs":True,
            "pdf_import":True,"local_recovery":True,"english":True
        },
        "principles":{
            "official_submission":False,"flight_purchase":False,
            "flight_booking":False,"visa_submission":False,
            "dviajeros_submission":False,
            "official_sources_only":True,
            "user_controls_final_action":True
        },
        "notice":SIM_NOTICE,
        "no_booking":NO_BOOKING
    }

@app.post("/api/flight")
async def flight(req:FlightRequest):
    d=model_dict(req)
    r=call_engine("analyze_flight",d)
    r["guided_flow"]=[
        {"step":1,"id":"origin","title":"¿De dónde sales?","required":True},
        {"step":2,"id":"destination","title":"¿A dónde vas?","required":True},
        {"step":3,"id":"dates","title":"¿Cuándo viajas?","required":True},
        {"step":4,"id":"passengers","title":"¿Cuántas personas viajan?","required":True},
        {"step":5,"id":"flight_type","title":"¿Quieres vuelo directo o con conexiones?","required":True},
        {"step":6,"id":"result","title":"Tu preparación está lista","required":False}
    ]
    r["official_next_action"]="Continúa en el sitio oficial de la aerolínea."
    return normalize(r)

@app.post("/api/booking")
async def booking(req:BookingRequest):
    return normalize(call_engine("booking_simulation",model_dict(req)))

@app.post("/api/connection")
async def connection(req:ConnectionRequest):
    return normalize(call_engine("connection_analysis",model_dict(req)))

@app.post("/api/baggage")
async def baggage(req:BaggageRequest):
    return normalize(call_engine("baggage_rules",model_dict(req)))

@app.post("/api/item")
async def item(req:ItemRequest):
    return normalize(call_engine("item_analysis",model_dict(req)))

@app.post("/api/cuba")
async def cuba(req:CubaRequest):
    return normalize(call_engine("cuba_check",model_dict(req)))

@app.post("/api/cuba/entry")
async def cuba_entry(req:CubaEntryRequest):
    d=model_dict(req)
    fn=getattr(engine,"cuba_profile",None) if engine else None
    if not fn:return normalize({"ok":False,"message":"No se pudo preparar este paso."})
    return normalize(fn(d))

@app.post("/api/documents")
async def documents(req:DocumentRequest):
    return normalize(call_engine("document_analysis",model_dict(req)))

@app.post("/api/practice")
async def practice(req:PracticeRequest):
    return normalize(call_engine("practice_scenario",model_dict(req)))

@app.post("/api/dviajeros")
async def dviajeros(req:DViajeroRequest):
    d=model_dict(req)
    r=call_engine("dviajeros_simulation",d)
    r["required_flow"]=[
        {"step":1,"id":"new_application","title":"Crear nueva aplicación","fields":["language","create_form"]},
        {"step":2,"id":"personal_visa","title":"Datos personales y visa","fields":["given_name","surname","passport_number","purpose","evisa_number"]},
        {"step":3,"id":"flight","title":"Información del vuelo","fields":["origin_country","airline","flight_number","entry_date"]},
        {"step":4,"id":"accommodation","title":"Alojamiento","fields":["accommodation_type","province","municipality","hotel_or_address"]},
        {"step":5,"id":"customs_health","title":"Aduana y salud","fields":["medication","cash_over_5000","health_control"]},
        {"step":6,"id":"final","title":"Final y código QR","fields":["submit","qr","official_pdf"]}
    ]
    r["official_submission"]=False
    r["official_next_action"]="Cuando termines la práctica, abre D’Viajeros oficial y completa allí el formulario real."
    return normalize(r)

@app.post("/api/visa")
async def visa(req:VisaRequest):
    d=model_dict(req)
    r=call_engine("visa_simulation",d)
    r["required_flow"]=[
        {"step":1,"id":"passport_data","title":"Datos del pasaporte","fields":["nationality","given_name","surname","passport_number","date_of_birth"]},
        {"step":2,"id":"purpose_payment","title":"Propósito y pago","fields":["purpose","email","official_payment_method"]},
        {"step":3,"id":"result","title":"Resultado de preparación","fields":["result","next_action","official_link"]}
    ]
    r["official_submission"]=False
    r["official_next_action"]="Si corresponde solicitar visa/eVisa, continúa en el sitio oficial indicado."
    return normalize(r)

@app.get("/api/sources")
async def sources(kind:Optional[str]=None):
    return normalize({"sources":official_sources(kind),"official_only":True})

@app.post("/api/sources")
async def sources_post(req:SourceRequest):
    d=model_dict(req)
    kind=d.get("kind") or d.get("category")
    return normalize({"sources":official_sources(kind),"official_only":True})

@app.get("/api/airlines")
async def airlines():
    if registry is None:return normalize({"airlines":[]})
    try:
        fn=getattr(registry,"get_airlines",None)
        if fn:return normalize({"airlines":clean(fn())})
        return normalize({"airlines":[]})
    except Exception:return normalize({"airlines":[]})

@app.post("/api/airlines")
async def airlines_post(req:AirlineRequest):
    return await airlines()

@app.get("/api/charters")
async def charters():
    if registry is None:return normalize({"charters":[]})
    try:
        fn=getattr(registry,"get_charters",None)
        if fn:return normalize({"charters":clean(fn())})
    except Exception:pass
    return normalize({"charters":[]})

@app.post("/api/solve")
async def solve(req:SolveRequest):
    return normalize(call_engine("solve",model_dict(req)))

@app.post("/api/guide")
async def guide(req:GuideRequest):
    return normalize(call_engine("build_guide",model_dict(req)))

@app.post("/api/pdf")
async def pdf(req:PDFRequest):
    d=model_dict(req)
    title=d.get("title") or "Mi resumen de preparación"
    kind=str(d.get("type") or d.get("document_type") or d.get("process") or "general").lower()
    titles={
        "flight":"Mi preparación de vuelo",
        "booking":"Mi preparación de vuelo",
        "baggage":"Mi resumen de equipaje",
        "documents":"Mis documentos para viajar",
        "dviajeros":"Mi preparación de D’Viajeros",
        "visa":"Mi preparación de visa/eVisa",
        "cuba":"Mi preparación para Cuba",
        "item":"Mi resumen del artículo",
        "trip":"Mi carpeta de viaje",
        "general":"Mi guía personal de preparación"
    }
    title=titles.get(kind,title)
    try:
        content=make_pdf(d,title)
        filename=safe_filename(title)
        return StreamingResponse(io.BytesIO(content),media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{filename}"'})
    except Exception:
        return normalize({"ok":False,"message":"No pudimos crear el PDF todavía.","next_action":"Guarda tus datos y vuelve a intentarlo."})

@app.post("/api/pdf/import")
async def pdf_import(req:PDFImportRequest):
    d=model_dict(req)
    text_value=str(d.get("text") or "")
    recovery=d.get("recovery_data") or {}
    if not text_value and not recovery:
        return normalize({"ok":False,"message":"El documento no contiene datos recuperables.","next_action":"Usa un PDF generado por esta aplicación o un archivo de recuperación."})
    return normalize({
        "ok":True,
        "imported":True,
        "recovery_data":clean(recovery),
        "text":text_value,
        "next_action":"Revisa los datos recuperados antes de continuar."
    })

@app.post("/api/pdf/upload")
async def pdf_upload(file:UploadFile=File(...)):
    raw=await file.read()
    if not raw:return normalize({"ok":False,"message":"El archivo está vacío."})
    text_value=""
    try:
        from pypdf import PdfReader
        reader=PdfReader(io.BytesIO(raw))
        text_value="\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:pass
    return normalize({
        "ok":True,
        "filename":file.filename,
        "text":text_value,
        "imported":bool(text_value.strip()),
        "next_action":"Revisa la información recuperada y corrige cualquier dato antes de continuar."
    })

@app.post("/api/export")
async def export_data(req:TripExportRequest):
    d=model_dict(req)
    return normalize({"recovery_data":trip_from(d),"format":"json","local_only":True})

@app.post("/api/local-data")
async def local_data(req:TripExportRequest):
    return await export_data(req)

@app.post("/api/local-data/import")
async def local_data_import(req:TripExportRequest):
    d=model_dict(req)
    recovery=d.get("recovery_data") or d.get("trip") or {}
    return normalize({"imported":True,"recovery_data":clean(recovery),"next_action":"Continúa desde el punto donde lo dejaste."})

@app.delete("/api/local-data")
async def delete_local(req:DeleteLocalRequest):
    return normalize({"deleted":True,"message":"Los datos locales de esta aplicación pueden eliminarse desde este dispositivo."})

@app.get("/api/legal")
async def legal():
    return normalize({
        "notice":NO_BOOKING,
        "status":"independent_preparation",
        "statements":[
            "May Roga LLC no es una aerolínea.",
            "May Roga LLC no es aeropuerto, gobierno, aduana, inmigración ni consulado.",
            "May Roga LLC no es una agencia de viajes.",
            "La aplicación no compra ni reserva vuelos.",
            "La aplicación no presenta solicitudes oficiales.",
            "Las prácticas de Visa y D’Viajeros son simulaciones.",
            "La decisión oficial corresponde siempre a la autoridad o proveedor correspondiente."
        ]
    })

@app.get("/api/ping")
async def ping():
    return {"ok":True,"version":APP_VERSION}

@app.exception_handler(HTTPException)
async def http_error(request:Request,exc:HTTPException):
    return JSONResponse(status_code=exc.status_code,content={"ok":False,"message":"No pudimos completar este paso.","next_action":"Regresa al paso anterior y vuelve a intentarlo."})

@app.exception_handler(Exception)
async def general_error(request:Request,exc:Exception):
    if os.getenv("DEBUG","").lower()=="true":
        traceback.print_exc()
    return JSONResponse(status_code=500,content={"ok":False,"message":"No pudimos completar este paso.","next_action":"Revisa los datos e inténtalo nuevamente."})

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=int(os.getenv("PORT","10000")))
