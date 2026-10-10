# Clasificación de intención de compra en sesiones de navegación

## Resumen

Este proyecto construyó un clasificador para estimar si una sesión de navegación en una tienda en línea terminó en una compra. Se utilizó el *Online Shoppers Purchasing Intention Dataset* de UCI, con 12,330 sesiones. La variable objetivo es `Revenue`: `True` indica compra y `False`, ausencia de compra.

El conjunto está desbalanceado: 15.47% de las sesiones terminaron en compra. Por eso no evaluamos el clasificador solo con exactitud. Comparamos una regresión logística, un árbol de decisión pequeño y una regla base. La configuración final fue una regresión logística balanceada con umbral 0.60. En la prueba reservada alcanzó 75.22% de exactitud, 31.62% de precisión, 51.57% de recall de compra y F1 de 0.392. Detectó 197 compras de 382 y generó 426 falsas alarmas.

El modelo detecta compras mejor que la regla que siempre predice “no compra”, pero todavía produce muchas alertas incorrectas y omite casi la mitad de las compras. Es una demostración académica, no una solución lista para decisiones comerciales.

## 1. Objetivo y alcance

La pregunta del proyecto es: **¿podemos estimar, usando datos de una sesión, si esta terminará en una compra?** La etiqueta que se predice es `Revenue`.

Se asumió que la predicción se realiza antes de que termine la sesión. Por esa razón se excluyó `PageValues` del modelo principal: su relación con páginas de valor de conversión podría depender de información cercana al cierre de la sesión o de la transacción. La auditoría observó una asociación marcada entre valores distintos de cero y compras, pero eso por sí solo no demuestra fuga de información. `PageValues` podría analizarse en una comparación secundaria, con una definición temporal explícita.

El alcance es clasificación, no explicación causal. Que el modelo use una variable para clasificar no significa que esa variable provoque la compra.

## 2. Datos y fuente

- **Dataset:** [Online Shoppers Purchasing Intention Dataset](https://archive.ics.uci.edu/dataset/468/online+shoppers+purchasing+intention+dataset)
- **Autores:** C. Sakar y Yomi Kastro (2018).
- **DOI:** [10.24432/C5F88Q](https://doi.org/10.24432/C5F88Q)
- **Licencia indicada por UCI:** Creative Commons Attribution 4.0 International (CC BY 4.0). Al reutilizar o redistribuir el conjunto, conservar la atribución correspondiente.

La inspección directa del archivo encontró 12,330 filas y 18 columnas: 17 predictores originales y la etiqueta `Revenue`. No se encontraron campos vacíos o desconocidos. El CSV ocupa aproximadamente 1.07 MB. Se detectaron 125 filas completas adicionales que repetían una fila anterior. Se conservaron porque el dataset no proporciona un identificador que permita saber si representan sesiones duplicadas o sesiones distintas con atributos idénticos.

La distribución de la etiqueta fue:

| Resultado | Sesiones | Porcentaje |
|---|---:|---:|
| Sin compra (`False`) | 10,422 | 84.53% |
| Con compra (`True`) | 1,908 | 15.47% |

## 3. Preparación y evaluación

### Separación de los datos

Se reservaron 9,864 sesiones para entrenamiento y 2,466 para la prueba final. La partición fue estratificada para conservar aproximadamente la proporción de compras y no compras. También se mantuvieron juntos los registros que tenían los mismos predictores del modelo; así, una fila idéntica no podía aparecer en entrenamiento y prueba a la vez. La semilla fija fue `42`.

En el modelo principal quedaron 16 predictores; `Revenue` se mantuvo como respuesta y `PageValues` quedó fuera. El CSV original no se modificó.

### Transformación de variables

- Las columnas categóricas, como `Month`, `VisitorType` y códigos de navegador, se representaron mediante indicadores binarios. Por ejemplo, una columna equivalente a `VisitorType_New_Visitor` identifica si la sesión corresponde a una visita nueva.
- Las columnas numéricas se estandarizaron para que escalas como duraciones y tasas fueran comparables para la regresión logística.
- Estas transformaciones se ajustaron dentro de cada partición de entrenamiento mediante un `Pipeline`. Así, el grupo usado para validar no aportó información al escalado ni a la codificación.

### Comparación de modelos

Se usó validación cruzada agrupada de cinco particiones exclusivamente dentro del conjunto de entrenamiento. Se compararon:

1. Una regla base que siempre predice “no compra”.
2. Regresión logística sin balanceo de clases.
3. Regresión logística con pesos balanceados para prestar más atención a la clase minoritaria.
4. Un árbol de decisión balanceado con profundidad limitada.

El umbral 0.60 para la regresión logística balanceada se escogió antes de consultar la prueba final. En la validación cruzada dio F1 de 0.398, ligeramente superior al F1 de 0.391 con umbral 0.50. No se usó la prueba para seleccionar el modelo o el umbral.

## 4. Resultado final en datos reservados

La configuración seleccionada se ajustó con las 9,864 sesiones de entrenamiento y se evaluó una sola vez con las 2,466 sesiones de prueba, que contenían 382 compras y 2,084 sesiones sin compra.

| Métrica | Resultado | Interpretación sencilla |
|---|---:|---|
| Exactitud | 75.22% | Porcentaje de todas las sesiones clasificadas correctamente. |
| Precisión | 31.62% | De las sesiones señaladas como compra, cuántas realmente compraron. |
| Recall de compra | 51.57% | De las compras reales, qué porcentaje detectó el modelo. |
| F1 | 0.392 | Equilibrio entre precisión y recall. |
| ROC-AUC | 0.763 | Capacidad de ordenar compradores por encima de no compradores, independiente de un umbral fijo. |
| Average precision | 0.326 | Resumen de precisión y detección enfocado en la clase minoritaria. |

La matriz de confusión ayuda a entender qué hay detrás de esas métricas:

| Resultado real | Predijo compra | Predijo no compra |
|---|---:|---:|
| Compra | 197 compras detectadas | 185 compras omitidas |
| Sin compra | 426 falsas alarmas | 1,658 sesiones correctamente identificadas |

Por ejemplo, de 382 sesiones con compra, el modelo detectó 197 y no detectó 185. Además, de las sesiones que marcó como compra, aproximadamente 32 de cada 100 acabaron comprando; las restantes fueron falsas alarmas.

La regla base obtuvo 84.51% de exactitud, mayor que el 75.22% de la regresión logística. Sin embargo, como siempre responde “no compra”, su recall de compra es cero. En este problema, maximizar exactitud por sí sola ocultaría que no encuentra ninguna compra.

## 5. ¿Qué aprendimos de las variables?

La inspección inicial observó diferencias descriptivas entre grupos. Por ejemplo, `PageValues` era mayor que cero en 80.61% de las sesiones con compra y 11.44% de las sesiones sin compra; se excluyó del modelo principal por la definición temporal acordada.

En los coeficientes de la regresión logística, `ExitRates` tuvo un peso negativo destacado, mientras que algunos indicadores de mes y duración de páginas relacionadas con productos tuvieron pesos positivos. Estos valores describen cómo el modelo combina señales para clasificar; no prueban causalidad.

También aparecieron pesos grandes asociados con categorías poco frecuentes. Por ejemplo, `Browser_12` tuvo 10 sesiones en entrenamiento y `TrafficType_18` tuvo 8. Esos pesos son especialmente inciertos y no deben convertirse en reglas comerciales. El número de ejemplos de cada categoría importa al interpretar cualquier resultado.

## 6. Limitaciones

- **Desbalance de clases:** las compras son minoría; la exactitud puede ser engañosa.
- **Falsas alarmas y compras omitidas:** con el umbral elegido, hubo 426 falsas alarmas y 185 compras omitidas. La importancia de cada error depende del uso previsto.
- **Umbral no universal:** 0.60 fue una elección basada en F1 de validación cruzada. Un objetivo comercial podría priorizar más recall o más precisión.
- **Score no calibrado:** la regresión logística usó pesos balanceados. Su score no equivale automáticamente a una probabilidad real de compra.
- **Categorías raras:** algunos niveles tienen muy pocas observaciones y sus coeficientes pueden variar mucho.
- **Representatividad temporal y comercial:** este resultado describe este dataset, no garantiza el mismo desempeño en otra tienda, periodo o población.
- **Duplicados sin identificador:** se mantuvieron las 125 filas repetidas y se agruparon los mismos vectores de predictores al separar los datos. No es posible asegurar si cada fila corresponde a una sesión distinta.
- **Sin causalidad:** el modelo detecta patrones predictivos; no identifica qué acción causaría más compras.

La prueba reservada ya se utilizó para la evaluación final. No debe reutilizarse para ajustar el modelo y después presentarse como una medición independiente. Si se cambia sustancialmente el método, habrá que seleccionar con validación cruzada y conseguir un nuevo conjunto de prueba para otra evaluación final imparcial.

## 7. Conclusión

El proyecto mostró que un clasificador puede encontrar patrones asociados con la compra, pero también que la métrica elegida cambia la interpretación. La regla mayoritaria parece fuerte si miramos solo exactitud, aunque no detecta compras. La regresión logística balanceada detectó alrededor de la mitad de las compras del conjunto de prueba, pero generó más falsas alarmas que compras detectadas.

Por tanto, el modelo es una **base académica reproducible** para aprender clasificación, preparación de variables, desbalance, validación cruzada y evaluación. Antes de proponerlo para una tienda real sería necesario definir el costo de cada tipo de error, evaluar datos más recientes y comprobar si sus scores se pueden calibrar para el uso previsto.

## 8. Reproducibilidad

Desde la carpeta `online_shoppers_project`, con el entorno virtual ya creado:

```powershell
.\.venv\Scripts\python.exe ejecutables/revisar_datos.py
.\.venv\Scripts\python.exe ejecutables/explorar_datos.py
.\.venv\Scripts\python.exe ejecutables/preparar_division.py
.\.venv\Scripts\python.exe ejecutables/validacion_inicial.py
.\.venv\Scripts\python.exe ejecutables/comparar_modelos.py
.\.venv\Scripts\python.exe ejecutables/evaluar_final.py
.\.venv\Scripts\python.exe ejecutables/interpretar_modelo.py
```

**Nota:** la última evaluación vuelve a consultar la prueba reservada. Ya se realizó una evaluación final en este proyecto; no hace falta ejecutar de nuevo `evaluar_final.py` salvo que se quiera reproducir exactamente el mismo resultado. No se deben cambiar el modelo ni el umbral basándose en esa prueba y luego seguir llamándola una evaluación independiente.

## Fuentes de resultados del proyecto

- Auditoría del CSV: `informes/auditoria_datos.json`.
- Análisis exploratorio: `informes/resumen_exploratorio.md`.
- Partición de datos: `informes/resumen_division.json`.
- Validación cruzada inicial: `informes/validacion_inicial.md`.
- Comparación de modelos y umbrales: `informes/comparacion_modelos.md`.
- Evaluación final: `informes/evaluacion_final.md`.
- Interpretación de coeficientes: `informes/interpretacion_modelo.md`.
