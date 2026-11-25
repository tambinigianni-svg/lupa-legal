# Nombre: generar_pdfs_ejemplo.py
# Tema: Crear PDF de prueba (como en 07-ejemplos_avanzados del repositorio del curso)
# Objetivo: Generar dos PDF para probar la subida de archivos:
#   1) contrato_de_arrendamiento.pdf  -> PDF "digital" con texto seleccionable (reportlab)
#   2) casacion_penal_escaneada.pdf   -> PDF "fotocopiado": solo imágenes, sin texto (Pillow)
# Como ejecutarlo: python generar_pdfs_ejemplo.py

import os
import random
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ejemplos")


def pdf_con_texto(origen, destino):
    with open(origen, encoding="utf-8") as archivo:
        lineas = archivo.read().split("\n")
    hoja = canvas.Canvas(destino, pagesize=A4)
    ancho, alto = A4
    y = alto - 60
    hoja.setFont("Times-Roman", 11)
    for linea in lineas:
        for parte in textwrap.wrap(linea, 95) or [""]:
            if y < 60:
                hoja.showPage()
                hoja.setFont("Times-Roman", 11)
                y = alto - 60
            hoja.drawString(55, y, parte)
            y = y - 15
    hoja.save()


def cargar_fuente(tamano):
    for ruta in ["/System/Library/Fonts/Supplemental/Times New Roman.ttf",
                 "/System/Library/Fonts/Supplemental/Arial.ttf",
                 "C:/Windows/Fonts/times.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]:
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tamano)
    return ImageFont.load_default()


def pdf_escaneado(origen, destino):
    """Dibuja el texto sobre imágenes y les agrega 'ruido' para simular una fotocopia."""
    random.seed(7)
    with open(origen, encoding="utf-8") as archivo:
        lineas = archivo.read().split("\n")
    fuente = cargar_fuente(30)
    paginas = []
    ancho, alto = 1654, 2339  # A4 a 200 ppp
    imagen = None
    y = 0

    def nueva_pagina():
        return Image.new("L", (ancho, alto), 246), 120

    imagen, y = nueva_pagina()
    for linea in lineas:
        for parte in textwrap.wrap(linea, 80) or [""]:
            if y > alto - 140:
                paginas.append(imagen)
                imagen, y = nueva_pagina()
            ImageDraw.Draw(imagen).text((120, y), parte, fill=30, font=fuente)
            y = y + 44
    paginas.append(imagen)

    finales = []
    for pagina in paginas:
        pixeles = pagina.load()
        for _ in range(9000):  # puntos de suciedad de fotocopiadora
            pixeles[random.randrange(ancho), random.randrange(alto)] = random.randrange(90, 200)
        pagina = pagina.rotate(0.7, fillcolor=246, expand=False).filter(ImageFilter.GaussianBlur(0.6))
        finales.append(pagina.convert("RGB"))
    finales[0].save(destino, save_all=True, append_images=finales[1:], resolution=200)


if __name__ == "__main__":
    pdf_con_texto(os.path.join(CARPETA, "contrato_de_arrendamiento.txt"), os.path.join(CARPETA, "contrato_de_arrendamiento.pdf"))
    pdf_escaneado(os.path.join(CARPETA, "casacion_penal.txt"), os.path.join(CARPETA, "casacion_penal_escaneada.pdf"))
    print("PDF creados en", CARPETA)
