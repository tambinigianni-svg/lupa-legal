# Nombre: tipos_documento.py
# Tema: Reglas para otros documentos jurídicos (no solo contratos)
# Objetivo: Reconocer el tipo de documento y aplicar reglas propias de cada uno:
#   - Contrato                      -> reglas de cláusulas riesgosas (en reglas.py)
#   - Resolución judicial/casación  -> decisión, mandatos con plazo, doctrina vinculante, recursos
#   - Escrito o demanda             -> requisitos formales (CPC, arts. 424 y 425)
#
# Mismo patrón que en la EC1: cada regla es un DICCIONARIO dentro de una LISTA.

import re

# ---------------------------------------------------------------------------
# 1. DETECCIÓN DEL TIPO DE DOCUMENTO (reconocimiento de patrones)
# ---------------------------------------------------------------------------
# Se cuentan "pistas" de cada tipo; gana el que tenga más.
PISTAS_TIPO = {
    "contrato": [r"\bcontrato\b", r"\bclausula\b", r"las\s+partes", r"arrendador|arrendatari[oa]|locador|comitente|vendedor|comprador",
                 r"conste\s+por\s+el\s+presente", r"en\s+senal\s+de\s+conformidad"],
    "resolucion": [r"\bcasacion\s+n", r"\bsala\b", r"\bjuzgado\b", r"\bvistos?\b", r"\bconsiderando\b", r"\bfundamentos?\s+de\s+derecho\b",
                   r"\bresolvieron\b|\bse\s+resuelve\b|\bfallo\b|\bdeclararon\b", r"\bexpediente\b|\bexp\.", r"\bresolucion\s+n",
                   r"sentencia\s+(de\s+vista|casatoria)", r"recurrente|impugnante"],
    "escrito": [r"senor\s+juez|senora\s+jueza|senor(es)?\s+(juez|vocal)", r"\bsumilla\b", r"\bpetitorio\b", r"\bpor\s+tanto\b",
                r"otrosi\s+digo", r"\bdemanda\b", r"medios\s+probatorios", r"a\s+usted\s+(pido|solicito)"],
}

NOMBRES_TIPO = {
    "contrato": "Contrato",
    "resolucion": "Resolución judicial / casación",
    "escrito": "Escrito o demanda",
}

PISTAS_MATERIA = {
    "Penal": [r"\bimputad[oa]\b", r"\bfiscal", r"\bdelito\b", r"codigo\s+procesal\s+penal|\bcpp\b|codigo\s+penal", r"\bpena\b", r"agraviad[oa]", r"acusad[oa]|sentenciad[oa]"],
    "Civil": [r"codigo\s+procesal\s+civil|\bcpc\b", r"codigo\s+civil", r"demandante", r"demandad[oa]", r"desalojo|alimentos|divorcio|obligacion\s+de\s+dar"],
    "Laboral": [r"ley\s+29497|nueva\s+ley\s+procesal\s+del\s+trabajo", r"trabajador", r"despido", r"empleador", r"beneficios\s+sociales|cts"],
    "Constitucional": [r"\bamparo\b", r"habeas\s+corpus|habeas\s+data", r"tribunal\s+constitucional", r"agravio\s+constitucional"],
}


def contar_pistas(normal, patrones):
    total = 0
    for patron in patrones:
        total = total + len(re.findall(patron, normal))
    return total


def detectar_tipo(normal):
    puntajes = {}
    for tipo, patrones in PISTAS_TIPO.items():
        puntajes[tipo] = contar_pistas(normal, patrones)
    mejor = max(puntajes, key=puntajes.get)
    if puntajes[mejor] == 0:
        mejor = "contrato"
    return mejor, puntajes


def detectar_materia(normal):
    puntajes = {m: contar_pistas(normal, p) for m, p in PISTAS_MATERIA.items()}
    mejor = max(puntajes, key=puntajes.get)
    return mejor if puntajes[mejor] > 0 else "No identificada"


# ---------------------------------------------------------------------------
# 2. REGLAS PARA RESOLUCIONES JUDICIALES Y CASACIONES
# ---------------------------------------------------------------------------
REGLAS_RESOLUCION = [
    {
        "id": "J01", "categoria": "Decisión", "titulo": "Decisión desfavorable: improcedente, infundado o inadmisible", "nivel": "alto",
        "zona": "decision",  # solo se busca en la parte resolutiva (no en votos singulares ni antecedentes)
        "patrones": [r"\bimprocedente\b", r"\binfundad[oa]\b", r"\binadmisible\b", r"no\s+casaron"],
        "explicacion": "La resolución rechaza un pedido o recurso. Hay que evaluar si cabe impugnarla y controlar el plazo.",
        "recomendacion": "Identificar el recurso procedente y calcular su plazo en la Calculadora de plazos.",
        "base_legal": "CPP, arts. 413-414; CPC, arts. 355-356",
    },
    {
        "id": "J02", "categoria": "Mandatos", "titulo": "Mandato con plazo o apercibimiento", "nivel": "alto",
        "patrones": [r"plazo\s+de\s+\w+\s*(\(\d+\)\s*)?dias", r"dentro\s+del?\s+(tercer|quinto|decimo|segundo)\s+dia", r"bajo\s+apercibimiento"],
        "explicacion": "La resolución ordena hacer algo dentro de un plazo; si no se cumple se aplica una consecuencia.",
        "recomendacion": "Agendar el vencimiento desde la notificación y preparar el cumplimiento.",
        "base_legal": "CPC, art. 147 (cómputo de plazos); CPP, art. 143",
    },
    {
        "id": "J03", "categoria": "Precedente", "titulo": "Doctrina jurisprudencial o precedente vinculante", "nivel": "alto",
        "patrones": [r"doctrina\s+jurisprudencial\s+vinculante", r"como\s+doctrina\s+jurisprudencial", r"precedente\s+vinculante", r"caracter\s+vinculante", r"de\s+observancia\s+obligatoria"],
        "explicacion": "Fija un criterio que los jueces deben seguir. Puede afectar otros casos del estudio.",
        "recomendacion": "Identificar los fundamentos vinculantes y evaluar su impacto en casos similares.",
        "base_legal": "CPP, art. 433.3; CPC, art. 400; Ley 31307, art. VI T.P.",
    },
    {
        "id": "J04", "categoria": "Nulidad", "titulo": "Nulidad, casación o reenvío a otra instancia", "nivel": "medio",
        "patrones": [r"\bcasaron\b", r"declararon\s+(la\s+)?nul", r"\bnul[oa]\s+(la|el)\b", r"\breenvio\b", r"nuevo\s+(juicio|pronunciamiento|fallo)", r"\brevocaron\b"],
        "explicacion": "Se anula o cambia lo decidido antes. El proceso puede volver a una instancia anterior.",
        "recomendacion": "Revisar qué actos quedan sin efecto y qué órgano debe pronunciarse de nuevo.",
        "base_legal": "CPP, arts. 433 y 150; CPC, art. 396",
    },
    {
        "id": "J05", "categoria": "Votos", "titulo": "Voto singular o en discordia", "nivel": "medio",
        "patrones": [r"voto\s+singular", r"voto\s+en\s+discordia", r"\bdiscordia\b", r"voto\s+dirimente"],
        "explicacion": "No todos los jueces coincidieron. El voto minoritario puede dar argumentos para otros casos.",
        "recomendacion": "Leer el voto singular: puede aportar argumentos para futuras impugnaciones.",
        "base_legal": "LOPJ, arts. 141-144",
    },
    {
        "id": "J06", "categoria": "Medidas", "titulo": "Medidas sobre la libertad o el patrimonio", "nivel": "alto",
        "patrones": [r"prision\s+preventiva", r"ubicacion\s+y\s+captura|orden\s+de\s+captura", r"impedimento\s+de\s+salida", r"\bembargo\b", r"medida\s+cautelar", r"comparecencia\s+con\s+restricciones"],
        "explicacion": "Hay medidas que afectan la libertad o los bienes de una persona.",
        "recomendacion": "Verificar duración, requisitos y si corresponde apelar o pedir variación.",
        "base_legal": "CPP, arts. 268 y ss.; CPC, arts. 608 y ss.",
    },
    {
        "id": "J07", "categoria": "Condena", "titulo": "Pena, reparación civil o pago ordenado", "nivel": "medio",
        "patrones": [r"pena\s+privativa", r"\banos\s+de\s+pena\b", r"reparacion\s+civil", r"\bcondenaron\b|\bcondena\b", r"ordenaron\s+el\s+pago|cumpla\s+con\s+pagar"],
        "explicacion": "Se impone una pena o un pago. Importa el monto, la forma y el plazo de cumplimiento.",
        "recomendacion": "Revisar montos, forma de pago y consecuencias del incumplimiento.",
        "base_legal": "Código Penal, arts. 28 y 92-93; CPC, art. 716",
    },
    {
        "id": "J08", "categoria": "Costas", "titulo": "Costas, costos o multa", "nivel": "medio",
        "patrones": [r"\bcostas\b", r"\bcostos\b", r"\bmulta\b", r"unidades\s+de\s+referencia\s+procesal|\burp\b"],
        "explicacion": "Se ordena pagar gastos del proceso o una multa.",
        "recomendacion": "Verificar quién paga, cuánto y si se exoneró a alguna parte.",
        "base_legal": "CPP, arts. 497-507; CPC, arts. 410-414",
    },
    {
        "id": "J09", "categoria": "Admisibilidad", "titulo": "Requisitos de admisibilidad o causales de casación", "nivel": "medio",
        "patrones": [r"interes\s+casacional", r"desarrollo\s+de\s+la\s+doctrina", r"causal(es)?\s+(de|invocad)", r"requisitos\s+de\s+(admisibilidad|procedencia)", r"no\s+se\s+advierte"],
        "explicacion": "La Corte analizó si el recurso cumplía los requisitos. Es un punto típico de rechazo.",
        "recomendacion": "Revisar qué requisito se consideró incumplido para no repetir el error.",
        "base_legal": "CPP, arts. 427-429; CPC, arts. 386-388",
    },
    {
        "id": "J10", "categoria": "Firmeza", "titulo": "Firmeza, ejecución o archivo", "nivel": "bajo",
        "patrones": [r"\bconsentida\b", r"\bejecutoriada\b", r"\bdevuelvase\b|\bdevolvieron\b", r"\barchivese\b|\barchivo\s+definitivo\b", r"cosa\s+juzgada"],
        "explicacion": "La resolución queda firme o se ordena su ejecución o archivo.",
        "recomendacion": "Verificar si ya no cabe recurso y qué actos de ejecución siguen.",
        "base_legal": "CPC, art. 123; CPP, art. 402",
    },
]

ESENCIALES_RESOLUCION = [
    {"nombre": "Número de expediente o casación", "patrones": [r"casacion\s+n", r"expediente", r"\bexp\.", r"recurso\s+de\s+nulidad\s+n"]},
    {"nombre": "Órgano jurisdiccional", "patrones": [r"\bsala\b", r"\bjuzgado\b", r"corte\s+(suprema|superior)"]},
    {"nombre": "Fecha de la resolución", "patrones": [r"\d{1,2}\s+de\s+[a-z]+\s+de(l)?\s+(\d{4}|dos\s+mil)", r"\d{1,2}/\d{1,2}/\d{4}", r"de\s+dos\s+mil\s+\w+"]},
    {"nombre": "Vistos o antecedentes", "patrones": [r"\bvistos?\b", r"\bantecedentes\b"]},
    {"nombre": "Fundamentos o considerandos", "patrones": [r"\bconsiderando", r"\bfundamentos?\b"]},
    {"nombre": "Parte resolutiva (decisión)", "patrones": [r"\bdecision\b", r"\bfallo\b", r"\bresolvieron\b", r"se\s+resuelve", r"por\s+estos\s+fundamentos"]},
    {"nombre": "Firma de los jueces", "patrones": [r"\bs\.\s?s\.", r"\bss\.", r"jueces?\s+supremos?", r"\bjuez\b", r"\bfirmado\b"]},
]

# ---------------------------------------------------------------------------
# 3. REGLAS PARA ESCRITOS Y DEMANDAS
# ---------------------------------------------------------------------------
REGLAS_ESCRITO = [
    {
        "id": "E01", "categoria": "Plazos", "titulo": "Prescripción o caducidad mencionada", "nivel": "alto",
        "patrones": [r"prescripcion", r"caducidad", r"\bprescrit[oa]\b", r"\bcaduc"],
        "explicacion": "Si la acción prescribió o caducó, la demanda puede ser rechazada.",
        "recomendacion": "Calcular la fecha límite de la acción antes de presentar el escrito.",
        "base_legal": "Código Civil, arts. 1989-2007",
    },
    {
        "id": "E02", "categoria": "Medidas", "titulo": "Se solicita una medida cautelar", "nivel": "medio",
        "patrones": [r"medida\s+cautelar", r"\bembargo\b", r"anotacion\s+de\s+demanda", r"secuestro\s+(conservativo|judicial)"],
        "explicacion": "La medida cautelar exige verosimilitud, peligro en la demora y contracautela.",
        "recomendacion": "Verificar que se acrediten los tres requisitos y se ofrezca contracautela.",
        "base_legal": "CPC, arts. 610-613",
    },
    {
        "id": "E03", "categoria": "Pretensiones", "titulo": "Acumulación de pretensiones", "nivel": "bajo",
        "patrones": [r"pretension\s+(accesoria|subordinada|alternativa)", r"acumulacion", r"pretension\s+principal"],
        "explicacion": "Hay varias pretensiones. Deben ser compatibles y de la misma competencia y vía.",
        "recomendacion": "Revisar compatibilidad y orden de las pretensiones.",
        "base_legal": "CPC, arts. 83-87",
    },
    {
        "id": "E04", "categoria": "Forma", "titulo": "Expresiones de urgencia o plazo para la parte", "nivel": "medio",
        "patrones": [r"bajo\s+apercibimiento", r"en\s+el\s+plazo\s+de", r"dentro\s+del?\s+(tercer|quinto)\s+dia"],
        "explicacion": "El escrito menciona plazos o apercibimientos que conviene controlar.",
        "recomendacion": "Verificar el cómputo del plazo citado.",
        "base_legal": "CPC, art. 147",
    },
]

ESENCIALES_ESCRITO = [
    {"nombre": "Dirigido al juez o autoridad", "patrones": [r"senor\s+juez|senora\s+jueza|senor(es)?\s+(juez|vocal)|al\s+juzgado"]},
    {"nombre": "Sumilla", "patrones": [r"\bsumilla\b"]},
    {"nombre": "Identificación del demandante (DNI/RUC)", "patrones": [r"\bdni\b", r"\bruc\b", r"documento\s+nacional\s+de\s+identidad"]},
    {"nombre": "Domicilio procesal o casilla electrónica", "patrones": [r"domicilio\s+procesal", r"casilla\s+electronica"]},
    {"nombre": "Datos y domicilio del demandado", "patrones": [r"demandad[oa]", r"domicilio\s+real", r"emplazar"]},
    {"nombre": "Petitorio", "patrones": [r"\bpetitorio\b", r"\bpretension\b"]},
    {"nombre": "Fundamentos de hecho", "patrones": [r"fundamentos?\s+de\s+hecho", r"\bhechos\b"]},
    {"nombre": "Fundamentos de derecho", "patrones": [r"fundamentos?\s+(juridicos|de\s+derecho)", r"\bamparo\s+legal\b"]},
    {"nombre": "Vía procedimental", "patrones": [r"via\s+procedimental", r"proceso\s+(de\s+conocimiento|abreviado|sumarisimo|unico)"]},
    {"nombre": "Medios probatorios", "patrones": [r"medios\s+probatorios", r"\bpruebas\b"]},
    {"nombre": "Anexos", "patrones": [r"\banexos?\b", r"\b1-[a-z]\b"]},
    {"nombre": "Tasa judicial (arancel)", "patrones": [r"tasa\s+judicial", r"\barancel", r"derecho\s+de\s+notificacion"]},
    {"nombre": "Firma de abogado (colegiatura)", "patrones": [r"\bcal\b\s*n?|reg\.\s*cal|colegio\s+de\s+abogados|abogad[oa]\s*\n", r"\bc\.a\.l\.", r"registro\s+n"]},
]


# ---------------------------------------------------------------------------
# 4. FICHA DE UNA RESOLUCIÓN Y RECURSOS SUGERIDOS
# ---------------------------------------------------------------------------

def limites_parte_resolutiva(normal):
    """Devuelve (inicio, fin) de la parte resolutiva: desde 'por estos fundamentos', 'decision',
    'fallo' o 'se resuelve' hasta el voto singular (si lo hay) o el final del texto."""
    inicio = None
    for m in re.finditer(r"(por\s+estos\s+fundamentos|^\s*decision\b|^\s*fallo\b|se\s+resuelve|resolvieron)", normal, flags=re.MULTILINE):
        inicio = m.start()
        break
    if inicio is None:
        return None, None
    fin = len(normal)
    voto = re.search(r"voto\s+(singular|en\s+discordia)", normal[inicio:])
    if voto:
        fin = inicio + voto.start()
    return inicio, fin


def primera_coincidencia(texto, patron):
    m = re.search(patron, texto, flags=re.IGNORECASE)
    return " ".join(m.group(0).split()) if m else None


def extraer_ficha_resolucion(texto, normal, materia):
    """Extrae los datos principales de una resolución judicial."""
    numero = primera_coincidencia(texto, r"(casaci[oó]n|expediente|exp\.|recurso de nulidad)\s*(n\.?\s*[°º*]?\.?|n[uú]mero)\s*\d[\w\-/\.]*( [A-ZÁÉÍÓÚ]+)*")

    # Órgano: primero buscamos una línea con "Sala" o "Juzgado" en el encabezado; si no, "Corte".
    encabezado = texto[:900].split("\n")
    organo = None
    for patron in (r"\b(sala|juzgado)\b", r"\bcorte\b"):
        for linea in encabezado:
            limpia = linea.strip()
            if re.search(patron, limpia, flags=re.IGNORECASE) and len(limpia) < 140:
                organo = limpia
                break
        if organo:
            break

    # Fecha al inicio de una línea: "Lima, catorce de octubre de dos mil veinticinco".
    fecha = primera_coincidencia(texto, r"(?m)^[ \t]*[A-ZÁÉÍÓÚ][a-záéíóú]+( [A-ZÁÉÍÓÚ][a-záéíóú]+)*, (el )?[\wáéíóú ]{3,40}? de [a-záéíóú]+ de(l)? (\d{4}|dos mil[ a-záéíóú]{0,20})")

    inicio, fin = limites_parte_resolutiva(normal)
    decision = None
    sentidos = []
    if inicio is not None:
        bloque = texto[inicio:min(fin, inicio + 700)]
        decision = " ".join(bloque.split())
        if fin > inicio + 700:
            decision = decision.rsplit(" ", 1)[0] + "…"
        for palabra in ["fundado", "infundado", "improcedente", "inadmisible", "casaron", "no casaron", "confirmaron",
                        "revocaron", "nula", "nulo", "absolvieron", "condenaron"]:
            if re.search(r"\b" + palabra + r"\b", normal[inicio:fin]):
                sentidos.append(palabra.upper())

    # Instancia. Ojo: los juzgados también llevan "Corte Superior de Justicia de ..." en el encabezado.
    cabecera = normal[:900]
    if re.search(r"corte\s+suprema|sala\s+suprema|jueces?\s+supremos?", cabecera):
        instancia = "Corte Suprema"
    elif re.search(r"juzgado", cabecera):
        instancia = "Juzgado (primera instancia)"
    elif re.search(r"sala|sentencia\s+de\s+vista", cabecera):
        instancia = "Corte Superior (segunda instancia)"
    else:
        instancia = "No identificada"

    es_sentencia = bool(re.search(r"\bsentencia\b", normal[:1500]))
    es_auto = bool(re.search(r"\bauto\b", normal[:1500])) and not es_sentencia

    return {
        "numero": numero, "organo": organo, "fecha": fecha, "materia": materia, "instancia": instancia,
        "clase": "Sentencia" if es_sentencia else ("Auto" if es_auto else "Resolución"),
        "decision": decision, "sentidos": sentidos,
    }


def sugerir_recursos(ficha, normal):
    """Sugiere qué recursos podrían proceder y su id en la Calculadora de plazos (plazos.py)."""
    materia = ficha["materia"]
    prefijo = {"Penal": "pen", "Civil": "civ", "Laboral": "lab", "Constitucional": "const"}.get(materia)
    sugerencias = []
    nota = None

    if ficha["instancia"] == "Corte Suprema":
        nota = ("Resolución de la Corte Suprema: en general no admite recurso ordinario "
                "(en materia penal, la sentencia casatoria no es recurrible: CPP, art. 436.1). "
                "Verificar si cabe aclaración o corrección.")
    elif prefijo:
        if ficha["clase"] == "Sentencia" and ficha["instancia"].startswith("Corte Superior"):
            sugerencias.append({"id": prefijo + "-casacion" if prefijo != "const" else "const-rac",
                                "motivo": "Sentencia de segunda instancia"})
        elif ficha["clase"] == "Sentencia":
            sugerencias.append({"id": {"pen": "pen-apel-sent", "civ": "civ-apel-sent-conoc", "lab": "lab-apel-sent"}.get(prefijo, "const-rac"),
                                "motivo": "Sentencia de primera instancia"})
        else:
            if prefijo in ("pen", "civ"):
                sugerencias.append({"id": prefijo + "-apel-auto", "motivo": "Auto que pone fin al proceso o causa agravio"})

        if re.search(r"improcedente\s+el\s+recurso|declararon\s+improcedente\s+(el|la)\s+(recurso|apelacion|casacion)", normal) and prefijo in ("pen", "civ"):
            sugerencias.append({"id": prefijo + "-queja", "motivo": "Se declaró improcedente un recurso"})
    else:
        nota = "No se pudo identificar la materia: elija el recurso manualmente en la Calculadora de plazos."
    return sugerencias, nota
