# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v8.2.0
from __future__ import annotations
import os,secrets,time,hashlib
from datetime import datetime,timezone,timedelta
from pathlib import Path
from typing import Any,Dict,Optional,List
from urllib.parse import quote_plus
import stripe
from fastapi import FastAPI,HTTPException,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field

try:
 from flight_engine import engine as flight_engine
except Exception:
 from flight_engine import FlightEngine
 flight_engine=FlightEngine()

try:
 from source_registry import REGISTRY,google_flights_url
except Exception:
 REGISTRY=None
 def google_flights_url(origin="",destination="",departure_date="",return_date=""):
  q=f"{origin} to {destination}"
  return f"https://www.google.com/travel/flights?q={quote_plus(q)}"

try:
 from rules_engine import RuleRepository
 RULE_REPO=RuleRepository()
except Exception:
 RULE_REPO=None

VERSION="8.2.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
COMPANY="May Roga LLC"
PRICE_USD=15.99
SESSION_MINUTES=15
BASE=Path(__file__).resolve().parent
STATIC=BASE/"static"

ADMIN_USERNAME=os.getenv("ADMIN_USERNAME","")
ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD","")
STRIPE_SECRET_KEY=os.getenv("STRIPE_SECRET_KEY","")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","")
STRIPE_PRICE_ID1=os.getenv("STRIPE_PRICE_ID1","")
STRIPE_PUBLISHABLE_KEY=os.getenv("STRIPE_PUBLISHABLE_KEY","")
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","")

stripe.api_key=STRIPE_SECRET_KEY

app=FastAPI(title=APP_NAME,description="Preparación independiente de viaje, vuelos y equipaje — May Roga LLC",version=VERSION)
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
if STATIC.exists():
 app.mount("/static",StaticFiles(directory=str(STATIC)),name="static")

SESSIONS:Dict[str,Dict[str,Any]]={}
ADMIN_SESSIONS:Dict[str,Dict[str,Any]]={}
PAYMENT_TOKENS:Dict[str,Dict[str,Any]]={}
LOGIN_ATTEMPTS:Dict[str,List[float]]={}

LEGAL_ES={
 "title":"Aviso legal",
 "text":"¿QUÉ QUIERES LLEVAR? es un servicio independiente de preparación y orientación de May Roga LLC. No es TSA, FAA, CBP, IATA, una aerolínea, aeropuerto, gobierno, consulado, eVisa, D’Viajeros ni otro organismo oficial. La información ayuda a preparar el viaje, pero la decisión final corresponde a la autoridad, aerolínea o proveedor competente.",
 "short":"Orientación independiente de May Roga LLC. Confirma siempre la regla vigente con la fuente oficial correspondiente."
}
LEGAL_EN={
 "title":"Legal notice",
 "text":"¿QUÉ QUIERES LLEVAR? is an independent travel-preparation and guidance service from May Roga LLC. It is not TSA, FAA, CBP, IATA, an airline, airport, government, consulate, eVisa, D’Viajeros, or another official body. The information helps prepare the trip, but the final decision belongs to the applicable authority, airline, or provider.",
 "short":"Independent guidance from May Roga LLC. Always confirm the current rule with the applicable official source."
}

class BasePayload(BaseModel):
 session_token:Optional[str]=None
 language:str="es"

class FlightSearchRequest(BaseModel):
 natural_query:Optional[str]=None
 origin:Optional[str]=""
 destination:Optional[str]=""
 departure_date:Optional[str]=""
 return_date:Optional[str]=""
 airline:Optional[str]=""
 cabin:Optional[str]=""
 fare:Optional[str]=""
 passengers:int=1
 stops:Optional[int]=None
 session_token:Optional[str]=None
 language:str="es"

class FlightUnderstandRequest(FlightSearchRequest):
 pass

class ItemCheckRequest(BaseModel):
 session_token:Optional[str]=None
 item_description:str
 airline:Optional[str]=""
 baggage_type:Optional[str]=""
 origin:Optional[str]=""
 destination:Optional[str]=""
 quantity:Optional[int]=None
 wh:Optional[float]=None
 volts:Optional[float]=None
 ah:Optional[float]=None
 mah:Optional[float]=None
 spare:Optional[bool]=None
 language:str="es"

class AdminLoginRequest(BaseModel):
 username:str
 password:str

class CheckoutRequest(BaseModel):
 language:str="es"

class VerifyPaymentRequest(BaseModel):
 session_id:str

class CubaRequest(BaseModel):
 session_token:Optional[str]=None
 language:str="es"
 nationality:Optional[str]=""
 dual_nationality:Optional[bool]=None
 destination:Optional[str]="Cuba"
 origin:Optional[str]=""

class PracticeRequest(BaseModel):
 language:str="es"
 airline:Optional[str]=""
 origin:Optional[str]=""
 destination:Optional[str]=""
 practice_type:Optional[str]="general"

def now()->datetime:
 return datetime.now(timezone.utc)

def iso(dt:datetime)->str:
 return dt.astimezone(timezone.utc).isoformat()

def lang(v:Any)->str:
 return "en" if str(v or "").lower().strip() in ("en","english","inglés","ingles") else "es"

def clean(v:Any,maxlen:int=500)->str:
 return str(v or "").strip()[:maxlen]

def client_ip(request:Request)->str:
 return clean(request.headers.get("x-forwarded-for") or request.client.host if request.client else "unknown",100)

def legal(language:str="es")->Dict[str,str]:
 return LEGAL_EN.copy() if lang(language)=="en" else LEGAL_ES.copy()

def source_dict(x:Any)->Dict[str,Any]:
 if isinstance(x,dict):
  d=dict(x)
 else:
  d={k:getattr(x,k,None) for k in ("id","name","url","alternate_url","category","description","authority_type","official_for","country","airline","verified","verified_date")}
 d["official"]=d.get("authority_type") in ("government","airline") if "authority_type" in d else bool(d.get("official",True))
 d["verified"]=bool(d.get("verified",False))
 return d

def normalize_sources(items:Any)->List[Dict[str,Any]]:
 if isinstance(items,dict):
  items=items.get("sources") or items.get("official_sources") or items.get("airline_sources") or items.get("charter_sources") or []
 out=[]
 seen=set()
 for x in items or []:
  d=source_dict(x)
  url=clean(d.get("url"))
  if not url.startswith(("https://","http://")):continue
  key=d.get("id") or url
  if key in seen:continue
  seen.add(key)
  out.append(d)
 return out

def registry_call(name:str,*args,**kwargs)->Any:
 if REGISTRY is None:return []
 fn=getattr(REGISTRY,name,None)
 if not callable(fn):return []
 try:return fn(*args,**kwargs)
 except Exception:return []

def get_route_sources(origin="",destination="",airline="",language="es"):
 try:
  if hasattr(flight_engine,"sources_for_route"):
   d=flight_engine.sources_for_route(origin,destination,airline,language)
   return d
 except Exception:pass
 return {
  "success":True,
  "version":VERSION,
  "language":lang(language),
  "origin":origin,
  "destination":destination,
  "is_cuba_route":False,
  "sources":normalize_sources(registry_call("route_sources",origin,destination,airline)),
  "charter_sources":[],
  "airline_sources":normalize_sources(registry_call("official_for_airline",airline))
 }

def session_valid(token:str)->bool:
 if not token:return False
 d=SESSIONS.get(token) or ADMIN_SESSIONS.get(token)
 if not d:return False
 if d.get("admin"):return True
 exp=d.get("expires_at")
 if not exp:return False
 if isinstance(exp,str):
  try:exp=datetime.fromisoformat(exp)
  except Exception:return False
 if now()>=exp:
  SESSIONS.pop(token,None)
  return False
 return True

def require_session(token:Optional[str],allow_guest:bool=False)->Dict[str,Any]:
 if token and session_valid(token):
  return SESSIONS.get(token) or ADMIN_SESSIONS.get(token) or {}
 if allow_guest:return {}
 raise HTTPException(401,"Sesión de preparación no activa o expirada.")

def new_session(minutes:int=SESSION_MINUTES,admin:bool=False)->str:
 token=secrets.token_urlsafe(32)
 d={"created_at":iso(now()),"expires_at":iso(now()+timedelta(minutes=minutes)),"admin":admin,"language":"es"}
 if admin:ADMIN_SESSIONS[token]=d
 else:SESSIONS[token]=d
 return token

def cleanup():
 t=now()
 for store in (SESSIONS,PAYMENT_TOKENS):
  dead=[]
  for k,v in store.items():
   e=v.get("expires_at")
   try:
    if e and datetime.fromisoformat(e)<=t:dead.append(k)
   except Exception:dead.append(k)
  for k in dead:store.pop(k,None)

def login_allowed(ip:str)->bool:
 t=time.time()
 arr=[x for x in LOGIN_ATTEMPTS.get(ip,[]) if t-x<300]
 LOGIN_ATTEMPTS[ip]=arr
 return len(arr)<8

def register_login(ip:str):
 LOGIN_ATTEMPTS.setdefault(ip,[]).append(time.time())

def rules_call(method:str,**kwargs)->Any:
 if RULE_REPO is None:return None
 fn=getattr(RULE_REPO,method,None)
 if callable(fn):
  try:return fn(**kwargs)
  except TypeError:
   try:return fn(kwargs)
   except Exception:return None
  except Exception:return None
 for name in ("advisor_call","advise","evaluate"):
  fn=getattr(RULE_REPO,name,None)
  if callable(fn):
   try:return fn(method,**kwargs)
   except Exception:continue
 return None

def fallback_item(item:str,language:str="es")->Dict[str,Any]:
 en=lang(language)=="en"
 return {
  "status_category":"CHECK" if en else "REVISA ESTO ANTES DE VIAJAR",
  "short_answer":"We need more details and the applicable official rule before confirming this item." if en else "Necesitamos más datos y la regla oficial aplicable antes de confirmar este artículo.",
  "details":"The result depends on the item, baggage type, airline, route or destination. Do not treat a generic rule as universal." if en else "El resultado puede depender del artículo, tipo de equipaje, aerolínea, ruta o destino. No tomes una regla general como universal.",
  "next_action":"Confirm the applicable rule with the airline and official authority." if en else "Confirma la regla aplicable con la aerolínea y la autoridad oficial correspondiente.",
  "official_sources":[]
 }

def battery_result(p:ItemCheckRequest)->Optional[Dict[str,Any]]:
 wh=p.wh
 try:
  if wh is None and p.volts is not None:
   if p.ah is not None:wh=float(p.volts)*float(p.ah)
   elif p.mah is not None:wh=float(p.volts)*(float(p.mah)/1000)
 except Exception:return None
 if wh is None:return None
 en=lang(p.language)=="en"
 if wh>160:
  status="CANNOT TAKE IT" if en else "NO PUEDES LLEVARLO"
  answer="A lithium battery over 160 Wh is not permitted for passenger aircraft." if en else "Una batería de litio de más de 160 Wh no está permitida en aeronaves de pasajeros."
 elif wh>100:
  status="CHECK THIS FIRST" if en else "REVISA ESTO ANTES DE VIAJAR"
  answer="101–160 Wh generally requires airline approval. The airline may impose stricter limits." if en else "De 101–160 Wh generalmente requiere aprobación de la aerolínea. La aerolínea puede imponer límites más estrictos."
 else:
  status="GENERALLY ALLOWED" if en else "PUEDES LLEVARLO"
  answer="Up to 100 Wh is generally allowed under FAA passenger guidance, subject to applicable airline and security rules." if en else "Hasta 100 Wh generalmente está permitido según la guía de la FAA para pasajeros, sujeto a las reglas aplicables de la aerolínea y seguridad."
 if p.spare is True:
  place="Spare lithium batteries and power banks must be carried in the cabin, not checked baggage." if en else "Las baterías de litio de repuesto y los power banks deben ir en cabina, no en el equipaje facturado."
 else:
  place="Confirm the airline's current baggage rule for the device." if en else "Confirma la regla vigente de la aerolínea para el dispositivo."
 sources=normalize_sources(registry_call("search","battery"))
 return {
  "status_category":status,
  "short_answer":answer,
  "details":place,
  "next_action":"Confirm the current airline rule before travel." if en else "Confirma la regla vigente de la aerolínea antes de viajar.",
  "official_sources":sources,
  "battery_wh":round(wh,2)
 }

@app.get("/",response_class=FileResponse)
def root():
 f=STATIC/"index.html"
 if f.exists():return FileResponse(str(f))
 raise HTTPException(404,"static/index.html not found")

@app.get("/health")
@app.get("/api/health")
def health():
 cleanup()
 return {"status":"ok","app":APP_NAME,"version":VERSION,"time":iso(now())}

@app.get("/api/v1/meta")
def meta():
 return {"name":APP_NAME,"company":COMPANY,"version":VERSION,"payment_minutes":SESSION_MINUTES,"price":PRICE_USD,"currency":"USD","live_flight_results":False}

@app.get("/api/v1/config")
def config():
 return {
  "name":APP_NAME,
  "company":COMPANY,
  "version":VERSION,
  "price":PRICE_USD,
  "currency":"USD",
  "payment_minutes":SESSION_MINUTES,
  "stripe_enabled":bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
  "publishable_key":STRIPE_PUBLISHABLE_KEY,
  "language_default":"es",
  "live_results_available":False
 }

@app.get("/api/v1/legal")
def legal_api(language:str="es"):
 return legal(language)

@app.get("/api/v1/session")
def session_status(request:Request,session_token:Optional[str]=None):
 token=session_token or request.headers.get("x-session-token") or request.cookies.get("session_token")
 if not token or not session_valid(token):return {"active":False}
 d=SESSIONS.get(token) or ADMIN_SESSIONS.get(token)
 return {"active":True,"admin":bool(d.get("admin")),"expires_at":d.get("expires_at"),"session_token":token}

@app.post("/api/v1/admin/login")
def admin_login(payload:AdminLoginRequest,request:Request):
 ip=client_ip(request)
 if not login_allowed(ip):raise HTTPException(429,"Demasiados intentos. Espera unos minutos.")
 if not ADMIN_USERNAME or not ADMIN_PASSWORD:
  raise HTTPException(503,"Administrator credentials are not configured.")
 if not secrets.compare_digest(payload.username,ADMIN_USERNAME) or not secrets.compare_digest(payload.password,ADMIN_PASSWORD):
  register_login(ip)
  raise HTTPException(401,"Credenciales inválidas.")
 token=new_session(1440,True)
 return {"status":"success","token":token,"admin_token":token,"session_token":token,"expires_at":ADMIN_SESSIONS[token]["expires_at"]}

@app.post("/api/v1/create-checkout-session")
def create_checkout(payload:CheckoutRequest,request:Request):
 if not STRIPE_SECRET_KEY or not STRIPE_PRICE_ID1:
  raise HTTPException(503,"Stripe no está configurado.")
 base=str(request.base_url).rstrip("/")
 try:
  s=stripe.checkout.Session.create(
   mode="payment",
   line_items=[{"price":STRIPE_PRICE_ID1,"quantity":1}],
   success_url=f"{base}/?session_id={{CHECKOUT_SESSION_ID}}",
   cancel_url=f"{base}/?payment=cancelled",
   metadata={"app":APP_NAME,"version":VERSION},
   allow_promotion_codes=True
  )
 except stripe.error.StripeError:
  raise HTTPException(502,"No se pudo iniciar el pago.")
 return {"checkout_url":s.url,"url":s.url,"session_id":s.id,"price":PRICE_USD,"currency":"USD","minutes":SESSION_MINUTES}

@app.post("/api/v1/verify-payment")
def verify_payment(payload:VerifyPaymentRequest):
 sid=clean(payload.session_id,200)
 if not sid.startswith("cs_"):raise HTTPException(400,"Sesión de pago inválida.")
 if not STRIPE_SECRET_KEY:raise HTTPException(503,"Stripe no está configurado.")
 try:
  s=stripe.checkout.Session.retrieve(sid,expand=["line_items"])
 except stripe.error.StripeError:
  raise HTTPException(502,"No se pudo verificar el pago.")
 if s.get("payment_status")!="paid" or s.get("status")!="complete":
  raise HTTPException(402,"El pago no aparece como completado.")
 items=s.get("line_items",{}).get("data",[])
 if not items:raise HTTPException(402,"No se pudo verificar el producto pagado.")
 price_ids=[x.get("price",{}).get("id") for x in items]
 if STRIPE_PRICE_ID1 and STRIPE_PRICE_ID1 not in price_ids:
  raise HTTPException(402,"El producto pagado no corresponde a este servicio.")
 old=PAYMENT_TOKENS.get(sid)
 if old and session_valid(old["token"]):
  token=old["token"]
 else:
  token=new_session()
  PAYMENT_TOKENS[sid]={"token":token,"created_at":iso(now()),"expires_at":SESSIONS[token]["expires_at"]}
 return {"success":True,"token":token,"service_token":token,"expires_at":SESSIONS[token]["expires_at"],"minutes":SESSION_MINUTES}

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request:Request):
 body=await request.body()
 sig=request.headers.get("stripe-signature")
 if not STRIPE_WEBHOOK_SECRET:
  raise HTTPException(503,"Stripe webhook is not configured.")
 try:event=stripe.Webhook.construct_event(body,sig,STRIPE_WEBHOOK_SECRET)
 except Exception:raise HTTPException(400,"Invalid Stripe webhook.")
 if event.get("type")=="checkout.session.completed":
  obj=event.get("data",{}).get("object",{})
  sid=obj.get("id")
  if sid and obj.get("payment_status")=="paid":
   PAYMENT_TOKENS.setdefault(sid,{"webhook_seen":True,"created_at":iso(now())})
 return {"status":"received"}

@app.post("/api/v1/flight/search")
@app.post("/api/v1/flight/search-external")
def flight_search(payload:FlightSearchRequest):
 language=lang(payload.language)
 origin=clean(payload.origin)
 destination=clean(payload.destination)
 if not origin and payload.natural_query:
  q=clean(payload.natural_query)
 else:q=""
 try:
  if payload.natural_query and not origin and not destination:
   result=flight_engine.search_external(natural_query=payload.natural_query,language=language,session_token=payload.session_token)
  else:
   result=flight_engine.search(origin=origin,destination=destination,departure_date=clean(payload.departure_date),return_date=clean(payload.return_date),airline=clean(payload.airline),cabin=clean(payload.cabin),fare=clean(payload.fare),passengers=max(1,payload.passengers),stops=payload.stops,language=language)
 except Exception:
  result={"success":True,"flights":[],"results":[],"confirmed_flights":[],"live_results_available":False}
 result["legal_notice"]=legal(language)
 return result

@app.post("/api/v1/flight/understand")
def flight_understand(payload:FlightUnderstandRequest):
 language=lang(payload.language)
 try:
  result=flight_engine.understand(
   origin=clean(payload.origin),destination=clean(payload.destination),
   departure_date=clean(payload.departure_date),return_date=clean(payload.return_date),
   airline=clean(payload.airline),cabin=clean(payload.cabin),fare=clean(payload.fare),
   passengers=max(1,payload.passengers),stops=payload.stops,language=language
  )
 except Exception:
  result={"success":True,"understood":{},"sources":[],"live_results_available":False}
 u=result.get("understood",{})
 if isinstance(u,dict):
  result["understood_text"]=(
   f"Origen: {u.get('origin') or 'no indicado'} | Destino: {u.get('destination') or 'no indicado'} | "
   f"Fecha: {u.get('departure_date') or 'no indicada'} | Regreso: {u.get('return_date') or 'no indicado'} | "
   f"Aerolínea: {u.get('airline') or 'no indicada'}"
   if language=="es" else
   f"Origin: {u.get('origin') or 'not provided'} | Destination: {u.get('destination') or 'not provided'} | "
   f"Date: {u.get('departure_date') or 'not provided'} | Return: {u.get('return_date') or 'not provided'} | "
   f"Airline: {u.get('airline') or 'not provided'}"
  )
 result["legal_notice"]=legal(language)
 return result

@app.post("/api/v1/consultar-articulo")
@app.post("/api/v1/item/check")
def item_check(payload:ItemCheckRequest):
 language=lang(payload.language)
 item=clean(payload.item_description,1000)
 if not item:raise HTTPException(422,"Escribe el artículo que deseas consultar.")
 result=battery_result(payload)
 if result is None:
  kwargs={
   "item":item,"item_description":item,"airline":clean(payload.airline),
   "baggage_type":clean(payload.baggage_type),"origin":clean(payload.origin),
   "destination":clean(payload.destination),"quantity":payload.quantity,
   "wh":payload.wh,"volts":payload.volts,"ah":payload.ah,"mah":payload.mah,
   "spare":payload.spare,"language":language,"registry":REGISTRY
  }
  result=rules_call("advise",**kwargs)
 if not isinstance(result,dict):
  result=fallback_item(item,language)
 sources=result.get("official_sources") or result.get("sources") or []
 result["official_sources"]=normalize_sources(sources)
 result["official_links"]=result["official_sources"]
 result["legal_notice"]=legal(language)
 result.setdefault("source_reference","TSA / FAA / autoridad o aerolínea aplicable")
 result.setdefault("next_action",("Confirm the applicable official rule before travel." if language=="en" else "Confirma la regla oficial aplicable antes de viajar."))
 return result

@app.get("/api/v1/rules")
def rules(language:str="es"):
 if RULE_REPO is not None:
  for name in ("to_dicts","list_rules"):
   fn=getattr(RULE_REPO,name,None)
   if callable(fn):
    try:return {"version":VERSION,"language":lang(language),"rules":fn()}
    except Exception:pass
 return {"version":VERSION,"language":lang(language),"rules":[]}

@app.post("/api/v1/item/teach")
def item_teach(payload:ItemCheckRequest):
 language=lang(payload.language)
 item=clean(payload.item_description)
 d=rules_call("explain_term",item=item,language=language,registry=REGISTRY)
 if not isinstance(d,dict):
  d={"term":item,"explanation":("No tenemos una explicación específica todavía." if language=="es" else "A specific explanation is not available yet."),"official_sources":[]}
 d["official_sources"]=normalize_sources(d.get("official_sources") or d.get("sources"))
 d["legal_notice"]=legal(language)
 return d

@app.get("/api/v1/official-sources")
def official_sources(language:str="es",airline:str="",origin:str="",destination:str=""):
 d=get_route_sources(clean(origin),clean(destination),clean(airline),lang(language))
 d["sources"]=normalize_sources(d.get("sources"))
 d["airline_sources"]=normalize_sources(d.get("airline_sources"))
 d["charter_sources"]=normalize_sources(d.get("charter_sources"))
 d["legal_notice"]=legal(language)
 return d

@app.post("/api/v1/flight/sources")
def flight_sources(payload:FlightSearchRequest):
 return official_sources(payload.language,payload.airline,payload.origin,payload.destination)

@app.get("/api/v1/cuba/official")
def cuba_official(language:str="es",origin:str="",destination:str="Cuba"):
 l=lang(language)
 try:d=flight_engine.cuba_sources(origin,destination,"",l)
 except Exception:
  d={"success":True,"sources":normalize_sources(registry_call("cuba_sources")),"charter_sources":[]}
 d["sources"]=normalize_sources(d.get("sources"))
 d["official_sources"]=d["sources"]
 d["charter_sources"]=normalize_sources(d.get("charter_sources"))
 d["legal_notice"]=legal(l)
 d["next_action"]=("Review the official Cuba entry sources and verify requirements for your nationality and travel date." if l=="en" else "Revisa las fuentes oficiales de entrada a Cuba y confirma los requisitos según tu nacionalidad y fecha de viaje.")
 return d

@app.post("/api/v1/cuba/official")
def cuba_official_post(payload:CubaRequest):
 return cuba_official(payload.language,payload.origin,payload.destination or "Cuba")

@app.get("/api/v1/cuba/visa")
def cuba_visa(language:str="es"):
 l=lang(language)
 src=normalize_sources(registry_call("cuba_sources"))
 urls=[x for x in src if "visa" in (x.get("id","")+" "+x.get("name","")).lower()]
 return {"success":True,"language":l,"sources":urls or src,"legal_notice":legal(l)}

@app.get("/api/v1/cuba/dviajeros")
def cuba_dviajeros(language:str="es"):
 l=lang(language)
 src=normalize_sources(registry_call("cuba_sources"))
 urls=[x for x in src if "viajero" in (x.get("id","")+" "+x.get("name","")).lower() or "dviajeros" in (x.get("url","")).lower()]
 return {"success":True,"language":l,"sources":urls or src,"legal_notice":legal(l)}

@app.post("/api/v1/cuba/practice")
def cuba_practice(payload:PracticeRequest):
 l=lang(payload.language)
 if l=="en":
  steps=[
   {"step":1,"title":"Identify your travel situation","text":"Confirm nationality, passport situation, destination and travel date."},
   {"step":2,"title":"Check the official entry process","text":"Review the current Cuba entry requirements and the official D’Viajeros process."},
   {"step":3,"title":"Check visa requirements","text":"Confirm the visa or eVisa route that applies to your nationality and circumstances."},
   {"step":4,"title":"Review baggage","text":"Check airline baggage rules separately from Cuba entry/import rules."},
   {"step":5,"title":"Verify before submitting","text":"Use the official source before completing the real process."}
  ]
 else:
  steps=[
   {"step":1,"title":"Identifica tu situación de viaje","text":"Confirma nacionalidad, situación del pasaporte, destino y fecha de viaje."},
   {"step":2,"title":"Revisa el proceso oficial de entrada","text":"Consulta los requisitos vigentes de entrada a Cuba y el proceso oficial D’Viajeros."},
   {"step":3,"title":"Revisa la visa","text":"Confirma qué visa o eVisa corresponde a tu nacionalidad y circunstancias."},
   {"step":4,"title":"Revisa el equipaje","text":"Comprueba por separado las reglas de equipaje de la aerolínea y las reglas de entrada/importación de Cuba."},
   {"step":5,"title":"Verifica antes de enviar","text":"Usa la fuente oficial antes de completar el proceso real."}
  ]
 return {"success":True,"simulation":True,"practice_notice":("May Roga practice — not the official Cuba process." if l=="en" else "Práctica de May Roga — no es el proceso oficial de Cuba."),"steps":steps,"sources":cuba_official(l)["sources"],"legal_notice":legal(l)}

@app.post("/api/v1/practice")
def practice(payload:PracticeRequest):
 l=lang(payload.language)
 airline=clean(payload.airline)
 sources=normalize_sources(registry_call("official_for_airline",airline)) if airline else []
 if l=="en":
  steps=[
   {"step":1,"title":"Identify the airline","text":"Confirm the airline shown on your itinerary."},
   {"step":2,"title":"Prepare the flight details","text":"Practice entering origin, destination, dates and passengers."},
   {"step":3,"title":"Review baggage","text":"Practice checking carry-on and checked-baggage rules for the airline and fare."},
   {"step":4,"title":"Review special items","text":"Check batteries, liquids, medical items or other special articles separately."},
   {"step":5,"title":"Verify on the official site","text":"The practice is not the airline's official system. Confirm the real process before submitting anything."}
  ]
 else:
  steps=[
   {"step":1,"title":"Identifica la aerolínea","text":"Confirma la aerolínea que aparece en tu itinerario."},
   {"step":2,"title":"Prepara los datos del vuelo","text":"Practica cómo introducir origen, destino, fechas y pasajeros."},
   {"step":3,"title":"Revisa el equipaje","text":"Practica la revisión del equipaje de cabina y facturado según aerolínea y tarifa."},
   {"step":4,"title":"Revisa artículos especiales","text":"Comprueba por separado baterías, líquidos, artículos médicos u otros objetos especiales."},
   {"step":5,"title":"Verifica en el sitio oficial","text":"La práctica no es el sistema oficial de la aerolínea. Confirma el proceso real antes de enviar datos."}
  ]
 return {"success":True,"simulation":True,"practice_notice":("May Roga practice — not an official airline system." if l=="en" else "Práctica de May Roga — no es el sistema oficial de la aerolínea."),"airline":airline,"steps":steps,"sources":sources,"legal_notice":legal(l)}

@app.get("/api/v1/guide")
def guide(language:str="es"):
 l=lang(language)
 if l=="en":
  sections=[
   {"title":"1. Prepare the trip","text":"Have your origin, destination, dates, airline and passenger information available."},
   {"title":"2. Understand baggage","text":"A carry-on, personal item and checked bag are different categories. The permitted quantity, size and weight can depend on the airline and fare."},
   {"title":"3. Check special items","text":"Batteries, power banks, liquids, aerosols, food, medicines, tools and other special items may have additional rules."},
   {"title":"4. Check the route","text":"Security rules, airline rules and destination-entry rules are different layers. Do not use one as a substitute for another."},
   {"title":"5. Verify before travel","text":"Open the applicable official source and confirm the rule for your exact trip."}
  ]
 else:
  sections=[
   {"title":"1. Prepara el viaje","text":"Ten a mano origen, destino, fechas, aerolínea y datos de los pasajeros."},
   {"title":"2. Entiende el equipaje","text":"El artículo personal, el equipaje de cabina y la maleta facturada son categorías diferentes. La cantidad, peso y medidas pueden depender de la aerolínea y la tarifa."},
   {"title":"3. Revisa artículos especiales","text":"Baterías, power banks, líquidos, aerosoles, alimentos, medicamentos, herramientas y otros artículos pueden tener reglas adicionales."},
   {"title":"4. Revisa la ruta","text":"Las reglas de seguridad, las reglas de la aerolínea y las reglas de entrada del destino son capas diferentes. Una no sustituye a otra."},
   {"title":"5. Verifica antes de viajar","text":"Abre la fuente oficial aplicable y confirma la regla para tu viaje concreto."}
  ]
 return {"success":True,"language":l,"sections":sections,"legal_notice":legal(l)}

@app.get("/api/v1/baggage")
def baggage(language:str="es",airline:str="",origin:str="",destination:str=""):
 l=lang(language)
 d=get_route_sources(origin,destination,airline,l)
 return {"success":True,"language":l,"airline":airline,"sources":normalize_sources(d.get("sources"))+normalize_sources(d.get("airline_sources")),"next_action":("Check the airline's current baggage allowance for your fare." if l=="en" else "Consulta la franquicia de equipaje vigente de tu aerolínea para tu tarifa."),"legal_notice":legal(l)}

@app.get("/api/v1/terms/{term}")
def term(term:str,language:str="es"):
 l=lang(language)
 d=rules_call("explain_term",item=clean(term),language=l,registry=REGISTRY)
 if not isinstance(d,dict):d={"term":term,"explanation":term,"official_sources":[]}
 d["official_sources"]=normalize_sources(d.get("official_sources") or d.get("sources"))
 d["legal_notice"]=legal(l)
 return d

@app.exception_handler(Exception)
async def unhandled(request:Request,exc:Exception):
 return JSONResponse(status_code=500,content={"detail":"No se pudo completar la solicitud. Intenta nuevamente."})

@app.on_event("startup")
async def startup():
 cleanup()
