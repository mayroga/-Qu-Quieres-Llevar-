"use strict";
const APP={name:"QUE QUIERES LLEVAR",version:"8.1.0",lang:localStorage.getItem("qql_lang")||"es",serviceToken:localStorage.getItem("qql_service_token")||"",adminToken:localStorage.getItem("qql_admin_token")||"",session:null,config:null,_bound:false};
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
const txt=v=>String(v??"").trim();
const val=id=>txt(document.getElementById(id)?.value);
function active(){return!!(APP.serviceToken||APP.adminToken)}
function headers(extra={}){const h={"Content-Type":"application/json",...extra};if(APP.serviceToken)h["X-Service-Token"]=APP.serviceToken;if(APP.adminToken)h["X-Admin-Token"]=APP.adminToken;return h}
function saveTokens(){localStorage.setItem("qql_service_token",APP.serviceToken||"");localStorage.setItem("qql_admin_token",APP.adminToken||"")}
function clearTokens(){APP.serviceToken="";APP.adminToken="";APP.session=null;saveTokens()}
function msg(text,type="info"){let b=$("#appMessage")||$("#message")||$(".app-message");if(!b){b=document.createElement("div");b.id="appMessage";document.body.prepend(b)}b.className=`app-message ${type}`;b.textContent=text}
async function api(path,options={},timeout=25000){
 const c=new AbortController(),tm=setTimeout(()=>c.abort(),timeout);
 try{
  const r=await fetch(path,{...options,headers:headers(options.headers||{}),signal:c.signal});
  let d={};try{d=await r.json()}catch(_){}
  if(!r.ok){const e=new Error(d.detail||d.message||`HTTP ${r.status}`);e.status=r.status;e.data=d;throw e}
  return d
 }catch(e){
  if(e.name==="AbortError")throw new Error(APP.lang==="en"?"The request took too long. Please try again.":"La solicitud tardó demasiado. Intenta nuevamente.");
  throw e
 }finally{clearTimeout(tm)}
}
function screens(){return["loading","home","payment","flight","item","baggage","cuba","guide","sources","teach","legal","admin"].map(id=>document.getElementById(id)).filter(Boolean)}
function setView(name){
 screens().forEach(x=>x.classList.toggle("hidden",x.id!==name));
 document.body.dataset.view=name
}
function home(){setView(active()?"home":"payment")}
function requirePaid(){
 if(active())return true;
 setView("payment");
 msg(APP.lang==="en"?"Payment or administrator access is required.":"Se requiere acceso mediante pago o administrador.","warn");
 return false
}
function lang(){return APP.lang==="en"?"en":"es"}
function setLang(v){APP.lang=v==="en"?"en":"es";localStorage.setItem("qql_lang",APP.lang);translate();loadConfig()}
function toggleLang(){setLang(APP.lang==="es"?"en":"es")}
function translate(){
 document.documentElement.lang=APP.lang;
 $$("[data-es][data-en]").forEach(e=>e.textContent=e.dataset[APP.lang]||e.dataset.es||"");
 const b=$("#langBtn");if(b)b.textContent=APP.lang==="en"?"ES":"EN";
 const l=$("#loadingText");if(l)l.textContent=APP.lang==="en"?"Preparing your trip...":"Preparando tu viaje...";
 const s=$("#sessionStatus");if(s)s.textContent=active()?(APP.lang==="en"?"Access active":"Acceso activo"):(APP.lang==="en"?"Session not active":"Sesión no activa");
}
async function checkSession(){
 if(!active()){home();return false}
 try{
  const d=await api("/api/v1/session",{method:"GET"});
  if(d.active===false){clearTokens();home();return false}
  APP.session=d;translate();home();return true
 }catch(e){
  if(e.status===401||e.status===403){clearTokens();home();return false}
  APP.session={active:true};translate();home();return true
 }
}
async function loadConfig(){
 try{APP.config=await api("/api/v1/config",{method:"GET"});renderConfig(APP.config)}catch(_){}
}
function renderConfig(d){
 if(!d)return;
 $$("[data-config]").forEach(e=>{const k=e.dataset.config;if(d[k]!=null)e.textContent=d[k]})
}
async function createCheckout(){
 try{
  const d=await api("/api/v1/create-checkout-session",{method:"POST",body:JSON.stringify({language:lang()})});
  const u=d.checkout_url||d.url;
  if(u)location.href=u;
  else msg(APP.lang==="en"?"Payment link ready to continue.":"El enlace de pago está listo para continuar.","error")
 }catch(e){msg(e.message||"No se pudo iniciar el pago.","error")}
}
async function verifyPayment(){
 const q=new URLSearchParams(location.search),sid=q.get("session_id")||q.get("checkout_session_id");
 if(!sid)return false;
 try{
  const d=await api("/api/v1/verify-payment",{method:"POST",body:JSON.stringify({session_id:sid})});
  const t=d.token||d.service_token;
  if(!t)throw new Error(APP.lang==="en"?"Access could not be activated.":"No se pudo activar el acceso.");
  APP.serviceToken=t;APP.adminToken="";saveTokens();
  history.replaceState({},document.title,location.pathname);
  await checkSession();
  msg(APP.lang==="en"?"Your 15-minute preparation session is active.":"Tu sesión de preparación de 15 minutos está activa.","success");
  return true
 }catch(e){msg(e.message||"No se pudo verificar el pago.","error");return false}
}
async function adminLogin(){
 const user=val("adminUser"),pass=val("adminPass");
 if(!user||!pass){msg(APP.lang==="en"?"Enter username and password.":"Escribe usuario y contraseña.","warn");return}
 try{
  const d=await api("/api/v1/admin/login",{method:"POST",body:JSON.stringify({username:user,password:pass})});
  const t=d.token||d.admin_token;
  if(!t)throw new Error(APP.lang==="en"?"Administrator access is ready to be activated.":"El acceso de administrador está listo para activarse.");
  APP.adminToken=t;APP.serviceToken="";saveTokens();await checkSession();
  msg(APP.lang==="en"?"Administrator access is active.":"El acceso de administrador está activo.","success")
 }catch(e){msg(e.message||"No se pudo iniciar sesión.","error")}
}
function logout(){clearTokens();home();translate();msg(APP.lang==="en"?"Session closed.":"Sesión cerrada.","info")}
function ensureAirlineField(){
 const form=$("#flight")?.querySelector(".form");
 if(!form||$("#airline"))return;
 const label=document.createElement("label");
 label.innerHTML=APP.lang==="en"?"Airline":"Aerolínea";
 const input=document.createElement("input");
 input.id="airline";
 input.maxLength=40;
 input.placeholder=APP.lang==="en"?"Example: American Airlines":"Ej.: American Airlines";
 label.appendChild(input);
 const passengers=$("#passengers")?.closest("label");
 if(passengers)form.insertBefore(label,passengers);else form.insertBefore(label,form.querySelector("button"));
}
function dataObject(){
 ensureAirlineField();
 const o={language:lang()};
 ["origin","destination","departureDate","returnDate","airline","cabin","fare","passengers","stops"].forEach(id=>{
  const v=val(id);
  if(v!==""){
   const k=id==="departureDate"?"departure_date":id==="returnDate"?"return_date":id;
   o[k]=k==="passengers"||k==="stops"?Number(v):v
  }
 });
 return o
}
async function flight(){
 if(!requirePaid())return;
 const data=dataObject();
 if(!data.origin||!data.destination){
  msg(APP.lang==="en"?"Enter your origin and destination to continue.":"Escribe tu origen y destino para continuar.","warn");
  return
 }
 try{
  const d=await api("/api/v1/flight/understand",{method:"POST",body:JSON.stringify(data)});
  renderFlight(d)
 }catch(e){msg(e.message||"No se pudo preparar la información del vuelo.","error")}
}
function sourceList(items){
 if(!Array.isArray(items)||!items.length)return"";
 return `<div class="source-list">${items.map(x=>{
  const name=esc(x.name||"Fuente oficial"),url=esc(x.url||"#");
  const desc=x.description?`<p>${esc(x.description)}</p>`:"";
  const alt=x.alternate_url?` <a href="${esc(x.alternate_url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Alternative":"Alternativa"}</a>`:"";
  return `<div class="source-card"><strong>${name}</strong>${desc}${x.url?`<a href="${url}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open source":"Abrir fuente"}</a>${alt}`:""}</div>`
 }).join("")}</div>`
}
function renderFlight(d){
 const b=$("#flightResult");if(!b)return;
 let h="";
 const airline=d.airline||val("airline");
 const origin=d.origin||val("origin");
 const destination=d.destination||val("destination");
 const date=d.departure_date||val("departureDate");
 if(origin||destination||date||airline){
  h+=`<div class="next-action"><strong>${APP.lang==="en"?"Flight information":"Información del vuelo"}</strong>`;
  if(origin)h+=`<p>${esc(APP.lang==="en"?"Origin: ":"Origen: ")}${esc(origin)}</p>`;
  if(destination)h+=`<p>${esc(APP.lang==="en"?"Destination: ":"Destino: ")}${esc(destination)}</p>`;
  if(date)h+=`<p>${esc(APP.lang==="en"?"Date: ":"Fecha: ")}${esc(date)}</p>`;
  if(airline)h+=`<p>${esc(APP.lang==="en"?"Airline: ":"Aerolínea: ")}${esc(airline)}</p>`;
  h+="</div>"
 }
 if(d.understood){
  h+=`<p>${esc(typeof d.understood==="string"?d.understood:JSON.stringify(d.understood))}</p>`
 }
 if(d.steps&&Array.isArray(d.steps)&&d.steps.length){
  h+=`<h3>${APP.lang==="en"?"Next steps":"Próximos pasos"}</h3><ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||JSON.stringify(x)))}</li>`).join("")}</ol>`
 }
 if(d.google_flights_url){
  h+=`<div class="next-action"><strong>${APP.lang==="en"?"Continue with flight availability":"Continúa con la disponibilidad del vuelo"}</strong><p>${APP.lang==="en"?"Open Google Flights to review the route and current flight options.":"Abre Google Flights para revisar la ruta y las opciones actuales de vuelo."}</p><p><a href="${esc(d.google_flights_url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open Google Flights":"Abrir Google Flights"}</a></p></div>`
 }
 const chars=d.charter_sources||[];
 if(chars.length)h+=`<h3>${APP.lang==="en"?"Charter flight/travel providers":"Proveedores de vuelos chárter/servicios de viaje"}</h3>${sourceList(chars)}`;
 const airs=d.airline_sources||[];
 if(airs.length)h+=`<h3>${APP.lang==="en"?"Airline sources":"Fuentes de la aerolínea"}</h3>${sourceList(airs)}`;
 const sources=d.sources||[];
 if(!chars.length&&!airs.length&&sources.length)h+=sourceList(sources);
 if(d.next_action)h+=`<p><strong>${esc(d.next_action)}</strong></p>`;
 if(d.legal_notice)h+=`<p>${esc(typeof d.legal_notice==="string"?d.legal_notice:(d.legal_notice.full_notice||d.legal_notice.short_notice||""))}</p>`;
 if(!h)h=`<div class="next-action"><strong>${APP.lang==="en"?"Continue your flight preparation":"Continúa la preparación de tu vuelo"}</strong><p>${APP.lang==="en"?"Enter the airline and open the available official flight source to verify the current itinerary.":"Indica la aerolínea y abre la fuente de vuelo disponible para verificar directamente el itinerario vigente."}</p></div>`;
 b.innerHTML=h
}
async function charterSources(){
 if(!requirePaid())return;
 try{
  const d=await api("/api/v1/flight/sources",{method:"POST",body:JSON.stringify({origin:val("origin"),destination:val("destination"),airline:val("airline"),language:lang()})});
  renderSources(d.charter_sources||d.sources||[])
 }catch(e){
  try{
   const d=await api(`/api/v1/sources/charter?language=${encodeURIComponent(lang())}`,{method:"GET"});
   renderSources(d.sources||d.charter_sources||[])
  }catch(x){msg(x.message||e.message||"No se pudieron cargar las fuentes.","error")}
 }
}
function renderSources(items){
 const b=$("#sourcesResult")||$("#flightResult");if(!b)return;
 b.innerHTML=Array.isArray(items)&&items.length?sourceList(items):`<div class="next-action"><strong>${APP.lang==="en"?"Official sources":"Fuentes oficiales"}</strong><p>${APP.lang==="en"?"Use the official source for your airline and route to verify the current information.":"Usa la fuente oficial de tu aerolínea y ruta para verificar la información vigente."}</p></div>`
}
async function officialSources(){
 if(!requirePaid())return;
 try{
  const d=await api("/api/v1/sources/official",{method:"GET"});
  renderSources(d.sources||d.official_sources||d.links||[])
 }catch(e){msg(e.message||"No se pudieron cargar las fuentes oficiales.","error")}
}
async function cubaGuide(){
 if(!requirePaid())return;
 try{
  const d=await api(`/api/v1/cuba/official?language=${encodeURIComponent(lang())}`,{method:"GET"});
  renderObject($("#cubaResult"),d)
 }catch(e){msg(e.message||"No se pudo cargar la preparación de Cuba.","error")}
}
async function guide(){
 if(!requirePaid())return;
 const payload={language:lang(),flight:dataObject()};
 try{renderGuide(await api("/api/v1/guide",{method:"POST",body:JSON.stringify(payload)}))}
 catch(e){msg(e.message||"No se pudo preparar la guía.","error")}
}
function renderGuide(d){
 const b=$("#guideResult");if(!b)return;
 let h="";
 if(d.next_action)h+=`<div class="next-action"><strong>${esc(d.next_action)}</strong></div>`;
 if(Array.isArray(d.steps)&&d.steps.length)h+=`<ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||JSON.stringify(x)))}</li>`).join("")}</ol>`;
 if(Array.isArray(d.cuba_steps)&&d.cuba_steps.length)h+=`<h3>${APP.lang==="en"?"Cuba preparation":"Preparación para Cuba"}</h3><ol>${d.cuba_steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||JSON.stringify(x)))}</li>`).join("")}</ol>`;
 if(Array.isArray(d.official_sources)&&d.official_sources.length)h+=sourceList(d.official_sources);
 if(d.legal_notice)h+=`<p>${esc(typeof d.legal_notice==="string"?d.legal_notice:(d.legal_notice.full_notice||d.legal_notice.short_notice||""))}</p>`;
 b.innerHTML=h||`<div class="next-action"><strong>${APP.lang==="en"?"Continue your preparation":"Continúa tu preparación"}</strong></div>`
}
function renderObject(b,d){
 if(!b)return;
 if(typeof d==="string"){b.innerHTML=`<p>${esc(d)}</p>`;return}
 let h="";
 if(d.title)h+=`<h2>${esc(d.title)}</h2>`;
 if(d.intro)h+=`<p>${esc(d.intro)}</p>`;
 if(d.short_notice)h+=`<p>${esc(d.short_notice)}</p>`;
 if(d.status){
  const l={prohibited:APP.lang==="en"?"Restricted/prohibited":"Restringido/prohibido",conditional:APP.lang==="en"?"Conditions apply":"Tiene condiciones",allowed:APP.lang==="en"?"May be allowed":"Puede estar permitido",unknown:APP.lang==="en"?"Needs verification":"Necesita verificación"};
  h+=`<p><strong>${esc(l[d.status]||d.status)}</strong></p>`
 }
 ["message","reason","explanation"].forEach(k=>{if(d[k])h+=`<p>${esc(d[k])}</p>`});
 if(d.baggage_place)h+=`<p><strong>${APP.lang==="en"?"Baggage:":"Equipaje:"}</strong> ${esc(d.baggage_place)}</p>`;
 if(Array.isArray(d.conditions)&&d.conditions.length)h+=`<h3>${APP.lang==="en"?"Conditions":"Condiciones"}</h3><ul>${d.conditions.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`;
 if(Array.isArray(d.missing_information)&&d.missing_information.length)h+=`<h3>${APP.lang==="en"?"Still needed":"Información que falta"}</h3><ul>${d.missing_information.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`;
 if(d.source)h+=`<p><strong>${APP.lang==="en"?"Source:":"Fuente:"}</strong> ${esc(d.source)}</p>`;
 if(d.source_name)h+=`<p>${esc(d.source_name)}</p>`;
 if(d.verified===true)h+=`<p>${APP.lang==="en"?"Verified source information.":"Información de fuente verificada."}</p>`;
 if(d.official_link)h+=`<p><a href="${esc(d.official_link)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open official source":"Abrir fuente oficial"}</a></p>`;
 const s=d.sources||d.official_sources||d.links||[];
 if(Array.isArray(s)&&s.length)h+=sourceList(s);
 if(d.next_action)h+=`<p><strong>${esc(d.next_action)}</strong></p>`;
 if(d.legal_notice)h+=`<p>${esc(typeof d.legal_notice==="string"?d.legal_notice:(d.legal_notice.full_notice||d.legal_notice.short_notice||""))}</p>`;
 b.innerHTML=h||`<div class="next-action"><strong>${APP.lang==="en"?"Continue":"Continúa"}</strong></div>`
}
async function legal(){
 try{
  const d=await api(`/api/v1/legal?language=${encodeURIComponent(lang())}`,{method:"GET"}),b=$("#legalResult");
  if(!b)return;
  let h="";
  ["short_notice","full_notice","user_guidance","source_notice"].forEach(k=>{if(d[k])h+=`<p>${esc(d[k])}</p>`});
  b.innerHTML=h||`<p>${APP.lang==="en"?"Review the service information.":"Revisa la información del servicio."}</p>`
 }catch(e){msg(e.message||"No se pudo cargar el aviso legal.","error")}
}
async function itemConsult(){
 if(!requirePaid())return;
 const item=val("itemName"),quantity=val("itemQty")||"1",description=val("itemDescription");
 if(!item){msg(APP.lang==="en"?"Enter the item to continue.":"Escribe el artículo para continuar.","warn");return}
 try{
  const d=await api("/api/v1/consultar-articulo",{method:"POST",body:JSON.stringify({item,quantity,description,language:lang(),baggage_type:val("baggage_type"),airline:val("airline"),destination:val("destination"),origin:val("origin"),cabin:val("cabin"),fare:val("fare")})});
  renderObject($("#itemResult"),d)
 }catch(e){msg(e.message||"No se pudo preparar la consulta del artículo.","error")}
}
async function teach(){
 if(!requirePaid())return;
 const term=val("term");
 if(!term){msg(APP.lang==="en"?"Enter a term to continue.":"Escribe un término para continuar.","warn");return}
 try{renderObject($("#teachResult"),await api("/api/v1/item/teach",{method:"POST",body:JSON.stringify({term,language:lang()})}))}
 catch(e){msg(e.message||"No se pudo preparar la explicación.","error")}
}
function bind(){
 if(APP._bound)return;
 APP._bound=true;
 $("#langBtn")?.addEventListener("click",toggleLang);
 $("#adminBtn")?.addEventListener("click",()=>setView("admin"));
 $("#startBtn")?.addEventListener("click",()=>{if(requirePaid())setView("flight")});
 $("#payBtn")?.addEventListener("click",createCheckout);
 $("#flightBtn")?.addEventListener("click",flight);
 $("#itemBtn")?.addEventListener("click",itemConsult);
 $("#teachBtn")?.addEventListener("click",teach);
 $("#adminLoginBtn")?.addEventListener("click",adminLogin);
 document.addEventListener("click",e=>{
  const b=e.target.closest("[data-action]");if(!b)return;
  const a=b.dataset.action;
  if(a==="home")home();
  else if(a==="flight"){if(requirePaid())setView("flight")}
  else if(a==="item"){if(requirePaid())setView("item")}
  else if(a==="baggage"){if(requirePaid()){setView("baggage")}}
  else if(a==="cuba"){if(requirePaid()){setView("cuba");cubaGuide()}}
  else if(a==="guide"){if(requirePaid()){setView("guide");guide()}}
  else if(a==="sources"){if(requirePaid()){setView("sources");officialSources()}}
  else if(a==="teach"){if(requirePaid())setView("teach")}
  else if(a==="legal"){setView("legal");legal()}
  else if(a==="pay"||a==="payment")createCheckout();
  else if(a==="logout")logout()
 });
}
async function init(){
 document.documentElement.lang=APP.lang;
 bind();
 translate();
 ensureAirlineField();
 setView("loading");
 await loadConfig();
 const paid=active()?await checkSession():false;
 if(!paid)setView("payment");
 const verified=await verifyPayment();
 if(verified)await checkSession();
 else if(active())await checkSession();
}
window.APP=APP;
window.createCheckout=createCheckout;
window.adminLogin=adminLogin;
window.logout=logout;
window.flight=flight;
window.charterSources=charterSources;
window.flightSources=charterSources;
window.officialSources=officialSources;
window.cubaGuide=cubaGuide;
window.guide=guide;
window.itemConsult=itemConsult;
window.teach=teach;
window.toggleLang=toggleLang;
window.legal=legal;
document.addEventListener("DOMContentLoaded",init);
