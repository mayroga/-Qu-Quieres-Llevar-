"use strict";

const APP={
 name:"¿QUÉ QUIERES LLEVAR?",
 version:"8.2.0",
 lang:localStorage.getItem("qql_lang")||"es",
 serviceToken:localStorage.getItem("qql_service_token")||"",
 adminToken:localStorage.getItem("qql_admin_token")||"",
 session:null,
 config:null,
 _bound:false
};

const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
const txt=v=>String(v??"").trim();
const lang=()=>APP.lang==="en"?"en":"es";
const active=()=>!!(APP.serviceToken||APP.adminToken);

function headers(extra={}){
 const h={"Content-Type":"application/json",...extra};
 if(APP.serviceToken)h["X-Service-Token"]=APP.serviceToken;
 if(APP.adminToken)h["X-Admin-Token"]=APP.adminToken;
 return h;
}

function saveTokens(){
 localStorage.setItem("qql_service_token",APP.serviceToken||"");
 localStorage.setItem("qql_admin_token",APP.adminToken||"");
}

function clearTokens(){
 APP.serviceToken="";
 APP.adminToken="";
 APP.session=null;
 saveTokens();
}

function val(id){
 return txt(document.getElementById(id)?.value);
}

function msg(text,type="info"){
 let box=$("#appMessage")||$("#message")||$(".app-message");
 if(!box){
  box=document.createElement("div");
  box.id="appMessage";
  document.body.prepend(box);
 }
 box.className=`app-message ${type}`;
 box.textContent=text;
}

async function api(path,options={},timeout=25000){
 const ctl=new AbortController();
 const tm=setTimeout(()=>ctl.abort(),timeout);
 try{
  const r=await fetch(path,{...options,headers:headers(options.headers||{}),signal:ctl.signal});
  let d={};
  try{d=await r.json()}catch(_){}
  if(!r.ok){
   const e=new Error(d.detail||d.message||`HTTP ${r.status}`);
   e.status=r.status;
   e.data=d;
   throw e;
  }
  return d;
 }catch(e){
  if(e.name==="AbortError")throw new Error(APP.lang==="en"?"The request took too long. Please try again.":"La solicitud tardó demasiado. Intenta nuevamente.");
  throw e;
 }finally{clearTimeout(tm)}
}

function show(name){
 $$(".screen").forEach(x=>x.classList.add("hidden"));
 const x=document.getElementById(name);
 if(x)x.classList.remove("hidden");
 document.body.dataset.view=name;
 window.scrollTo({top:0,behavior:"smooth"});
}

function home(){
 if(active())show("home");
 else show("payment");
}

function requirePaid(){
 if(active())return true;
 show("payment");
 msg(APP.lang==="en"?"Start the service to use the guided tools.":"Activa el servicio para comenzar a usar las herramientas guiadas.","warn");
 return false;
}

const I18N={
 es:{
  title:"¿Qué quieres llevar?",
  subtitle:"Te acompañamos paso a paso para entender tu viaje, tu vuelo, tu aerolínea, tu equipaje y los procesos que necesitas realizar.",
  start:"Empezar",
  flight:"Mi vuelo",
  flightSmall:"Entiende tu itinerario y tu aerolínea",
  item:"¿Qué llevo?",
  itemSmall:"Aprende dónde y cómo llevar cada artículo",
  baggage:"Equipaje",
  baggageSmall:"Aprende a preparar tus maletas",
  airline:"Mi aerolínea",
  airlineSmall:"Aprende a usar su proceso paso a paso",
  simulation:"Practicar",
  simulationSmall:"Simula procesos antes de hacerlos",
  cuba:"Cuba",
  cubaSmall:"Visa, D’Viajeros y preparación",
  guide:"Guía",
  guideSmall:"Organiza tu viaje paso a paso",
  sources:"Fuentes oficiales",
  sourcesSmall:"Encuentra dónde confirmar",
  teach:"Aprender",
  teachSmall:"Entiende palabras y procesos",
  legal:"Aviso legal",
  legalSmall:"Conoce el servicio",
  paymentTitle:"Antes de empezar, conoce el servicio",
  paymentIntro:"¿QUÉ QUIERES LLEVAR? está diseñado para acompañarte cuando quieres viajar pero no sabes exactamente qué hacer, dónde hacerlo o cómo entender lo que ves en una página de una aerolínea, gobierno o proveedor.",
  simulationTitle:"Aprendes practicando",
  simulationText:"La aplicación puede mostrar simulaciones educativas inspiradas en el tipo de proceso que encontrarás en una aerolínea, D’Viajeros, visa u otro servicio. La simulación te enseña antes de entrar al sitio real.",
  paymentNotice:"Es un servicio independiente de May Roga LLC. El pago es único: $15.99 por una sesión de 15 minutos.",
  pay:"Continuar al pago"
 },
 en:{
  title:"What do you want to take?",
  subtitle:"We guide you step by step through your trip, flight, airline, baggage and travel processes.",
  start:"Start",
  flight:"My flight",
  flightSmall:"Understand your itinerary and airline",
  item:"What can I take?",
  itemSmall:"Learn where and how to carry an item",
  baggage:"Baggage",
  baggageSmall:"Learn how to prepare your bags",
  airline:"My airline",
  airlineSmall:"Learn its process step by step",
  simulation:"Practice",
  simulationSmall:"Practice before doing the real process",
  cuba:"Cuba",
  cubaSmall:"Visa, D’Viajeros and preparation",
  guide:"Guide",
  guideSmall:"Prepare your trip step by step",
  sources:"Official sources",
  sourcesSmall:"Find where to verify",
  teach:"Learn",
  teachSmall:"Understand words and processes",
  legal:"Legal notice",
  legalSmall:"About the service",
  paymentTitle:"Before you start, understand the service",
  paymentIntro:"¿QUÉ QUIERES LLEVAR? is designed to guide you when you want to travel but are unsure what to do, where to do it or how to understand an airline, government or provider website.",
  simulationTitle:"Learn by practicing",
  simulationText:"The application can provide educational simulations inspired by the type of process you may encounter with an airline, D’Viajeros, a visa process or another service. The simulation lets you practice before using the real website.",
  paymentNotice:"This is an independent May Roga LLC service. One-time payment: $15.99 for a 15-minute session.",
  pay:"Continue to payment"
 }
};

function translate(){
 const t=I18N[APP.lang]||I18N.es;
 $$("[data-i18n]").forEach(el=>{
  const k=el.dataset.i18n;
  if(t[k]!=null)el.textContent=t[k];
 });
 const b=$("#langBtn");
 if(b)b.textContent=APP.lang==="en"?"ES":"EN";
 document.documentElement.lang=APP.lang;
}

function toggleLang(){
 APP.lang=APP.lang==="es"?"en":"es";
 localStorage.setItem("qql_lang",APP.lang);
 translate();
 loadConfig();
}

async function loadConfig(){
 try{
  APP.config=await api("/api/v1/config",{method:"GET"});
  renderSession();
 }catch(_){}
}

function renderSession(){
 const box=$("#sessionStatus");
 if(!box)return;
 if(APP.session?.active){
  const n=Math.ceil(Number(APP.session.remaining_seconds||0)/60);
  box.textContent=APP.session.admin
   ?(APP.lang==="en"?"Administrator access active":"Acceso de administrador activo")
   :(APP.lang==="en"?`Service active — about ${n} minutes remaining`:`Servicio activo — quedan aproximadamente ${n} minutos`);
 }else{
  box.textContent=APP.lang==="en"?"Service not active":"Sesión no activa";
 }
}

async function checkSession(){
 if(!active()){
  renderSession();
  show("payment");
  return false;
 }
 try{
  const d=await api("/api/v1/session",{method:"GET"});
  if(!d.active){
   clearTokens();
   renderSession();
   show("payment");
   return false;
  }
  APP.session=d;
  renderSession();
  show("home");
  return true;
 }catch(e){
  if(e.status===401||e.status===403){
   clearTokens();
   renderSession();
   show("payment");
   return false;
  }
  show("home");
  return true;
 }
}

async function createCheckout(){
 try{
  const d=await api("/api/v1/create-checkout-session",{
   method:"POST",
   body:JSON.stringify({language:lang()})
  });
  const u=d.checkout_url||d.url;
  if(u)location.href=u;
  else msg(APP.lang==="en"?"Payment page is ready but no checkout link was returned.":"La página de pago está preparada pero no se recibió el enlace.","error");
 }catch(e){
  msg(e.message||"No se pudo preparar el pago.","error");
 }
}

async function verifyPayment(){
 const q=new URLSearchParams(location.search);
 const sid=q.get("session_id")||q.get("checkout_session_id");
 if(!sid)return;
 try{
  const d=await api("/api/v1/verify-payment",{
   method:"POST",
   body:JSON.stringify({session_id:sid})
  });
  const t=d.token||d.service_token;
  if(t){
   APP.serviceToken=t;
   APP.adminToken="";
   saveTokens();
   history.replaceState({},document.title,location.pathname);
   await checkSession();
   msg(APP.lang==="en"?"Your guided session is ready.":"Tu sesión guiada está lista.","success");
  }
 }catch(e){
  msg(e.message||"No se pudo activar la sesión.","error");
 }
}

async function adminLogin(){
 const user=txt($("#adminUser")?.value);
 const pass=txt($("#adminPass")?.value);
 if(!user||!pass){
  msg(APP.lang==="en"?"Enter username and password.":"Escribe usuario y contraseña.","warn");
  return;
 }
 try{
  const d=await api("/api/v1/admin/login",{
   method:"POST",
   body:JSON.stringify({username:user,password:pass})
  });
  const t=d.token||d.admin_token;
  if(!t)throw new Error(APP.lang==="en"?"Administrator access could not be activated.":"No se recibió el acceso de administrador.");
  APP.adminToken=t;
  APP.serviceToken="";
  saveTokens();
  await checkSession();
  msg(APP.lang==="en"?"Administrator access activated.":"Acceso de administrador activado.","success");
 }catch(e){
  msg(e.message||"No se pudo iniciar sesión.","error");
 }
}

function logout(){
 clearTokens();
 show("payment");
 msg(APP.lang==="en"?"Session closed.":"Sesión cerrada.","info");
}

function dataObject(){
 const o={language:lang()};
 const fields=["origin","destination","departureDate","returnDate","airline","cabin","fare","passengers","stops"];
 fields.forEach(id=>{
  const v=val(id);
  if(v!==""){
   const key=id==="departureDate"?"departure_date":id==="returnDate"?"return_date":id;
   o[key]=["passengers","stops"].includes(id)?Number(v):v;
  }
 });
 return o;
}

async function flight(){
 if(!requirePaid())return;
 const data=dataObject();
 if(!data.origin||!data.destination){
  msg(APP.lang==="en"?"Enter the origin and destination so we can guide you.":"Escribe el origen y destino para poder guiarte.","warn");
  return;
 }
 try{
  const d=await api("/api/v1/flight/understand",{
   method:"POST",
   body:JSON.stringify(data)
  });
  renderFlight(d);
 }catch(e){
  msg(e.message||"No se pudo procesar la información del vuelo.","error");
 }
}

function renderFlight(d){
 const box=$("#flightResult");
 if(!box)return;
 let h="";
 if(d.origin||d.destination||d.departure_date){
  h+=`<div class="result-card"><h3>✈️ ${APP.lang==="en"?"Your trip information":"Tu información de viaje"}</h3>`;
  if(d.origin)h+=`<p><b>${APP.lang==="en"?"Origin":"Origen"}:</b> ${esc(d.origin)}</p>`;
  if(d.destination)h+=`<p><b>${APP.lang==="en"?"Destination":"Destino"}:</b> ${esc(d.destination)}</p>`;
  if(d.departure_date)h+=`<p><b>${APP.lang==="en"?"Date":"Fecha"}:</b> ${esc(d.departure_date)}</p>`;
  if(val("airline"))h+=`<p><b>${APP.lang==="en"?"Airline":"Aerolínea"}:</b> ${esc(val("airline"))}</p>`;
  h+=`</div>`;
 }
 if(d.message)h+=`<p>${esc(d.message)}</p>`;
 if(d.google_flights_url){
  h+=`<p><a class="primary-link" href="${esc(d.google_flights_url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open Google Flights":"Abrir Google Flights"}</a></p>`;
 }
 const airs=d.airline_sources||[];
 if(airs.length){
  h+=`<h3>${APP.lang==="en"?"Airline information":"Información de la aerolínea"}</h3>${sourceList(airs)}`;
 }
 const chars=d.charter_sources||[];
 if(chars.length){
  h+=`<h3>${APP.lang==="en"?"Flight and travel sources":"Fuentes de vuelos y viajes"}</h3>${sourceList(chars)}`;
 }
 const sources=d.sources||[];
 if(!airs.length&&!chars.length&&sources.length)h+=sourceList(sources);
 if(d.next_action)h+=`<div class="next-action"><strong>${esc(d.next_action)}</strong></div>`;
 h+=`<div class="result-card"><h3>🖥️ ${APP.lang==="en"?"Learn before you book":"Aprende antes de reservar"}</h3><p>${APP.lang==="en"?"You can practice the airline booking process before entering the real airline website.":"Puedes practicar el proceso de reserva de la aerolínea antes de entrar en la página real."}</p><button class="primary" data-action="simulation">Practicar reserva</button></div>`;
 box.innerHTML=h;
}

function sourceList(items){
 if(!Array.isArray(items)||!items.length)return"";
 return `<div class="source-list">${items.map(x=>{
  const name=esc(x.name||"Fuente oficial");
  const url=esc(x.url||"#");
  const desc=x.description?`<p>${esc(x.description)}</p>`:"";
  const alt=x.alternate_url?`<a href="${esc(x.alternate_url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Alternative source":"Fuente alternativa"}</a>`:"";
  return `<div class="source-card"><strong>${name}</strong>${desc}${x.url?`<a href="${url}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open official source":"Abrir fuente oficial"}</a>${alt}`:""}</div>`;
 }).join("")}</div>`;
}

async function officialSources(){
 if(!requirePaid())return;
 try{
  const d=await api("/api/v1/sources/official",{method:"GET"});
  renderSources(d.sources||d.official_sources||[]);
 }catch(e){
  msg(e.message||"No se pudieron cargar las fuentes.","error");
 }
}

function renderSources(items){
 const box=$("#sourcesResult");
 if(!box)return;
 box.innerHTML=Array.isArray(items)&&items.length
  ?sourceList(items)
  :`<p>${APP.lang==="en"?"Official sources will appear here when available.":"Aquí aparecerán las fuentes oficiales disponibles."}</p>`;
}

async function itemConsult(){
 if(!requirePaid())return;
 const item=val("itemName");
 const quantity=val("itemQty")||"1";
 const description=val("itemDescription");
 const airline=val("itemAirline")||val("airline");
 if(!item){
  msg(APP.lang==="en"?"Write the item you want to understand.":"Escribe el artículo que quieres entender.","warn");
  return;
 }
 try{
  const d=await api("/api/v1/consultar-articulo",{
   method:"POST",
   body:JSON.stringify({
    item,
    quantity,
    description,
    airline,
    destination:val("destination"),
    origin:val("origin"),
    cabin:val("cabin"),
    fare:val("fare"),
    language:lang()
   })
  });
  renderObject($("#itemResult"),d);
 }catch(e){
  msg(e.message||"No se pudo consultar el artículo.","error");
 }
}

async function teach(){
 if(!requirePaid())return;
 const term=val("term");
 if(!term){
  msg(APP.lang==="en"?"Write a term or process.":"Escribe un término o proceso.","warn");
  return;
 }
 try{
  const d=await api("/api/v1/item/teach",{
   method:"POST",
   body:JSON.stringify({term,language:lang()})
  });
  renderObject($("#teachResult"),d);
 }catch(e){
  msg(e.message||"No se pudo explicar el término.","error");
 }
}

async function guide(){
 if(!requirePaid())return;
 try{
  const d=await api("/api/v1/guide",{
   method:"POST",
   body:JSON.stringify({language:lang(),flight:dataObject()})
  });
  renderGuide(d);
 }catch(e){
  msg(e.message||"No se pudo cargar la guía.","error");
 }
}

function renderGuide(d){
 const box=$("#guideResult");
 if(!box)return;
 let h="";
 if(d.next_action)h+=`<div class="next-action"><strong>${esc(d.next_action)}</strong></div>`;
 if(Array.isArray(d.steps)&&d.steps.length){
  h+=`<h3>${APP.lang==="en"?"Your preparation":"Tu preparación"}</h3><ol>`;
  d.steps.forEach(x=>h+=`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||""))}</li>`);
  h+="</ol>";
 }
 if(Array.isArray(d.cuba_steps)&&d.cuba_steps.length){
  h+=`<h3>${APP.lang==="en"?"Cuba":"Cuba"}</h3><ol>`;
  d.cuba_steps.forEach(x=>h+=`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||""))}</li>`);
  h+="</ol>";
 }
 if(Array.isArray(d.official_sources)&&d.official_sources.length)h+=sourceList(d.official_sources);
 if(d.legal_notice)h+=`<p>${esc(typeof d.legal_notice==="string"?d.legal_notice:(d.legal_notice.full_notice||d.legal_notice.short_notice||""))}</p>`;
 box.innerHTML=h;
}

async function cubaGuide(){
 if(!requirePaid())return;
 try{
  const d=await api(`/api/v1/cuba/official?language=${encodeURIComponent(lang())}`,{method:"GET"});
  renderObject($("#cubaGuideResult"),d);
 }catch(e){
  msg(e.message||"No se pudo cargar la guía de Cuba.","error");
 }
}

async function legal(){
 try{
  const d=await api(`/api/v1/legal?language=${encodeURIComponent(lang())}`,{method:"GET"});
  const box=$("#legalResult");
  if(!box)return;
  let h="";
  if(d.short_notice)h+=`<p>${esc(d.short_notice)}</p>`;
  if(d.full_notice)h+=`<p>${esc(d.full_notice)}</p>`;
  if(d.user_guidance)h+=`<p>${esc(d.user_guidance)}</p>`;
  if(d.source_notice)h+=`<p>${esc(d.source_notice)}</p>`;
  box.innerHTML=h||`<p>${APP.lang==="en"?"Legal information is available from May Roga LLC.":"La información legal del servicio está disponible aquí."}</p>`;
 }catch(e){
  msg(e.message||"No se pudo cargar el aviso legal.","error");
 }
}

function renderObject(box,d){
 if(!box)return;
 if(typeof d==="string"){
  box.innerHTML=`<p>${esc(d)}</p>`;
  return;
 }
 let h="";
 if(d.title)h+=`<h2>${esc(d.title)}</h2>`;
 if(d.intro)h+=`<p>${esc(d.intro)}</p>`;
 if(d.message)h+=`<p>${esc(d.message)}</p>`;
 if(d.explanation)h+=`<div class="result-card"><h3>${APP.lang==="en"?"Explanation":"Explicación"}</h3><p>${esc(d.explanation)}</p></div>`;
 if(d.reason)h+=`<p>${esc(d.reason)}</p>`;
 if(d.baggage_place)h+=`<p><b>${APP.lang==="en"?"Baggage":"Equipaje"}:</b> ${esc(d.baggage_place)}</p>`;
 if(Array.isArray(d.conditions)&&d.conditions.length){
  h+=`<h3>${APP.lang==="en"?"Conditions":"Condiciones"}</h3><ul>`;
  d.conditions.forEach(x=>h+=`<li>${esc(x)}</li>`);
  h+="</ul>";
 }
 if(Array.isArray(d.missing_information)&&d.missing_information.length){
  h+=`<h3>${APP.lang==="en"?"Information to confirm":"Información que debes confirmar"}</h3><ul>`;
  d.missing_information.forEach(x=>h+=`<li>${esc(x)}</li>`);
  h+="</ul>";
 }
 const src=d.sources||d.official_sources||d.links||[];
 if(Array.isArray(src)&&src.length)h+=sourceList(src);
 if(d.official_link)h+=`<p><a href="${esc(d.official_link)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open official source":"Abrir fuente oficial"}</a></p>`;
 if(d.next_action)h+=`<div class="next-action"><strong>${esc(d.next_action)}</strong></div>`;
 box.innerHTML=h||`<p>${APP.lang==="en"?"The next guided step is ready.":"El siguiente paso guiado está listo."}</p>`;
}

function simulationData(){
 const airline=val("simulationAirline")||val("airlineName")||val("airline")||"";
 const process=val("simulationProcess")||val("airlineProcess")||"booking";
 return {airline,process,language:lang()};
}

function simulationTemplate(airline,process){
 const a=airline||"tu aerolínea";
 const es={
  booking:{
   title:`Simulación de reserva — ${a}`,
   steps:[
    "1. Identifica el botón para buscar o reservar un vuelo.",
    "2. Practica escribir origen, destino y fecha.",
    "3. Aprende a revisar pasajeros y opciones antes de continuar.",
    "4. Aprende dónde aparecen las opciones de tarifa.",
    "5. Practica revisar el resumen antes de confirmar.",
    "6. Aprende dónde aparece el precio final antes del pago."
   ],
   action:"Después de practicar, podrás reconocer cada parte cuando entres al sitio real."
  },
  checkin:{
   title:`Simulación de check-in — ${a}`,
   steps:[
    "1. Identifica la opción Check-in.",
    "2. Practica localizar tu reserva.",
    "3. Aprende dónde se solicitan los datos necesarios.",
    "4. Practica revisar el vuelo y el pasajero.",
    "5. Aprende dónde aparece el pase de abordar."
   ],
   action:"La práctica te permite llegar al proceso real sabiendo qué buscar."
  },
  baggage:{
   title:`Simulación de equipaje — ${a}`,
   steps:[
    "1. Identifica la sección Equipaje.",
    "2. Aprende a diferenciar equipaje incluido y opciones adicionales.",
    "3. Practica revisar las condiciones mostradas.",
    "4. Aprende dónde aparece cualquier costo antes de continuar.",
    "5. Confirma siempre la condición final en la fuente oficial."
   ],
   action:"Primero entiendes la pantalla; después realizas el proceso real."
  },
  manage:{
   title:`Simulación de administración de reserva — ${a}`,
   steps:[
    "1. Identifica la opción para administrar una reserva.",
    "2. Aprende dónde se localiza una reservación.",
    "3. Practica reconocer las opciones disponibles.",
    "4. Aprende a revisar los cambios antes de confirmarlos."
   ],
   action:"La simulación te ayuda a navegar con más seguridad."
  },
  boarding:{
   title:`Simulación de pase de abordar — ${a}`,
   steps:[
    "1. Aprende dónde encontrar el pase de abordar.",
    "2. Identifica nombre, vuelo, fecha y aeropuerto.",
    "3. Aprende a reconocer puerta y grupo cuando aparezcan.",
    "4. Practica revisar la información antes de dirigirte a la puerta."
   ],
   action:"Aprendes a leer tu pase antes del viaje."
  },
  dviajeros:{
   title:"Simulación educativa de D’Viajeros",
   steps:[
    "1. Aprende qué información suele solicitar el proceso.",
    "2. Practica identificar cada campo.",
    "3. Aprende a avanzar paso a paso.",
    "4. Practica revisar la información antes de enviarla.",
    "5. Cuando estés preparado, utiliza el portal oficial D’Viajeros."
   ],
   action:"La simulación enseña el recorrido; el envío real se realiza en el portal oficial."
  },
  visa:{
   title:"Simulación educativa de visa / eVisa",
   steps:[
    "1. Aprende qué información debes revisar antes de comenzar.",
    "2. Practica identificar los campos del proceso.",
    "3. Aprende a revisar documentos e información solicitada.",
    "4. Practica revisar todo antes de continuar.",
    "5. Realiza el proceso real únicamente en la fuente oficial correspondiente."
   ],
   action:"La práctica te ayuda a entender el proceso antes de utilizar la página oficial."
  }
 };
 const en={
  booking:{
   title:`Booking practice — ${a}`,
   steps:["1. Identify the button used to search or book.","2. Practice entering origin, destination and date.","3. Learn where passenger and fare options appear.","4. Practice reviewing the trip summary.","5. Learn where the final price appears before payment."],
   action:"After practicing, you will recognize the main parts when using the real website."
  },
  checkin:{
   title:`Check-in practice — ${a}`,
   steps:["1. Identify the Check-in option.","2. Practice locating your reservation.","3. Learn where the required information is entered.","4. Review passenger and flight information.","5. Learn where the boarding pass appears."],
   action:"Practice first, then use the real airline process with greater confidence."
  },
  baggage:{
   title:`Baggage practice — ${a}`,
   steps:["1. Identify the Baggage section.","2. Learn the difference between included and additional baggage.","3. Practice reviewing the displayed conditions.","4. Learn where any price appears before continuing.","5. Confirm the final rule with the official source."],
   action:"First understand the screen; then use the real process."
  },
  manage:{
   title:`Manage booking practice — ${a}`,
   steps:["1. Identify the manage-booking option.","2. Learn where a reservation is located.","3. Practice recognizing available options.","4. Review any change before confirming."],
   action:"The simulation helps you navigate with greater confidence."
  },
  boarding:{
   title:`Boarding pass practice — ${a}`,
   steps:["1. Learn where to find the boarding pass.","2. Identify passenger, flight, date and airport.","3. Learn where gate and group may appear.","4. Practice reviewing the information before going to the gate."],
   action:"You learn how to read the boarding pass before traveling."
  },
  dviajeros:{
   title:"D’Viajeros educational practice",
   steps:["1. Learn what information the process may request.","2. Practice identifying each field.","3. Learn how to move through the process.","4. Practice reviewing information before submitting.","5. When ready, use the official D’Viajeros portal."],
   action:"The simulation teaches the process; the real submission happens on the official portal."
  },
  visa:{
   title:"Visa / eVisa educational practice",
   steps:["1. Learn what information to review first.","2. Practice identifying process fields.","3. Learn how to review requested documents and information.","4. Practice reviewing everything before continuing.","5. Use only the applicable official source for the real process."],
   action:"Practice helps you understand the process before using the official website."
  }
 };
 return (APP.lang==="en"?en:es)[process]||(APP.lang==="en"?en:es).booking;
}

function runSimulation(){
 if(!requirePaid())return;
 const d=simulationData();
 const t=simulationTemplate(d.airline,d.process);
 const box=$("#simulationResult")||$("#cubaResult");
 if(!box)return;
 let h=`<div class="simulation-card"><div class="simulation-head"><span>🖥️</span><div><h3>${esc(t.title)}</h3><small>${APP.lang==="en"?"Educational guided practice":"Práctica educativa guiada"}</small></div></div><div class="simulation-steps">`;
 t.steps.forEach((s,i)=>h+=`<div class="simulation-step"><b>${i+1}</b><p>${esc(s.replace(/^\d+\.\s*/,""))}</p></div>`);
 h+=`</div><div class="next-action"><strong>${esc(t.action)}</strong></div>`;
 if(["dviajeros","visa"].includes(d.process)){
  h+=`<p><button class="primary" data-action="sources">${APP.lang==="en"?"Open official sources":"Ver fuentes oficiales"}</button></p>`;
 }
 h+="</div>";
 box.innerHTML=h;
 show(box.id==="cubaResult"?"cuba":"simulation");
}

function runSimulationType(type){
 if(!requirePaid())return;
 if(type==="dviajeros"){
  $("#simulationProcess").value="dviajeros";
 }else if(type==="visa"){
  $("#simulationProcess").value="visa";
 }
 runSimulation();
}

function bind(){
 if(APP._bound)return;
 APP._bound=true;

 $("#langBtn")?.addEventListener("click",toggleLang);
 $("#adminBtn")?.addEventListener("click",()=>show("admin"));

 document.addEventListener("click",e=>{
  const b=e.target.closest("[data-action]");
  if(!b)return;
  const a=b.dataset.action;

  if(a==="payment"||a==="pay")createCheckout();
  else if(a==="admin")show("admin");
  else if(a==="admin-login")adminLogin();
  else if(a==="logout")logout();
  else if(a==="home")home();
  else if(a==="flight"||a==="search-flight"||a==="flight-understand")a==="flight"?show("flight"):flight();
  else if(a==="airline")show("airline");
  else if(a==="simulation")show("simulation");
  else if(a==="run-simulation")runSimulation();
  else if(a==="simulation-dviajeros")runSimulationType("dviajeros");
  else if(a==="simulation-visa")runSimulationType("visa");
  else if(a==="official-sources"||a==="sources")officialSources();
  else if(a==="guide")guide();
  else if(a==="cuba")show("cuba");
  else if(a==="cuba-guide")cubaGuide();
  else if(a==="legal")legal();
  else if(a==="item"||a==="consult-item")a==="item"?show("item"):itemConsult();
  else if(a==="baggage"){
   show("baggage");
  }
  else if(a==="teach"||a==="teach-item")a==="teach"?show("teach"):teach();
  else if(a==="logout")logout();
 });

 $("#flightBtn")?.addEventListener("click",flight);
 $("#itemBtn")?.addEventListener("click",itemConsult);
 $("#teachBtn")?.addEventListener("click",teach);
 $("#payBtn")?.addEventListener("click",createCheckout);
 $("#adminLoginBtn")?.addEventListener("click",adminLogin);
}

async function init(){
 document.documentElement.lang=APP.lang;
 bind();
 translate();
 show("loading");
 await loadConfig();

 if(active())await checkSession();
 else show("payment");

 await verifyPayment();

 if(active())await checkSession();
 else if(!APP.session)show("payment");
}

window.APP=APP;
window.createCheckout=createCheckout;
window.adminLogin=adminLogin;
window.logout=logout;
window.flight=flight;
window.officialSources=officialSources;
window.cubaGuide=cubaGuide;
window.guide=guide;
window.itemConsult=itemConsult;
window.teach=teach;
window.toggleLang=toggleLang;
window.legal=legal;
window.runSimulation=runSimulation;

document.addEventListener("DOMContentLoaded",init);
