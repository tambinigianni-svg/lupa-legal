// =========================================================
// Lupa Legal - código compartido por todas las páginas
//   - utilidades (escapar HTML, pedir datos al servidor)
//   - estado de la IA en el encabezado
//   - chatbot "Lupa" (se agrega solo en cada página)
// =========================================================

const $ = (id) => document.getElementById(id);

function escaparHTML(texto) {
  return String(texto ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#39;");
}

async function pedirJSON(url, datos) {
  const opciones = datos === undefined ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(datos),
  };
  const respuesta = await fetch(url, opciones);
  const json = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) throw new Error(json.error || "Error " + respuesta.status);
  return json;
}

// Cada página puede definir qué contexto recibe el chatbot (documento y/o cálculo de plazo).
window.contextoChat = window.contextoChat || (() => ({ texto: "", calculo_plazo: null, anonimizar: true }));

const Lupa = { iaDisponible: false, historial: [] };

async function consultarEstadoIA() {
  const pill = $("estado-ia");
  try {
    const info = await pedirJSON("/api/estado");
    Lupa.iaDisponible = info.disponible;
    Lupa.infoIA = info;
    if (pill) {
      pill.textContent = info.disponible ? `IA activa · ${info.nombre_proveedor}` : "IA no disponible";
      pill.classList.toggle("on", info.disponible);
    }
    const sub = $("chat-modelo");
    if (sub) sub.textContent = info.disponible ? `Conectado con ${info.nombre_proveedor}` : "IA no disponible";
  } catch {
    if (pill) pill.textContent = "Servidor no disponible";
  }
}

// ---------- Chatbot ----------
const SUGERENCIAS_CHAT = window.SUGERENCIAS_CHAT || [
  "Resume el documento en 5 puntos",
  "¿Qué es lo más riesgoso o urgente?",
  "¿Qué recurso procede y en qué plazo?",
  "Explícalo en lenguaje sencillo",
];

function crearChat() {
  const boton = document.createElement("button");
  boton.className = "boton primario boton-chat";
  boton.id = "abrir-chat";
  boton.type = "button";
  boton.textContent = "💬 Pregúntale a Lupa";

  const chat = document.createElement("section");
  chat.className = "chat";
  chat.id = "chat";
  chat.setAttribute("aria-label", "Asistente de IA");
  chat.innerHTML = `
    <div class="chat-cabecera">
      <div><strong>Lupa · asistente legal</strong><small id="chat-modelo">Verificando IA…</small></div>
      <button type="button" id="cerrar-chat" aria-label="Cerrar chat">×</button>
    </div>
    <div class="chat-mensajes" id="chat-mensajes">
      <div class="burbuja asistente">¡Hola! Soy Lupa 👋. Puedo explicarte el documento que cargaste (contrato, resolución, casación o escrito), decirte qué revisar y ayudarte con los plazos.</div>
    </div>
    <div class="sugerencias" id="sugerencias">
      ${SUGERENCIAS_CHAT.map((s) => `<button class="chip" type="button">${escaparHTML(s)}</button>`).join("")}
    </div>
    <form id="chat-form">
      <input type="text" id="chat-pregunta" placeholder="Escribe tu pregunta…" autocomplete="off" maxlength="2000">
      <button class="boton primario" type="submit">Enviar</button>
    </form>`;
  document.body.append(boton, chat);

  boton.addEventListener("click", () => {
    chat.classList.toggle("abierto");
    if (chat.classList.contains("abierto")) $("chat-pregunta").focus();
  });
  $("cerrar-chat").addEventListener("click", () => chat.classList.remove("abierto"));
  $("sugerencias").addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (chip) enviarPregunta(chip.textContent);
  });
  $("chat-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const pregunta = $("chat-pregunta").value.trim();
    if (pregunta) enviarPregunta(pregunta);
  });
}

function abrirChatCon(pregunta) {
  $("chat").classList.add("abierto");
  if (pregunta) enviarPregunta(pregunta);
}

function agregarBurbuja(clases, texto) {
  const burbuja = document.createElement("div");
  burbuja.className = "burbuja " + clases;
  burbuja.textContent = texto;
  $("chat-mensajes").appendChild(burbuja);
  $("chat-mensajes").scrollTop = $("chat-mensajes").scrollHeight;
  return burbuja;
}

function formatoSimple(texto) {
  // Convierte **negrita** en <strong> de forma segura (primero se escapa el HTML).
  return escaparHTML(texto).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

async function enviarPregunta(pregunta) {
  $("chat-pregunta").value = "";
  agregarBurbuja("usuario", pregunta);
  const burbuja = agregarBurbuja("asistente escribiendo", "");

  if (!Lupa.iaDisponible) {
    burbuja.classList.remove("escribiendo");
    burbuja.textContent = "🔑 La IA no está disponible. Inicia sesión en Claude Code (VS Code o la app) o agrega una clave en el archivo .env, y reinicia el servidor.";
    return;
  }

  const contexto = window.contextoChat();
  let respuesta = "";
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pregunta, historial: Lupa.historial, ...contexto }),
    });
    if (!r.ok) {
      const error = await r.json().catch(() => ({}));
      throw new Error(error.error || "Error " + r.status);
    }
    // Lectura en streaming: el texto aparece mientras la IA lo escribe.
    const lector = r.body.getReader();
    const decodificador = new TextDecoder();
    while (true) {
      const { done, value } = await lector.read();
      if (done) break;
      respuesta += decodificador.decode(value, { stream: true });
      burbuja.innerHTML = formatoSimple(respuesta);
      $("chat-mensajes").scrollTop = $("chat-mensajes").scrollHeight;
    }
    Lupa.historial.push({ role: "user", content: pregunta }, { role: "assistant", content: respuesta });
  } catch (error) {
    burbuja.textContent = "⚠️ " + error.message;
  } finally {
    burbuja.classList.remove("escribiendo");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  crearChat();
  consultarEstadoIA();
});
