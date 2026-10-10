# Predicción de compras en sesiones de navegación

Proyecto académico para estimar si una sesión de navegación en una tienda en línea terminará en una compra (`Revenue`). Incluye auditoría y análisis de los datos, preparación de las particiones, comparación de modelos, evaluación final, interpretación y visualizaciones en un notebook.

**Repositorio:** [github.com/noomdalv/clasificador_intencion_compras](https://github.com/noomdalv/clasificador_intencion_compras)

## Guía rápida para revisar el proyecto

1. Lee `informes/conclusiones.md` para conocer el objetivo, las decisiones metodológicas, los resultados y sus límites.
2. Abre `notebook_visualizaciones.ipynb` para revisar las gráficas y el resumen de resultados. Necesita `datos/preparados/entrenamiento.csv` e `informes/evaluacion_final.json`.
3. Consulta los informes de `informes/` para ver la auditoría, el análisis exploratorio, la comparación de modelos, la evaluación final y la interpretación.
4. Revisa `clasificador_compras/` y `ejecutables/` para seguir la implementación.

Para ejecutar el proyecto en otra computadora, crea un entorno de Python e instala `requirements.txt` siguiendo la sección **Preparar Python en una computadora nueva**. El entorno `.venv/` no se incluye en GitHub porque cada persona debe crearlo localmente. El `.gitignore` también excluye archivos temporales de Python.

Al publicar el repositorio, conserva los datos originales y preparados, los informes, el modelo guardado, el notebook, el código y `requirements.txt`: juntos permiten revisar los resultados y entender cómo se generaron. El ZIP descargado de UCI es opcional si ya incluyes el CSV original extraído. Mantén la atribución y la licencia del dataset indicadas más abajo.

## Fuente y atribución

- Dataset: [Online Shoppers Purchasing Intention Dataset](https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset)
- Autores: C. Sakar y Yomi Kastro (2018).
- DOI: <https://doi.org/10.24432/C5F88Q>
- Licencia indicada por UCI: Creative Commons Attribution 4.0 International (CC BY 4.0). Al redistribuir datos o resultados derivados, incluir la atribución correspondiente.
- Ficha UCI verificada el 10 de octubre de 2026: 12,330 sesiones, 17 variables predictoras, sin valores faltantes reportados; 10,422 sesiones sin compra y 1,908 con compra.

## Descargar y auditar

Desde esta carpeta, ejecuta:

```powershell
python ejecutables/revisar_datos.py
```

El script usa solo la biblioteca estándar de Python. Descarga el ZIP oficial en `datos/originales/`, extrae el CSV original en la misma carpeta y escribe el resumen de auditoría en `informes/auditoria_datos.json`.

La auditoría comprueba filas, columnas, campos vacíos, etiquetas, duplicados exactos, tamaño y la relación entre `PageValues` y `Revenue`. Esa relación se reporta como señal para revisar posible fuga de información, no como prueba concluyente por sí sola.

## Resultado de la auditoría inicial

La descarga e inspección directa se completaron desde Cursor. El CSV contiene 12,330 filas y las 18 columnas esperadas, incluidos 17 predictores y `Revenue`; el script no encontró campos vacíos o desconocidos. El archivo ocupa 1,072,063 bytes (aprox. 1.07 MB). La estimación de 9.48 MiB corresponde al tamaño aproximado de los valores como cadenas de Python, no al uso de memoria de un DataFrame.

`Revenue=False`: 10,422 sesiones (84.53%). `Revenue=True`: 1,908 (15.47%). Hay 125 filas completas repetidas después de la primera aparición. Se conservan por ahora: sin identificador de sesión, no se puede concluir que sean registros erróneos o sesiones duplicadas.

`PageValues` es distinto de cero en 1,538/1,908 sesiones con compra y en 1,192/10,422 sin compra. Es una asociación fuerte, pero no una prueba de fuga por sí sola. Como su definición UCI se vincula a páginas visitadas antes de completar una transacción, se recomienda decidir explícitamente el momento de predicción antes de incluirla en el modelo.

Los resultados completos están en `informes/auditoria_datos.json`. Esta etapa confirma la fuente, la licencia declarada por UCI y las propiedades básicas del CSV; todavía no incluye limpieza, partición, entrenamiento ni dashboard.

## Análisis exploratorio

Ejecuta desde esta carpeta:

```powershell
python ejecutables/explorar_datos.py
```

El resumen se guarda en `informes/resumen_exploratorio.md`. Incluye el balance de clases, tasas de compra por categoría y comparaciones de mediana y promedio para variables numéricas. Las diferencias son descriptivas: no demuestran que una variable cause una compra.

Como siguiente metodología de evaluación, se propone reservar 20% para prueba final y usar una división estratificada para mantener aproximadamente el mismo balance de compras. Las filas idénticas se mantendrán; al construir esa partición habrá que evitar que una copia quede en entrenamiento y otra en prueba. Las transformaciones se ajustarán solo con entrenamiento para evitar fuga de información.

## Notebook de visualizaciones

Puedes abrir `notebook_visualizaciones.ipynb` en cualquier editor o aplicación que admita notebooks `.ipynb`; no hace falta usar Cursor. Por ejemplo, puedes usar JupyterLab o VS Code con el soporte para notebooks habilitado.

### Preparar Python en una computadora nueva

El archivo `.gitignore` excluye `.venv/` intencionalmente. Esa carpeta contiene una instalación local de Python y sus bibliotecas; no se comparte al descargar el proyecto. Cada persona crea su propio entorno y lo prepara con la lista de dependencias del proyecto.

En Windows, desde la carpeta principal del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

En macOS o Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

**Seleccionar el intérprete o kernel** significa indicarle al editor qué instalación de Python debe usar al ejecutar las celdas. Elige la de `.venv`, creada en el paso anterior; ahí quedan disponibles pandas, matplotlib y el soporte de kernel que instala `requirements.txt`.

El notebook espera que la carpeta del proyecto incluya `datos/preparados/entrenamiento.csv` e `informes/evaluacion_final.json`. Si lo abres en un servicio remoto como Colab, también tendrás que subir esos archivos conservando esa estructura de carpetas o ajustar las rutas del notebook.

El notebook usa solo el archivo de entrenamiento para describir los datos y lee las métricas finales ya guardadas en `informes/evaluacion_final.json`; no vuelve a abrir ni evaluar `prueba.csv`.

Incluye cuatro gráficos: balance de compras en entrenamiento, tasa de compra por mes y tipo de visitante, y matriz de confusión de la evaluación final registrada. Cada uno tiene una explicación y una nota para no confundir asociaciones con causas. La última sección presenta conclusiones directas en formato de reporte.

## Partición de entrenamiento y prueba

Ejecuta:

```powershell
python ejecutables/preparar_division.py
```

El script guarda `datos/preparados/entrenamiento.csv`, `datos/preparados/prueba.csv` y el resumen `informes/resumen_division.json`. Usa una semilla fija (`42`) para que la misma versión del CSV produzca la misma separación. Mantiene juntos todos los registros con el mismo vector de predictores del modelo, excluye `PageValues` y conserva `Revenue` como objetivo. La asignación busca mantener el balance de clases y una proporción de prueba de 20%.

Resultado de la primera ejecución: 9,864 sesiones para entrenamiento y 2,466 para prueba. Entrenamiento tiene 15.47% de compras y prueba 15.49%. No hay vectores de predictores idénticos en ambos grupos. La prueba queda reservada para una evaluación final; no se debe usar para elegir variables o ajustar el modelo.

## Entorno de Python y primer modelo de referencia

Para preparar las variables y comparar un primer modelo se requieren pandas y scikit-learn. En PowerShell, desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python ejecutables/validacion_inicial.py
```

`validacion_inicial.py` compara una regla que siempre predice “sin compra” con una regresión logística. Usa validación cruzada agrupada sobre entrenamiento; cada partición aprende sus propias codificaciones y escalas. El conjunto de prueba final no se utiliza. Los resultados se guardarán en `informes/validacion_inicial.md` y `informes/validacion_inicial.json`.

Primera ejecución: el modelo mayoritario logró 84.53% de exactitud y 0% de recall de compra; la regresión logística balanceada logró 64.78% de exactitud, 26.71% de precisión, 73.00% de recall, F1 de 0.391, ROC-AUC de 0.748 y average precision de 0.327. Es un primer punto de referencia: recupera muchas compras, con bastantes falsas alarmas. Estos valores provienen de cinco particiones de entrenamiento y no son la evaluación final en `prueba.csv`.

## Comparar modelos y umbrales

Ejecuta:

```powershell
.\.venv\Scripts\python.exe ejecutables/comparar_modelos.py
```

Este paso compara la regla mayoritaria, regresión logística normal y balanceada, y un árbol balanceado poco profundo. También muestra cómo cambia la regresión logística balanceada al variar el umbral entre 0.20 y 0.70. Usa predicciones fuera de muestra de validación cruzada agrupada sobre entrenamiento; no usa el conjunto de prueba final. Los resultados quedan en `informes/comparacion_modelos.md` y `informes/comparacion_modelos.json`.

En la primera ejecución, con umbral 0.50, el logístico balanceado obtuvo F1 0.391 y recall 0.730; el árbol pequeño obtuvo F1 0.390 y recall 0.699. Para el logístico balanceado, umbral 0.60 dio F1 0.398, precisión 0.313 y recall 0.544. No se declara un umbral definitivo: hay que elegirlo según el costo relativo de dejar pasar compras y generar falsas alarmas.

## Evaluación final

La configuración candidata se fijó antes de abrir el conjunto de prueba: regresión logística balanceada, umbral 0.60. Se ajustó con las 9,864 sesiones de entrenamiento y se evaluó una vez con las 2,466 sesiones reservadas. Resultado: exactitud 75.22%, precisión 31.62%, recall 51.57%, F1 0.392, ROC-AUC 0.763 y average precision 0.326. Detectó 197 compras, omitió 185 y produjo 426 falsas alarmas. La regla “siempre no compra” logró 84.51% de exactitud pero recall cero.

El informe está en `informes/evaluacion_final.md` y `informes/evaluacion_final.json`; las predicciones fila por fila están en `informes/predicciones_prueba.csv`. El pipeline ajustado quedó en `modelos/regresion_logistica_balanceada_umbral_060.joblib`. La prueba ya se utilizó para la evaluación final; no debe emplearse ahora para cambiar el umbral o elegir otro modelo. Cualquier ajuste adicional debe hacerse con validación cruzada y requeriría un nuevo conjunto de prueba independiente para volver a medir de forma imparcial.

## Decisión de alcance: momento de predicción

El objetivo será estimar si una sesión terminará en compra antes de que finalice. Por ello, `PageValues` se excluirá del conjunto de variables del modelo principal, porque su significado puede depender de información disponible al cierre o tras una transacción. En una etapa posterior se podrá entrenar una variante secundaria con `PageValues` para medir su efecto y discutir el riesgo de fuga; esa comparación no cambiará la definición del modelo principal.

## Interpretación del modelo

Ejecuta `python ejecutables/interpretar_modelo.py` con el entorno `.venv` activo. Lee el pipeline entrenado y el conjunto de entrenamiento, nunca el conjunto de prueba. Genera `informes/interpretacion_modelo.md` y `informes/pesos_variables.csv`. Los coeficientes explican cómo el modelo construye su score, no efectos causales. Revisa el número de sesiones de cada categoría: algunos pesos grandes corresponden a niveles poco frecuentes y pueden ser inestables.

## Informe final del proyecto

La síntesis para presentar o estudiar está en `informes/conclusiones.md`. Resume el objetivo, el dataset y su licencia, las decisiones de preparación, los resultados de validación y prueba, la interpretación, las limitaciones y los comandos para reproducir el flujo.

## Refactorización a POO

Las responsabilidades reutilizables viven en el paquete `clasificador_compras/`; los archivos de `ejecutables/` son puntos de entrada que permiten ejecutar cada paso desde la terminal o Cursor.

- `RutasProyecto` centraliza las carpetas del proyecto.
- `AuditorDatos` obtiene el archivo de UCI y crea la auditoría inicial.
- `AnalizadorExploratorio` calcula resúmenes y relaciones descriptivas del dataset.
- `DivisorDatos` agrupa sesiones con los mismos predictores y prepara entrenamiento/prueba sin permitir que un grupo aparezca en ambos.
- `ConfiguracionModelo` concentra decisiones compartidas, como objetivo, tipos de variables, semilla, pliegues y umbral.
- `FabricaModelos` crea los preprocesadores, modelos y estrategia de validación cruzada.
- `InterpreteModelo` explica los coeficientes del modelo usando el artefacto y el conjunto de entrenamiento; no lee el conjunto de prueba.

Los nombres de módulos, clases, funciones, carpetas y archivos propios están en español para que el proyecto sea más fácil de seguir. Conservamos en inglés los nombres originales de las columnas de UCI y los nombres que exige scikit-learn; traducirlos impediría conectar el código con esos datos y herramientas.

La refactorización organiza el flujo y evita mantener copias de la misma lógica en varios scripts. Las comprobaciones después de los cambios se limitan al flujo de datos y a la validación cruzada; la evaluación final no se repite para no volver a consultar el conjunto de prueba.
