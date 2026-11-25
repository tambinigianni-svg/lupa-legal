# Guía del código de Lupa Legal

Recorrido por el código para mostrarlo en VS Code durante la exposición. Cada sección indica **qué archivo abrir**, **qué fragmento mostrar** y **qué tema del curso aplica**.

> **Cómo se construyó:** el código lo escribió **Claude Code**, la IA agéntica de la Sesión 13 ("Creemos una página web usando Claude Code"), a partir de nuestras instrucciones. Nosotros definimos qué queríamos, revisamos, probamos y pedimos correcciones. **VS Code** es el editor donde se abre, se lee y se ejecuta el proyecto (Semana 2: "VS Code es el editor; Python es el lenguaje").

## Cómo abrirlo y ejecutarlo en VS Code

1. **Archivo → Abrir carpeta…** → `Legal Tech/revisor-contratos`.
2. Si VS Code lo pregunta, elige el intérprete `.venv` (ya está configurado en `.vscode/settings.json`).
3. Ve al panel **Ejecutar y depurar** (▶ con un insecto, `Cmd+Shift+D`) y elige:
   - **▶ Iniciar Lupa Legal (página web)** → abre <http://127.0.0.1:5050>
   - **📅 Calculadora de plazos en consola (como la EC1)** → la versión de terminal, igual que la EC1
   - **🔍 Probar reglas en consola** → el análisis sin página web
4. Para ver los diagramas de la bitácora: abre `BITACORA.md` y presiona `Cmd+Shift+V` (vista previa). La extensión *Markdown Preview Mermaid* dibuja los diagramas.

## Mapa: tema del curso → dónde está en el código

| Tema del curso | Archivo y lugar | Qué mostrar |
|---|---|---|
| Semana 1: Entrada → Proceso → Salida | `reglas.py` (encabezado) | El comentario inicial describe entrada, proceso y salida |
| Semana 1: pseudocódigo y algoritmos | `BITACORA.md`, paso 2 | Pseudocódigo antes del código |
| Semana 2: variables, `input()`, `print()` | `plazos.py`, bloque `if __name__ == "__main__"` | Menú de consola como en la EC1 |
| Semana 3: condicionales y funciones | `plazos.py` → `motivo_inhabil()` y `es_dia_habil()` | `if` encadenados: sábado, domingo, feriado |
| Semana 3: bucles `for` y `while` | `plazos.py` → `sumar_dias_habiles()` (`while`); `reglas.py` → `buscar_alertas()` (`for` dentro de `for`) | Recorrer días y recorrer reglas |
| Semana 4: listas y diccionarios | `plazos.py` → `RECURSOS`; `reglas.py` → `REGLAS`; `tipos_documento.py` → `REGLAS_RESOLUCION` | Lista de diccionarios, como en la EC1 |
| Semana 4: archivos | `extraccion.py` (PDF, Word, TXT); `asistente_ia.py` → `registrar_consulta()` (CSV); `app.py` → `cargar_env()` | Leer y escribir archivos |
| Ejemplos avanzados del repositorio (pypdf, reportlab) | `extraccion.py` → `extraer_de_pdf()`; `generar_pdfs_ejemplo.py` | Las mismas librerías de `07-ejemplos_avanzados` |
| Texto: `strip()`, `lower()`, búsqueda | `reglas.py` → `normalizar_texto()` | Corrige la limitación de tildes de la EC1 |
| Semana 6: Mermaid | `web/como-funciona.html` y `BITACORA.md` | Diagramas del flujo y de la arquitectura |
| Semana 9: HTML, JavaScript, frontend y backend | `web/*.html` (estructura), `web/*.js` (interacción), `app.py` (servidor) | `fetch()` en JS llama a una ruta `@app.route` en Python |
| Sesión 10: ciberseguridad y confidencialidad | `anonimizador.py`; `.gitignore` (oculta `.env`) | Datos personales ocultos antes de usar IA |
| Sesión 13: prompt engineering | `asistente_ia.py` → `PROMPT_ANALISIS`, `CRITERIOS_POR_TIPO`, `PROMPT_CHAT` | Rol, alcance, criterios, formato y limitaciones |
| Sesión 13: controles de IA | `asistente_ia.py` → `ESQUEMA_ANALISIS`, `registrar_consulta()`, `_comando_cli()` (`--tools ""`) | Salida verificable, trazabilidad y una IA sin herramientas |

## Recorrido sugerido (de 5 a 7 minutos en VS Code)

### 1. Los datos: listas de diccionarios (igual que la EC1)

**Abrir `plazos.py`, línea ~69 (`RECURSOS`).**

```python
RECURSOS = [
    {"id": "pen-casacion", "materia": "Penal", "nombre": "Recurso de casación",
     "plazo": 10, "unidad": "habiles", "base_legal": "CPP, art. 414.1.a"},
    ...
]
```

Qué decir: "En la EC1 teníamos `recursos = [{"nombre": "casacion", "plazo": 10}, ...]`. Mantuvimos la idea y agregamos materia, unidad y base legal. Así, agregar un recurso nuevo es agregar un diccionario, sin tocar la lógica."

### 2. La lógica heredada de la EC1

**Abrir `plazos.py` → `motivo_inhabil()` y `sumar_dias_habiles()` (líneas ~117-142).**

```python
def sumar_dias_habiles(fecha, cantidad, inhabiles_extra=None):
    while cantidad > 0:
        fecha = fecha + timedelta(days=1)
        if es_dia_habil(fecha, inhabiles_extra):
            cantidad = cantidad - 1
    return fecha
```

Qué decir: "Es la misma función de la EC1: avanza día por día y solo descuenta los días hábiles. La mejora es que ahora acepta días inhábiles adicionales (por ejemplo, una suspensión de labores)."

**Luego `calcular_plazo()` (línea ~187):** muestra el `DESPLAZAMIENTO_NOTIFICACION = {"fisica": 1, "electronica": 3}`, que es la regla de notificación de la EC1, y cómo se arma el detalle día por día.

### 3. El motor de reglas

**Abrir `reglas.py` → `REGLAS` (línea ~28)** y mostrar una regla completa (R02, resolución unilateral).

**Luego `normalizar_texto()` (línea ~278):**

```python
for caracter in texto.lower():
    base = unicodedata.normalize("NFD", caracter)[0]   # á -> a, ñ -> n
```

Qué decir: "En la EC1 reconocimos que `lower()` no quita tildes. Aquí lo resolvimos: 'casación' y 'casacion' se tratan igual."

**Luego `buscar_alertas()` (línea ~366):** un `for` sobre las reglas, otro `for` sobre los patrones y un `if` cuando hay coincidencia.

### 4. Otros documentos: resoluciones y casaciones

**Abrir `tipos_documento.py`:**
- `detectar_tipo()` (línea ~47) **reconoce patrones**: cuenta pistas de cada tipo ("considerando", "sala", "cláusula", "petitorio") y elige el que tenga más.
- `REGLAS_RESOLUCION` (línea ~66): la regla J01 tiene `"zona": "decision"`, así que solo se busca en la parte resolutiva y no en el voto singular.
- `sugerir_recursos()` (línea ~279) conecta el documento con la calculadora: si es un auto civil, sugiere `civ-apel-auto`.

### 5. Leer PDF y Word

**Abrir `extraccion.py`:**
- `extraer_de_pdf()` usa `pypdf`, la librería del ejemplo `05-unir-pdfs.py` del repositorio del curso.
- `extraer_de_docx()` muestra que un `.docx` es un ZIP con XML adentro.
- Si el PDF no tiene texto (fotocopia), devuelve `necesita_ocr: True` y la página hace OCR con Tesseract (`web/ocr.js`).

### 6. Frontend y backend conectados

**Abrir `web/app.js` → `analizarConReglas()`** y **`app.py` → `analizar()` (`@app.route("/api/analizar")`).**

Qué decir: "El navegador envía el texto con `fetch` (JavaScript) a una ruta de Flask (Python). Python analiza y responde en JSON, y JavaScript lo dibuja. Es el esquema frontend–backend de la Semana 9."

### 7. La IA con controles

**Abrir `asistente_ia.py`:**
- `PROMPT_ANALISIS` (línea ~41): las secciones ROL, ALCANCE, CRITERIOS, FORMATO y LIMITACIONES de la diapositiva de prompt engineering.
- `ESQUEMA_ANALISIS` (línea ~95): la IA debe responder con estos campos exactos.
- `_comando_cli()` (línea ~257): `--tools ""` quiere decir que Claude no tiene herramientas. Solo lee y responde, no puede abrir archivos ni ejecutar nada.
- `registrar_consulta()` (línea ~215): cada consulta queda en `registros/consultas_ia.csv`, sin guardar el documento.
- `PROMPT_CHAT`: "No calcules fechas por tu cuenta; usa `<calculo_plazo>`". La exactitud la garantiza Python y la explicación la da la IA.

### 8. Demostración en consola (opcional)

Ejecuta **📅 Calculadora de plazos en consola** y elige casación penal, `24/07/2026`, `fisica`. Resultado: inicio 27/07/2026 y vencimiento 12/08/2026, el mismo que en la web.

## Archivos del proyecto

| Archivo | Líneas | Para qué sirve |
|---|---|---|
| `app.py` | ~270 | Servidor Flask: rutas que usa la página |
| `reglas.py` | ~550 | Motor de reglas de contratos y análisis general |
| `tipos_documento.py` | ~300 | Reglas de resoluciones, casaciones y escritos; ficha y recursos |
| `plazos.py` | ~310 | Calculadora de plazos (evolución de la EC1) |
| `extraccion.py` | ~80 | Lectura de PDF, Word y TXT |
| `anonimizador.py` | ~50 | Oculta datos personales |
| `asistente_ia.py` | ~440 | Conexión con Claude: prompts, esquema, chat y registro |
| `probar_reglas.py` | ~45 | Prueba del análisis en consola |
| `generar_pdfs_ejemplo.py` | ~85 | Crea los PDF de ejemplo (digital y fotocopiado) |
| `web/index.html` + `app.js` | ~580 | Página del analizador |
| `web/plazos.html` + `plazos.js` | ~300 | Página de la calculadora |
| `web/comun.js` | ~165 | Chatbot y funciones compartidas |
| `web/ocr.js` | ~80 | OCR en el navegador |
| `web/como-funciona.html` | ~200 | Explicación del sistema con diagramas |
| `web/style.css` | ~350 | Diseño con los colores del curso, adaptable a celular |
