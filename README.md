# Clasificación y priorización automática de PQRS en salud mediante PLN

**Proyecto de Aula — Inteligencia Artificial**  
**Programa:** Ingeniería de Sistemas — 7.º semestre  
**Grupo:** 02  
**Docente:** Lic. Tonny Jiménez  
**Ubicación:** Valledupar, Colombia  
**Año:** 2026

---

## 1. Descripción del proyecto

Este proyecto consiste en el desarrollo de un sistema inteligente para la **clasificación y priorización automática de Peticiones, Quejas, Reclamos y Sugerencias (PQRS) en el sector salud colombiano**, utilizando técnicas de Procesamiento del Lenguaje Natural (PLN) y aprendizaje automático.

El objetivo es apoyar la identificación de reclamos relacionados con barreras de acceso a los servicios de salud, teniendo en cuenta el nivel de riesgo que puede representar la situación descrita por el usuario.

El proyecto toma como referencia la **Circular Externa 2023151000000010-5 de 2023 de la Superintendencia Nacional de Salud**, que establece criterios para la clasificación de reclamos en salud según el riesgo y los términos máximos de resolución correspondientes.

La solución integra un modelo de clasificación basado en **TF-IDF y Multinomial Naive Bayes**, una aplicación web pública, un panel administrativo, almacenamiento mediante SQLite, notificaciones por correo electrónico y un módulo de carga masiva de datos.

El sistema constituye un prototipo académico desarrollado con datos sintéticos. No reemplaza la valoración humana, la atención médica ni los procedimientos oficiales de las entidades de salud.

---

## 2. Problemática

En Colombia, las entidades del sector salud reciben solicitudes relacionadas con demoras en citas médicas, falta de medicamentos, negación de procedimientos, problemas de autorizaciones y dificultades en la prestación de servicios.

Estas situaciones pueden representar distintos niveles de riesgo para los pacientes.

Una demora en una consulta administrativa no necesariamente tiene las mismas consecuencias que la interrupción de un tratamiento indispensable o la falta de atención ante una situación que compromete la vida.

Por esta razón, resulta importante contar con mecanismos que permitan identificar y priorizar oportunamente los reclamos de mayor riesgo.

El procesamiento manual de grandes volúmenes de solicitudes puede dificultar esta tarea, especialmente cuando la información se presenta mediante descripciones escritas en lenguaje natural.

El proyecto propone utilizar inteligencia artificial para analizar automáticamente estos textos y generar una clasificación inicial que sirva como apoyo para la gestión de las PQRS.

---

## 3. Fundamentación normativa colombiana

### Circular Externa 2023151000000010-5 de 2023

La Superintendencia Nacional de Salud establece una clasificación de los reclamos en salud de acuerdo con el riesgo asociado a la situación presentada.

Para los reclamos sujetos a esta clasificación se contemplan tres categorías:

| Clasificación | Descripción | Plazo máximo de resolución |
|---|---|---|
| **Riesgo Vital** | Situaciones que representan un riesgo inminente para la vida o integridad del usuario y requieren atención inmediata. | **24 horas** |
| **Riesgo Priorizado** | Situaciones que comprometen la integridad o afectan especialmente a poblaciones vulnerables, entre otros supuestos definidos por la regulación. | **48 horas** |
| **Riesgo Simple** | Manifestaciones de insatisfacción relacionadas con la prestación del servicio que no reúnen los criterios de riesgo vital o priorizado. | **72 horas** |

Los plazos representan límites máximos de resolución para los reclamos comprendidos en estas categorías. No deben interpretarse como una autorización para retrasar la atención cuando la situación requiere una intervención inmediata.

**Importante:** estos términos no se aplican indistintamente a todas las peticiones, solicitudes de información o trámites administrativos. Su aplicación depende de la naturaleza del reclamo y del marco normativo correspondiente.

### Relación con el modelo de inteligencia artificial

El modelo desarrollado utiliza internamente las etiquetas:

- `Alta`
- `Media`
- `Baja`

Estas etiquetas se interpretan en el prototipo mediante la siguiente correspondencia:

| Etiqueta del modelo | Categoría de referencia | Plazo normativo |
|---|---|---|
| Alta | Riesgo Vital | 24 horas |
| Media | Riesgo Priorizado | 48 horas |
| Baja | Riesgo Simple | 72 horas |

Esta correspondencia permite relacionar las predicciones del clasificador con los niveles de riesgo utilizados como referencia normativa.

Sin embargo, **la correspondencia entre etiquetas no demuestra por sí sola que el modelo cumpla todos los criterios jurídicos de clasificación**. Para ello sería necesario verificar que los datos, las reglas de etiquetado y los procedimientos de gestión reflejen correctamente los supuestos establecidos por la regulación.

El sistema proporciona una estimación automática que debe estar sujeta a revisión humana, especialmente en situaciones de riesgo vital.

### Referencia normativa

Superintendencia Nacional de Salud. (2023). *Circular Externa 2023151000000010-5 de 2023*.

Documento oficial:

https://docs.supersalud.gov.co/PortalWeb/Juridica/CircularesExterna/Circular%20Externa%20No.%202023151000000010-5%20de%202023.pdf

---

## 4. Objetivos

### Objetivo general

Desarrollar un prototipo de inteligencia artificial basado en procesamiento del lenguaje natural que permita clasificar y priorizar automáticamente las PQRS del sector salud colombiano, tomando como referencia los niveles de riesgo establecidos por la Superintendencia Nacional de Salud.

### Objetivos específicos

1. Analizar la problemática relacionada con la clasificación y priorización de reclamos en el sector salud.
2. Construir un conjunto de datos sintéticos que represente diferentes situaciones relacionadas con la prestación de servicios de salud.
3. Implementar técnicas de limpieza, normalización y procesamiento del lenguaje natural.
4. Entrenar y comparar modelos supervisados para la clasificación de urgencia.
5. Evaluar el desempeño mediante métricas como precisión, recall y F1 macro.
6. Integrar el modelo seleccionado en una aplicación web funcional.
7. Implementar herramientas de registro, seguimiento y gestión administrativa de PQRS.
8. Desarrollar un módulo de carga masiva que facilite incorporar nuevos datos y realizar evaluaciones posteriores.

---

## 5. Estado del proyecto

**Estado actual: Fase 3 — Prototipo funcional integrado**

| Fase | Actividades principales | Estado |
|---|---|---|
| **Fase 1** | Planteamiento del problema, revisión normativa, generación de datos y análisis exploratorio | Completada |
| **Fase 2** | Preprocesamiento, entrenamiento, comparación de algoritmos y evaluación | Completada |
| **Fase 3** | Integración web, panel administrativo, almacenamiento, notificaciones y carga masiva | Implementada |

Las tres fases conforman una prueba de concepto que integra la experimentación con inteligencia artificial y el desarrollo de software.

---

## 6. Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Python | Lenguaje principal del proyecto |
| Flask | Desarrollo de las aplicaciones web y sus API |
| scikit-learn | Entrenamiento y evaluación de clasificadores |
| NLTK | Procesamiento del lenguaje natural |
| TF-IDF | Vectorización de textos |
| Multinomial Naive Bayes | Modelo seleccionado para clasificación |
| Pandas | Procesamiento y análisis de datos |
| NumPy | Operaciones numéricas |
| SQLite | Almacenamiento de PQRS |
| SQLAlchemy | Interacción con la base de datos |
| Joblib | Serialización del modelo |
| HTML | Estructura de las interfaces |
| CSS | Diseño visual |
| JavaScript | Interacción dinámica con las API |
| Jupyter Notebook | Experimentación y análisis de resultados |

---

## 7. Metodología de desarrollo

### Fase 1 — Planteamiento, datos y análisis exploratorio

Se identificó la necesidad de mejorar los procesos de clasificación de reclamos en el sector salud, considerando las diferencias entre situaciones administrativas y casos que pueden representar riesgos importantes para los pacientes.

Se construyó un conjunto inicial de **3.000 registros sintéticos**, generado con semilla 42 para favorecer la reproducibilidad.

Los ejemplos representan situaciones relacionadas con:

- Medicamentos y tratamientos.
- Citas médicas.
- Autorizaciones de procedimientos.
- Atención de urgencias.
- Demoras en la prestación de servicios.
- Trámites y solicitudes administrativas.

Los registros contienen textos descriptivos y etiquetas de clasificación.

Posteriormente se realizó un análisis exploratorio para revisar la distribución de los datos, identificar patrones y preparar la información para el entrenamiento.

### Fase 2 — Procesamiento del lenguaje natural y modelado

#### Preprocesamiento

El texto de cada PQRS se transforma mediante procedimientos de limpieza y normalización.

Entre las operaciones utilizadas se encuentran:

- Conversión a minúsculas.
- Normalización de caracteres.
- Eliminación de elementos innecesarios.
- Tratamiento de palabras vacías o *stopwords*.
- Reducción de variaciones lingüísticas.
- Conservación de negaciones relevantes.

El propósito es reducir el ruido de los textos sin eliminar información importante para la clasificación.

#### Vectorización TF-IDF

Se utiliza **TF-IDF (Term Frequency–Inverse Document Frequency)** para convertir las descripciones escritas en representaciones numéricas.

TF-IDF asigna pesos a los términos según su importancia dentro de un documento y su frecuencia en el conjunto de textos.

De esta manera, los algoritmos de aprendizaje automático pueden procesar las solicitudes.

#### Algoritmos evaluados

Se compararon diferentes modelos y estrategias:

1. Clasificador de clase mayoritaria.
2. Clasificador basado en palabras clave.
3. Multinomial Naive Bayes con TF-IDF.
4. SVM lineal con TF-IDF.
5. Random Forest con TF-IDF.
6. Combinaciones de SVD, LDA y clasificadores supervisados.

#### Modelo seleccionado

Se seleccionó **TF-IDF + Multinomial Naive Bayes**.

Esta combinación ofrece un desempeño competitivo, requiere recursos computacionales moderados y permite integrar el clasificador en una aplicación web sin una infraestructura compleja.

### Fase 3 — Integración y aplicación funcional

La tercera fase consistió en integrar el modelo de clasificación en un sistema web para registrar, consultar y gestionar solicitudes.

Se desarrollaron dos componentes principales:

**Aplicación pública**

Permite registrar una PQRS, procesar su descripción, obtener una clasificación automática y generar un radicado.

**Aplicación administrativa**

Permite consultar solicitudes, aplicar filtros, actualizar estados, exportar información y acceder al módulo de carga masiva y evaluación.

Ambas aplicaciones utilizan la infraestructura de almacenamiento y los componentes desarrollados durante las fases anteriores.

---

## 8. Arquitectura del sistema

```text
                     USUARIO
                        |
                        v
                 FORMULARIO WEB
                     app.py
                        |
                        v
                REGISTRO DE PQRS
                        |
              +---------+---------+
              |                   |
              v                   v
       PROCESAMIENTO PLN      BASE DE DATOS
              |                 SQLite
              v                   |
         VECTOR TF-IDF            |
              |                   |
              v                   |
       MULTINOMIAL NAIVE BAYES    |
              |                   |
              v                   |
       CLASIFICACIÓN AUTOMÁTICA   |
              |                   |
              +---------+---------+
                        |
                        v
                 RADICACIÓN Y
                  SEGUIMIENTO
                        |
                        v
               PANEL ADMINISTRATIVO
                     admin.py
                        |
           +------------+------------+
           |            |            |
           v            v            v
        CONSULTA     GESTIÓN DE   EXPORTACIÓN
        Y FILTROS     ESTADOS        CSV

               MÓDULO DE DATOS
                        |
                        v
                CARGA MASIVA
                        |
                        v
               VALIDACIÓN DE DATOS
                        |
                        v
             EVALUACIÓN DE CANDIDATO
```

La clasificación automática se utiliza como apoyo a la priorización de solicitudes.

El modelo no determina por sí mismo el cumplimiento de los plazos normativos ni reemplaza la intervención de las entidades responsables.

---

## 9. Estructura del repositorio

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

### Archivos principales

| Archivo | Descripción |
|---|---|
| `app.py` | Aplicación pública de registro de PQRS |
| `admin.py` | Aplicación administrativa |
| `src/preprocesamiento.py` | Limpieza y normalización del texto |
| `src/ingesta.py` | Ingesta de datos y evaluación |
| `models/modelo_urgencia.joblib` | Modelo serializado |
| `models/evaluacion_candidato.json` | Resultados de evaluación de un candidato |
| `data/pqrs.db` | Base de datos SQLite |
| `templates/formulario.html` | Formulario público |
| `templates/admin_login.html` | Acceso administrativo |
| `templates/admin.html` | Panel administrativo |
| `templates/carga.html` | Carga masiva y evaluación |

La estructura muestra los componentes principales del proyecto y puede incluir archivos auxiliares adicionales.

---

## 10. Instalación y ejecución

### Requisitos

- Python 3.
- Git.
- Dependencias incluidas en `requirements.txt`.
- Navegador web.

### Paso 1. Clonar el repositorio

```bash
git clone https://github.com/jorgepelaezp/pqrs-salud-nlp.git
cd pqrs-salud-nlp
```

### Paso 2. Crear el entorno virtual

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

### Paso 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### Paso 4. Descargar recursos de NLTK

```bash
python -c "import nltk; nltk.download('stopwords')"
```

### Paso 5. Ejecutar la aplicación pública

```bash
python app.py
```

Acceso habitual:

http://127.0.0.1:5000

### Paso 6. Ejecutar el panel administrativo

En una segunda terminal, con el entorno virtual activado:

```bash
python admin.py
```

Acceso habitual:

http://127.0.0.1:5001

Los puertos pueden variar dependiendo de la configuración de los servidores.

**Nota:** El envío de correos electrónicos requiere la configuración correspondiente. Las credenciales y contraseñas no deben almacenarse públicamente en GitHub.

---

## 11. Funcionalidades del sistema

### 11.1. Formulario público de PQRS

El formulario permite registrar información de la solicitud, incluyendo datos de contacto y descripción del caso.

Al enviarla, el sistema procesa el texto y obtiene una clasificación automática de urgencia.

La solicitud se almacena para su posterior seguimiento.

### 11.2. Clasificación automática de riesgo

El modelo analiza el contenido de la descripción y genera una de las tres etiquetas internas:

- Alta.
- Media.
- Baja.

Estas etiquetas se relacionan, como referencia de diseño, con Riesgo Vital, Riesgo Priorizado y Riesgo Simple.

La predicción es una estimación estadística. No sustituye una valoración clínica ni determina automáticamente la categoría jurídica definitiva de un reclamo.

### 11.3. Generación de radicado

El sistema genera un identificador para facilitar la consulta y el seguimiento de la solicitud registrada.

### 11.4. Notificaciones por correo electrónico

La aplicación contempla el envío de mensajes relacionados con la radicación y las actualizaciones del estado de las solicitudes.

Esta funcionalidad depende de la correcta configuración del servicio de correo.

### 11.5. Panel administrativo

El administrador dispone de herramientas para:

- Consultar las PQRS registradas.
- Buscar solicitudes.
- Filtrar información.
- Revisar la clasificación automática.
- Actualizar estados.
- Consultar información de seguimiento.
- Exportar registros.

### 11.6. Exportación de datos

El sistema permite exportar información de solicitudes en formato CSV para su análisis y seguimiento.

### 11.7. Carga masiva de datos

El módulo de datos permite incorporar nuevos registros desde archivos compatibles, como Excel y CSV.

Para la clasificación de urgencia se utilizan principalmente las siguientes columnas:

| Columna | Contenido |
|---|---|
| `texto` | Descripción de la PQRS |
| `urgencia` | Etiqueta Baja, Media o Alta |

El proceso permite validar registros antes de incorporarlos al conjunto de datos.

### 11.8. Evaluación de modelos candidatos

El sistema permite realizar evaluaciones utilizando los datos disponibles.

Es importante diferenciar:

**Modelo desplegado:** modelo guardado que utiliza la aplicación para realizar predicciones.

**Modelo candidato:** modelo generado o evaluado a partir de los datos disponibles durante una nueva experimentación.

La evaluación de un candidato no implica necesariamente que se reemplace el modelo activo.

---

## 12. Resultados del modelo — Fase 2

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

El modelo seleccionado obtuvo un **F1 macro de 0,838**, superando el objetivo académico de 0,75.

El recall de la clase Alta fue de 0,832 en el conjunto de prueba original.

En validación cruzada se obtuvo un recall Alta de 0,852.

Por lo tanto, aunque los resultados son cercanos al objetivo de 0,85, el conjunto de prueba original no permitió confirmar estrictamente su cumplimiento.

La selección de Naive Bayes se fundamentó en su desempeño competitivo y su facilidad de integración.

### Clasificación de tipo y tema

Durante la experimentación también se evaluaron tareas de clasificación de tipo y tema.

Los resultados fueron inferiores a los obtenidos para urgencia:

| Tarea | F1 macro |
|---|---:|
| Tipo | 0,235 |
| Tema | 0,362 |

Por esta razón, el componente principal de inteligencia artificial se concentra en la clasificación de urgencia.

---

## 13. Evaluación posterior — Fase 3

Durante la evolución del proyecto se incorporaron nuevos ejemplos sintéticos y se realizaron evaluaciones adicionales.

En una evaluación posterior, utilizando una partición agrupada, se registraron los siguientes resultados:

| Indicador | Resultado |
|---|---:|
| Registros de entrenamiento | 2.523 |
| Registros de prueba | 639 |
| F1 macro | 0,8216 |
| Recall Alta | 0,8492 |

Esta evaluación es diferente de la realizada originalmente durante la Fase 2.

Los resultados deben interpretarse teniendo en cuenta los datos, la partición utilizada y el procedimiento experimental correspondiente.

No se debe asumir que las métricas de un candidato representan automáticamente el rendimiento del modelo desplegado.

---

## 14. Matriz de confusión

La matriz de confusión permite analizar los aciertos y errores del clasificador.

En la evaluación posterior de 639 registros se obtuvo:

| Clase real / Predicha | Baja | Media | Alta |
|---|---:|---:|---:|
| **Baja** | **221** | 41 | 0 |
| **Media** | 34 | **195** | 22 |
| **Alta** | 0 | 19 | **107** |

### ¿Cómo se interpreta?

Las filas representan las categorías reales y las columnas las categorías predichas.

Los valores de la diagonal principal indican los aciertos del modelo.

Los valores fuera de la diagonal representan errores.

En esta evaluación:

- 221 registros de clase Baja fueron clasificados correctamente.
- 195 registros de clase Media fueron clasificados correctamente.
- 107 registros de clase Alta fueron clasificados correctamente.
- 19 registros realmente clasificados como Alta fueron predichos como Media.

### Recall de la clase Alta

El recall permite conocer qué proporción de los casos realmente pertenecientes a una clase fue identificada correctamente.

Para la clase Alta:

```text
Recall Alta = Verdaderos positivos / Total de casos Alta

Recall Alta = 107 / 126

Recall Alta = 0,8492

Recall Alta = 84,92 %
```

Este indicador es especialmente relevante porque la clase Alta se utiliza como representación interna del nivel de riesgo más crítico.

Aunque el modelo identificó correctamente una proporción importante de estos casos, los errores restantes muestran la necesidad de supervisión humana.

La evaluación con datos sintéticos no garantiza el mismo comportamiento en situaciones reales.

---

## 15. Métricas de evaluación

### Accuracy

Representa la proporción total de predicciones correctas.

### Precisión

Mide qué proporción de los registros clasificados por el modelo en una categoría realmente pertenece a ella.

### Recall

Mide qué proporción de los registros reales de una categoría fue detectada correctamente.

En este proyecto se presta especial atención al recall de la clase Alta, debido a la importancia de identificar solicitudes potencialmente críticas.

### F1-score

Combina precisión y recall mediante su media armónica.

### F1 macro

Calcula el promedio del F1-score de todas las clases, otorgándoles el mismo peso.

Esta métrica permite evaluar el desempeño global sin depender exclusivamente de la clase más frecuente.

---

## 16. Reproducibilidad

El notebook principal de experimentación se encuentra en:

```text
notebooks/Fase2_Modelado_PQRS.ipynb
```

Para ejecutarlo:

```bash
jupyter notebook notebooks/Fase2_Modelado_PQRS.ipynb
```

El conjunto inicial fue generado utilizando semilla 42.

El notebook contiene los procedimientos de preparación de datos, entrenamiento, comparación y evaluación de modelos.

Los resultados pueden variar si se modifican los datos, las versiones de las bibliotecas o los procedimientos de evaluación.

### Uso del modelo guardado

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

print("Clasificación:", prediccion[0])
```

Los modelos serializados deben cargarse únicamente desde fuentes confiables y con versiones compatibles de las dependencias utilizadas durante su entrenamiento.

---

## 17. Limitaciones

El proyecto presenta las siguientes limitaciones:

1. **Datos sintéticos:** los ejemplos no representan completamente la diversidad de solicitudes reales.
2. **Errores de clasificación:** el modelo puede confundir categorías, incluso cuando una solicitud presenta condiciones potencialmente críticas.
3. **Ambigüedad lingüística:** algunas descripciones pueden contener información insuficiente o contradictoria.
4. **Dependencia del entrenamiento:** las predicciones están condicionadas por los patrones presentes en los datos utilizados.
5. **Generalización:** las métricas obtenidas con datos sintéticos no garantizan el desempeño con reclamos reales.
6. **Correspondencia normativa:** las etiquetas internas Alta, Media y Baja requieren validación adicional para comprobar su alineación con todos los criterios establecidos por la Superintendencia Nacional de Salud.
7. **Gestión de plazos:** la clasificación automática no equivale a garantizar que una EPS o IPS resuelva efectivamente los reclamos dentro de los términos legales.
8. **Clasificación de tipo y tema:** estas tareas presentaron un desempeño inferior al de urgencia.

El generador inicial de datos contempla un 8 % de ruido de etiqueta y un 10 % de ambigüedad.

Por estas razones, el sistema debe considerarse una prueba de concepto y no una herramienta validada para su uso autónomo en la gestión real de reclamos de salud.

---

## 18. Consideraciones éticas y legales

El sistema fue desarrollado con fines académicos y de experimentación.

La información utilizada para el entrenamiento y las evaluaciones documentadas es sintética.

En un eventual despliegue real sería necesario considerar:

- Protección de datos personales.
- Confidencialidad de la información de salud.
- Seguridad de las aplicaciones.
- Control de acceso administrativo.
- Validación del modelo con datos reales autorizados.
- Evaluación de sesgos y errores.
- Supervisión humana.
- Procedimientos para identificar y escalar situaciones críticas.
- Verificación del cumplimiento de las obligaciones legales aplicables.

El proyecto toma como referencia la normativa colombiana de clasificación de reclamos en salud, pero no constituye una certificación de cumplimiento regulatorio.

---

## 19. Mejoras futuras

Entre las posibles mejoras se encuentran:

1. Ampliar el conjunto de datos con ejemplos diversos y representativos.
2. Evaluar el modelo con datos reales debidamente anonimizados y autorizados.
3. Mejorar el recall de la categoría correspondiente al riesgo vital.
4. Incorporar mecanismos de revisión y escalamiento de solicitudes críticas.
5. Registrar versiones y resultados históricos de los modelos.
6. Fortalecer la seguridad y los controles de acceso.
7. Implementar seguimiento de los plazos normativos aplicables.
8. Desarrollar visualizaciones adicionales para el análisis administrativo.
9. Evaluar algoritmos más avanzados de procesamiento del lenguaje natural.

---

## 20. Conclusiones

El proyecto permitió desarrollar un prototipo funcional que integra procesamiento del lenguaje natural, aprendizaje automático y desarrollo web para apoyar la clasificación y priorización de PQRS del sector salud.

La combinación de **TF-IDF y Multinomial Naive Bayes** obtuvo resultados competitivos en la clasificación de urgencia sobre datos sintéticos.

La aplicación permite registrar solicitudes, generar radicados, consultar información desde un panel administrativo y realizar operaciones de seguimiento.

El módulo de carga masiva amplía las posibilidades de experimentación al facilitar la incorporación de nuevos registros y la evaluación de modelos candidatos.

Uno de los elementos centrales del proyecto es su fundamentación en la clasificación de riesgo utilizada por la **Superintendencia Nacional de Salud de Colombia**, que diferencia los reclamos de riesgo vital, priorizado y simple.

Sin embargo, la alineación normativa completa y el uso del sistema en instituciones reales requerirían validaciones adicionales, procedimientos de supervisión humana y controles operativos.

En conclusión, el proyecto demuestra cómo la inteligencia artificial puede servir como herramienta de apoyo para identificar solicitudes potencialmente críticas y contribuir al análisis de información en el sector salud.

---

## 21. Integrantes

**Grupo 02 — Proyecto de Aula de Inteligencia Artificial**

- Eder David Martínez Molina.
- Víctor Torres Solano.
- Jorge Pelaez.

**Docente:** Lic. Tonny Jiménez  
**Programa:** Ingeniería de Sistemas  
**Valledupar, Colombia — 2026**

---

## 22. Referencias

**Superintendencia Nacional de Salud. (2023).** *Circular Externa 2023151000000010-5 de 2023*. https://docs.supersalud.gov.co/PortalWeb/Juridica/CircularesExterna/Circular%20Externa%20No.%202023151000000010-5%20de%202023.pdf

**Pedregosa, F., et al. (2011).** Scikit-learn: Machine Learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830. https://jmlr.org/papers/v12/pedregosa11a.html

**Scikit-learn Developers.** *Feature extraction from text*. https://scikit-learn.org/stable/modules/feature_extraction.html

**Scikit-learn Developers.** *Naive Bayes*. https://scikit-learn.org/stable/modules/naive_bayes.html

**Pallets Projects.** *Flask documentation*. https://flask.palletsprojects.com/

**NLTK Project.** *Natural Language Toolkit*. https://www.nltk.org/

---

**Aviso:** Este repositorio corresponde a un proyecto académico de investigación y desarrollo. Las clasificaciones automáticas son estimaciones experimentales y no sustituyen la valoración humana ni las obligaciones legales de las entidades responsables de la atención en salud.