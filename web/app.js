// =========================================================
// Lupa Legal - página del analizador (frontend)
// El navegador NO decide nada jurídico: envía el texto al backend (Python)
// y muestra la respuesta. Así la lógica queda en Python, como en clase.
// =========================================================

const estado = {
  informe: null,          // resultado del análisis por reglas
  textoAnalizado: "",     // texto con el que se hizo el análisis
  recursos: [],           // catálogo de recursos de la calculadora
};

const NIVELES = {
  alto: { nombre: "Alto", color: "#d93838", frase: "Hay puntos importantes que conviene revisar antes de actuar o firmar." },
  medio: { nombre: "Medio", color: "#d98a0b", frase: "Hay aspectos que requieren atención, aunque no necesariamente son graves." },
  bajo: { nombre: "Bajo", color: "#2b7bd6", frase: "No se detectaron alertas importantes con las reglas actuales. Igual revisa el detalle." },
};

// El chatbot recibe el documento cargado como contexto.
window.contextoChat = () => ({ texto: $("contrato").value, anonimizar: $("anonimizar").checked, calculo_plazo: null });

function actualizarContador() {
  const texto = $("contrato").value;
  const palabras = texto.trim() ? texto.trim().split(/\s+/).length : 0;
  $("contador").textContent = `${palabras.toLocaleString("es-PE")} palabras · ${texto.length.toLocaleString("es-PE")} caracteres`;
}

function ponerTexto(texto, origen) {
  $("contrato").value = texto;
  $("origen-texto").textContent = origen ? "· " + origen : "";
  actualizarContador();
}

// ---------- Ejemplos ----------
async function cargarListaEjemplos() {
  try {
    const ejemplos = await pedirJSON("/api/ejemplos");
    for (const e of ejemplos) {
      const opcion = document.createElement("option");
      opcion.value = e.archivo;
      opcion.textContent = (e.archivo.endsWith(".pdf") ? "📕 " : "📄 ") + e.nombre;
      $("selector-ejemplo").appendChild(opcion);
    }
  } catch { /* sin ejemplos */ }
}

async function cargarEjemplo(nombre) {
  const respuesta = await fetch("/ejemplos/" + encodeURIComponent(nombre));
  const blob = await respuesta.blob();
  await procesarArchivo(new File([blob], nombre, { type: blob.type }));
}

$("selector-ejemplo").addEventListener("change", async (evento) => {
  const nombre = evento.target.value;
  if (!nombre) return;
  evento.target.value = "";
  await cargarEjemplo(nombre);
});

// Atajo para la exposición: index.html?ejemplo=casacion_penal.txt carga y analiza ese ejemplo.
const parametrosURL = new URLSearchParams(location.search);
if (parametrosURL.get("ejemplo")) {
  cargarEjemplo(parametrosURL.get("ejemplo")).then(() => {
    if (parametrosURL.get("pestana")) activarPestana(parametrosURL.get("pestana"));
  });
}

// ---------- Subida de archivos (PDF, Word, TXT, imágenes) ----------
function mostrarProgreso(mensaje, porcentaje) {
  $("progreso").hidden = false;
  $("progreso-texto").textContent = mensaje;
  $("barra-progreso").style.width = (porcentaje ?? 0) + "%";
}

async function procesarArchivo(archivo) {
  if (!archivo) return;
  mostrarProgreso("Leyendo " + archivo.name + "…", 5);
  try {
    let texto = "";
    let origen = "";
    if (archivo.name.toLowerCase().endsWith(".txt")) {
      texto = await archivo.text();
      origen = archivo.name;
    } else {
      // El servidor intenta extraer el texto (pypdf para PDF, zipfile para Word).
      const formulario = new FormData();
      formulario.append("archivo", archivo);
      const r = await fetch("/api/extraer", { method: "POST", body: formulario });
      const datos = await r.json();
      if (!r.ok) throw new Error(datos.error || "No se pudo leer el archivo.");

      if (datos.necesita_ocr) {
        // Fotocopia o imagen: se lee con OCR en el navegador.
        mostrarProgreso("El documento es una imagen o fotocopia: aplicando OCR…", 0);
        texto = await leerConOCR(archivo, mostrarProgreso);
        origen = archivo.name + " · leído con OCR (revisa posibles errores de lectura)";
      } else {
        texto = datos.texto;
        origen = archivo.name + " · " + datos.metodo + (datos.paginas ? ` · ${datos.paginas} página(s)` : "");
      }
    }
    if (!texto.trim()) throw new Error("No se encontró texto en el archivo.");
    ponerTexto(texto, origen);
    $("progreso").hidden = true;
    await analizarConReglas();
  } catch (error) {
    mostrarProgreso("⚠️ " + error.message, 0);
  }
}

$("archivo").addEventListener("change", (e) => {
  procesarArchivo(e.target.files[0]);
  e.target.value = "";
});

// Arrastrar y soltar
const zona = $("zona-archivo");
["dragenter", "dragover"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.add("encima"); }));
["dragleave", "drop"].forEach((t) => zona.addEventListener(t, (e) => { e.preventDefault(); zona.classList.remove("encima"); }));
zona.addEventListener("drop", (e) => procesarArchivo(e.dataTransfer.files[0]));

$("limpiar").addEventListener("click", () => {
  ponerTexto("", "");
  $("contrato").focus();
});
$("contrato").addEventListener("input", actualizarContador);

// ---------- Análisis por reglas ----------
$("analizar").addEventListener("click", analizarConReglas);
$("tipo-documento").addEventListener("change", () => { if ($("contrato").value.trim()) analizarConReglas(); });

async function analizarConReglas() {
  const texto = $("contrato").value;
  const boton = $("analizar");
  boton.disabled = true;
  boton.textContent = "Analizando…";
  try {
    const informe = await pedirJSON("/api/analizar", { texto, tipo: $("tipo-documento").value });
    estado.informe = informe;
    estado.textoAnalizado = texto;
    mostrarInforme(informe, texto);
    if (window.innerWidth < 920) $("titulo-resultado").scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    alert(error.message);
  } finally {
    boton.disabled = false;
    boton.textContent = "🔍 Analizar documento";
  }
}

function mostrarInforme(informe, texto) {
  $("vacio").hidden = true;
  $("resultado").hidden = false;
  $("imprimir").hidden = false;

  const nivel = NIVELES[informe.semaforo];
  $("arco").style.strokeDashoffset = 389.6 * (1 - informe.indice_riesgo / 100);
  $("arco").style.stroke = nivel.color;
  $("indice").textContent = informe.indice_riesgo;
  $("etiqueta-riesgo").textContent = "Nivel de atención " + nivel.nombre.toLowerCase();
  $("etiqueta-riesgo").className = "etiqueta-riesgo " + informe.semaforo + "-bg";
  $("frase-riesgo").textContent = nivel.frase;
  $("etiqueta-tipo").textContent = "📂 " + informe.tipo_nombre + ($("tipo-documento").value === "auto" ? " (detectado)" : "");
  $("etiqueta-materia").textContent = "🏛️ Materia: " + informe.materia;

  const faltantes = informe.clausulas_esenciales.filter((c) => !c.presente).length;
  $("conteos").innerHTML = `
    <span class="chip alto-bg">${informe.conteo.alto} alto</span>
    <span class="chip medio-bg">${informe.conteo.medio} medio</span>
    <span class="chip bajo-bg">${informe.conteo.bajo} bajo</span>
    <span class="chip ${faltantes ? "alto-bg" : "ok-bg"}">${faltantes} elementos esenciales faltantes</span>
    <span class="chip">${informe.reglas_evaluadas} reglas evaluadas</span>`;

  document.querySelectorAll("#filtros .chip").forEach((c) => c.classList.toggle("activo", c.dataset.nivel === "todos"));
  mostrarAlertas("todos");
  mostrarFicha(informe);
  mostrarTextoResaltado(texto, informe);
  mostrarChecklist(informe);
  mostrarDatosClave(informe.datos_clave);
  if (informe.tipo === "resolucion") activarPestana("panel-ficha");
  else activarPestana("panel-alertas");
}

function mostrarAlertas(filtro) {
  const lista = $("lista-alertas");
  const alertas = estado.informe.alertas.filter((a) => filtro === "todos" || a.nivel === filtro);
  if (!alertas.length) {
    lista.innerHTML = `<p class="vacio" style="padding:16px">No hay alertas ${filtro === "todos" ? "" : "de nivel " + filtro}.</p>`;
    return;
  }
  lista.innerHTML = alertas.map((a) => `
    <article class="alerta ${a.nivel}">
      <div class="cabecera">
        <h4>${escaparHTML(a.titulo)}</h4>
        <span class="insignia ${a.nivel}-bg">${a.nivel}</span>
      </div>
      <div class="meta">${a.id} · ${escaparHTML(a.categoria)} · ${escaparHTML(a.clausula)}${a.apariciones > 1 ? ` · ${a.apariciones} apariciones` : ""}</div>
      <blockquote class="cita">“${escaparHTML(a.fragmento)}”</blockquote>
      <p><strong>¿Por qué revisarlo?</strong> ${escaparHTML(a.explicacion)}</p>
      <p><strong>Recomendación:</strong> ${escaparHTML(a.recomendacion)}</p>
      <p class="legal">📚 Referencia: ${escaparHTML(a.base_legal)}</p>
      <button class="enlace no-imprimir" data-inicio="${a.posiciones[0].inicio}">Ver en el texto →</button>
    </article>`).join("");
}

$("filtros").addEventListener("click", (evento) => {
  const chip = evento.target.closest(".chip");
  if (!chip) return;
  document.querySelectorAll("#filtros .chip").forEach((c) => c.classList.toggle("activo", c === chip));
  mostrarAlertas(chip.dataset.nivel);
});

$("lista-alertas").addEventListener("click", (evento) => {
  const enlace = evento.target.closest(".enlace");
  if (!enlace) return;
  activarPestana("panel-texto");
  const marca = document.querySelector(`mark[data-inicio="${enlace.dataset.inicio}"]`);
  if (marca) {
    marca.scrollIntoView({ behavior: "smooth", block: "center" });
    marca.classList.remove("destello");
    void marca.offsetWidth;
    marca.classList.add("destello");
  }
});

// ---------- Ficha del documento y plazos ----------
function nombreRecurso(id) {
  const r = estado.recursos.find((x) => x.id === id);
  return r ? `${r.nombre} (${r.materia}) · ${r.plazo} días hábiles · ${r.base_legal}` : id;
}

function mostrarFicha(informe) {
  let html = "";
  if (informe.ficha) {
    const f = informe.ficha;
    const fila = (etiqueta, valor) => valor ? `<tr><th>${etiqueta}</th><td>${escaparHTML(valor)}</td></tr>` : "";
    html += `<h3 style="margin-top:0">Ficha de la resolución</h3>
      <div class="tabla-scroll"><table class="ficha">
        ${fila("Número", f.numero)}${fila("Órgano", f.organo)}${fila("Instancia", f.instancia)}
        ${fila("Clase", f.clase)}${fila("Fecha", f.fecha)}${fila("Materia", f.materia)}
        ${f.sentidos.length ? `<tr><th>Sentido</th><td>${f.sentidos.map((s) => `<span class="chip">${escaparHTML(s)}</span>`).join(" ")}</td></tr>` : ""}
      </table></div>
      ${f.decision ? `<h4>Parte resolutiva</h4><blockquote class="cita" style="font-style:normal">${escaparHTML(f.decision)}</blockquote>` : ""}`;

    html += `<h3>Recursos que podrían proceder</h3>`;
    if (informe.nota_recursos) html += `<div class="aviso">ℹ️ ${escaparHTML(informe.nota_recursos)}</div>`;
    html += informe.recursos_sugeridos.map((r) => `
      <div class="recurso-sugerido">
        <div><strong>${escaparHTML(nombreRecurso(r.id))}</strong><br><small>${escaparHTML(r.motivo)}</small></div>
        <a class="boton primario pequeno" href="plazos.html?recurso=${encodeURIComponent(r.id)}">📅 Calcular plazo</a>
      </div>`).join("");
    if (!informe.recursos_sugeridos.length && !informe.nota_recursos) html += "<p><small>No se identificaron recursos.</small></p>";
  } else {
    html += `<p>Documento identificado como <strong>${escaparHTML(informe.tipo_nombre)}</strong> · materia: <strong>${escaparHTML(informe.materia)}</strong>.</p>`;
  }

  const plazosTexto = informe.datos_clave.plazos;
  html += `<h3>Plazos mencionados en el documento</h3>`;
  html += plazosTexto.length
    ? `<ul>${plazosTexto.map((p) => `<li>${escaparHTML(p)}</li>`).join("")}</ul>`
    : "<p><small>No se encontraron plazos expresos.</small></p>";
  html += `<p><a class="boton claro pequeno" href="plazos.html">📅 Abrir la Calculadora de plazos</a></p>`;
  $("ficha").innerHTML = html;
}

function mostrarTextoResaltado(texto, informe) {
  const tramos = [];
  for (const a of informe.alertas) {
    for (const p of a.posiciones) tramos.push({ ...p, clase: a.nivel, titulo: a.titulo });
  }
  for (const c of informe.campos_vacios) tramos.push({ inicio: c.inicio, fin: c.fin, clase: "vacio", titulo: "Dato por completar" });
  tramos.sort((x, y) => x.inicio - y.inicio);

  let html = "";
  let cursor = 0;
  for (const t of tramos) {
    if (t.inicio < cursor) continue;
    html += escaparHTML(texto.slice(cursor, t.inicio));
    html += `<mark class="${t.clase}" data-inicio="${t.inicio}" title="${escaparHTML(t.titulo)}">${escaparHTML(texto.slice(t.inicio, t.fin))}</mark>`;
    cursor = t.fin;
  }
  html += escaparHTML(texto.slice(cursor));
  $("texto-resaltado").innerHTML = html;
}

function mostrarChecklist(informe) {
  $("lista-esenciales").innerHTML = informe.clausulas_esenciales.map((c) => `
    <li><span class="${c.presente ? "marca-ok" : "marca-no"}">${c.presente ? "✓" : "✗"}</span>
      ${escaparHTML(c.nombre)}${c.presente ? "" : " — <em>no se encontró</em>"}</li>`).join("");
  const vacios = informe.campos_vacios;
  $("campos-vacios").hidden = !vacios.length;
  if (vacios.length) {
    $("campos-vacios").innerHTML = `⚠️ Hay <strong>${vacios.length}</strong> espacio(s) sin completar (p. ej. <code>${escaparHTML(vacios[0].texto)}</code>).`;
  }
}

function mostrarDatosClave(datos) {
  const bloques = [["💰 Montos", datos.montos], ["⏳ Plazos", datos.plazos], ["📅 Fechas", datos.fechas], ["％ Porcentajes", datos.porcentajes]];
  $("datos-clave").innerHTML = bloques.map(([titulo, items]) => `
    <div class="dato"><h5>${titulo}</h5>
      ${items.length ? `<ul>${items.map((i) => `<li>${escaparHTML(i)}</li>`).join("")}</ul>` : `<small>No se encontraron.</small>`}
    </div>`).join("");
}

// ---------- Pestañas ----------
function activarPestana(idPanel) {
  document.querySelectorAll(".pestanas button").forEach((b) => b.classList.toggle("activo", b.dataset.panel === idPanel));
  document.querySelectorAll(".panel").forEach((p) => p.classList.toggle("activo", p.id === idPanel));
}
document.querySelector(".pestanas").addEventListener("click", (evento) => {
  const boton = evento.target.closest("button");
  if (boton) activarPestana(boton.dataset.panel);
});

$("imprimir").addEventListener("click", () => window.print());

// ---------- Vista previa de anonimización ----------
$("ver-anonimo").addEventListener("click", async (evento) => {
  evento.preventDefault();
  try {
    const datos = await pedirJSON("/api/anonimizar", { texto: $("contrato").value });
    const resumen = Object.entries(datos.ocultos).map(([k, v]) => `${k}: ${v}`).join(", ") || "ningún dato detectado";
    const ventana = window.open("", "_blank");
    ventana.document.write(`<title>Texto que se enviaría a la IA</title><meta charset="utf-8">
      <body style="font-family:system-ui;max-width:900px;margin:24px auto;padding:0 16px">
      <h2>Texto que se enviaría a la IA</h2><p><strong>Datos ocultos:</strong> ${escaparHTML(resumen)}</p>
      <p style="color:#a0521a">⚠️ La anonimización es automática y básica: no oculta nombres ni direcciones. Revísalo antes de enviar.</p>
      <pre style="white-space:pre-wrap;background:#f4f6fb;padding:16px;border-radius:10px">${escaparHTML(datos.texto)}</pre></body>`);
    ventana.document.close();
  } catch (error) {
    alert(error.message);
  }
});

// ---------- Segunda opinión IA ----------
$("analizar-ia").addEventListener("click", async () => {
  const texto = $("contrato").value;
  const contenedor = $("ia-contenido");
  if (!texto.trim()) { alert("Sube, pega o carga un documento antes de analizar."); return; }
  if (!Lupa.iaDisponible) {
    contenedor.innerHTML = `<div class="aviso error">🔑 La IA no está disponible. Inicia sesión en Claude Code (VS Code o la app) o agrega una clave en <code>.env</code>, y reinicia el servidor. El análisis por reglas sí funciona sin IA.</div>`;
    return;
  }
  if (estado.textoAnalizado !== texto) await analizarConReglas();

  const boton = $("analizar-ia");
  boton.disabled = true;
  const inicio = Date.now();
  contenedor.innerHTML = `<div class="cargando"><div class="giro"></div> <span id="ia-espera">La IA está leyendo el documento…</span></div>`;
  const reloj = setInterval(() => {
    const s = Math.round((Date.now() - inicio) / 1000);
    const el = $("ia-espera");
    if (el) el.textContent = `La IA está leyendo el documento… ${s} s (suele tardar entre 15 y 40 s)`;
  }, 1000);
  $("titulo-ia").scrollIntoView({ behavior: "smooth", block: "start" });
  try {
    const r = await pedirJSON("/api/analizar-ia", { texto, anonimizar: $("anonimizar").checked, tipo: $("tipo-documento").value });
    r.segundos = Math.round((Date.now() - inicio) / 1000);
    contenedor.innerHTML = htmlSegundaOpinion(r);
  } catch (error) {
    contenedor.innerHTML = `<div class="aviso error">⚠️ ${escaparHTML(error.message)}</div>`;
  } finally {
    clearInterval(reloj);
    boton.disabled = false;
  }
});

function htmlSegundaOpinion(r) {
  const iconoVeredicto = { confirmada: "✅", matizada: "🟡", descartada: "❌" };
  const orden = { alto: 0, medio: 1, bajo: 2 };
  const hallazgos = [...r.hallazgos].sort((a, b) => orden[a.riesgo] - orden[b.riesgo]);
  const ocultos = Object.entries(r.datos_ocultos || {}).map(([k, v]) => `${k} (${v})`).join(", ");
  const lista = (items) => items.length ? `<ul>${items.map((i) => `<li>${escaparHTML(i)}</li>`).join("")}</ul>` : "<p><small>Ninguno.</small></p>";

  return `
    <div class="aviso">🤖 <strong>Contenido generado por IA.</strong> Úsalo como apoyo: verifica las citas, normas y plazos antes de decidir.</div>
    <p><strong>Tipo de documento:</strong> ${escaparHTML(r.tipo_documento)}</p>
    <p>${escaparHTML(r.resumen)}</p>
    ${r.partes.length ? `<p><strong>Partes:</strong> ${r.partes.map((p) => `${escaparHTML(p.rol)} (${escaparHTML(p.posicion)})`).join(" · ")}</p>` : ""}

    ${r.plazos_y_acciones.length ? `<h3>⏰ Acciones con plazo</h3>
      <div class="tabla-scroll"><table><thead><tr><th>Acción</th><th>Plazo</th><th>Base legal</th></tr></thead><tbody>
      ${r.plazos_y_acciones.map((p) => `<tr><td>${escaparHTML(p.accion)}</td><td>${escaparHTML(p.plazo)}</td><td>${escaparHTML(p.base_legal)}</td></tr>`).join("")}
      </tbody></table></div>
      <p><a class="boton claro pequeno" href="plazos.html">📅 Calcular la fecha exacta en la Calculadora de plazos</a></p>` : ""}

    <h3>Hallazgos (${hallazgos.length})</h3>
    ${hallazgos.map((h) => `
      <div class="hallazgo">
        <h4><span class="insignia ${h.riesgo}-bg">${h.riesgo}</span> ${escaparHTML(h.seccion)}</h4>
        <blockquote class="cita">“${escaparHTML(h.texto_citado)}”</blockquote>
        <p><strong>Problema:</strong> ${escaparHTML(h.problema)}</p>
        <p><strong>Recomendación:</strong> ${escaparHTML(h.recomendacion)}</p>
        <p class="legal" style="font-size:.8rem;color:#5b6478">📚 ${escaparHTML(h.fundamento)}</p>
      </div>`).join("")}

    <div class="columnas-ia">
      <div>
        <h3>Revisión de las alertas de las reglas</h3>
        ${r.validacion_reglas.length ? r.validacion_reglas.map((v) => `
          <div class="validacion"><span>${iconoVeredicto[v.veredicto] || "•"}</span>
            <span><strong>${escaparHTML(v.id_regla)} · ${escaparHTML(v.veredicto)}</strong><br>${escaparHTML(v.comentario)}</span></div>`).join("") : "<p><small>Sin alertas que revisar.</small></p>"}
      </div>
      <div>
        <h3>Lo que falta o hay que verificar</h3>
        ${lista(r.elementos_faltantes)}
        <h3>Preguntas para el cliente</h3>
        ${lista(r.preguntas_para_el_cliente)}
      </div>
    </div>

    <h3>Conclusión</h3>
    <p style="white-space:pre-line">${escaparHTML(r.conclusion)}</p>
    <div class="meta-ia">${escaparHTML(r.proveedor)} · modelo ${escaparHTML(r.modelo)} · plantilla ${escaparHTML(r.plantilla)} · ${r.segundos} s ·
      ${ocultos ? "Datos ocultos antes del envío: " + escaparHTML(ocultos) : "Sin anonimización"}</div>`;
}

// ---------- Inicio ----------
cargarListaEjemplos();
actualizarContador();
pedirJSON("/api/plazos/catalogo").then((c) => { estado.recursos = c.recursos; }).catch(() => {});
