# Clasificación y priorización automática de PQRS en salud mediante PLN

**Proyecto de Aula — Inteligencia Artificial**  
Ingeniería de Sistemas · 7.º semestre  
Grupo 02 · Docente: Lic. Tonny Jiménez  
Valledupar, Colombia · 2026

## Descripción del proyecto

Este proyecto desarrolla un sistema de clasificación y priorización automática de **Peticiones, Quejas, Reclamos y Sugerencias (PQRS)** del sector salud mediante técnicas de **Procesamiento del Lenguaje Natural (PLN)** y aprendizaje automático.

Su propósito es apoyar la identificación de solicitudes que requieren mayor atención, clasificando su nivel de urgencia en tres categorías:

- **Alta:** situaciones que pueden representar un riesgo importante para la salud o requieren atención prioritaria.
- **Media:** solicitudes que necesitan seguimiento o resolución, sin evidenciar necesariamente una emergencia inmediata.
- **Baja:** consultas, trámites y solicitudes de menor prioridad.

La solución integra un modelo de clasificación basado en **TF-IDF y Multinomial Naive Bayes**, una aplicación web pública, un panel administrativo, una base de datos SQLite y un módulo de carga masiva de información.

El proyecto constituye un **prototipo académico y una prueba de concepto**. Los datos empleados para el desarrollo y las evaluaciones documentadas son sintéticos y no corresponden a historias clínicas ni a PQRS reales de pacientes.

## Estado del proyecto

**Fase 3 — Prototipo funcional integrado**

| Fase | Contenido | Estado |
|---|---|---|
| Fase 1 | Planteamiento del problema, generación de datos y análisis exploratorio | Completada |
| Fase 2 | Preprocesamiento, representación TF-IDF, entrenamiento, comparación y evaluación de modelos | Completada |
| Fase 3 | Integración web, gestión administrativa, almacenamiento, notificaciones y carga masiva | Implementada |

El sistema dispone de una interfaz pública para registrar PQRS y de una interfaz administrativa para consultar, clasificar y gestionar solicitudes.

## Objetivos

### Objetivo general

Desarrollar un prototipo basado en procesamiento del lenguaje natural y aprendizaje automático que permita clasificar y priorizar automáticamente las PQRS del sector salud según su nivel de urgencia.

### Objetivos específicos

1. Construir un conjunto de datos sintéticos representativo de diferentes situaciones relacionadas con los servicios de salud.
2. Aplicar técnicas de limpieza, normalización y procesamiento de texto.
3. Entrenar y comparar algoritmos de clasificación supervisada.
4. Evaluar el desempeño mediante métricas como precisión, recall y F1 macro.
5. Integrar el modelo seleccionado en una aplicación web funcional.
6. Implementar herramientas de seguimiento administrativo y carga masiva de información.
7. Analizar las limitaciones y posibles mejoras del sistema.

## Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Python | Lenguaje principal |
| Flask | Desarrollo de las aplicaciones web y API |
| scikit-learn | Entrenamiento y evaluación de modelos |
| NLTK | Procesamiento del lenguaje natural |
| TF-IDF | Representación numérica de textos |
| Multinomial Naive Bayes | Clasificación automática de urgencia |
| SQLite | Almacenamiento de solicitudes |
| SQLAlchemy | Interacción con la base de datos |
| Pandas | Manipulación y procesamiento de datos |
| Joblib | Serialización y carga del modelo |
| HTML, CSS y JavaScript | Interfaces de usuario |
| Jupyter Notebook | Experimentación y análisis |

## Metodología

### Fase 1 — Planteamiento y preparación de los datos

Se identificó la necesidad de apoyar la clasificación de PQRS en instituciones del sector salud, donde el volumen de solicitudes puede dificultar la identificación oportuna de situaciones prioritarias.

Para desarrollar el prototipo se construyó inicialmente un conjunto de **3.000 registros sintéticos**, generado con semilla 42 para favorecer la reproducibilidad.

Los registros incluyen textos relacionados con solicitudes de medicamentos, citas médicas, autorizaciones, atención administrativa y otros servicios de salud.

Se realizó un análisis exploratorio para estudiar la distribución de categorías, revisar los textos e identificar posibles problemas en los datos.

### Fase 2 — Preprocesamiento y modelado

El procesamiento de los textos contempla operaciones de normalización y limpieza, incluyendo tratamiento de caracteres, palabras frecuentes y conservación de información relevante para la clasificación.

La representación numérica utiliza **TF-IDF (Term Frequency–Inverse Document Frequency)**.

Esta técnica asigna pesos a los términos de acuerdo con su frecuencia en un documento y su relevancia respecto al conjunto de documentos.

Se compararon diferentes estrategias de clasificación, incluyendo:

- Clasificador de clase mayoritaria.
- Clasificador basado en palabras clave.
- Multinomial Naive Bayes con TF-IDF.
- SVM lineal con TF-IDF.
- Random Forest con TF-IDF.
- Combinaciones de reducción de dimensionalidad, LDA y clasificadores supervisados.

Se seleccionó **TF-IDF + Multinomial Naive Bayes** por su desempeño competitivo, sencillez computacional y facilidad de integración en la aplicación.

### Fase 3 — Integración y funcionamiento del sistema

Se desarrolló una solución web que conecta el modelo de aprendizaje automático con un proceso de registro y seguimiento de PQRS.

Esta fase incorpora:

- Formulario público de radicación.
- Clasificación automática de urgencia.
- Generación de números de radicado.
- Almacenamiento de solicitudes.
- Notificaciones por correo electrónico.
- Acceso administrativo.
- Panel de consulta y seguimiento.
- Búsqueda y filtros de solicitudes.
- Actualización del estado de las PQRS.
- Exportación de información a CSV.
- Importación masiva de registros.
- Evaluación de modelos candidatos.

## Arquitectura general

El funcionamiento del sistema puede representarse de la siguiente manera:

```text
                 USUARIO
                    |
                    v
          FORMULARIO PÚBLICO
               Flask
              app.py
                    |
                    v
           REGISTRO DE PQRS
                    |
           +--------+--------+
           |                 |
           v                 v
      MODELO PLN         BASE DE DATOS
      TF-IDF + NB           SQLite
           |                 |
           v                 |
     URGENCIA ESTIMADA       |
           |                 |
           +--------+--------+
                    |
                    v
            PANEL ADMINISTRATIVO
                 admin.py
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
     CONSULTA     ESTADOS    EXPORTACIÓN
     Y FILTROS    DE PQRS       CSV

        MÓDULO DE DATOS Y MODELO
                    |
                    v
          CARGA MASIVA DE DATOS
                    |
                    v
           VALIDACIÓN DE DATOS
                    |
                    v
        EVALUACIÓN DE CANDIDATO
```

El sistema utiliza el modelo guardado para realizar predicciones y una base de datos para conservar la información registrada.

Las funcionalidades de correo permiten comunicar la radicación y los cambios de estado cuando el servicio de notificaciones está configurado correctamente.

## Estructura del repositorio

Los principales archivos y directorios del proyecto son:

```text
pqrs-salud-nlp/
|
|-- app.py
|-- admin.py
|-- requirements.txt
|-- README.md
|
|-- data/
|   |-- pqrs_dataset_sintetico.csv
|   |-- pqrs_nuevos.csv
|   |-- pqrs.db
|
|-- notebooks/
|   |-- Fase2_Modelado_PQRS.ipynb
|
|-- src/
|   |-- preprocesamiento.py
|   |-- ingesta.py
|
|-- models/
|   |-- modelo_urgencia.joblib
|   |-- evaluacion_candidato.json
|
|-- templates/
|   |-- formulario.html
|   |-- admin_login.html
|   |-- admin.html
|   |-- carga.html
|
|-- results/
|-- figs/
```

**Descripción de los componentes principales:**

- `app.py`: aplicación pública de registro y clasificación.
- `admin.py`: aplicación administrativa.
- `src/preprocesamiento.py`: funciones de limpieza y normalización.
- `src/ingesta.py`: procesamiento de nuevas cargas y evaluación.
- `models/modelo_urgencia.joblib`: modelo serializado utilizado por el sistema.
- `models/evaluacion_candidato.json`: información de una evaluación de modelo candidato.
- `data/pqrs.db`: base de datos SQLite.
- `templates/`: interfaces HTML.
- `notebooks/`: experimentación y modelado.
- `results/` y `figs/`: resultados y figuras del análisis.

La estructura anterior resume los componentes principales y no necesariamente todos los archivos auxiliares del repositorio.

## Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/jorgepelaezp/pqrs-salud-nlp.git
cd pqrs-salud-nlp
```

### 2. Crear el entorno virtual

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Descargar recursos de NLTK

```bash
python -c "import nltk; nltk.download('stopwords')"
```

### 5. Ejecutar la aplicación pública

Desde la raíz del proyecto:

```bash
python app.py
```

Dirección de acceso habitual:

http://127.0.0.1:5000

### 6. Ejecutar el panel administrativo

Abrir otra terminal, activar el mismo entorno virtual y ejecutar:

```bash
python admin.py
```

Dirección de acceso habitual:

http://127.0.0.1:5001

Los puertos indicados corresponden a la configuración prevista para el prototipo y pueden variar si se modifican los archivos de ejecución.

**Nota:** Las notificaciones por correo requieren la configuración de las credenciales y variables de entorno correspondientes. No deben publicarse contraseñas, tokens ni secretos en el repositorio.

## Funcionalidades de la aplicación

### 1. Registro público de PQRS

El usuario puede completar un formulario con la información requerida y describir su solicitud.

El sistema procesa el texto, obtiene una predicción de urgencia y registra la solicitud para su seguimiento.

### 2. Clasificación automática

El texto de la PQRS pasa por el procesamiento lingüístico y el modelo de clasificación.

La predicción corresponde a una de las siguientes clases:

- Baja.
- Media.
- Alta.

La urgencia predicha constituye una **recomendación automática de priorización**, no un diagnóstico médico ni una decisión clínica definitiva.

### 3. Radicación y notificaciones

El sistema permite generar un identificador de radicación y comunicar información de la solicitud mediante correo electrónico, según la configuración del servicio.

### 4. Panel administrativo

El administrador puede consultar solicitudes registradas, buscar información, aplicar filtros y gestionar el estado de las PQRS.

También dispone de funciones para exportar información y revisar los datos almacenados.

### 5. Carga masiva de información

El módulo de datos permite incorporar nuevos registros desde archivos compatibles, como CSV y Excel.

El proceso contempla la lectura y validación de registros antes de incorporarlos al conjunto de datos.

Para los conjuntos de entrenamiento de urgencia se utilizan principalmente las columnas:

| Columna | Descripción |
|---|---|
| `texto` | Descripción textual de la PQRS |
| `urgencia` | Etiqueta correspondiente: Baja, Media o Alta |

La carga masiva facilita ampliar el conjunto de ejemplos y realizar nuevas evaluaciones.

### 6. Evaluación de modelos candidatos

El sistema contempla la evaluación de modelos candidatos a partir de los datos disponibles.

Es importante distinguir dos conceptos:

**Modelo desplegado:** modelo serializado que utiliza la aplicación para clasificar solicitudes.

**Modelo candidato:** modelo generado o evaluado durante un proceso de experimentación posterior.

La evaluación de un candidato **no debe interpretarse automáticamente como su despliegue**. La sustitución del modelo activo requiere comprobar que el procedimiento de actualización se haya ejecutado.

## Resultados de la Fase 2

La evaluación original se realizó sobre un conjunto de prueba de **584 registros**.

| Modelo | F1 macro | Recall Alta |
|---|---:|---:|
| Baseline: clase mayoritaria | 0,196 | 0,000 |
| Baseline: palabras clave | 0,349 | 0,655 |
| **Naive Bayes (TF-IDF)** | **0,838** | **0,832** |
| SVM lineal (TF-IDF) | 0,837 | 0,832 |
| Random Forest (TF-IDF) | 0,831 | 0,832 |
| SVD + LDA + Naive Bayes gaussiano | 0,837 | 0,823 |
| SVD + LDA + Random Forest | 0,829 | 0,832 |

### Interpretación

El modelo seleccionado obtuvo un F1 macro de **0,838**, superando el objetivo académico de 0,75.

El recall de la clase Alta fue **0,832** en el conjunto de prueba original, por debajo del objetivo de 0,85.

En validación cruzada se obtuvo un recall Alta de 0,852. Por tanto, el cumplimiento de esta segunda meta no quedó confirmado de forma concluyente por el conjunto de prueba.

La comparación mostró que TF-IDF combinado con Naive Bayes ofrecía un rendimiento competitivo respecto a alternativas más complejas.

Las evaluaciones también evidenciaron que la clasificación de tipo y tema presentaba resultados inferiores, por lo que el prototipo se centra principalmente en la **priorización por urgencia**.

## Evaluación posterior de la Fase 3

Durante la evolución del proyecto se incorporaron nuevos ejemplos sintéticos y se realizaron evaluaciones adicionales.

En una evaluación agrupada posterior se registraron los siguientes resultados:

| Indicador | Resultado |
|---|---:|
| Registros de entrenamiento | 2.523 |
| Registros de prueba | 639 |
| F1 macro | 0,8216 |
| Recall Alta | 0,8492 |

Estos resultados corresponden a una evaluación posterior y **no deben confundirse con los resultados originales de la Fase 2**.

La partición de datos y la composición del conjunto evaluado pueden afectar las métricas. Por ello, las diferencias entre evaluaciones no demuestran por sí solas una mejora o un deterioro del modelo.

### Matriz de confusión

La siguiente matriz corresponde a la evaluación posterior con 639 ejemplos:

| Urgencia real / Predicha | Baja | Media | Alta |
|---|---:|---:|---:|
| **Baja** | **221** | 41 | 0 |
| **Media** | 34 | **195** | 22 |
| **Alta** | 0 | 19 | **107** |

### Interpretación de la matriz

Las filas representan las clases reales y las columnas las clases predichas.

Los valores de la diagonal principal representan clasificaciones correctas:

- 221 solicitudes de urgencia Baja clasificadas correctamente.
- 195 solicitudes de urgencia Media clasificadas correctamente.
- 107 solicitudes de urgencia Alta clasificadas correctamente.

Los valores fuera de la diagonal representan errores de clasificación.

Para la clase Alta:

- Existían 126 solicitudes realmente clasificadas como Alta.
- El modelo identificó correctamente 107.
- Las 19 restantes fueron clasificadas como Media.

Por tanto:

```text
Recall Alta = 107 / (107 + 19)

Recall Alta = 0,8492

Recall Alta ≈ 84,92 %
```

Este indicador es especialmente importante porque permite medir qué proporción de las solicitudes verdaderamente urgentes es detectada por el sistema.

Aunque el resultado se aproxima al objetivo de 0,85, no debe presentarse como una superación estricta de esa meta.

## Evaluaciones posteriores mediante carga masiva

El módulo de carga masiva permite realizar pruebas con nuevos conjuntos de datos.

Para interpretar correctamente los resultados se recomienda registrar:

- Cantidad de registros incorporados.
- Cantidad de registros utilizados para entrenamiento y prueba.
- F1 macro.
- Recall de la clase Alta.
- Matriz de confusión.
- Fecha de evaluación.
- Estado de despliegue del modelo candidato.

Los resultados de cada ejecución deben consultarse en los archivos de evaluación o en la interfaz administrativa.

No se deben atribuir al modelo activo métricas de un candidato que no haya sido desplegado.

## Partición y prevención de duplicados

Durante el modelado se consideró la agrupación de textos equivalentes después de su normalización.

El objetivo es evitar que ejemplos idénticos o equivalentes aparezcan simultáneamente en entrenamiento y prueba, situación que podría producir estimaciones excesivamente optimistas del rendimiento.

En la Fase 2 se utilizaron estrategias de partición y validación agrupada, incluyendo `StratifiedGroupKFold`.

La metodología de cada evaluación debe revisarse junto con sus resultados, especialmente cuando se incorporan nuevos registros.

## Uso del modelo guardado

Ejemplo de carga y predicción:

```python
import joblib
from src.preprocesamiento import preprocesar

modelo = joblib.load("models/modelo_urgencia.joblib")

texto = (
    "Mi madre no ha recibido la insulina "
    "y necesita atención urgente"
)

texto_procesado = preprocesar(texto)

prediccion = modelo.predict([texto_procesado])

print("Urgencia estimada:", prediccion[0])
```

El archivo serializado debe cargarse en un entorno compatible con las versiones de las bibliotecas utilizadas durante su entrenamiento.

Por seguridad, solo deben cargarse modelos Joblib provenientes de fuentes confiables.

## Reproducibilidad

El proyecto conserva el notebook de experimentación:

```text
notebooks/Fase2_Modelado_PQRS.ipynb
```

Para ejecutarlo localmente:

```bash
jupyter notebook notebooks/Fase2_Modelado_PQRS.ipynb
```

El conjunto inicial fue generado con semilla 42 y el notebook contiene los procedimientos utilizados durante el desarrollo de la Fase 2.

Los resultados pueden variar si se modifican los datos, dependencias, hiperparámetros o procedimientos de evaluación.

## Limitaciones

El prototipo presenta las siguientes limitaciones:

1. **Datos sintéticos:** los ejemplos se construyeron artificialmente y pueden no representar la diversidad del lenguaje utilizado en solicitudes reales.
2. **Variación lingüística:** errores ortográficos, expresiones regionales y narraciones complejas pueden afectar la clasificación.
3. **Ambigüedad:** una misma solicitud puede contener información asociada a diferentes niveles de urgencia.
4. **Errores de clasificación:** algunas solicitudes de urgencia Alta pueden clasificarse como Media o Baja.
5. **Generalización:** el desempeño observado con datos sintéticos no garantiza el mismo resultado en un entorno real.
6. **Clasificación de tipo y tema:** los resultados de estas tareas fueron inferiores a los obtenidos en la clasificación de urgencia.
7. **Despliegue:** la evaluación de nuevos candidatos no implica necesariamente la sustitución automática del modelo utilizado por la aplicación.

El generador inicial contempla ruido de etiqueta del 8 % y ambigüedad del 10 %, condiciones que también influyen en el desempeño.

## Consideraciones éticas

El sistema fue desarrollado con fines académicos.

La clasificación automática debe considerarse una herramienta de apoyo y no un mecanismo que sustituya la revisión humana de situaciones que puedan afectar la salud de las personas.

En un eventual despliegue real sería necesario fortalecer:

- Protección de datos personales.
- Control de acceso.
- Seguridad de la información.
- Validación con datos reales autorizados.
- Supervisión humana.
- Evaluación de sesgos.
- Monitoreo de errores, especialmente en urgencias altas.

El prototipo no está validado para tomar decisiones clínicas ni reemplazar sistemas oficiales de atención de emergencias.

## Posibles mejoras

Entre las mejoras futuras se encuentran:

- Evaluación con conjuntos de datos reales, anonimizados y autorizados.
- Ampliación de la variedad lingüística del entrenamiento.
- Mejoras en la detección de solicitudes de alta urgencia.
- Implementación de controles de seguridad adicionales.
- Registro histórico de evaluaciones y versiones de modelos.
- Comparación de nuevos algoritmos de PLN.
- Incorporación de visualizaciones estadísticas adicionales.
- Despliegue en un entorno de producción después de las validaciones correspondientes.

## Conclusiones

El proyecto demuestra la viabilidad técnica de integrar procesamiento del lenguaje natural y aprendizaje automático en un prototipo para la gestión de PQRS del sector salud.

La combinación de TF-IDF y Multinomial Naive Bayes permitió obtener resultados competitivos en la clasificación de urgencia sobre datos sintéticos.

La integración con Flask y SQLite permitió desarrollar una aplicación que conecta el registro público de solicitudes con herramientas de seguimiento administrativo.

Adicionalmente, el módulo de carga masiva facilita incorporar nuevos ejemplos y evaluar candidatos, contribuyendo a la experimentación y al análisis de resultados.

Aunque el sistema presenta limitaciones y requiere validaciones adicionales para un uso real, constituye una prueba de concepto de inteligencia artificial aplicada a la priorización de solicitudes.

## Integrantes

**Grupo 02 — Proyecto de Aula de Inteligencia Artificial**

- Eder David Martínez Molina.
- Víctor Torres Solano.
- Jorge Pelaez.

**Docente:** Lic. Tonny Jiménez  
**Programa:** Ingeniería de Sistemas  
**Lugar y año:** Valledupar, 2026

---

**Nota académica:** Las métricas reportadas corresponden a evaluaciones experimentales con datos sintéticos. No representan una validación clínica ni garantizan el desempeño del sistema en instituciones de salud reales.