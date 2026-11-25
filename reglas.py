# Nombre: reglas.py
# Tema: Motor de reglas para revisar contratos
# Objetivo: Leer el texto de un contrato y señalar cláusulas que requieren revisión.
#
# Idea central (pensamiento computacional):
#   ENTRADA  -> texto del contrato
#   PROCESO  -> normalizar texto, buscar patrones de riesgo, verificar cláusulas esenciales
#   SALIDA   -> lista de alertas con nivel de riesgo, explicación, recomendación y base legal
#
# Igual que en la EC1 (plazos penales), los datos están organizados como una
# LISTA DE DICCIONARIOS: cada regla es un registro con claves fijas.
# Así, agregar una regla nueva no exige tocar la lógica: solo se agrega un diccionario.
#
# IMPORTANTE: las referencias legales son orientativas (Código Civil peruano y normas
# conexas). Antes de usarlas en un caso real se debe verificar su vigencia.

import re
import unicodedata

import tipos_documento

# ---------------------------------------------------------------------------
# 1. DATOS: reglas de riesgo (lista de diccionarios)
# ---------------------------------------------------------------------------
# Cada patrón es una "expresión regular" que se busca en el texto normalizado
# (en minúsculas y sin tildes). \s+ significa "uno o más espacios".

REGLAS = [
    {
        "id": "R01",
        "categoria": "Responsabilidad",
        "titulo": "Exoneración o limitación de responsabilidad",
        "nivel": "alto",
        "patrones": [
            r"no\s+(sera|seran|asume|asumira|asumen)\s+(responsable|responsabilidad)",
            r"(exonera|exime|libera)\w*\s+(de\s+)?(toda\s+)?responsabilidad",
            r"sin\s+responsabilidad\s+alguna",
            r"responsabilidad\s+(maxima|total)\s+(se\s+)?limita",
            r"limita\w*\s+(su\s+)?responsabilidad",
        ],
        "explicacion": "La cláusula excluye o recorta la responsabilidad de una de las partes. "
                       "Es nula si cubre dolo o culpa inexcusable, y en contratos por adhesión "
                       "no es válida a favor de quien redactó el contrato.",
        "recomendacion": "Precisar que la limitación no alcanza dolo ni culpa inexcusable y fijar "
                         "un tope razonable y recíproco.",
        "base_legal": "Código Civil, arts. 1328 y 1398",
    },
    {
        "id": "R02",
        "categoria": "Terminación",
        "titulo": "Resolución o terminación unilateral",
        "nivel": "alto",
        "patrones": [
            r"(resolver|rescindir|terminar|dar\s+por\s+terminado|dejar\s+sin\s+efecto)\s+(el\s+)?(presente\s+)?contrato\s+(de\s+manera\s+|en\s+forma\s+)?unilateral",
            r"unilateralmente",
            r"en\s+cualquier\s+momento\s+y\s+sin\s+(expresion\s+de\s+causa|causa|justificacion)",
            r"a\s+su\s+sola\s+(discrecion|decision|voluntad)",
            r"sin\s+expresion\s+de\s+causa",
        ],
        "explicacion": "Una parte puede terminar el contrato sola, sin causa o sin aviso. "
                       "Genera desequilibrio y, en contratos por adhesión, puede ser inválida.",
        "recomendacion": "Exigir causa objetiva, preaviso por escrito (p. ej. 30 días) y que la "
                         "facultad sea recíproca.",
        "base_legal": "Código Civil, arts. 1365, 1398 y 1430",
    },
    {
        "id": "R03",
        "categoria": "Penalidades",
        "titulo": "Penalidad o cláusula penal",
        "nivel": "medio",
        "patrones": [
            r"penalidad",
            r"clausula\s+penal",
            r"\bmulta\b",
            r"indemnizacion\s+(fija|equivalente)",
        ],
        "explicacion": "Hay una pena por incumplimiento. Revisar si es proporcional y si se aplica "
                       "a ambas partes; el juez puede reducirla si es manifiestamente excesiva.",
        "recomendacion": "Verificar monto, tope máximo, reciprocidad y si excluye o no el daño ulterior.",
        "base_legal": "Código Civil, arts. 1341 a 1346",
    },
    {
        "id": "R04",
        "categoria": "Renovación",
        "titulo": "Renovación o prórroga automática",
        "nivel": "medio",
        "patrones": [
            r"(renovara|renueva|prorrogara|prorroga)\w*\s+(de\s+manera\s+|en\s+forma\s+)?automatica",
            r"renovacion\s+automatica",
            r"prorroga\s+automatica",
            r"tacita\s+(reconduccion|renovacion|prorroga)",
        ],
        "explicacion": "El contrato se renueva solo si nadie avisa. Puede atar a una parte por un "
                       "nuevo periodo sin que lo advierta.",
        "recomendacion": "Fijar un plazo de aviso de no renovación y la forma de comunicarlo.",
        "base_legal": "Código Civil, arts. 1398 y 1700 (arrendamiento)",
    },
    {
        "id": "R05",
        "categoria": "Modificación",
        "titulo": "Modificación unilateral de condiciones o precio",
        "nivel": "alto",
        "patrones": [
            r"(podra|puede|se\s+reserva\s+el\s+derecho\s+de)\s+(modificar|variar|cambiar|ajustar|incrementar)",
            r"modificar\w*\s+(las\s+)?(condiciones|tarifas|precios?|terminos)\s+(sin|previa)",
            r"sin\s+(previo\s+)?aviso",
            r"reajust\w+\s+(de\s+manera\s+)?(automatic|unilateral|discrecional)",
        ],
        "explicacion": "Una parte puede cambiar precio o condiciones sin acuerdo de la otra. "
                       "Rompe la obligatoriedad de lo pactado.",
        "recomendacion": "Cualquier cambio debe constar por escrito y firmado por ambas partes; "
                         "los reajustes deben tener fórmula y tope.",
        "base_legal": "Código Civil, art. 1361; Ley 29571, arts. 49-50 (si es de consumo)",
    },
    {
        "id": "R06",
        "categoria": "Derechos",
        "titulo": "Renuncia a derechos o acciones",
        "nivel": "alto",
        "patrones": [
            r"renuncia\w*\s+(expresamente\s+)?a\s+(cualquier|todo|toda|su|sus|interponer|ejercer|reclamar)",
            r"renuncia\w*\s+(expresamente\s+)?(al|a\s+la|a\s+los|a\s+las)\s+(derecho|accion|reclamo|fuero|excepcion)",
            r"no\s+podra\s+(reclamar|interponer|oponer)",
        ],
        "explicacion": "Una parte renuncia de antemano a reclamar o a defenderse. Las renuncias a "
                       "derechos irrenunciables o contrarias al orden público son nulas.",
        "recomendacion": "Eliminar renuncias generales; si se mantienen, que sean específicas y recíprocas.",
        "base_legal": "Código Civil, Título Preliminar art. V y art. 1398",
    },
    {
        "id": "R07",
        "categoria": "Intereses",
        "titulo": "Intereses, moras o capitalización",
        "nivel": "medio",
        "patrones": [
            r"interes\w*\s+(moratorio|compensatorio|convencional)",
            r"capitaliza\w*\s+(de\s+)?intereses",
            r"intereses\s+capitalizables",
            r"\d+(\.\d+)?\s*%\s+(mensual|diario)",
        ],
        "explicacion": "Se pactan intereses. Deben respetar la tasa máxima fijada por el BCRP y no "
                       "puede pactarse capitalización al celebrar el contrato (salvo excepciones).",
        "recomendacion": "Verificar la tasa frente al máximo legal vigente y eliminar capitalización anticipada.",
        "base_legal": "Código Civil, arts. 1243 y 1249",
    },
    {
        "id": "R08",
        "categoria": "Controversias",
        "titulo": "Jurisdicción, arbitraje o sede desfavorable",
        "nivel": "medio",
        "patrones": [
            r"arbitraje",
            r"\barbitr(o|al)\b",
            r"(se\s+someten|sometimiento)\s+a\s+(la\s+)?(competencia|jurisdiccion)",
            r"renuncia\w*\s+al\s+fuero",
            r"jueces\s+y\s+tribunales\s+de",
        ],
        "explicacion": "Define dónde y cómo se resuelven los conflictos. Un arbitraje costoso o una "
                       "sede lejana pueden impedir en la práctica que una parte reclame.",
        "recomendacion": "Revisar sede, costos, institución arbitral y si es razonable para ambas partes.",
        "base_legal": "Código Procesal Civil, art. 25; Decreto Legislativo 1071 (Ley de Arbitraje)",
    },
    {
        "id": "R09",
        "categoria": "Datos personales",
        "titulo": "Tratamiento de datos personales",
        "nivel": "medio",
        "patrones": [
            r"datos\s+personales",
            r"(compartir|transferir|ceder)\w*\s+(sus\s+|los\s+)?(datos|informacion)\s+(personal|a\s+terceros)",
            r"autoriza\w*\s+(el\s+)?(uso|tratamiento)\s+de\s+(sus\s+)?datos",
        ],
        "explicacion": "El contrato trata datos personales. Se requiere consentimiento informado, "
                       "finalidad clara y medidas de seguridad.",
        "recomendacion": "Precisar finalidad, plazo de conservación, destinatarios y derechos ARCO.",
        "base_legal": "Ley 29733, Ley de Protección de Datos Personales",
    },
    {
        "id": "R10",
        "categoria": "Cesión",
        "titulo": "Cesión del contrato sin consentimiento",
        "nivel": "medio",
        "patrones": [
            r"(podra|puede)\s+ceder\w*\s+(su\s+posicion|el\s+contrato|sus\s+derechos)",
            r"ceder\w*\s+.{0,40}sin\s+(necesidad\s+de\s+)?(consentimiento|autorizacion|aprobacion)",
        ],
        "explicacion": "Una parte puede pasar el contrato a un tercero. La cesión de posición "
                       "contractual requiere la conformidad del otro contratante.",
        "recomendacion": "Exigir autorización previa y por escrito de la otra parte.",
        "base_legal": "Código Civil, art. 1435",
    },
    {
        "id": "R11",
        "categoria": "Obligaciones",
        "titulo": "Exclusividad o no competencia",
        "nivel": "medio",
        "patrones": [
            r"exclusividad",
            r"no\s+competencia",
            r"no\s+podra\s+(prestar|contratar|trabajar|dedicarse)",
        ],
        "explicacion": "Restringe la libertad de una parte para contratar con otros. Debe ser "
                       "limitada en tiempo, territorio y actividad.",
        "recomendacion": "Acotar duración, ámbito geográfico y actividad; valorar una compensación.",
        "base_legal": "Código Civil, art. 1354 (libertad contractual) y art. V T.P.",
    },
    {
        "id": "R12",
        "categoria": "Confidencialidad",
        "titulo": "Confidencialidad indefinida o amplia",
        "nivel": "bajo",
        "patrones": [
            r"confidencialidad\s+.{0,60}(indefinid|perpetu|tiempo\s+indeterminado)",
            r"(de\s+manera|en\s+forma|por\s+tiempo)\s+(indefinida|indeterminado|perpetua)",
        ],
        "explicacion": "Una obligación sin plazo final puede ser difícil de cumplir y de controlar.",
        "recomendacion": "Fijar un plazo (p. ej. 2 a 5 años después del término) y excepciones claras.",
        "base_legal": "Código Civil, art. 1354",
    },
    {
        "id": "R13",
        "categoria": "Pago",
        "titulo": "Pagos adelantados, garantías o retenciones",
        "nivel": "bajo",
        "patrones": [
            r"(garantia|deposito)\s+(de|equivalente|por)",
            r"pago\s+(por\s+)?adelantado",
            r"no\s+(sera|seran)\s+(devuelt|reembolsab)",
            r"no\s+reembolsable",
            r"retener\w*\s+(la\s+)?garantia",
        ],
        "explicacion": "Hay dinero entregado por adelantado o en garantía. Revisar cuándo y cómo se devuelve.",
        "recomendacion": "Precisar plazo y condiciones de devolución, y qué descuentos son válidos.",
        "base_legal": "Código Civil, arts. 1361 y 1362 (buena fe)",
    },
    {
        "id": "R14",
        "categoria": "Fuerza mayor",
        "titulo": "Fuerza mayor excluida o asumida por una sola parte",
        "nivel": "medio",
        "patrones": [
            r"(aun|incluso)\s+(en\s+)?(caso|casos)\s+(fortuito|de\s+fuerza\s+mayor)",
            r"asume\w*\s+(el\s+)?riesgo\s+.{0,40}(fuerza\s+mayor|caso\s+fortuito)",
        ],
        "explicacion": "Una parte responde incluso por hechos imprevisibles e irresistibles.",
        "recomendacion": "Definir eventos de fuerza mayor y sus efectos de forma equilibrada.",
        "base_legal": "Código Civil, art. 1315",
    },
]

# Puntos que suma cada alerta al índice de riesgo.
PESO_POR_NIVEL = {"alto": 15, "medio": 8, "bajo": 3}

# ---------------------------------------------------------------------------
# 2. DATOS: cláusulas que todo contrato debería tener (se verifica su AUSENCIA)
# ---------------------------------------------------------------------------
CLAUSULAS_ESENCIALES = [
    {"nombre": "Identificación de las partes", "patrones": [r"\bdni\b", r"\bruc\b", r"documento\s+de\s+identidad", r"carnet\s+de\s+extranjeria"]},
    {"nombre": "Objeto del contrato", "patrones": [r"\bobjeto\b", r"por\s+el\s+presente", r"se\s+obliga\s+a"]},
    {"nombre": "Precio o contraprestación", "patrones": [r"\bprecio\b", r"\brenta\b", r"\bmerced\b", r"contraprestacion", r"honorarios", r"retribucion", r"s/\s*\d", r"us\$\s*\d", r"\bsoles\b", r"\bdolares\b"]},
    {"nombre": "Plazo o vigencia", "patrones": [r"\bplazo\b", r"\bvigencia\b", r"\bduracion\b"]},
    {"nombre": "Forma y oportunidad de pago", "patrones": [r"forma\s+de\s+pago", r"\bpagara\b", r"\bpago\b", r"\babonara\b", r"deposito\s+en\s+(la\s+)?cuenta"]},
    {"nombre": "Resolución o terminación", "patrones": [r"resolucion", r"\bresolver\b", r"terminacion", r"rescision", r"resolutoria"]},
    {"nombre": "Solución de controversias", "patrones": [r"controversia", r"arbitraje", r"jurisdiccion", r"competencia\s+de\s+los\s+jueces", r"jueces\s+y\s+tribunales"]},
    {"nombre": "Domicilio y notificaciones", "patrones": [r"\bdomicilio\b", r"notificaciones", r"comunicaciones"]},
    {"nombre": "Firma de las partes", "patrones": [r"\bfirma", r"suscriben", r"en\s+senal\s+de\s+conformidad"]},
]
PESO_CLAUSULA_FALTANTE = 6

# Marcas que indican datos sin completar en una plantilla.
PATRONES_CAMPOS_VACIOS = [r"_{3,}", r"\.{5,}", r"\[[^\]\n]{0,40}\]", r"\bx{3,}\b", r"\(completar\)", r"<[^>\n]{1,30}>"]


# ---------------------------------------------------------------------------
# 3. FUNCIONES
# ---------------------------------------------------------------------------

def normalizar_texto(texto):
    """Pasa a minúsculas y quita tildes SIN cambiar la longitud del texto.

    Esto corrige una limitación reconocida en la EC1: lower() no quitaba tildes,
    así "casación" no coincidía con "casacion". Aquí cada carácter se convierte
    en su versión sin tilde (á -> a, ñ -> n), uno por uno, para que las posiciones
    encontradas en el texto normalizado sirvan también en el texto original.
    """
    resultado = []
    for caracter in texto.lower():
        base = unicodedata.normalize("NFD", caracter)[0]
        resultado.append(base)
    return "".join(resultado)


def dividir_en_clausulas(texto):
    """Devuelve una lista de cláusulas: [{"titulo", "inicio", "fin"}].

    Se considera que empieza una cláusula cuando una línea empieza con
    'CLÁUSULA', 'ARTÍCULO', un ordinal ('PRIMERA', 'SEGUNDA'...) o un número ('1.', '2)').
    """
    patron_inicio = re.compile(
        r"^\s*(clausula|articulo|vistos?|considerando|antecedentes|fundamentos?|decision|fallo|petitorio|sumilla|primer[ao]|segund[ao]|tercer[ao]|cuart[ao]|quint[ao]|sext[ao]|"
        r"septim[ao]|setim[ao]|octav[ao]|noven[ao]|decim[ao]|undecim[ao]|duodecim[ao]|\d{1,2}[\.\)])",
        re.MULTILINE,
    )
    normal = normalizar_texto(texto)
    inicios = [m.start() for m in patron_inicio.finditer(normal)]
    tiene_encabezado = not inicios or inicios[0] != 0
    if tiene_encabezado:
        inicios = [0] + inicios

    clausulas = []
    for i, inicio in enumerate(inicios):
        fin = inicios[i + 1] if i + 1 < len(inicios) else len(texto)
        if i == 0 and tiene_encabezado:
            titulo = "Encabezado / introducción"
        else:
            titulo = texto[inicio:fin].strip().split("\n")[0][:80]
        clausulas.append({"titulo": titulo, "inicio": inicio, "fin": fin})
    return clausulas


def ubicar_clausula(clausulas, posicion):
    """Busca a qué cláusula pertenece una posición del texto."""
    for clausula in clausulas:
        if clausula["inicio"] <= posicion < clausula["fin"]:
            return clausula["titulo"]
    return "No identificada"


def extraer_fragmento(texto, inicio, fin, maximo=260):
    """Devuelve la oración donde aparece la coincidencia (para mostrarla como contexto).

    Retrocede hasta el punto o salto de línea anterior y avanza hasta el siguiente.
    Un punto entre números (S/ 8,400.00) no cuenta como fin de oración.
    """
    def es_limite(i):
        if texto[i] in ";\n":
            return True
        if texto[i] == ".":
            numero_antes = i > 0 and texto[i - 1].isdigit()
            numero_despues = i + 1 < len(texto) and texto[i + 1].isdigit()
            return not (numero_antes and numero_despues)
        return False

    desde = inicio
    while desde > 0 and not es_limite(desde - 1):
        desde = desde - 1
    hasta = fin
    while hasta < len(texto) and not es_limite(hasta):
        hasta = hasta + 1
    fragmento = " ".join(texto[desde:hasta + 1].split())
    if len(fragmento) > maximo:
        fragmento = fragmento[:maximo].rsplit(" ", 1)[0] + "…"
    return fragmento


def esta_en_titulo(texto, posicion):
    """True si la posición está en una línea corta escrita en MAYÚSCULAS (un título)."""
    inicio_linea = texto.rfind("\n", 0, posicion) + 1
    fin_linea = texto.find("\n", posicion)
    if fin_linea == -1:
        fin_linea = len(texto)
    linea = texto[inicio_linea:fin_linea].strip()
    return len(linea) < 90 and linea == linea.upper()


def buscar_alertas(texto, normal, clausulas, lista_reglas):
    """Recorre cada regla y cada patrón; si hay coincidencia, crea una alerta."""
    alertas = []
    zona_inicio, zona_fin = tipos_documento.limites_parte_resolutiva(normal)
    for regla in lista_reglas:
        coincidencias = []
        for patron in regla["patrones"]:
            for m in re.finditer(patron, normal):
                # Algunas reglas solo se buscan en la parte resolutiva (la decisión).
                if regla.get("zona") == "decision":
                    if zona_inicio is None or not zona_inicio <= m.start() < zona_fin:
                        continue
                coincidencias.append((m.start(), m.end()))
        if not coincidencias:
            continue

        # Quitamos coincidencias repetidas o superpuestas y las ordenamos.
        coincidencias.sort()
        unicas = []
        for inicio, fin in coincidencias:
            if unicas and inicio < unicas[-1][1]:
                continue
            unicas.append((inicio, fin))

        # Para la cita preferimos una coincidencia en el cuerpo de la cláusula y no en su
        # título (p. ej. "CLÁUSULA OCTAVA: PENALIDADES"), porque el cuerpo explica más.
        primera = unicas[0]
        for inicio, fin in unicas:
            if not esta_en_titulo(texto, inicio):
                primera = (inicio, fin)
                break
        alertas.append({
            "id": regla["id"],
            "categoria": regla["categoria"],
            "titulo": regla["titulo"],
            "nivel": regla["nivel"],
            "explicacion": regla["explicacion"],
            "recomendacion": regla["recomendacion"],
            "base_legal": regla["base_legal"],
            "clausula": ubicar_clausula(clausulas, primera[0]),
            "fragmento": extraer_fragmento(texto, primera[0], primera[1]),
            "apariciones": len(unicas),
            "posiciones": [{"inicio": a, "fin": b} for a, b in unicas],
        })
    return alertas


def verificar_clausulas_esenciales(normal, lista_esenciales):
    """Para cada cláusula esencial indica si se encontró (True) o no (False)."""
    resultado = []
    for clausula in lista_esenciales:
        encontrada = False
        for patron in clausula["patrones"]:
            if re.search(patron, normal):
                encontrada = True
                break
        resultado.append({"nombre": clausula["nombre"], "presente": encontrada})
    return resultado


def detectar_campos_vacios(texto):
    """Encuentra espacios en blanco de plantilla (____, [nombre], XXX)."""
    campos = []
    for patron in PATRONES_CAMPOS_VACIOS:
        for m in re.finditer(patron, texto, flags=re.IGNORECASE):
            campos.append({"texto": m.group(0), "inicio": m.start(), "fin": m.end()})
    campos.sort(key=lambda c: c["inicio"])
    return campos


def extraer_datos_clave(texto):
    """Extrae montos, plazos y fechas para un resumen rápido."""
    montos = re.findall(r"(?:S/\.?|US\$|\$|USD|PEN)\s?\d(?:[\d.,]*\d)?", texto)
    plazos = re.findall(r"(?:\b[a-záéíóúñ]+\s)?\(?\b\d{1,4}\)?\s*(?:días|dias|mes(?:es)?|años?|anos?|semanas?|horas?)\b(?:\s+(?:hábiles|habiles|calendario|naturales))?", texto, flags=re.IGNORECASE)
    fechas = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{1,2}\s+de\s+[a-záéíóú]+\s+de(?:l)?\s+\d{4}\b", texto, flags=re.IGNORECASE)
    porcentajes = re.findall(r"\b\d+(?:[.,]\d+)?\s?%", texto)

    def sin_repetir(lista):
        vistos = []
        for item in lista:
            limpio = " ".join(item.split())
            if limpio not in vistos:
                vistos.append(limpio)
        return vistos[:12]

    return {
        "montos": sin_repetir(montos),
        "plazos": sin_repetir(plazos),
        "fechas": sin_repetir(fechas),
        "porcentajes": sin_repetir(porcentajes),
    }


def calcular_indice_riesgo(alertas, esenciales, campos_vacios):
    """Suma puntos por cada hallazgo y devuelve un índice de 0 a 100 y un semáforo."""
    puntos = 0
    for alerta in alertas:
        puntos = puntos + PESO_POR_NIVEL[alerta["nivel"]]
    for clausula in esenciales:
        if not clausula["presente"]:
            puntos = puntos + PESO_CLAUSULA_FALTANTE
    if campos_vacios:
        puntos = puntos + 5

    indice = min(puntos, 100)
    if indice >= 60:
        semaforo = "alto"
    elif indice >= 30:
        semaforo = "medio"
    else:
        semaforo = "bajo"
    return indice, semaforo


# Cada tipo de documento tiene su propia lista de reglas y de partes esenciales.
CONFIG_TIPOS = {
    "contrato": {"reglas": REGLAS, "esenciales": CLAUSULAS_ESENCIALES},
    "resolucion": {"reglas": tipos_documento.REGLAS_RESOLUCION, "esenciales": tipos_documento.ESENCIALES_RESOLUCION},
    "escrito": {"reglas": tipos_documento.REGLAS_ESCRITO, "esenciales": tipos_documento.ESENCIALES_ESCRITO},
}


def analizar_documento(texto, tipo="auto"):
    """Función principal: recibe el texto y devuelve el informe completo.

    tipo: "auto" (lo detecta el programa), "contrato", "resolucion" o "escrito".
    """
    if texto is None or not texto.strip():
        raise ValueError("El texto del documento está vacío.")

    normal = normalizar_texto(texto)
    tipo_detectado, puntajes = tipos_documento.detectar_tipo(normal)
    if tipo not in CONFIG_TIPOS:
        tipo = tipo_detectado
    config = CONFIG_TIPOS[tipo]
    materia = tipos_documento.detectar_materia(normal)

    clausulas = dividir_en_clausulas(texto)
    alertas = buscar_alertas(texto, normal, clausulas, config["reglas"])
    esenciales = verificar_clausulas_esenciales(normal, config["esenciales"])
    campos_vacios = detectar_campos_vacios(texto)
    datos_clave = extraer_datos_clave(texto)
    indice, semaforo = calcular_indice_riesgo(alertas, esenciales, campos_vacios)

    # Ordenamos: primero las alertas de nivel alto.
    orden = {"alto": 0, "medio": 1, "bajo": 2}
    alertas.sort(key=lambda a: (orden[a["nivel"]], a["id"]))

    conteo = {"alto": 0, "medio": 0, "bajo": 0}
    for alerta in alertas:
        conteo[alerta["nivel"]] = conteo[alerta["nivel"]] + 1

    # En resoluciones judiciales: ficha del caso y recursos que podrían proceder.
    ficha = None
    recursos = []
    nota_recursos = None
    if tipo == "resolucion":
        ficha = tipos_documento.extraer_ficha_resolucion(texto, normal, materia)
        recursos, nota_recursos = tipos_documento.sugerir_recursos(ficha, normal)

    return {
        "tipo": tipo,
        "tipo_nombre": tipos_documento.NOMBRES_TIPO[tipo],
        "tipo_detectado": tipo_detectado,
        "materia": materia,
        "indice_riesgo": indice,
        "semaforo": semaforo,
        "conteo": conteo,
        "alertas": alertas,
        "clausulas_esenciales": esenciales,
        "campos_vacios": campos_vacios,
        "datos_clave": datos_clave,
        "ficha": ficha,
        "recursos_sugeridos": recursos,
        "nota_recursos": nota_recursos,
        "estadisticas": {
            "caracteres": len(texto),
            "palabras": len(texto.split()),
            "clausulas_detectadas": len(clausulas),
        },
        "reglas_evaluadas": len(config["reglas"]),
    }


def analizar_contrato(texto):
    """Se mantiene por compatibilidad: analiza el texto como contrato."""
    return analizar_documento(texto, "contrato")
