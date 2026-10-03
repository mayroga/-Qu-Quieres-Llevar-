from __future__ import annotations
import json,os,re
from copy import deepcopy
from pathlib import Path
from typing import Any,Dict,List,Optional

VERSION="12.0.0"
APP_NAME="¿QUÉ QUIERES LLEVAR?"
BASE_DIR=Path(__file__).resolve().parent
DATA_DIR=BASE_DIR/"data"
VISA_FILE=DATA_DIR/"cuba_visa.json"
DVIJEROS_FILE=DATA_DIR/"dviajeros.json"

OFFICIAL_VISA_URL="https://evisacuba.cu/"
OFFICIAL_DVIAJEROS_URL="https://dviajeros.mitrans.gob.cu/"
OFFICIAL_MINREX_URL="https://cubaminrex.cu/"
OFFICIAL_ADUANA_URL="https://www.aduana.gob.cu/"
OFFICIAL_MITRANS_URL="https://www.mitrans.gob.cu/"

CHARTER_SOURCES=[
 {"id":"xael_charters","name":"Xael Charters","url":"https://www.xaelcharter.com/","category":"charter","country":"United States","description":"Operador/agencia de vuelos charter relacionado con viajes a Cuba. Confirma directamente disponibilidad, ruta y condiciones.","official":True},
 {"id":"aerocuba","name":"Aerocuba","url":"https://www.aerocuba.com/","category":"charter","country":"United States","description":"Fuente de vuelos y servicios relacionados con Cuba. Confirma directamente las condiciones aplicables.","official":True},
 {"id":"cubazul_air_charter","name":"Cubazul Air Charter","url":"https://cubazulaircharter.com/","category":"charter","country":"United States","description":"Fuente de servicios de vuelos charter relacionados con Cuba. Confirma directamente rutas y condiciones.","official":True},
 {"id":"cuballama_viajes","name":"Cuballama Viajes","url":"https://www.cuballama.com/viajes/vuelos/charters","category":"charter","country":"United States","description":"Sección de vuelos charter de Cuballama Viajes. Confirma directamente disponibilidad y condiciones.","official":True}
]

OFFICIAL_SOURCES=[
 {"id":"cuba_minrex","name":"Ministerio de Relaciones Exteriores de Cuba","url":OFFICIAL_MINREX_URL,"category":"government","country":"Cuba","description":"Información consular y oficial relacionada con Cuba.","official":True},
 {"id":"cuba_aduana","name":"Aduana General de la República de Cuba","url":OFFICIAL_ADUANA_URL,"category":"customs","country":"Cuba","description":"Información oficial de aduanas, equipaje y mercancías.","official":True},
 {"id":"cuba_mitrans","name":"Ministerio de Transporte de Cuba","url":OFFICIAL_MITRANS_URL,"category":"transport","country":"Cuba","description":"Información oficial relacionada con transporte.","official":True},
 {"id":"cuba_visa","name":"Visa / eVisa Cuba","url":OFFICIAL_VISA_URL,"category":"visa","country":"Cuba","description":"Portal indicado para información y proceso de visa/eVisa cubana.","official":True},
 {"id":"dviajeros","name":"D’Viajeros","url":OFFICIAL_DVIAJEROS_URL,"category":"entry","country":"Cuba","description":"Portal oficial utilizado para el proceso D’Viajeros.","official":True}
]

def _text(v:Any)->str:
 return str(v or "").strip()

def _norm(v:Any)->str:
 s=_text(v).lower()
 return re.sub(r"\s+"," ",s)

def _bool(v:Any)->bool:
 if isinstance(v,bool):return v
 return _norm(v) in {"1","true","yes","y","si","sí"}

def _load_json(path:Path)->Dict[str,Any]:
 try:
  if not path.exists():return {}
  with path.open("r",encoding="utf-8") as f:
   d=json.load(f)
  return d if isinstance(d,dict) else {}
 except(Exception,):
  return {}

def _missing(data:Dict[str,Any],fields:List[str])->List[str]:
 out=[]
 for f in fields:
  v=data.get(f)
  if v is None or (isinstance(v,str) and not v.strip()):out.append(f)
 return out

def _status(missing:List[str])->str:
 return "INCOMPLETE" if missing else "READY"

def _source(s:Dict[str,Any],language:str="es")->Dict[str,Any]:
 d=deepcopy(s)
 if language=="en":
  names={"dviajeros":"D’Viajeros","cuba_visa":"Cuba visa / eVisa","cuba_minrex":"Ministry of Foreign Affairs of Cuba","cuba_aduana":"General Customs of the Republic of Cuba","cuba_mitrans":"Ministry of Transportation of Cuba"}
  if d.get("id") in names:d["name"]=names[d["id"]]
 return d

def get_charter_sources(language:str="es")->List[Dict[str,Any]]:
 return [_source(x,language) for x in CHARTER_SOURCES]

def get_official_sources(language:str="es")->List[Dict[str,Any]]:
 return [_source(x,language) for x in OFFICIAL_SOURCES]

def charter_sources(language:str="es")->List[Dict[str,Any]]:
 return get_charter_sources(language)

def official_sources(language:str="es")->List[Dict[str,Any]]:
 return get_official_sources(language)

def get_visa_data()->Dict[str,Any]:
 return _load_json(VISA_FILE)

def get_dviajeros_data()->Dict[str,Any]:
 return _load_json(DVIJEROS_FILE)

def is_cuba_route(origin:str="",destination:str="")->bool:
 t=_norm(f"{origin} {destination}")
 aliases=("cuba","havana","habana","varadero","camaguey","camagüey","holguin","holguín","santiago de cuba","santa clara")
 return any(x in t for x in aliases)

def cuba_sources(language:str="es")->List[Dict[str,Any]]:
 return get_official_sources(language)

def evaluate_visa(request:Any=None,**kwargs)->Dict[str,Any]:
 data=request.model_dump() if hasattr(request,"model_dump") else (dict(request) if isinstance(request,dict) else dict(kwargs))
 nationality=_text(data.get("nationality"))
 residence=_text(data.get("country_of_residence"))
 passport_country=_text(data.get("passport_country"))
 purpose=_text(data.get("travel_purpose"))
 entry_type=_text(data.get("entry_type"))
 has_passport=_bool(data.get("has_passport"))
 passport_valid=_bool(data.get("passport_valid"))
 dual=_bool(data.get("dual_nationality"))
 missing=_missing(data,["nationality","country_of_residence","passport_country","travel_purpose"])
 checks=[]
 checks.append({"id":"passport","status":"READY" if has_passport else "INCOMPLETE","message":"Pasaporte informado." if has_passport else "Debes confirmar que cuentas con el pasaporte correspondiente."})
 checks.append({"id":"passport_validity","status":"READY" if passport_valid else "INCOMPLETE","message":"Vigencia indicada." if passport_valid else "Confirma la vigencia exigida para tu caso."})
 if dual:
  checks.append({"id":"dual_nationality","status":"REVIEW","message":"La doble nacionalidad puede cambiar qué documento o condición corresponde. Confirma tu situación directamente con la fuente oficial cubana aplicable."})
 if entry_type:
  checks.append({"id":"entry_type","status":"READY","message":f"Tipo de entrada indicado: {entry_type}."})
 status=_status(missing)
 if not has_passport or not passport_valid:status="INCOMPLETE"
 return {"module":"visa","status":status,"missing_fields":missing,"nationality":nationality,"country_of_residence":residence,"passport_country":passport_country,"travel_purpose":purpose,"entry_type":entry_type,"dual_nationality":dual,"checks":checks,"official_portal":OFFICIAL_VISA_URL,"official_submission_completed":False,"official_document_issued":False,"official_qr_generated":False,"source_data_loaded":bool(get_visa_data()),"sources":get_official_sources("es")}

def evaluate_dviajeros(request:Any=None,**kwargs)->Dict[str,Any]:
 data=request.model_dump() if hasattr(request,"model_dump") else (dict(request) if isinstance(request,dict) else dict(kwargs))
 required=["first_name","last_name","nationality","date_of_birth","passport_country","arrival_date","airline","accommodation","purpose_of_trip"]
 missing=_missing(data,required)
 modules=[
  {"id":"traveler","title":"Datos del viajero","status":"INCOMPLETE" if any(x in missing for x in ["first_name","last_name","nationality","date_of_birth"]) else "READY"},
  {"id":"passport","title":"Pasaporte","status":"INCOMPLETE" if "passport_country" in missing else "READY"},
  {"id":"arrival","title":"Llegada","status":"INCOMPLETE" if any(x in missing for x in ["arrival_date","airline"]) else "READY"},
  {"id":"accommodation","title":"Hospedaje","status":"INCOMPLETE" if "accommodation" in missing else "READY"},
  {"id":"purpose","title":"Motivo del viaje","status":"INCOMPLETE" if "purpose_of_trip" in missing else "READY"},
  {"id":"review","title":"Revisión","status":"INCOMPLETE" if missing else "READY"}
 ]
 return {"module":"dviajeros","status":_status(missing),"missing_fields":missing,"modules":modules,"submission_status":"READY_FOR_OFFICIAL_FORM" if not missing else "INCOMPLETE","official_portal":OFFICIAL_DVIAJEROS_URL,"official_submission_completed":False,"official_qr_generated":False,"source_data_loaded":bool(get_dviajeros_data()),"sources":get_official_sources("es")}

def visa_information(language:str="es")->Dict[str,Any]:
 return {"module":"visa","name":"Cuba visa / eVisa" if language=="en" else "Visa cubana / eVisa","official_portal":OFFICIAL_VISA_URL,"data":get_visa_data(),"sources":get_official_sources(language)}

def dviajeros_information(language:str="es")->Dict[str,Any]:
 return {"module":"dviajeros","name":"D’Viajeros","official_portal":OFFICIAL_DVIAJEROS_URL,"data":get_dviajeros_data(),"sources":get_official_sources(language)}

def official_information(language:str="es")->Dict[str,Any]:
 return {"language":language,"visa":OFFICIAL_VISA_URL,"dviajeros":OFFICIAL_DVIAJEROS_URL,"sources":get_official_sources(language),"charter_sources":get_charter_sources(language)}

def simulation_steps(mode:str="visa",language:str="es")->List[str]:
 en=language=="en"
 if mode=="dviajeros":
  return [
   "D’Viajeros practice. This is only a simulation." if en else "Práctica de D’Viajeros. Esto es solamente una simulación.",
   "Open the official D’Viajeros portal." if en else "Abre el portal oficial de D’Viajeros.",
   "Identify the information requested by the official form." if en else "Identifica la información que solicita el formulario oficial.",
   "Practice the order of the fields without entering sensitive information." if en else "Practica el orden de los campos sin introducir información sensible.",
   "Review the information before submitting the real form." if en else "Revisa la información antes de enviar el formulario real.",
   "Complete the real process only at the official portal." if en else "Realiza el proceso real solamente en el portal oficial."
  ]
 return [
  "Cuba visa/eVisa practice. This is only a simulation." if en else "Práctica de visa/eVisa de Cuba. Esto es solamente una simulación.",
  "Open the official Cuba visa/eVisa source." if en else "Abre la fuente oficial de visa/eVisa de Cuba.",
  "Check the requirement for your nationality." if en else "Comprueba el requisito según tu nacionalidad.",
  "Review the documents and information requested." if en else "Revisa los documentos y la información solicitada.",
  "Practice the order of the process without submitting anything." if en else "Practica el orden del proceso sin enviar nada.",
  "Complete the real process only through the applicable official source." if en else "Realiza el proceso real solamente mediante la fuente oficial correspondiente."
 ]

def simulation(mode:str="visa",language:str="es")->Dict[str,Any]:
 return {"simulation":True,"official_submission":False,"official_document_issued":False,"official_qr_generated":False,"mode":mode,"title":"D’Viajeros" if mode=="dviajeros" else ("Cuba visa/eVisa" if language=="en" else "Visa/eVisa de Cuba"),"notice":"PRACTICE SIMULATION — NOT THE OFFICIAL SITE." if language=="en" else "SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL.","steps":simulation_steps(mode,language),"official_url":OFFICIAL_DVIAJEROS_URL if mode=="dviajeros" else OFFICIAL_VISA_URL,"sources":get_official_sources(language)}

def public_config(language:str="es")->Dict[str,Any]:
 return {"app":{"name":APP_NAME,"version":VERSION},"cuba":{"visa_url":OFFICIAL_VISA_URL,"dviajeros_url":OFFICIAL_DVIAJEROS_URL,"official_sources":get_official_sources(language),"charter_sources":get_charter_sources(language)},"simulation":{"enabled":True,"official_submission":False}}

def disclaimer(language:str="es")->Dict[str,str]:
 if language=="en":
  return {"text":"¿QUÉ QUIERES LLEVAR? is an independent May Roga LLC preparation and orientation service. It is not the Government of Cuba, an airline, airport, customs authority, immigration authority or consulate. Simulations are educational and do not submit official forms or issue official documents. Requirements can change and must be confirmed through the applicable official source."}
 return {"text":"¿QUÉ QUIERES LLEVAR? es un servicio independiente de preparación y orientación de May Roga LLC. No es el Gobierno de Cuba, una aerolínea, aeropuerto, autoridad aduanera, autoridad migratoria ni consulado. Las simulaciones son educativas y no envían formularios oficiales ni emiten documentos oficiales. Los requisitos pueden cambiar y deben confirmarse mediante la fuente oficial correspondiente."}

class CubaEngine:
 def __init__(self):
  self.version=VERSION
 def evaluate_visa(self,request:Any)->Dict[str,Any]:return evaluate_visa(request)
 def evaluate_dviajeros(self,request:Any)->Dict[str,Any]:return evaluate_dviajeros(request)
 def get_visa_data(self)->Dict[str,Any]:return get_visa_data()
 def get_dviajeros_data(self)->Dict[str,Any]:return get_dviajeros_data()
 def get_charter_sources(self,language:str="es")->List[Dict[str,Any]]:return get_charter_sources(language)
 def get_official_sources(self,language:str="es")->List[Dict[str,Any]]:return get_official_sources(language)
 def simulation(self,mode:str="visa",language:str="es")->Dict[str,Any]:return simulation(mode,language)
 def public_config(self,language:str="es")->Dict[str,Any]:return public_config(language)
 def disclaimer(self,language:str="es")->Dict[str,str]:return disclaimer(language)

engine=CubaEngine()
cuba_engine=engine

__all__=["VERSION","APP_NAME","OFFICIAL_VISA_URL","OFFICIAL_DVIAJEROS_URL","OFFICIAL_MINREX_URL","OFFICIAL_ADUANA_URL","OFFICIAL_MITRANS_URL","CHARTER_SOURCES","OFFICIAL_SOURCES","get_charter_sources","get_official_sources","charter_sources","official_sources","get_visa_data","get_dviajeros_data","is_cuba_route","cuba_sources","evaluate_visa","evaluate_dviajeros","visa_information","dviajeros_information","official_information","simulation_steps","simulation","public_config","disclaimer","CubaEngine","engine","cuba_engine"]
