# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.0.0
from __future__ import annotations
import os,secrets,time,io
from pathlib import Path
from typing import Any,Dict
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,JSONResponse,StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from schemas import *
import cuba_engine as engine

try:
    import source_registry as registry
except Exception:
    registry=None

VERSION="12.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
BASE_DIR=Path(__file__).resolve().parent
STATIC_DIR=BASE_DIR/"static"
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","")
STRIPE_PRICE_ID=os.getenv("STRIPE_PRICE_ID") or os.getenv("STRIPE_PRICE_ID1","")
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","")
STRIPE_MODE=os.getenv("STRIPE_MODE","subscription").lower()
ACCESS_TTL=60*60*24
TOKENS:Dict[str,float]={}

app=FastAPI(title=APP_NAME,version=VERSION)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])

if STATIC_DIR.exists():
    app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")

def clean_token_store():
    now=time.time()
    for k,v in list(TOKENS.items()):
        if v<=now:
            TOKENS.pop(k,None)

def issue_token():
    clean_token_store()
    token=secrets.token_urlsafe(32)
    TOKENS[token]=time.time()+ACCESS_TTL
    return token

def authorized(token:str=""):
    clean_token_store()
    return bool(token and token in TOKENS and TOKENS[token]>time.time())

def get_token(request:Request):
    h=request.headers.get("authorization","")
    if h.lower().startswith("bearer "):
        return h[7:].strip()
    return request.headers.get("x-access-token","").strip()

def source_list(topic="",query=""):
    if registry:
        for fn in ("get_sources","sources_for","find_sources","official_sources"):
            f=getattr(registry,fn,None)
            if callable(f):
                try:
                    result=f(topic=topic,query=query)
                    if isinstance(result,dict):
                        result=result.get("sources",[])
                    if isinstance(result,list):
                        return result
                except TypeError:
                    try:
                        result=f(topic,query)
                        if isinstance(result,dict):
                            result=result.get("sources",[])
                        if isinstance(result,list):
                            return result
                    except Exception:
                        pass
                except Exception:
                    pass
    return []

def call_engine(*names,**kwargs):
    for name in names:
        fn=getattr(engine,name,None)
        if callable(fn):
            try:
                return fn(**kwargs)
            except TypeError:
                try:
                    return fn(kwargs)
                except TypeError:
                    continue
    raise HTTPException(500,"El módulo de orientación no tiene disponible esta función.")

def model_dict(obj):
    if hasattr(obj,"model_dump"):
        return obj.model_dump(by_alias=True)
    if isinstance(obj,dict):
        return obj
    return {"data":obj}

def normalize_result(result,default_title="Resultado"):
    d=model_dict(result)
    if "title" not in d or not d["title"]:
        d["title"]=default_title
    if "sources" not in d or not d["sources"]:
        d["sources"]=source_list(d.get("topic",""),d.get("query",""))
    return d

@app.get("/",include_in_schema=False)
async def home():
    f=STATIC_DIR/"index.html"
    if not f.exists():
        return JSONResponse({"ok":False,"error":"static/index.html no encontrado"},status_code=500)
    return FileResponse(str(f))

@app.get("/health",response_model=HealthResponse)
async def health():
    return HealthResponse(ok=True,app=APP_NAME,version=VERSION,status="ready")

@app.get("/api/config")
async def config():
    return {
        "ok":True,
        "app":APP_NAME,
        "version":VERSION,
        "price":"15.99",
        "stripe_public_key":STRIPE_PUBLISHABLE_KEY,
        "stripe_ready":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID),
        "access_required":bool(ADMIN_USERNAME and ADMIN_PASSWORD),
        "language_default":"es",
        "features":{
            "flight":True,
            "booking_simulation":True,
            "baggage":True,
            "item_advisor":True,
            "cuba":True,
            "documents":True,
            "practice":True,
            "sources":True,
            "guide":True,
            "pdf":True,
            "airlines":True,
            "dviajeros":True,
            "visa":True
        }
    }

@app.post("/api/access",response_model=AccessResponse)
async def access(data:AccessRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        return AccessResponse(ok=True,authorized=False,message="El acceso administrativo no está configurado.")
    if secrets.compare_digest(data.username,ADMIN_USERNAME) and secrets.compare_digest(data.password,ADMIN_PASSWORD):
        return AccessResponse(ok=True,authorized=True,token=issue_token(),message="Acceso autorizado.")
    return AccessResponse(ok=True,authorized=False,message="Usuario o contraseña incorrectos.")

@app.get("/api/access")
async def access_status(request:Request):
    return {"ok":True,"authorized":authorized(get_token(request))}

@app.post("/api/checkout",response_model=CheckoutResponse)
async def checkout(data:CheckoutRequest):
    if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID:
        return CheckoutResponse(ok=False,message="Stripe no está configurado todavía.")
    try:
        stripe.api_key=STRIPE_SECRET_KEY
        params={
            "mode":"subscription" if STRIPE_MODE=="subscription" else "payment",
            "line_items":[{"price":STRIPE_PRICE_ID,"quantity":1}],
            "success_url":data.success_url or "https://example.com/?payment=success",
            "cancel_url":data.cancel_url or "https://example.com/?payment=cancelled"
        }
        session=stripe.checkout.Session.create(**params)
        return CheckoutResponse(ok=True,url=session.url,session_id=session.id,message="Checkout creado.")
    except Exception as e:
        return CheckoutResponse(ok=False,message=f"No fue posible iniciar el acceso: {str(e)}")

@app.post("/api/flight",response_model=FlightResponse)
async def flight(data:FlightRequest):
    result=call_engine("analyze_flight","flight_analysis","understand_flight",data=data.model_dump(by_alias=True))
    return normalize_result(result,"Mi vuelo")

@app.post("/api/booking",response_model=BookingResponse)
async def booking(data:BookingRequest):
    result=call_engine("booking_simulation","flight_search_simulation","simulate_booking",data=data.model_dump(by_alias=True))
    d=normalize_result(result,"Práctica de búsqueda de vuelo")
    d["simulation"]=True
    d["real_booking"]=False
    d["payment"]=False
    return d

@app.post("/api/connection")
async def connection(data:ConnectionRequest):
    result=call_engine("connection_analysis","analyze_connection",data=data.model_dump())
    return normalize_result(result,"Mi escala")

@app.post("/api/baggage",response_model=BaggageResponse)
async def baggage(data:BaggageRequest):
    result=call_engine("baggage_rules","analyze_baggage","baggage_analysis","check_baggage","baggage_check",data=data.model_dump())
    return normalize_result(result,"Mi equipaje")

@app.post("/api/item",response_model=ItemResponse)
async def item(data:ItemRequest):
    result=call_engine("item_analysis","analyze_item","check_item","item_check",data=data.model_dump())
    return normalize_result(result,"¿Qué quiero llevar?")

@app.post("/api/cuba",response_model=CubaResponse)
async def cuba(data:CubaRequest):
    result=call_engine("cuba_check","analyze_cuba","cuba_analysis","cuba_entry_check",data=data.model_dump())
    return normalize_result(result,"Viajo a Cuba")

@app.post("/api/documents",response_model=DocumentResponse)
async def documents(data:DocumentRequest):
    result=call_engine("document_analysis","document_check","documents_check",data=data.model_dump())
    return normalize_result(result,"Mis documentos")

@app.post("/api/practice",response_model=PracticeResponse)
async def practice(data:PracticeRequest):
    result=call_engine("practice_scenario","practice","run_practice",data=data.model_dump())
    return normalize_result(result,"Practicar")

@app.post("/api/dviajeros")
async def dviajeros(data:DViajeroRequest):
    result=call_engine("dviajeros_simulation","simulate_dviajeros",data=data.model_dump())
    d=normalize_result(result,"Práctica D’Viajeros")
    d["official_submission"]=False
    return d

@app.post("/api/visa")
async def visa(data:VisaRequest):
    result=call_engine("visa_simulation","simulate_visa",data=data.model_dump())
    d=normalize_result(result,"Práctica de visa")
    d["official_submission"]=False
    return d

@app.get("/api/sources",response_model=SourceResponse)
async def sources(topic:str="official",query:str=""):
    return SourceResponse(ok=True,sources=source_list(topic,query),topic=topic)

@app.post("/api/sources",response_model=SourceResponse)
async def sources_post(data:SourceRequest):
    return SourceResponse(ok=True,sources=source_list(data.topic,data.query),topic=data.topic)

@app.post("/api/airlines",response_model=AirlineResponse)
async def airlines(data:AirlineRequest):
    q=(data.name or data.airline or "").strip().lower()
    matches=[]
    if registry:
        for fn in ("get_airlines","airlines","find_airlines","airline_list"):
            f=getattr(registry,fn,None)
            if callable(f):
                try:
                    r=f(q)
                    if isinstance(r,dict):
                        r=r.get("airlines",r.get("matches",[]))
                    if isinstance(r,list):
                        matches=r
                        break
                except Exception:
                    pass
    if not matches:
        all_sources=source_list("airlines",q)
        for s in all_sources:
            if isinstance(s,dict) and (s.get("type")=="airline" or s.get("category")=="airline"):
                matches.append(s)
    return AirlineResponse(ok=True,query=q,matches=matches,message="Estas son las aerolíneas disponibles en el registro. Las rutas y condiciones deben confirmarse en el sitio oficial.",next_action="Selecciona tu aerolínea y después revisa su itinerario y equipaje.")

@app.post("/api/solve")
async def solve(data:SolveRequest):
    q=data.question.strip()
    if not q:
        return {"ok":False,"message":"Escribe la pregunta que necesitas resolver.","next_action":"Escribe qué quieres saber."}
    try:
        result=call_engine("solve","answer","resolve",question=q,data=data.data)
        return normalize_result(result,"Ayuda para tu viaje")
    except HTTPException:
        pass
    sources=source_list("general",q)
    return {
        "ok":True,
        "title":"Cómo comprobarlo",
        "message":"Para darte una respuesta responsable necesito que compruebes el dato en la fuente que controla ese requisito.",
        "details":[
            "Busca el nombre exacto del requisito en tu boleto, reserva o documento.",
            "Después comprueba la misma información en el sitio oficial correspondiente.",
            "Si me indicas lo que aparece allí, puedo ayudarte a entenderlo."
        ],
        "sources":sources,
        "next_action":"Busca el dato y vuelve con lo que aparece."
    }

@app.post("/api/guide",response_model=GuideResponse)
async def guide(data:GuideRequest):
    result=call_engine("build_guide","make_guide","guide",data=data.model_dump())
    return normalize_result(result,"Mi guía de viaje")

@app.post("/api/pdf")
async def pdf(data:PDFRequest):
    buffer=io.BytesIO()
    styles=getSampleStyleSheet()
    title=styles["Title"]
    title.alignment=TA_CENTER
    normal=styles["BodyText"]
    normal.leading=14
    story=[Paragraph("¿QUÉ QUIERES LLEVAR?",title),Paragraph("Guía personal de preparación de viaje — May Roga LLC",normal),Spacer(1,12)]
    trip=data.trip or {}
    rows=[]
    labels={
        "origin":"Origen","destination":"Destino","airline":"Aerolínea",
        "flight_number":"Número de vuelo","flight_type":"Tipo de vuelo",
        "nationality":"Nacionalidad","country_of_residence":"Residencia",
        "purpose":"Motivo del viaje","arrival_date":"Llegada","departure_date":"Regreso"
    }
    for k,label in labels.items():
        v=trip.get(k,"")
        if v not in ("",None,False):
            rows.append([label,str(v)])
    if rows:
        t=Table(rows,colWidths=[150,360])
        t.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),.5,colors.grey),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),9),
            ("BOTTOMPADDING",(0,0),(-1,-1),6),
            ("TOPPADDING",(0,0),(-1,-1),6)
        ]))
        story.extend([Paragraph("Datos del viaje",styles["Heading2"]),t,Spacer(1,12)])
    if data.items:
        story.append(Paragraph("Artículos revisados",styles["Heading2"]))
        for x in data.items:
            if isinstance(x,dict):
                text=" — ".join(str(v) for v in [x.get("item",""),x.get("status",""),x.get("message","")] if v)
            else:
                text=str(x)
            story.extend([Paragraph(text,normal),Spacer(1,5)])
    if data.documents:
        story.append(Paragraph("Documentos",styles["Heading2"]))
        for x in data.documents:
            if isinstance(x,dict):
                text=f"{x.get('name','Documento')} — {x.get('status','REVISAR')}"
            else:
                text=str(x)
            story.extend([Paragraph(text,normal),Spacer(1,5)])
    if data.pending:
        story.append(Paragraph("Pendientes",styles["Heading2"]))
        for x in data.pending:
            story.extend([Paragraph(str(x),normal),Spacer(1,4)])
    if data.sources:
        story.append(Paragraph("Fuentes oficiales consultadas",styles["Heading2"]))
        for x in data.sources:
            if isinstance(x,dict):
                name=x.get("name") or x.get("publisher") or "Fuente oficial"
                url=x.get("url","")
                story.append(Paragraph(f"{name}: {url}",normal))
            else:
                story.append(Paragraph(str(x),normal))
            story.append(Spacer(1,4))
    story.extend([
        Spacer(1,12),
        Paragraph("IMPORTANTE: esta guía es una herramienta independiente de preparación y orientación de May Roga LLC. No sustituye las instrucciones de una aerolínea, gobierno, aeropuerto, autoridad migratoria, aduanera o de seguridad.",normal)
    ])
    SimpleDocTemplate(buffer,pagesize=letter,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40).build(story)
    buffer.seek(0)
    return StreamingResponse(buffer,media_type="application/pdf",headers={"Content-Disposition":"attachment; filename=mi-guia-viaje.pdf"})

@app.get("/api/legal")
async def legal():
    return {
        "ok":True,
        "title":"Aviso importante",
        "message":"¿QUÉ QUIERES LLEVAR? es una herramienta independiente de preparación y orientación de May Roga LLC.",
        "points":[
            "No es una aerolínea, agencia de viajes, aeropuerto, gobierno, consulado ni autoridad.",
            "No vende ni reserva vuelos.",
            "Las simulaciones son educativas y no son formularios oficiales.",
            "Las condiciones de vuelos, equipaje, entrada, visa, aduana y seguridad deben confirmarse en las fuentes oficiales.",
            "Cuando un dato no está confirmado, la aplicación debe indicar qué revisar y dónde comprobarlo."
        ]
    }

@app.post("/api/export")
async def export_trip(data:TripExportRequest):
    return {"ok":True,"data":data.data.model_dump(),"message":"Datos preparados para conservarlos localmente."}

@app.get("/api/ping")
async def ping():
    return {"ok":True,"app":APP_NAME,"version":VERSION}

@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):
    return JSONResponse(
        status_code=500,
        content={
            "ok":False,
            "error":"internal_error",
            "message":"La aplicación encontró un problema al procesar esta acción.",
            "details":str(exc)
        }
    )
