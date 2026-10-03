# cuba_engine.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC | v12.1.0
from __future__ import annotations
import json,re
from copy import deepcopy
from pathlib import Path
from typing import Any,Dict,List

VERSION="12.1.0"
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
 {"id":"xael_charters","name":"Xael Charters","url":"https://www.xaelcharter.com/","category":"charter","country":"United States","description":"Operador/agencia de vuelos charter relacionados con Cuba. Confirma directamente disponibilidad, ruta, equipaje, fechas y condiciones del boleto.","official":True},
 {"id":"aerocuba","name":"Aerocuba","url":"https://www.aerocuba.com/","category":"charter","country":"United States","description":"Fuente de vuelos y servicios relacionados con Cuba. Confirma directamente ruta, disponibilidad, equipaje y condiciones aplicables.","official":True},
 {"id":"cubazul_air_charter","name":"Cubazul Air Charter","url":"https://cubazulaircharter.com/","category":"charter","country":"United States","description":"Fuente de servicios de vuelos charter relacionados con Cuba. Confirma directamente rutas, boleto, equipaje y condiciones aplicables.","official":True},
 {"id":"cuballama_viajes","name":"Cuballama Viajes","url":"https://www.cuballama.com/viajes/vuelos/charters","category":"charter","country":"United States","description":"Sección de vuelos charter de Cuballama Viajes. Confirma directamente disponibilidad, ruta, boleto y condiciones.","official":True}
]

OFFICIAL_SOURCES=[
 {"id":"cuba_minrex","name":"Ministerio de Relaciones Exteriores de Cuba","url":OFFICIAL_MINREX_URL,"category":"government","country":"Cuba","description":"Información oficial relacionada con asuntos consulares, documentación y requisitos aplicables.","official":True},
 {"id":"cuba_aduana","name":"Aduana General de la República de Cuba","url":OFFICIAL_ADUANA_URL,"category":"customs","country":"Cuba","description":"Información oficial sobre aduanas, equipaje, mercancías, importación y restricciones.","official":True},
 {"id":"cuba_mitrans","name":"Ministerio de Transporte de Cuba","url":OFFICIAL_MITRANS_URL,"category":"transport","country":"Cuba","description":"Información oficial relacionada con transporte y procesos vinculados al viaje.","official":True},
 {"id":"cuba_visa","name":"Visa / eVisa Cuba","url":OFFICIAL_VISA_URL,"category":"visa","country":"Cuba","description":"Portal oficial indicado para información y proceso de visa/eVisa cubana.","official":True},
 {"id":"dviajeros","name":"D’Viajeros","url":OFFICIAL_DVIAJEROS_URL,"category":"entry","country":"Cuba","description":"Portal oficial para el proceso D’Viajeros y la información requerida al viajero.","official":True}
]

def _text(v:Any)->str:
 return str(v or "").strip()

def _norm(v:Any)->str:
 return re.sub(r"\s+"," ",_text(v).lower()).strip()

def _bool(v:Any)->bool:
 if isinstance(v,bool):return v
 return _norm(v) in {"1","true","yes","y","si","sí","on"}

def _data(request:Any=None,**kwargs)->Dict[str,Any]:
 if request is not None:
  if hasattr(request,"model_dump"):
   try:return request.model_dump()
   except Exception:pass
  if isinstance(request,dict):return dict(request)
 return dict(kwargs)

def _load_json(path:Path)->Dict[str,Any]:
 try:
  if not path.exists():return {}
  with path.open("r",encoding="utf-8") as f:
   value=json.load(f)
  return value if isinstance(value,dict) else {}
 except Exception:
  return {}

def _missing(data:Dict[str,Any],fields:List[str])->List[str]:
 out=[]
 for field in fields:
  value=data.get(field)
  if value is None or (isinstance(value,str) and not value.strip()):
   out.append(field)
 return out

def _status(missing:List[str])->str:
 return "INCOMPLETE" if missing else "READY"

def _language(language:str)->str:
 return "en" if _norm(language) in {"en","english","inglés","ingles"} else "es"

def _source(source:Dict[str,Any],language:str="es")->Dict[str,Any]:
 d=deepcopy(source)
 if _language(language)=="en":
  names={
   "dviajeros":"D’Viajeros",
   "cuba_visa":"Cuba Visa / eVisa",
   "cuba_minrex":"Ministry of Foreign Affairs of Cuba",
   "cuba_aduana":"General Customs of the Republic of Cuba",
   "cuba_mitrans":"Ministry of Transportation of Cuba"
  }
  descriptions={
   "dviajeros":"Official portal for the D’Viajeros process.",
   "cuba_visa":"Official portal indicated for Cuba visa/eVisa information and process.",
   "cuba_minrex":"Official information related to consular matters and requirements.",
   "cuba_aduana":"Official information about customs, baggage, goods and restrictions.",
   "cuba_mitrans":"Official information related to transportation.",
  }
  if d.get("id") in names:d["name"]=names[d["id"]]
  if d.get("id") in descriptions:d["description"]=descriptions[d["id"]]
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
 text=_norm(f"{origin} {destination}")
 aliases=("cuba","havana","habana","varadero","camaguey","camagüey","holguin","holguín","santiago de cuba","santa clara","cayo coco","cayo largo")
 return any(x in text for x in aliases)

def cuba_sources(language:str="es")->List[Dict[str,Any]]:
 return get_official_sources(language)

def evaluate_visa(request:Any=None,**kwargs)->Dict[str,Any]:
 data=_data(request,**kwargs)
 nationality=_text(data.get("nationality"))
 residence=_text(data.get("country_of_residence") or data.get("residence_country"))
 passport_country=_text(data.get("passport_country"))
 purpose=_text(data.get("purpose") or data.get("travel_purpose"))
 entry_type=_text(data.get("entry_type") or data.get("flight_type"))
 has_passport=_bool(data.get("has_passport"))
 if not has_passport:
  has_passport=bool(_text(data.get("passport_number")) or data.get("has_cuban_passport") is True or data.get("has_other_passport") is True)
 passport_valid=_bool(data.get("passport_valid"))
 if not passport_valid:
  passport_valid=bool(_text(data.get("passport_valid_until")))
 dual=_bool(data.get("dual_nationality") or data.get("dual_citizen"))
 cuban=_bool(data.get("cuban_nationality"))
 missing=_missing(data,["nationality","country_of_residence","passport_country","purpose"])
 checks=[
  {"id":"passport","status":"READY" if has_passport else "INCOMPLETE","message":"Pasaporte informado." if has_passport else "Confirma qué pasaporte corresponde a tu viaje."},
  {"id":"passport_validity","status":"READY" if passport_valid else "INCOMPLETE","message":"Vigencia indicada." if passport_valid else "Confirma la vigencia del pasaporte aplicable a tu caso."}
 ]
 if dual or cuban:
  checks.append({"id":"nationality","status":"REVIEW","message":"La nacionalidad cubana o la doble nacionalidad puede cambiar qué documento o condición corresponde. Confirma directamente con la fuente oficial cubana aplicable."})
 if entry_type:
  checks.append({"id":"entry_type","status":"READY","message":f"Tipo de viaje indicado: {entry_type}."})
 if purpose:
  checks.append({"id":"purpose","status":"READY","message":f"Motivo del viaje indicado: {purpose}."})
 status=_status(missing)
 if not has_passport or not passport_valid:status="INCOMPLETE"
 return {
  "module":"visa",
  "status":status,
  "missing_fields":missing,
  "nationality":nationality,
  "country_of_residence":residence,
  "passport_country":passport_country,
  "travel_purpose":purpose,
  "purpose":purpose,
  "entry_type":entry_type,
  "dual_nationality":dual,
  "cuban_nationality":cuban,
  "checks":checks,
  "official_portal":OFFICIAL_VISA_URL,
  "official_submission_completed":False,
  "official_document_issued":False,
  "official_qr_generated":False,
  "source_data_loaded":bool(get_visa_data()),
  "sources":get_official_sources("es")
 }

def evaluate_dviajeros(request:Any=None,**kwargs)->Dict[str,Any]:
 data=_data(request,**kwargs)
 aliases={
  "first_name":["first_name","given_names"],
  "last_name":["last_name","surnames"],
  "nationality":["nationality"],
  "date_of_birth":["date_of_birth","birth_date"],
  "passport_country":["passport_country"],
  "arrival_date":["arrival_date"],
  "airline":["airline"],
  "accommodation":["accommodation","address_destination"],
  "purpose_of_trip":["purpose_of_trip","purpose"]
 }
 normalized={}
 for target,names in aliases.items():
  normalized[target]=""
  for name in names:
   if _text(data.get(name)):
    normalized[target]=_text(data.get(name))
    break
 missing=[k for k,v in normalized.items() if not v]
 modules=[
  {"id":"traveler","title":"Datos del viajero","status":"INCOMPLETE" if any(x in missing for x in ["first_name","last_name","nationality","date_of_birth"]) else "READY"},
  {"id":"passport","title":"Pasaporte","status":"INCOMPLETE" if "passport_country" in missing else "READY"},
  {"id":"arrival","title":"Llegada","status":"INCOMPLETE" if any(x in missing for x in ["arrival_date","airline"]) else "READY"},
  {"id":"accommodation","title":"Hospedaje","status":"INCOMPLETE" if "accommodation" in missing else "READY"},
  {"id":"purpose","title":"Motivo del viaje","status":"INCOMPLETE" if "purpose_of_trip" in missing else "READY"},
  {"id":"review","title":"Revisión","status":"INCOMPLETE" if missing else "READY"}
 ]
 return {
  "module":"dviajeros",
  "status":_status(missing),
  "missing_fields":missing,
  "normalized":normalized,
  "modules":modules,
  "submission_status":"READY_FOR_OFFICIAL_FORM" if not missing else "INCOMPLETE",
  "official_portal":OFFICIAL_DVIAJEROS_URL,
  "official_submission_completed":False,
  "official_qr_generated":False,
  "source_data_loaded":bool(get_dviajeros_data()),
  "sources":get_official_sources("es")
 }

def visa_information(language:str="es")->Dict[str,Any]:
 en=_language(language)=="en"
 return {
  "module":"visa",
  "name":"Cuba Visa / eVisa" if en else "Visa cubana / eVisa",
  "official_portal":OFFICIAL_VISA_URL,
  "data":get_visa_data(),
  "sources":get_official_sources(language)
 }

def dviajeros_information(language:str="es")->Dict[str,Any]:
 en=_language(language)=="en"
 return {
  "module":"dviajeros",
  "name":"D’Viajeros",
  "official_portal":OFFICIAL_DVIAJEROS_URL,
  "data":get_dviajeros_data(),
  "sources":get_official_sources(language)
 }

def official_information(language:str="es")->Dict[str,Any]:
 return {
  "language":_language(language),
  "visa":OFFICIAL_VISA_URL,
  "dviajeros":OFFICIAL_DVIAJEROS_URL,
  "minrex":OFFICIAL_MINREX_URL,
  "aduana":OFFICIAL_ADUANA_URL,
  "mitrans":OFFICIAL_MITRANS_URL,
  "sources":get_official_sources(language),
  "charter_sources":get_charter_sources(language)
 }

def simulation_steps(mode:str="visa",language:str="es")->List[str]:
 en=_language(language)=="en"
 mode=_norm(mode)
 if mode in {"dviajeros","d'viajeros","dviajero"}:
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
 en=_language(language)=="en"
 is_dv=_norm(mode) in {"dviajeros","d'viajeros","dviajero"}
 return {
  "simulation":True,
  "official_submission":False,
  "official_document_issued":False,
  "official_qr_generated":False,
  "mode":"dviajeros" if is_dv else "visa",
  "title":"D’Viajeros" if is_dv else ("Cuba Visa / eVisa" if en else "Visa/eVisa de Cuba"),
  "notice":"PRACTICE SIMULATION — NOT THE OFFICIAL SITE." if en else "SIMULACIÓN DE PRÁCTICA — NO ES EL SITIO OFICIAL.",
  "steps":simulation_steps("dviajeros" if is_dv else "visa",language),
  "official_url":OFFICIAL_DVIAJEROS_URL if is_dv else OFFICIAL_VISA_URL,
  "sources":get_official_sources(language)
 }

def public_config(language:str="es")->Dict[str,Any]:
 return {
  "app":{"name":APP_NAME,"version":VERSION},
  "cuba":{
   "visa_url":OFFICIAL_VISA_URL,
   "dviajeros_url":OFFICIAL_DVIAJEROS_URL,
   "minrex_url":OFFICIAL_MINREX_URL,
   "aduana_url":OFFICIAL_ADUANA_URL,
   "mitrans_url":OFFICIAL_MITRANS_URL,
   "official_sources":get_official_sources(language),
   "charter_sources":get_charter_sources(language)
  },
  "simulation":{"enabled":True,"official_submission":False}
 }

def disclaimer(language:str="es")->Dict[str,str]:
 if _language(language)=="en":
  return {"text":"¿QUÉ QUIERES LLEVAR? is an independent preparation and orientation service from May Roga LLC. It is not the Government of Cuba, an airline, airport, customs authority, immigration authority or consulate. Simulations do not submit official forms, make payments, issue visas or generate official QR codes. Requirements can change and must be confirmed through the applicable official source."}
 return {"text":"¿QUÉ QUIERES LLEVAR? es un servicio independiente de preparación y orientación de May Roga LLC. No es el Gobierno de Cuba, una aerolínea, aeropuerto, autoridad aduanera, autoridad migratoria ni consulado. Las simulaciones no envían formularios oficiales, no realizan pagos, no emiten visas ni generan códigos QR oficiales. Los requisitos pueden cambiar y deben confirmarse mediante la fuente oficial correspondiente."}

class CubaEngine:
 def __init__(self):
  self.version=VERSION
  self.app_name=APP_NAME
 def evaluate_visa(self,request:Any)->Dict[str,Any]:
  return evaluate_visa(request)
 def evaluate_dviajeros(self,request:Any)->Dict[str,Any]:
  return evaluate_dviajeros(request)
 def get_visa_data(self)->Dict[str,Any]:
  return get_visa_data()
 def get_dviajeros_data(self)->Dict[str,Any]:
  return get_dviajeros_data()
 def get_charter_sources(self,language:str="es")->List[Dict[str,Any]]:
  return get_charter_sources(language)
 def get_official_sources(self,language:str="es")->List[Dict[str,Any]]:
  return get_official_sources(language)
 def official_information(self,language:str="es")->Dict[str,Any]:
  return official_information(language)
 def visa_information(self,language:str="es")->Dict[str,Any]:
  return visa_information(language)
 def dviajeros_information(self,language:str="es")->Dict[str,Any]:
  return dviajeros_information(language)
 def simulation(self,mode:str="visa",language:str="es")->Dict[str,Any]:
  return simulation(mode,language)
 def public_config(self,language:str="es")->Dict[str,Any]:
  return public_config(language)
 def disclaimer(self,language:str="es")->Dict[str,str]:
  return disclaimer(language)
 def is_cuba_route(self,origin:str="",destination:str="")->bool:
  return is_cuba_route(origin,destination)

engine=CubaEngine()
cuba_engine=engine

__all__=[
 "VERSION","APP_NAME","OFFICIAL_VISA_URL","OFFICIAL_DVIAJEROS_URL",
 "OFFICIAL_MINREX_URL","OFFICIAL_ADUANA_URL","OFFICIAL_MITRANS_URL",
 "CHARTER_SOURCES","OFFICIAL_SOURCES","get_charter_sources",
 "get_official_sources","charter_sources","official_sources",
 "get_visa_data","get_dviajeros_data","is_cuba_route","cuba_sources",
 "evaluate_visa","evaluate_dviajeros","visa_information",
 "dviajeros_information","official_information","simulation_steps",
 "simulation","public_config","disclaimer","CubaEngine","engine","cuba_engine"
]
