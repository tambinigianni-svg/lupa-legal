# Nombre: anonimizador.py
# Tema: Confidencialidad y protección de datos antes de usar IA
# Objetivo: Reemplazar datos personales por etiquetas antes de enviar el texto a un
#           servicio externo (la API de Claude).
#
# Conexión con el curso (Sesiones 10 y 13): la información enviada a una IA en la nube
# se procesa en infraestructura de terceros. Para cuidar el secreto profesional y la
# Ley 29733 (Protección de Datos Personales), primero "tapamos" los datos sensibles.
#
# Limitación: es una anonimización básica por patrones. NO detecta nombres propios
# ni direcciones; por eso el usuario siempre debe revisar lo que envía.

import re

# Lista de diccionarios: cada patrón tiene un nombre (etiqueta) y una expresión regular.
# El orden importa: primero los patrones más largos (RUC de 11 dígitos antes que DNI de 8).
PATRONES_SENSIBLES = [
    {"etiqueta": "CORREO", "patron": r"[\w.+-]+@[\w-]+\.[\w.]+"},
    {"etiqueta": "CUENTA_BANCARIA", "patron": r"\b\d{20}\b|\b\d{3,4}-\d{3,10}(?:-\d{1,4}){1,3}\b"},
    {"etiqueta": "RUC", "patron": r"\b(10|15|17|20)\d{9}\b"},
    {"etiqueta": "PARTIDA_REGISTRAL", "patron": r"\b\d{8,9}\b(?=[^\n]{0,40}[Rr]egistro)"},
    {"etiqueta": "DNI", "patron": r"\b\d{8}\b"},
    {"etiqueta": "TELEFONO", "patron": r"(?<!\d)(\+?51[\s-]?)?9\d{2}[\s-]?\d{3}[\s-]?\d{3}(?!\d)"},
]


def anonimizar(texto):
    """Devuelve (texto_anonimizado, resumen) donde resumen cuenta cuántos datos se ocultaron."""
    resumen = {}
    for item in PATRONES_SENSIBLES:
        contador = {"n": 0}

        def reemplazar(coincidencia, etiqueta=item["etiqueta"], contador=contador):
            contador["n"] = contador["n"] + 1
            return "[" + etiqueta + "]"

        texto = re.sub(item["patron"], reemplazar, texto)
        if contador["n"] > 0:
            resumen[item["etiqueta"]] = contador["n"]
    return texto, resumen


if __name__ == "__main__":
    ejemplo = "Juan Pérez, con DNI N° 45879632, RUC 20512345678, correo juan@mail.com, celular 987 654 321."
    anonimo, conteo = anonimizar(ejemplo)
    print(anonimo)
    print(conteo)
