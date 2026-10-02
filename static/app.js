"use strict";
const APP={name:"¿QUÉ QUIERES LLEVAR?",version:"8.0.2",lang:localStorage.getItem("cuba_lang")||"es",token:localStorage.getItem("cuba_service_token")||"",adminToken:localStorage.getItem("cuba_admin_token")||"",config:null};
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
  try{d=await r.json()}catch(_){d={success:false,message:"Respuesta inválida del servidor."}}
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
  title:"¿Qué quieres llevar?",subtitle:"Te ayudamos a organizar tu preparación de viaje, entender tu vuelo, revisar artículos y confirmar la información oficial.",start:"Empezar",flight:"Mi vuelo",flightSmall:"Entiende tu itinerario",item:"¿Qué llevo?",itemSmall:"Consulta un artículo",baggage:"Equipaje",baggageSmall:"Prepara tus maletas",cuba:"Cuba",cubaSmall:"Pasos y fuentes oficiales",guide:"Guía",guideSmall:"Prepara tu viaje",sources:"Fuentes oficiales",sourcesSmall:"Consulta directamente",teach:"Aprender un término",teachSmall:"Entiende lo que significa",legal:"Aviso legal",legalSmall:"Quién presta el servicio",paymentTitle:"Activa tu preparación",paymentText:"Servicio independiente de May Roga LLC. Pago único de $15.99 para una sesión de 15 minutos.",paymentNotice:"No somos una aerolínea, banco, agencia gubernamental ni vendedor de boletos.",pay:"Continuar al pago"
 },
 en:{
  title:"What do you want to carry?",subtitle:"We help you prepare for your trip, understand your flight, review items and confirm official information.",start:"Start",flight:"My flight",flightSmall:"Understand your itinerary",item:"What do I carry?",itemSmall:"Check an item",baggage:"Baggage",baggageSmall:"Prepare your bags",cuba:"Cuba",cubaSmall:"Steps and official sources",guide:"Guide",guideSmall:"Prepare your trip",sources:"Official sources",sourcesSmall:"Check directly",teach:"Learn a term",teachSmall:"Understand what it means",legal:"Legal notice",legalSmall:"Who provides the service",paymentTitle:"Activate your preparation",paymentText:"Independent May Roga LLC service. One-time $15.99 payment for a 15-minute session.",paymentNotice:"We are not an airline, bank, government agency or ticket seller.",pay:"Continue to payment"
 }
};
const renderLang=()=>{
 const t=langText[APP.lang]||langText.es;
 qa("[data-i18n]").forEach(e=>{if(t[e.dataset.i18n]!=null)e.textContent=t[e.dataset.i18n]});
 if($("langBtn"))$("langBtn").textContent=APP.lang==="es"?"EN":"ES"
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
  if(d.active)return true;
  clearService();
  clearAdmin();
  updateStatus();
  return false
 }catch(e){
  const adminWas=!!APP.adminToken;
  const serviceWas=!!APP.token;
  clearService();
  clearAdmin();
  updateStatus();
  return !(adminWas||serviceWas)
 }
};
const init=async()=>{
 await loadConfig();
 await checkSession();
 renderLang();
 updateStatus();
 show(active()?"home":"home")
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
 const status=p.get("payment"),sid=p.get("session_id");
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
const flight=async()=>{
 if(!requirePaid())return;
 const origin=($("origin")?.value||"").trim().toUpperCase();
 const destination=($("destination")?.value||"").trim().toUpperCase();
 const departure_date=$("departureDate")?.value||"";
 const passengers=Math.max(1,Number($("passengers")?.value||1));
 if(!origin||!destination||!departure_date){
  msg("flightResult",APP.lang==="es"?"Completa origen, destino y fecha.":"Complete origin, destination and date.");
  return
 }
 try{
  const d=await api("/api/v1/flight/search-external",{
   method:"POST",
   body:{origin,destination,departure_date,language:APP.lang}
  });
  $("flightResult").innerHTML=renderObject(d)
 }catch(e){
  if(e.status===401){clearService();clearAdmin();updateStatus();show("payment");return}
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
  if(e.status===401){clearService();clearAdmin();updateStatus();show("payment");return}
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
  if(e.status===401){clearService();clearAdmin();updateStatus();show("payment");return}
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
  if(e.status===401){clearService();clearAdmin();updateStatus();show("payment");return}
  msg("guideResult",e.message)
 }
};
const cuba=async()=>{
 if(!requirePaid())return;
 try{
  const d=await api(`/api/v1/cuba/official?language=${encodeURIComponent(APP.lang)}`);
  $("cubaResult").innerHTML=renderObject(d)
 }catch(e){
  if(e.status===401){clearService();clearAdmin();updateStatus();show("payment");return}
  msg("cubaResult",e.message)
 }
};
const sources=async()=>{
 try{
  const d=await api("/api/v1/sources/official");
  $("sourcesResult").innerHTML=renderSources(d.sources||[])
 }catch(e){msg("sourcesResult",e.message)}
};
const legal=async()=>{
 try{
  const d=await api(`/api/v1/legal?language=${encodeURIComponent(APP.lang)}`);
  $("legalResult").innerHTML=`<article><h3>${esc(d.app_name||APP.name)}</h3><p>${esc(d.intro||"")}</p><p>${esc(d.short_notice||"")}</p><p>${esc(d.user_guidance||"")}</p><p>${esc(d.source_notice||"")}</p><p>${esc(d.full_notice||"")}</p></article>`
 }catch(e){msg("legalResult",e.message)}
};
const renderSources=a=>a.map(x=>`<article class="source"><h3>${esc(x.name||"Fuente oficial")}</h3><p>${esc(x.description||x.notes||"")}</p>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">Abrir fuente oficial</a>`:""}</article>`).join("")||"<p>No hay fuentes disponibles.</p>";
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
 if(o.steps&&Array.isArray(o.steps))h+=`<ol>${o.steps.map(x=>{
  if(typeof x==="object"){
   const title=x.title||x.name||"";
   const desc=x.description||x.action||"";
   const url=x.official_url||x.url||"";
   return`<li><b>${esc(title)}</b>${desc?`<br>${esc(desc)}`:""}${url?`<br><a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Fuente oficial</a>`:""}</li>`
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
   if(v!==null&&v!==undefined&&typeof v!=="object"&&k!=="success"&&k!=="version")h+=`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`
  });
  h+="</dl>"
 }
 return h||"<p>Sin información.</p>"
};
const adminLogin=async()=>{
 const u=($("adminUser")?.value||"").trim();
 const p=$("adminPass")?.value||"";
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
if($("langBtn"))$("langBtn").onclick=()=>{
 APP.lang=APP.lang==="es"?"en":"es";
 localStorage.setItem("cuba_lang",APP.lang);
 renderLang();
 updateStatus();
 loadConfig()
};
if($("adminBtn"))$("adminBtn").onclick=()=>show("admin");
window.addEventListener("load",async()=>{
 await init();
 await verifyPayment()
});
