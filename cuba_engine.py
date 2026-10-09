# cuba_engine.py | QQL | ¿QUÉ QUIERES LLEVAR?
from __future__ import annotations
import json,os,re,urllib.request
from typing import Any

VERSION="17.1.0"
APP="¿QUÉ QUIERES LLEVAR?"
GEMINI_API_KEY=os.getenv("GEMINI_API_KEY","").strip()
GEMINI_MODEL=os.getenv("GEMINI_MODEL","gemini-2.5-flash")

OFFICIAL_URLS={
 "dviajeros":"https://dviajeros.mitrans.gob.cu/",
 "visa":"https://evisacuba.cu/",
 "evisa":"https://evisacuba.cu/",
 "consular":"https://misiones.cubaminrex.cu/",
 "flights":"https://www.google.com/travel/flights",
 "tsa":"https://www.tsa.gov/travel/security-screening/whatcanibring/all",
 "faa":"https://www.faa.gov/hazmat/packsafe",
 "iata":"https://www.iata.org/"
}

SOURCES=[
 {"id":"dviajeros","name":"D'Viajeros","title":"Formulario de entrada a Cuba","url":OFFICIAL_URLS["dviajeros"],"official":True,"type":"entrada"},
 {"id":"evisa","name":"eVisa Cuba","title":"Visa electrónica para Cuba","url":OFFICIAL_URLS["evisa"],"official":True,"type":"visa"},
 {"id":"cubaminrex","name":"Ministerio de Relaciones Exteriores de Cuba","title":"Información consular","url":OFFICIAL_URLS["consular"],"official":True,"type":"consular"},
 {"id":"google_flights","name":"Google Flights","title":"Búsqueda de vuelos","url":OFFICIAL_URLS["flights"],"official":False,"type":"vuelos"},
 {"id":"tsa","name":"TSA","title":"Información sobre artículos y equipaje","url":OFFICIAL_URLS["tsa"],"official":True,"type":"equipaje"},
 {"id":"faa","name":"FAA","title":"Baterías y seguridad aérea","url":OFFICIAL_URLS["faa"],"official":True,"type":"equipaje"},
 {"id":"iata","name":"IATA","title":"Información general de aerolíneas","url":OFFICIAL_URLS["iata"],"official":True,"type":"vuelos"},
]

AIRLINES=[
 {"id":"american","name":"American Airlines","url":"https://www.aa.com/","source_id":"aa"},
 {"id":"delta","name":"Delta Air Lines","url":"https://www.delta.com/","source_id":"delta"},
 {"id":"southwest","name":"Southwest Airlines","url":"https://www.southwest.com/","source_id":"southwest"},
 {"id":"jetblue","name":"JetBlue","url":"https://www.jetblue.com/","source_id":"jetblue"},
 {"id":"united","name":"United Airlines","url":"https://www.united.com/","source_id":"united"},
 {"id":"spirit","name":"Spirit Airlines","url":"https://www.spirit.com/","source_id":"spirit"},
]

CHARTERS=[
 {"id":"charter_general","name":"Vuelos chárter a Cuba","description":"Consulta el operador, aeropuerto, fecha y disponibilidad antes de comprar.","url":OFFICIAL_URLS["flights"],"source_id":"google_flights"}
]

def _text(v:Any,d=""):
 return d if v is None else str(v).strip()

def _lang(data:Any=None):
 if isinstance(data,dict) and _text(data.get("language") or data.get("lang")).lower().startswith("en"): return "en"
 return "es"

def _localized(lang,es,en):
 return en if lang=="en" else es

def _source(i):
 for x in SOURCES:
  if x["id"]==_text(i): return dict(x)
 return {"id":_text(i),"name":_text(i),"title":_text(i),"url":"","official":False,"type":"general"}

def source_by_id(i): return _source(i)
def get_sources(*a,**k): return [dict(x) for x in SOURCES]
def all_sources(*a,**k): return get_sources()
def official_sources(*a,**k): return [dict(x) for x in SOURCES if x.get("official")]
def answer_sources(*a,**k): return official_sources()
def get_airlines(*a,**k): return [dict(x) for x in AIRLINES]
def get_charters(*a,**k): return [dict(x) for x in CHARTERS]
def official_url(name=""): return OFFICIAL_URLS.get(_text(name).lower(),"")
def sources(*a,**k): return get_sources()

def _sources(ids):
 r=[];seen=set()
 for i in ids:
  if i in seen: continue
  seen.add(i);x=_source(i)
  if x.get("url"): r.append(x)
 return r

def _response(ok=True,message="",data=None,language="es",**extra):
 r={"ok":bool(ok),"success":bool(ok),"message":message,"language":language,"version":VERSION}
 if isinstance(data,dict): r.update(data)
 elif data is not None: r["data"]=data
 r.update(extra)
 return r

def _step(n,tes,xes,ten,xen,url=""):
 return {"step":n,"number":n,"title":tes,"text":xes,"title_es":tes,"text_es":xes,"title_en":ten,"text_en":xen,"url":url}

DVIAJEROS_STEPS=[
 _step(1,"Entra al sitio oficial","Abre D'Viajeros antes de tu viaje.","Open the official site","Open D'Viajeros before your trip.",OFFICIAL_URLS["dviajeros"]),
 _step(2,"Completa tus datos","Escribe los datos que el formulario oficial te solicita.","Enter your information","Enter the information requested by the official form.",OFFICIAL_URLS["dviajeros"]),
 _step(3,"Revisa lo escrito","Mira cada dato antes de continuar y corrige cualquier error.","Review your information","Check each detail before continuing and correct any mistake.",OFFICIAL_URLS["dviajeros"]),
 _step(4,"Termina el formulario","Sigue las instrucciones que aparecen en el sitio oficial.","Finish the form","Follow the instructions shown on the official site.",OFFICIAL_URLS["dviajeros"]),
 _step(5,"Guarda el resultado","Conserva el comprobante o código que te entregue el sitio.","Save the result","Keep the confirmation or code provided by the site.",OFFICIAL_URLS["dviajeros"])
]

def dviajeros_simulation(data=None,**kwargs):
 lang=_lang(data);steps=[]
 for x in DVIAJEROS_STEPS:
  y=dict(x);y["title"]=x["title_en"] if lang=="en" else x["title_es"];y["text"]=x["text_en"] if lang=="en" else x["text_es"];steps.append(y)
 return _response(True,_localized(lang,"Aquí tienes la secuencia sencilla para hacer D'Viajeros en el sitio oficial.","Here is the simple sequence to complete D'Viajeros on the official website."),language=lang,steps=steps,simulation=steps,official_url=OFFICIAL_URLS["dviajeros"],source=_source("dviajeros"))

VISA_ROUTES=[
 {"id":"evisa","name":"Visa electrónica","title_es":"Visa electrónica","title_en":"Electronic visa","description_es":"Consulta y realiza el proceso desde el sitio oficial de eVisa Cuba.","description_en":"Check and complete the process through the official eVisa Cuba website.","url":OFFICIAL_URLS["evisa"]},
 {"id":"consular","name":"Consulado","title_es":"Consulado","title_en":"Consulate","description_es":"Si necesitas la vía consular, consulta las instrucciones actuales del consulado correspondiente.","description_en":"If you need the consular route, check the current instructions from the appropriate consulate.","url":OFFICIAL_URLS["consular"]},
 {"id":"airport","name":"Aeropuerto","title_es":"Aeropuerto","title_en":"Airport","description_es":"Si esta opción está disponible para tu viaje, confirma directamente con la aerolínea antes de viajar.","description_en":"If this option is available for your trip, confirm directly with the airline before traveling.","url":"https://www.miami-airport.com/"}
]

def visa_simulation(data=None,**kwargs):
 lang=_lang(data)
 raw=[
  _step(1,"Revisa qué opción tienes","La forma de obtener la visa puede depender de tu situación y del viaje.","First check which option applies","The way to obtain the visa can depend on your situation and trip.",OFFICIAL_URLS["evisa"]),
  _step(2,"Visa electrónica","Abre el sitio oficial y sigue las instrucciones que aparecen allí.","Electronic visa","Open the official site and follow the instructions shown there.",OFFICIAL_URLS["evisa"]),
  _step(3,"Vía consular","Si corresponde al consulado, usa sus instrucciones actuales antes de preparar documentos o pagos.","Consular route","If the consular route applies, use its current instructions before preparing documents or payment.",OFFICIAL_URLS["consular"]),
  _step(4,"Opción en aeropuerto","Si tu aerolínea ofrece esta posibilidad, confirma antes del viaje cómo funciona y qué debes llevar.","Airport option","If your airline offers this option, confirm before the trip how it works and what you need.","https://www.miami-airport.com/"),
  _step(5,"Guarda tu comprobante","Cuando termines, conserva el resultado que te entregue el proceso.","Save your confirmation","When finished, keep the result provided by the process.",OFFICIAL_URLS["evisa"])
 ]
 steps=[]
 for x in raw:
  y=dict(x);y["title"]=x["title_en"] if lang=="en" else x["title_es"];y["text"]=x["text_en"] if lang=="en" else x["text_es"];steps.append(y)
 routes=[]
 for x in VISA_ROUTES:
  y=dict(x);y["title"]=x["title_en"] if lang=="en" else x["title_es"];y["description"]=x["description_en"] if lang=="en" else x["description_es"];routes.append(y)
 return _response(True,_localized(lang,"Estas son las principales vías de visa. Confirma los requisitos actuales en el sitio oficial.","These are the main visa routes. Confirm current requirements on the official site."),language=lang,steps=steps,simulation=steps,routes=routes,official_url=OFFICIAL_URLS["evisa"],source=_source("evisa"),sources=_sources(["evisa","cubaminrex"]))

def practice_scenario(data=None,**kwargs):
 s=_text(data.get("scenario") or data.get("type") or data.get("kind"),"dviajeros").lower() if isinstance(data,dict) else "dviajeros"
 return visa_simulation(data) if s in ("visa","evisa") else dviajeros_simulation(data)

def dviajeros_analysis(data=None,**kwargs): return dviajeros_simulation(data,**kwargs)
def visa_analysis(data=None,**kwargs): return visa_simulation(data,**kwargs)

def document_analysis(data=None,**kwargs):
 lang=_lang(data)
 docs=[
  {"id":"passport","name":"Pasaporte","title_es":"Pasaporte","title_en":"Passport","description_es":"Revisa que tengas tu pasaporte y que cumpla las condiciones aplicables a tu viaje.","description_en":"Make sure you have your passport and that it meets the conditions applicable to your trip."},
  {"id":"dviajeros","name":"D'Viajeros","title_es":"D'Viajeros","title_en":"D'Viajeros","description_es":"Completa el formulario oficial cuando corresponda.","description_en":"Complete the official form when applicable."},
  {"id":"visa","name":"Visa","title_es":"Visa para Cuba","title_en":"Visa for Cuba","description_es":"Confirma qué vía de visa corresponde a tu situación.","description_en":"Confirm which visa route applies to your situation."}
 ]
 for x in docs:
  x["title"]=x["title_en"] if lang=="en" else x["title_es"];x["description"]=x["description_en"] if lang=="en" else x["description_es"]
 return _response(True,_localized(lang,"Guía de documentos","Document guidance"),language=lang,documents=docs,sources=_sources(["dviajeros","evisa","cubaminrex"]))

def baggage_rules(data=None,**kwargs):
 lang=_lang(data)
 carry={"title":_localized(lang,"Equipaje de mano","Carry-on baggage"),"text":_localized(lang,"Las medidas, peso y cantidad permitidos dependen de la aerolínea y del boleto.","Size, weight and quantity depend on the airline and ticket.")}
 checked={"title":_localized(lang,"Equipaje facturado","Checked baggage"),"text":_localized(lang,"El peso, tamaño y cantidad dependen de la aerolínea y del boleto.","Weight, size and quantity depend on the airline and ticket.")}
 msg=_localized(lang,"Para saber exactamente cuánto puedes llevar, revisa las condiciones de tu aerolínea.","To know exactly what you can bring, check your airline's conditions.")
 return _response(True,msg,language=lang,carry_on=carry,checked=checked,important=msg,sources=_sources(["tsa","faa"]))

def baggage_analysis(data=None,**kwargs): return baggage_rules(data,**kwargs)

def _fallback_item(item,lang):
 return {
  "item":item,
  "answer":_localized(lang,"Revisa las reglas oficiales de equipaje y las condiciones de tu aerolínea antes de viajar.","Check the official baggage rules and your airline's conditions before traveling."),
  "allowed":None,"carry_on":None,"checked":None,
  "reason":_localized(lang,"La regla exacta depende del artículo y de los requisitos vigentes.","The exact rule depends on the item and current requirements."),
  "sources":_sources(["tsa","faa"])
 }

def _gemini_prompt(item,lang):
 return f"""Travel orientation assistant. User item: {item}
Language: {lang}
Do not invent rules. Do not claim certainty when unclear. Give a short plain-language answer. Separate carry-on and checked baggage when possible. Official rules have priority. Return JSON only with item,answer,allowed,carry_on,checked,reason."""

def _gemini_item(item,lang):
 if not GEMINI_API_KEY:return None
 url=f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
 body={"contents":[{"parts":[{"text":_gemini_prompt(item,lang)}]}],"generationConfig":{"temperature":0.1,"responseMimeType":"application/json"}}
 try:
  req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"},method="POST")
  with urllib.request.urlopen(req,timeout=20) as r: p=json.loads(r.read().decode())
  c=p.get("candidates") or []
  if not c:return None
  t="".join(x.get("text","") for x in c[0].get("content",{}).get("parts",[])).strip()
  t=re.sub(r"^```json\s*|^```\s*|\s*```$","",t,flags=re.I)
  x=json.loads(t)
  if not isinstance(x,dict):return None
  x["item"]=item;x["sources"]=_sources(["tsa","faa"])
  return x
 except Exception:return None

def item_analysis(data=None,**kwargs):
 lang=_lang(data);item=""
 if isinstance(data,dict):item=_text(data.get("item") or data.get("name") or data.get("question"))
 elif data is not None:item=_text(data)
 if not item:return _response(False,_localized(lang,"Escribe el artículo que quieres consultar.","Write the item you want to check."),language=lang)
 ai=_gemini_item(item,lang)
 if ai:return _response(True,ai.get("answer",""),language=lang,item=item,result=ai,sources=ai.get("sources",_sources(["tsa","faa"])))
 x=_fallback_item(item,lang)
 return _response(True,x["answer"],language=lang,item=item,result=x,**x)

def item_check(data=None,**kwargs): return item_analysis(data,**kwargs)

def analyze_flight(data=None,**kwargs):
 lang=_lang(data);origin="";destination="Cuba";date=""
 if isinstance(data,dict):
  origin=_text(data.get("origin") or data.get("from"))
  destination=_text(data.get("destination") or data.get("to"),"Cuba")
  date=_text(data.get("date") or data.get("departure_date") or data.get("departure"))
 return _response(True,_localized(lang,"Usa la búsqueda de vuelos y confirma la ruta directamente con la aerolínea.","Use flight search and confirm the route directly with the airline."),language=lang,origin=origin,destination=destination,date=date,search_url=OFFICIAL_URLS["flights"],airlines=get_airlines(),charters=get_charters(),sources=_sources(["google_flights"]))

def flight_analysis(data=None,**kwargs): return analyze_flight(data,**kwargs)

def booking_simulation(data=None,**kwargs):
 lang=_lang(data)
 raw=[
  _step(1,"Busca el vuelo","Busca opciones para tu ruta.","Search for the flight","Search options for your route.",OFFICIAL_URLS["flights"]),
  _step(2,"Abre la página de la aerolínea","Revisa la información directamente con la aerolínea.","Open the airline website","Review the information directly with the airline.",""),
  _step(3,"Revisa el vuelo","Comprueba fecha, horario, pasajeros y equipaje.","Review the flight","Check the date, time, passengers and baggage.",""),
  _step(4,"Compra solo si quieres","La aplicación no compra ni paga vuelos.","Buy only if you want to","This application does not buy or pay for flights.","")
 ]
 steps=[]
 for x in raw:
  y=dict(x);y["title"]=x["title_en"] if lang=="en" else x["title_es"];y["text"]=x["text_en"] if lang=="en" else x["text_es"];steps.append(y)
 return _response(True,_localized(lang,"Simulación de preparación. No es una compra real.","Preparation simulation. This is not a real purchase."),language=lang,steps=steps,simulation=steps,official=False,sources=_sources(["google_flights"]))

def booking_analysis(data=None,**kwargs): return booking_simulation(data,**kwargs)

def connection_analysis(data=None,**kwargs):
 lang=_lang(data)
 return _response(True,_localized(lang,"Revisa cada tramo, la fecha y el tiempo entre vuelos directamente con la aerolínea.","Check each flight segment, date and connection time directly with the airline."),language=lang,sources=_sources(["google_flights"]))

def airport_analysis(data=None,**kwargs): return analyze_flight(data,**kwargs)

def cuba_check(data=None,**kwargs):
 lang=_lang(data)
 return _response(True,_localized(lang,"Para viajar a Cuba, revisa primero D'Viajeros, la visa que corresponda y tu vuelo.","For travel to Cuba, first check D'Viajeros, the applicable visa and your flight."),language=lang,dviajeros={"url":OFFICIAL_URLS["dviajeros"],"steps":dviajeros_simulation(data).get("steps",[])},visa={"url":OFFICIAL_URLS["evisa"],"routes":VISA_ROUTES},flights={"url":OFFICIAL_URLS["flights"],"airlines":get_airlines(),"charters":get_charters()},sources=_sources(["dviajeros","evisa","cubaminrex","google_flights"]))

def cuba_entry(data=None,**kwargs): return dviajeros_simulation(data,**kwargs)
def cuba_analysis(data=None,**kwargs): return cuba_check(data,**kwargs)

def build_guide(data=None,**kwargs):
 lang=_lang(data)
 d=dviajeros_simulation(data);v=visa_simulation(data)
 return _response(True,_localized(lang,"Guía básica para preparar un viaje a Cuba.","Basic guide for preparing a trip to Cuba."),language=lang,sections=[
  {"id":"dviajeros","title":"D'Viajeros","url":OFFICIAL_URLS["dviajeros"],"steps":d.get("steps",[])},
  {"id":"visa","title":_localized(lang,"Visa para Cuba","Visa for Cuba"),"url":OFFICIAL_URLS["evisa"],"routes":v.get("routes",[]),"steps":v.get("steps",[])},
  {"id":"flights","title":_localized(lang,"Vuelos a Cuba","Flights to Cuba"),"url":OFFICIAL_URLS["flights"],"airlines":get_airlines(),"charters":get_charters()}
 ],sources=_sources(["dviajeros","evisa","cubaminrex","google_flights"]))

def solve(data=None,**kwargs):
 lang=_lang(data);q=""
 if isinstance(data,dict):q=_text(data.get("question") or data.get("query") or data.get("message"))
 if not q:return build_guide(data,**kwargs)
 l=q.lower()
 if "dviajero" in l or "d'viajero" in l:return dviajeros_simulation(data)
 if "visa" in l:return visa_simulation(data)
 if any(x in l for x in ("vuelo","volar","aerolínea","aerolinea","flight")):return analyze_flight(data)
 if any(x in l for x in ("llevar","equipaje","maleta","batería","bateria")):return item_analysis({"language":lang,"item":q})
 return _response(True,_localized(lang,"Revisa D'Viajeros, la visa y el vuelo en los sitios correspondientes.","Check D'Viajeros, the visa and the flight on the corresponding websites."),language=lang,sources=_sources(["dviajeros","evisa","google_flights"]))

def answer(data=None,**kwargs): return solve(data,**kwargs)

def health(*a,**k):
 return {"ok":True,"success":True,"status":"ok","engine":"cuba_engine","version":VERSION,"source_registry_dependency":False,"gemini_configured":bool(GEMINI_API_KEY)}

__all__=[
 "VERSION","APP","SOURCES","AIRLINES","CHARTERS","OFFICIAL_URLS",
 "source_by_id","get_sources","all_sources","official_sources","answer_sources","official_url","get_airlines","get_charters","sources",
 "dviajeros_simulation","dviajeros_analysis","visa_simulation","visa_analysis","practice_scenario","document_analysis",
 "baggage_rules","baggage_analysis","item_analysis","item_check","analyze_flight","flight_analysis",
 "booking_simulation","booking_analysis","connection_analysis","cuba_check","cuba_entry","cuba_analysis",
 "build_guide","solve","answer","health","airport_analysis"
]
