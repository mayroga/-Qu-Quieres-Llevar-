"use strict";

const APP={
 name:"¿QUÉ QUIERES LLEVAR?",
 version:"9.0.0",
 lang:localStorage.getItem("qql_lang")||"es",
 token:localStorage.getItem("qql_session")||"",
 screen:"home"
};

const $=id=>document.getElementById(id);
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const val=id=>$(id)?.value?.trim()||"";
const post=async(url,data={})=>{
 const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json",...(APP.token?{"X-Session-Token":APP.token}:{})},body:JSON.stringify({...data,language:APP.lang})});
 let j={};
 try{j=await r.json()}catch(e){j={ok:false,message:"Respuesta no válida"}}
 if(!r.ok)throw new Error(j.message||"Error");
 return j
};
const get=async(url)=>{
 const u=new URL(url,location.origin);
 u.searchParams.set("language",APP.lang);
 if(APP.token)u.searchParams.set("session_token",APP.token);
 const r=await fetch(u.toString(),{headers:APP.token?{"X-Session-Token":APP.token}:{}});
 let j={};
 try{j=await r.json()}catch(e){j={ok:false,message:"Respuesta no válida"}}
 if(!r.ok)throw new Error(j.message||"Error");
 return j
};

function show(id){
 document.querySelectorAll(".screen").forEach(x=>x.classList.add("hidden"));
 const el=$(id);
 if(el)el.classList.remove("hidden");
 APP.screen=id;
 window.scrollTo({top:0,behavior:"smooth"});
}

function msg(text,type=""){
 const el=$("appMessage");
 if(!el)return;
 el.className="app-message "+type;
 el.textContent=text||"";
}

function busy(button,state,text){
 if(!button)return;
 if(state){
  button.dataset.original=button.textContent;
  button.disabled=true;
  button.textContent=text||"Procesando...";
 }else{
  button.disabled=false;
  button.textContent=button.dataset.original||button.textContent;
 }
}

function renderSources(list){
 if(!Array.isArray(list)||!list.length)return `<p>${APP.lang==="es"?"No hay fuentes disponibles para esta consulta.":"No sources are available for this request."}</p>`;
 return `<div class="sources">${list.map(s=>`<article class="source"><h3>${esc(s.name)}</h3><p>${esc(s.description||"")}</p><a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">Abrir fuente oficial ↗</a></article>`).join("")}</div>`;
}

function renderSteps(steps){
 if(!Array.isArray(steps)||!steps.length)return "";
 return `<div class="steps">${steps.map((s,i)=>`<article class="step${s.important?" important":""}"><b>${i+1}. ${esc(s.title)}</b><p>${esc(s.text)}</p></article>`).join("")}</div>`;
}

function renderResult(el,data){
 if(!el)return;
 if(!data||data.ok===false){
  el.innerHTML=`<div class="notice error">${esc(data?.message||(APP.lang==="es"?"No se pudo completar la consulta.":"The request could not be completed."))}</div>`;
  return;
 }
 let html="";
 if(data.title)html+=`<h3>${esc(data.title)}</h3>`;
 if(data.message)html+=`<p>${esc(data.message)}</p>`;
 if(data.result?.steps)html+=renderSteps(data.result.steps);
 else if(data.steps)html+=renderSteps(data.steps);
 if(data.result?.definition||data.definition)html+=`<div class="definition">${esc(data.result?.definition||data.definition)}</div>`;
 if(data.sources)html+=renderSources(data.sources);
 if(data.source)html+=renderSources([data.source]);
 if(data.results?.length)html+=data.results.map(x=>`<article class="step"><b>${esc(x.origin||"")} → ${esc(x.destination||"")}</b><p>${esc(x.message||"")}</p></article>`).join("");
 el.innerHTML=html||`<p>${APP.lang==="es"?"Consulta completada.":"Request completed."}</p>`;
}

async function init(){
 try{
  const data=await get("/api/v1/config");
  if(data.language)APP.lang=data.language;
 }catch(e){}
 $("loading")?.classList.add("hidden");
 show("home");
 updateLanguageButton();
 bind();
 loadLegal();
}

function updateLanguageButton(){
 const b=$("langBtn");
 if(b)b.textContent=APP.lang==="es"?"EN":"ES";
 document.documentElement.lang=APP.lang;
}

function toggleLanguage(){
 APP.lang=APP.lang==="es"?"en":"es";
 localStorage.setItem("qql_lang",APP.lang);
 updateLanguageButton();
 msg("");
}

async function createSession(){
 if(APP.token)return APP.token;
 try{
  const data=await post("/api/v1/session",{});
  if(data.session_token){
   APP.token=data.session_token;
   localStorage.setItem("qql_session",APP.token);
  }
 }catch(e){}
 return APP.token;
}

async function flight(){
 const button=$("flightBtn");
 const result=$("flightResult");
 busy(button,true,APP.lang==="es"?"Revisando...":"Checking...");
 try{
  await createSession();
  const data=await post("/api/v1/flight/understand",{
   origin:val("origin"),
   destination:val("destination"),
   departure_date:val("departureDate"),
   return_date:val("returnDate"),
   airline:val("airline"),
   cabin:val("cabin"),
   fare:val("fare"),
   passengers:Number(val("passengers")||1),
   stops:val("stops")
  });
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }finally{busy(button,false)}
}

async function item(){
 const button=$("itemBtn");
 const result=$("itemResult");
 busy(button,true,APP.lang==="es"?"Consultando...":"Checking...");
 try{
  await createSession();
  const data=await post("/api/v1/item/check",{
   item_name:val("itemName"),
   quantity:Number(val("itemQty")||1),
   description:val("itemDescription"),
   baggage_type:val("itemBaggage"),
   airline:val("itemAirline"),
   destination:val("itemDestination")
  });
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }finally{busy(button,false)}
}

async function baggage(){
 const button=$("baggageBtn");
 const result=$("baggageResult");
 busy(button,true,APP.lang==="es"?"Revisando...":"Checking...");
 try{
  const data=await post("/api/v1/baggage",{
   airline:val("baggageAirline"),
   destination:val("baggageDestination"),
   bag_type:val("baggageType")
  });
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }finally{busy(button,false)}
}

async function sources(){
 const result=$("sourcesResult");
 result.innerHTML=`<p>${APP.lang==="es"?"Cargando...":"Loading..."}</p>`;
 try{
  const data=await get("/api/v1/sources/official");
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }
}

async function legal(){
 const result=$("legalResult");
 result.innerHTML=`<p>${APP.lang==="es"?"Cargando...":"Loading..."}</p>`;
 try{
  const data=await get("/api/v1/legal");
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }
}

async function loadLegal(){
 if(APP.screen!=="legal")return;
 await legal();
}

async function teach(){
 const button=$("teachBtn");
 const result=$("teachResult");
 busy(button,true,APP.lang==="es"?"Buscando...":"Searching...");
 try{
  const data=await post("/api/v1/item/teach",{term:val("term")});
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }finally{busy(button,false)}
}

async function guide(){
 const button=$("guideBtn");
 const result=$("guideResult");
 busy(button,true,APP.lang==="es"?"Preparando...":"Preparing...");
 try{
  const data=await post("/api/v1/guide",{
   origin:val("origin"),
   destination:val("destination"),
   departure_date:val("departureDate"),
   return_date:val("returnDate"),
   airline:val("airline"),
   item_name:val("itemName")
  });
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }finally{busy(button,false)}
}

async function cuba(topic){
 const result=$("cubaResult");
 result.innerHTML=`<p>${APP.lang==="es"?"Consultando...":"Checking..."}</p>`;
 try{
  const data=await get("/api/v1/cuba/"+topic);
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }
}

async function cubaPractice(){
 const result=$("cubaResult");
 try{
  const data=await post("/api/v1/cuba/practice",{topic:"visa"});
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }
}

async function practice(topic){
 const result=$("practiceResult");
 result.innerHTML=`<p>${APP.lang==="es"?"Preparando práctica...":"Preparing practice..."}</p>`;
 try{
  const data=await post("/api/v1/practice",{topic});
  renderResult(result,data);
 }catch(e){
  renderResult(result,{ok:false,message:e.message});
 }
}

function bind(){
 $("langBtn")?.addEventListener("click",toggleLanguage);
 $("startBtn")?.addEventListener("click",()=>show("flight"));
 $("flightBtn")?.addEventListener("click",flight);
 $("itemBtn")?.addEventListener("click",item);
 $("baggageBtn")?.addEventListener("click",baggage);
 $("sourcesBtn")?.addEventListener("click",sources);
 $("teachBtn")?.addEventListener("click",teach);
 $("guideBtn")?.addEventListener("click",guide);
 $("cubaVisaBtn")?.addEventListener("click",()=>cuba("visa"));
 $("cubaDviajerosBtn")?.addEventListener("click",()=>cuba("dviajeros"));
 $("cubaOfficialBtn")?.addEventListener("click",()=>cuba("official"));
 $("cubaPracticeBtn")?.addEventListener("click",cubaPractice);
 document.querySelectorAll("[data-action]").forEach(b=>b.addEventListener("click",()=>{
  const a=b.dataset.action;
  if(a==="home")show("home");
  else if(a==="flight")show("flight");
  else if(a==="item")show("item");
  else if(a==="baggage")show("baggage");
  else if(a==="cuba")show("cuba");
  else if(a==="guide")show("guide");
  else if(a==="sources")sources().then(()=>show("sources"));
  else if(a==="teach")show("teach");
  else if(a==="legal")legal().then(()=>show("legal"));
  else if(a==="practice")show("practice");
 }));
 document.querySelectorAll("[data-practice]").forEach(b=>b.addEventListener("click",()=>practice(b.dataset.practice)));
}

document.addEventListener("DOMContentLoaded",init);
