"use strict";
const APP={name:"QUE QUIERES LLEVAR",version:"8.1.2",lang:localStorage.getItem("qql_lang")||"es",serviceToken:localStorage.getItem("qql_service_token")||"",adminToken:localStorage.getItem("qql_admin_token")||"",session:null,config:null,_bound:false,practice:null,adminTaps:0,adminTapTimer:null};
const $=(s,r=document)=>r.querySelector(s),$$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));
const txt=v=>String(v??"").trim();
const val=id=>txt(document.getElementById(id)?.value);
function active(){return!!(APP.serviceToken||APP.adminToken)}
function headers(extra={}){const h={"Content-Type":"application/json",...extra};if(APP.serviceToken)h["X-Service-Token"]=APP.serviceToken;if(APP.adminToken)h["X-Admin-Token"]=APP.adminToken;return h}
function saveTokens(){localStorage.setItem("qql_service_token",APP.serviceToken||"");localStorage.setItem("qql_admin_token",APP.adminToken||"")}
function clearTokens(){APP.serviceToken="";APP.adminToken="";APP.session=null;saveTokens()}
function msg(text,type="info"){let b=$("#appMessage")||$("#message")||$(".app-message");if(!b){b=document.createElement("div");b.id="appMessage";document.body.prepend(b)}b.className=`app-message ${type}`;b.textContent=text}
async function api(path,options={},timeout=10000){
 const c=new AbortController(),tm=setTimeout(()=>c.abort(),timeout);
 try{
  const r=await fetch(path,{...options,headers:headers(options.headers||{}),signal:c.signal});
  let d={};try{d=await r.json()}catch(_){}
  if(!r.ok){const e=new Error(d.detail||d.message||`HTTP ${r.status}`);e.status=r.status;e.data=d;throw e}
  return d
 }catch(e){
  if(e.name==="AbortError")throw new Error(APP.lang==="en"?"The server took too long to respond.":"El servidor tardó demasiado en responder.");
  throw e
 }finally{clearTimeout(tm)}
}
function screens(){return["loading","home","payment","flight","item","baggage","cuba","cubaPractice","guide","sources","teach","legal","admin"].map(id=>document.getElementById(id)).filter(Boolean)}
function setView(name){screens().forEach(x=>x.classList.toggle("hidden",x.id!==name));document.body.dataset.view=name}
function home(){setView(active()?"home":"payment")}
function requirePaid(){if(active())return true;setView("payment");msg(APP.lang==="en"?"Payment or administrator access is required.":"Se requiere acceso mediante pago o administrador.","warn");return false}
function lang(){return APP.lang==="en"?"en":"es"}
function setLang(v){APP.lang=v==="en"?"en":"es";localStorage.setItem("qql_lang",APP.lang);translate();ensureAirlineField();ensureFlightPracticeButton();ensureCubaPracticeButtons()}
function toggleLang(){setLang(APP.lang==="es"?"en":"es")}
function translate(){
 document.documentElement.lang=APP.lang;
 $$("[data-es][data-en]").forEach(e=>e.textContent=e.dataset[APP.lang]||e.dataset.es||"");
 const b=$("#langBtn");if(b)b.textContent=APP.lang==="en"?"ES":"EN";
 const l=$("#loadingText");if(l)l.textContent=APP.lang==="en"?"Preparing your trip...":"Preparando tu viaje...";
 const s=$("#sessionStatus");if(s)s.textContent=active()?(APP.lang==="en"?"Access active":"Acceso activo"):(APP.lang==="en"?"Session not active":"Sesión no activa");
 const p=$("#payment .card");if(p){
  const h=p.querySelector("h2"),ps=p.querySelectorAll("p"),n=p.querySelector(".notice"),bt=$("#payBtn");
  if(h)h.textContent=APP.lang==="en"?"Activate your travel preparation":"Activa tu preparación";
  if(ps[0])ps[0].textContent=APP.lang==="en"?"Before paying, know what you receive: a simple 15-minute guided session to organize your trip, understand your flight, practice airline procedures, review baggage, practice D’Viajeros and Cuba visa/eVisa procedures, and reach official sources.":"Antes de pagar, conoce lo que recibes: una sesión guiada de 15 minutos para organizar tu viaje, entender tu vuelo, practicar procesos de la aerolínea, revisar equipaje, practicar D’Viajeros y visa/eVisa de Cuba, y llegar a las fuentes oficiales.";
  if(n)n.innerHTML=APP.lang==="en"?"<strong>What you gain:</strong> you practice before doing the real process and finish with clear next actions.":"<strong>Qué ganas:</strong> practicas antes de hacer el proceso real y terminas con próximos pasos claros.";
  if(bt)bt.textContent=APP.lang==="en"?"Continue to payment — $15.99":"Continuar al pago — $15.99";
 }
}
async function checkSession(){
 if(!active()){home();return false}
 try{
  const d=await api("/api/v1/session",{method:"GET"},7000);
  if(d.active===false){clearTokens();home();return false}
  APP.session=d;translate();home();return true
 }catch(e){
  if(e.status===401||e.status===403){clearTokens();home();return false}
  APP.session={active:true};translate();home();return true
 }
}
async function loadConfig(){
 try{APP.config=await api("/api/v1/config",{method:"GET"},7000);renderConfig(APP.config)}catch(_){}
}
function renderConfig(d){
 if(!d)return;
 $$("[data-config]").forEach(e=>{const k=e.dataset.config;if(d[k]!=null)e.textContent=d[k]})
}
async function createCheckout(){
 try{
  const d=await api("/api/v1/create-checkout-session",{method:"POST",body:JSON.stringify({language:lang()})},15000);
  const u=d.checkout_url||d.url;
  if(u)location.href=u;else msg(APP.lang==="en"?"The payment link was not received.":"No se recibió el enlace de pago.","error")
 }catch(e){msg(e.message||"No se pudo iniciar el pago.","error")}
}
async function verifyPayment(){
 const q=new URLSearchParams(location.search),sid=q.get("session_id")||q.get("checkout_session_id");
 if(!sid)return false;
 try{
  const d=await api("/api/v1/verify-payment",{method:"POST",body:JSON.stringify({session_id:sid})},15000);
  const t=d.token||d.service_token;
  if(!t)throw new Error(APP.lang==="en"?"Access could not be activated.":"No se pudo activar el acceso.");
  APP.serviceToken=t;APP.adminToken="";saveTokens();
  history.replaceState({},document.title,location.pathname);
  APP.session={active:true};setView("home");translate();
  msg(APP.lang==="en"?"Your 15-minute preparation session is active.":"Tu sesión de preparación de 15 minutos está activa.","success");
  return true
 }catch(e){msg(e.message||"No se pudo verificar el pago.","error");return false}
}
async function adminLogin(){
 const user=val("adminUser"),pass=val("adminPass");
 if(!user||!pass){msg(APP.lang==="en"?"Enter username and password.":"Escribe usuario y contraseña.","warn");return}
 try{
  const d=await api("/api/v1/admin/login",{method:"POST",body:JSON.stringify({username:user,password:pass})},15000);
  const t=d.token||d.admin_token;
  if(!t)throw new Error(APP.lang==="en"?"Administrator access could not be activated.":"No se pudo activar el acceso de administrador.");
  APP.adminToken=t;APP.serviceToken="";saveTokens();APP.session={active:true,admin:true};setView("home");translate();
  msg(APP.lang==="en"?"Administrator access is active.":"El acceso de administrador está activo.","success")
 }catch(e){msg(e.message||"No se pudo iniciar sesión.","error")}
}
function logout(){clearTokens();home();translate();msg(APP.lang==="en"?"Session closed.":"Sesión cerrada.","info")}
function ensureAirlineField(){
 const form=$("#flight")?.querySelector(".form");
 if(!form||$("#airline"))return;
 const label=document.createElement("label");
 label.textContent=APP.lang==="en"?"Airline":"Aerolínea";
 const input=document.createElement("input");
 input.id="airline";input.maxLength=40;input.placeholder=APP.lang==="en"?"Example: American Airlines":"Ej.: American Airlines";
 label.appendChild(input);
 const passengers=$("#passengers")?.closest("label");
 if(passengers)form.insertBefore(label,passengers);else form.insertBefore(label,form.querySelector("button"));
}
function ensureFlightPracticeButton(){
 const form=$("#flight")?.querySelector(".form");
 if(!form||$("#practiceAirlineBtn"))return;
 const b=document.createElement("button");
 b.id="practiceAirlineBtn";b.type="button";b.className="primary";
 b.textContent=APP.lang==="en"?"Practice with my airline":"Practicar con mi aerolínea";
 form.appendChild(b);b.addEventListener("click",startAirlinePractice)
}
function ensureCubaPracticeButtons(){
 const card=$("#cuba")?.querySelector(".card");
 if(!card||$("#practiceCubaBtn"))return;
 const wrap=document.createElement("div");wrap.className="practice-actions";
 const a=document.createElement("button");a.id="practiceCubaBtn";a.className="primary";a.type="button";a.textContent=APP.lang==="en"?"Practice D’Viajeros":"Practicar D’Viajeros";
 const v=document.createElement("button");v.id="practiceVisaBtn";v.className="primary";v.type="button";v.textContent=APP.lang==="en"?"Practice Cuba visa/eVisa":"Practicar visa/eVisa de Cuba";
 wrap.append(a,v);card.insertBefore(wrap,$("#cubaResult"));
 a.addEventListener("click",()=>startCubaPractice("dviajeros"));
 v.addEventListener("click",()=>startCubaPractice("visa"))
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
 if(!data.origin||!data.destination){msg(APP.lang==="en"?"Enter your origin and destination to continue.":"Escribe tu origen y destino para continuar.","warn");return}
 try{renderFlight(await api("/api/v1/flight/understand",{method:"POST",body:JSON.stringify(data)},15000))}
 catch(e){msg(e.message||"No se pudo preparar la información del vuelo.","error")}
}
function sourceList(items){
 if(!Array.isArray(items)||!items.length)return"";
 return `<div class="source-list">${items.map(x=>{const n=esc(x.name||"Fuente oficial"),u=esc(x.url||"#"),d=x.description?`<p>${esc(x.description)}</p>`:"";return `<div class="source-card"><strong>${n}</strong>${d}${x.url?`<a href="${u}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open source":"Abrir fuente"}</a>`:""}</div>`}).join("")}</div>`
}
function renderFlight(d){
 const b=$("#flightResult");if(!b)return;
 let h="",a=d.airline||val("airline"),o=d.origin||val("origin"),des=d.destination||val("destination"),date=d.departure_date||val("departureDate");
 if(o||des||date||a)h+=`<div class="next-action"><strong>${APP.lang==="en"?"Flight information":"Información del vuelo"}</strong>${o?`<p>Origen: ${esc(o)}</p>`:""}${des?`<p>Destino: ${esc(des)}</p>`:""}${date?`<p>Fecha: ${esc(date)}</p>`:""}${a?`<p>Aerolínea: ${esc(a)}</p>`:""}</div>`;
 if(d.understood)h+=`<p>${esc(typeof d.understood==="string"?d.understood:JSON.stringify(d.understood))}</p>`;
 if(Array.isArray(d.steps)&&d.steps.length)h+=`<h3>${APP.lang==="en"?"Next steps":"Próximos pasos"}</h3><ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||JSON.stringify(x)))}</li>`).join("")}</ol>`;
 if(d.google_flights_url)h+=`<div class="next-action"><strong>${APP.lang==="en"?"Review current flight options":"Revisa las opciones actuales de vuelo"}</strong><p><a href="${esc(d.google_flights_url)}" target="_blank" rel="noopener noreferrer">Google Flights</a></p></div>`;
 if((d.airline_sources||[]).length)h+=sourceList(d.airline_sources);
 if((d.charter_sources||[]).length)h+=sourceList(d.charter_sources);
 h+=`<div class="next-action"><strong>${APP.lang==="en"?"Practice before doing it for real":"Practica antes de hacerlo de verdad"}</strong><p>${APP.lang==="en"?"Use the Practice with my airline button. It does not purchase anything.":"Usa el botón Practicar con mi aerolínea. No realiza ninguna compra."}</p></div>`;
 b.innerHTML=h
}
async function charterSources(){
 if(!requirePaid())return;
 try{
  const d=await api("/api/v1/flight/sources",{method:"POST",body:JSON.stringify({origin:val("origin"),destination:val("destination"),airline:val("airline"),language:lang()})},12000);
  renderSources(d.charter_sources||d.sources||[])
 }catch(e){
  try{const d=await api(`/api/v1/sources/charter?language=${encodeURIComponent(lang())}`,{method:"GET"},8000);renderSources(d.sources||d.charter_sources||[])}
  catch(x){msg(x.message||e.message||"No se pudieron cargar las fuentes.","error")}
 }
}
function renderSources(items){
 const b=$("#sourcesResult")||$("#flightResult");if(!b)return;
 b.innerHTML=Array.isArray(items)&&items.length?sourceList(items):`<div class="next-action"><strong>${APP.lang==="en"?"Official sources":"Fuentes oficiales"}</strong><p>${APP.lang==="en"?"Open the official source for your airline and route.":"Abre la fuente oficial de tu aerolínea y ruta."}</p></div>`
}
async function officialSources(){
 if(!requirePaid())return;
 try{const d=await api("/api/v1/sources/official",{method:"GET"},10000);renderSources(d.sources||d.official_sources||d.links||[])}
 catch(e){msg(e.message||"No se pudieron cargar las fuentes oficiales.","error")}
}
async function cubaGuide(){
 if(!requirePaid())return;
 try{renderObject($("#cubaResult"),await api(`/api/v1/cuba/official?language=${encodeURIComponent(lang())}`,{method:"GET"},10000))}
 catch(e){msg(e.message||"No se pudo cargar la preparación de Cuba.","error")}
}
async function guide(){
 if(!requirePaid())return;
 try{renderGuide(await api("/api/v1/guide",{method:"POST",body:JSON.stringify({language:lang(),flight:dataObject()})},10000))}
 catch(e){msg(e.message||"No se pudo preparar la guía.","error")}
}
function renderGuide(d){
 const b=$("#guideResult");if(!b)return;
 let h="";
 if(d.next_action)h+=`<div class="next-action"><strong>${esc(d.next_action)}</strong></div>`;
 if(Array.isArray(d.steps)&&d.steps.length)h+=`<ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||JSON.stringify(x)))}</li>`).join("")}</ol>`;
 if(Array.isArray(d.cuba_steps)&&d.cuba_steps.length)h+=`<h3>${APP.lang==="en"?"Cuba preparation":"Preparación para Cuba"}</h3><ol>${d.cuba_steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||JSON.stringify(x)))}</li>`).join("")}</ol>`;
 if(Array.isArray(d.official_sources)&&d.official_sources.length)h+=sourceList(d.official_sources);
 b.innerHTML=h||`<div class="next-action"><strong>${APP.lang==="en"?"Continue your preparation":"Continúa tu preparación"}</strong></div>`
}
function renderObject(b,d){
 if(!b)return;
 if(typeof d==="string"){b.innerHTML=`<p>${esc(d)}</p>`;return}
 let h="";
 ["title","intro","short_notice","message","reason","explanation"].forEach(k=>{if(d[k])h+=k==="title"?`<h2>${esc(d[k])}</h2>`:`<p>${esc(d[k])}</p>`});
 if(d.status)h+=`<p><strong>${esc(d.status)}</strong></p>`;
 if(d.baggage_place)h+=`<p><strong>Equipaje:</strong> ${esc(d.baggage_place)}</p>`;
 if(Array.isArray(d.conditions)&&d.conditions.length)h+=`<h3>${APP.lang==="en"?"Conditions":"Condiciones"}</h3><ul>${d.conditions.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`;
 if(Array.isArray(d.missing_information)&&d.missing_information.length)h+=`<h3>${APP.lang==="en"?"Still needed":"Información que falta"}</h3><ul>${d.missing_information.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`;
 if(d.source_name)h+=`<p>${esc(d.source_name)}</p>`;
 if(d.official_link)h+=`<p><a href="${esc(d.official_link)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open official source":"Abrir fuente oficial"}</a></p>`;
 const s=d.sources||d.official_sources||d.links||[];if(Array.isArray(s)&&s.length)h+=sourceList(s);
 if(d.next_action)h+=`<p><strong>${esc(d.next_action)}</strong></p>`;
 b.innerHTML=h||`<div class="next-action">${APP.lang==="en"?"Continue":"Continúa"}</div>`
}
async function legal(){
 try{
  const d=await api(`/api/v1/legal?language=${encodeURIComponent(lang())}`,{method:"GET"},8000),b=$("#legalResult");
  if(!b)return;
  let h="";["short_notice","full_notice","user_guidance","source_notice"].forEach(k=>{if(d[k])h+=`<p>${esc(d[k])}</p>`});
  b.innerHTML=h||`<p>${APP.lang==="en"?"Review the service information.":"Revisa la información del servicio."}</p>`
 }catch(e){msg(e.message||"No se pudo cargar el aviso legal.","error")}
}
async function itemConsult(){
 if(!requirePaid())return;
 const item=val("itemName"),quantity=val("itemQty")||"1",description=val("itemDescription");
 if(!item){msg(APP.lang==="en"?"Enter the item to continue.":"Escribe el artículo para continuar.","warn");return}
 try{renderObject($("#itemResult"),await api("/api/v1/consultar-articulo",{method:"POST",body:JSON.stringify({item,quantity,description,language:lang(),baggage_type:val("baggage_type"),airline:val("itemAirline")||val("airline"),destination:val("itemDestination")||val("destination"),origin:val("origin"),cabin:val("cabin"),fare:val("fare")})},15000))}
 catch(e){msg(e.message||"No se pudo preparar la consulta del artículo.","error")}
}
async function teach(){
 if(!requirePaid())return;
 const term=val("term");if(!term){msg(APP.lang==="en"?"Enter a term to continue.":"Escribe un término para continuar.","warn");return}
 try{renderObject($("#teachResult"),await api("/api/v1/item/teach",{method:"POST",body:JSON.stringify({term,language:lang()})},10000))}
 catch(e){msg(e.message||"No se pudo preparar la explicación.","error")}
}
function practiceBox(){
 let x=$("#qqlPractice");if(x)return x;
 x=document.createElement("div");x.id="qqlPractice";x.className="card";
 const host=$("#flight")||$("#cuba")||document.body;host.appendChild(x);return x
}
function closePractice(){const x=$("#qqlPractice");if(x)x.remove();APP.practice=null}
function startAirlinePractice(){if(!requirePaid())return;APP.practice={type:"airline",airline:val("airline")||"mi aerolínea",step:0};renderPractice()}
function startCubaPractice(mode){if(!requirePaid())return;APP.practice={type:"cuba",mode,step:0};renderPractice()}
function practiceSteps(){
 const p=APP.practice;
 if(p.type==="airline")return[
  APP.lang==="en"?`We will practice ${p.airline}. Nothing is purchased.`:`Practicaremos ${p.airline}. No se compra nada.`,
  APP.lang==="en"?"Open the airline's official website or app.":"Abre el sitio o aplicación oficial de la aerolínea.",
  APP.lang==="en"?"Enter origin, destination and travel date.":"Escribe origen, destino y fecha del viaje.",
  APP.lang==="en"?"Review flight options, airports, times and stops.":"Revisa vuelos, aeropuertos, horarios y escalas.",
  APP.lang==="en"?"Select a flight for practice only.":"Selecciona un vuelo solamente para practicar.",
  APP.lang==="en"?"Review passenger information using fictitious information.":"Revisa los datos del pasajero usando información ficticia.",
  APP.lang==="en"?"Review baggage and fare conditions.":"Revisa equipaje y condiciones de la tarifa.",
  APP.lang==="en"?"Stop before payment. The real process must be completed on the official airline site/app.":"Detente antes del pago. El proceso real debe hacerse en el sitio o aplicación oficial."
 ];
 if(p.mode==="dviajeros")return[
  APP.lang==="en"?"D’Viajeros practice. This is only a simulation.":"Práctica de D’Viajeros. Esto es solamente una simulación.",
  APP.lang==="en"?"Open the official D’Viajeros portal.":"Abre el portal oficial de D’Viajeros.",
  APP.lang==="en"?"Identify the information requested by the official form.":"Identifica la información que solicita el formulario oficial.",
  APP.lang==="en"?"Practice the order of the fields without entering sensitive information.":"Practica el orden de los campos sin introducir información sensible.",
  APP.lang==="en"?"Review the information before submitting the real form.":"Revisa la información antes de enviar el formulario real.",
  APP.lang==="en"?"Complete the real process only at the official portal.":"Realiza el proceso real solamente en el portal oficial."
 ];
 return[
  APP.lang==="en"?"Cuba visa/eVisa practice. This is only a simulation.":"Práctica de visa/eVisa de Cuba. Esto es solamente una simulación.",
  APP.lang==="en"?"Open the official Cuba visa/eVisa source.":"Abre la fuente oficial de visa/eVisa de Cuba.",
  APP.lang==="en"?"Check the requirement for your nationality.":"Comprueba el requisito según tu nacionalidad.",
  APP.lang==="en"?"Review the documents and information requested.":"Revisa los documentos y la información solicitada.",
  APP.lang==="en"?"Practice the order of the process without submitting anything.":"Practica el orden del proceso sin enviar nada.",
  APP.lang==="en"?"Complete the real process only through the applicable official source.":"Realiza el proceso real solamente mediante la fuente oficial correspondiente."
 ]
}
function renderPractice(){
 const p=APP.practice;if(!p)return;
 const steps=practiceSteps(),b=practiceBox(),title=p.type==="airline"?(APP.lang==="en"?`Practice: ${p.airline}`:`Práctica: ${p.airline}`):(p.mode==="dviajeros"?(APP.lang==="en"?"Practice: D’Viajeros":"Práctica: D’Viajeros"):(APP.lang==="en"?"Practice: Cuba visa/eVisa":"Práctica: visa/eVisa de Cuba"));
 b.innerHTML=`<div><button id="practiceClose" type="button">× ${APP.lang==="en"?"Close":"Cerrar"}</button><h2>${esc(title)}</h2><div class="next-action"><strong>${APP.lang==="en"?`Step ${p.step+1} of ${steps.length}`:`Paso ${p.step+1} de ${steps.length}`}</strong><p>${esc(steps[p.step])}</p></div><div class="practice-actions">${p.step?`<button id="practiceBack" class="primary" type="button">${APP.lang==="en"?"Back":"Atrás"}</button>`:""}${p.step<steps.length-1?`<button id="practiceNext" class="primary" type="button">${APP.lang==="en"?"Next":"Siguiente"}</button>`:`<button id="practiceFinish" class="primary" type="button">${APP.lang==="en"?"Finish":"Terminar"}</button>`}</div></div>`;
 $("#practiceClose").onclick=closePractice;
 $("#practiceBack")?.addEventListener("click",()=>{p.step--;renderPractice()});
 $("#practiceNext")?.addEventListener("click",()=>{p.step++;renderPractice()});
 $("#practiceFinish")?.addEventListener("click",finishPractice)
}
function finishPractice(){
 const p=APP.practice,b=$("#qqlPractice");if(!b)return;
 const s=p.type==="airline"?(APP.lang==="en"?"For the real process, use the airline's official website/app.":"Para el proceso real, usa el sitio o aplicación oficial de la aerolínea."):p.mode==="dviajeros"?(APP.lang==="en"?"Official D’Viajeros: https://dviajeros.mitrans.gob.cu/":"D’Viajeros oficial: https://dviajeros.mitrans.gob.cu/"):(APP.lang==="en"?"Official Cuba eVisa: https://evisacuba.cu/":"eVisa Cuba oficial: https://evisacuba.cu/");
 b.innerHTML=`<div><button id="practiceClose" type="button">× ${APP.lang==="en"?"Close":"Cerrar"}</button><h2>${APP.lang==="en"?"Practice completed":"Práctica completada"}</h2><div class="next-action"><strong>${APP.lang==="en"?"You are ready for the real process.":"Ya puedes pasar al proceso real."}</strong><p>${esc(s)}</p><p>${APP.lang==="en"?"No real information was submitted or purchased.":"No se envió información real ni se realizó ninguna compra."}</p></div></div>`;
 $("#practiceClose").onclick=closePractice
}
function createHiddenAdminAccess(){
 const btn=$("#adminBtn");
 if(btn)btn.style.display="none";
 const homeScreen=$("#home");
 if(!homeScreen)return;
 homeScreen.addEventListener("click",adminTapHandler,true);
}
function adminTapHandler(e){
 if(e.target.closest("button,input,textarea,select,a"))return;
 APP.adminTaps++;
 clearTimeout(APP.adminTapTimer);
 APP.adminTapTimer=setTimeout(()=>APP.adminTaps=0,900);
 if(APP.adminTaps>=3){
  APP.adminTaps=0;
  clearTimeout(APP.adminTapTimer);
  openHiddenAdmin()
 }
}
function openHiddenAdmin(){
 const existing=$("#qqlHiddenAdmin");
 if(existing){existing.remove();return}
 const box=document.createElement("div");
 box.id="qqlHiddenAdmin";
 box.innerHTML=`<div class="qql-admin-overlay"><div class="qql-admin-card"><button id="qqlAdminClose" type="button">×</button><h2>ADMIN</h2><p>${APP.lang==="en"?"Enter administrator credentials.":"Escribe usuario y contraseña."}</p><label>${APP.lang==="en"?"Username":"Usuario"}<input id="qqlHiddenUser" type="text" autocomplete="username"></label><label>${APP.lang==="en"?"Password":"Contraseña"}<input id="qqlHiddenPass" type="password" autocomplete="current-password"></label><button id="qqlHiddenLogin" class="primary" type="button">${APP.lang==="en"?"Sign in":"Entrar"}</button><p id="qqlHiddenMsg" class="message"></p></div></div>`;
 document.body.appendChild(box);
 $("#qqlAdminClose").onclick=()=>box.remove();
 $("#qqlHiddenLogin").onclick=hiddenAdminLogin;
 $("#qqlHiddenUser").focus();
 $("#qqlHiddenPass").addEventListener("keydown",e=>{if(e.key==="Enter")hiddenAdminLogin()});
}
async function hiddenAdminLogin(){
 const u=txt($("#qqlHiddenUser")?.value),p=txt($("#qqlHiddenPass")?.value),m=$("#qqlHiddenMsg");
 if(!u||!p){if(m)m.textContent=APP.lang==="en"?"Enter username and password.":"Escribe usuario y contraseña.";return}
 try{
  const d=await api("/api/v1/admin/login",{method:"POST",body:JSON.stringify({username:u,password:p})},15000);
  const t=d.token||d.admin_token;
  if(!t)throw new Error(APP.lang==="en"?"Administrator access could not be activated.":"No se pudo activar el acceso de administrador.");
  APP.adminToken=t;APP.serviceToken="";APP.session={active:true,admin:true};saveTokens();
  $("#qqlHiddenAdmin")?.remove();
  setView("home");translate();
  msg(APP.lang==="en"?"Administrator access is active.":"El acceso de administrador está activo.","success");
 }catch(e){if(m)m.textContent=e.message||"No se pudo iniciar sesión."}
}
function bind(){
 if(APP._bound)return;
 APP._bound=true;
 $("#langBtn")?.addEventListener("click",toggleLang);
 $("#adminBtn")?.addEventListener("click",openHiddenAdmin);
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
  else if(a==="baggage"){if(requirePaid())setView("baggage")}
  else if(a==="cuba"){if(requirePaid()){setView("cuba");cubaGuide()}}
  else if(a==="guide"){if(requirePaid()){setView("guide");guide()}}
  else if(a==="sources"){if(requirePaid()){setView("sources");officialSources()}}
  else if(a==="teach"){if(requirePaid())setView("teach")}
  else if(a==="legal"){setView("legal");legal()}
  else if(a==="baggageSources"){if(requirePaid()){setView("sources");charterSources()}}
  else if(a==="cuba-visa"){if(requirePaid()){setView("cubaPractice");startCubaPractice("visa")}}
  else if(a==="cuba-dviajeros"){if(requirePaid()){setView("cubaPractice");startCubaPractice("dviajeros")}}
  else if(a==="cuba-official"){if(requirePaid()){setView("cuba");cubaGuide()}}
  else if(a==="practice"){if(requirePaid())setView("practice")}
  else if(a==="pay"||a==="payment")createCheckout();
  else if(a==="logout")logout()
 });
 createHiddenAdminAccess()
}
function init(){
 document.documentElement.lang=APP.lang;
 bind();
 translate();
 ensureAirlineField();
 ensureFlightPracticeButton();
 ensureCubaPracticeButtons();
 if(active())setView("home");else setView("payment");
 Promise.resolve().then(async()=>{
  await loadConfig();
  if(active())await checkSession();
  const q=new URLSearchParams(location.search);
  if(q.get("session_id")||q.get("checkout_session_id")){
   const ok=await verifyPayment();
   if(ok)await checkSession()
  }
 }).catch(()=>{})
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
window.startAirlinePractice=startAirlinePractice;
window.startCubaPractice=startCubaPractice;
window.closePractice=closePractice;
document.addEventListener("DOMContentLoaded",init);
