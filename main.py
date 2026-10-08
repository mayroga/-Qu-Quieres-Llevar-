from pathlib import Path
import os
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles

import cuba_engine as engine

BASE=Path(__file__).resolve().parent
STATIC=BASE/"static"
VERSION="17.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"

app=FastAPI(title=APP_NAME,version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

if STATIC.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC)),name="static")

@app.get("/",include_in_schema=False)
def home():
    f=STATIC/"index.html"
    if not f.exists():
        raise HTTPException(404,"No se encontró la aplicación.")
    return FileResponse(str(f))

@app.get("/health")
def health():
    try:
        h=engine.health()
        if isinstance(h,dict):
            return {"ok":True,"version":VERSION,**h}
    except Exception:
        pass
    return {
        "ok":True,
        "version":VERSION,
        "gemini":bool(os.getenv("GEMINI_API_KEY"))
    }

@app.get("/api/config")
def config():
    return {
        "app_name":APP_NAME,
        "version":VERSION,
        "language":"es",
        "languages":["es","en"],
        "free":True,
        "login":False,
        "payment":False,
        "server_storage":False,
        "pdf":"optional",
        "features":{
            "dviajeros":True,
            "visa":True,
            "flights":True,
            "charters":True,
            "baggage":True,
            "items":True,
            "official_deep_links":True,
            "visual_guides":True,
            "pdf_optional":True
        }
    }

def call_engine(fn,data):
    try:
        return fn(data)
    except TypeError:
        try:
            return fn(**data)
        except Exception as e:
            raise HTTPException(400,str(e))
    except Exception as e:
        raise HTTPException(400,str(e))

@app.post("/api/item")
def item(req):
    return call_engine(engine.item_analysis,req.model_dump())

@app.post("/api/baggage")
def baggage(req):
    return call_engine(engine.baggage_rules,req.model_dump())

@app.post("/api/flight")
def flight(req):
    return call_engine(engine.analyze_flight,req.model_dump())

@app.post("/api/booking")
def booking(req):
    return call_engine(engine.booking_simulation,req.model_dump())

@app.post("/api/connection")
def connection(req):
    return call_engine(engine.connection_analysis,req.model_dump())

@app.post("/api/cuba")
def cuba(req):
    return call_engine(engine.cuba_check,req.model_dump())

@app.post("/api/cuba/entry")
def cuba_entry(req):
    return call_engine(engine.cuba_entry,req.model_dump())

@app.post("/api/documents")
def documents(req):
    return call_engine(engine.document_analysis,req.model_dump())

@app.post("/api/practice")
def practice(req):
    return call_engine(engine.practice_scenario,req.model_dump())

@app.post("/api/dviajeros")
def dviajeros(req):
    return call_engine(engine.dviajeros_simulation,req.model_dump())

@app.post("/api/visa")
def visa(req):
    return call_engine(engine.visa_simulation,req.model_dump())

@app.get("/api/sources")
def sources():
    try:
        return engine.get_sources()
    except Exception:
        return []

@app.post("/api/sources")
def add_source(data:dict):
    fn=getattr(engine,"add_source",None)
    if not fn:
        raise HTTPException(404,"Función no disponible.")
    return call_engine(fn,data)

@app.get("/api/official")
def official():
    try:
        return engine.official_sources()
    except Exception:
        return []

@app.get("/api/airlines")
def airlines():
    try:
        return engine.get_airlines()
    except Exception:
        return []

@app.post("/api/airlines")
def add_airline(data:dict):
    fn=getattr(engine,"add_airline",None)
    if not fn:
        raise HTTPException(404,"Función no disponible.")
    return call_engine(fn,data)

@app.get("/api/charters")
def charters():
    try:
        return engine.get_charters()
    except Exception:
        return []

@app.get("/api/cuba-official")
def cuba_official():
    try:
        return engine.official_url("cuba")
    except Exception:
        return {
            "dviajeros":"https://dviajeros.mitrans.gob.cu/",
            "visa":"https://evisacuba.cu/"
        }

@app.get("/api/airlines-cuba")
def airlines_cuba():
    try:
        return engine.get_airlines()
    except Exception:
        return []

@app.post("/api/solve")
def solve(data:dict):
    fn=getattr(engine,"solve",None)
    if not fn:
        raise HTTPException(404,"Función no disponible.")
    return call_engine(fn,data)

@app.post("/api/guide")
def guide(data:dict):
    fn=getattr(engine,"guide",None)
    if not fn:
        raise HTTPException(404,"Función no disponible.")
    return call_engine(fn,data)

@app.post("/api/pdf")
def pdf(req):
    return call_engine(engine.create_pdf,req.model_dump())

@app.post("/api/pdf/import")
def pdf_import(req):
    fn=getattr(engine,"import_pdf",None)
    if not fn:
        raise HTTPException(404,"Importación no disponible.")
    return call_engine(fn,req.model_dump())

@app.post("/api/export")
def export(data:dict):
    fn=getattr(engine,"export_data",None)
    if not fn:
        raise HTTPException(404,"Exportación no disponible.")
    return call_engine(fn,data)

@app.post("/api/local-data")
def local_data(data:dict):
    return {
        "ok":True,
        "server_storage":False,
        "message":"Los datos deben conservarse en el dispositivo del cliente."
    }

@app.get("/api/legal")
def legal():
    return {
        "version":VERSION,
        "text":"No somos gobierno, aerolínea, aeropuerto, aduana, inmigración, consulado ni agencia de viajes.",
        "details":[
            "La aplicación sirve para preparación y orientación.",
            "No vende boletos.",
            "No realiza reservas.",
            "No presenta formularios oficiales por el cliente.",
            "No realiza pagos oficiales.",
            "No sustituye las instrucciones del sitio oficial."
        ]
    }

@app.get("/api/ping")
def ping():
    return {"ok":True,"version":VERSION}

@app.exception_handler(Exception)
async def unexpected(request,exc):
    return JSONResponse(
        status_code=500,
        content={"ok":False,"error":"No pudimos completar esta acción. Inténtalo nuevamente."}
    )
