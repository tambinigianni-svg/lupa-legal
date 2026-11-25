// =========================================================
// Lupa Legal - Calculadora de plazos (frontend)
// El cálculo lo hace Python (plazos.py). Aquí solo se piden los datos y se dibuja el resultado.
// =========================================================

const calc = { catalogo: null, inhabiles: [], ultimo: null };
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

// El chatbot recibe el último cálculo como contexto (así no "inventa" fechas).
window.contextoChat = () => ({
  texto: "",
  anonimizar: true,
  calculo_plazo: calc.ultimo ? {
    recurso: calc.ultimo.recurso.nombre, materia: calc.ultimo.recurso.materia, plazo: calc.ultimo.recurso.plazo + " " + calc.ultimo.unidad_texto,
    base_legal: calc.ultimo.recurso.base_legal, fecha_notificacion: calc.ultimo.fecha_base, tipo_notificacion: calc.ultimo.tipo_notificacion,
    inicio_computo: calc.ultimo.inicio, vencimiento: calc.ultimo.vencimiento, estado: calc.ultimo.estado.texto,
  } : null,
});

const aISO = (dmy) => { const [d, m, a] = dmy.split("/"); return `${a}-${m}-${d}`; };
const aDMY = (iso) => { const [a, m, d] = iso.split("-"); return `${d}/${m}/${a}`; };

async function iniciar() {
  calc.catalogo = await pedirJSON("/api/plazos/catalogo");
  $("materia").innerHTML = calc.catalogo.materias.map((m) => `<option>${escaparHTML(m)}</option>`).join("") + `<option value="Otro">Otro (plazo manual)</option>`;
  const hoy = new Date(); // fecha local (no UTC), para que en la noche no salte al día siguiente
  $("fecha").value = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;

  // Si viene desde el analizador: plazos.html?recurso=civ-apel-auto
  const params = new URLSearchParams(location.search);
  const id = params.get("recurso");
  const recurso = calc.catalogo.recursos.find((r) => r.id === id);
  if (recurso) $("materia").value = recurso.materia;
  llenarRecursos(recurso ? recurso.id : null);
  if (params.get("fecha")) $("fecha").value = aISO(params.get("fecha"));
  if (params.get("notificacion") === "electronica") document.querySelector("input[value=electronica]").checked = true;
  // Atajo para la exposición: ...&calcular=1 calcula de inmediato.
  if (params.get("calcular") && params.get("fecha")) $("form-plazo").requestSubmit();
}

function llenarRecursos(seleccionado) {
  const materia = $("materia").value;
  if (materia === "Otro") {
    $("recurso").innerHTML = `<option value="manual">Plazo personalizado en días hábiles</option>`;
  } else {
    $("recurso").innerHTML = calc.catalogo.recursos
      .filter((r) => r.materia === materia)
      .map((r) => `<option value="${r.id}">${escaparHTML(r.nombre)} — ${r.plazo} ${r.unidad === "habiles" ? "días hábiles" : r.unidad === "naturales" ? "días calendario" : "meses"}</option>`)
      .join("");
  }
  if (seleccionado) $("recurso").value = seleccionado;
  actualizarFormulario();
}

function actualizarFormulario() {
  const id = $("recurso").value;
  const recurso = calc.catalogo.recursos.find((r) => r.id === id);
  const esInvestigacion = recurso && recurso.unidad !== "habiles";
  $("caja-manual").hidden = id !== "manual";
  $("caja-notificacion").hidden = esInvestigacion;
  $("etiqueta-fecha").textContent = esInvestigacion ? "Fecha de inicio (disposición fiscal)" : "Fecha de notificación";
  $("base-legal").textContent = recurso ? "📚 " + recurso.base_legal : "";
}

$("materia").addEventListener("change", () => llenarRecursos());
$("recurso").addEventListener("change", actualizarFormulario);

// ---------- Días inhábiles adicionales ----------
function dibujarInhabiles() {
  $("lista-inhabiles").innerHTML = calc.inhabiles.map((d, i) =>
    `<span class="chip">${d.fecha}${d.motivo ? " · " + escaparHTML(d.motivo) : ""} <button type="button" data-i="${i}" style="border:0;background:none;cursor:pointer">✕</button></span>`).join("");
}
$("agregar-inhabil").addEventListener("click", () => {
  if (!$("inhabil-fecha").value) return;
  calc.inhabiles.push({ fecha: aDMY($("inhabil-fecha").value), motivo: $("inhabil-motivo").value.trim() });
  $("inhabil-fecha").value = "";
  $("inhabil-motivo").value = "";
  dibujarInhabiles();
});
$("lista-inhabiles").addEventListener("click", (e) => {
  const b = e.target.closest("button[data-i]");
  if (!b) return;
  calc.inhabiles.splice(Number(b.dataset.i), 1);
  dibujarInhabiles();
});

// ---------- Cálculo ----------
$("form-plazo").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const r = await pedirJSON("/api/plazos/calcular", {
      recurso: $("recurso").value,
      fecha: aDMY($("fecha").value),
      notificacion: document.querySelector("input[name=notificacion]:checked").value,
      inhabiles: calc.inhabiles,
      plazo_manual: $("plazo-manual").value,
    });
    calc.ultimo = r;
    dibujarResultado(r);
  } catch (error) {
    $("resultado-plazo").innerHTML = `<div class="aviso error">⚠️ ${escaparHTML(error.message)}</div>`;
  }
});

$("resultado-plazo").addEventListener("click", (e) => {
  if (e.target.id !== "ejemplo-ec1") return;
  $("materia").value = "Penal";
  llenarRecursos("pen-casacion");
  $("fecha").value = "2026-07-24";
  document.querySelector("input[value=fisica]").checked = true;
  $("form-plazo").requestSubmit();
});

function dibujarResultado(r) {
  $("acciones-plazo").hidden = false;
  const [d, m, a] = r.vencimiento.split("/");
  let html = `
    <div class="vencimiento">
      <small>${escaparHTML(r.recurso.nombre)} · ${escaparHTML(r.recurso.materia)} · ${r.recurso.plazo} ${escaparHTML(r.unidad_texto)}</small>
      <div class="fecha-grande">Vence el ${r.vencimiento_dia} ${Number(d)} de ${MESES[Number(m) - 1]} de ${a}</div>
      <span class="estado-plazo ${r.estado.codigo}">${escaparHTML(r.estado.texto)}</span>
    </div>
    <div class="resumen-plazo">
      <div class="dato"><h5>${r.tipo_notificacion ? "Notificación" : "Fecha de inicio"}</h5>${r.fecha_base}${r.tipo_notificacion ? " · " + (r.tipo_notificacion === "electronica" ? "electrónica" : "física") : ""}</div>
      <div class="dato"><h5>Primer día del cómputo</h5>${r.inicio}</div>
      <div class="dato"><h5>Último día</h5>${r.vencimiento}</div>
      <div class="dato"><h5>Base legal</h5>${escaparHTML(r.recurso.base_legal)}</div>
    </div>
    <p class="aviso">ℹ️ ${escaparHTML(r.explicacion)}</p>`;

  if (r.detalle.length) {
    html += `<h3>Calendario del cómputo</h3>
      <div class="leyenda"><span><mark style="background:#16224a;color:#fff">notificación</mark></span><span><mark class="bajo">día contado</mark></span>
      <span><mark style="background:#eceef3">no se cuenta</mark></span><span><mark class="alto">feriado / inhábil</mark></span><span><mark style="background:#f2661f;color:#fff">vencimiento</mark></span></div>
      ${dibujarCalendario(r.detalle)}
      <details><summary><strong>Ver el detalle día por día</strong></summary>
      <div class="tabla-scroll"><table><thead><tr><th>Fecha</th><th>Día</th><th>¿Cuenta?</th></tr></thead><tbody>
      ${r.detalle.map((x) => `<tr><td>${x.fecha}</td><td>${x.dia_semana}</td><td>${x.cuenta ? "✅ " : "➖ "}${escaparHTML(x.etiqueta)}</td></tr>`).join("")}
      </tbody></table></div></details>`;
  }
  $("resultado-plazo").innerHTML = html;
  if (window.innerWidth < 920) $("titulo-resultado-plazo").scrollIntoView({ behavior: "smooth" });
}

function dibujarCalendario(detalle) {
  // Agrupa los días por mes y los dibuja en una cuadrícula de lunes a domingo.
  const porMes = {};
  detalle.forEach((x, i) => {
    const [d, m, a] = x.fecha.split("/");
    const clave = `${a}-${m}`;
    (porMes[clave] = porMes[clave] || []).push({ ...x, dia: Number(d), mes: Number(m), anio: Number(a), indice: i });
  });
  let html = "";
  for (const dias of Object.values(porMes)) {
    const primero = new Date(dias[0].anio, dias[0].mes - 1, dias[0].dia);
    const huecos = (primero.getDay() + 6) % 7; // lunes = 0
    html += `<div class="mes-titulo">${MESES[dias[0].mes - 1]} ${dias[0].anio}</div><div class="calendario">`;
    html += ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"].map((n) => `<div class="dia-nombre">${n}</div>`).join("");
    html += `<div class="dia vacio-cal"></div>`.repeat(huecos);
    for (const x of dias) {
      let clase = x.cuenta ? "cuenta" : "no-cuenta";
      if (/feriado|inhábil/.test(x.etiqueta)) clase = "feriado";
      if (x.indice === 0) clase = "notificacion";
      if (x.indice === detalle.length - 1) clase = "final";
      const texto = x.indice === 0 ? "notif." : x.cuenta ? x.etiqueta.replace("Día ", "").split(" de ")[0] : (clase === "feriado" ? "feriado" : "—");
      html += `<div class="dia ${clase}" title="${escaparHTML(x.etiqueta)}"><b>${x.dia}</b>${escaparHTML(texto)}</div>`;
    }
    html += `</div>`;
  }
  return html;
}

// ---------- Calendario (.ics) ----------
$("descargar-ics").addEventListener("click", () => {
  const r = calc.ultimo;
  if (!r) return;
  const [d, m, a] = r.vencimiento.split("/");
  const fecha = `${a}${m}${d}`;
  const ics = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Lupa Legal//Plazos//ES", "BEGIN:VEVENT",
    `UID:${Date.now()}@lupa-legal`, `DTSTAMP:${new Date().toISOString().replace(/[-:]/g, "").slice(0, 15)}Z`,
    `DTSTART;VALUE=DATE:${fecha}`, `SUMMARY:VENCE: ${r.recurso.nombre} (${r.recurso.materia})`,
    `DESCRIPTION:Notificación: ${r.fecha_base}. Inicio del cómputo: ${r.inicio}. ${r.recurso.base_legal}. Cálculo referencial de Lupa Legal.`,
    "BEGIN:VALARM", "TRIGGER:-P1D", "ACTION:DISPLAY", "DESCRIPTION:Vence mañana", "END:VALARM",
    "END:VEVENT", "END:VCALENDAR",
  ].join("\r\n");
  const enlace = document.createElement("a");
  enlace.href = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
  enlace.download = `vencimiento-${fecha}.ics`;
  enlace.click();
});

$("preguntar-ia").addEventListener("click", () => abrirChatCon("Explícame este cálculo de plazo y qué debo tener en cuenta para no perderlo."));

iniciar();
