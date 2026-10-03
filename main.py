# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | CUBA TRAVEL
import os,secrets,time
from pathlib import Path
from typing import Optional
import stripe
from fastapi import FastAPI,Request,HTTPException
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from schemas import AccessRequest,FlightRequest,ItemRequest,CubaRequest,PracticeRequest,GuideRequest

APP_NAME="¿QUÉ QUIERES LLEVAR?"
VERSION="1.0.0"
BASE=Path(__file__).resolve().parent
STATIC=BASE/"static"
stripe.api_key=os.getenv("STRIPE_SECRET_KEY","")
ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
STRIPE_PRICE_ID=os.getenv("STRIPE_PRICE_ID","")
SESSIONS={}
app=FastAPI(title=APP_NAME,version=VERSION)
app.mount("/static",StaticFiles(directory=str(STATIC)),name="static")

def lang(v):
    return "en" if str(v or "es").lower().startswith("en") else "es"

def ok(data=None,message="OK"):
    return {"ok":True,"message":message,"data":data or {}}

@app.get("/")
def home():
    return FileResponse(STATIC/"index.html")

@app.get("/health")
def health():
    return {"status":"ok","app":APP_NAME,"version":VERSION}

@app.get("/api/config")
def config():
    return {
        "app_name":APP_NAME,
        "version":VERSION,
        "language_default":"es",
        "price":15.99,
        "currency":"USD",
        "stripe_enabled":bool(stripe.api_key and STRIPE_PRICE_ID)
    }

@app.post("/api/access")
def access(data:AccessRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(503,"Acceso administrativo no configurado")
    if data.username!=ADMIN_USERNAME or data.password!=ADMIN_PASSWORD:
        raise HTTPException(401,"Usuario o contraseña incorrectos")
    token=secrets.token_urlsafe(24)
    SESSIONS[token]=time.time()
    return {"ok":True,"token":token,"expires_in":86400}

@app.post("/api/checkout")
def checkout(request:Request):
    if not stripe.api_key or not STRIPE_PRICE_ID:
        raise HTTPException(503,"Pago no configurado")
    origin=str(request.base_url).rstrip("/")
    try:
        s=stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price":STRIPE_PRICE_ID,"quantity":1}],
            success_url=origin+"/?payment=success",
            cancel_url=origin+"/?payment=cancelled"
        )
        return {"ok":True,"url":s.url}
    except Exception as e:
        raise HTTPException(500,str(e))

@app.post("/api/flight")
def flight(data:FlightRequest):
    l=lang(data.language)
    return ok({
        "origin":data.origin,
        "destination":data.destination,
        "airline":data.airline,
        "flight_number":data.flight_number,
        "connection":data.connection,
        "cuba":("cuba" in data.destination.lower()),
        "next":("Verifica tu vuelo y sus condiciones directamente con la aerolínea."
                if l=="es" else
                "Verify your flight and its conditions directly with the airline.")
    })

@app.post("/api/item")
def item(data:ItemRequest):
    return ok({"item":data.item,"language":lang(data.language)})

@app.post("/api/cuba")
def cuba(data:CubaRequest):
    return ok({
        "nationality":data.nationality,
        "cuban_nationality":data.cuban_nationality,
        "passport":data.passport,
        "arrival_by":data.arrival_by,
        "topic":data.topic,
        "language":lang(data.language)
    })

@app.post("/api/practice")
def practice(data:PracticeRequest):
    return ok({
        "topic":data.topic,
        "step":1,
        "simulation":True,
        "real_submission":False,
        "language":lang(data.language)
    })

@app.post("/api/guide")
def guide(data:GuideRequest):
    return ok({
        "language":lang(data.language),
        "flight":data.flight,
        "baggage":data.baggage,
        "items":data.items,
        "documents":data.documents,
        "cuba":data.cuba
    })

@app.get("/api/sources")
def sources():
    try:
        from source_registry import registry
        return ok(registry())
    except Exception:
        return ok({})

@app.get("/api/legal")
def legal():
    return ok({
        "company":"May Roga LLC",
        "text":"¿QUÉ QUIERES LLEVAR? es un servicio independiente de preparación y orientación para viajes. No es una aerolínea, gobierno, aeropuerto, autoridad migratoria, agencia de viajes ni proveedor oficial de D’Viajeros o visa de Cuba. Los trámites reales deben completarse en las fuentes oficiales correspondientes."
    })

@app.exception_handler(Exception)
async def error_handler(request:Request,exc:Exception):
    return JSONResponse(status_code=500,content={"ok":False,"error":"Error interno"})

if __name__=="__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0",port=int(os.getenv("PORT","10000")))
