# Nombre: extraccion.py
# Tema: Leer documentos en distintos formatos (TXT, PDF y Word)
# Objetivo: Obtener el texto de un archivo subido para poder analizarlo.
#
# Conexión con el curso (Semana 4 y ejemplos avanzados del repositorio python-intro):
#   - Leer archivos de texto con open().
#   - pypdf, la misma librería de 07-ejemplos_avanzados/05-unir-pdfs.py, para leer PDF.
#   - Un archivo .docx es en realidad un ZIP con XML adentro: lo abrimos con zipfile.
#
# PDF escaneado (fotocopia): no tiene texto, solo imágenes. En ese caso devolvemos
# "necesita_ocr": True y la página hace OCR (reconocimiento óptico de caracteres)
# en el navegador con Tesseract.

import io
import re
import zipfile

from pypdf import PdfReader

# Si una página tiene menos caracteres que esto, se considera escaneada.
MINIMO_CARACTERES_POR_PAGINA = 40


def extraer_de_txt(contenido):
    for codificacion in ("utf-8", "latin-1"):
        try:
            return contenido.decode(codificacion)
        except UnicodeDecodeError:
            continue
    return contenido.decode("utf-8", errors="ignore")


def extraer_de_docx(contenido):
    with zipfile.ZipFile(io.BytesIO(contenido)) as archivo_zip:
        xml = archivo_zip.read("word/document.xml").decode("utf-8")
    xml = re.sub(r"<w:tab/>", "\t", xml)
    xml = re.sub(r"</w:p>", "\n", xml)          # cada párrafo termina en salto de línea
    texto = re.sub(r"<[^>]+>", "", xml)           # quitamos las etiquetas XML
    for entidad, caracter in (("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")):
        texto = texto.replace(entidad, caracter)
    return texto


def extraer_de_pdf(contenido):
    lector = PdfReader(io.BytesIO(contenido))
    paginas = []
    for pagina in lector.pages:
        paginas.append(pagina.extract_text() or "")
    return paginas


def extraer_texto(nombre_archivo, contenido):
    """Devuelve un diccionario con el texto y cómo se obtuvo."""
    nombre = nombre_archivo.lower()

    if nombre.endswith(".txt"):
        return {"texto": extraer_de_txt(contenido), "metodo": "Archivo de texto", "paginas": None, "necesita_ocr": False}

    if nombre.endswith(".docx"):
        return {"texto": extraer_de_docx(contenido), "metodo": "Documento Word (.docx)", "paginas": None, "necesita_ocr": False}

    if nombre.endswith(".pdf"):
        paginas = extraer_de_pdf(contenido)
        total = sum(len(p.strip()) for p in paginas)
        escaneado = total < MINIMO_CARACTERES_POR_PAGINA * max(1, len(paginas))
        texto = "\n\n".join(p.strip() for p in paginas)
        return {
            "texto": "" if escaneado else texto,
            "metodo": "PDF escaneado: requiere OCR" if escaneado else "PDF con texto (pypdf)",
            "paginas": len(paginas),
            "necesita_ocr": escaneado,
        }

    if nombre.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return {"texto": "", "metodo": "Imagen: requiere OCR", "paginas": 1, "necesita_ocr": True}

    raise ValueError("Formato no soportado. Use PDF, Word (.docx), TXT o una imagen (JPG/PNG).")
