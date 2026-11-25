# Nombre: probar_reglas.py
# Tema: Prueba del motor de reglas desde la terminal (sin página web ni IA)
# Sirve para contratos, resoluciones/casaciones y escritos.
# Como ejecutarlo: python probar_reglas.py ejemplos/contrato_de_arrendamiento.txt

import sys

import anonimizador
import reglas

ruta = sys.argv[1] if len(sys.argv) > 1 else "ejemplos/contrato_de_arrendamiento.txt"
with open(ruta, encoding="utf-8") as archivo:
    texto = archivo.read()

informe = reglas.analizar_documento(texto)  # detecta el tipo automáticamente

print("=== LUPA LEGAL - REVISIÓN POR REGLAS ===")
print("Archivo:", ruta)
print("Tipo de documento:", informe["tipo_nombre"], "| Materia:", informe["materia"])
print("Índice de riesgo:", informe["indice_riesgo"], "/ 100  ->  riesgo", informe["semaforo"].upper())
print("Alertas: alto =", informe["conteo"]["alto"], "| medio =", informe["conteo"]["medio"], "| bajo =", informe["conteo"]["bajo"])
print()

for alerta in informe["alertas"]:
    print("[" + alerta["nivel"].upper() + "]", alerta["id"], "-", alerta["titulo"])
    print("   Sección:", alerta["clausula"])
    print("   Texto:", alerta["fragmento"][:150])
    print("   Base legal:", alerta["base_legal"])
    print()

if informe["ficha"]:
    print("Ficha:", informe["ficha"]["numero"], "|", informe["ficha"]["organo"], "|", informe["ficha"]["instancia"])
    print("Recursos sugeridos:", [r["id"] for r in informe["recursos_sugeridos"]], informe["nota_recursos"] or "")
    print()

print("Elementos esenciales:")
for clausula in informe["clausulas_esenciales"]:
    marca = "OK " if clausula["presente"] else "FALTA"
    print("  ", marca, clausula["nombre"])

print("\nCampos por completar:", len(informe["campos_vacios"]))
print("Datos clave:", informe["datos_clave"])

anonimo, ocultos = anonimizador.anonimizar(texto)
print("\nDatos que se ocultarían antes de enviar a la IA:", ocultos)
