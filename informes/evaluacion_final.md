# Evaluación final en el conjunto de prueba

La configuración se fijó antes de evaluar: regresión logística balanceada, umbral `0.60`. El modelo se ajustó con entrenamiento y se midió una sola vez en el conjunto reservado.

Filas de prueba: **2,466**; compras reales: **382** (15.49%).

| Referencia | Exactitud | Precisión | Recall de compra | F1 |
|---|---:|---:|---:|---:|
| Siempre no compra | 0.845 | 0.000 | 0.000 | 0.000 |
| Regresión logística balanceada, umbral 0.60 | 0.752 | 0.316 | 0.516 | 0.392 |

ROC-AUC: **0.763**. Average precision: **0.326**.

## Qué significan los aciertos y errores

- Compras detectadas: **197**.
- Compras omitidas: **185**.
- Falsas alarmas: **426**.
- Sesiones sin compra correctamente identificadas: **1,658**.

La regresión logística con pesos balanceados produce un score que permite ordenar y clasificar sesiones. No se debe interpretar automáticamente como una probabilidad calibrada de compra.

## Lectura y límites

La diferencia con la validación cruzada es normal: la prueba contiene sesiones que no participaron en selección ni ajuste. Este resultado estima el rendimiento en datos reservados de este dataset; no garantiza el mismo resultado en otra tienda o periodo. Como la prueba ya se utilizó para evaluación final, no se debe elegir otro umbral basándose en ella. Cualquier mejora posterior debe decidirse con validación cruzada y requeriría un nuevo conjunto de prueba independiente para una nueva evaluación imparcial.
