"use strict";

const APP={
name:"¿QUÉ QUIERES LLEVAR?",
version:"8.3.0",
lang:localStorage.getItem("qql_lang")||"es",
session:null,
config:null,
adminTaps:0,
adminTapTimer:null,
practice:{step:0,airline:"",trip:"round",origin:"",destination:"",departure:"",returnDate:"",passengers:1,flight:null,passenger:{first:"",last:"",email:""},baggage:"none",seat:"",extras:[]}
};

const $=id=>document.getElementById(id);
const qs=s=>document.querySelector(s);
const qsa=s=>Array.from(document.querySelectorAll(s));

const T={
es:{
loading:"Cargando...",
start:"Comenzar",
flight:"Preparar mi vuelo",
practice:"Practicar con una aerolínea",
item:"¿Qué puedo llevar?",
baggage:"Equipaje",
cuba:"Cuba",
guide:"Mi guía",
sources:"Fuentes oficiales",
teach:"Aprender un término",
legal:"Aviso legal",
back:"Volver",
next:"Continuar",
search:"Buscar vuelos",
startPractice:"Comenzar simulación",
finish:"Finalizar simulación",
round:"Ida y vuelta",
oneway:"Solo ida",
none:"Sin equipaje",
carry:"Equipaje de mano",
checked:"Maleta facturada",
both:"Mano + facturada",
select:"Seleccionar",
selected:"Seleccionado",
fictional:"SIMULACIÓN / ENTRENAMIENTO",
continue:"Continuar",
review:"Revisar",
real:"Esto es una simulación. No crea una reserva ni realiza un pago.",
paymentStop:"La simulación termina antes del pago.",
first:"Nombre ficticio",
last:"Apellido ficticio",
email:"Correo de práctica",
seat:"Selecciona un asiento",
passenger:"Datos del pasajero ficticio",
flightSelected:"Vuelo seleccionado",
baggageSelected:"Equipaje seleccionado",
reviewTitle:"Revisión de tu simulación",
complete:"Simulación completada",
official:"Para realizar el proceso real, utiliza el sitio o la aplicación oficial de la aerolínea.",
required:"Completa los campos necesarios.",
error:"Ocurrió un error. Intenta nuevamente.",
noSession:"Necesitas iniciar una sesión.",
admin:"Acceso administrativo",
login:"Entrar",
logout:"Salir"
},
en:{
loading:"Loading...",
start:"Start",
flight:"Prepare my flight",
practice:"Practice with an airline",
item:"What can I take?",
baggage:"Baggage",
cuba:"Cuba",
guide:"My guide",
sources:"Official sources",
teach:"Learn a term",
legal:"Legal notice",
back:"Back",
next:"Continue",
search:"Search flights",
startPractice:"Start simulation",
finish:"Finish simulation",
round:"Round trip",
oneway:"One way",
none:"No baggage",
carry:"Carry-on",
checked:"Checked bag",
both:"Carry-on + checked",
select:"Select",
selected:"Selected",
fictional:"SIMULATION / TRAINING",
continue:"Continue",
review:"Review",
real:"This is a simulation. It does not create a reservation or make a payment.",
paymentStop:"The simulation ends before payment.",
first:"Fictional first name",
last:"Fictional last name",
email:"Practice email",
seat:"Select a seat",
passenger:"Fictional passenger information",
flightSelected:"Selected flight",
baggageSelected:"Selected baggage",
reviewTitle:"Review your simulation",
complete:"Simulation completed",
official:"For the real process, use the airline's official website or app.",
required:"Complete the required fields.",
error:"An error occurred. Try again.",
noSession:"You need to start a session.",
admin:"Administrative access",
login:"Login",
logout:"Logout"
}
};

const tr=k=>(T[APP.lang]&&T[APP.lang][k])||T.es[k]||k;
const esc=v=>String(v??"").replace(/[&<>"']/g,m=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[m]));

function api(path,opt={}){
return fetch(path,Object.assign({headers:{"Content-Type":"application/json"}},opt)).then(async r=>{
let d=null;
try{d=await r.json()}catch(_){}
if(!r.ok){
let e=new Error(d?.detail||d?.message||"HTTP "+r.status);
e.status=r.status;
e.data=d;
throw e;
}
return d;
});
}

function setView(id){
qsa("main section[id]").forEach(s=>s.hidden=s.id!==id);
const h=$(id);
if(h)h.hidden=false;
window.scrollTo({top:0,behavior:"smooth"});
}

function home(){
setView("home");
translate();
}

function loading(v=true){
const x=$("loading");
if(x)x.hidden=!v;
}

function msg(el,text,type=""){
if(!el)return;
el.className="result "+type;
el.innerHTML=text;
}

function button(label,action,cls=""){
return `<button type="button" class="${cls}" data-dyn-action="${esc(action)}">${esc(label)}</button>`;
}

function translate(){
const b=$("langBtn");
if(b)b.textContent=APP.lang==="es"?"EN":"ES";
const s=$("startBtn");
if(s)s.textContent=tr("start");
const a=$("adminBtn");
if(a)a.textContent=tr("admin");
const map={
flight:tr("flight"),
practice:tr("practice"),
item:tr("item"),
baggage:tr("baggage"),
cuba:tr("cuba"),
guide:tr("guide"),
sources:tr("sources"),
teach:tr("teach"),
legal:tr("legal")
};
qsa("[data-action]").forEach(x=>{
const k=x.getAttribute("data-action");
if(map[k])x.textContent=map[k];
});
const ps=$("practiceStartBtn");
if(ps)ps.textContent=tr("startPractice");
}

async function getConfig(){
try{
APP.config=await api("/api/v1/config");
}catch(_){
APP.config=null;
}
}

async function checkSession(){
try{
const d=await api("/api/v1/session");
APP.session=d||{active:false};
if(APP.session.active){
const s=$("sessionStatus");
if(s)s.textContent=APP.lang==="es"?"Sesión activa":"Session active";
return true;
}
const s=$("sessionStatus");
if(s)s.textContent=APP.lang==="es"?"Sesión no iniciada":"Session not started";
return false;
}catch(e){
APP.session=null;
const s=$("sessionStatus");
if(s)s.textContent=tr("noSession");
return false;
}
}

async function startSession(){
loading(true);
try{
const d=await api("/api/v1/session",{method:"POST",body:JSON.stringify({})});
APP.session=d||{active:true};
home();
}catch(e){
const s=$("sessionStatus");
if(s)s.textContent=e.message||tr("error");
}finally{loading(false)}
}

async function createCheckout(){
try{
const d=await api("/api/v1/create-checkout",{method:"POST",body:JSON.stringify({})});
if(d?.url)location.href=d.url;
else if(d?.checkout_url)location.href=d.checkout_url;
else alert(d?.message||tr("error"));
}catch(e){alert(e.message||tr("error"))}
}

async function verifyPayment(){
try{
const d=await api("/api/v1/verify-payment",{method:"POST",body:JSON.stringify({})});
if(d?.active||d?.paid){
APP.session=d;
home();
}else alert(d?.message||tr("error"));
}catch(e){alert(e.message||tr("error"))}
}

function dataObject(){
return{
origin:$("origin")?.value.trim()||"",
destination:$("destination")?.value.trim()||"",
departureDate:$("departureDate")?.value||"",
returnDate:$("returnDate")?.value||"",
airline:$("airline")?.value||"",
cabin:$("cabin")?.value||"",
fare:$("fare")?.value||"",
passengers:Number($("passengers")?.value||1),
stops:$("stops")?.value||""
};
}

function showFlightData(d){
const r=$("flightResult");
if(!r)return;
const x=d?.understood||d?.result||d||{};
let html=`<div class="resultCard"><h3>${esc(APP.lang==="es"?"Preparación del vuelo":"Flight preparation")}</h3>`;
if(x.origin)html+=`<p><b>Origen:</b> ${esc(x.origin)}</p>`;
if(x.destination)html+=`<p><b>Destino:</b> ${esc(x.destination)}</p>`;
if(x.departureDate)html+=`<p><b>Salida:</b> ${esc(x.departureDate)}</p>`;
if(x.returnDate)html+=`<p><b>Regreso:</b> ${esc(x.returnDate)}</p>`;
if(x.airline)html+=`<p><b>Aerolínea:</b> ${esc(x.airline)}</p>`;
if(x.cabin)html+=`<p><b>Cabina:</b> ${esc(x.cabin)}</p>`;
if(x.fare)html+=`<p><b>Tarifa:</b> ${esc(x.fare)}</p>`;
if(x.passengers)html+=`<p><b>Pasajeros:</b> ${esc(x.passengers)}</p>`;
if(x.stops)html+=`<p><b>Escalas:</b> ${esc(x.stops)}</p>`;
if(Array.isArray(d?.steps)&&d.steps.length){
html+=`<h4>${APP.lang==="es"?"Pasos":"Steps"}</h4><ol>`;
d.steps.forEach(v=>html+=`<li>${esc(typeof v==="string"?v:(v.label||v.title||JSON.stringify(v)))}</li>`);
html+=`</ol>`;
}
html+=`<p><small>${tr("real")}</small></p></div>`;
msg(r,html);
}

async function flight(){
if(!(await checkSession()))return;
const d=dataObject();
if(!d.origin||!d.destination||!d.departureDate||!d.airline){
msg($("flightResult"),`<b>${tr("required")}</b>`,"error");
return;
}
loading(true);
try{
const r=await api("/api/v1/flight/understand",{method:"POST",body:JSON.stringify(d)});
showFlightData(r);
}catch(e){
msg($("flightResult"),esc(e.message||tr("error")),"error");
}finally{loading(false)}
}

function setPracticeAirline(v){
const x=$("practiceAirline");
if(x)x.value=v||"";
}

function practiceReset(){
APP.practice={
step:0,airline:$("practiceAirline")?.value||"",
trip:"round",origin:"",destination:"",departure:"",returnDate:"",
passengers:1,flight:null,passenger:{first:"",last:"",email:""},baggage:"none",seat:"",extras:[]
};
}

function practiceStart(){
const airline=$("practiceAirline")?.value||"";
if(!airline){
msg($("practiceResult"),tr("required"),"error");
return;
}
practiceReset();
APP.practice.airline=airline;
renderPractice();
}

function practiceShell(title,body,footer=""){
return `<div class="resultCard practiceCard"><div><strong>${esc(tr("fictional"))}</strong></div><h3>${title}</h3>${body}${footer}</div>`;
}

function practiceNav(back=true,next=""){
return `<div class="practiceNav">${back?button(tr("back"),"practice-back"):""}${next?button(next,"practice-next"):""}</div>`;
}

function renderPractice(){
const r=$("practiceResult");
if(!r)return;
const p=APP.practice;
let h="";
if(p.step===0){
h=practiceShell(
APP.lang==="es"?"1. Tipo de viaje":"1. Trip type",
`<p>${tr("real")}</p>
<div class="choiceGrid">
<button type="button" data-practice-trip="round" class="${p.trip==="round"?"selected":""}">${tr("round")}</button>
<button type="button" data-practice-trip="oneway" class="${p.trip==="oneway"?"selected":""}">${tr("oneway")}</button>
</div>`,
practiceNav(false,tr("next"))
);
}
else if(p.step===1){
h=practiceShell(
APP.lang==="es"?"2. Viaje":"2. Trip",
`<label>Origen<input id="pOrigin" value="${esc(p.origin)}" placeholder="Miami"></label>
<label>Destino<input id="pDestination" value="${esc(p.destination)}" placeholder="Madrid"></label>
<label>Salida<input id="pDeparture" type="date" value="${esc(p.departure)}"></label>
${p.trip==="round"?`<label>Regreso<input id="pReturn" type="date" value="${esc(p.returnDate)}"></label>`:""}
<label>Pasajeros<input id="pPassengers" type="number" min="1" max="9" value="${p.passengers}"></label>`,
practiceNav(true,tr("search"))
);
}
else if(p.step===2){
const flights=[
{id:"A1",time:"08:20",arrive:"11:05",route:p.origin+" → "+p.destination,code:"MR101"},
{id:"A2",time:"12:40",arrive:"15:25",route:p.origin+" → "+p.destination,code:"MR205"},
{id:"A3",time:"18:15",arrive:"21:00",route:p.origin+" → "+p.destination,code:"MR318"}
];
h=practiceShell(
APP.lang==="es"?"3. Selecciona un vuelo ficticio":"3. Select a fictional flight",
`<p>${esc(p.airline)} · ${esc(p.departure)}</p>
<div class="flightChoices">`+
flights.map(f=>`<button type="button" class="flightChoice ${p.flight?.id===f.id?"selected":""}" data-practice-flight="${f.id}" data-time="${f.time}" data-arrive="${f.arrive}" data-code="${f.code}"><strong>${f.code}</strong><br>${f.time} → ${f.arrive}<br><small>${esc(f.route)}</small></button>`).join("")+
`</div>${practiceNav(true,p.flight?tr("next"):"")}`
);
}
else if(p.step===3){
h=practiceShell(
tr("passenger"),
`<p>${tr("real")}</p>
<label>${tr("first")}<input id="pFirst" value="${esc(p.passenger.first)}" autocomplete="off"></label>
<label>${tr("last")}<input id="pLast" value="${esc(p.passenger.last)}" autocomplete="off"></label>
<label>${tr("email")}<input id="pEmail" type="email" value="${esc(p.passenger.email)}" autocomplete="off"></label>`,
practiceNav(true,tr("next"))
);
}
else if(p.step===4){
const choices=[
["none",tr("none")],
["carry",tr("carry")],
["checked",tr("checked")],
["both",tr("both")]
];
h=practiceShell(
APP.lang==="es"?"5. Equipaje":"5. Baggage",
`<p>${tr("real")}</p><div class="choiceGrid">`+
choices.map(c=>`<button type="button" data-practice-bag="${c[0]}" class="${p.baggage===c[0]?"selected":""}">${c[1]}</button>`).join("")+
`</div>${practiceNav(true,p.baggage?tr("next"):"")}`
);
}
else if(p.step===5){
const rows=["1A","1B","1C","1D","2A","2B","2C","2D","3A","3B","3C","3D","4A","4B","4C","4D"];
h=practiceShell(
tr("seat"),
`<p>${tr("real")}</p><div class="seatGrid">`+
rows.map(s=>`<button type="button" data-practice-seat="${s}" class="${p.seat===s?"selected":""}">${s}</button>`).join("")+
`</div>${practiceNav(true,p.seat?tr("next"):"")}`
);
}
else if(p.step===6){
h=practiceShell(
tr("reviewTitle"),
`<div class="reviewBox">
<p><b>${tr("flightSelected")}:</b> ${esc(p.flight?.code||"")} · ${esc(p.flight?.time||"")} → ${esc(p.flight?.arrive||"")}</p>
<p><b>Aerolínea:</b> ${esc(p.airline)}</p>
<p><b>Ruta:</b> ${esc(p.origin)} → ${esc(p.destination)}</p>
<p><b>Salida:</b> ${esc(p.departure)}</p>
${p.trip==="round"?`<p><b>Regreso:</b> ${esc(p.returnDate)}</p>`:""}
<p><b>Pasajeros:</b> ${p.passengers}</p>
<p><b>Pasajero ficticio:</b> ${esc(p.passenger.first)} ${esc(p.passenger.last)}</p>
<p><b>Equipaje:</b> ${esc(bagText(p.baggage))}</p>
<p><b>Asiento:</b> ${esc(p.seat)}</p>
</div>`,
practiceNav(true,tr("finish"))
);
}
else{
h=practiceShell(
tr("complete"),
`<p>${tr("paymentStop")}</p>
<p>${tr("official")}</p>
<p><b>${esc(p.airline)}</b></p>
${button(tr("back"),"practice-back")} ${button(tr("finish"),"practice-end")}`
);
}
r.innerHTML=h;
}

function bagText(v){
return{
none:tr("none"),
carry:tr("carry"),
checked:tr("checked"),
both:tr("both")
}[v]||v;
}

function practiceNext(){
const p=APP.practice;
if(p.step===0){p.step=1;renderPractice();return}
if(p.step===1){
p.origin=$("pOrigin")?.value.trim()||"";
p.destination=$("pDestination")?.value.trim()||"";
p.departure=$("pDeparture")?.value||"";
p.returnDate=$("pReturn")?.value||"";
p.passengers=Math.max(1,Math.min(9,Number($("pPassengers")?.value||1)));
if(!p.origin||!p.destination||!p.departure||(p.trip==="round"&&!p.returnDate)){
alert(tr("required"));return;
}
p.step=2;renderPractice();return;
}
if(p.step===2){if(!p.flight){alert(tr("required"));return}p.step=3;renderPractice();return}
if(p.step===3){
p.passenger.first=$("pFirst")?.value.trim()||"";
p.passenger.last=$("pLast")?.value.trim()||"";
p.passenger.email=$("pEmail")?.value.trim()||"";
if(!p.passenger.first||!p.passenger.last){alert(tr("required"));return}
p.step=4;renderPractice();return;
}
if(p.step===4){p.step=5;renderPractice();return}
if(p.step===5){if(!p.seat){alert(tr("required"));return}p.step=6;renderPractice();return}
if(p.step===6){p.step=7;renderPractice();return}
}

function practiceBack(){
if(APP.practice.step>0){
APP.practice.step--;
renderPractice();
}else setView("practice");
}

function practiceEnd(){
APP.practice.step=0;
const r=$("practiceResult");
if(r)r.innerHTML=practiceShell(
tr("complete"),
`<p>${tr("paymentStop")}</p><p>${tr("official")}</p>
${button(APP.lang==="es"?"Volver a inicio":"Back home","home")}`
);
}

function startFlightPractice(){
const a=$("airline")?.value||"";
setPracticeAirline(a);
setView("practice");
renderPractice();
}

async function itemConsult(){
if(!(await checkSession()))return;
const name=$("itemName")?.value.trim()||"";
if(!name){
msg($("itemResult"),tr("required"),"error");
return;
}
const payload={
item:name,
quantity:Number($("itemQty")?.value||1),
description:$("itemDescription")?.value.trim()||"",
baggage_type:$("baggage_type")?.value||"",
airline:$("itemAirline")?.value||"",
destination:$("itemDestination")?.value||"",
wh:Number($("itemWh")?.value||0),
volts:Number($("itemVolts")?.value||0),
ah:Number($("itemAh")?.value||0),
mah:Number($("itemMah")?.value||0)
};
loading(true);
try{
const d=await api("/api/v1/item/check",{method:"POST",body:JSON.stringify(payload)});
renderGenericResult("itemResult",d,"Consulta del artículo");
}catch(e){msg($("itemResult"),esc(e.message||tr("error")),"error")}
finally{loading(false)}
}

async function baggage(){
if(!(await checkSession()))return;
loading(true);
try{
const d=await api("/api/v1/baggage",{method:"POST",body:JSON.stringify({
airline:$("airline")?.value||"",
cabin:$("cabin")?.value||"",
destination:$("destination")?.value||""
})});
renderGenericResult("baggageResult",d,"Equipaje");
}catch(e){msg($("baggageResult"),esc(e.message||tr("error")),"error")}
finally{loading(false)}
}

function renderGenericResult(id,d,title){
const r=$(id);
if(!r)return;
let h=`<div class="resultCard"><h3>${esc(title)}</h3>`;
if(typeof d==="string")h+=`<p>${esc(d)}</p>`;
else{
const walk=(v)=>{
if(v===null||v===undefined)return"";
if(typeof v==="string"||typeof v==="number"||typeof v==="boolean")return esc(v);
if(Array.isArray(v))return `<ul>${v.map(x=>`<li>${walk(x)}</li>`).join("")}</ul>`;
return `<div>${Object.entries(v).map(([k,x])=>`<p><b>${esc(k)}:</b> ${walk(x)}</p>`).join("")}</div>`;
};
h+=walk(d);
}
h+=`</div>`;
msg(r,h);
}

async function sources(){
loading(true);
try{
const d=await api("/api/v1/official-sources");
renderGenericResult("sourcesResult",d,"Fuentes oficiales");
}catch(e){msg($("sourcesResult"),esc(e.message||tr("error")),"error")}
finally{loading(false)}
}

async function flightSources(){
try{
const d=await api("/api/v1/flight/sources");
renderGenericResult("flightResult",d,"Fuentes oficiales de vuelos");
}catch(e){msg($("flightResult"),esc(e.message||tr("error")),"error")}
}

async function guide(){
if(!(await checkSession()))return;
loading(true);
try{
const d=await api("/api/v1/guide");
renderGenericResult("guideResult",d,"Mi guía");
}catch(e){msg($("guideResult"),esc(e.message||tr("error")),"error")}
finally{loading(false)}
}

async function teach(){
const term=$("term")?.value.trim()||"";
if(!term){
msg($("teachResult"),tr("required"),"error");
return;
}
loading(true);
try{
const d=await api("/api/v1/terms",{method:"POST",body:JSON.stringify({term})});
renderGenericResult("teachResult",d,"Término");
}catch(e){
try{
const d=await api("/api/v1/item/teach",{method:"POST",body:JSON.stringify({term})});
renderGenericResult("teachResult",d,"Término");
}catch(_){msg($("teachResult"),esc(e.message||tr("error")),"error")}
}finally{loading(false)}
}

async function legal(){
try{
const d=await api("/api/v1/legal");
renderGenericResult("legalResult",d,"Aviso legal");
}catch(e){
msg($("legalResult"),`
<div class="resultCard">
<h3>Aviso legal</h3>
<p>¿QUÉ QUIERES LLEVAR? es un servicio independiente de May Roga LLC.</p>
<p>No es una aerolínea, agencia de viajes, autoridad gubernamental ni servicio de reserva.</p>
<p>La información debe verificarse en las fuentes oficiales correspondientes.</p>
</div>`);
}
}

function cubaPracticeStart(type){
setView("cubaPractice");
const r=$("cubaPracticeResult");
if(!r)return;
renderCubaPractice(type||"general",0,{});
}

function renderCubaPractice(type,step,data){
const r=$("cubaPracticeResult");
if(!r)return;
let h=`<div class="resultCard"><strong>${tr("fictional")}</strong>`;
if(step===0){
h+=`<h3>${type==="visa"?"Simulación de visa / eVisa":"Simulación D’Viajeros"}</h3>
<p>Esta práctica no envía datos a ninguna autoridad.</p>
<label>Nombre ficticio<input id="cpName" value="${esc(data.name||"")}"></label>
<label>Nacionalidad ficticia<input id="cpNationality" value="${esc(data.nationality||"")}"></label>
<label>Fecha de viaje<input id="cpDate" type="date" value="${esc(data.date||"")}"></label>
<button type="button" data-cuba-next="1" data-cuba-type="${esc(type)}">${tr("next")}</button>`;
}else if(step===1){
h+=`<h3>Revisión de práctica</h3>
<p><b>Proceso:</b> ${type==="visa"?"Visa / eVisa":"D’Viajeros"}</p>
<p><b>Nombre:</b> ${esc(data.name)}</p>
<p><b>Nacionalidad:</b> ${esc(data.nationality)}</p>
<p><b>Fecha:</b> ${esc(data.date)}</p>
<p>Estos datos son únicamente de entrenamiento.</p>
<button type="button" data-cuba-next="2" data-cuba-type="${esc(type)}">${tr("next")}</button>`;
}else{
h+=`<h3>${tr("complete")}</h3>
<p>No se realizó ningún envío.</p>
<p>${tr("official")}</p>
<button type="button" data-action="cuba">${tr("back")}</button>`;
}
h+=`</div>`;
r.innerHTML=h;
r.dataset.cubaType=type;
r.dataset.cubaStep=step;
r.dataset.cubaData=JSON.stringify(data);
}

function cubaNext(type,step){
let data={};
try{data=JSON.parse($("cubaPracticeResult").dataset.cubaData||"{}")}catch(_){}
if(step===1){
data.name=$("cpName")?.value.trim()||"";
data.nationality=$("cpNationality")?.value.trim()||"";
data.date=$("cpDate")?.value||"";
if(!data.name||!data.nationality||!data.date){alert(tr("required"));return}
}
renderCubaPractice(type,step,data);
}

async function cubaOfficial(){
try{
const d=await api("/api/v1/cuba/official");
renderGenericResult("cubaResult",d,"Fuentes oficiales de Cuba");
}catch(e){msg($("cubaResult"),esc(e.message||tr("error")),"error")}
}

async function cubaVisa(){
cubaPracticeStart("visa");
}

async function cubaDviajeros(){
cubaPracticeStart("dviajeros");
}

async function cubaGeneralPractice(){
cubaPracticeStart("general");
}

function openHiddenAdmin(){
let box=$("qqlHiddenAdmin");
if(box){box.hidden=false;return}
box=document.createElement("div");
box.id="qqlHiddenAdmin";
box.className="resultCard";
box.innerHTML=`
<div style="position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px">
<div style="background:#fff;max-width:420px;width:100%;padding:20px;border-radius:12px">
<h3>${tr("admin")}</h3>
<label>Username<input id="qqlHiddenUser" autocomplete="username"></label>
<label>Password<input id="qqlHiddenPass" type="password" autocomplete="current-password"></label>
<div id="qqlHiddenMsg"></div>
<div style="display:flex;gap:8px;margin-top:12px">
<button type="button" id="qqlHiddenLogin">${tr("login")}</button>
<button type="button" id="qqlHiddenClose">${tr("back")}</button>
</div>
</div></div>`;
document.body.appendChild(box);
$("qqlHiddenClose").onclick=()=>box.remove();
$("qqlHiddenLogin").onclick=adminLogin;
}

async function adminLogin(){
const u=$("qqlHiddenUser")?.value||"";
const p=$("qqlHiddenPass")?.value||"";
const m=$("qqlHiddenMsg");
if(!u||!p){
if(m)m.textContent=tr("required");
return;
}
try{
const d=await api("/api/v1/admin/login",{method:"POST",body:JSON.stringify({username:u,password:p})});
if(d?.ok||d?.success||d?.token||d?.admin){
if(m)m.innerHTML="<b>Admin OK</b>";
if(d?.redirect)location.href=d.redirect;
else if(d?.url)location.href=d.url;
else{
const x=$("qqlHiddenAdmin");
if(x)x.remove();
}
}else if(m)m.textContent=d?.message||tr("error");
}catch(e){
if(m)m.textContent=e.message||tr("error");
}
}

function adminTapHandler(e){
if(e.target.closest("button,input,select,textarea,a"))return;
APP.adminTaps++;
clearTimeout(APP.adminTapTimer);
APP.adminTapTimer=setTimeout(()=>APP.adminTaps=0,900);
if(APP.adminTaps>=3){
APP.adminTaps=0;
openHiddenAdmin();
}
}

function createHiddenAdminAccess(){
const h=$("home");
if(!h)return;
h.removeEventListener("click",adminTapHandler);
h.addEventListener("click",adminTapHandler);
}

function goAction(a){
switch(a){
case"flight":setView("flight");break;
case"practice":setView("practice");renderPractice();break;
case"item":setView("item");break;
case"baggage":setView("baggage");break;
case"cuba":setView("cuba");break;
case"guide":setView("guide");break;
case"sources":setView("sources");sources();break;
case"teach":setView("teach");break;
case"legal":setView("legal");legal();break;
case"cuba-visa":cubaVisa();break;
case"cuba-dviajeros":cubaDviajeros();break;
case"cuba-official":cubaOfficial();break;
case"baggageSources":flightSources();break;
case"cuba-practice":cubaGeneralPractice();break;
case"home":home();break;
case"practice-back":practiceBack();break;
case"practice-next":practiceNext();break;
case"practice-end":practiceEnd();break;
}
}

function bind(){
$("langBtn")?.addEventListener("click",()=>{
APP.lang=APP.lang==="es"?"en":"es";
localStorage.setItem("qql_lang",APP.lang);
translate();
});
$("startBtn")?.addEventListener("click",async()=>{
if(await checkSession())setView("flight");
else await startSession();
});
$("adminBtn")?.addEventListener("click",openHiddenAdmin);
$("flightBtn")?.addEventListener("click",flight);
$("practiceAirlineBtn")?.addEventListener("click",startFlightPractice);
$("practiceStartBtn")?.addEventListener("click",practiceStart);
$("itemBtn")?.addEventListener("click",itemConsult);
$("guideBtn")?.addEventListener("click",guide);
qsa("[data-action]").forEach(x=>x.addEventListener("click",e=>{
e.preventDefault();
goAction(x.getAttribute("data-action"));
}));
document.addEventListener("click",e=>{
const a=e.target.closest("[data-dyn-action]");
if(a){e.preventDefault();goAction(a.dataset.dynAction);return}
const t=e.target.closest("[data-practice-trip]");
if(t){
APP.practice.trip=t.dataset.practiceTrip;
renderPractice();
return;
}
const f=e.target.closest("[data-practice-flight]");
if(f){
APP.practice.flight={
id:f.dataset.practiceFlight,
time:f.dataset.time,
arrive:f.dataset.arrive,
code:f.dataset.code
};
renderPractice();
return;
}
const b=e.target.closest("[data-practice-bag]");
if(b){
APP.practice.baggage=b.dataset.practiceBag;
renderPractice();
return;
}
const s=e.target.closest("[data-practice-seat]");
if(s){
APP.practice.seat=s.dataset.practiceSeat;
renderPractice();
return;
}
const c=e.target.closest("[data-cuba-next]");
if(c){
const type=c.dataset.cubaType;
const step=Number(c.dataset.cubaNext);
cubaNext(type,step);
return;
}
});
createHiddenAdminAccess();
}

async function init(){
loading(true);
try{
await getConfig();
translate();
bind();
await checkSession();
setView("home");
}catch(e){
console.error(e);
}finally{loading(false)}
}

document.addEventListener("DOMContentLoaded",init);
