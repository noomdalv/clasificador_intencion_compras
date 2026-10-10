"""Compara clasificadores y umbrales con predicciones agrupadas fuera de muestra."""

import json
import sys
from pathlib import Path

import pandas as pd
import sklearn
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_predict

CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_PROYECTO))
from clasificador_compras.modelado import ConfiguracionModelo, FabricaModelos  # noqa: E402


RUTA_ENTRENAMIENTO = CARPETA_PROYECTO / "datos" / "preparados" / "entrenamiento.csv"
RUTA_JSON = CARPETA_PROYECTO / "informes" / "comparacion_modelos.json"
RUTA_MARKDOWN = CARPETA_PROYECTO / "informes" / "comparacion_modelos.md"
UMBRALES = (0.20, 0.30, 0.40, 0.50, 0.60, 0.70)


def resumir_metricas(y_true, puntajes, umbral=0.5):
    y_pred = (puntajes >= umbral).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "threshold": umbral,
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, puntajes)), 4),
        "average_precision": round(float(average_precision_score(y_true, puntajes)), 4),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }


def crear_informe_markdown(informe):
    lines = [
        "# Comparación de modelos y umbrales",
        "",
        f"Se usaron predicciones fuera de muestra para las {informe['training_rows']:,} "
        "sesiones de entrenamiento: cada fila fue predicha por un modelo que no la vio "
        "al entrenar. El conjunto de prueba final no se utilizó.",
        "",
        f"Se usó validación cruzada agrupada de {informe['folds']} pliegues con "
        f"semilla `{informe['random_seed']}`; "
        "los mismos vectores de predictores nunca se separan entre entrenamiento y validación.",
        "",
        "## Comparación con umbral 0.50",
        "",
        "Un umbral de 0.50 quiere decir: marcar compra si el score del modelo es 0.50 o más.",
        "",
        "| Modelo | Exactitud | Precisión | Recall | F1 | ROC-AUC | Average precision |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    nombres = {
        "majority_baseline": "Siempre no compra",
        "logistic_default": "Regresión logística, pesos normales",
        "logistic_balanced": "Regresión logística, balanceada",
        "decision_tree_balanced": "Árbol pequeño, balanceado",
    }
    for key, label in nombres.items():
        m = informe["models"][key]["at_0_50"]
        lines.append(
            f"| {label} | {m['accuracy']:.3f} | {m['precision']:.3f} | "
            f"{m['recall']:.3f} | {m['f1']:.3f} | {m['roc_auc']:.3f} | "
            f"{m['average_precision']:.3f} |"
        )
    lines.extend([
        "",
        "## Cambiar el umbral de la regresión logística balanceada",
        "",
        "Al bajar el umbral, el modelo marca más sesiones como posibles compras: normalmente "
        "sube el recall y bajan la precisión y la exactitud. Al subirlo, suele ocurrir lo contrario.",
        "",
        "| Umbral | Exactitud | Precisión | Recall | F1 | Compras detectadas | Falsas alarmas |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for valor, m in informe["threshold_analysis"].items():
        cm = m["confusion_matrix"]
        lines.append(
            f"| {float(valor):.2f} | {m['accuracy']:.3f} | {m['precision']:.3f} | "
            f"{m['recall']:.3f} | {m['f1']:.3f} | {cm['true_positive']:,} | "
            f"{cm['false_positive']:,} |"
        )
    lines.extend([
        "",
        "## ¿Qué es una matriz de confusión?",
        "",
        "- **Compra detectada (TP):** sí compró y el modelo lo predijo.",
        "- **Compra omitida (FN):** sí compró, pero el modelo dijo que no.",
        "- **Falsa alarma (FP):** no compró, pero el modelo predijo compra.",
        "- **No compra detectada (TN):** no compró y el modelo dijo que no.",
        "",
        "Los scores de una regresión con pesos balanceados sirven para ordenar y clasificar; "
        "no deben interpretarse automáticamente como probabilidades calibradas de compra.",
        "El umbral y el modelo aún no se han elegido. Esta tabla sirve para entender el "
        "intercambio entre detectar compradores y generar falsas alarmas.",
        "",
        "Los resultados agregan las predicciones fuera de muestra de los cinco pliegues. "
        "Pueden diferir levemente del informe anterior, que promedió las métricas calculadas "
        "por separado en cada pliegue.",
        "",
    ])
    return "\n".join(lines)


def principal():
    if not RUTA_ENTRENAMIENTO.exists():
        raise FileNotFoundError("Ejecuta antes ejecutables/preparar_division.py")
    configuracion = ConfiguracionModelo()
    fabrica = FabricaModelos(configuracion)
    datos = pd.read_csv(RUTA_ENTRENAMIENTO)
    X = datos[list(configuracion.variables_modelo)]
    y = fabrica.codificar_objetivo(datos[configuracion.objetivo])
    grupos = fabrica.crear_ids_grupo(X)
    cv = fabrica.crear_validador_cruzado()

    modelos = {
        "majority_baseline": fabrica.crear_referencia_mayoritaria(),
        "logistic_default": fabrica.crear_regresion_logistica(balancear_clases=False),
        "logistic_balanced": fabrica.crear_regresion_logistica(balancear_clases=True),
        "decision_tree_balanced": fabrica.crear_arbol_decision(balancear_clases=True),
    }

    resultados = {
        "training_rows": len(datos),
        "test_rows_used": 0,
        "excluded_features": list(configuracion.variables_excluidas),
        "folds": configuracion.pliegues,
        "random_seed": configuracion.semilla,
        "scikit_learn_version": sklearn.__version__,
        "prediction_method": "out-of-fold probabilities from grouped stratified CV",
        "models": {},
        "threshold_analysis": {},
    }
    scores_by_model = {}
    for nombre, estimador in modelos.items():
        puntajes_pliegues = cross_val_predict(
            estimador,
            X,
            y,
            groups=grupos,
            cv=cv,
            method="predict_proba",
            n_jobs=1,
        )[:, 1]
        scores_by_model[nombre] = puntajes_pliegues
        resultados["models"][nombre] = {
            "at_0_50": resumir_metricas(y, puntajes_pliegues, 0.50)
        }

    for umbral in UMBRALES:
        resultados["threshold_analysis"][f"{umbral:.2f}"] = resumir_metricas(
            y, scores_by_model["logistic_balanced"], umbral
        )

    RUTA_JSON.parent.mkdir(parents=True, exist_ok=True)
    RUTA_JSON.write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    RUTA_MARKDOWN.write_text(crear_informe_markdown(resultados), encoding="utf-8")
    print(crear_informe_markdown(resultados))
    print(f"\nDetalle guardado en: {RUTA_JSON}")


if __name__ == "__main__":
    principal()
