"use strict";
const APP={name:"¿QUÉ QUIERES LLEVAR?",version:"8.0.1",lang:localStorage.getItem("cuba_lang")||"es",token:localStorage.getItem("cuba_service_token")||"",adminToken:localStorage.getItem("cuba_admin_token")||"",config:null};
const $=id=>document.getElementById(id);
const q=s=>document.querySelector(s);
const qa=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const api=async(path,opt={})=>{
 const o={...opt,headers:{Accept:"application/json",...(opt.headers||{})}};
 if(APP.token)o.headers["X-Service-Token"]=APP.token;
 if(APP.adminToken)o.headers["X-Admin-Token"]=APP.adminToken;
 if(o.body&&typeof o.body!=="string"){o.headers["Content-Type"]="application/json";o.body=JSON.stringify(o.body)}
 const r=await fetch(path,o);
 let d=null;try{d=await r.json()}catch(_){d={success:false,message:"Respuesta inválida del servidor."}}
 if(!r.ok)throw Object.assign(new Error(d.message||`Error ${r.status}`),{status:r.status,data:d});
 return d
};
const show=id=>{
 qa(".screen").forEach(x=>x.classList.add("hidden"));
 $(id)?.classList.remove("hidden");
 window.scrollTo({top:0,behavior:"smooth"});
};
const msg=(id,text,good=false)=>{const e=$(id);if(e)e.innerHTML=`<div class="${good?"good":"bad"}">${esc(text)}</div>`};
const active=()=>!!APP.token;
const requirePaid=()=>{if(active())return true;show("payment");return false};
const langText={
 es:{title:"¿Qué quieres llevar?",subtitle:"Te ayudamos a organizar tu preparación de viaje, entender tu vuelo, revisar artículos y confirmar la información oficial.",start:"Empezar",flight:"Mi vuelo",flightSmall:"Entiende tu itinerario",item:"¿Qué llevo?",itemSmall:"Consulta un artículo",baggage:"Equipaje",baggageSmall:"Prepara tus maletas",cuba:"Cuba",cubaSmall:"Pasos y fuentes oficiales",guide:"Guía",guideSmall:"Prepara tu viaje",sources:"Fuentes oficiales",sourcesSmall:"Consulta directamente",teach:"Aprender un término",teachSmall:"Entiende lo que significa",legal:"Aviso legal",legalSmall:"Quién presta el servicio",paymentTitle:"Activa tu preparación",paymentText:"Servicio independiente de May Roga LLC. Pago único de $15.99 para una sesión de 15 minutos.",paymentNotice:"No somos una aerolínea, banco, agencia gubernamental ni vendedor de boletos.",pay:"Continuar al pago"},
 en:{title:"What do you want to carry?",subtitle:"We help you prepare for your trip, understand your flight, review items and confirm official information.",start:"Start",flight:"My flight",flightSmall:"Understand your itinerary",item:"What do I carry?",itemSmall:"Check an item",baggage:"Baggage",baggageSmall:"Prepare your bags",cuba:"Cuba",cubaSmall:"Steps and official sources",guide:"Guide",guideSmall:"Prepare your trip",sources:"Official sources",sourcesSmall:"Check directly",teach:"Learn a term",teachSmall:"Understand what it means",legal:"Legal notice",legalSmall:"Who provides the service",paymentTitle:"Activate your preparation",paymentText:"Independent May Roga LLC service. One-time $15.99 payment for a 15-minute session.",paymentNotice:"We are not an airline, bank, government agency or ticket seller.",pay:"Continue to payment"}
};
const renderLang=()=>{
 const t=langText[APP.lang];
 qa("[data-i18n]").forEach(e=>{if(t[e.dataset.i18n]!=null)e.textContent=t[e.dataset.i18n]});
 $("langBtn").textContent=APP.lang==="es"?"EN":"ES";
};
const updateStatus=()=>{
 $("sessionStatus").textContent=active()?(APP.lang==="es"?"Sesión activa":"Session active"):(APP.lang==="es"?"Sesión no activa":"Session not active");
};
const loadConfig=async()=>{
 try{APP.config=await api("/api/v1/config");return APP.config}catch(e){$("loadingText").textContent=e.message;return null}
};
const checkSession=async()=>{
 if(!APP.token)return false;
 try{const d=await api("/api/v1/session");if(!d.active){APP.token="";localStorage.removeItem("cuba_service_token");return false}return true}catch(_){APP.token="";localStorage.removeItem("cuba_service_token");return false}
};
const init=async()=>{
 await loadConfig();
 await checkSession();
 renderLang();updateStatus();
 show("home");
};
const payment=async()=>{
 const b=$("payBtn");b.disabled=true;$("payMsg").textContent=APP.lang==="es"?"Preparando el pago...":"Preparing payment...";
 try{
  const d=await api("/api/v1/create-checkout-session",{method:"POST",body:{language:APP.lang,return_path:"/"}});
  if(!d.success||!d.checkout_url)throw new Error(d.message||"No pudimos iniciar el pago.");
  location.href=d.checkout_url;
 }catch(e){$("payMsg").textContent=e.message;b.disabled=false}
};
const verifyPayment=async()=>{
 const p=new URLSearchParams(location.search);
 if(p.get("payment")!=="success"||!p.get("session_id"))return;
 try{
  const d=await api("/api/v1/verify-payment",{method:"POST",body:{session_id:p.get("session_id")}});
  if(d.paid&&d.service_token){
   APP.token=d.service_token;localStorage.setItem("cuba_service_token",APP.token);
   history.replaceState({},document.title,"/");
   updateStatus();show("home");
   alert(APP.lang==="es"?"Pago confirmado. Tu sesión de 15 minutos está activa.":"Payment confirmed. Your 15-minute session is active.");
  }else{
   $("loadingText").textContent=d.message||"El pago no aparece como completado.";
  }
 }catch(e){$("loadingText").textContent=e.message}
};
const flight=async()=>{
 if(!requirePaid())return;
 const origin=$("origin").value.trim().toUpperCase(),destination=$("destination").value.trim().toUpperCase(),departure_date=$("departureDate").value,passengers=Math.max(1,Number($("passengers").value||1));
 if(!origin||!destination||!departure_date){msg("flightResult","Completa origen, destino y fecha.");return}
 try{
  const d=await api("/api/v1/flight/search-external",{method:"POST",body:{origin,destination,departure_date,passengers,language:APP.lang}});
  $("flightResult").innerHTML=renderObject(d);
 }catch(e){msg("flightResult",e.message)}
};
const item=async()=>{
 if(!requirePaid())return;
 const itemName=$("itemName").value.trim(),description=$("itemDescription").value.trim(),quantity=Math.max(1,Number($("itemQty").value||1));
 if(!itemName){msg("itemResult",APP.lang==="es"?"Escribe el artículo que quieres consultar.":"Enter the item you want to check.");return}
 try{
  const d=await api("/api/v1/consultar-articulo",{method:"POST",body:{item:itemName,description,quantity,language:APP.lang}});
  $("itemResult").innerHTML=renderObject(d);
 }catch(e){msg("itemResult",e.message)}
};
const teach=async()=>{
 if(!requirePaid())return;
 const term=$("term").value.trim();
 if(!term){msg("teachResult",APP.lang==="es"?"Escribe un término.":"Enter a term.");return}
 try{
  const d=await api("/api/v1/item/teach",{method:"POST",body:{term,language:APP.lang}});
  $("teachResult").innerHTML=renderObject(d);
 }catch(e){msg("teachResult",e.message)}
};
const guide=async()=>{
 if(!requirePaid())return;
 try{$("guideResult").innerHTML=renderObject(await api("/api/v1/guide",{method:"POST",body:{language:APP.lang}}))}catch(e){msg("guideResult",e.message)}
};
const cuba=async()=>{
 if(!requirePaid())return;
 try{$("cubaResult").innerHTML=renderObject(await api(`/api/v1/cuba/guide?language=${encodeURIComponent(APP.lang)}`))}catch(e){msg("cubaResult",e.message)}
};
const sources=async()=>{
 try{
  const d=await api("/api/v1/official");
  $("sourcesResult").innerHTML=renderSources(d.sources||[]);
 }catch(e){msg("sourcesResult",e.message)}
};
const legal=async()=>{
 try{
  const d=await api(`/api/v1/legal?language=${encodeURIComponent(APP.lang)}`);
  $("legalResult").innerHTML=`<article><h3>${esc(d.app_name||APP.name)}</h3><p>${esc(d.notice||"")}</p><p>${esc(d.short_notice||"")}</p><p>${esc(d.source_notice||"")}</p></article>`;
 }catch(e){msg("legalResult",e.message)}
};
const renderSources=a=>a.map(x=>`<article class="source"><h3>${esc(x.name)}</h3><p>${esc(x.description||"")}</p>${x.url?`<a href="${esc(x.url)}" target="_blank" rel="noopener noreferrer">Abrir fuente oficial</a>`:""}</article>`).join("")||"<p>No hay fuentes disponibles.</p>";
const renderObject=o=>{
 if(o==null)return"<p>Sin información.</p>";
 if(Array.isArray(o))return o.map(renderObject).join("");
 if(typeof o!=="object")return`<p>${esc(o)}</p>`;
 let h="";
 if(o.title)h+=`<h3>${esc(o.title)}</h3>`;
 if(o.message)h+=`<p>${esc(o.message)}</p>`;
 if(o.next_action)h+=`<div class="next"><b>${APP.lang==="es"?"Siguiente acción":"Next action"}:</b> ${esc(o.next_action)}</div>`;
 if(o.steps&&Array.isArray(o.steps))h+=`<ol>${o.steps.map(x=>`<li>${esc(typeof x==="object"?JSON.stringify(x):x)}</li>`).join("")}</ol>`;
 if(o.sources&&Array.isArray(o.sources))h+=renderSources(o.sources);
 if(o.official_sources&&Array.isArray(o.official_sources))h+=renderSources(o.official_sources);
 if(o.explanation)h+=`<p>${esc(o.explanation)}</p>`;
 if(o.example)h+=`<p><b>Ejemplo:</b> ${esc(o.example)}</p>`;
 if(!h){
  h="<dl>";
  Object.entries(o).forEach(([k,v])=>{if(v!==null&&v!==undefined&&typeof v!=="object")h+=`<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`});
  h+="</dl>";
 }
 return h;
};
const adminLogin=async()=>{
 try{
  const d=await api("/api/v1/admin/login",{method:"POST",body:{username:$("adminUser").value,password:$("adminPass").value}});
  if(!d.success)throw new Error(d.message||"No se pudo iniciar sesión.");
  APP.adminToken=d.token;localStorage.setItem("cuba_admin_token",APP.adminToken);msg("adminMsg","Sesión administrativa activa.",true);
 }catch(e){msg("adminMsg",e.message)}
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
}));
$("startBtn").onclick=()=>active()?show("flight"):show("payment");
$("payBtn").onclick=payment;
$("flightBtn").onclick=flight;
$("itemBtn").onclick=item;
$("teachBtn").onclick=teach;
$("adminLoginBtn").onclick=adminLogin;
$("langBtn").onclick=()=>{APP.lang=APP.lang==="es"?"en":"es";localStorage.setItem("cuba_lang",APP.lang);renderLang();updateStatus()};
$("adminBtn").onclick=()=>show("admin");
window.addEventListener("load",async()=>{await init();await verifyPayment()});
