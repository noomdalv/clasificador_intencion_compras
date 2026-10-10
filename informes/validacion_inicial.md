# Primera comparación de modelos (validación cruzada)

Se usaron solo las 9,864 filas de entrenamiento. El conjunto de prueba final no se abrió.

Validación: 5 particiones agrupadas, semilla `42`. Las filas con los mismos predictores permanecen juntas también dentro de cada partición.

| Modelo | Exactitud | Precisión | Recall de compra | F1 | ROC-AUC | Average precision |
|---|---:|---:|---:|---:|---:|---:|
| Siempre predice no compra | 0.845 | 0.000 | 0.000 | 0.000 | 0.500 | 0.155 |
| Regresión logística (pesos balanceados) | 0.648 | 0.267 | 0.730 | 0.391 | 0.748 | 0.327 |

## Cómo leer las métricas

- **Exactitud (accuracy):** fracción total de predicciones correctas. Puede parecer alta aunque se ignoren las compras, debido al desbalance de clases.
- **Precisión:** de las sesiones que el modelo marca como compra, qué proporción realmente compró.
- **Recall de compra:** de todas las sesiones que sí compraron, qué proporción detectó el modelo.
- **F1:** equilibrio entre precisión y recall.
- **ROC-AUC** y **average precision:** resumen cómo separa y ordena los casos positivos y negativos al variar el umbral. Average precision pone el foco en la clase minoritaria.

Cada valor de la tabla es el promedio de cinco particiones; la desviación estándar está en el JSON. Son resultados de referencia, no la evaluación final.
La regresión logística es un primer modelo lineal: estima una probabilidad a partir de una combinación ponderada de variables. `class_weight=balanced` da más peso a la clase de compras, que aparece menos; esto puede elevar el recall y también producir más falsas alarmas.

El preprocesamiento vive dentro de un `Pipeline`. En cada partición, el escalado y la codificación se ajustan solo con la parte de entrenamiento de esa partición, para que los datos de validación no filtren información.

## Límites

Esta comparación no usa el conjunto de prueba reservado. No demuestra causalidad ni el rendimiento en cualquier tienda real; estima rendimiento en particiones de este dataset. El siguiente análisis revisará métricas por pliegue y decidirá qué modelo probar antes de usar la prueba final.
