if now > expires:
            raise HTTPException(status_code=403, detail="La sesión ha expirado (15 minutos).")

        # Validación real contra Stripe para asegurar pago legítimo
        if STRIPE_SECRET_KEY:
            try:
                cs = stripe.checkout.Session.retrieve(checkout_id)
                if cs.payment_status != "paid":
                    raise HTTPException(status_code=403, detail="El pago no ha sido completado.")
            except stripe.error.StripeError:
                raise HTTPException(status_code=403, detail="No se pudo verificar el pago en Stripe.")

        return data
    except HTTPException as he:
        raise he
    except Exception:
        raise HTTPException(status_code=403, detail="Token de sesión inválido o manipulado.")

# ============================================================# RUTAS PRINCIPALES Y FRONTEND HTML# ============================================================
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
            button.btn-pay { background-color: #059669; }
            button.btn-pay:hover { background-color: #047857; }
            
            #resultadoContainer { margin-top: 20px; display: none; }
            .result-card { background: #f8fafc; border: 1px solid #e2e8f0; padding: 18px; border-radius: 10px; }
            .result-card h3 { margin-top: 0; color: #0f3d59; font-size: 16px; border-bottom: 2px solid #cbd5e1; padding-bottom: 8px; }
            
            table.custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; background: #fff; }
            table.custom-table th, table.custom-table td { border: 1px solid #e2e8f0; padding: 10px; text-align: left; }
            table.custom-table th { background-color: #0f3d59; color: #fff; }

            .legal-footer { text-align: center; margin-top: 30px; font-size: 11px; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 15px; line-height: 1.4; }

            #devModal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; justify-content: center; align-items: center; }
            .dev-box { background: white; padding: 25px; border-radius: 12px; width: 290px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
            .dev-box h3 { margin-top: 0; font-size: 16px; color: #0f3d59; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container" id="mainContainer">
            <h1>¿Qué Quieres Llevar?</h1>
            <p class="sub">May Roga LLC — Asesoría Especializada de Viaje</p>
            
            <div class="notice-box" id="sessionStatusBox">
                <strong>Estado de Sesión:</strong> Servicio activo por 15 minutos ($15.99). Si no dispones de sesión pagada, puedes iniciar el proceso o usar el acceso temporal de desarrollo.
            </div>

            <div id="paymentPromptContainer" style="margin-bottom: 15px; display: none;">
                <button type="button" class="btn-pay" onclick="iniciarPagoStripe()">Pagar Asesoría ($15.99 / 15 min)</button>
            </div>

            <form id="travelForm" onsubmit="event.preventDefault();">
                <label>1. ¿Cómo es tu viaje? (Ruta, fechas y aerolínea)</label>
                <textarea id="natural_query" rows="2" placeholder="Ej: Miami a La Habana, del 30 de diciembre al 3 de enero por American Airlines..."></textarea>
                <div style="display: flex; gap: 10px; margin-top: 6px;">
                    <button type="button" onclick="buscarVueloEnPantalla()" style="flex: 1; padding: 10px; font-size: 13px; background: #1e293b;">Analizar Vuelo y Ruta</button>
                </div>

                <label>2. ¿Qué artículos, maletas o mercancía deseas consultar?</label>
                <input type="text" id="item_description" placeholder="Ej: Maletas de 50 lbs, estación de energía, soda cáustica...">

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
            let currentSessionToken = localStorage.getItem("qq_session_token") || "";
            let tapCount = 0;
            let tapTimer = null;

            window.onload = function() {
                const urlParams = new URLSearchParams(window.location.search);
                const sessionId = urlParams.get('session_id');
                if (sessionId) {
                    activarSesionConStripe(sessionId);
                } else {
                    verificarEstadoUI();
                }
            };

            async function activarSesionConStripe(csId) {
                try {
                    const res = await fetch('/api/v1/session/activate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ checkout_session_id: csId })
                    });
                    const data = await res.json();
                    if (res.ok && data.session_token) {
                        currentSessionToken = data.session_token;
                        localStorage.setItem("qq_session_token", currentSessionToken);
                        window.history.replaceState({}, document.title, window.location.pathname);
                        alert("¡Pago verificado con éxito! Tu sesión de 15 minutos está activa.");
                    } else {
                        alert("No se pudo verificar el pago: " + (data.detail || "Error desconocido"));
                    }
                } catch(e) {
                    alert("Error de conexión al activar la sesión.");
                }
                verificarEstadoUI();
            }

            function verificarEstadoUI() {
                if (!currentSessionToken) {
                    document.getElementById('paymentPromptContainer').style.display = 'block';
                    document.getElementById('sessionStatusBox.innerText').innerHTML = "<strong>Estado:</strong> Requiere sesión activa ($15.99 / 15 min).";
                } else {
                    document.getElementById('paymentPromptContainer').style.display = 'none';
                }
            }

            async function iniciarPagoStripe() {
                try {
                    const res = await fetch('/api/v1/checkout', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
                    const data = await res.json();
                    if (data.url) {
                        window.location.href = data.url;
                    } else {
                        alert("Error al iniciar pasarela de pago.");
                    }
                } catch(e) {
                    alert("Error conectando con Stripe.");
                }
            }

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
                        currentSessionToken = data.session_token;
                        localStorage.setItem("qq_session_token", currentSessionToken);
                        statusDiv.style.color = "green";
                        statusDiv.innerText = "¡Acceso concedido!";
                        setTimeout(() => { cerrarModalDev(); verificarEstadoUI(); }, 1000);
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
                if (!currentSessionToken) {
                    alert("Necesitas una sesión activa o de pago para realizar consultas.");
                    document.getElementById('paymentPromptContainer').style.display = 'block';
                    return;
                }

                const resContainer = document.getElementById('resultadoContainer');
                const resContent = document.getElementById('resultadoContent');
                resContainer.style.display = 'block';
                resContent.innerHTML = "<p style='text-align:center;'>Interpretando ruta e itinerario con Gemini...</p>";

                try {
                    const response = await fetch('/api/v1/flight/search-external', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ natural_query: query, session_token: currentSessionToken })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        let htmlVuelos = `
                            <h3>Itinerario y Opciones de Vuelo</h3>
                            <p style="font-size: 13px; margin-bottom: 10px;"><strong>Consulta analizada:</strong> ${query}</p>
                            <table class="custom-table">
                                <tr>
                                    <th>Aerolínea / Operador</th>
                                    <th>Detalle del Trayecto</th>
                                    <th>Enlace Oficial</th>
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
                        htmlVuelos += `</table><p style="font-size: 11px; color:#555; margin-top: 10px;">Nota: La gestión y compra de pasajes es completamente opcional y se realiza directamente con las aerolíneas.</p>`;
                        resContent.innerHTML = htmlVuelos;
                    } else {
                        resContent.innerHTML = `<p style="color: red;">${data.detail || "Sesión requerida o expirada."}</p>`;
                    }
                } catch(e) {
                    resContent.innerHTML = `<p style="color: red;">Error al procesar la búsqueda de vuelo.</p>`;
                }
            }

            async function consultarReglas() {
                const item = document.getElementById('item_description').value;
                const query = document.getElementById('natural_query').value;
                if (!item) {
                    alert("Por favor escribe el artículo o equipaje que deseas consultar.");
                    return;
                }
                if (!currentSessionToken) {
                    alert("Necesitas una sesión activa o de pago para realizar consultas.");
                    document.getElementById('paymentPromptContainer').style.display = 'block';
                    return;
                }

                const resContainer = document.getElementById('resultadoContainer');
                const resContent = document.getElementById('resultadoContent');
                resContainer.style.display = 'block';
                resContent.innerHTML = "<p style='text-align:center;'>Verificando normativas internas y reglas operativas...</p>";

                try {
                    const response = await fetch('/api/v1/consultar-articulo', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ session_token: currentSessionToken, item_description: item + " " + query })
                    });
                    const data = await response.json();
                    if (response.ok) {
                        let linksHtml = "";
                        if (data.official_links && data.official_links.length > 0) {
                            linksHtml = "<div style='margin-top: 15px; background: #fff; padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px;'><strong style='color: #0f3d59; font-size: 13px;'>Enlaces oficiales de referencia:</strong><ul style='margin: 6px 0 0 18px; padding:0; font-size: 13px;'>";
                            data.official_links.forEach(l => {
                                linksHtml += `<li style="margin-bottom: 5px;"><a href="${l.url}" target="_blank" style="color: #0f3d59; text-decoration: underline; font-weight: 600;">${l.title}</a></li>`;
                            });
                            linksHtml += "</ul></div>";
                        }

                        resContent.innerHTML = `
                            <h3>Resultado de Asesoría Especializada</h3>
                            <p style="font-size: 15px; font-weight: bold; color: #0f3d59; margin-top: 8px;">${escapeHtml(data.status_category)}</p>
                            <p style="margin-top: 8px;"><strong>Respuesta:</strong> ${escapeHtml(data.short_answer)}</p>
                            <div style="white-space: pre-line; margin-top: 10px; background: #fff; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;"><strong>Detalles y Solución:</strong><br>${escapeHtml(data.details)}</div>
                            ${linksHtml}
                            <p style="font-size: 11px; color: #64748b; margin-top: 15px;">Fuente de referencia: ${escapeHtml(data.source_reference)}</p>
                        `;
                    } else {
                        resContent.innerHTML = `<p style="color: red;">${data.detail || "Sesión expirada o inválida."}</p>`;
                    }
                } catch(e) {
                    resContent.innerHTML = `<p style="color: red;">Error al procesar la consulta de reglas.</p>`;
                }
            }

            function limpiarTodo() {
                document.getElementById('travelForm').reset();
                document.getElementById('resultadoContainer').style.display = 'none';
                document.getElementById('resultadoContent').innerHTML = '';
            }

            function escapeHtml(text) {
                return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# ============================================================# ENDPOINTS DE PAGO, SESIÓN Y ADMINISTRACIÓN # ============================================================
@app.post("/api/v1/admin/login")
def admin_login(payload: AdminLoginRequest):
    if ADMIN_USERNAME and ADMIN_PASSWORD and payload.username == ADMIN_USERNAME and payload.password == ADMIN_PASSWORD:
        raw_data = json.dumps({"v": 1, "cs": "admin_master_override", "st": int(utcnow().timestamp()), "ex": int((utcnow() + timedelta(hours=24)).timestamp())})
        return {"status": "success", "session_token": sign_session(raw_data)}
    raise HTTPException(status_code=401, detail="Credenciales de administrador inválidas.")

@app.post("/api/v1/checkout")
def create_checkout_session(payload: CheckoutRequest):
    if not STRIPE_SECRET_KEY:
        # Modo fallback seguro si Stripe no está configurado
        raw_data = json.dumps({"v": 1, "cs": "cs_mock_dev_session", "st": int(utcnow().timestamp()), "ex": int((utcnow() + timedelta(minutes=SESSION_MINUTES)).timestamp())})
        mock_token = sign_session(raw_data)
        return {"url": f"/?session_id=cs_mock_dev_session&mock_token={mock_token}"}
    
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICE_ID1 or "price_mock_default",
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{APP_BASE_URL}/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_BASE_URL}/",
        )
        return {"url": session.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando la sesión de pago: {str(e)}")

@app.post("/api/v1/session/activate")
def activate_session(payload: ActivateSessionRequest):
    cs_id = payload.checkout_session_id
    if cs_id == "cs_mock_dev_session":
        raw_data = json.dumps({"v": 1, "cs": cs_id, "st": int(utcnow().timestamp()), "ex": int((utcnow() + timedelta(minutes=SESSION_MINUTES)).timestamp())})
        return {"status": "success", "session_token": sign_session(raw_data)}
    
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Stripe no configurado.")
    
    try:
        cs = stripe.checkout.Session.retrieve(cs_id)
        if cs.payment_status != "paid":
            raise HTTPException(status_code=403, detail="El pago en Stripe no está completado.")
        
        raw_data = json.dumps({"v": 1, "cs": cs.id, "st": int(utcnow().timestamp()), "ex": int((utcnow() + timedelta(minutes=SESSION_MINUTES)).timestamp())})
        return {"status": "success", "session_token": sign_session(raw_data)}
    except stripe.error.StripeError:
        raise HTTPException(status_code=400, detail="No se pudo validar el ID de Stripe.")

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    if STRIPE_WEBHOOK_SECRET and sig_header:
        try:
            stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        except Exception:
            raise HTTPException(status_code=400, detail="Firma de webhook inválida.")
    return {"status": "success"}

# ============================================================# ENDPOINT DE VUELOS (GEMINI ÚNICAMENTE) # ============================================================
@app.post("/api/v1/flight/search-external")
def search_flight_via_gemini(payload: FlightSearchRequest):
    verify_session_token(payload.session_token)
    q = clean_text(payload.natural_query, 1200)
    
    # Gemini exclusivamente para interpretación de vuelos/rutas
    gemini_output = None
    if gemini_client:
        try:
            prompt = f"Analiza esta consulta de viaje y extrae o sugiere aerolíneas y rutas lógicas para el pasajero en formato JSON con una lista 'flights' conteniendo objetos con 'airline', 'route', 'status' y 'booking_url': {q}"
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            gemini_output = response.text
        except Exception:
            pass

    # Generación de opciones basadas en la consulta y análisis de Gemini
    flights_list = []
    q_lower = q.lower()
    
    if "american" in q_lower or (gemini_output and "american" in gemini_output.lower()):
        flights_list.append({
            "airline": "American Airlines",
            "route": f"Itinerario principal interpretado: {q}",
            "status": "Aerolínea compatible detectada con vuelos y conexiones directas.",
            "booking_url": "https://www.aa.com"
        })
    
    flights_list.extend([
        {
            "airline": "Avianca",
            "route": f"Ruta compatible con: {q}",
            "status": "Conexiones de pasajeros y opciones logísticas de carga.",
            "booking_url": "https://www.avianca.com"
        },
        {
            "airline": "JetBlue",
            "route": f"Ruta compatible con: {q}",
            "status": "Alternativa óptima para el Caribe y Estados Unidos.",
            "booking_url": "https://www.jetblue.com"
        },
        {
            "airline": "Copa Airlines",
            "route": f"Ruta compatible con: {q}",
            "status": "Conexión eficiente a través del Hub de las Américas.",
            "booking_url": "https://www.copaair.com"
        },
        {
            "airline": "Google Flights (Comparador General)",
            "route": f"Búsqueda general para: {q}",
            "status": "Comparador global de tarifas y horarios.",
            "booking_url": "https://www.google.com/travel/flights"
        }
    ])
    
    return {"status": "success", "flights": flights_list, "gemini_interpretation": gemini_output}

# ============================================================# ENDPOINT DE REGLAS (AUTORIDAD INTERNA EXCLUSIVA) # ============================================================
@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    verify_session_token(payload.session_token)
    texto = clean_text(payload.item_description, 2000).lower()
    
    tiene_maletas = any(k in texto for k in ["maleta", "maletas", "equipaje", "libra", "libras", "lb"])
    tiene_estacion = any(k in texto for k in ["estacion", "estación", "energia", "energía", "watt", "watts", "wh", "bateria", "batería", "litio"])
    tiene_soda = any(k in texto for k in ["soda", "cáustica", "caustica", "hidróxido", "quimico", "químico", "peligroso"])
    
    # Motor de reglas interno estricto (Gemini NO decide permitido/prohibido)
    if tiene_maletas and tiene_estacion and tiene_soda:
        return {
            "status_category": "ORIENTACIÓN MULTIMODAL: EQUIPAJE, BATERÍAS Y SUSTANCIAS",
            "short_answer": "Cada elemento sigue una vía independiente: maletas en counter, estación de energía por carga comercial, y soda cáustica por mercancía peligrosa (Hazmat).",
            "details": "ANÁLISIS TÉCNICO Y SOLUCIÓN DIRECTA:\n\n1. Maletas personales: Se ajustan al límite estándar (aprox. 50 lbs / 23 kg).\n2. Estación de energía (Watt-horas elevados): Excede los límites permitidos en equipaje de pasajero; debe despacharse mediante servicio comercial de carga.\n3. Soda cáustica: Clasificada como material corrosivo peligroso. Prohibida en cabina y bodega de pasajeros; requiere estricto manejo de Carga Peligrosa (DGR) con embalaje certificado UN.",
            "source_reference": "Normativa IATA DGR, DOT y Estándares TSA (Verificado 2026)",
            "official_links": [
                {"title": "IATA Dangerous Goods (DGR)", "url": "https://www.iata.org/en/programs/cargo/dgr/"},
                {"title": "DOT Hazardous Materials Safety", "url": "https://www.phmsa.dot.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_maletas and tiene_estacion:
        return {
            "status_category": "ORIENTACIÓN ESPECIALIZADA: EQUIPAJE Y ACUMULADORES",
            "short_answer": "Tus maletas cumplen con el estándar y la estación de energía requiere canalización por carga comercial.",
            "details": "INSTRUCCIÓN DIRECTA:\n\n1. Equipaje: Dos maletas de 50 lbs (23 kg) cumplen con los parámetros habituales.\n2. Estación de energía: Su capacidad energética requiere transporte exclusivo por carga comercial autorizada.",
            "source_reference": "Normativa Internacional de Equipaje y Carga (Verificado 2026)",
            "official_links": [
                {"title": "IATA Lithium Batteries Guide", "url": "https://www.iata.org/en/programs/cargo/dgr/lithium-batteries/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_soda:
        return {
            "status_category": "ORIENTACIÓN NORMATIVA: SUSTANCIAS CORROSIVAS",
            "short_answer": "La soda cáustica es una sustancia regulada que exige transporte especializado fuera del equipaje de pasajeros.",
            "details": "INSTRUCCIÓN TÉCNICA:\n\n1. Restricción de pasajero: No está permitida en equipaje de mano ni facturado.\n2. Solución logística: Debe tramitarse mediante un operador de carga bajo el reglamento de Mercancías Peligrosas.",
            "source_reference": "Regulaciones IATA DGR y DOT Hazmat (Verificado 2026)",
            "official_links": [
                {"title": "IATA Dangerous Goods Regulations", "url": "https://www.iata.org/en/programs/cargo/dgr/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_estacion:
        return {
            "status_category": "ORIENTACIÓN SOBRE ACUMULADORES Y ENERGÍA",
            "short_answer": "Las estaciones de energía de alta capacidad se gestionan mediante carga comercial.",
            "details": "INSTRUCCIÓN PRÁCTICA:\nLos acumuladores energéticos están sujetos a normativas rigurosas de seguridad aérea. Despacharlo por carga comercial asegura un procedimiento sin contratiempos.",
            "source_reference": "Estándares Operativos de Transporte (Verificado 2026)",
            "official_links": [
                {"title": "IATA DGR Oficial", "url": "https://www.iata.org/en/programs/cargo/dgr/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    if tiene_maletas:
        return {
            "status_category": "ORIENTACIÓN DE PESO Y EQUIPAJE",
            "short_answer": "Tus maletas se encuentran dentro de los parámetros habituales para el mostrador.",
            "details": "INSTRUCCIÓN DIRECTA:\nMantener el peso de cada pieza en torno a las 50 lbs (23 kg) garantiza un proceso fluido.",
            "source_reference": "Políticas Generales de Equipaje DOT (Verificado 2026)",
            "official_links": [
                {"title": "DOT Air Consumer Baggage", "url": "https://www.transportation.gov/airconsumer/baggage"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }

    # Búsqueda en el repositorio interno de reglas
    rule = rule_repo.find_rule(payload.airline or "General", texto)
    if rule and rule.status == RuleStatus.ACTIVA:
        return {
            "status_category": rule.category_visual,
            "short_answer": rule.short_answer,
            "details": rule.details,
            "source_reference": f"{rule.source_name} (Verificado el {rule.verification_date})",
            "official_links": [{"title": "Sitio Oficial de Referencia Regulatoria", "url": "https://www.iata.org"}],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
    else:
        return {
            "status_category": "ORIENTACIÓN LOGÍSTICA INTEGRAL",
            "short_answer": f"Todo tiene solución para el traslado de '{payload.item_description}'. Organicémoslo paso a paso.",
            "details": "PASO SUGERIDO:\nEvaluación del objeto: Si el artículo incluye mercancías especiales, pesadas o químicas, la recomendación operativa es canalizarlo mediante un servicio de carga o courier autorizado.",
            "source_reference": "Asesoría Logística Multimodal (Verificado 2026)",
            "official_links": [
                {"title": "IATA Official Website", "url": "https://www.iata.org/"},
                {"title": "U.S. Customs and Border Protection", "url": "https://www.cbp.gov/"}
            ],
            "disclaimer": LegalNoticeManager.get_official_disclaimer()["content"]
        }
try:
        const response = await fetch("/api/v1/item/check", {{
            method:"POST",
            headers:{{"Content-Type":"application/json"}},
            body:JSON.stringify({{
                session_token:sessionToken,
                item_description:item,
                flight_context:{{natural_query:flightQuery}}
            }})
        }});

        const data = await response.json();

        if (!response.ok) {{
            throw new Error(data.detail || "No fue posible revisar el artículo.");
        }}

        let cls = "info";
        let statusText = "INFORMACIÓN";

        if (data.status === "allowed") {{
            cls = "ok";
            statusText = "SÍ PUEDE LLEVARSE";
        }} else if (data.status === "prohibited") {{
            cls = "no";
            statusText = "NO ESTÁ PERMITIDO";
        }} else if (data.status === "conditional") {{
            cls = "warn";
            statusText = "SUJETO A CONDICIONES";
        }} else if (data.status === "need_info") {{
            cls = "info";
            statusText = "NECESITO MÁS INFORMACIÓN";
        }}

        let out = "<div class='result'>";
        out += "<h3 class='" + cls + "'>" + statusText + "</h3>";
        out += "<p><strong>Artículo:</strong> " + escapeHtml(data.item || item) + "</p>";
        out += "<p>" + escapeHtml(data.short_answer || "") + "</p>";

        if (data.details) {{
            out += "<div class='box'>" + escapeHtml(data.details) + "</div>";
        }}

        if (data.recommendations && data.recommendations.length) {{
            out += "<p><strong>Sugerencias y soluciones:</strong></p><ul>";
            data.recommendations.forEach(r => {{
                out += "<li>" + escapeHtml(r) + "</li>";
            }});
            out += "</ul>";
        }}

        if (data.official_links && data.official_links.length) {{
            out += "<p><strong>Enlaces oficiales:</strong></p><ul>";
            data.official_links.forEach(l => {{
                if (l.url && /^https?:\/\//i.test(l.url)) {{
                    out += "<li><a target='_blank' rel='noopener noreferrer' href='" +
                           escapeAttr(l.url) + "'>" + escapeHtml(l.title || l.url) + "</a></li>";
                }}
            }});
            out += "</ul>";
        }}

        if (data.disclaimer) {{
            out += "<p class='small' style='margin-top:12px'>" +
                   escapeHtml(data.disclaimer) + "</p>";
        }}

        out += "</div>";
        document.getElementById("result").innerHTML = out;

    }} catch(error) {{
        showResult(
            "<div class='result'><p class='info'>🔵 NECESITO MÁS INFORMACIÓN</p>" +
            "<p>" + escapeHtml(error.message) + "</p></div>"
        );
    }}
}}

function clearForm() {{
    document.getElementById("flightQuery").value = "";
    document.getElementById("item").value = "";
    document.getElementById("result").innerHTML = "";
}}

function showResult(htmlText) {{
    document.getElementById("result").innerHTML =
        "<div class='result'>" + htmlText + "</div>";
}}

function escapeHtml(str) {{
    return String(str || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}}

function escapeAttr(str) {{
    return escapeHtml(str);
}}

window.addEventListener("DOMContentLoaded", () => {{
    activateFromStripe();
}});
</script>

</body>
</html>
    """
    return HTMLResponse(content=html_content)
# main.py — ¿QUÉ QUIERES LLEVAR? | May Roga LLC
# Producción: FastAPI + Stripe + Gemini API
# Producto actual: $15.99 = 1 servicio / 15 minutos
# Gemini: búsqueda/interpretación de vuelos únicamente.
# Motor de reglas: autoridad interna para las respuestas de equipaje.

import os
import re
import json
import html
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import stripe
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from rules_engine import RuleRepository, RuleStatus
from legal_disclaimer import LegalNoticeManager

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

# ============================================================
# CONFIGURACIÓN
# ============================================================
APP_NAME = "¿Qué Quieres Llevar?"
APP_VERSION = "6.0.0"
OWNER = "May Roga LLC"
SESSION_MINUTES = 15

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
STRIPE_PRICE_ID1 = os.getenv("STRIPE_PRICE_ID1", "").strip()
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
APP_BASE_URL = os.getenv("APP_BASE_URL", "https://que-quieres-llevar.onrender.com").rstrip("/")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "").strip()

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

rule_repo = RuleRepository()
gemini_client = None
if GEMINI_API_KEY and genai is not None:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception:
        gemini_client = None

# ============================================================
# APP
# ============================================================
app = FastAPI(
    title=APP_NAME,
    description="Herramienta independiente de orientación preventiva sobre equipaje, artículos y vuelos. May Roga LLC.",
    version=APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[APP_BASE_URL],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Stripe-Signature"],
)

# ============================================================
# MODELOS
# ============================================================
class FlightSearchRequest(BaseModel):
    natural_query: str = Field(..., min_length=3, max_length=1200)
    session_token: str = Field(..., min_length=20, max_length=300)

class ItemCheckRequest(BaseModel):
    session_token: str = Field(..., min_length=20, max_length=300)
    item_description: str = Field(..., min_length=1, max_length=2000)
    airline: Optional[str] = Field(default=None, max_length=150)
    destination: Optional[str] = Field(default=None, max_length=150)
    flight_context: Optional[dict[str, Any]] = None

class AdminLoginRequest(BaseModel):
    username: str
    password: str

class ActivateSessionRequest(BaseModel):
    checkout_session_id: str = Field(..., min_length=10, max_length=300)

class CheckoutRequest(BaseModel):
    pass

# ============================================================
# UTILIDADES
# ============================================================
def utcnow() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()

def clean_text(value: Any, max_len: int = 2000) -> str:
    if value is None:
        return ""
    return str(value).strip()[:max_len]

def safe_url(url: str) -> bool:
    return bool(isinstance(url, str) and (url.startswith("https://") or url.startswith("http://")))

def escape(value: Any) -> str:
    return html.escape(str(value or ""))

# ============================================================
# SESIONES
# ============================================================
SESSION_SECRET = os.getenv("SESSION_SIGNING_SECRET", "").strip()

def require_session_secret():
    if not SESSION_SECRET:
        raise HTTPException(status_code=503, detail="El servicio de sesiones no está configurado.")

def sign_session(raw: str) -> str:
    require_session_secret()
    sig = hmac.new(SESSION_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"

def build_session_token(checkout_session_id: str, started_at: datetime, expires_at: datetime) -> str:
    raw = json.dumps(
        {
            "v": 1,
            "cs": checkout_session_id,
            "st": int(started_at.timestamp()),
            "ex": int(expires_at.timestamp())
        },
        separators=(",", ":"),
        sort_keys=True
    )
    return sign_session(raw)

def verify_session_token(token: str) -> dict:
    require_session_secret()
    try:
        raw, signature = token.rsplit(".", 1)
        expected = hmac.new(SESSION_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError("firma")
        data = json.loads(raw)
        if data.get("v") != 1:
            raise ValueError("version")
        
        checkout_id = data.get("cs")
        started = int(data.get("st"))
        expires = int(data.get("ex"))
        now = int(utcnow().timestamp())

        if now >= expires:
            raise HTTPException(status_code=403, detail="La sesión de 15 minutos ha terminado.")
        if expires <= started:
            raise ValueError("fechas")
        if not checkout_id:
            raise ValueError("checkout")
        return data
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=403, detail="Sesión inválida o expirada.")

def stripe_payment_is_valid(checkout_session_id: str) -> dict:
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe no está configurado.")
    if not checkout_session_id.startswith("cs_"):
        raise HTTPException(status_code=400, detail="Identificador de pago inválido.")
    try:
        session = stripe.checkout.Session.retrieve(checkout_session_id, expand=["line_items"])
    except Exception:
        raise HTTPException(status_code=400, detail="No fue posible verificar el pago.")

    if session.get("payment_status") != "paid":
        raise HTTPException(status_code=402, detail="El pago todavía no está confirmado.")

    line_items = session.get("line_items", {}).get("data", [])
    valid_price = any(item.get("price", {}).get("id") == STRIPE_PRICE_ID1 for item in line_items)
    if not valid_price:
        raise HTTPException(status_code=403, detail="El pago no corresponde al servicio solicitado.")
    return session

def get_active_session(token: str) -> dict:
    data = verify_session_token(token)
    session = stripe_payment_is_valid(data["cs"])
    if session.get("payment_status") != "paid":
        raise HTTPException(status_code=403, detail="El pago ya no está confirmado.")
    return data

# ============================================================
# LEGAL
# ============================================================
def legal_intro() -> dict:
    try:
        return LegalNoticeManager.get_intro_explanation()
    except Exception:
        return {
            "what_is_it": "¿QUÉ QUIERES LLEVAR? es una aplicación independiente desarrollada por May Roga LLC.",
            "what_it_does": "Ayuda al pasajero a revisar información sobre equipaje y artículos antes de viajar.",
            "problem_solved": "Reduce la incertidumbre y evita decisiones basadas únicamente en suposiciones.",
            "core_message": "Dime qué quieres llevar y te ayudaremos a revisar si puede viajar contigo según los datos de tu vuelo y las reglas que podamos verificar."
        }

def legal_disclaimer() -> str:
    try:
        return LegalNoticeManager.get_official_disclaimer()["content"]
    except Exception:
        return "Esta aplicación proporciona información orientativa basada en fuentes verificadas. No sustituye a la aerolínea, TSA, DOT, FAA, CBP ni a ninguna autoridad competente."

# ============================================================
# HEALTH & STATUS
# ============================================================
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
        "stripe_configured": bool(STRIPE_SECRET_KEY and STRIPE_PRICE_ID1),
        "gemini_configured": bool(gemini_client)
    }

@app.get("/api/v1/status")
def service_status():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "payment": "configured" if STRIPE_SECRET_KEY and STRIPE_PRICE_ID1 else "not_configured",
        "flight_search": "configured" if gemini_client else "not_configured",
        "session_minutes": SESSION_MINUTES
    }

# ============================================================
# PÁGINA PRINCIPAL / FRONTEND HTML
# ============================================================
@app.get("/", response_class=HTMLResponse)
def read_root():
    intro = legal_intro()
    html_content = f"""
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(APP_NAME)} — May Roga LLC</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f3f6f8;color:#1f2937;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:700px;margin:auto;padding:18px}}
.card{{background:#fff;border-radius:16px;padding:22px;box-shadow:0 5px 25px rgba(0,0,0,.08)}}
h1{{text-align:center;margin:4px 0;color:#0f3d59;font-size:25px}}
.sub{{text-align:center;color:#64748b;font-size:13px}}
.box{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px;margin:14px 0;line-height:1.5;font-size:14px}}
.warning{{border-left:4px solid #0f3d59}}
label{{display:block;font-weight:700;margin:15px 0 6px;font-size:14px}}
textarea,input{{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:9px;font-size:15px}}
button{{width:100%;border:0;border-radius:9px;padding:13px;margin-top:10px;background:#0f3d59;color:#fff;font-weight:700;font-size:15px;cursor:pointer}}
button.secondary{{background:#64748b}}
button.green{{background:#166534}}
button:disabled{{opacity:.55;cursor:not-allowed}}
.small{{font-size:12px;color:#64748b;line-height:1.45}}
#appArea{{display:none}}
#result{{margin-top:15px}}
.result{{padding:15px;border-radius:10px;background:#f8fafc;border:1px solid #e2e8f0}}
.ok{{color:#166534;font-weight:800}}
.no{{color:#991b1b;font-weight:800}}
.warn{{color:#92400e;font-weight:800}}
.info{{color:#1e40af;font-weight:800}}
.timer{{text-align:center;font-size:20px;font-weight:800;margin:12px 0;color:#0f3d59}}
a{{color:#0f3d59;font-weight:700}}
ul{{padding-left:20px}}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h1>¿QUÉ QUIERES LLEVAR?</h1>
<div class="sub">May Roga LLC</div>

<div class="box warning">
<strong>¿Qué es?</strong><br>{escape(intro.get("what_is_it",""))}<br><br>
<strong>¿Para qué sirve?</strong><br>{escape(intro.get("what_it_does",""))}<br><br>
<strong>¿Qué problema busca resolver?</strong><br>{escape(intro.get("problem_solved",""))}<br><br>
<strong>Mensaje principal:</strong><br>{escape(intro.get("core_message",""))}
</div>

<div class="box">
<strong>Importante:</strong><br>
La aplicación ayuda a reducir la incertidumbre antes de llegar al aeropuerto. No garantiza que una aerolínea acepte un artículo ni sustituye la decisión final de la aerolínea o autoridad competente. Si una regla no puede verificarse, la aplicación no debe inventar una respuesta.
</div>

<div id="legal">
<h3>Antes de comenzar</h3>
<p class="small">Al continuar reconoces que esta aplicación ofrece orientación informativa y preventiva basada en fuentes verificadas. No sustituye a la aerolínea, TSA, DOT, FAA, CBP ni a otra autoridad competente.</p>
<p class="small">El servicio actual cuesta <strong>$15.99</strong> y corresponde a <strong>un solo servicio de 15 minutos</strong>. No es una suscripción.</p>
<label><input type="checkbox" id="acceptLegal" style="width:auto"> He leído y acepto esta explicación.</label>
<button id="payBtn" onclick="startPayment()" disabled>PAGAR $15.99 — INICIAR SERVICIO</button>
</div>

<div id="appArea">
<div class="timer">Tiempo restante: <span id="timer">15:00</span></div>
<label>1. ¿Dónde y cuándo viajas?</label>
<textarea id="flightQuery" rows="3" placeholder="Ejemplo: Miami a La Habana el 15 de diciembre con American Airlines"></textarea>
<button onclick="searchFlight()">✈️ BUSCAR / IDENTIFICAR MI VUELO</button>

<label>2. ¿Qué quieres llevar?</label>
<textarea id="item" rows="3" placeholder="Ejemplo: una cafetera de 8 libras"></textarea>
<button class="green" onclick="checkItem()">🔎 REVISAR SI PUEDO LLEVARLO</button>
<button class="secondary" onclick="clearForm()">BORRAR</button>
<div id="result"></div>
</div>

<div class="box small" style="margin-top:20px"><strong>Aviso:</strong><br>{escape(legal_disclaimer())}</div>
<div class="small" style="text-align:center">&copy; 2026 May Roga LLC. Todos los derechos reservados.</div>
</div>
</div>

<script>
let sessionToken = "";
let expiresAt = 0;
let timerHandle = null;

const legalCheck = document.getElementById("acceptLegal");
const payBtn = document.getElementById("payBtn");

legalCheck.addEventListener("change", () => {{
    payBtn.disabled = !legalCheck.checked;
}});

async function startPayment() {{
    payBtn.disabled = true;
    payBtn.innerText = "CREANDO PAGO...";
    try {{
        const response = await fetch("/api/v1/stripe/create-checkout", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{}})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No fue posible iniciar el pago.");
        window.location.href = data.checkout_url;
    }} catch(error) {{
        alert(error.message);
        payBtn.disabled = false;
        payBtn.innerText = "PAGAR $15.99 — INICIAR SERVICIO";
    }}
}}

async function activateFromStripe() {{
    const params = new URLSearchParams(window.location.search);
    const checkoutSessionId = params.get("session_id");
    if (!checkoutSessionId) return false;

    try {{
        const response = await fetch("/api/v1/stripe/activate", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ checkout_session_id: checkoutSessionId }})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No se pudo activar el servicio.");

        sessionToken = data.session_token;
        expiresAt = Date.parse(data.expires_at);

        document.getElementById("legal").style.display = "none";
        document.getElementById("appArea").style.display = "block";
        history.replaceState({{}}, document.title, "/");
        startTimer();
        return true;
    }} catch(error) {{
        document.getElementById("result").innerHTML = "<div class='result'><strong>No se pudo activar el servicio.</strong><br>" + escapeHtml(error.message) + "</div>";
        return false;
    }}
}}

function startTimer() {{
    clearInterval(timerHandle);
    function update() {{
        const remaining = Math.max(0, expiresAt - Date.now());
        const totalSeconds = Math.floor(remaining / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;

        document.getElementById("timer").innerText = String(minutes).padStart(2,"0") + ":" + String(seconds).padStart(2,"0");
        if (remaining <= 0) {{
            clearInterval(timerHandle);
            sessionToken = "";
            document.getElementById("appArea").innerHTML = "<div class='result'><h3>⏱️ SERVICIO TERMINADO</h3><p>Tu servicio de 15 minutos ha terminado.</p><button onclick='window.location.href=\"/\"'>INICIAR DE NUEVO</button></div>";
        }}
    }}
    update();
    timerHandle = setInterval(update, 1000);
}}

async function searchFlight() {{
    const query = document.getElementById("flightQuery").value.trim();
    if (!query) {{ alert("Escribe primero los datos de tu viaje."); return; }}
    showResult("Buscando información actual del vuelo...");

    try {{
        const response = await fetch("/api/v1/flight/search", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ natural_query: query, session_token: sessionToken }})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No fue posible buscar el vuelo.");

        let out = "<div class='result'><h3>✈️ Resultado de búsqueda</h3>";
        if (!data.flights || !data.flights.length) {{
            out += "<p class='info'>🔵 NECESITO MÁS INFORMACIÓN</p><p>No encontramos suficiente información verificable.</p>";
        }} else {{
            data.flights.forEach((f) => {{
                out += "<div class='box'><strong>" + escapeHtml(f.airline || "") + "</strong><br>" + escapeHtml(f.route || "") + "<br>";
                if (f.flight_number) out += "Vuelo: " + escapeHtml(f.flight_number) + "<br>";
                if (f.source) out += "<span class='small'>Fuente: " + escapeHtml(f.source) + "</span><br>";
                if (f.url && /^https?:\\/\\//i.test(f.url)) out += "<a target='_blank' rel='noopener noreferrer' href='" + escapeAttr(f.url) + "'>Ver fuente</a>";
                out += "</div>";
            }});
        }}
        out += "</div>";
        document.getElementById("result").innerHTML = out;
    }} catch(error) {{
        showResult("<div class='result'><p class='info'>🔵 NECESITO MÁS INFORMACIÓN</p><p>" + escapeHtml(error.message) + "</p></div>");
    }}
}}

async function checkItem() {{
    const item = document.getElementById("item").value.trim();
    const flightQuery = document.getElementById("flightQuery").value.trim();
    if (!item) {{ alert("Escribe primero qué quieres llevar."); return; }}
    showResult("Revisando la información disponible...");

    try {{
        const response = await fetch("/api/v1/consultar-articulo", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ session_token: sessionToken, item_description: item, flight_context: {{ natural_query: flightQuery }} }})
        }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "No fue posible realizar la consulta.");

        let cls = "info";
        if ((data.status_category || "").includes("PUEDES LLEVARLO")) cls = "ok";
        if ((data.status_category || "").includes("NO PUEDES")) cls = "no";

        let links = "";
        if (Array.isArray(data.official_links)) {{
            links = "<ul>";
            data.official_links.forEach((link) => {{
                if (link.url && /^https?:\\/\\//i.test(link.url)) {{
                    links += "<li><a target='_blank' rel='noopener noreferrer' href='" + escapeAttr(link.url) + "'>" + escapeHtml(link.title || "Fuente oficial") + "</a></li>";
                }}
            }});
            links += "</ul>";
        }}

        document.getElementById("result").innerHTML = "<div class='result'><h3 class='" + cls + "'>" + escapeHtml(data.status_category || "RESULTADO") + "</h3><p><strong>" + escapeHtml(data.short_answer || "") + "</strong></p><div class='box'>" + escapeHtml(data.details || "") + "</div>" + (links ? "<div class='box'><strong>Fuentes:</strong>" + links + "</div>" : "") + "<p class='small'>" + escapeHtml(data.source_reference || "") + "</p></div>";
    }} catch(error) {{
        showResult("<div class='result'><p class='info'>🔵 NECESITO MÁS INFORMACIÓN</p><p>" + escapeHtml(error.message) + "</p></div>");
    }}
}}

function clearForm() {{
    document.getElementById("flightQuery").value = "";
    document.getElementById("item").value = "";
    document.getElementById("result").innerHTML = "";
}}

function showResult(text) {{
    document.getElementById("result").innerHTML = "<div class='result'>" + text + "</div>";
}}

function escapeHtml(value) {{
    return String(value ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
}}

function escapeAttr(value) {{
    return escapeHtml(value);
}}

activateFromStripe();
</script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

# ============================================================
# STRIPE & CHECKOUT
# ============================================================
@app.post("/api/v1/stripe/create-checkout")
def create_checkout(_: CheckoutRequest):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe não está configurado.")
    if not STRIPE_PRICE_ID1:
        raise HTTPException(status_code=503, detail="STRIPE_PRICE_ID1 no está configurado.")

    try:
        checkout = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_ID1, "quantity": 1}],
            success_url=f"{APP_BASE_URL}/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_BASE_URL}/",
            allow_promotion_codes=False,
            metadata={"service": "que_quieres_llevar", "service_version": APP_VERSION, "duration_minutes": str(SESSION_MINUTES)}
        )
    except Exception:
        raise HTTPException(status_code=502, detail="No fue posible crear el pago.")

    return {"status": "created", "checkout_url": checkout.url, "checkout_session_id": checkout.id}

@app.post("/api/v1/stripe/webhook")
async def stripe_webhook(request: Request):
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="STRIPE_WEBHOOK_SECRET no está configurado.")
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Falta la firma de Stripe.")
    try:
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except Exception:
        raise HTTPException(status_code=400, detail="Firma de Stripe inválida.")
    return {"received": True, "event_type": event.get("type")}

@app.post("/api/v1/stripe/activate")
def activate_session(payload: ActivateSessionRequest):
    session = stripe_payment_is_valid(payload.checkout_session_id)
    metadata = dict(session.get("metadata") or {})
    if metadata.get("service") != "que_quieres_llevar":
        raise HTTPException(status_code=403, detail="El pago no corresponde a este servicio.")
    if metadata.get("activated_at"):
        raise HTTPException(status_code=403, detail="Este pago ya fue utilizado para iniciar un servicio.")

    started_at = utcnow()
    expires_at = started_at + timedelta(minutes=SESSION_MINUTES)

    try:
        stripe.checkout.Session.modify(
            payload.checkout_session_id,
            metadata={**metadata, "activated_at": iso(started_at), "expires_at": iso(expires_at), "service_status": "active"}
        )
    except Exception:
        raise HTTPException(status_code=502, detail="No fue posible registrar el inicio del servicio.")

    token = build_session_token(payload.checkout_session_id, started_at, expires_at)
    return {"status": "active", "session_token": token, "started_at": iso(started_at), "expires_at": iso(expires_at), "minutes": SESSION_MINUTES}

@app.get("/api/v1/session/status")
def session_status(session_token: str):
    data = get_active_session(session_token)
    expires = datetime.fromtimestamp(int(data["ex"]), tz=timezone.utc)
    remaining = max(0, int((expires - utcnow()).total_seconds()))
    return {"active": remaining > 0, "expires_at": iso(expires), "remaining_seconds": remaining}

# ============================================================
# GEMINI — BÚSQUEDA DE VUELOS
# ============================================================
def extract_json_object(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except Exception:
        pass
    match = re.search(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, flags=re.S)
    if not match:
        return None
    try:
        value = json.loads(match.group(0))
        return value if isinstance(value, dict) else None
    except Exception:
        return None

def gemini_flight_search(query: str) -> dict:
    if gemini_client is None:
        raise HTTPException(status_code=503, detail="La búsqueda de vuelos no está configurada.")

    prompt = f"""
Eres un módulo interno de búsqueda de vuelos de una aplicación llamada ¿QUÉ QUIERES LLEVAR? de May Roga LLC.
Tu trabajo aquí NO es decidir reglas de equipaje.
Busca información actual disponible públicamente sobre vuelos que correspondan a la solicitud del usuario.
SOLICITUD DEL USUARIO:{query}
Devuelve exclusivamente JSON válido con estructura:
{{
  "flights": [
    {{
      "airline": "",
      "flight_number": "",
      "origin": "",
      "destination": "",
      "date": "",
      "route": "",
      "source": "",
      "url": ""
    }}
  ],
  "notice": ""
}}
"""
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
        )
    except Exception:
        raise HTTPException(status_code=502, detail="No fue posible consultar el servicio de búsqueda.")

    result = extract_json_object(getattr(response, "text", "") or "")
    if not result:
        return {"flights": [], "notice": "No encontramos información suficientemente verificable."}

    flights = result.get("flights")
    if not isinstance(flights, list):
        flights = []

    cleaned = []
    for flight in flights[:10]:
        if not isinstance(flight, dict):
            continue
        item = {
            "airline": clean_text(flight.get("airline"), 150),
            "flight_number": clean_text(flight.get("flight_number"), 50),
            "route": clean_text(flight.get("route"), 250),
            "source": clean_text(flight.get("source"), 200),
            "url": clean_text(flight.get("url"), 500)
        }
        if item["url"] and not safe_url(item["url"]):
            item["url"] = ""
        if item["airline"] or item["flight_number"] or item["route"]:
            cleaned.append(item)

    return {"flights": cleaned, "notice": clean_text(result.get("notice", "Confirmar antes de viajar."), 500)}

@app.post("/api/v1/flight/search")
def search_flight(payload: FlightSearchRequest):
    get_active_session(payload.session_token)
    query = clean_text(payload.natural_query, 1200)
    result = gemini_flight_search(query)
    return {"status": "success", **result}

# ============================================================
# MOTOR DE REGLAS
# ============================================================
def normalize_airline(value: Optional[str]) -> str:
    return clean_text(value, 150) or "general"

def official_rule_links(rule) -> list:
    source = getattr(rule, "source_name", "") or ""
    return [{"title": source or "Fuente de referencia", "url": "https://www.iata.org/"}]

@app.post("/api/v1/consultar-articulo")
def consultar_articulo(payload: ItemCheckRequest):
    get_active_session(payload.session_token)
    item = clean_text(payload.item_description, 2000)
    airline = normalize_airline(payload.airline)

    if not item:
        raise HTTPException(status_code=422, detail="Debes indicar qué artículo quieres consultar.")

    rule = rule_repo.find_rule(airline, item.lower())
    if rule and rule.status == RuleStatus.ACTIVA:
        return {
            "status_category": rule.category_visual,
            "short_answer": rule.short_answer,
            "details": rule.details,
            "source_reference": f"{rule.source_name} (Verificado el {rule.verification_date})",
            "official_links": official_rule_links(rule),
            "disclaimer": legal_disclaimer()
        }

    return {
        "status_category": "NECESITO MÁS INFORMACIÓN",
        "short_answer": "No encontramos una regla verificada suficiente para darte una respuesta segura sobre este artículo.",
        "details": "No vamos a inventar una autorización o prohibición. Necesitamos información adicional o una fuente oficial que permita verificar la condición aplicable.",
        "source_reference": "Regla no verificada",
        "official_links": [
            {"title": "IATA", "url": "https://www.iata.org/"},
            {"title": "TSA — What Can I Bring?", "url": "https://www.tsa.gov/travel/security-screening/whatcanibring/"},
            {"title": "U.S. DOT — Air Consumer", "url": "https://www.transportation.gov/airconsumer"}
        ],
        "disclaimer": legal_disclaimer()
    }

# ============================================================
# ADMIN
# ============================================================
ADMIN_TOKENS = {}

@app.post("/api/v1/admin/login")
def admin_login(payload: AdminLoginRequest):
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Acceso administrativo no configurado.")
    if not hmac.compare_digest(payload.username, ADMIN_USERNAME) or not hmac.compare_digest(payload.password, ADMIN_PASSWORD):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")

    token = secrets.token_urlsafe(32)
    ADMIN_TOKENS[token] = utcnow() + timedelta(hours=2)
    return {"status": "success", "session_token": token, "expires_at": iso(ADMIN_TOKENS[token])}

# ============================================================
# EXCEPCIONES Y STARTUP
# ============================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "detail": str(exc.detail)})

@app.on_event("startup")
async def startup_check():
    missing = []
    if not STRIPE_SECRET_KEY: missing.append("STRIPE_SECRET_KEY")
    if not STRIPE_PRICE_ID1: missing.append("STRIPE_PRICE_ID1")
    if not STRIPE_WEBHOOK_SECRET: missing.append("STRIPE_WEBHOOK_SECRET")
    if not SESSION_SECRET: missing.append("SESSION_SIGNING_SECRET")
    if not GEMINI_API_KEY: missing.append("GEMINI_API_KEY")

    if missing:
        print(f"[CONFIGURACIÓN] Variables faltantes: {', '.join(missing)}")
    else:
        print(f"[OK] {APP_NAME} v{APP_VERSION} configurado.")    
