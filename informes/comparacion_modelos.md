# Comparación de modelos y umbrales

Se usaron predicciones fuera de muestra para las 9,864 sesiones de entrenamiento: cada fila fue predicha por un modelo que no la vio al entrenar. El conjunto de prueba final no se utilizó.

Se usó validación cruzada agrupada de 5 pliegues con semilla `42`; los mismos vectores de predictores nunca se separan entre entrenamiento y validación.

## Comparación con umbral 0.50

Un umbral de 0.50 quiere decir: marcar compra si el score del modelo es 0.50 o más.

| Modelo | Exactitud | Precisión | Recall | F1 | ROC-AUC | Average precision |
|---|---:|---:|---:|---:|---:|---:|
| Siempre no compra | 0.845 | 0.000 | 0.000 | 0.000 | 0.500 | 0.155 |
| Regresión logística, pesos normales | 0.843 | 0.420 | 0.033 | 0.061 | 0.747 | 0.322 |
| Regresión logística, balanceada | 0.648 | 0.267 | 0.730 | 0.391 | 0.748 | 0.320 |
| Árbol pequeño, balanceado | 0.662 | 0.270 | 0.699 | 0.390 | 0.746 | 0.327 |

## Cambiar el umbral de la regresión logística balanceada

Al bajar el umbral, el modelo marca más sesiones como posibles compras: normalmente sube el recall y bajan la precisión y la exactitud. Al subirlo, suele ocurrir lo contrario.

| Umbral | Exactitud | Precisión | Recall | F1 | Compras detectadas | Falsas alarmas |
|---:|---:|---:|---:|---:|---:|---:|
| 0.20 | 0.356 | 0.191 | 0.976 | 0.319 | 1,490 | 6,314 |
| 0.30 | 0.447 | 0.210 | 0.932 | 0.343 | 1,422 | 5,353 |
| 0.40 | 0.551 | 0.238 | 0.865 | 0.373 | 1,320 | 4,225 |
| 0.50 | 0.648 | 0.267 | 0.730 | 0.391 | 1,114 | 3,062 |
| 0.60 | 0.745 | 0.313 | 0.544 | 0.398 | 830 | 1,819 |
| 0.70 | 0.808 | 0.361 | 0.316 | 0.337 | 482 | 853 |

## ¿Qué es una matriz de confusión?

- **Compra detectada (TP):** sí compró y el modelo lo predijo.
- **Compra omitida (FN):** sí compró, pero el modelo dijo que no.
- **Falsa alarma (FP):** no compró, pero el modelo predijo compra.
- **No compra detectada (TN):** no compró y el modelo dijo que no.

Los scores de una regresión con pesos balanceados sirven para ordenar y clasificar; no deben interpretarse automáticamente como probabilidades calibradas de compra.
El umbral y el modelo aún no se han elegido. Esta tabla sirve para entender el intercambio entre detectar compradores y generar falsas alarmas.

Los resultados agregan las predicciones fuera de muestra de los cinco pliegues. Pueden diferir levemente del informe anterior, que promedió las métricas calculadas por separado en cada pliegue.
