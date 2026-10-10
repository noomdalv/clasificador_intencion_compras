# Análisis exploratorio inicial

Filas analizadas: **12,330 sesiones**. La variable objetivo es `Revenue`.

## 1. ¿Qué queremos predecir?

`Revenue=True` significa que la sesión terminó en compra; `False`, que no. El modelo principal se plantea antes de que termine la sesión, así que `PageValues` se deja fuera del conjunto principal de predictores.

## 2. Distribución de la etiqueta

| Resultado | Sesiones | Porcentaje |
|---|---:|---:|
| Sin compra (`False`) | 10,422 | 84.53% |
| Con compra (`True`) | 1,908 | 15.47% |

**Cómo leerlo:** hay aproximadamente una compra por cada 5.5 sesiones sin compra. Si un modelo dijera siempre `False`, acertaría mucho por simple mayoría, pero no detectaría ninguna compra. Por eso luego miraremos también métricas que evalúan la detección de compras.

## 3. Tipos de variables

Las variables categóricas representan grupos. Por ejemplo, `Month=Feb` es un mes, no un valor menor que `Month=Nov`. Algunos códigos numéricos también son categorías (por ejemplo, `Browser` y `Region`); no deben interpretarse como cantidades.

### Variables categóricas: frecuencia y tasa de compra

#### `Browser`

| Categoría | Sesiones | Compras | Tasa de compra |
|---|---:|---:|---:|
| 2 | 7,961 | 1,223 | 15.36% |
| 1 | 2,462 | 365 | 14.83% |
| 4 | 736 | 130 | 17.66% |
| 5 | 467 | 86 | 18.42% |
| 6 | 174 | 20 | 11.49% |
| 10 | 163 | 32 | 19.63% |
| 8 | 135 | 21 | 15.56% |
| 3 | 105 | 5 | 4.76% |
| 13 | 61 | 16 | 26.23% |
| 7 | 49 | 6 | 12.24% |
| 12 | 10 | 3 | 30.00% |
| 11 | 6 | 1 | 16.67% |
| 9 | 1 | 0 | 0.00% |

#### `Month`

| Categoría | Sesiones | Compras | Tasa de compra |
|---|---:|---:|---:|
| May | 3,364 | 365 | 10.85% |
| Nov | 2,998 | 760 | 25.35% |
| Mar | 1,907 | 192 | 10.07% |
| Dec | 1,727 | 216 | 12.51% |
| Oct | 549 | 115 | 20.95% |
| Sep | 448 | 86 | 19.20% |
| Aug | 433 | 76 | 17.55% |
| Jul | 432 | 66 | 15.28% |
| June | 288 | 29 | 10.07% |
| Feb | 184 | 3 | 1.63% |

#### `OperatingSystems`

| Categoría | Sesiones | Compras | Tasa de compra |
|---|---:|---:|---:|
| 2 | 6,601 | 1,155 | 17.50% |
| 1 | 2,585 | 379 | 14.66% |
| 3 | 2,555 | 268 | 10.49% |
| 4 | 478 | 85 | 17.78% |
| 8 | 79 | 17 | 21.52% |
| 6 | 19 | 2 | 10.53% |
| 7 | 7 | 1 | 14.29% |
| 5 | 6 | 1 | 16.67% |

#### `Region`

| Categoría | Sesiones | Compras | Tasa de compra |
|---|---:|---:|---:|
| 1 | 4,780 | 771 | 16.13% |
| 3 | 2,403 | 349 | 14.52% |
| 4 | 1,182 | 175 | 14.81% |
| 2 | 1,136 | 188 | 16.55% |
| 6 | 805 | 112 | 13.91% |
| 7 | 761 | 119 | 15.64% |
| 9 | 511 | 86 | 16.83% |
| 8 | 434 | 56 | 12.90% |
| 5 | 318 | 52 | 16.35% |

#### `TrafficType`

| Categoría | Sesiones | Compras | Tasa de compra |
|---|---:|---:|---:|
| 2 | 3,913 | 847 | 21.65% |
| 1 | 2,451 | 262 | 10.69% |
| 3 | 2,052 | 180 | 8.77% |
| 4 | 1,069 | 165 | 15.43% |
| 13 | 738 | 43 | 5.83% |
| 10 | 450 | 90 | 20.00% |
| 6 | 444 | 53 | 11.94% |
| 8 | 343 | 95 | 27.70% |
| 5 | 260 | 56 | 21.54% |
| 11 | 247 | 47 | 19.03% |
| 20 | 198 | 50 | 25.25% |
| 9 | 42 | 4 | 9.52% |
| 7 | 40 | 12 | 30.00% |
| 15 | 38 | 0 | 0.00% |
| 19 | 17 | 1 | 5.88% |
| 14 | 13 | 2 | 15.38% |
| 18 | 10 | 0 | 0.00% |
| 16 | 3 | 1 | 33.33% |
| 12 | 1 | 0 | 0.00% |
| 17 | 1 | 0 | 0.00% |

#### `VisitorType`

| Categoría | Sesiones | Compras | Tasa de compra |
|---|---:|---:|---:|
| Returning_Visitor | 10,551 | 1,470 | 13.93% |
| New_Visitor | 1,694 | 422 | 24.91% |
| Other | 85 | 16 | 18.82% |

#### `Weekend`

| Categoría | Sesiones | Compras | Tasa de compra |
|---|---:|---:|---:|
| FALSE | 9,462 | 1,409 | 14.89% |
| TRUE | 2,868 | 499 | 17.40% |

### Variables numéricas: comparación por resultado

La **mediana** es el valor central y suele describir mejor una variable sesgada que el promedio. El promedio sigue siendo útil como referencia, pero unos pocos valores muy grandes pueden elevarlo.

| Variable | Sin compra: mediana | Sin compra: promedio | Con compra: mediana | Con compra: promedio |
|---|---:|---:|---:|---:|
| `Administrative` | 0 | 2.118 | 2 | 3.394 |
| `Administrative_Duration` | 0 | 73.74 | 52.367 | 119.483 |
| `Informational` | 0 | 0.452 | 0 | 0.786 |
| `Informational_Duration` | 0 | 30.236 | 0 | 57.611 |
| `ProductRelated` | 16 | 28.715 | 29 | 48.21 |
| `ProductRelated_Duration` | 510.19 | 1,069.988 | 1,109.906 | 1,876.21 |
| `BounceRates` | 0.004 | 0.025 | 0 | 0.005 |
| `ExitRates` | 0.029 | 0.047 | 0.016 | 0.02 |
| `PageValues` | 0 | 1.976 | 16.758 | 27.265 |
| `SpecialDay` | 0 | 0.068 | 0 | 0.023 |

## 4. `PageValues`: variable reservada para comparación posterior

Se informa aparte, aunque no se usará en el modelo principal:

| Resultado | `PageValues > 0` | Total | Porcentaje del grupo |
|---|---:|---:|---:|
| `False` | 1,192 | 10,422 | 11.44% |
| `True` | 1,538 | 1,908 | 80.61% |

Una diferencia entre grupos indica asociación, no demuestra por sí sola que una variable cause una compra ni que exista fuga de información.

## 5. Plan de evaluación antes del entrenamiento

- Reservar **20%** como conjunto de prueba final; el otro **80%** se usará para desarrollar el modelo.
- Usar una división **estratificada**: conserva aproximadamente el porcentaje de compras y no compras en ambos grupos. Así evitamos que la prueba quede con una proporción de compras accidentalmente muy distinta.
- Elegir modelos y ajustes solo con los datos de entrenamiento, mediante validación cruzada; abrir el conjunto de prueba para la evaluación final una sola vez.
- Ajustar cualquier transformación (por ejemplo, escalado o codificación) usando solo entrenamiento. Si aprende de toda la tabla antes de dividir, información de la prueba se filtra al proceso.
- Mantener por ahora las 125 filas idénticas reportadas. Antes de dividir, revisar si las filas repetidas podrían quedar a ambos lados; si ocurre, eso puede hacer que la evaluación parezca mejor. Más adelante decidiremos una estrategia de grupo o una comparación con y sin esas repeticiones, sin borrarlas silenciosamente.

### Ejemplo sencillo de fuga de información

Imagina que estudias para un examen y una copia de las respuestas aparece también en la prueba. La nota ya no mide bien si puedes resolver preguntas nuevas. En un modelo ocurre algo parecido si el entrenamiento y la prueba contienen sesiones idénticas, o si una transformación se calcula usando ambos grupos.

## Alcance de este informe

Este resumen describe los datos y propone una evaluación. No elimina filas, no entrena un modelo y no afirma causalidad. Los conteos y estadísticas son descriptivos; las asociaciones no son explicaciones causales.
