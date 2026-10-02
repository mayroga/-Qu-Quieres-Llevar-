"use strict";
const APP={name:"QUE QUIERES LLEVAR",version:"8.1.1",lang:localStorage.getItem("qql_lang")||"es",serviceToken:localStorage.getItem("qql_service_token")||"",adminToken:localStorage.getItem("qql_admin_token")||"",session:null,config:null,_bound:false,practice:null};
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
function setView(name){screens().forEach(x=>x.classList.toggle("hidden",x.id!==name));document.body.dataset.view=name;window.scrollTo(0,0)}
function home(){setView(active()?"home":"payment")}
function requirePaid(){
 if(active())return true;
 setView("payment");
 msg(APP.lang==="en"?"Payment or administrator access is required.":"Se requiere acceso mediante pago o administrador.","warn");
 return false
}
function lang(){return APP.lang==="en"?"en":"es"}
function setLang(v){APP.lang=v==="en"?"en":"es";localStorage.setItem("qql_lang",APP.lang);translate();loadConfig();ensureAirlineField();renderPaymentInfo()}
function toggleLang(){setLang(APP.lang==="es"?"en":"es")}
function translate(){
 document.documentElement.lang=APP.lang;
 $$("[data-es][data-en]").forEach(e=>e.textContent=e.dataset[APP.lang]||e.dataset.es||"");
 const b=$("#langBtn");if(b)b.textContent=APP.lang==="en"?"ES":"EN";
 const l=$("#loadingText");if(l)l.textContent=APP.lang==="en"?"Preparing your trip...":"Preparando tu viaje...";
 const s=$("#sessionStatus");if(s)s.textContent=active()?(APP.lang==="en"?"Access active":"Acceso activo"):(APP.lang==="en"?"Session not active":"Sesión no activa");
 renderPaymentInfo();
}
function renderPaymentInfo(){
 const p=$("#payment .card");if(!p)return;
 const h2=p.querySelector("h2"),ps=p.querySelectorAll("p"),notice=p.querySelector(".notice"),btn=$("#payBtn");
 if(h2)h2.textContent=APP.lang==="en"?"Activate your travel preparation":"Activa tu preparación";
 if(ps[0])ps[0].textContent=APP.lang==="en"?"Before paying, know exactly what you receive: a simple 15-minute guided session from May Roga LLC to organize your trip, understand your flight, practice airline procedures, review what you can carry, prepare Cuba procedures such as D’Viajeros and visa/eVisa, and reach official sources. It does not sell tickets or complete official procedures for you.":"Antes de pagar, conoce exactamente lo que recibes: una sesión guiada de 15 minutos de May Roga LLC para organizar tu viaje, entender tu vuelo, practicar procesos de la aerolínea, revisar lo que puedes llevar, preparar procesos de Cuba como D’Viajeros y visa/eVisa, y llegar a las fuentes oficiales. No vende boletos ni realiza por ti los trámites oficiales.";
 if(notice)notice.innerHTML=APP.lang==="en"?"<strong>What you gain:</strong> you practice the process before doing it for real, learn where to click and what information to prepare, and finish with clear next actions.":"<strong>Qué ganas:</strong> practicas el proceso antes de hacerlo de verdad, aprendes dónde entrar y qué información preparar, y terminas con próximos pasos claros.";
 if(btn)btn.textContent=APP.lang==="en"?"Continue to payment — $15.99":"Continuar al pago — $15.99";
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
  if(!t)throw new Error(APP.lang==="en"?"Administrator access could not be activated.":"No se pudo activar el acceso de administrador.");
  APP.adminToken=t;APP.serviceToken="";saveTokens();await checkSession();
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
 input.id="airline";input.maxLength=40;
 input.placeholder=APP.lang==="en"?"Example: American Airlines":"Ej.: American Airlines";
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
 form.appendChild(b);
 b.addEventListener("click",startAirlinePractice);
}
function ensureCubaPracticeButtons(){
 const b=$("#cuba")?.querySelector(".card");
 if(!b||$("#practiceCubaBtn"))return;
 const wrap=document.createElement("div");
 wrap.className="practice-actions";
 wrap.innerHTML=`<button id="practiceCubaBtn" class="primary" type="button">${APP.lang==="en"?"Practice D’Viajeros":"Practicar D’Viajeros"}</button><button id="practiceVisaBtn" class="primary" type="button">${APP.lang==="en"?"Practice Cuba visa/eVisa":"Practicar visa/eVisa de Cuba"}</button>`;
 b.insertBefore(wrap,$("#cubaResult"));
 $("#practiceCubaBtn").addEventListener("click",()=>startCubaPractice("dviajeros"));
 $("#practiceVisaBtn").addEventListener("click",()=>startCubaPractice("visa"));
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
  const name=esc(x.name||"Fuente oficial"),url=esc(x.url||"#"),desc=x.description?`<p>${esc(x.description)}</p>`:"";
  const alt=x.alternate_url?` <a href="${esc(x.alternate_url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Alternative":"Alternativa"}</a>`:"";
  return `<div class="source-card"><strong>${name}</strong>${desc}${x.url?`<a href="${url}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open source":"Abrir fuente"}</a>${alt}`:""}</div>`
 }).join("")}</div>`
}
function renderFlight(d){
 const b=$("#flightResult");if(!b)return;
 let h="";
 const airline=d.airline||val("airline"),origin=d.origin||val("origin"),destination=d.destination||val("destination"),date=d.departure_date||val("departureDate");
 if(origin||destination||date||airline){
  h+=`<div class="next-action"><strong>${APP.lang==="en"?"Flight information":"Información del vuelo"}</strong>`;
  if(origin)h+=`<p>${APP.lang==="en"?"Origin: ":"Origen: "}${esc(origin)}</p>`;
  if(destination)h+=`<p>${APP.lang==="en"?"Destination: ":"Destino: "}${esc(destination)}</p>`;
  if(date)h+=`<p>${APP.lang==="en"?"Date: ":"Fecha: "}${esc(date)}</p>`;
  if(airline)h+=`<p>${APP.lang==="en"?"Airline: ":"Aerolínea: "}${esc(airline)}</p>`;
  h+="</div>"
 }
 if(d.understood)h+=`<p>${esc(typeof d.understood==="string"?d.understood:JSON.stringify(d.understood))}</p>`;
 if(Array.isArray(d.steps)&&d.steps.length)h+=`<h3>${APP.lang==="en"?"Next steps":"Próximos pasos"}</h3><ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||JSON.stringify(x)))}</li>`).join("")}</ol>`;
 if(d.google_flights_url)h+=`<div class="next-action"><strong>${APP.lang==="en"?"Continue with flight availability":"Continúa con la disponibilidad del vuelo"}</strong><p>${APP.lang==="en"?"Open Google Flights to review current route options.":"Abre Google Flights para revisar las opciones actuales de la ruta."}</p><p><a href="${esc(d.google_flights_url)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open Google Flights":"Abrir Google Flights"}</a></p></div>`;
 const chars=d.charter_sources||[],airs=d.airline_sources||[],sources=d.sources||[];
 if(chars.length)h+=`<h3>${APP.lang==="en"?"Charter flight/travel providers":"Proveedores de vuelos chárter/servicios de viaje"}</h3>${sourceList(chars)}`;
 if(airs.length)h+=`<h3>${APP.lang==="en"?"Airline sources":"Fuentes de la aerolínea"}</h3>${sourceList(airs)}`;
 if(!chars.length&&!airs.length&&sources.length)h+=sourceList(sources);
 if(d.next_action)h+=`<p><strong>${esc(d.next_action)}</strong></p>`;
 h+=`<div class="next-action"><strong>${APP.lang==="en"?"You can practice before doing it for real.":"Puedes practicar antes de hacerlo de verdad."}</strong><p>${APP.lang==="en"?"Use “Practice with my airline” above. The simulation does not buy a ticket or send real information.":"Usa “Practicar con mi aerolínea” arriba. La simulación no compra boletos ni envía información real."}</p></div>`;
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
 b.innerHTML=Array.isArray(items)&&items.length?sourceList(items):`<div class="next-action"><strong>${APP.lang==="en"?"Official sources":"Fuentes oficiales"}</strong><p>${APP.lang==="en"?"Use the official source for your airline and route to verify current information.":"Usa la fuente oficial de tu aerolínea y ruta para verificar la información vigente."}</p></div>`
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
 try{renderGuide(await api("/api/v1/guide",{method:"POST",body:JSON.stringify({language:lang(),flight:dataObject()})}))}
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
function practiceBox(){
 let x=$("#qqlPractice");
 if(x)return x;
 x=document.createElement("div");x.id="qqlPractice";x.className="card";
 document.body.appendChild(x);
 return x
}
function closePractice(){const x=$("#qqlPractice");if(x)x.remove();APP.practice=null}
function startAirlinePractice(){
 if(!requirePaid())return;
 const airline=val("airline")||"Mi aerolínea";
 APP.practice={type:"airline",airline,step:0,data:{}};
 renderPractice()
}
function startCubaPractice(type){
 if(!requirePaid())return;
 APP.practice={type:"cuba",mode:type,step:0,data:{}};
 renderPractice()
}
function practiceData(){
 const p=APP.practice||{};
 if(p.type==="airline")return[
  APP.lang==="en"?`Welcome. We will practice ${p.airline} without buying anything.`:`Bienvenido. Practicaremos ${p.airline} sin comprar nada.`,
  APP.lang==="en"?"Step 1: open the airline's official website or app. Look for the flight search option.":"Paso 1: abre el sitio o aplicación oficial de la aerolínea. Busca la opción para buscar vuelos.",
  APP.lang==="en"?"Step 2: enter origin, destination and travel date.":"Paso 2: escribe origen, destino y fecha del viaje.",
  APP.lang==="en"?"Step 3: review the flight options. Check date, time, airports and stops before selecting one.":"Paso 3: revisa las opciones. Comprueba fecha, hora, aeropuertos y escalas antes de seleccionar.",
  APP.lang==="en"?"Step 4: select the flight. In this practice, nothing is purchased.":"Paso 4: selecciona el vuelo. En esta práctica no se compra nada.",
  APP.lang==="en"?"Step 5: review passenger information. Use only fictitious information during practice.":"Paso 5: revisa la información del pasajero. En la práctica usa solamente información ficticia.",
  APP.lang==="en"?"Step 6: review baggage and fare conditions shown by the airline.":"Paso 6: revisa el equipaje y las condiciones de la tarifa que muestra la aerolínea.",
  APP.lang==="en"?"Step 7: stop before payment. For a real purchase, use only the airline's official site/app and verify the final information there.":"Paso 7: detente antes del pago. Para una compra real, usa solamente el sitio/aplicación oficial y verifica allí la información final."
 ][p.step]||"";
 if(p.mode==="dviajeros")return[
  APP.lang==="en"?"Practice: D’Viajeros. This is only a simulation; do not enter sensitive information.":"Práctica: D’Viajeros. Esto es solamente una simulación; no introduzcas información sensible.",
  APP.lang==="en"?"Step 1: open the official D’Viajeros portal.":"Paso 1: abre el portal oficial de D’Viajeros.",
  APP.lang==="en"?"Step 2: identify the traveler information the official form requests.":"Paso 2: identifica la información del viajero que solicita el formulario oficial.",
  APP.lang==="en"?"Step 3: complete the official form directly on the official portal when required.":"Paso 3: completa el formulario oficial directamente en el portal oficial cuando corresponda.",
  APP.lang==="en"?"Step 4: review your entries before submitting.":"Paso 4: revisa los datos antes de enviar.",
  APP.lang==="en"?"Step 5: keep the official confirmation available for your trip.":"Paso 5: conserva disponible la confirmación oficial para tu viaje."
 ][p.step]||"";
 return[
  APP.lang==="en"?"Practice: Cuba visa/eVisa. This is only a simulation.":"Práctica: visa/eVisa de Cuba. Esto es solamente una simulación.",
  APP.lang==="en"?"Step 1: open the official Cuba visa/eVisa source that applies to your situation.":"Paso 1: abre la fuente oficial de visa/eVisa de Cuba que corresponda a tu situación.",
  APP.lang==="en"?"Step 2: check the requirement for your nationality and trip.":"Paso 2: comprueba el requisito según tu nacionalidad y viaje.",
  APP.lang==="en"?"Step 3: review the documents and information requested by the official process.":"Paso 3: revisa los documentos y la información que solicita el proceso oficial.",
  APP.lang==="en"?"Step 4: complete the real process only on the official source.":"Paso 4: realiza el proceso real solamente en la fuente oficial.",
  APP.lang==="en"?"Step 5: keep the official confirmation or document available.":"Paso 5: conserva disponible la confirmación o documento oficial."
 ][p.step]||""
}
function practiceTitle(){
 const p=APP.practice||{};
 if(p.type==="airline")return APP.lang==="en"?`Practice: ${p.airline}`:`Práctica: ${p.airline}`;
 return p.mode==="dviajeros"?(APP.lang==="en"?"Practice: D’Viajeros":"Práctica: D’Viajeros"):(APP.lang==="en"?"Practice: Cuba visa/eVisa":"Práctica: visa/eVisa de Cuba")
}
function renderPractice(){
 const p=APP.practice;if(!p)return;
 const steps=p.type==="airline"?8:(p.mode==="dviajeros"?6:6),text=practiceData(),b=practiceBox();
 b.innerHTML=`<div><button id="practiceClose" type="button">× ${APP.lang==="en"?"Close":"Cerrar"}</button><h2>${esc(practiceTitle())}</h2><div class="next-action"><strong>${APP.lang==="en"?`Practice step ${p.step+1} of ${steps}`:`Paso ${p.step+1} de ${steps}`}</strong><p>${esc(text)}</p></div><div class="practice-actions">${p.step>0?`<button id="practiceBack" class="primary" type="button">${APP.lang==="en"?"Back":"Atrás"}</button>`:""}${p.step<steps-1?`<button id="practiceNext" class="primary" type="button">${APP.lang==="en"?"Next step":"Siguiente paso"}</button>`:`<button id="practiceFinish" class="primary" type="button">${APP.lang==="en"?"Finish practice":"Terminar práctica"}</button>`}</div></div>`;
 $("#practiceClose").onclick=closePractice;
 $("#practiceBack")?.addEventListener("click",()=>{if(APP.practice.step>0){APP.practice.step--;renderPractice()}});
 $("#practiceNext")?.addEventListener("click",()=>{APP.practice.step++;renderPractice()});
 $("#practiceFinish")?.addEventListener("click",finishPractice);
 b.scrollIntoView({behavior:"auto",block:"start"})
}
function finishPractice(){
 const p=APP.practice;
 const b=$("#qqlPractice");if(!b)return;
 let source="";
 if(p.type==="airline")source=APP.lang==="en"?"For the real process, use the airline's official website/app and verify the final fare, baggage, passenger requirements and payment information there.":"Para el proceso real, usa el sitio/aplicación oficial de la aerolínea y verifica allí la tarifa final, equipaje, requisitos del pasajero y pago.";
 else if(p.mode==="dviajeros")source=APP.lang==="en"?"Official D’Viajeros: https://dviajeros.mitrans.gob.cu/":"D’Viajeros oficial: https://dviajeros.mitrans.gob.cu/";
 else source=APP.lang==="en"?"Official Cuba eVisa source: https://evisacuba.cu/":"Fuente oficial de eVisa Cuba: https://evisacuba.cu/";
 b.innerHTML=`<div><button id="practiceClose" type="button">× ${APP.lang==="en"?"Close":"Cerrar"}</button><h2>${APP.lang==="en"?"Practice completed":"Práctica completada"}</h2><div class="next-action"><strong>${APP.lang==="en"?"You are ready for the real process.":"Ya puedes pasar al proceso real."}</strong><p>${esc(source)}</p><p>${APP.lang==="en"?"The simulation did not send, save or purchase anything.":"La simulación no envió, guardó ni compró nada."}</p></div></div>`;
 $("#practiceClose").onclick=closePractice
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
  else if(a==="baggage"){if(requirePaid())setView("baggage")}
  else if(a==="cuba"){if(requirePaid()){setView("cuba");cubaGuide()}}
  else if(a==="guide"){if(requirePaid()){setView("guide");guide()}}
  else if(a==="sources"){if(requirePaid()){setView("sources");officialSources()}}
  else if(a==="teach"){if(requirePaid())setView("teach")}
  else if(a==="legal"){setView("legal");legal()}
  else if(a==="pay"||a==="payment")createCheckout();
  else if(a==="logout")logout()
 })
}
async function init(){
 document.documentElement.lang=APP.lang;
 bind();
 translate();
 ensureAirlineField();
 ensureFlightPracticeButton();
 ensureCubaPracticeButtons();
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
window.startAirlinePractice=startAirlinePractice;
window.startCubaPractice=startCubaPractice;
window.closePractice=closePractice;
document.addEventListener("DOMContentLoaded",init);
