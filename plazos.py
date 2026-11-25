# Nombre: plazos.py
# Tema: Cálculo de plazos procesales (versión mejorada de la EC1)
# Objetivo: Calcular cuándo empieza y cuándo vence el plazo para interponer un recurso,
#           contando solo días hábiles (sin sábados, domingos ni feriados).
#
# Qué se mantuvo de la EC1:
#   - La lista de feriados 2026 y la función es_dia_habil().
#   - sumar_dias_habiles() y la regla de notificación física (+1) / electrónica (+3).
#   - Los recursos guardados como LISTA DE DICCIONARIOS.
# Qué se mejoró:
#   - Más materias: penal, civil, laboral y constitucional (no solo penal).
#   - Feriados 2027 con su nombre, y días inhábiles adicionales (p. ej. suspensión de labores).
#   - Detalle día por día de cómo se contó el plazo (para poder verificarlo).
#   - Estado frente a la fecha de hoy: vencido, vence hoy o cuántos días hábiles quedan.
#   - Los plazos en meses (investigación compleja) se suman como meses reales, no como 30 días.
#
# IMPORTANTE: los plazos son referenciales. Verificar siempre la norma vigente y si existe
# una regla especial para el caso concreto.

from datetime import date, datetime, timedelta

# ---------------------------------------------------------------------------
# 1. DATOS: feriados nacionales (fecha -> nombre)
# ---------------------------------------------------------------------------
FERIADOS = {
    # 2026 (lista usada en la EC1)
    "01/01/2026": "Año Nuevo",
    "02/04/2026": "Jueves Santo",
    "03/04/2026": "Viernes Santo",
    "01/05/2026": "Día del Trabajo",
    "07/06/2026": "Batalla de Arica y Día de la Bandera",
    "29/06/2026": "San Pedro y San Pablo",
    "23/07/2026": "Día de la Fuerza Aérea del Perú",
    "28/07/2026": "Fiestas Patrias",
    "29/07/2026": "Fiestas Patrias",
    "06/08/2026": "Batalla de Junín",
    "30/08/2026": "Santa Rosa de Lima",
    "08/10/2026": "Combate de Angamos",
    "01/11/2026": "Día de Todos los Santos",
    "08/12/2026": "Inmaculada Concepción",
    "09/12/2026": "Batalla de Ayacucho",
    "25/12/2026": "Navidad",
    # 2027
    "01/01/2027": "Año Nuevo",
    "25/03/2027": "Jueves Santo",
    "26/03/2027": "Viernes Santo",
    "01/05/2027": "Día del Trabajo",
    "07/06/2027": "Batalla de Arica y Día de la Bandera",
    "29/06/2027": "San Pedro y San Pablo",
    "23/07/2027": "Día de la Fuerza Aérea del Perú",
    "28/07/2027": "Fiestas Patrias",
    "29/07/2027": "Fiestas Patrias",
    "06/08/2027": "Batalla de Junín",
    "30/08/2027": "Santa Rosa de Lima",
    "08/10/2027": "Combate de Angamos",
    "01/11/2027": "Día de Todos los Santos",
    "08/12/2027": "Inmaculada Concepción",
    "09/12/2027": "Batalla de Ayacucho",
    "25/12/2027": "Navidad",
}

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# ---------------------------------------------------------------------------
# 2. DATOS: recursos y plazos por materia (lista de diccionarios, como en la EC1)
# ---------------------------------------------------------------------------
# unidad: "habiles" (días hábiles desde la notificación), "naturales" (días calendario)
#         o "meses" (meses calendario).
RECURSOS = [
    # --- Penal (Código Procesal Penal, D. Leg. 957) ---
    {"id": "pen-casacion", "materia": "Penal", "nombre": "Recurso de casación", "plazo": 10, "unidad": "habiles", "base_legal": "CPP, art. 414.1.a"},
    {"id": "pen-apel-sent", "materia": "Penal", "nombre": "Apelación de sentencia", "plazo": 5, "unidad": "habiles", "base_legal": "CPP, art. 414.1.b"},
    {"id": "pen-apel-auto", "materia": "Penal", "nombre": "Apelación de auto", "plazo": 3, "unidad": "habiles", "base_legal": "CPP, art. 414.1.c"},
    {"id": "pen-queja", "materia": "Penal", "nombre": "Recurso de queja", "plazo": 3, "unidad": "habiles", "base_legal": "CPP, art. 414.1.d"},
    {"id": "pen-reposicion", "materia": "Penal", "nombre": "Recurso de reposición", "plazo": 2, "unidad": "habiles", "base_legal": "CPP, art. 414.1.e"},
    # --- Investigación fiscal (CPP) - se cuentan desde la disposición de inicio ---
    {"id": "inv-preliminar", "materia": "Investigación fiscal", "nombre": "Diligencias preliminares", "plazo": 60, "unidad": "naturales", "base_legal": "CPP, art. 334.2"},
    {"id": "inv-simple", "materia": "Investigación fiscal", "nombre": "Investigación preparatoria simple", "plazo": 120, "unidad": "naturales", "base_legal": "CPP, art. 342.1"},
    {"id": "inv-compleja", "materia": "Investigación fiscal", "nombre": "Investigación preparatoria compleja", "plazo": 8, "unidad": "meses", "base_legal": "CPP, art. 342.2"},
    {"id": "inv-crimen-org", "materia": "Investigación fiscal", "nombre": "Investigación por organización criminal", "plazo": 36, "unidad": "meses", "base_legal": "CPP, art. 342.2"},
    # --- Civil (Código Procesal Civil) ---
    {"id": "civ-casacion", "materia": "Civil", "nombre": "Recurso de casación", "plazo": 10, "unidad": "habiles", "base_legal": "CPC, art. 387"},
    {"id": "civ-apel-sent-conoc", "materia": "Civil", "nombre": "Apelación de sentencia (proceso de conocimiento)", "plazo": 10, "unidad": "habiles", "base_legal": "CPC, art. 373"},
    {"id": "civ-apel-sent-sumar", "materia": "Civil", "nombre": "Apelación de sentencia (proceso sumarísimo)", "plazo": 3, "unidad": "habiles", "base_legal": "CPC, art. 556"},
    {"id": "civ-apel-auto", "materia": "Civil", "nombre": "Apelación de auto", "plazo": 3, "unidad": "habiles", "base_legal": "CPC, art. 376"},
    {"id": "civ-reposicion", "materia": "Civil", "nombre": "Recurso de reposición", "plazo": 3, "unidad": "habiles", "base_legal": "CPC, art. 363"},
    {"id": "civ-queja", "materia": "Civil", "nombre": "Recurso de queja", "plazo": 3, "unidad": "habiles", "base_legal": "CPC, art. 403"},
    # --- Laboral (Nueva Ley Procesal del Trabajo, Ley 29497) ---
    {"id": "lab-apel-sent", "materia": "Laboral", "nombre": "Apelación de sentencia (proceso ordinario)", "plazo": 5, "unidad": "habiles", "base_legal": "Ley 29497, art. 32"},
    {"id": "lab-casacion", "materia": "Laboral", "nombre": "Recurso de casación", "plazo": 10, "unidad": "habiles", "base_legal": "Ley 29497, art. 35"},
    # --- Constitucional (Nuevo Código Procesal Constitucional, Ley 31307) ---
    {"id": "const-rac", "materia": "Constitucional", "nombre": "Recurso de agravio constitucional", "plazo": 10, "unidad": "habiles", "base_legal": "Ley 31307, art. 24"},
]

# Días hábiles que se suman a la fecha de notificación para obtener el PRIMER día del plazo.
#   física: el plazo corre desde el día hábil siguiente a la notificación.
#   electrónica: la notificación surte efectos el segundo día hábil siguiente a su ingreso
#                en la casilla; el plazo corre desde el día hábil siguiente (es decir, el 3.º).
DESPLAZAMIENTO_NOTIFICACION = {"fisica": 1, "electronica": 3}


# ---------------------------------------------------------------------------
# 3. FUNCIONES (las tres primeras vienen de la EC1)
# ---------------------------------------------------------------------------

def texto_a_fecha(texto):
    """Convierte 'dd/mm/aaaa' o 'aaaa-mm-dd' en una fecha. Lanza ValueError si no es válida."""
    texto = str(texto).strip()
    for formato in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            pass
    raise ValueError("Fecha no válida: use el formato dd/mm/aaaa.")


def motivo_inhabil(fecha, inhabiles_extra=None):
    """Devuelve por qué un día NO es hábil, o None si sí lo es."""
    fecha_texto = fecha.strftime("%d/%m/%Y")
    if fecha.weekday() == 5:
        return "sábado"
    if fecha.weekday() == 6:
        return "domingo"
    if fecha_texto in FERIADOS:
        return "feriado: " + FERIADOS[fecha_texto]
    if inhabiles_extra and fecha_texto in inhabiles_extra:
        return "día inhábil: " + inhabiles_extra[fecha_texto]
    return None


def es_dia_habil(fecha, inhabiles_extra=None):
    return motivo_inhabil(fecha, inhabiles_extra) is None


def sumar_dias_habiles(fecha, cantidad, inhabiles_extra=None):
    """Avanza 'cantidad' días hábiles a partir de 'fecha' (sin contar la fecha inicial)."""
    while cantidad > 0:
        fecha = fecha + timedelta(days=1)
        if es_dia_habil(fecha, inhabiles_extra):
            cantidad = cantidad - 1
    return fecha


def sumar_meses(fecha, meses):
    """Suma meses calendario (31/01 + 1 mes = 28/02 o 29/02)."""
    mes = fecha.month - 1 + meses
    anio = fecha.year + mes // 12
    mes = mes % 12 + 1
    ultimo_dia = [31, 29 if anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0) else 28,
                  31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]
    return date(anio, mes, min(fecha.day, ultimo_dia))


def buscar_recurso(id_recurso):
    for recurso in RECURSOS:
        if recurso["id"] == id_recurso:
            return recurso
    return None


def contar_habiles_entre(desde, hasta, inhabiles_extra=None):
    """Cuántos días hábiles hay desde 'desde' (incluido) hasta 'hasta' (incluido)."""
    total = 0
    fecha = desde
    while fecha <= hasta:
        if es_dia_habil(fecha, inhabiles_extra):
            total = total + 1
        fecha = fecha + timedelta(days=1)
    return total


def estado_frente_a_hoy(vencimiento, hoy, inhabiles_extra=None, en_habiles=True):
    if hoy > vencimiento:
        return {"codigo": "vencido", "texto": "El plazo ya venció.", "dias_restantes": 0}
    if hoy == vencimiento:
        return {"codigo": "hoy", "texto": "¡El plazo vence HOY!", "dias_restantes": 0}
    if en_habiles:
        restantes = contar_habiles_entre(hoy + timedelta(days=1), vencimiento, inhabiles_extra)
        texto = "Quedan " + str(restantes) + " día(s) hábil(es) después de hoy."
    else:
        restantes = (vencimiento - hoy).days
        texto = "Quedan " + str(restantes) + " día(s) calendario."
    codigo = "urgente" if restantes <= 2 else "vigente"
    return {"codigo": codigo, "texto": texto, "dias_restantes": restantes}


def calcular_plazo(id_recurso, fecha_texto, tipo_notificacion="fisica", inhabiles_extra=None, hoy=None, plazo_manual=None):
    """Función principal. Devuelve un diccionario con el resultado y el detalle del cómputo.

    - id_recurso: uno de RECURSOS, o "manual" para un plazo libre en días hábiles.
    - fecha_texto: fecha de notificación (o de inicio, para plazos de investigación).
    - inhabiles_extra: {"dd/mm/aaaa": "motivo"} con días no laborables adicionales.
    """
    inhabiles_extra = inhabiles_extra or {}
    hoy = hoy or date.today()
    fecha = texto_a_fecha(fecha_texto)

    if id_recurso == "manual":
        if not plazo_manual or int(plazo_manual) <= 0:
            raise ValueError("Indique un plazo mayor a 0 días.")
        recurso = {"id": "manual", "materia": "Otro", "nombre": "Plazo personalizado",
                   "plazo": int(plazo_manual), "unidad": "habiles", "base_legal": "Indicado por el usuario"}
    else:
        recurso = buscar_recurso(id_recurso)
        if recurso is None:
            raise ValueError("Recurso no reconocido.")

    resultado = {"recurso": recurso, "fecha_base": fecha.strftime("%d/%m/%Y")}

    if recurso["unidad"] == "habiles":
        if tipo_notificacion not in DESPLAZAMIENTO_NOTIFICACION:
            raise ValueError("Tipo de notificación no válido. Use 'fisica' o 'electronica'.")
        inicio = sumar_dias_habiles(fecha, DESPLAZAMIENTO_NOTIFICACION[tipo_notificacion], inhabiles_extra)
        vencimiento = sumar_dias_habiles(inicio, recurso["plazo"] - 1, inhabiles_extra)

        # Detalle día por día: desde la notificación hasta el vencimiento.
        detalle = []
        contador = 0
        dia = fecha
        while dia <= vencimiento:
            motivo = motivo_inhabil(dia, inhabiles_extra)
            if dia == fecha:
                etiqueta = "Notificación (" + ("electrónica" if tipo_notificacion == "electronica" else "física") + ")"
                cuenta = False
            elif dia < inicio:
                etiqueta = ("No se cuenta: " + motivo) if motivo else "No se cuenta: la notificación aún no surte efectos"
                cuenta = False
            elif motivo:
                etiqueta = "No se cuenta: " + motivo
                cuenta = False
            else:
                contador = contador + 1
                etiqueta = "Día " + str(contador) + " de " + str(recurso["plazo"])
                cuenta = True
            detalle.append({"fecha": dia.strftime("%d/%m/%Y"), "dia_semana": DIAS_SEMANA[dia.weekday()],
                            "cuenta": cuenta, "etiqueta": etiqueta})
            dia = dia + timedelta(days=1)

        resultado.update({
            "tipo_notificacion": tipo_notificacion,
            "inicio": inicio.strftime("%d/%m/%Y"),
            "vencimiento": vencimiento.strftime("%d/%m/%Y"),
            "vencimiento_dia": DIAS_SEMANA[vencimiento.weekday()],
            "unidad_texto": "días hábiles",
            "detalle": detalle,
            "estado": estado_frente_a_hoy(vencimiento, hoy, inhabiles_extra, True),
            "explicacion": (
                "Notificación " + ("electrónica: surte efectos el segundo día hábil siguiente y el plazo corre desde el día hábil siguiente"
                                   if tipo_notificacion == "electronica"
                                   else "física: el plazo corre desde el día hábil siguiente")
                + ". Se excluyen sábados, domingos, feriados y días inhábiles indicados."
            ),
        })
    else:
        # Plazos de investigación: se cuentan en días calendario o meses desde la fecha de inicio.
        if recurso["unidad"] == "naturales":
            vencimiento = fecha + timedelta(days=recurso["plazo"])
            unidad_texto = "días calendario"
        else:
            vencimiento = sumar_meses(fecha, recurso["plazo"])
            unidad_texto = "meses"
        resultado.update({
            "tipo_notificacion": None,
            "inicio": fecha.strftime("%d/%m/%Y"),
            "vencimiento": vencimiento.strftime("%d/%m/%Y"),
            "vencimiento_dia": DIAS_SEMANA[vencimiento.weekday()],
            "unidad_texto": unidad_texto,
            "detalle": [],
            "estado": estado_frente_a_hoy(vencimiento, hoy, None, False),
            "explicacion": "Plazo en " + unidad_texto + " contado desde la fecha de inicio (incluye fines de semana y feriados). "
                           "Puede prorrogarse según la ley.",
        })
    return resultado


def catalogo():
    """Datos para llenar los menús de la página."""
    materias = []
    for recurso in RECURSOS:
        if recurso["materia"] not in materias:
            materias.append(recurso["materia"])
    return {"materias": materias, "recursos": RECURSOS,
            "feriados": [{"fecha": f, "nombre": n} for f, n in FERIADOS.items()]}


# ---------------------------------------------------------------------------
# Modo consola (como la EC1): python plazos.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== CALCULADORA DE PLAZOS ===")
    for i, r in enumerate(RECURSOS, start=1):
        print(str(i) + ".", r["materia"], "-", r["nombre"], "(" + str(r["plazo"]), r["unidad"] + ")")
    opcion = input("\nElija un número: ").strip()
    if not opcion.isdigit() or not 1 <= int(opcion) <= len(RECURSOS):
        print("Opción no válida.")
    else:
        elegido = RECURSOS[int(opcion) - 1]
        fecha_usuario = input("Fecha de notificación o inicio (dd/mm/aaaa): ")
        tipo = "fisica"
        if elegido["unidad"] == "habiles":
            tipo = input("Tipo de notificación (fisica/electronica): ").strip().lower()
        try:
            r = calcular_plazo(elegido["id"], fecha_usuario, tipo)
            print("\nRecurso:", r["recurso"]["nombre"], "-", r["recurso"]["base_legal"])
            print("Inicio del cómputo:", r["inicio"])
            print("Vencimiento:", r["vencimiento"], "(" + r["vencimiento_dia"] + ")")
            print(r["estado"]["texto"])
        except ValueError as error:
            print("Error:", error)
