// =========================================================
// Lupa Legal - OCR (reconocimiento óptico de caracteres)
// Para PDF escaneados (fotocopias) e imágenes: convierte la imagen en texto.
//   - pdf.js (Mozilla) dibuja cada página del PDF como imagen.
//   - Tesseract.js lee el texto de la imagen, en español.
// Todo ocurre en el navegador: el documento NO se envía a ningún servidor externo
// (solo se descargan las librerías y el modelo de idioma la primera vez).
// =========================================================

const OCR_LIBRERIAS = {
  pdfjs: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js",
  pdfjsWorker: "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js",
  tesseract: "https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js",
};

function cargarScript(url) {
  return new Promise((resolver, rechazar) => {
    if (document.querySelector(`script[src="${url}"]`)) return resolver();
    const s = document.createElement("script");
    s.src = url;
    s.onload = resolver;
    s.onerror = () => rechazar(new Error("No se pudo descargar " + url + ". ¿Hay conexión a internet?"));
    document.head.appendChild(s);
  });
}

// Convierte un PDF en una lista de imágenes (canvas), una por página.
async function pdfAImagenes(archivo, alAvanzar) {
  await cargarScript(OCR_LIBRERIAS.pdfjs);
  window.pdfjsLib.GlobalWorkerOptions.workerSrc = OCR_LIBRERIAS.pdfjsWorker;
  const datos = new Uint8Array(await archivo.arrayBuffer());
  const pdf = await window.pdfjsLib.getDocument({ data: datos }).promise;
  const paginas = [];
  for (let n = 1; n <= pdf.numPages; n++) {
    alAvanzar(`Preparando página ${n} de ${pdf.numPages}…`, 0);
    const pagina = await pdf.getPage(n);
    const vista = pagina.getViewport({ scale: 2 }); // más escala = mejor lectura
    const canvas = document.createElement("canvas");
    canvas.width = vista.width;
    canvas.height = vista.height;
    await pagina.render({ canvasContext: canvas.getContext("2d"), viewport: vista }).promise;
    paginas.push(canvas);
  }
  return paginas;
}

// Lee el texto de un PDF escaneado o de una imagen. alAvanzar(mensaje, porcentaje)
async function leerConOCR(archivo, alAvanzar) {
  alAvanzar("Descargando el lector de texto (OCR)…", 0);
  await cargarScript(OCR_LIBRERIAS.tesseract);

  const esPDF = archivo.name.toLowerCase().endsWith(".pdf");
  const imagenes = esPDF ? await pdfAImagenes(archivo, alAvanzar) : [archivo];

  let paginaActual = 1;
  const worker = await window.Tesseract.createWorker("spa", 1, {
    logger: (m) => {
      if (m.status === "recognizing text") {
        const total = imagenes.length;
        const porcentaje = Math.round(((paginaActual - 1 + m.progress) / total) * 100);
        alAvanzar(`Leyendo página ${paginaActual} de ${total}…`, porcentaje);
      } else if (m.status && m.status.includes("loading")) {
        alAvanzar("Cargando el idioma español…", 0);
      }
    },
  });

  const textos = [];
  for (const imagen of imagenes) {
    const { data } = await worker.recognize(imagen);
    textos.push(data.text.trim());
    paginaActual++;
  }
  await worker.terminate();
  alAvanzar("Lectura terminada", 100);
  return textos.join("\n\n");
}
