"use strict";
const APP={name:"¿QUÉ QUIERES LLEVAR?",version:"8.0.3",lang:localStorage.getItem("cuba_lang")||"es",token:localStorage.getItem("cuba_service_token")||"",adminToken:localStorage.getItem("cuba_admin_token")||"",config:null};
const $=id=>document.getElementById(id);
const q=s=>document.querySelector(s);
const qa=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const api=async(path,opt={})=>{
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),25000);
 const o={...opt,signal:controller.signal,headers:{Accept:"application/json",...(opt.headers||{})}};
 if(APP.token)o.headers["X-Service-Token"]=APP.token;
 if(APP.adminToken)o.headers["X-Admin-Token"]=APP.adminToken;
 if(o.body&&typeof o.body!=="string"){o.headers["Content-Type"]="application/json";o.body=JSON.stringify(o.body)}
 try{
  const r=await fetch(path,o);
  let d=null;
  try{d=await r.json()}catch(_){d={success:false,message:APP.lang==="es"?"Respuesta inválida del servidor.":"Invalid server response."}}
  if(!r.ok)throw Object.assign(new Error(d.message||d.detail||d.error||`Error ${r.status}`),{status:r.status,data:d});
  return d
 }catch(e){
  if(e.name==="AbortError")throw new Error(APP.lang==="es"?"La conexión tardó demasiado. Intenta nuevamente.":"The connection took too long. Please try again.");
  if(!e.message)throw new Error(APP.lang==="es"?"No se pudo conectar con el servidor.":"Could not connect to the server.");
  throw e
 }finally{clearTimeout(timer)}
};
const show=id=>{
 qa(".screen").forEach(x=>x.classList.add("hidden"));
 $(id)?.classList.remove("hidden");
 window.scrollTo({top:0,behavior:"smooth"})
};
const msg=(id,text,good=false)=>{
 const e=$(id);
 if(e)e.innerHTML=`<div class="${good?"good":"bad"}">${esc(text)}</div>`
};
const active=()=>!!(APP.token||APP.adminToken);
const adminActive=()=>!!APP.adminToken;
const requirePaid=()=>{
 if(active())return true;
 show("payment");
 return false
};
const langText={
 es:{
  title:"¿Qué quieres llevar?",
  subtitle:"Te ayudamos a organizar tu preparación de viaje, entender tu vuelo, revisar artículos y confirmar la información oficial.",
  start:"Empezar",
  flight:"Mi vuelo",
  flightSmall:"Entiende tu itinerario",
  item:"¿Qué llevo?",
  itemSmall:"Consulta un artículo",
  baggage:"Equipaje",
  baggageSmall:"Prepara tus maletas",
  cuba:"Cuba",
  cubaSmall:"Pasos y fuentes oficiales",
  guide:"Guía",
  guideSmall:"Prepara tu viaje",
  sources:"Fuentes oficiales",
  sourcesSmall:"Consulta directamente",
  teach:"Aprender un término",
  teachSmall:"Entiende lo que significa",
  legal:"Aviso legal",
  legalSmall:"Quién presta el servicio",
  paymentTitle:"Activa tu preparación",
  paymentText:"Servicio independiente de May Roga LLC. Pago único de $15.99 para una sesión de 15 minutos.",
  paymentNotice:"No somos una aerolínea, banco, agencia gubernamental ni vendedor de boletos.",
  pay:"Continuar al pago",
  charterTitle:"Vuelos oficiales a Cuba",
  charterText:"Consulta directamente estas opciones de vuelos y servicios chárter. La compra se realiza con el proveedor.",
  openOfficial:"Abrir sitio oficial",
  beforeBuy:"Antes de comprar",
  confirmProvider:"Confirma directamente con el proveedor el precio, fecha, horario, disponibilidad, equipaje y condiciones del boleto.",
  noTicketSale:"¿QUÉ QUIERES LLEVAR? no vende ni reserva boletos."
 },
 en:{
  title:"What do you want to carry?",
  subtitle:"We help you prepare for your trip, understand your flight, review items and confirm official information.",
  start:"Start",
  flight:"My flight",
  flightSmall:"Understand your itinerary",
  item:"What do I carry?",
  itemSmall:"Check an item",
  baggage:"Baggage",
  baggageSmall:"Prepare your bags",
  cuba:"Cuba",
  cubaSmall:"Steps and official sources",
  guide:"Guide",
  guideSmall:"Prepare your trip",
  sources:"Official sources",
  sourcesSmall:"Check directly",
  teach:"Learn a term",
  teachSmall:"Understand what it means",
  legal:"Legal notice",
  legalSmall:"Who provides the service",
  paymentTitle:"Activate your preparation",
  paymentText:"Independent May Roga LLC service. One-time $15.99 payment for a 15-minute session.",
  paymentNotice:"We are not an airline, bank, government agency or ticket seller.",
  pay:"Continue to payment",
  charterTitle:"Official flights to Cuba",
  charterText:"Check these flight and charter service options directly. Purchase is completed with the provider.",
  openOfficial:"Open official site",
  beforeBuy:"Before buying",
  confirmProvider:"Confirm the price, date, schedule, availability, baggage and ticket conditions directly with the provider.",
  noTicketSale:"¿QUÉ QUIERES LLEVAR? does not sell or book tickets."
 }
};
const renderLang=()=>{
 const t=langText[APP.lang]||langText.es;
 qa("[data-i18n]").forEach(e=>{if(t[e.dataset.i18n]!=null)e.textContent=t[e.dataset.i18n]});
 if($("langBtn"))$("langBtn").textContent=APP.lang==="es"?"EN":"ES";
 updateStatus()
};
const updateStatus=()=>{
 const e=$("sessionStatus");
 if(!e)return;
 if(adminActive())e.textContent=APP.lang==="es"?"Administrador activo":"Administrator active";
 else if(APP.token)e.textContent=APP.lang==="es"?"Sesión activa":"Session active";
 else e.textContent=APP.lang==="es"?"Sesión no activa":"Session not active"
};
const clearService=()=>{
 APP.token="";
 localStorage.removeItem("cuba_service_token")
};
const clearAdmin=()=>{
 APP.adminToken="";
 localStorage.removeItem("cuba_admin_token")
};
const clearAccess=()=>{
 clearService();
 clearAdmin();
 updateStatus()
};
const loadConfig=async()=>{
 try{
  APP.config=await api("/api/v1/config?language="+encodeURIComponent(APP.lang));
  return APP.config
 }catch(e){
  const x=$("loadingText");
  if(x)x.textContent=e.message;
  return null
 }
};
const checkSession=async()=>{
 if(!APP.token&&!APP.adminToken)return false;
 try{
  const d=await api("/api/v1/session");
  if(d.active===true)return true;
  if(d.active===false){
   clearAccess();
   return false
  }
  return active()
 }catch(e){
  if(e.status===401||e.status===403){
   clearAccess();
   return false
  }
  return active()
 }
};
const init=async()=>{
 await loadConfig();
 await checkSession();
 renderLang();
 updateStatus();
 show(active()?"home":"payment")
};
const payment=async()=>{
 const b=$("payBtn"),m=$("payMsg");
 if(b)b.disabled=true;
 if(m)m.textContent=APP.lang==="es"?"Preparando el pago...":"Preparing payment...";
 try{
  const d=await api("/api/v1/create-checkout-session",{
   method:"POST",
   body:{language:APP.lang,return_path:"/"}
  });
  if(!d.success||!(d.checkout_url||d.url))throw new Error(d.message||"No pudimos iniciar el pago.");
  location.href=d.checkout_url||d.url
 }catch(e){
  if(m)m.textContent=e.message;
  if(b)b.disabled=false
 }
};
const verifyPayment=async()=>{
 const p=new URLSearchParams(location.search);
 const status=p.get("payment"),sid=p.get("session_id")||p.get("checkout_session_id");
 if(status==="cancelled"){
  const m=$("payMsg");
  if(m)m.textContent=APP.lang==="es"?"El pago fue cancelado. Puedes intentarlo nuevamente.":"Payment was cancelled. You can try again.";
  show("payment");
  return
 }
 if(status!=="success"||!sid)return;
 try{
  const d=await api("/api/v1/verify-payment",{
   method:"POST",
   body:{session_id:sid}
  });
  const serviceToken=d.token||d.service_token||"";
  if(d.success&&d.paid&&serviceToken){
   APP.token=serviceToken;
   localStorage.setItem("cuba_service_token",APP.token);
   history.replaceState({},document.title,"/");
   updateStatus();
   show("home");
   alert(APP.lang==="es"?"Pago confirmado. Tu sesión de 15 minutos está activa.":"Payment confirmed. Your 15-minute session is active.");
  }else{
   const x=$("loadingText");
   if(x)x.textContent=d.message||"El pago no aparece como completado.";
   show("payment")
  }
 }catch(e){
  const x=$("loadingText");
  if(x)x.textContent=e.message;
  show("payment")
 }
};
const charterFallback=[
 {id:"cubazul",name:"Cubazul Air Charter",url:"https://cubazulaircharter.com/",type:"charter_booking",description_es:"Consulta y reserva vuelos chárter a Cuba.",description_en:"Check and book charter flights to Cuba."},
 {id:"xael",name:"Xael Charters",url:"https://www.xaelcharter.com/",type:"charter_booking",description_es:"Consulta y reserva vuelos a Cuba.",description_en:"Check and book flights to Cuba."},
 {id:"cuballama",name:"Cuballama Viajes",url:"https://www.cuballama.com/viajes/vuelos/charters",type:"charter_booking",description_es:"Consulta y reserva vuelos chárter a Cuba.",description_en:"Check and book charter flights to Cuba."},
 {id:"ibc_airways",name:"IBC Airways / IBC Air",url:"https://ibcairways.com/",alternate_url:"https://flyibcair.com/",type:"charter_booking",description_es:"Consulta servicios de vuelos y chárter.",description_en:"Check flight and charter services."}
];
const onlyCharters=a=>{
 const ids=["cubazul","xael","cuballama","ibc_airways"];
 return Array.isArray(a)?a.filter(x=>ids.includes(x.id)):[] 
};
const renderCharterSources=a=>{
 const data=onlyCharters(a).length?onlyCharters(a):charterFallback;
 const t=langText[APP.lang]||langText.es;
 return `<section class="charter-section"><article class="card"><h2>✈️ ${esc(t.charterTitle)}</h2><p>${esc(t.charterText)}</p><div class="charter-grid">${data.map(x=>`<article class="source charter-source"><h3>${esc(x.name||"Proveedor oficial")}</h3><p>${esc(x[APP.lang==="en"?"description_en":"description_es"]||x.description||"")}</p><a class="btn" href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${esc(t.openOfficial)}</a>${x.alternate_url?`<a class="btn secondary" href="${esc(x.alternate_url)}" target="_blank" rel="noopener noreferrer">IBC Air</a>`:""}</article>`).join("")}</div><div class="notice"><b>${esc(t.beforeBuy)}</b><p>${esc(t.confirmProvider)}</p><p>${esc(t.noTicketSale)}</p></div></article></section>`
};
const charterSources=async()=>{
 try{
  let d=null;
  try{
   d=await api("/api/v1/flight/sources")
  }catch(_){
   try{d=await api("/api/v1/sources/official")}catch(__){d=null}
  }
  const list=onlyCharters(d?.sources||d?.official_booking_options||d?.data||[]);
  const html=renderCharterSources(list);
  const target=$("flightSourcesResult");
  if(target){
   target.innerHTML=html;
   show("flightSources")
  }else{
   const existing=$("dynamicFlightSources");
   if(existing)existing.remove();
   const wrap=document.createElement("div");
   wrap.id="dynamicFlightSources";
   wrap.innerHTML=html;
   document.body.appendChild(wrap);
   wrap.scrollIntoView({behavior:"smooth",block:"start"})
  }
 }catch(e){
  msg("flightResult",e.message)
 }
};
const flight=async()=>{
 if(!requirePaid())return;
 const origin=($("origin")?.value||"").trim().toUpperCase();
 const destination=($("destination")?.value||"").trim().toUpperCase();
 const departure_date=$("departureDate")?.value||"";
 if(!origin||!destination||!departure_date){
  msg("flightResult",APP.lang==="es"?"Completa origen, destino y fecha.":"Complete origin, destination and date.");
  return
 }
 try{
  const d=await api("/api/v1/flight/search-external",{
   method:"POST",
   body:{origin,destination,departure_date,language:APP.lang}
  });
  const options=d.official_booking_options||d.charter_sources||[];
  let h=renderCharterSources(options);
  if(d.message_es||d.message_en)h+=`<div class="notice"><p>${esc(APP.lang==="es"?d.message_es||"":d.message_en||"")}</p></div>`;
  if(d.google_flights_url)h+=`<p><a href="${esc(d.google_flights_url)}" target="_blank" rel="noopener noreferrer">Google Flights</a></p>`;
  $("flightResult").innerHTML=h
 }catch(e){
  if(e.status===401){
   clearAccess();
   show("payment");
   return
  }
  msg("flightResult",e.message)
 }
};
const item=async()=>{
 if(!requirePaid())return;
 const itemName=($("itemName")?.value||"").trim();
 const description=($("itemDescription")?.value||"").trim();
 const quantity=Math.max(1,Number($("itemQty")?.value||1));
 if(!itemName){
  msg("itemResult",APP.lang==="es"?"Escribe el artículo que quieres consultar.":"Enter the item you want to check.");
  return
 }
 try{
  const d=await api("/api/v1/consultar-articulo",{
   method:"POST",
   body:{item:itemName,baggage_type:"",description,quantity,language:APP.lang}
  });
  $("itemResult").innerHTML=renderObject(d)
 }catch(e){
  if(e.status===401){clearAccess();show("payment");return}
  msg("itemResult",e.message)
 }
};
const teach=async()=>{
 if(!requirePaid())return;
 const term=($("term")?.value||"").trim();
 if(!term){
  msg("teachResult",APP.lang==="es"?"Escribe un término.":"Enter a term.");
  return
 }
 try{
  const d=await api("/api/v1/item/teach",{
   method:"POST",
   body:{term,language:APP.lang}
  });
  $("teachResult").innerHTML=renderObject(d)
 }catch(e){
  if(e.status===401){clearAccess();show("payment");return}
  msg("teachResult",e.message)
 }
};
const guide=async()=>{
 if(!requirePaid())return;
 try{
  const d=await api("/api/v1/guide",{
   method:"POST",
   body:{language:APP.lang}
  });
  $("guideResult").innerHTML=renderObject(d)
 }catch(e){
  if(e.status===401){clearAccess();show("payment");return}
  msg("guideResult",e.message)
 }
};
const cuba=async()=>{
 if(!requirePaid())return;
 try{
  const d=await api(`/api/v1/cuba/official?language=${encodeURIComponent(APP.lang)}`);
  $("cubaResult").innerHTML=renderObject(d)
 }catch(e){
  if(e.status===401){clearAccess();show("payment");return}
  msg("cubaResult",e.message)
 }
};
const sources=async()=>{
 try{
  const d=await api("/api/v1/sources/official");
  $("sourcesResult").innerHTML=renderSources(d.sources||d.official_sources||[]);
 }catch(e){msg("sourcesResult",e.message)}
};
const legal=async()=>{
 try{
  const d=await api(`/api/v1/legal?language=${encodeURIComponent(APP.lang)}`);
  $("legalResult").innerHTML=`<article><h3>${esc(d.app_name||APP.name)}</h3><p>${esc(d.intro||"")}</p><p>${esc(d.short_notice||"")}</p><p>${esc(d.user_guidance||"")}</p><p>${esc(d.source_notice||"")}</p><p>${esc(d.full_notice||"")}</p></article>`
 }catch(e){msg("legalResult",e.message)}
};
const renderSources=a=>Array.isArray(a)&&a.length?a.map(x=>`<article class="source"><h3>${esc(x.name||"Fuente oficial")}</h3><p>${esc(x.description||x.description_es||x.notes||"")}</p>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="es"?"Abrir fuente oficial":"Open official source"}</a>`:""}</article>`).join(""):`<p>${APP.lang==="es"?"No hay fuentes disponibles.":"No sources available."}</p>`;
const renderObject=o=>{
 if(o==null)return"<p>Sin información.</p>";
 if(Array.isArray(o))return o.map(renderObject).join("");
 if(typeof o!=="object")return`<p>${esc(o)}</p>`;
 let h="";
 if(o.title)h+=`<h3>${esc(o.title)}</h3>`;
 if(o.message)h+=`<p>${esc(o.message)}</p>`;
 if(o.explanation)h+=`<p>${esc(o.explanation)}</p>`;
 if(o.baggage_summary)h+=`<p>${esc(o.baggage_summary)}</p>`;
 if(o.next_action)h+=`<div class="next"><b>${APP.lang==="es"?"Siguiente acción":"Next action"}:</b> ${esc(o.next_action)}</div>`;
 if(o.legal_notice)h+=`<p>${esc(o.legal_notice)}</p>`;
 if(o.official_booking_options&&Array.isArray(o.official_booking_options))h+=renderCharterSources(o.official_booking_options);
 if(o.charter_sources&&Array.isArray(o.charter_sources))h+=renderCharterSources(o.charter_sources);
 if(o.steps&&Array.isArray(o.steps))h+=`<ol>${o.steps.map(x=>{
  if(typeof x==="object"){
   const title=x.title||x.name||"";
   const desc=x.description||x.action||"";
   const url=x.official_url||x.url||"";
   return`<li><b>${esc(title)}</b>${desc?`<br>${esc(desc)}`:""}${url?`<br><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="es"?"Fuente oficial":"Official source"}</a>`:""}</li>`
  }
  return`<li>${esc(x)}</li>`
 }).join("")}</ol>`;
 if(o.sources&&Array.isArray(o.sources))h+=renderSources(o.sources);
 if(o.official_sources&&Array.isArray(o.official_sources))h+=renderSources(o.official_sources);
 if(o.conditions&&Array.isArray(o.conditions)&&o.conditions.length)h+=`<p><b>${APP.lang==="es"?"Condiciones":"Conditions"}:</b> ${o.conditions.map(esc).join(", ")}</p>`;
 if(o.missing_information&&Array.isArray(o.missing_information)&&o.missing_information.length)h+=`<p><b>${APP.lang==="es"?"Falta información":"Missing information"}:</b> ${o.missing_information.map(esc).join(", ")}</p>`;
 if(!h){
  h="<dl>";
  Object.entries(o).forEach(([k,v])=>{
   if(v!==null&&v!==undefined&&typeof v!=="object"&&k!=="success"&&k!=="version")h+=`<dt>${esc(k.replace(/_/g," "))}</dt><dd>${esc(v)}</dd>`
  });
  h+="</dl>"
 }
 return h||"<p>Sin información.</p>"
};
const adminLogin=async()=>{
 const u=($("adminUser")?.value||$("adminUsername")?.value||"").trim();
 const p=$("adminPass")?.value||$("adminPassword")?.value||"";
 if(!u||!p){
  msg("adminMsg",APP.lang==="es"?"Escribe el usuario y la contraseña.":"Enter the username and password.");
  return
 }
 const b=$("adminLoginBtn");
 if(b)b.disabled=true;
 try{
  const d=await api("/api/v1/admin/login",{
   method:"POST",
   body:{username:u,password:p}
  });
  if(!d.success||!d.token)throw new Error(d.message||"No se pudo iniciar sesión.");
  APP.adminToken=d.token;
  localStorage.setItem("cuba_admin_token",APP.adminToken);
  updateStatus();
  msg("adminMsg",APP.lang==="es"?"Sesión administrativa activa. La aplicación está desbloqueada.":"Administrator session active. The application is unlocked.",true);
  show("home");
 }catch(e){
  msg("adminMsg",e.message)
 }finally{
  if(b)b.disabled=false
 }
};
const adminLogout=()=>{
 clearAdmin();
 updateStatus();
 show("home")
};
qa("[data-action]").forEach(b=>b.addEventListener("click",async()=>{
 const a=b.dataset.action;
 if(a==="home")show("home");
 else if(a==="flight"){if(requirePaid())show("flight")}
 else if(a==="flight-sources"||a==="charter-sources"){await charterSources()}
 else if(a==="item"){if(requirePaid())show("item")}
 else if(a==="baggage"){if(requirePaid())show("baggage")}
 else if(a==="cuba"){if(requirePaid()){show("cuba");await cuba()}}
 else if(a==="guide"){if(requirePaid()){show("guide");await guide()}}
 else if(a==="sources"){show("sources");await sources()}
 else if(a==="teach"){if(requirePaid())show("teach")}
 else if(a==="legal"){show("legal");await legal()}
 else if(a==="payment")show("payment");
 else if(a==="admin")show("admin")
}));
if($("startBtn"))$("startBtn").onclick=()=>active()?show("flight"):show("payment");
if($("payBtn"))$("payBtn").onclick=payment;
if($("flightBtn"))$("flightBtn").onclick=flight;
if($("itemBtn"))$("itemBtn").onclick=item;
if($("teachBtn"))$("teachBtn").onclick=teach;
if($("adminLoginBtn"))$("adminLoginBtn").onclick=adminLogin;
if($("adminLogoutBtn"))$("adminLogoutBtn").onclick=adminLogout;
if($("charterSourcesBtn"))$("charterSourcesBtn").onclick=charterSources;
if($("flightSourcesBtn"))$("flightSourcesBtn").onclick=charterSources;
if($("langBtn"))$("langBtn").onclick=()=>{
 APP.lang=APP.lang==="es"?"en":"es";
 localStorage.setItem("cuba_lang",APP.lang);
 renderLang();
 loadConfig()
};
if($("adminBtn"))$("adminBtn").onclick=()=>show("admin");
window.charterSources=charterSources;
window.flight=flight;
window.item=item;
window.teach=teach;
window.guide=guide;
window.cuba=cuba;
window.sources=sources;
window.legal=legal;
window.adminLogin=adminLogin;
window.adminLogout=adminLogout;
window.addEventListener("load",async()=>{
 await init();
 await verifyPayment()
});
