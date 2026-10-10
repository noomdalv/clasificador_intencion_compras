# Interpretación inicial de la regresión logística

Esta lectura usa los coeficientes del modelo entrenado con `entrenamiento.csv`. No vuelve a leer ni a analizar `prueba.csv`.

## ¿Qué representa un coeficiente?

La regresión logística combina los valores transformados mediante una suma ponderada. Un coeficiente positivo empuja el score hacia `Revenue=True`; uno negativo lo empuja hacia `Revenue=False`, manteniendo lo demás fijo.

Las variables numéricas fueron estandarizadas: su coeficiente corresponde al cambio asociado a una desviación estándar en esa variable. Las categorías se convirtieron en indicadores binarios, por ejemplo `Month_Nov` vale 1 si el mes es noviembre y 0 si no.

## Coeficientes más positivos (hasta 12)

| Variable transformada | Coeficiente | Sesiones de entrenamiento |
|---|---:|---:|
| `categorical__Browser_12` | 1.1616 | 10 |
| `categorical__Browser_13` | 0.9720 | 39 |
| `categorical__TrafficType_7` | 0.7276 | 32 |
| `categorical__TrafficType_20` | 0.6945 | 146 |
| `categorical__TrafficType_8` | 0.6377 | 293 |
| `categorical__Month_Nov` | 0.6076 | 2408 |
| `numeric__BounceRates` | 0.4263 | — |
| `categorical__TrafficType_11` | 0.4138 | 202 |
| `categorical__Month_Jul` | 0.3956 | 346 |
| `categorical__Month_Sep` | 0.3485 | 365 |
| `numeric__ProductRelated_Duration` | 0.3334 | — |
| `categorical__Month_Aug` | 0.3022 | 353 |

## Coeficientes más negativos (hasta 12)

| Variable transformada | Coeficiente | Sesiones de entrenamiento |
|---|---:|---:|
| `numeric__ExitRates` | -1.4210 | — |
| `categorical__Browser_3` | -1.2431 | 89 |
| `categorical__TrafficType_15` | -1.1817 | 27 |
| `categorical__Month_Feb` | -1.1030 | 142 |
| `categorical__TrafficType_13` | -0.7156 | 579 |
| `categorical__TrafficType_18` | -0.6665 | 8 |
| `categorical__OperatingSystems_6` | -0.5909 | 14 |
| `categorical__Browser_7` | -0.5547 | 38 |
| `categorical__Browser_6` | -0.4797 | 145 |
| `categorical__TrafficType_3` | -0.3893 | 1626 |
| `categorical__Month_Mar` | -0.3887 | 1505 |
| `categorical__TrafficType_19` | -0.3077 | 16 |

## Cómo interpretarlo con prudencia

- Un peso describe cómo el modelo usa una variable para clasificar, no demuestra que esa variable cause una compra.
- Los pesos dependen de las demás variables incluidas, del escalado y de la regularización de la regresión.
- Los indicadores de categorías se interpretan como parte del conjunto de categorías codificadas; no son comparaciones causales entre grupos.
- Una categoría rara puede tener un peso grande con poca evidencia. Conviene revisar sus frecuencias en el análisis exploratorio antes de sacar conclusiones.
- El modelo usó pesos balanceados, por lo que los coeficientes y scores se orientan a reconocer la clase minoritaria y no equivalen automáticamente a probabilidades calibradas.
- `PageValues` no aparece porque fue excluida del modelo principal.

Esta tabla sirve para explicar el comportamiento del clasificador, no para cambiar el umbral usando el conjunto de prueba.
