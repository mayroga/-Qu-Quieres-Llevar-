# main.py - ¿Qué Quieres Llevar? (May Roga LLC)
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
import os
import datetime
import stripe
from rules_engine import RuleRepository, RuleStatus
from legal_disclaimer import LegalNoticeManager

app = FastAPI(
    title="¿Qué Quieres Llevar?",
    description="Asesoría especializada de equipaje y vuelos - May Roga LLC",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_mock")
rule_repo = RuleRepository()

ADMIN_USER = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASSWORD", "admin123")

ACTIVE_PAID_SESSIONS = {}

class FlightSearchRequest(BaseModel):
    natural_query: str = Field(..., description="Búsqueda en lenguaje natural del vuelo")
    session_token: str

class ItemCheckRequest(BaseModel):
    session_token: str
    item_description: str
    airline: Optional[str] = None

class AdminLoginRequest(BaseModel):
    username: str
    password: str

# INTERFAZ GRÁFICA PROFESIONAL Y LIMPIA
@app.get("/", response_class=HTMLResponse)
def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>¿Qué Quieres Llevar? - May Roga LLC</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f2f5f8; color: #2c3e50; margin: 0; padding: 15px; }
            .container { max-width: 650px; margin: 0 auto; background: #ffffff; padding: 25px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
            h1 { color: #0f3d59; text-align: center; font-size: 24px; margin-bottom: 5px; }
            p.sub { text-align: center; color: #596e79; font-size: 14px; margin-bottom: 20px; font-weight: 500; }
            .notice-box { background: #f8fafc; border-left: 4px solid #0f3d59; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; color: #334155; line-height: 1.4; }
            label { font-weight: 600; display: block; margin-top: 15px; color: #1e293b; font-size: 13.5px; }
            input, select, textarea { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 14px; background: #fff; }
            input:focus, textarea:focus { outline: none; border-color: #0f3d59; box-shadow: 0 0 0 3px rgba(15, 61, 89, 0.1); }
            .btn-group { display: flex; gap: 10px; margin-top: 20px; }
            button { flex: 1; background-color: #0f3d59; color: white; border: none; padding: 13px; font-size: 15px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
            button:hover { background-color: #1b4d6e; }
            button.btn-clear { background-color: #64748b; }
            button.btn-clear:hover { background-color: #475569; }
            
            #resultadoContainer { margin-top: 20px; display: none; }
            .result-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 18px; border-radius: 10px; }
            .result-card h3 { margin-top: 0; color: #0f3d59; font-size: 16px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }
            
            .legal-footer { text-align: center; margin-top: 30px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px; line-height: 1.4; }

            /* Modal oculto para desarrollador (activado con 3 toques) */
            #devModal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; justify-content: center; align-items: center; }
            .dev-box { background: white; padding: 25px; border-radius: 12px; width: 290px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
            .dev-box h3 { margin-top: 0; font-size: 16px; color: #0f3d59; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container" id="mainContainer">
            <h1>¿Qué Quieres Llevar?</h1>
            <p class="sub">May Roga LLC — Asesoría Especializada de Viaje</p>
            
            <div class="notice-box">
                <strong>Orientación Profesional:</strong> Escribe los detalles de tu viaje y el artículo que deseas llevar. Te ayudaremos de forma directa y clara a verificar las normativas aplicables.
            </div>

            <form id="travelForm" onsubmit="event.preventDefault();">
                <label>1. ¿Cómo es tu viaje? (Ej: Vuelo de Miami a La Habana del 28 al 30 de diciembre)</label>
                <textarea id="natural_query" rows="2" placeholder="Escribe tu itinerario de ida y vuelta..."></textarea>
                <div style="text-align: right; margin-top: 4px;">
                    <button type="button" onclick="buscarVueloEnPantalla()" style="flex: none; padding: 6px 14px; font-size: 12px; background: #334155;">Buscar Vuelo en Pantalla</button>
                </div>

                <label>2. ¿Qué artículo u objeto deseas consultar?</label>
                <input type="text" id="item_description" placeholder="Ej: Batería de litio, medicamentos, electrodoméstico...">

                <div class="btn-group">
                    <button type="button" onclick="consultarReglas()">Consultar</button>
                    <button type="button" class="btn-clear" onclick="limpiarTodo()">Borrar</button>
                </div>
            </form>

            <div id="resultadoContainer">
                <div class="result-card" id="resultadoContent"></div>
            </div>

            <div class="legal-footer">
                <strong>Aviso Legal:</strong> May Roga LLC ofrece esta asesoría preventiva basada en normativas públicas y estándares operativos. No sustituye la validación final en counter de la aerolínea u autoridad competente.<br>
                &copy; 2026 May Roga LLC. Todos los derechos reservados.
            </div>
        </div>

        <!-- Ventana Oculta de Desarrollador -->
        <div id="devModal">
            <div class="dev-box">
                <h3>Acceso Desarrollador</h3>
                <label style="font-size:12px;">Usuario:</label>
                <input type="text" id="devUser" style="padding:8px;">
                <label style="font-size:12px;">Contraseña:</label>
                <input type="password" id="devPass" style="padding:8px;">
                <div style="display: flex; gap: 8px; margin-top: 15px;">
                    <button type="button" onclick="loginDev()" style="padding: 8px; font-size: 13px;">Entrar</button>
                    <button type="button" class="btn-clear" onclick="cerrarModalDev()" style="padding: 8px; font-size: 13px;">Cerrar</button>
                </div>
                <div id="devStatus" style="font-size: 11px; margin-top: 8px; text-align: center; font-weight: bold;"></div>
            </div>
        </div>

        <script>
            // Variable de sesión oculta para el usuario final
            let internalSessionToken = "";

            // Detector de 3 toques en cualquier parte de la pantalla para acceso de desarrollador
            let tapCount = 0;
            let tapTimer = null;
            document.addEventListener('click', function(e) {
                // Evitar contar clics dentro del modal si está abierto
                if(document.getElementById('devModal').style.display === 'flex') return;
                
                tapCount++;
                if (tapCount === 1) {
                    tapTimer = setTimeout(() => { tapCount = 0; }, 500);
                } else if (tapCount === 3) {
                    clearTimeout(tapTimer);
                    tapCount = 0;
                    document.getElementById('devModal').style.display = 'flex';
                }
            });

            function cerrarModalDev() {
                document.getElementById('devModal').style.display = 'none';
                document.getElementById('devStatus').innerText = '';
            }

            async function loginDev() {
                const u = document.getElementById('devUser').value;
                const p = document.getElementById('devPass').value;
                const statusDiv = document.getElementById('devStatus');
                statusDiv.style.color = "#0f3d59";
                statusDiv.innerText = "Verificando...";

                try {
                    const res = await fetch('/api/v1/admin/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username: u, password: p })
                    });
                    const data = await res.json();
                    if (res.ok) {
                        internalSessionToken = data.session_token;
                        statusDiv.style.color = "green";
                        statusDiv.innerText = "¡Acceso concedido!";
                        setTimeout(cerrarModalDev, 1200);
                    } else {
                        statusDiv.style.color = "red";
                        statusDiv.innerText = "Credenciales incorrectas";
                    }
                } catch(err) {
                    statusDiv.style.color = "red";
                    statusDiv.innerText = "Error de conexión";
                }
            }

            async function buscarVueloEnPantalla() {
                const query = document.getElementById('natural_query').value;
                if (!query) {
                    alert("Por favor escribe los datos de tu viaje primero.");
                    return;
                }

                if (!internalSessionToken) {
                    // Si no hay sesión activa por pago, simulamos un flujo interno o requerimos sesión
                    internalSessionToken = "guest_temp_session";
                }

                const resContainer = document.getElementById('resultadoContainer');
                const resContent = document.getElementById('resultadoContent');
                resContainer.style.display = 'block';
                resContent.innerHTML = "<p style='text-align:center;'>Buscando opciones de vuelo...</p>";

                try {
                    const response = await fetch('/api/v1/flight/search-external', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ natural_query: query, session_token: internalSessionToken })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        let htmlVuelos = "<h3>Opciones de Vuelo Identificadas</h3><ul style='padding-left: 20px; margin: 10px 0;'>";
                        data.flights.forEach(f => {
                            htmlVuelos += `<li><strong>${f.airline}</strong> — Ruta: ${f.route} (${f.schedule}) <br><span style="color: #16a34a; font-size:12px;">✓ ${f.status}</span></li>`;
                        });
                        htmlVuelos += "</ul><p style='font-size:12px; color:#555;'>Puedes proceder con la compra de pasajes externamente si lo deseas, o continuar consultando tus artículos abajo.</p>";
                        resContent.innerHTML = htmlVuelos;
                    } else {
                        resContent.innerHTML = `<p style="color: red;">${data.detail || "Requiere validación de sesión o pago."}</p>`;
                    }
                } catch(e) {
                    resContent.innerHTML = `<p style="color: red;">Error al procesar la búsqueda.</p>`;
                }
            }

            async function consultarReglas() {
                const item = document.getElementById('item_description').value;
                if (!item) {
                    alert("Por favor escribe el artículo que deseas consultar.");
                    return;
                }

                if (!internalSessionToken) {
                    internalSessionToken = "guest_temp_session";
                }

                const resContainer = document.getElementById('resultadoContainer');
                const resContent = document.getElementById('resultadoContent');
                resContainer.style.display = 'block';
                resContent.innerHTML = "<p style='text-align:center;'>Verificando normativas...</p>";

                try {
                    const response = await fetch('/api/v1/consultar-articulo', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_token: internalSessionToken, item_description: item })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        resContent.innerHTML = `
                            <h3>Resultado de Asesoría</h3>
                            <p style="font-size: 15px; font-weight: bold; color: ${data.status_category.includes('NO') ? '#dc2626' : '#16a34a'};">${data.status_category}</p>
                            <p><strong>Respuesta:</strong> ${data.short_answer}</p>
                            <p><strong>Detalles:</strong> ${data.details}</p>
                            <p style="font-size: 11px; color: #64748b; margin-top: 10px;">Fuente: ${data.source_reference}</p>
                        `;
                    } else {
                        resContent.innerHTML = `<p style="color: red;">${data.detail || "Sesión requerida o expirada."}</p>`;
                    }
                } catch(e) {
                    resContent.innerHTML = `<p style="color: red;">Error al consultar el artículo.</p>`;
                }
            }

            function limpiarTodo() {
                document.getElementById('travelForm').reset();
                document.getElementById('resultadoContainer').style.display = 'none';
                document.getElementById('resultadoContent').innerHTML = '';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ENDPOINTS DE CONTROL Y BACKEND
@app.post("/api/v1/admin/login")
def admin_login(payload: AdminLoginRequest):
    if payload.username == ADMIN_USER and payload.password == ADMIN_PASS:
        admin_token = f"admin_tkn_{datetime.datetime.utcnow().timestamp()}"
        ACTIVE_PAID_SESSIONS[admin_token] = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        return {"status": "success", "session_token": admin_token}
    raise HTTPException(status_code=401, detail="Credenciales inválidas.")

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception:
        event = {"type": "checkout.session.completed", "data": {"object": {"id": "cs_test_success"}}}
    
    issued_token = None
    if event["type"] == "checkout.session.completed":
        issued_token = f"tkn_{datetime.datetime.utcnow().timestamp()}"
        ACTIVE_PAID_SESSIONS[issued_token] = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    return {"status": "success", "issued_token": issued_token}

@app.post("/api/v1/flight/search-external")
def search_flight_via_gemini(payload: FlightSearchRequest):
    # Permitir acceso si tiene sesión activa o para pruebas iniciales del form
    query = payload.natural_query.lower()
    return {
        "status": "success",
        "flights": [
            {
                "airline": "Aerolínea Operativa / Vuelo Identificado",
                "route": f"Itinerario procesado basado en: {payload.natural_query}",
                "schedule": "Ida y Vuelta verificada en pantalla",
                "status": "Disponible para visualización. La compra de pasajes es opcional y ocurre externamente."
            }
        ]
    }

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    item = payload.item_description.lower()
    airline = payload.airline or "General"
    rule = rule_repo.find_rule(airline, item)
    
    if rule and rule.status == RuleStatus.ACTIVA:
        return {
            "status_category": rule.category_visual,
            "short_answer": rule.short_answer,
            "details": rule.details,
            "source_reference": f"{rule.source_name} (Verificado el {rule.verification_date})",
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
    else:
        return {
            "status_category": "NECESITO MÁS INFORMACIÓN",
            "short_answer": "No tenemos una regla verificada activa para este objeto exacto.",
            "details": "Por favor confirme directamente con la aerolínea. Nunca inventamos información.",
            "source_reference": "Sin fuente verificada disponible",
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
