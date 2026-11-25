# Nombre: app.py
# Tema: Servidor web (backend) de Lupa Legal
# Objetivo: Conectar la página web (frontend) con los módulos de Python.
#
# Arquitectura (Sesión 9 - Frontend y Backend):
#   Navegador (HTML + CSS + JavaScript)  --HTTP-->  Flask (Python)  -->  reglas.py + tipos_documento.py
#                                                                  -->  plazos.py (calculadora de la EC1)
#                                                                  -->  extraccion.py (PDF, Word, TXT)
#                                                                  -->  anonimizador.py
#                                                                  -->  asistente_ia.py --> Claude
#
# Cómo ejecutarlo:
#   1) Activar el entorno:   source .venv/bin/activate      (Windows: .venv\Scripts\activate)
#   2) Iniciar el servidor:  python app.py
#   3) Abrir en el navegador: http://127.0.0.1:5050

import os

from flask import Flask, Response, jsonify, request, send_from_directory

import anonimizador
import asistente_ia
import extraccion
import plazos
import reglas

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))
CARPETA_WEB = os.path.join(CARPETA_BASE, "web")
CARPETA_EJEMPLOS = os.path.join(CARPETA_BASE, "ejemplos")
LIMITE_CARACTERES = 150000           # aprox. 50 páginas
LIMITE_ARCHIVO = 25 * 1024 * 1024    # 25 MB por archivo subido


def cargar_env(ruta):
    """Lee el archivo .env (CLAVE=valor) y lo carga como variables de entorno.

    Así la clave de API nunca se escribe dentro del código ni se sube a GitHub.
    """
    if not os.path.exists(ruta):
        return
    with open(ruta, encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


cargar_env(os.path.join(CARPETA_BASE, ".env"))

app = Flask(__name__, static_folder=CARPETA_WEB, static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = LIMITE_ARCHIVO


def leer_texto_de_la_peticion():
    """Valida la entrada: debe existir texto y no superar el límite."""
    datos = request.get_json(silent=True) or {}
    texto = str(datos.get("texto", ""))
    if not texto.strip():
        return None, datos, "Pega, sube o carga un documento antes de analizar."
    if len(texto) > LIMITE_CARACTERES:
        return None, datos, "El texto supera el límite de " + str(LIMITE_CARACTERES) + " caracteres."
    return texto, datos, None


# ---------------------------------------------------------------------------
# PÁGINAS
# ---------------------------------------------------------------------------

@app.route("/")
def inicio():
    return send_from_directory(CARPETA_WEB, "index.html")


# ---------------------------------------------------------------------------
# API GENERAL
# ---------------------------------------------------------------------------

@app.route("/api/estado")
def estado():
    """Indica a la página si la IA está disponible y con qué proveedor."""
    info = asistente_ia.info_ia()
    info["reglas"] = sum(len(c["reglas"]) for c in reglas.CONFIG_TIPOS.values())
    return jsonify(info)


@app.route("/api/reglas")
def listar_reglas():
    """Publica las reglas y el prompt (transparencia: se puede ver qué se revisa y por qué)."""
    campos = ["id", "categoria", "titulo", "nivel", "base_legal", "recomendacion"]
    return jsonify({
        "tipos": {
            tipo: {
                "nombre": reglas.tipos_documento.NOMBRES_TIPO[tipo],
                "reglas": [{c: r[c] for c in campos} for r in config["reglas"]],
                "esenciales": [e["nombre"] for e in config["esenciales"]],
            }
            for tipo, config in reglas.CONFIG_TIPOS.items()
        },
        "prompt_analisis": asistente_ia.PROMPT_ANALISIS,
        "prompt_chat": asistente_ia.PROMPT_CHAT,
        "version_plantilla": asistente_ia.VERSION_PLANTILLA,
    })


# ---------------------------------------------------------------------------
# DOCUMENTOS: ejemplos, subida de archivos y análisis
# ---------------------------------------------------------------------------

NOMBRES_EJEMPLOS = {
    "contrato_de_arrendamiento.txt": "Contrato de arrendamiento (con cláusulas abusivas)",
    "contrato_de_arrendamiento.pdf": "Contrato de arrendamiento · PDF digital",
    "contrato_de_locacion_de_servicios.txt": "Contrato de locación de servicios (equilibrado)",
    "casacion_penal.txt": "Casación penal (Corte Suprema)",
    "casacion_penal_escaneada.pdf": "Casación penal · PDF fotocopiado (OCR)",
    "resolucion_auto_civil.txt": "Auto civil que declara improcedente la demanda",
    "demanda_de_alimentos.txt": "Demanda de alimentos (escrito)",
}


@app.route("/api/ejemplos")
def listar_ejemplos():
    lista = []
    for archivo in sorted(os.listdir(CARPETA_EJEMPLOS)):
        if archivo.endswith((".txt", ".pdf")):
            nombre = NOMBRES_EJEMPLOS.get(archivo, archivo.rsplit(".", 1)[0].replace("_", " ").capitalize())
            lista.append({"archivo": archivo, "nombre": nombre})
    lista.sort(key=lambda e: list(NOMBRES_EJEMPLOS).index(e["archivo"]) if e["archivo"] in NOMBRES_EJEMPLOS else 99)
    return jsonify(lista)


@app.route("/ejemplos/<nombre>")
def descargar_ejemplo(nombre):
    # Solo se entregan archivos que estén en la carpeta ejemplos (evita leer otros archivos).
    if nombre not in os.listdir(CARPETA_EJEMPLOS):
        return jsonify({"error": "Ejemplo no encontrado."}), 404
    return send_from_directory(CARPETA_EJEMPLOS, nombre)


@app.route("/api/extraer", methods=["POST"])
def extraer():
    """Recibe un archivo (PDF, Word, TXT o imagen) y devuelve su texto."""
    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename:
        return jsonify({"error": "No se recibió ningún archivo."}), 400
    try:
        resultado = extraccion.extraer_texto(archivo.filename, archivo.read())
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "No se pudo leer el archivo. ¿Está dañado o protegido con contraseña?"}), 400
    return jsonify(resultado)


@app.errorhandler(413)
def archivo_muy_grande(_):
    return jsonify({"error": "El archivo supera el límite de 25 MB."}), 413


@app.route("/api/analizar", methods=["POST"])
def analizar():
    """Análisis por reglas: rápido, gratuito, sin internet y 100% explicable."""
    texto, datos, error = leer_texto_de_la_peticion()
    if error:
        return jsonify({"error": error}), 400
    return jsonify(reglas.analizar_documento(texto, datos.get("tipo", "auto")))


@app.route("/api/anonimizar", methods=["POST"])
def vista_previa_anonimizada():
    """Muestra al usuario exactamente qué se enviaría a la IA."""
    texto, _, error = leer_texto_de_la_peticion()
    if error:
        return jsonify({"error": error}), 400
    anonimo, resumen = anonimizador.anonimizar(texto)
    return jsonify({"texto": anonimo, "ocultos": resumen})


@app.route("/api/analizar-ia", methods=["POST"])
def analizar_ia():
    """Segunda opinión con Claude."""
    texto, datos, error = leer_texto_de_la_peticion()
    if error:
        return jsonify({"error": error}), 400

    anonimizar = bool(datos.get("anonimizar", True))
    ocultos = {}
    texto_para_ia = texto
    if anonimizar:
        texto_para_ia, ocultos = anonimizador.anonimizar(texto)

    informe = reglas.analizar_documento(texto_para_ia, datos.get("tipo", "auto"))
    try:
        resultado = asistente_ia.analizar_con_ia(texto_para_ia, informe, anonimizar)
    except asistente_ia.ErrorIA as e:
        return jsonify({"error": str(e)}), 503
    resultado["datos_ocultos"] = ocultos
    return jsonify(resultado)


# ---------------------------------------------------------------------------
# PLAZOS (calculadora heredada y mejorada de la EC1)
# ---------------------------------------------------------------------------

@app.route("/api/plazos/catalogo")
def catalogo_plazos():
    return jsonify(plazos.catalogo())


@app.route("/api/plazos/calcular", methods=["POST"])
def calcular_plazo():
    datos = request.get_json(silent=True) or {}
    extra = {}
    for item in datos.get("inhabiles", []) or []:
        try:
            fecha = plazos.texto_a_fecha(item.get("fecha", ""))
            extra[fecha.strftime("%d/%m/%Y")] = str(item.get("motivo") or "Día inhábil indicado por el usuario")[:80]
        except (ValueError, AttributeError):
            continue
    try:
        resultado = plazos.calcular_plazo(
            str(datos.get("recurso", "")),
            str(datos.get("fecha", "")),
            str(datos.get("notificacion", "fisica")),
            inhabiles_extra=extra,
            plazo_manual=datos.get("plazo_manual"),
        )
    except (ValueError, TypeError) as error:
        return jsonify({"error": str(error)}), 400
    return jsonify(resultado)


# ---------------------------------------------------------------------------
# CHATBOT
# ---------------------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    """Chatbot: responde en streaming (texto que va apareciendo)."""
    datos = request.get_json(silent=True) or {}
    pregunta = str(datos.get("pregunta", "")).strip()
    if not pregunta:
        return jsonify({"error": "Escribe una pregunta."}), 400
    if len(pregunta) > 2000:
        return jsonify({"error": "La pregunta es demasiado larga."}), 400
    if not asistente_ia.ia_disponible():
        return jsonify({"error": "La IA no está disponible: inicia sesión en Claude Code o agrega ANTHROPIC_API_KEY en .env."}), 503

    texto = str(datos.get("texto", ""))[:LIMITE_CARACTERES]
    anonimizar = bool(datos.get("anonimizar", True))
    if anonimizar and texto:
        texto, _ = anonimizador.anonimizar(texto)
    historial = datos.get("historial", [])
    if not isinstance(historial, list):
        historial = []
    calculo = datos.get("calculo_plazo")
    if not isinstance(calculo, dict):
        calculo = None

    generador = asistente_ia.responder_chat(texto, historial, pregunta, anonimizar, calculo)
    return Response(generador, mimetype="text/plain; charset=utf-8",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", "5050"))
    info = asistente_ia.info_ia()
    print("Lupa Legal en http://127.0.0.1:" + str(puerto))
    print("IA:", info["nombre_proveedor"] if info["disponible"] else "no disponible (inicia sesión en Claude Code o usa .env)")
    app.run(host="127.0.0.1", port=puerto, debug=False, threaded=True)
