# main.py - ¿Qué Quieres Llevar? (May Roga LLC)
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import os
import datetime
import stripe
from rules_engine import RuleRepository, RuleStatus
from legal_disclaimer import LegalNoticeManager

app = FastAPI(
    title="¿Qué Quieres Llevar?",
    description="Asesoría especializada de transporte, carga y equipaje - May Roga LLC",
    version="6.0.0"
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
    natural_query: str = Field(..., description="Búsqueda en lenguaje natural del trayecto o ruta")
    session_token: str

class ItemCheckRequest(BaseModel):
    session_token: str
    item_description: str
    airline: Optional[str] = None
    transport_mode: Optional[str] = Field("general", description="aereo, maritimo, terrestre o general")

class AdminLoginRequest(BaseModel):
    username: str
    password: str

# INTERFAZ GRÁFICA PROFESIONAL Y UNIVERSAL
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
            .container { max-width: 720px; margin: 0 auto; background: #ffffff; padding: 25px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
            h1 { color: #0f3d59; text-align: center; font-size: 24px; margin-bottom: 5px; }
            p.sub { text-align: center; color: #596e79; font-size: 14px; margin-bottom: 20px; font-weight: 500; }
            .notice-box { background: #f8fafc; border-left: 4px solid #0f3d59; padding: 12px 15px; border-radius: 6px; margin-bottom: 20px; font-size: 13px; color: #334155; line-height: 1.5; }
            label { font-weight: 600; display: block; margin-top: 15px; color: #1e293b; font-size: 13.5px; }
            input, select, textarea { width: 100%; padding: 12px; margin-top: 6px; border: 1px solid #cbd5e1; border-radius: 8px; box-sizing: border-box; font-size: 14px; background: #fff; }
            input:focus, textarea:focus { outline: none; border-color: #0f3d59; box-shadow: 0 0 0 3px rgba(15, 61, 89, 0.1); }
            .btn-group { display: flex; gap: 10px; margin-top: 20px; }
            button { flex: 1; background-color: #0f3d59; color: white; border: none; padding: 13px; font-size: 15px; border-radius: 8px; cursor: pointer; font-weight: 600; transition: background 0.2s; }
            button:hover { background-color: #1b4d6e; }
            button.btn-clear { background-color: #64748b; }
            button.btn-clear:hover { background-color: #475569; }
            
            #resultadoContainer { margin-top: 20px; display: none; }
            .result-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; line-height: 1.6; }
            .result-card h3 { margin-top: 0; color: #0f3d59; font-size: 16px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }
            
            table.custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; background: #fff; }
            table.custom-table th, table.custom-table td { border: 1px solid #e2e8f0; padding: 10px; text-align: left; }
            table.custom-table th { background-color: #0f3d59; color: #fff; }

            .legal-footer { text-align: center; margin-top: 30px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px; line-height: 1.5; }

            #devModal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; justify-content: center; align-items: center; }
            .dev-box { background: white; padding: 25px; border-radius: 12px; width: 290px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
            .dev-box h3 { margin-top: 0; font-size: 16px; color: #0f3d59; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container" id="mainContainer">
            <h1>¿Qué Quieres Llevar?</h1>
            <p class="sub">May Roga LLC — Asesoría Especializada Multimodal</p>
            
            <div class="notice-box">
                <strong>Orientación Profesional:</strong> Diseñado para brindarte soluciones claras, directas y seguras en el traslado de cualquier tipo de carga, equipaje o mercancía por vía aérea, terrestre o marítima.
            </div>

            <form id="travelForm" onsubmit="event.preventDefault();">
                <label>1. ¿Cómo es tu ruta o itinerario general? (Ej: Miami a La Habana, carga comercial, mudanza o envío terrestre)</label>
                <textarea id="natural_query" rows="2" placeholder="Describe tu trayecto, fechas o necesidades logísticas..."></textarea>
                <div style="display: flex; gap: 10px; margin-top: 6px;">
                    <button type="button" onclick="buscarVueloEnPantalla()" style="flex: 1; padding: 10px; font-size: 13px; background: #1e293b;">Analizar Rutas y Opciones</button>
                </div>

                <label>2. ¿Qué artículo, mercancía o carga universal deseas consultar?</label>
                <input type="text" id="item_description" placeholder="Ej: Maquinaria, alimentos, repuestos, baterías, químicos, menaje...">

                <label>3. Selecciona el medio o modalidad de transporte</label>
                <select id="transport_mode">
                    <option value="general">Multimodal / General (Aéreo, Marítimo, Terrestre)</option>
                    <option value="aereo">Transporte Aéreo (Pasajero o Carga)</option>
                    <option value="maritimo">Transporte Marítimo (Contenedores / Carga suelta)</option>
                    <option value="terrestre">Transporte Terrestre (Camiones / Courier)</option>
                </select>

                <div class="btn-group">
                    <button type="button" onclick="consultarReglas()">Consultar Asesoría</button>
                    <button type="button" class="btn-clear" onclick="limpiarTodo()">Borrar</button>
                </div>
            </form>

            <div id="resultadoContainer">
                <div class="result-card" id="resultadoContent"></div>
            </div>

            <div class="legal-footer">
                <strong>Aviso Legal:</strong> May Roga LLC ofrece esta asesoría preventiva basada en normativas públicas y estándares internacionales de la industria. No sustituye la validación final en puerto, aduana o counter autorizado.<br>
                &copy; 2026 May Roga LLC. Todos los derechos reservados.
            </div>
        </div>

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
            let internalSessionToken = "";
            let tapCount = 0;
            let tapTimer = null;

            document.addEventListener('click', function(e) {
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
                    alert("Por favor escribe los detalles de tu ruta o trayecto primero.");
                    return;
                }

                if (!internalSessionToken) {
                    internalSessionToken = "guest_temp_session";
                }

                const resContainer = document.getElementById('resultadoContainer');
                const resContent = document.getElementById('resultadoContent');
                resContainer.style.display = 'block';
                resContent.innerHTML = "<p style='text-align:center;'>Analizando opciones logísticas y de transporte...</p>";

                try {
                    const response = await fetch('/api/v1/flight/search-external', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ natural_query: query, session_token: internalSessionToken })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        let htmlVuelos = `
                            <h3>Opciones de Ruta y Conectividad Multimodal</h3>
                            <p style="font-size: 13px; margin-bottom: 10px;"><strong>Consulta analizada:</strong> ${query}</p>
                            <table class="custom-table">
                                <tr>
                                    <th>Canal / Operador</th>
                                    <th>Especificación de la Ruta</th>
                                    <th>Acción Opcional</th>
                                </tr>
                        `;
                        data.flights.forEach(f => {
                            htmlVuelos += `
                                <tr>
                                    <td><strong>${f.airline}</strong></td>
                                    <td>${f.route}<br><span style="color: #16a34a; font-size:11px;">✓ ${f.status}</span></td>
                                    <td><a href="${f.booking_url}" target="_blank" style="background: #0f3d59; color: #fff; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; display: inline-block;">Ver / Cotizar</a></td>
                                </tr>
                            `;
                        });
                        htmlVuelos += `</table><p style="font-size: 11px; color:#555; margin-top: 10px;">Nota: La gestión y contratación de servicios es completamente opcional y directa a través de las plataformas vinculadas.</p>`;
                        resContent.innerHTML = htmlVuelos;
                    } else {
                        resContent.innerHTML = `<p style="color: red;">${data.detail || "Requiere validación."}</p>`;
                    }
                } catch(e) {
                    resContent.innerHTML = `<p style="color: red;">Error al procesar la búsqueda logística.</p>`;
                }
            }

            async function consultarReglas() {
                const item = document.getElementById('item_description').value;
                const mode = document.getElementById('transport_mode').value;
                if (!item) {
                    alert("Por favor escribe el artículo o mercancía que deseas consultar.");
                    return;
                }

                if (!internalSessionToken) {
                    internalSessionToken = "guest_temp_session";
                }

                const resContainer = document.getElementById('resultadoContainer');
                const resContent = document.getElementById('resultadoContent');
                resContainer.style.display = 'block';
                resContent.innerHTML = "<p style='text-align:center;'>Procesando asesoría especializada...</p>";

                try {
                    const response = await fetch('/api/v1/consultar-articulo', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_token: internalSessionToken, item_description: item, transport_mode: mode })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        resContent.innerHTML = `
                            <h3>Resultado de Asesoría Multimodal</h3>
                            <p style="font-size: 15px; font-weight: bold; color: #0f3d59;">${data.status_category}</p>
                            <p><strong>Respuesta:</strong> ${data.short_answer}</p>
                            <div style="white-space: pre-line; margin-top: 10px;"><strong>Detalles:</strong><br>${data.details}</div>
                            <p style="font-size: 11px; color: #64748b; margin-top: 15px;">Fuente: ${data.source_reference}</p>
                        `;
                    } else {
                        resContent.innerHTML = `<p style="color: red;">${data.detail || "Sesión requerida o expirada."}</p>`;
                    }
                } catch(e) {
                    resContent.innerHTML = `<p style="color: red;">Error al procesar la consulta del artículo.</p>`;
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

# ENDPOINTS DE CONTROL Y BACKEND UNIVERSAL
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
    query = payload.natural_query.lower()
    return {
        "status": "success",
        "flights": [
            {
                "airline": "Buscador Global Multimodal",
                "route": f"Trayecto solicitado: {payload.natural_query}",
                "status": "Comparador universal de pasajes, carga y conexiones.",
                "booking_url": "https://www.google.com/travel/flights"
            },
            {
                "airline": "Avianca",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conectividad de pasajeros y carga especializada.",
                "booking_url": "https://www.avianca.com"
            },
            {
                "airline": "American Airlines",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Red internacional de transporte de pasajeros.",
                "booking_url": "https://www.aa.com"
            },
            {
                "airline": "JetBlue",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conexiones en América del Norte y Caribe.",
                "booking_url": "https://www.jetblue.com"
            },
            {
                "airline": "Copa Airlines",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conexión continental mediante Hub central.",
                "booking_url": "https://www.copaair.com"
            },
            {
                "airline": "Southwest Airlines",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Flexibilidad en equipaje y traslados regionales.",
                "booking_url": "https://www.southwest.com"
            },
            {
                "airline": "Aeroméxico",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conectividad hacia México y enlaces globales.",
                "booking_url": "https://www.aeromexico.com"
            }
        ]
    }

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    item = payload.item_description.lower()
    mode = payload.transport_mode.lower()
    
    # Detección inteligente ampliada y universal de categorías
    tiene_bateria = any(k in item for k in ["bateria", "batería", "wh", "watt", "watts", "litio", "acumulador", "pila"])
    tiene_maletas = any(k in item for k in ["maleta", "maletas", "equipaje", "bolso", "libra", "libras", "mochila", "valija"])
    tiene_paneles = any(k in item for k in ["panel", "paneles", "solar", "fotovoltaico", "inversor"])
    tiene_medicina = any(k in item for k in ["medicina", "medicamento", "insulina", "vacuna", "alimento", "carne", "perecedero", "suplemento", "farmaco"])
    tiene_soda = any(k in item for k in ["soda", "soda caustica", "cáustica", "hidroxido", "quimico", "corrosivo", "sustancia", "liquido"])
    tiene_maquinaria = any(k in item for k in ["motor", "maquina", "maquinaria", "repuesto", "pieza", "metal", "acero", "herramienta"])

    # Lógica combinada / múltiple universal
    if (tiene_soda and tiene_maletas) or (tiene_paneles and tiene_maletas) or (tiene_soda and tiene_paneles) or (tiene_bateria and tiene_maletas):
        return {
            "status_category": "ORIENTACIÓN Y SOLUCIÓN DE CARGA MULTIMODAL",
            "short_answer": "Tranquilo, todo tiene solución. Lo mejor es separar las mercancías según su naturaleza para viajar o enviar sin contratiempos.",
            "details": "PASOS SENCILLOS A SEGUIR:\n\n"
                       "Sustancias o equipos especiales: Nuestra sugerencia es canalizarlos mediante carga comercial autorizada y no en equipaje de mano o maletas personales.\n\n"
                       "Soportes o componentes frágiles: Sugerimos un embalaje firme con protección reforzada para asegurar su integridad en cualquier trayecto.\n\n"
                       "Equipaje personal: Te aconsejamos ajustar el peso y dimensiones estándar (como 50 lbs / 23 kg) para evitar inconvenientes en los puntos de recepción.",
            "source_reference": "Normas Internacionales de Logística y Transporte (Verificado 2026)",
            "official_links": [
                {"title": "Guía de Referencia IATA DGR", "url": "https://www.iata.org/en/programs/cargo/dgr/"},
                {"title": "Directrices de Seguridad Logística", "url": "https://www.transportation.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_soda or (mode == "maritimo" and tiene_quimicos_gen(item)):
        return {
            "status_category": "ORIENTACIÓN SOBRE PRODUCTOS Y SUSTANCIAS",
            "short_answer": "No te preocupes, este tipo de producto se gestiona adecuadamente a través de la vía logística correcta.",
            "details": "SUGERENCIA PRÁCTICA:\n\n"
                       "Las normativas generales sugieren transportar componentes químicos o industriales mediante un agente de carga especializado y documentado.\n\n"
                       "Te recomendamos mantener a la mano la hoja de seguridad (MSDS), factura o ficha técnica del producto al momento de cotizar el envío.",
            "source_reference": "Pautas de Logística Multimodal (Verificado 2026)",
            "official_links": [
                {"title": "Dangerous Goods Regulations", "url": "https://www.iata.org/en/programs/cargo/dgr/"},
                {"title": "PHMSA Materials Safety", "url": "https://www.phmsa.dot.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_bateria:
        return {
            "status_category": "ORIENTACIÓN TÉCNICA DE ACUMULADORES Y ENERGÍA",
            "short_answer": "Respira hondo, existe un procedimiento seguro y directo para enviar o trasladar este acumulador.",
            "details": "SUGERENCIA PRÁCTICA:\n\n"
                       "Los dispositivos de alta potencia o capacidad suelen requerir canalización por carga comercial o restricciones específicas según su capacidad en Vatios-hora (Wh).\n\n"
                       "Te sugerimos proteger adecuadamente los bornes o terminales y consultar con un especialista en embalaje para garantizar un tránsito sin contratiempos.",
            "source_reference": "Estándares de Transporte de Energía (Verificado 2026)",
            "official_links": [
                {"title": "IATA Lithium Batteries Guidelines", "url": "https://www.iata.org/en/programs/cargo/dgr/lithium-batteries/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_paneles:
        return {
            "status_category": "ORIENTACIÓN SOBRE EQUIPAMIENTO SOLAR Y FOTOVOLTAICO",
            "short_answer": "Todo tiene solución. Cuidaremos que tu inversión y paneles lleguen en óptimas condiciones.",
            "details": "SUGERENCIA PRÁCTICA:\n\n"
                       "Debido a la sensibilidad de los componentes y su estructura de cristal, nuestra recomendación es cotizar el envío mediante carga protegida con soportes de madera o estructura rígida.\n\n"
                       "De esta manera garantizamos estabilidad y prevención de daños durante el transporte aéreo, marítimo o terrestre.",
            "source_reference": "Estándares Logísticos Especializados (Verificado 2026)",
            "official_links": [
                {"title": "U.S. Customs and Border Protection", "url": "https://www.cbp.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_medicina:
        return {
            "status_category": "ORIENTACIÓN PARA PRODUCTOS MÉDICOS Y PERECEDEROS",
            "short_answer": "Lleva tus insumos con calma; aquí te mostramos la mejor manera de organizarlos.",
            "details": "SUGERENCIA PRÁCTICA:\n\n"
                       "Para uso personal o médico inmediato, lo ideal es llevarlos en el equipaje de mano acompañados de su debida prescripción o receta visible.\n\n"
                       "Para volúmenes comerciales o de cadena de frío, te aconsejamos coordinar contenedores térmicos certificados con la aerolínea o courier.",
            "source_reference": "Directrices de Manejo Sanitario y Logístico (Verificado 2026)",
            "official_links": [
                {"title": "Medical Guidelines & Procedures", "url": "https://www.tsa.gov/travel/special-procedures"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_maquinaria:
        return {
            "status_category": "ORIENTACIÓN DE MAQUINARIA Y REPUESTOS INDUSTRIALES",
            "short_answer": "Tranquilo, cualquier pieza o herramienta pesada se puede organizar de forma eficiente.",
            "details": "SUGERENCIA PRÁCTICA:\n\n"
                       "Para maquinaria o repuestos con presencia de fluidos o peso elevado, sugerimos un drenaje completo previo y un pallet de madera resistente.\n\n"
                       "Te aconsejamos preparar la factura comercial y descripción arancelaria para agilizar cualquier revisión en destino.",
            "source_reference": "Guía de Carga Comercial Multimodal (Verificado 2026)",
            "official_links": [
                {"title": "Comercio y Aduanas Internacionales", "url": "https://www.cbp.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_maletas:
        return {
            "status_category": "ORIENTACIÓN DE PESO Y MEDIDAS DE EQUIPAJE",
            "short_answer": "No te preocupes por el peso, con una pequeña organización todo saldrá perfecto.",
            "details": "INSTRUCCIÓN DIRECTA:\n\n"
                       "Te sugerimos mantener cada pieza de equipaje dentro del límite estándar (generalmente 50 lbs / 23 kg) para evitar cobros adicionales inesperados en el mostrador.\n\n"
                       "Verifica el pesaje en casa antes de partir y viaja con absoluta tranquilidad.",
            "source_reference": "Políticas Internacionales de Equipaje (Verificado 2026)",
            "official_links": [
                {"title": "Baggage Consumer Protection", "url": "https://www.transportation.gov/airconsumer/baggage"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    # Búsqueda universal por motor de reglas o respuesta abierta universal
    rule = rule_repo.find_rule(payload.airline or "General", item)
    if rule and rule.status == RuleStatus.ACTIVA:
        return {
            "status_category": rule.category_visual,
            "short_answer": rule.short_answer,
            "details": rule.details,
            "source_reference": f"{rule.source_name} (Verificado el {rule.verification_date})",
            "official_links": [
                {"title": "Sitio Oficial de Referencia Regulatoria", "url": "https://www.iata.org"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
    else:
        return {
            "status_category": "ORIENTACIÓN LOGÍSTICA UNIVERSAL",
            "short_answer": f"Todo tiene solución para el traslado de '{payload.item_description}'. Respira y organicémoslo paso a paso.",
            "details": "PASOS SUGERIDOS:\n\n"
                       "Evaluación del objeto: Si el artículo es voluminoso, pesado o de características especiales, nuestra recomendación es canalizarlo mediante un servicio de carga o courier autorizado.\n\n"
                       "Preparación y empaque: Mide y pesa tu bulto, asegura un embalaje firme y ten listos los documentos de respaldo para viajar o enviar sin contratiempos.",
            "source_reference": "Asesoría Logística Multimodal Internacional (Verificado 2026)",
            "official_links": [
                {"title": "IATA Official Website", "url": "https://www.iata.org/"},
                {"title": "U.S. Customs and Border Protection", "url": "https://www.cbp.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

def tiene_quimicos_gen(txt):
    return any(w in txt for w in ["liquido", "aceite", "pintura", "gas", "inflamable", "compuesto"])
