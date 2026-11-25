# 🔍 Lupa Legal: revisión de documentos jurídicos y control de plazos

Página web que **analiza contratos, resoluciones judiciales, casaciones y escritos**, señala lo que requiere revisión y **calcula plazos procesales** en días hábiles. Es la evolución de nuestra EC1 (consulta de plazos penales en consola). Lee **PDF, incluso fotocopiados (OCR)**, Word, imágenes y texto, y usa a **Claude** como asistente.

**Integrantes:** Gianni Tambini · Aldrin Muñoz

> Prototipo académico · Legal Tech (DER 614) · 2026-2. Sus resultados son orientativos y no reemplazan la revisión de un abogado.

## ¿Qué hace?

| Función | Cómo funciona | ¿Necesita internet? |
|---|---|---|
| Lectura de archivos | PDF digital (pypdf), PDF fotocopiado o foto (OCR con Tesseract en el navegador), Word y TXT | Solo la primera vez, para descargar el OCR |
| Tipo de documento | Detecta contrato, resolución o casación, o escrito, y la materia | No |
| Análisis por reglas | 28 reglas (14 de contratos, 10 judiciales y 4 de escritos) y checklists de elementos esenciales | No |
| Ficha de resolución | Número, órgano, instancia, fecha, sentido del fallo, parte resolutiva y recursos sugeridos | No |
| Calculadora de plazos | 19 plazos (penal, civil, laboral, constitucional e investigación), feriados 2026-2027, notificación física o electrónica, calendario y archivo .ics | No |
| Segunda opinión IA | Claude confirma o descarta alertas, agrega hallazgos y acciones con plazo (JSON estructurado) | Sí |
| Chatbot "Lupa" | Responde sobre el documento o el cálculo de plazo, en streaming | Sí |
| Anonimización | Oculta DNI, RUC, correos, teléfonos y cuentas antes de enviar a la IA | No |

## Estructura del proyecto

```text
revisor-contratos/
|-- app.py                  # Servidor web (Flask): conecta la página con Python
|-- reglas.py               # Motor de reglas (contratos) y análisis general
|-- tipos_documento.py      # Resoluciones, casaciones y escritos: reglas, ficha y recursos
|-- plazos.py               # Calculadora de plazos (evolución de la EC1)
|-- extraccion.py           # Lectura de PDF, Word y TXT
|-- anonimizador.py         # Oculta datos personales antes de usar IA
|-- asistente_ia.py         # Claude: plantillas de prompt, esquema JSON, chat y registro
|-- probar_reglas.py        # Prueba del análisis en consola
|-- generar_pdfs_ejemplo.py # Crea PDF de ejemplo (digital y fotocopiado)
|-- ejemplos/               # Documentos de ejemplo (ficticios)
|-- web/                    # Frontend: index, plazos y como-funciona (HTML, CSS y JS)
|-- .vscode/                # Configuración para ejecutar desde VS Code
|-- BITACORA.md             # Registro paso a paso del desarrollo
|-- GUIA_DEL_CODIGO.md      # Recorrido del código para la exposición
```

## Cómo ejecutarlo

**Desde VS Code:** abre la carpeta, ve a **Ejecutar y depurar** (`Cmd+Shift+D`) y elige **▶ Iniciar Lupa Legal (página web)**.

**Desde la terminal**, dentro de la carpeta `revisor-contratos`:

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

En Windows: `.venv\Scripts\activate`

```bash
pip install -r requirements.txt
```

```bash
python app.py
```

Luego abre <http://127.0.0.1:5050>.

**Versión de consola (como la EC1):**

```bash
python plazos.py
```

```bash
python probar_reglas.py ejemplos/casacion_penal.txt
```

## La IA

La página elige automáticamente cómo conectarse con Claude:

1. **Claude Code (tu sesión):** si Claude Code está instalado (por ejemplo, la extensión de VS Code) y tiene una sesión iniciada. **No necesita clave.**
2. **API de Anthropic:** copia `.env.example` como `.env` y coloca tu `ANTHROPIC_API_KEY` (de <https://console.anthropic.com>).

En ambos casos Claude **no tiene herramientas** (no abre archivos ni ejecuta nada), recibe los datos personales ocultos y **no calcula fechas** (eso lo hace `plazos.py`). Cada consulta se registra en `registros/consultas_ia.csv`, sin guardar el documento.

Opciones en `.env`: `IA_PROVEEDOR` (`api`, `claude_code` o `ninguno`), `CLAUDE_MODEL` e `IA_ESFUERZO_ANALISIS` (`low`, `medium` o `high`).

## Limitaciones

- Las reglas detectan palabras y frases: puede haber falsos positivos y omisiones.
- El OCR puede leer mal fotocopias de baja calidad: revisa el texto obtenido.
- Los plazos no incluyen feriados locales ni suspensiones si no se agregan a mano.
- La anonimización no oculta nombres ni direcciones.
- Las referencias legales son orientativas: verifica la norma vigente.
