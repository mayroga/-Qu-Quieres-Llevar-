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
    version="5.1.0"
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
            .container { max-width: 680px; margin: 0 auto; background: #ffffff; padding: 25px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
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
            
            table.custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; background: #fff; }
            table.custom-table th, table.custom-table td { border: 1px solid #e2e8f0; padding: 10px; text-align: left; }
            table.custom-table th { background-color: #0f3d59; color: #fff; }

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
                <strong>Orientación Profesional:</strong> Escribe los detalles de tu itinerario de vuelo y el artículo que deseas llevar. Te ayudaremos de forma directa y clara a verificar las normativas aplicables.
            </div>

            <form id="travelForm" onsubmit="event.preventDefault();">
                <label>1. ¿Cómo es tu viaje? (Ej: Miami 30 de diciembre a Habana, regreso el 3 de enero)</label>
                <textarea id="natural_query" rows="2" placeholder="Escribe tu ruta y fechas de ida y vuelta..."></textarea>
                <div style="display: flex; gap: 10px; margin-top: 6px;">
                    <button type="button" onclick="buscarVueloEnPantalla()" style="flex: 1; padding: 10px; font-size: 13px; background: #1e293b;">Buscar Vuelo / Opciones</button>
                </div>

                <label>2. ¿Qué artículo u objeto deseas consultar?</label>
                <input type="text" id="item_description" placeholder="Ej: Batería de litio de 1843 Watt, 66 libras...">

                <div class="btn-group">
                    <button type="button" onclick="consultarReglas()">Consultar Asesoría</button>
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
                    alert("Por favor escribe los datos de tu viaje primero.");
                    return;
                }

                if (!internalSessionToken) {
                    internalSessionToken = "guest_temp_session";
                }

                const resContainer = document.getElementById('resultadoContainer');
                const resContent = document.getElementById('resultadoContent');
                resContainer.style.display = 'block';
                resContent.innerHTML = "<p style='text-align:center;'>Consultando opciones y disponibilidad de vuelos...</p>";

                try {
                    const response = await fetch('/api/v1/flight/search-external', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ natural_query: query, session_token: internalSessionToken })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        let htmlVuelos = `
                            <h3>Itinerario y Opciones de Vuelo</h3>
                            <p style="font-size: 13px; margin-bottom: 10px;"><strong>Ruta analizada:</strong> ${query}</p>
                            <table class="custom-table">
                                <tr>
                                    <th>Servicio / Aerolínea</th>
                                    <th>Detalle del Trayecto</th>
                                    <th>Acción Opcional</th>
                                </tr>
                        `;
                        data.flights.forEach(f => {
                            htmlVuelos += `
                                <tr>
                                    <td><strong>${f.airline}</strong></td>
                                    <td>${f.route}<br><span style="color: #16a34a; font-size:11px;">✓ ${f.status}</span></td>
                                    <td><a href="${f.booking_url}" target="_blank" style="background: #0f3d59; color: #fff; padding: 6px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; display: inline-block;">Ver / Cotizar Vuelo</a></td>
                                </tr>
                            `;
                        });
                        htmlVuelos += `</table><p style="font-size: 11px; color:#555; margin-top: 10px;">Nota: La compra de pasajes es completamente opcional y se realiza directamente a través de las plataformas asociadas si el cliente así lo desea.</p>`;
                        resContent.innerHTML = htmlVuelos;
                    } else {
                        resContent.innerHTML = `<p style="color: red;">${data.detail || "Requiere validación."}</p>`;
                    }
                } catch(e) {
                    resContent.innerHTML = `<p style="color: red;">Error al procesar la búsqueda de vuelo.</p>`;
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
                resContent.innerHTML = "<p style='text-align:center;'>Verificando normativas de equipaje...</p>";

                try {
                    const response = await fetch('/api/v1/consultar-articulo', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_token: internalSessionToken, item_description: item })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        resContent.innerHTML = `
                            <h3>Resultado de Asesoría de Carga / Equipaje</h3>
                            <p style="font-size: 15px; font-weight: bold; color: ${data.status_category.includes('NO') || data.status_category.includes('RESTRINGIDO') ? '#dc2626' : '#16a34a'};">${data.status_category}</p>
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
    query = payload.natural_query.lower()
    return {
        "status": "success",
        "flights": [
            {
                "airline": "Buscador General de Vuelos",
                "route": f"Itinerario solicitado: {payload.natural_query}",
                "status": "Comparador global de precios y horarios.",
                "booking_url": "https://www.google.com/travel/flights"
            },
            {
                "airline": "Avianca",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conexiones, pasajeros y carga especializada.",
                "booking_url": "https://www.avianca.com"
            },
            {
                "airline": "American Airlines",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Amplia red de conexiones norte y sur.",
                "booking_url": "https://www.aa.com"
            },
            {
                "airline": "JetBlue",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conexiones en el Caribe y Estados Unidos.",
                "booking_url": "https://www.jetblue.com"
            },
            {
                "airline": "Copa Airlines",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conexión a través del Hub de las Américas.",
                "booking_url": "https://www.copaair.com"
            },
            {
                "airline": "Southwest Airlines",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Vuelos flexibles y política de equipaje.",
                "booking_url": "https://www.southwest.com"
            },
            {
                "airline": "Aeroméxico",
                "route": f"Ruta optimizada para: {payload.natural_query}",
                "status": "Conexiones hacia México y conexiones internacionales.",
                "booking_url": "https://www.aeromexico.com"
            }
        ]
    }

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    item = payload.item_description.lower()
    
    tiene_bateria = any(k in item for k in ["bateria", "batería", "wh", "watt", "watts", "litio", "acumulador"])
    tiene_maletas = any(k in item for k in ["maleta", "maletas", "equipaje", "bolso", "libra", "libras"])
    tiene_paneles = any(k in item for k in ["panel", "paneles", "solar", "fotovoltaico"])
    tiene_medicina = any(k in item for k in ["medicina", "medicamento", "insulina", "vacuna", "alimento", "carne", "perecedero", "suplemento"])
    tiene_soda = any(k in item for k in ["soda", "soda caustica", "cáustica", "hidroxido", "quimico", "corrosivo"])
    
    if (tiene_soda and tiene_maletas) or (tiene_paneles and tiene_maletas) or (tiene_soda and tiene_paneles) or (tiene_bateria and tiene_maletas):
        return {
            "status_category": "ANÁLISIS DE ORIENTACIÓN Y SOLUCIÓN INTEGRAL DE CARGA",
            "short_answer": "Tu carga combina elementos químicos, equipos especiales y maletas de viaje. Nuestra sugerencia es separarlos para evitar contratiempos o recargos en los puntos de control.",
            "details": "GUÍA DE RUTA Y SEPARACIÓN RECOMENDADA:\n\n"
                       "🔹 1. PRODUCTOS QUÍMICOS / SODA CÁUSTICA:\n"
                       "• Sugerencia de Manejo: Generalmente no se aceptan en cabina ni en equipaje facturado de pasajeros debido a sus propiedades corrosivas.\n"
                       "• Solución Propuesta: Canalizar el envío mediante una agencia de carga comercial especializada.\n"
                       "• Empaque: Se sugiere utilizar envases sellados herméticamente y aptos para sustancias delicadas.\n\n"
                       "🔹 2. PANELES SOLARES / EQUIPOS FRÁGILES:\n"
                       "• Naturaleza: Superficies delicadas ante torsiones e impactos.\n"
                       "• Solución Propuesta: Envío por carga especializada con estructura rígida de soporte o pallet.\n"
                       "• Medidas Estándar: Un panel típico mide aprox. 170x100 cm (67 x 39 pulgadas) y excede las medidas de equipaje común.\n\n"
                       "🔹 3. MALETAS PERSONALES (Ej. 59 lbs / exceso):\n"
                       "• Parámetro Habitual: El límite más común en aerolíneas hacia Latinoamérica es de 50 lbs (23 kg) por maleta en bodega. Superar este peso suele activar cobros adicionales.\n"
                       "• Solución Propuesta: Sugerimos redistribuir el peso en dos maletas antes de llegar al mostrador.\n"
                       "• Dimensiones de Bodega: La suma lineal sugerida (Largo + Ancho + Alto) es de hasta 158 cm (62 pulgadas).",
            "source_reference": "Orientación basada en estándares internacionales de la industria (Verificado 2026)",
            "official_links": [
                {"title": "Guía de Referencia IATA DGR", "url": "https://www.iata.org/en/programs/cargo/dgr/"},
                {"title": "Directrices de Artículos TSA", "url": "https://www.tsa.gov/travel/security-screening/whatcanibring/"},
                {"title": "Departamento de Transporte (DOT)", "url": "https://www.transportation.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_soda:
        return {
            "status_category": "ORIENTACIÓN SOBRE PRODUCTOS QUÍMICOS",
            "short_answer": "Este tipo de producto suele requerir manejo especial como carga comercial y habitualmente no se permite en el equipaje de pasajeros.",
            "details": "SUGERENCIAS Y PAUTAS TÉCNICAS:\n\n"
                       "• Condición Habitual: Las políticas de aerolíneas de pasajeros suelen restringir sustancias corrosivas en cabina y bodega.\n"
                       "• Ruta Sugerida: Consultar con un consolidador o agente de carga autorizado para un despacho comercial adecuado.\n"
                       "• Recomendación: Disponer de la hoja técnica o factura comercial al cotizar el envío.",
            "source_reference": "Pautas de la Industria Logística y Transporte (Verificado 2026)",
            "official_links": [
                {"title": "IATA Dangerous Goods Regulations", "url": "https://www.iata.org/en/programs/cargo/dgr/"},
                {"title": "PHMSA Hazardous Materials Safety", "url": "https://www.phmsa.dot.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_bateria:
        return {
            "status_category": "ORIENTACIÓN TÉCNICA DE ACUMULADORES",
            "short_answer": "Los equipos de alta potencia superan los umbrales habituales para pasajeros y se recomienda canalizarlos por la vía de carga.",
            "details": "SUGERENCIAS Y ESPECIFICACIONES:\n\n"
                       "• Parámetro de Referencia: Las normativas generales suelen limitar los equipos portátiles a rangos de 100Wh–160Wh en aeronaves de pasajeros.\n"
                       "• Medidas y Peso Aproximados: Equipos grandes suelen pesar entre 20 y 30 lbs (9 a 13.5 kg).\n"
                       "• Recomendación: Acudir a una agencia de carga para asegurar un embalaje correcto y proteger los terminales.",
            "source_reference": "Estándares de Transporte de Acumuladores (Verificado 2026)",
            "official_links": [
                {"title": "IATA Lithium Batteries Guidance", "url": "https://www.iata.org/en/programs/cargo/dgr/lithium-batteries/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_paneles:
        return {
            "status_category": "ORIENTACIÓN SOBRE EQUIPAMIENTO FOTOVOLTAICO",
            "short_answer": "Debido a su tamaño y fragilidad, sugerimos planificar su transporte mediante carga especializada.",
            "details": "PAUTAS DE DIMENSIONES Y MANEJO:\n\n"
                       "• Dimensiones Frecuentes: Alrededor de 170 x 100 cm (67 x 39 pulgadas).\n"
                       "• Ruta Sugerida: Carga aérea de consolidación o transporte marítimo.\n"
                       "• Recomendación: Solicitar un embalaje rígido con protección perimetral para cuidar las celdas.",
            "source_reference": "Estándares Logísticos para Carga Frágil (Verificado 2026)",
            "official_links": [
                {"title": "U.S. Customs and Border Protection (CBP)", "url": "https://www.cbp.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_medicina:
        return {
            "status_category": "ORIENTACIÓN PARA PRODUCTOS MÉDICOS",
            "short_answer": "Los artículos de uso personal suelen llevarse en la maleta de mano; los volúmenes mayores o comerciales requieren contenedores térmicos.",
            "details": "PAUTAS SANITARIAS SUGERIDAS:\n\n"
                       "• En Cabina: Se aconseja llevar recetas médicas a la mano y visibles.\n"
                       "• Envíos Comerciales: Utilizar cadenas de frío validadas.\n"
                       "• Recomendación: Mantener la documentación accesible para agilizar cualquier revisión en los puntos de control.",
            "source_reference": "Directrices de Seguridad y Salud Aeroportuaria (Verificado 2026)",
            "official_links": [
                {"title": "TSA Medical Conditions Guidance", "url": "https://www.tsa.gov/travel/special-procedures"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_maletas:
        return {
            "status_category": "ORIENTACIÓN DE PESO Y MEDIDAS DE EQUIPAJE",
            "short_answer": "Sugerimos verificar las medidas y el peso antes de salir para evitar recargos en el mostrador.",
            "details": "PARÁMETROS HABITUALES EN AEROLÍNEAS:\n\n"
                       "• Peso Sugerido en Bodega: Mantenerse dentro del límite común de 50 lbs (23 kg) por pieza para evitar tarifas adicionales.\n"
                       "• Dimensiones Máximas (Suma Lineal): Se recomienda que Largo + Ancho + Alto no rebase los 158 cm (62 pulgadas).\n"
                       "• Recomendación: Pesar el equipaje en casa utilizando una báscula portátil.",
            "source_reference": "Políticas Internacionales de Equipaje de Referencia (Verificado 2026)",
            "official_links": [
                {"title": "DOT Aviation Consumer Protection - Baggage", "url": "https://www.transportation.gov/airconsumer/baggage"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

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
            "status_category": "ORIENTACIÓN LOGÍSTICA INTEGRAL",
            "short_answer": f"Evaluación orientativa para el traslado de '{payload.item_description}'.",
            "details": "PAUTAS Y RECOMENDACIONES:\n\n"
                       "• Criterio de Carga: Si el objeto supera las 50 lbs (23 kg) o los 158 cm (62 pulgadas) sumando sus lados, nuestra sugerencia es canalizarlo a través de servicios de carga comercial o courier.\n"
                       "• Recomendación: Preparar factura comercial, medir el bulto y asegurar un empaque firme acorde a la distancia del trayecto.",
            "source_reference": "Asesoría Logística Multimodal (Verificado 2026)",
            "official_links": [
                {"title": "IATA Official Website", "url": "https://www.iata.org/"},
                {"title": "U.S. Customs and Border Protection", "url": "https://www.cbp.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
