"use strict";
const APP={name:"QUE QUIERES LLEVAR",version:"8.3.0",lang:localStorage.getItem("qql_lang")||"es",serviceToken:localStorage.getItem("qql_service_token")||"",adminToken:localStorage.getItem("qql_admin_token")||"",session:null,config:null,_bound:false,practice:null,cubaPractice:null,adminTaps:0,adminTapTimer:null};
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
function screens(){return["loading","home","payment","flight","practice","item","baggage","cuba","cubaPractice","guide","sources","teach","legal","admin"].map(id=>document.getElementById(id)).filter(Boolean)}
function setView(name){screens().forEach(x=>x.classList.toggle("hidden",x.id!==name));document.body.dataset.view=name;window.scrollTo({top:0,behavior:"instant"})}
function home(){setView(active()?"home":"payment")}
function requirePaid(){if(active())return true;setView("payment");msg(APP.lang==="en"?"Payment or administrator access is required.":"Se requiere acceso mediante pago o administrador.","warn");return false}
function lang(){return APP.lang==="en"?"en":"es"}
function setLang(v){APP.lang=v==="en"?"en":"es";localStorage.setItem("qql_lang",APP.lang);translate();ensureAirlineField();ensureFlightPracticeButton()}
function toggleLang(){setLang(APP.lang==="es"?"en":"es")}
function translate(){
 document.documentElement.lang=APP.lang;
 $$("[data-es][data-en]").forEach(e=>{e.textContent=e.dataset[APP.lang]||e.dataset.es||""});
 const b=$("#langBtn");if(b)b.textContent=APP.lang==="en"?"ES":"EN";
 const l=$("#loadingText");if(l)l.textContent=APP.lang==="en"?"Preparing your trip...":"Preparando tu viaje...";
 const s=$("#sessionStatus");if(s)s.textContent=active()?(APP.lang==="en"?"Access active":"Acceso activo"):(APP.lang==="en"?"Session not active":"Sesión no activa");
 const p=$("#payment .card");
 if(p){
  const h=p.querySelector("h2"),ps=p.querySelectorAll("p"),n=p.querySelector(".notice"),bt=$("#payBtn");
  if(h)h.textContent=APP.lang==="en"?"Activate your travel preparation":"Activa tu preparación";
  if(ps[0])ps[0].textContent=APP.lang==="en"?"Before paying, know what you receive: a simple 15-minute guided session to organize your trip, understand your flight, practice airline procedures, review baggage, practice D’Viajeros and Cuba visa/eVisa procedures, and reach official sources.":"Antes de pagar, conoce lo que recibes: una sesión guiada de 15 minutos para organizar tu viaje, entender tu vuelo, practicar procesos de la aerolínea, revisar equipaje, practicar D’Viajeros y visa/eVisa de Cuba, y llegar a las fuentes oficiales.";
  if(n)n.innerHTML=APP.lang==="en"?"<strong>What you gain:</strong> you practice before doing the real process and finish with clear next actions.":"<strong>Qué ganas:</strong> practicas antes de hacerlo de verdad y terminas con próximos pasos claros.";
  if(bt)bt.textContent=APP.lang==="en"?"Continue to payment — $15.99":"Continuar al pago — $15.99"
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
  msg(APP.lang==="en"?"Your access could not be confirmed. Please try again.":"No se pudo confirmar tu acceso. Intenta nuevamente.","error");
  return false
 }
}
async function loadConfig(){try{APP.config=await api("/api/v1/config",{method:"GET"},7000);renderConfig(APP.config)}catch(_){}}
function renderConfig(d){if(!d)return;$$("[data-config]").forEach(e=>{const k=e.dataset.config;if(d[k]!=null)e.textContent=d[k]})}
async function createCheckout(){
 try{
  const d=await api("/api/v1/create-checkout-session",{method:"POST",body:JSON.stringify({language:lang()})},15000),u=d.checkout_url||d.url;
  if(u)location.href=u;else msg(APP.lang==="en"?"The payment link was not received.":"No se recibió el enlace de pago.","error")
 }catch(e){msg(e.message||"No se pudo iniciar el pago.","error")}
}
async function verifyPayment(){
 const q=new URLSearchParams(location.search),sid=q.get("session_id")||q.get("checkout_session_id");
 if(!sid)return false;
 try{
  const d=await api("/api/v1/verify-payment",{method:"POST",body:JSON.stringify({session_id:sid})},15000),t=d.token||d.service_token;
  if(!t)throw new Error(APP.lang==="en"?"Access could not be activated.":"No se pudo activar el acceso.");
  APP.serviceToken=t;APP.adminToken="";saveTokens();history.replaceState({},document.title,location.pathname);APP.session={active:true};setView("home");translate();msg(APP.lang==="en"?"Your 15-minute preparation session is active.":"Tu sesión de preparación de 15 minutos está activa.","success");return true
 }catch(e){msg(e.message||"No se pudo verificar el pago.","error");return false}
}
async function adminLogin(){
 const user=val("adminUser"),pass=val("adminPass");
 if(!user||!pass){msg(APP.lang==="en"?"Enter username and password.":"Escribe usuario y contraseña.","warn");return}
 try{
  const d=await api("/api/v1/admin/login",{method:"POST",body:JSON.stringify({username:user,password:pass})},15000),t=d.token||d.admin_token;
  if(!t)throw new Error(APP.lang==="en"?"Administrator access could not be activated.":"No se pudo activar el acceso de administrador.");
  APP.adminToken=t;APP.serviceToken="";APP.session={active:true,admin:true};saveTokens();setView("home");translate();msg(APP.lang==="en"?"Administrator access is active.":"El acceso de administrador está activo.","success")
 }catch(e){msg(e.message||"No se pudo iniciar sesión.","error")}
}
function logout(){clearTokens();home();translate();msg(APP.lang==="en"?"Session closed.":"Sesión cerrada.","info")}
function ensureAirlineField(){
 const i=$("#airline");if(i){i.placeholder=APP.lang==="en"?"Example: American Airlines":"Ej.: American Airlines";return}
 const form=$("#flight")?.querySelector(".form");if(!form)return;
 const label=document.createElement("label"),input=document.createElement("input");
 label.textContent=APP.lang==="en"?"Airline":"Aerolínea";input.id="airline";input.maxLength=80;input.placeholder=APP.lang==="en"?"Example: American Airlines":"Ej.: American Airlines";label.appendChild(input);
 const passengers=$("#passengers")?.closest("label");if(passengers)form.insertBefore(label,passengers)
}
function ensureFlightPracticeButton(){
 const b=$("#practiceAirlineBtn");if(!b)return;
 b.textContent=APP.lang==="en"?"🎓 Practice with my airline":"🎓 Practicar con mi aerolínea"
}
function dataObject(){
 const o={language:lang()};
 ["origin","destination","departureDate","returnDate","airline","cabin","fare","passengers","stops"].forEach(id=>{
  const v=val(id);if(v!==""){const k=id==="departureDate"?"departure_date":id==="returnDate"?"return_date":id;o[k]=k==="passengers"||k==="stops"?Number(v):v}
 });
 return o
}
async function flight(){
 if(!requirePaid())return;
 const data=dataObject();
 if(!data.origin||!data.destination){msg(APP.lang==="en"?"Enter your origin and destination to continue.":"Escribe origen y destino para continuar.","warn");return}
 try{renderFlight(await api("/api/v1/flight/understand",{method:"POST",body:JSON.stringify(data)},15000))}
 catch(e){msg(e.message||"No se pudo preparar la información del vuelo.","error")}
}
function sourceList(items){
 if(!Array.isArray(items)||!items.length)return"";
 return`<div class="source-list">${items.map(x=>{const n=esc(x.name||"Official source"),u=esc(x.url||""),d=x.description?`<p>${esc(x.description)}</p>`:"";return`<div class="source-card"><strong>${n}</strong>${d}${u?`<a href="${u}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open source":"Abrir fuente"}</a>`:""}</div>`}).join("")}</div>`
}
function renderFlight(d){
 const b=$("#flightResult");if(!b)return;
 let h="",a=d.airline||val("airline"),o=d.origin||val("origin"),des=d.destination||val("destination"),date=d.departure_date||val("departureDate");
 if(o||des||date||a)h+=`<div class="next-action"><strong>${APP.lang==="en"?"Flight information":"Información del vuelo"}</strong>${o?`<p>${APP.lang==="en"?"Origin":"Origen"}: ${esc(o)}</p>`:""}${des?`<p>${APP.lang==="en"?"Destination":"Destino"}: ${esc(des)}</p>`:""}${date?`<p>${APP.lang==="en"?"Date":"Fecha"}: ${esc(date)}</p>`:""}${a?`<p>${APP.lang==="en"?"Airline":"Aerolínea"}: ${esc(a)}</p>`:""}</div>`;
 if(d.understood){
  const u=typeof d.understood==="string"?d.understood:(d.understood.text||d.understood.message||d.understood.description||"");
  if(u)h+=`<p>${esc(u)}</p>`
 }
 if(Array.isArray(d.steps)&&d.steps.length)h+=`<h3>${APP.lang==="en"?"Next steps":"Próximos pasos"}</h3><ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||""))}</li>`).join("")}</ol>`;
 if(d.live_results_available===false)h+=`<div class="next-action"><strong>${APP.lang==="en"?"Current flight availability is not provided here":"Aquí no se muestra disponibilidad actual de vuelos"}</strong><p>${APP.lang==="en"?"Use the airline's official site or another current flight-search source to check schedules and availability.":"Usa el sitio oficial de la aerolínea u otra fuente actual de búsqueda para consultar horarios y disponibilidad."}</p></div>`;
 if(d.google_flights_url)h+=`<div class="next-action"><strong>${APP.lang==="en"?"Review current flight options":"Revisa las opciones actuales de vuelo"}</strong><p><a href="${esc(d.google_flights_url)}" target="_blank" rel="noopener noreferrer">Google Flights</a></p></div>`;
 if(Array.isArray(d.airline_sources)&&d.airline_sources.length)h+=sourceList(d.airline_sources);
 if(Array.isArray(d.charter_sources)&&d.charter_sources.length)h+=sourceList(d.charter_sources);
 b.innerHTML=h||`<p>${APP.lang==="en"?"No flight information was generated.":"No se generó información del vuelo."}</p>`
}
function renderSources(items){
 const b=$("#sourcesResult")||$("#flightResult");if(!b)return;
 b.innerHTML=Array.isArray(items)&&items.length?sourceList(items):`<div class="next-action"><strong>${APP.lang==="en"?"Official sources":"Fuentes oficiales"}</strong><p>${APP.lang==="en"?"No source was returned.":"No se recibió ninguna fuente."}</p></div>`
}
async function charterSources(){
 if(!requirePaid())return;
 try{
  const d=await api("/api/v1/flight/sources",{method:"POST",body:JSON.stringify({origin:val("origin"),destination:val("destination"),airline:val("airline"),language:lang()})},12000);
  renderSources(d.charter_sources||d.sources||[])
 }catch(e){msg(e.message||"No se pudieron cargar las fuentes.","error")}
}
async function officialSources(){
 if(!requirePaid())return;
 try{const d=await api(`/api/v1/sources/official?language=${encodeURIComponent(lang())}`,{method:"GET"},10000);renderSources(d.sources||d.official_sources||d.links||[])}
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
 if(Array.isArray(d.steps)&&d.steps.length)h+=`<ol>${d.steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||""))}</li>`).join("")}</ol>`;
 if(Array.isArray(d.cuba_steps)&&d.cuba_steps.length)h+=`<h3>${APP.lang==="en"?"Cuba preparation":"Preparación para Cuba"}</h3><ol>${d.cuba_steps.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.title||x.description||""))}</li>`).join("")}</ol>`;
 if(Array.isArray(d.official_sources)&&d.official_sources.length)h+=sourceList(d.official_sources);
 b.innerHTML=h||`<div class="next-action"><strong>${APP.lang==="en"?"No guide information was returned.":"No se recibió información para la guía."}</strong></div>`
}
function renderObject(b,d){
 if(!b)return;
 if(typeof d==="string"){b.innerHTML=`<p>${esc(d)}</p>`;return}
 let h="";
 ["title","intro","short_notice","message","reason","explanation"].forEach(k=>{if(d[k])h+=k==="title"?`<h2>${esc(d[k])}</h2>`:`<p>${esc(d[k])}</p>`});
 if(d.status)h+=`<p><strong>${esc(d.status)}</strong></p>`;
 if(d.baggage_place)h+=`<p><strong>${APP.lang==="en"?"Baggage":"Equipaje"}:</strong> ${esc(d.baggage_place)}</p>`;
 if(d.carry_on)h+=`<p><strong>${APP.lang==="en"?"Carry-on":"Equipaje de mano"}:</strong> ${esc(d.carry_on)}</p>`;
 if(d.checked_baggage)h+=`<p><strong>${APP.lang==="en"?"Checked baggage":"Equipaje facturado"}:</strong> ${esc(d.checked_baggage)}</p>`;
 if(Array.isArray(d.conditions)&&d.conditions.length)h+=`<h3>${APP.lang==="en"?"Conditions":"Condiciones"}</h3><ul>${d.conditions.map(x=>`<li>${esc(typeof x==="string"?x:(x.text||x.description||""))}</li>`).join("")}</ul>`;
 if(Array.isArray(d.missing_information)&&d.missing_information.length)h+=`<h3>${APP.lang==="en"?"Still needed":"Información que falta"}</h3><ul>${d.missing_information.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>`;
 if(d.source_name)h+=`<p>${esc(d.source_name)}</p>`;
 if(d.official_link)h+=`<p><a href="${esc(d.official_link)}" target="_blank" rel="noopener noreferrer">${APP.lang==="en"?"Open official source":"Abrir fuente oficial"}</a></p>`;
 const s=d.sources||d.official_sources||d.links||d.official_links||[];if(Array.isArray(s)&&s.length)h+=sourceList(s);
 if(d.next_action)h+=`<div class="next-action"><strong>${esc(d.next_action)}</strong></div>`;
 b.innerHTML=h||`<div class="next-action">${APP.lang==="en"?"No information was returned.":"No se recibió información."}</div>`
}
async function legal(){
 try{
  const d=await api(`/api/v1/legal?language=${encodeURIComponent(lang())}`,{method:"GET"},8000),b=$("#legalResult");if(!b)return;
  let h="";["short_notice","full_notice","user_guidance","source_notice"].forEach(k=>{if(d[k])h+=`<p>${esc(d[k])}</p>`});
  b.innerHTML=h||`<p>${APP.lang==="en"?"Review the service information.":"Revisa la información del servicio."}</p>`
 }catch(e){msg(e.message||"No se pudo cargar el aviso legal.","error")}
}
async function itemConsult(){
 if(!requirePaid())return;
 const item=val("itemName"),quantity=val("itemQty")||"1",description=val("itemDescription");
 if(!item){msg(APP.lang==="en"?"Enter the item to continue.":"Escribe el artículo para continuar.","warn");return}
 try{
  renderObject($("#itemResult"),await api("/api/v1/consultar-articulo",{method:"POST",body:JSON.stringify({item,quantity,description,language:lang(),baggage_type:val("baggage_type"),airline:val("itemAirline")||val("airline"),destination:val("itemDestination")||val("destination"),origin:val("origin"),cabin:val("cabin"),fare:val("fare"),wh:val("wh"),volts:val("volts"),ah:val("ah"),mah:val("mah")})},15000))
 }catch(e){msg(e.message||"No se pudo preparar la consulta del artículo.","error")}
}
async function teach(){
 if(!requirePaid())return;
 const term=val("term");if(!term){msg(APP.lang==="en"?"Enter a term to continue.":"Escribe un término para continuar.","warn");return}
 try{renderObject($("#teachResult"),await api("/api/v1/item/teach",{method:"POST",body:JSON.stringify({term,language:lang()})},10000))}
 catch(e){msg(e.message||"No se pudo preparar la explicación.","error")}
}
async function baggage(){
 if(!requirePaid())return;
 try{renderObject($("#baggageResult"),await api(`/api/v1/baggage?language=${encodeURIComponent(lang())}`,{method:"GET"},10000))}
 catch(e){msg(e.message||"No se pudo cargar la información de equipaje.","error")}
}
function practiceData(){
 return{
  airline:val("practiceAirline"),
  origin:val("practiceOrigin"),
  destination:val("practiceDestination"),
  date:val("practiceDate"),
  passengers:Number(val("practicePassengers")||1),
  flight:val("practiceFlight"),
  passengerName:val("practicePassengerName"),
  baggage:val("practiceBaggage"),
  seat:val("practiceSeat")
 }
}
function practiceStep(n){
 const p=APP.practice;
 p.step=n;
 renderAirlinePractice();
}
function practiceStart(){
 const d=practiceData();
 if(!d.airline){msg(APP.lang==="en"?"Select an airline.":"Selecciona una aerolínea.","warn");return}
 APP.practice={step:1,...d};
 renderAirlinePractice()
}
function renderAirlinePractice(){
 if(!APP.practice)return;
 const p=APP.practice,b=$("#practiceResult");if(!b)return;
 const s=p.step||1;
 let h=`<div class="next-action"><strong>${APP.lang==="en"?`Simulation step ${s} of 7`:`Paso ${s} de 7 de la simulación`}</strong><p>${APP.lang==="en"?"This is a functional training simulation. No purchase or real submission is performed.":"Esta es una simulación funcional de entrenamiento. No realiza compras ni envíos reales."}</p></div>`;
 if(s===1){
  h+=`<div class="form"><label>${APP.lang==="en"?"Origin":"Origen"}<input id="practiceOrigin" maxlength="80" value="${esc(p.origin)}" placeholder="MIA"></label><label>${APP.lang==="en"?"Destination":"Destino"}<input id="practiceDestination" maxlength="80" value="${esc(p.destination)}" placeholder="HAV"></label><label>${APP.lang==="en"?"Travel date":"Fecha de viaje"}<input id="practiceDate" type="date" value="${esc(p.date)}"></label><label>${APP.lang==="en"?"Passengers":"Pasajeros"}<input id="practicePassengers" type="number" min="1" max="9" value="${p.passengers||1}"></label><button id="practiceStep1" class="primary" type="button">${APP.lang==="en"?"Search flights":"Buscar vuelos"}</button></div>`
 }else if(s===2){
  h+=`<h3>${APP.lang==="en"?"Available practice flights":"Vuelos disponibles para practicar"}</h3><div class="practice-choice"><button data-pflight="PR101" type="button"><strong>PR101</strong><span>${esc(p.origin||"MIA")} → ${esc(p.destination||"HAV")}</span><small>08:00 → 11:30 · Economy</small></button><button data-pflight="PR205" type="button"><strong>PR205</strong><span>${esc(p.origin||"MIA")} → ${esc(p.destination||"HAV")}</span><small>13:20 → 16:50 · Economy</small></button><button data-pflight="PR310" type="button"><strong>PR310</strong><span>${esc(p.origin||"MIA")} → ${esc(p.destination||"HAV")}</span><small>19:00 → 22:30 · Economy</small></button></div><button id="practiceBack1" class="secondary" type="button">${APP.lang==="en"?"Back":"Atrás"}</button>`
 }else if(s===3){
  h+=`<div class="form"><label>${APP.lang==="en"?"Passenger name — fictional":"Nombre del pasajero — ficticio"}<input id="practicePassengerName" maxlength="80" value="${esc(p.passengerName)}" placeholder="${APP.lang==="en"?"Example: Alex Garcia":"Ejemplo: Alex Garcia"}"></label><label>${APP.lang==="en"?"Passenger type":"Tipo de pasajero"}<select><option>Adulto / Adult</option><option>Child / Niño</option></select></label><button id="practiceStep3" class="primary" type="button">${APP.lang==="en"?"Continue to baggage":"Continuar al equipaje"}</button></div>`
 }else if(s===4){
  h+=`<div class="form"><label>${APP.lang==="en"?"Baggage":"Equipaje"}<select id="practiceBaggage"><option value="">${APP.lang==="en"?"Select":"Selecciona"}</option><option value="personal">${APP.lang==="en"?"Personal item":"Artículo personal"}</option><option value="carry-on">${APP.lang==="en"?"Carry-on":"Equipaje de mano"}</option><option value="checked">${APP.lang==="en"?"Checked bag":"Equipaje facturado"}</option></select></label><button id="practiceStep4" class="primary" type="button">${APP.lang==="en"?"Continue to seat":"Continuar al asiento"}</button></div>`
 }else if(s===5){
  h+=`<h3>${APP.lang==="en"?"Choose a practice seat":"Elige un asiento para practicar"}</h3><div class="seat-grid">${["1A","1B","1C","1D","2A","2B","2C","2D","3A","3B","3C","3D"].map(x=>`<button type="button" data-seat="${x}" class="${p.seat===x?"selected":""}">${x}</button>`).join("")}</div><button id="practiceStep5" class="primary" type="button">${APP.lang==="en"?"Continue to check-in review":"Continuar a revisión de check-in"}</button>`
 }else if(s===6){
  h+=`<div class="review"><h3>${APP.lang==="en"?"Check-in review":"Revisión del check-in"}</h3><p><strong>${APP.lang==="en"?"Airline":"Aerolínea"}:</strong> ${esc(p.airline)}</p><p><strong>${APP.lang==="en"?"Flight":"Vuelo"}:</strong> ${esc(p.flight)}</p><p><strong>${APP.lang==="en"?"Passenger":"Pasajero"}:</strong> ${esc(p.passengerName||"—")}</p><p><strong>${APP.lang==="en"?"Baggage":"Equipaje"}:</strong> ${esc(p.baggage||"—")}</p><p><strong>${APP.lang==="en"?"Seat":"Asiento"}:</strong> ${esc(p.seat||"—")}</p></div><button id="practiceStep6" class="primary" type="button">${APP.lang==="en"?"Continue to final review":"Continuar a revisión final"}</button>`
 }else{
  h+=`<div class="review"><h3>${APP.lang==="en"?"Final review":"Revisión final"}</h3><p>${APP.lang==="en"?"This reproduces the preparation flow up to the point where a real airline would request payment or final confirmation.":"Esta simulación reproduce el flujo de preparación hasta el punto en que una aerolínea real solicitaría el pago o la confirmación final."}</p><p><strong>${APP.lang==="en"?"Airline":"Aerolínea"}:</strong> ${esc(p.airline)}</p><p><strong>${APP.lang==="en"?"Route":"Ruta"}:</strong> ${esc(p.origin)} → ${esc(p.destination)}</p><p><strong>${APP.lang==="en"?"Flight":"Vuelo"}:</strong> ${esc(p.flight)}</p><p><strong>${APP.lang==="en"?"Passenger":"Pasajero"}:</strong> ${esc(p.passengerName)}</p><p><strong>${APP.lang==="en"?"Baggage":"Equipaje"}:</strong> ${esc(p.baggage)}</p><p><strong>${APP.lang==="en"?"Seat":"Asiento"}:</strong> ${esc(p.seat)}</p></div><div class="notice">${APP.lang==="en"?"Simulation completed. Nothing was purchased and no real airline information was submitted.":"Simulación completada. No se compró nada y no se envió información real a ninguna aerolínea."}</div><button id="practiceRestart" class="secondary" type="button">${APP.lang==="en"?"Practice again":"Practicar nuevamente"}</button>`
 }
 b.innerHTML=h;
 $("#practiceStep1")?.addEventListener("click",()=>{
  const d=practiceData();
  if(!d.origin||!d.destination||!d.date){msg(APP.lang==="en"?"Enter origin, destination and date.":"Escribe origen, destino y fecha.","warn");return}
  APP.practice={...p,...d,step:2};renderAirlinePractice()
 });
 $$("[data-pflight]").forEach(x=>x.addEventListener("click",()=>{APP.practice.flight=x.dataset.pflight;APP.practice.step=3;renderAirlinePractice()}));
 $("#practiceBack1")?.addEventListener("click",()=>practiceStep(1));
 $("#practiceStep3")?.addEventListener("click",()=>{
  const d=practiceData();if(!d.passengerName){msg(APP.lang==="en"?"Enter a fictional passenger name.":"Escribe un nombre ficticio de pasajero.","warn");return}
  APP.practice={...p,...d,step:4};renderAirlinePractice()
 });
 $("#practiceStep4")?.addEventListener("click",()=>{
  const d=practiceData();if(!d.baggage){msg(APP.lang==="en"?"Select baggage.":"Selecciona el equipaje.","warn");return}
  APP.practice={...p,...d,step:5};renderAirlinePractice()
 });
 $$("[data-seat]").forEach(x=>x.addEventListener("click",()=>{APP.practice.seat=x.dataset.seat;renderAirlinePractice()}));
 $("#practiceStep5")?.addEventListener("click",()=>{
  if(!APP.practice.seat){msg(APP.lang==="en"?"Choose a seat.":"Elige un asiento.","warn");return}
  APP.practice.step=6;renderAirlinePractice()
 });
 $("#practiceStep6")?.addEventListener("click",()=>{APP.practice.step=7;renderAirlinePractice()});
 $("#practiceRestart")?.addEventListener("click",()=>{APP.practice=null;renderPracticeStart()})
}
function renderPracticeStart(){
 const b=$("#practiceResult");if(!b)return;
 b.innerHTML=`<div class="form"><label>${APP.lang==="en"?"Which airline do you want to practice with?":"¿Con qué aerolínea quieres practicar?"}<select id="practiceAirline"><option value="">${APP.lang==="en"?"Select an airline":"Selecciona una aerolínea"}</option><option>American Airlines</option><option>Delta Air Lines</option><option>United Airlines</option><option>Southwest Airlines</option><option>JetBlue</option><option>Spirit Airlines</option><option>Frontier Airlines</option><option>${APP.lang==="en"?"Another airline":"Otra aerolínea"}</option></select></label><button id="practiceStartBtn" class="primary" type="button">${APP.lang==="en"?"Start simulation":"Comenzar simulación"}</button></div>`;
 $("#practiceStartBtn").onclick=practiceStart
}
function startAirlinePractice(){
 if(!requirePaid())return;
 setView("practice");
 renderPracticeStart()
}
function startCubaPractice(mode){
 if(!requirePaid())return;
 APP.cubaPractice={mode,step:1};
 setView("cubaPractice");
 renderCubaPractice()
}
function renderCubaPractice(){
 const b=$("#cubaPracticeResult");if(!b)return;
 const p=APP.cubaPractice,s=p.step;
 let h=`<div class="next-action"><strong>${APP.lang==="en"?`Simulation step ${s} of 6`:`Paso ${s} de 6 de la simulación`}</strong><p>${APP.lang==="en"?"This simulation does not submit information to Cuba or any authority.":"Esta simulación no envía información a Cuba ni a ninguna autoridad."}</p></div>`;
 if(p.mode==="dviajeros"){
  if(s===1)h+=`<div class="form"><label>${APP.lang==="en"?"Full name — fictional":"Nombre completo — ficticio"}<input id="cubaName" placeholder="${APP.lang==="en"?"Example: Alex Garcia":"Ejemplo: Alex Garcia"}"></label><label>${APP.lang==="en"?"Passport number — fictional":"Número de pasaporte — ficticio"}<input id="cubaPassport" placeholder="ABC123456"></label><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button></div>`;
  else if(s===2)h+=`<div class="form"><label>${APP.lang==="en"?"Arrival date":"Fecha de llegada"}<input id="cubaDate" type="date"></label><label>${APP.lang==="en"?"Flight number — fictional":"Número de vuelo — ficticio"}<input id="cubaFlight" placeholder="XX123"></label><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button></div>`;
  else if(s===3)h+=`<div class="form"><label>${APP.lang==="en"?"Address in Cuba — practice":"Dirección en Cuba — práctica"}<input id="cubaAddress" placeholder="La Habana"></label><label>${APP.lang==="en"?"Purpose of travel":"Motivo del viaje"}<select id="cubaPurpose"><option>${APP.lang==="en"?"Tourism":"Turismo"}</option><option>${APP.lang==="en"?"Family visit":"Visita familiar"}</option><option>${APP.lang==="en"?"Other":"Otro"}</option></select></label><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button></div>`;
  else if(s===4)h+=`<div class="review"><h3>${APP.lang==="en"?"Review D’Viajeros fields":"Revisión de campos de D’Viajeros"}</h3><p>${APP.lang==="en"?"Name, passport, arrival, flight, address and travel purpose have been practiced.":"Has practicado nombre, pasaporte, llegada, vuelo, dirección y motivo del viaje."}</p></div><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button>`;
  else if(s===5)h+=`<div class="review"><h3>${APP.lang==="en"?"Final review":"Revisión final"}</h3><p>${APP.lang==="en"?"The real D’Viajeros process continues on the official portal.":"El proceso real de D’Viajeros continúa en el portal oficial."}</p></div><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button>`;
  else h+=`<div class="notice"><strong>${APP.lang==="en"?"Simulation completed":"Simulación completada"}</strong><p>${APP.lang==="en"?"No information was sent. Complete the real form only on the official D’Viajeros portal.":"No se envió información. Completa el formulario real solamente en el portal oficial de D’Viajeros."}</p><p><a href="https://dviajeros.mitrans.gob.cu/" target="_blank" rel="noopener noreferrer">D’Viajeros oficial</a></p></div>`;
 }else{
  if(s===1)h+=`<div class="form"><label>${APP.lang==="en"?"Nationality — practice":"Nacionalidad — práctica"}<input id="visaNationality" placeholder="${APP.lang==="en"?"Example: United States":"Ejemplo: Estados Unidos"}"></label><label>${APP.lang==="en"?"Passport type":"Tipo de pasaporte"}<select id="visaPassportType"><option>${APP.lang==="en"?"Regular passport":"Pasaporte regular"}</option><option>${APP.lang==="en"?"Cuban passport":"Pasaporte cubano"}</option><option>${APP.lang==="en"?"Dual nationality":"Doble nacionalidad"}</option></select></label><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button></div>`;
  else if(s===2)h+=`<div class="form"><label>${APP.lang==="en"?"Travel purpose":"Motivo del viaje"}<select id="visaPurpose"><option>${APP.lang==="en"?"Tourism":"Turismo"}</option><option>${APP.lang==="en"?"Family visit":"Visita familiar"}</option><option>${APP.lang==="en"?"Other":"Otro"}</option></select></label><label>${APP.lang==="en"?"Passport expiration date":"Vencimiento del pasaporte"}<input id="visaExpiry" type="date"></label><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button></div>`;
  else if(s===3)h+=`<div class="form"><label>${APP.lang==="en"?"Entry document to practice":"Documento de entrada a practicar"}<select id="visaDocument"><option>Visa / eVisa</option><option>${APP.lang==="en"?"Other authorization":"Otra autorización"}</option><option>${APP.lang==="en"?"Check official requirement":"Comprobar requisito oficial"}</option></select></label><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button></div>`;
  else if(s===4)h+=`<div class="review"><h3>${APP.lang==="en"?"Requirement review":"Revisión del requisito"}</h3><p>${APP.lang==="en"?"The simulation teaches where nationality, passport and travel purpose affect the real process.":"La simulación enseña dónde influyen la nacionalidad, el pasaporte y el motivo del viaje en el proceso real."}</p></div><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button>`;
  else if(s===5)h+=`<div class="review"><h3>${APP.lang==="en"?"Final review":"Revisión final"}</h3><p>${APP.lang==="en"?"The real requirement must be confirmed through the applicable official Cuba source.":"El requisito real debe confirmarse mediante la fuente oficial de Cuba que corresponda."}</p></div><button id="cubaNext" class="primary" type="button">${APP.lang==="en"?"Continue":"Continuar"}</button>`;
  else h+=`<div class="notice"><strong>${APP.lang==="en"?"Simulation completed":"Simulación completada"}</strong><p>${APP.lang==="en"?"No application or payment was submitted.":"No se presentó ninguna solicitud ni se realizó ningún pago."}</p><p><a href="https://evisacuba.cu/" target="_blank" rel="noopener noreferrer">eVisa Cuba oficial</a></p></div>`
 }
 b.innerHTML=h;
 $("#cubaNext")?.addEventListener("click",()=>{APP.cubaPractice.step++;renderCubaPractice()})
}
function finishCuba(){APP.cubaPractice=null;setView("cuba")}
function createHiddenAdminAccess(){
 const btn=$("#adminBtn");if(btn)btn.style.display="none";
 const homeScreen=$("#home");if(!homeScreen)return;
 homeScreen.addEventListener("click",adminTapHandler,true)
}
function adminTapHandler(e){
 if(e.target.closest("button,input,textarea,select,a"))return;
 APP.adminTaps++;clearTimeout(APP.adminTapTimer);
 APP.adminTapTimer=setTimeout(()=>APP.adminTaps=0,900);
 if(APP.adminTaps>=3){APP.adminTaps=0;clearTimeout(APP.adminTapTimer);openHiddenAdmin()}
}
function openHiddenAdmin(){
 const existing=$("#qqlHiddenAdmin");if(existing){existing.remove();return}
 const box=document.createElement("div");box.id="qqlHiddenAdmin";
 box.innerHTML=`<div class="qql-admin-overlay"><div class="qql-admin-card"><button id="qqlAdminClose" type="button">×</button><h2>MAY ROGA LLC</h2><p>${APP.lang==="en"?"Administrator access":"Acceso de administrador"}</p><label>${APP.lang==="en"?"Username":"Usuario"}<input id="qqlHiddenUser" type="text" autocomplete="username"></label><label>${APP.lang==="en"?"Password":"Contraseña"}<input id="qqlHiddenPass" type="password" autocomplete="current-password"></label><button id="qqlHiddenLogin" class="primary" type="button">${APP.lang==="en"?"Sign in":"Entrar"}</button><p id="qqlHiddenMsg" class="message"></p></div></div>`;
 document.body.appendChild(box);$("#qqlAdminClose").onclick=()=>box.remove();$("#qqlHiddenLogin").onclick=hiddenAdminLogin;$("#qqlHiddenUser").focus();$("#qqlHiddenPass").addEventListener("keydown",e=>{if(e.key==="Enter")hiddenAdminLogin()})
}
async function hiddenAdminLogin(){
 const u=txt($("#qqlHiddenUser")?.value),p=txt($("#qqlHiddenPass")?.value),m=$("#qqlHiddenMsg");
 if(!u||!p){if(m)m.textContent=APP.lang==="en"?"Enter username and password.":"Escribe usuario y contraseña.";return}
 try{
  const d=await api("/api/v1/admin/login",{method:"POST",body:JSON.stringify({username:u,password:p})},15000),t=d.token||d.admin_token;
  if(!t)throw new Error(APP.lang==="en"?"Administrator access could not be activated.":"No se pudo activar el acceso de administrador.");
  APP.adminToken=t;APP.serviceToken="";APP.session={active:true,admin:true};saveTokens();$("#qqlHiddenAdmin")?.remove();setView("home");translate();msg(APP.lang==="en"?"Administrator access is active.":"El acceso de administrador está activo.","success")
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
 $("#guideBtn")?.addEventListener("click",guide);
 $("#adminLoginBtn")?.addEventListener("click",adminLogin);
 $("#practiceStartBtn")?.addEventListener("click",practiceStart);
 $("#practiceAirlineBtn")?.addEventListener("click",startAirlinePractice);
 document.addEventListener("click",e=>{
  const b=e.target.closest("[data-action]");if(!b)return;
  const a=b.dataset.action;
  if(a==="home")home();
  else if(a==="flight"){if(requirePaid())setView("flight")}
  else if(a==="practice"){if(requirePaid())startAirlinePractice()}
  else if(a==="item"){if(requirePaid())setView("item")}
  else if(a==="baggage"){if(requirePaid()){setView("baggage");baggage()}}
  else if(a==="cuba"){if(requirePaid()){setView("cuba");cubaGuide()}}
  else if(a==="guide"){if(requirePaid()){setView("guide")}}
  else if(a==="sources"){if(requirePaid()){setView("sources");officialSources()}}
  else if(a==="teach"){if(requirePaid())setView("teach")}
  else if(a==="legal"){setView("legal");legal()}
  else if(a==="baggageSources"){if(requirePaid()){setView("sources");charterSources()}}
  else if(a==="cuba-visa"){startCubaPractice("visa")}
  else if(a==="cuba-dviajeros"){startCubaPractice("dviajeros")}
  else if(a==="cuba-official"){if(requirePaid()){setView("cuba");cubaGuide()}}
  else if(a==="pay"||a==="payment")createCheckout();
  else if(a==="logout")logout()
 });
 createHiddenAdminAccess()
}
function init(){
 document.documentElement.lang=APP.lang;
 bind();translate();ensureAirlineField();ensureFlightPracticeButton();
 if(active())setView("home");else setView("payment");
 Promise.resolve().then(async()=>{
  await loadConfig();
  if(active())await checkSession();
  const q=new URLSearchParams(location.search);
  if(q.get("session_id")||q.get("checkout_session_id")){const ok=await verifyPayment();if(ok)await checkSession()}
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
window.baggage=baggage;
window.toggleLang=toggleLang;
window.legal=legal;
window.startAirlinePractice=startAirlinePractice;
window.startCubaPractice=startCubaPractice;
window.finishCuba=finishCuba;
document.addEventListener("DOMContentLoaded",init);
