"use strict";
const APP={name:"QUE QUIERES LLEVAR",version:"8.0.3",lang:localStorage.getItem("qql_lang")||"es",serviceToken:localStorage.getItem("qql_service_token")||"",adminToken:localStorage.getItem("qql_admin_token")||"",session:null,config:null};
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
const txt=v=>String(v??"").trim();
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function active(){return !!(APP.serviceToken||APP.adminToken)}
function headers(extra={}){const h={"Content-Type":"application/json",...extra};if(APP.serviceToken)h["X-Service-Token"]=APP.serviceToken;if(APP.adminToken)h["X-Admin-Token"]=APP.adminToken;return h}
function saveTokens(){localStorage.setItem("qql_service_token",APP.serviceToken||"");localStorage.setItem("qql_admin_token",APP.adminToken||"")}
function clearTokens(){APP.serviceToken="";APP.adminToken="";APP.session=null;saveTokens()}
async function api(path,options={},timeout=25000){
  const ctl=new AbortController(),tm=setTimeout(()=>ctl.abort(),timeout);
  try{
    const r=await fetch(path,{...options,headers:headers(options.headers||{}),signal:ctl.signal});
    let d={};try{d=await r.json()}catch(_){}
    if(!r.ok){const e=new Error(d.detail||d.message||`HTTP ${r.status}`);e.status=r.status;e.data=d;throw e}
    return d
  }finally{clearTimeout(tm)}
}
function msg(text,type="info"){
  let box=$("#appMessage")||$("#message")||$(".app-message");
  if(!box){box=document.createElement("div");box.id="appMessage";document.body.prepend(box)}
  box.className=`app-message ${type}`;box.textContent=text
}
function setView(name){
  const views=$$("[data-view]");
  views.forEach(x=>x.hidden=x.dataset.view!==name);
  const target=document.getElementById(name);
  if(target&&target.dataset.view===name)target.hidden=false;
  document.body.dataset.view=name
}
function home(){if(!active()){setView("payment");return}setView("home")}
function requirePaid(){
  if(active())return true;
  setView("payment");msg(APP.lang==="en"?"Payment or administrator access is required.":"Se requiere acceso mediante pago o administrador.","warn");return false
}
function lang(){return APP.lang==="en"?"en":"es"}
function setLang(v){APP.lang=v==="en"?"en":"es";localStorage.setItem("qql_lang",APP.lang);document.documentElement.lang=APP.lang;translate();loadConfig()}
function translate(){
  $$("[data-es][data-en]").forEach(el=>{el.textContent=el.dataset[APP.lang]||el.dataset.es||""});
  const b=$("#langBtn");if(b)b.textContent=APP.lang==="en"?"ES":"EN"
}
function toggleLang(){setLang(APP.lang==="es"?"en":"es")}
async function checkSession(){
  if(!active()){home();return false}
  try{
    const d=await api("/api/v1/session",{method:"GET"});
    if(d.active===false){clearTokens();home();return false}
    APP.session=d;home();return true
  }catch(e){
    if(e.status===401||e.status===403){clearTokens();home();return false}
    home();return true
  }
}
async function loadConfig(){
  try{APP.config=await api("/api/v1/config",{method:"GET"});renderConfig(APP.config)}catch(_){}
}
function renderConfig(d){
  if(!d)return;
  $$("[data-config]").forEach(el=>{const k=el.dataset.config;if(d[k]!=null)el.textContent=d[k]});
}
async function createCheckout(){
  try{
    const d=await api("/api/v1/create-checkout-session",{method:"POST",body:JSON.stringify({language:lang()})});
    const u=d.checkout_url||d.url;
    if(u)location.href=u;else msg(APP.lang==="en"?"Checkout link unavailable.":"No se recibió el enlace de pago.","error")
  }catch(e){msg(e.message||"Error al crear el pago.","error")}
}
async function verifyPayment(){
  const q=new URLSearchParams(location.search),sid=q.get("session_id")||q.get("checkout_session_id");
  if(!sid)return;
  try{
    const d=await api("/api/v1/verify-payment",{method:"POST",body:JSON.stringify({session_id:sid})});
    const t=d.token||d.service_token;
    if(t){APP.serviceToken=t;saveTokens();history.replaceState({},document.title,location.pathname);await checkSession();msg(APP.lang==="en"?"Access activated.":"Acceso activado.","success")}
  }catch(e){msg(e.message||"No se pudo verificar el pago.","error")}
}
async function adminLogin(){
  const user=txt($("#adminUsername")?.value),pass=txt($("#adminPassword")?.value);
  if(!user||!pass){msg(APP.lang==="en"?"Enter username and password.":"Escribe usuario y contraseña.","warn");return}
  try{
    const d=await api("/api/v1/admin/login",{method:"POST",body:JSON.stringify({username:user,password:pass})});
    const t=d.token||d.admin_token;
    if(!t)throw new Error(APP.lang==="en"?"Administrator token was not returned.":"No se recibió el token de administrador.");
    APP.adminToken=t;saveTokens();await checkSession();msg(APP.lang==="en"?"Administrator access activated.":"Acceso de administrador activado.","success")
  }catch(e){msg(e.message||"No se pudo iniciar sesión.","error")}
}
function logout(){clearTokens();setView("payment");msg(APP.lang==="en"?"Session closed.":"Sesión cerrada.","info")}
function val(id){return txt(document.getElementById(id)?.value)}
function dataObject(){
  const o={language:lang()};
  ["origin","destination","departure_date","return_date","airline","cabin","fare","passengers","stops"].forEach(k=>{const v=val(k);if(v!=="")o[k]=k==="passengers"||k==="stops"?Number(v):v});
  return o
}
async function flight(){
  if(!requirePaid())return;
  const data=dataObject();
  if(!data.origin||!data.destination){msg(APP.lang==="en"?"Enter origin and destination.":"Escribe origen y destino.","warn");return}
  try{
    const d=await api("/api/v1/flight/understand",{method:"POST",body:JSON.stringify(data)});
    renderFlight(d)
  }catch(e){msg(e.message||"No se pudo procesar el vuelo.","error")}
}
function renderFlight(d){
  const box=$("#flightResult")||$("#flightResults");
  if(!box)return;
  let h="";
  if(d.message)h+=`<p>${esc(d.message)}</p>`;
  if(d.google_flights_url)h+=`<p><a href="${esc(d.google_flights_url)}" target="_blank" rel="noopener">Google Flights</a></p>`;
  const chars=d.charter_sources||[];
  if(chars.length)h+=`<h3>${APP.lang==="en"?"Charter flight/travel providers":"Proveedores de vuelos chárter/servicios de viaje"}</h3>${sourceList(chars)}`;
  const airs=d.airline_sources||[];
  if(airs.length)h+=`<h3>${APP.lang==="en"?"Airline sources":"Fuentes de aerolíneas"}</h3>${sourceList(airs)}`;
  if(d.next_action)h+=`<p><strong>${esc(d.next_action)}</strong></p>`;
  box.innerHTML=h||`<p>${esc(APP.lang==="en"?"No verified flight results were returned.":"No se recibieron resultados de vuelos verificados.")}</p>`;
}
function sourceList(items){
  return `<div class="source-list">${items.map(x=>`<div class="source-card"><strong>${esc(x.name)}</strong>${x.description?`<p>${esc(x.description)}</p>`:""}<a href="${esc(x.url)}" target="_blank" rel="noopener">Abrir fuente oficial</a>${x.alternate_url?` <a href="${esc(x.alternate_url)}" target="_blank" rel="noopener">Alternativa</a>`:""}</div>`).join("")}</div>`
}
async function charterSources(){
  if(!requirePaid())return;
  try{
    const d=await api("/api/v1/flight/sources",{method:"POST",body:JSON.stringify({origin:val("origin"),destination:val("destination"),language:lang()})});
    renderSources(d.charter_sources||d.sources||[])
  }catch(e){
    try{
      const d=await api("/api/v1/sources/charter",{method:"GET"});renderSources(d.sources||d.charter_sources||[])
    }catch(x){msg(x.message||e.message||"No se pudieron cargar las fuentes.","error")}
  }
}
function renderSources(items){
  const box=$("#flightSourcesResult")||$("#charterSourcesResult")||$("#sourcesResult");
  if(box)box.innerHTML=items.length?sourceList(items):`<p>${esc(APP.lang==="en"?"No sources available.":"No hay fuentes disponibles.")}</p>`;
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
    const d=await api("/api/v1/cuba/official",{method:"GET"});
    renderObject($("#guideResult")||$("#cubaGuideResult"),d)
  }catch(e){msg(e.message||"No se pudo cargar la guía de Cuba.","error")}
}
async function guide(){
  if(!requirePaid())return;
  const topic=val("guideTopic")||val("topic")||"";
  const payload={language:lang(),topic,flight:dataObject()};
  try{
    const d=await api("/api/v1/guide",{method:"POST",body:JSON.stringify(payload)});
    renderGuide(d)
  }catch(e){msg(e.message||"No se pudo cargar la guía.","error")}
}
function renderGuide(d){
  const box=$("#guideResult")||$("#result")||$("#guideResults");
  if(!box)return;
  let h="";
  if(d.next_action)h+=`<div class="next-action"><strong>${esc(d.next_action)}</strong></div>`;
  if(Array.isArray(d.steps)&&d.steps.length)h+=`<ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||JSON.stringify(x)))}</li>`).join("")}</ol>`;
  if(Array.isArray(d.cuba_steps)&&d.cuba_steps.length)h+=`<h3>${APP.lang==="en"?"Cuba steps":"Pasos para Cuba"}</h3><ol>${d.cuba_steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||JSON.stringify(x)))}</li>`).join("")}</ol>`;
  if(Array.isArray(d.official_sources)&&d.official_sources.length)h+=sourceList(d.official_sources);
  if(d.legal_notice)h+=`<p>${esc(typeof d.legal_notice==="string"?d.legal_notice:(d.legal_notice.full_notice||d.legal_notice.short_notice||""))}</p>`;
  box.innerHTML=h||`<p>${esc(APP.lang==="en"?"No guide information was returned.":"No se recibió información de la guía.")}</p>`;
}
function renderObject(box,d){
  if(!box)return;
  if(typeof d==="string"){box.innerHTML=`<p>${esc(d)}</p>`;return}
  let h="";
  if(d.title)h+=`<h2>${esc(d.title)}</h2>`;
  if(d.intro)h+=`<p>${esc(d.intro)}</p>`;
  if(d.short_notice)h+=`<p>${esc(d.short_notice)}</p>`;
  if(d.important_requirements)h+=`<h3>${esc(APP.lang==="en"?"Important requirements":"Requisitos importantes")}</h3><ul>${(Array.isArray(d.important_requirements)?d.important_requirements:[d.important_requirements]).map(x=>`<li>${esc(typeof x==="string"?x:JSON.stringify(x))}</li>`).join("")}</ul>`;
  const src=d.sources||d.official_sources||d.links||[];
  if(Array.isArray(src)&&src.length)h+=sourceList(src);
  if(d.next_action)h+=`<p><strong>${esc(d.next_action)}</strong></p>`;
  box.innerHTML=h||`<pre>${esc(JSON.stringify(d,null,2))}</pre>`;
}
async function legal(){
  try{
    const d=await api("/api/v1/legal",{method:"GET"});
    const box=$("#legalResult")||$("#legalNotice")||$("#legal");
    if(!box)return;
    const text=d.full_notice||d.short_notice||d.intro||d.user_guidance||d.source_notice||"";
    box.innerHTML=`<p>${esc(text)}</p>`;
    if(d.user_guidance)box.innerHTML+=`<p>${esc(d.user_guidance)}</p>`;
    if(d.source_notice)box.innerHTML+=`<p>${esc(d.source_notice)}</p>`;
  }catch(e){msg(e.message||"No se pudo cargar el aviso legal.","error")}
}
async function itemConsult(){
  if(!requirePaid())return;
  const item=val("item")||val("article")||val("itemName"),quantity=val("quantity")||"1",description=val("description")||"";
  if(!item){msg(APP.lang==="en"?"Enter the item.":"Escribe el artículo.","warn");return}
  try{
    const d=await api("/api/v1/consultar-articulo",{method:"POST",body:JSON.stringify({item,quantity,description,language:lang()})});
    renderObject($("#itemResult")||$("#baggageResult")||$("#consultResult"),d)
  }catch(e){msg(e.message||"No se pudo consultar el artículo.","error")}
}
async function teach(){
  if(!requirePaid())return;
  const term=val("term")||val("item")||"";
  if(!term){msg(APP.lang==="en"?"Enter a term.":"Escribe un término.","warn");return}
  try{
    const d=await api("/api/v1/item/teach",{method:"POST",body:JSON.stringify({term,language:lang()})});
    renderObject($("#teachResult")||$("#itemTeachResult"),d)
  }catch(e){msg(e.message||"No se pudo explicar el término.","error")}
}
function bind(){
  document.addEventListener("click",e=>{
    const b=e.target.closest("[data-action]");if(!b)return;
    const a=b.dataset.action;
    if(a==="lang")toggleLang();
    else if(a==="payment"||a==="pay")createCheckout();
    else if(a==="admin-login")adminLogin();
    else if(a==="logout")logout();
    else if(a==="home")home();
    else if(a==="flight"||a==="search-flight"||a==="flight-understand")flight();
    else if(a==="flight-sources"||a==="charter-sources")charterSources();
    else if(a==="official-sources"||a==="sources")officialSources();
    else if(a==="guide")guide();
    else if(a==="cuba-guide")cubaGuide();
    else if(a==="legal")legal();
    else if(a==="consult-item"||a==="baggage")itemConsult();
    else if(a==="teach-item"||a==="teach")teach();
  });
  const lb=$("#langBtn");if(lb)lb.addEventListener("click",toggleLang);
  const pb=$("#payBtn")||$("#paymentBtn");if(pb)pb.addEventListener("click",createCheckout);
  const ab=$("#adminLoginBtn");if(ab)ab.addEventListener("click",adminLogin);
  const fb=$("#flightBtn")||$("#searchFlightBtn");if(fb)fb.addEventListener("click",flight);
  const fs=$("#flightSourcesBtn");if(fs)fs.addEventListener("click",charterSources);
  const cs=$("#charterSourcesBtn");if(cs)cs.addEventListener("click",charterSources);
  const os=$("#officialSourcesBtn");if(os)os.addEventListener("click",officialSources);
  const gb=$("#guideBtn");if(gb)gb.addEventListener("click",guide);
  const cb=$("#cubaGuideBtn");if(cb)cb.addEventListener("click",cubaGuide);
  const lg=$("#legalBtn");if(lg)lg.addEventListener("click",legal);
  const ib=$("#consultItemBtn")||$("#baggageBtn");if(ib)ib.addEventListener("click",itemConsult);
  const tb=$("#teachBtn");if(tb)tb.addEventListener("click",teach);
  const lo=$("#logoutBtn");if(lo)lo.addEventListener("click",logout);
}
async function init(){
  document.documentElement.lang=APP.lang;
  bind();translate();
  if(location.pathname.includes("legal")){setView("legal");legal()}
  else if(active())await checkSession();
  else setView("payment");
  await verifyPayment();
  if(active())await checkSession();
  loadConfig();
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
