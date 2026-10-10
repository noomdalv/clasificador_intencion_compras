"""Ajusta el modelo elegido y evalúalo una sola vez con el conjunto de prueba reservado."""

import csv
import json
import sys
from pathlib import Path

import joblib
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


CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_PROYECTO))
from clasificador_compras.modelado import ConfiguracionModelo, FabricaModelos  # noqa: E402


RUTA_ENTRENAMIENTO = CARPETA_PROYECTO / "datos" / "preparados" / "entrenamiento.csv"
RUTA_PRUEBA = CARPETA_PROYECTO / "datos" / "preparados" / "prueba.csv"
RUTA_INFORME_JSON = CARPETA_PROYECTO / "informes" / "evaluacion_final.json"
RUTA_INFORME_MD = CARPETA_PROYECTO / "informes" / "evaluacion_final.md"
RUTA_PREDICCIONES = CARPETA_PROYECTO / "informes" / "predicciones_prueba.csv"
RUTA_MODELO = CARPETA_PROYECTO / "modelos" / "regresion_logistica_balanceada_umbral_060.joblib"

def porcentaje(numerador, denominador):
    return round(numerador / denominador * 100, 2) if denominador else 0


def crear_informe(resultado):
    modelo = resultado["selected_model"]
    baseline = resultado["majority_baseline"]
    cm = modelo["confusion_matrix"]
    umbral = resultado["threshold_selected_before_test"]
    lines = [
        "# Evaluación final en el conjunto de prueba",
        "",
        "La configuración se fijó antes de evaluar: regresión logística balanceada, "
        f"umbral `{umbral:.2f}`. El modelo se ajustó con entrenamiento y se midió "
        "una sola vez en el conjunto reservado.",
        "",
        f"Filas de prueba: **{resultado['test_rows']:,}**; compras reales: "
        f"**{resultado['test_class_counts']['True']:,}** "
        f"({resultado['test_class_percentages']['True']:.2f}%).",
        "",
        "| Referencia | Exactitud | Precisión | Recall de compra | F1 |",
        "|---|---:|---:|---:|---:|",
        f"| Siempre no compra | {baseline['accuracy']:.3f} | "
        f"{baseline['precision']:.3f} | {baseline['recall']:.3f} | {baseline['f1']:.3f} |",
        f"| Regresión logística balanceada, umbral {umbral:.2f} | "
        f"{modelo['accuracy']:.3f} | {modelo['precision']:.3f} | "
        f"{modelo['recall']:.3f} | {modelo['f1']:.3f} |",
        "",
        f"ROC-AUC: **{modelo['roc_auc']:.3f}**. Average precision: "
        f"**{modelo['average_precision']:.3f}**.",
        "",
        "## Qué significan los aciertos y errores",
        "",
        f"- Compras detectadas: **{cm['true_positive']:,}**.",
        f"- Compras omitidas: **{cm['false_negative']:,}**.",
        f"- Falsas alarmas: **{cm['false_positive']:,}**.",
        f"- Sesiones sin compra correctamente identificadas: **{cm['true_negative']:,}**.",
        "",
        "La regresión logística con pesos balanceados produce un score que permite "
        "ordenar y clasificar sesiones. No se debe interpretar automáticamente como "
        "una probabilidad calibrada de compra.",
        "",
        "## Lectura y límites",
        "",
        "La diferencia con la validación cruzada es normal: la prueba contiene sesiones "
        "que no participaron en selección ni ajuste. Este resultado estima el rendimiento "
        "en datos reservados de este dataset; no garantiza el mismo resultado en otra tienda "
        "o periodo. Como la prueba ya se utilizó para evaluación final, no se debe elegir "
        "otro umbral basándose en ella. Cualquier mejora posterior debe decidirse con "
        "validación cruzada y requeriría un nuevo conjunto de prueba independiente para "
        "una nueva evaluación imparcial.",
        "",
    ]
    return "\n".join(lines)


def principal():
    if not RUTA_ENTRENAMIENTO.exists() or not RUTA_PRUEBA.exists():
        raise FileNotFoundError("Ejecuta primero ejecutables/preparar_division.py")

    configuracion = ConfiguracionModelo()
    fabrica = FabricaModelos(configuracion)
    entrenamiento = pd.read_csv(RUTA_ENTRENAMIENTO)
    prueba = pd.read_csv(RUTA_PRUEBA)
    columnas_esperadas = set(configuracion.variables_modelo + (configuracion.objetivo,))
    if set(entrenamiento.columns) != columnas_esperadas or set(prueba.columns) != columnas_esperadas:
        raise ValueError(
            "Las columnas no coinciden con la configuración acordada; "
            "revisa que PageValues esté excluida y Revenue presente."
        )

    datos_entrenamiento = entrenamiento[list(configuracion.variables_modelo)]
    etiquetas_entrenamiento = fabrica.codificar_objetivo(entrenamiento[configuracion.objetivo])
    datos_prueba = prueba[list(configuracion.variables_modelo)]
    etiquetas_prueba = fabrica.codificar_objetivo(prueba[configuracion.objetivo])

    modelo = fabrica.crear_regresion_logistica(balancear_clases=True)
    modelo.fit(datos_entrenamiento, etiquetas_entrenamiento)
    puntajes = modelo.predict_proba(datos_prueba)[:, 1]
    predicciones = (puntajes >= configuracion.umbral_final).astype(int)

    tn, fp, fn, tp = confusion_matrix(etiquetas_prueba, predicciones, labels=[0, 1]).ravel()
    compras_totales = int(etiquetas_prueba.sum())
    sin_compra_totales = int(len(etiquetas_prueba) - compras_totales)
    metricas_modelo = {
        "threshold": configuracion.umbral_final,
        "accuracy": round(float(accuracy_score(etiquetas_prueba, predicciones)), 4),
        "precision": round(float(precision_score(etiquetas_prueba, predicciones, zero_division=0)), 4),
        "recall": round(float(recall_score(etiquetas_prueba, predicciones, zero_division=0)), 4),
        "f1": round(float(f1_score(etiquetas_prueba, predicciones, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(etiquetas_prueba, puntajes)), 4),
        "average_precision": round(float(average_precision_score(etiquetas_prueba, puntajes)), 4),
        "confusion_matrix": {
            "true_negative": int(tn),
            "false_positive": int(fp),
            "false_negative": int(fn),
            "true_positive": int(tp),
        },
    }
    metricas_referencia = {
        "accuracy": round(float(sin_compra_totales / len(etiquetas_prueba)), 4),
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }
    resultado = {
        "evaluation": "one final evaluation on held-out test set",
        "test_rows": len(prueba),
        "train_rows": len(entrenamiento),
        "test_rows_used_for_training_or_threshold_choice": 0,
        "threshold_selected_before_test": configuracion.umbral_final,
        "model": "LogisticRegression(class_weight='balanced')",
        "excluded_features": list(configuracion.variables_excluidas),
        "scikit_learn_version": sklearn.__version__,
        "test_class_counts": {"False": sin_compra_totales, "True": compras_totales},
        "test_class_percentages": {
            "False": porcentaje(sin_compra_totales, len(prueba)),
            "True": porcentaje(compras_totales, len(prueba)),
        },
        "majority_baseline": metricas_referencia,
        "selected_model": metricas_modelo,
    }

    RUTA_INFORME_JSON.parent.mkdir(parents=True, exist_ok=True)
    RUTA_MODELO.parent.mkdir(parents=True, exist_ok=True)
    RUTA_INFORME_JSON.write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    RUTA_INFORME_MD.write_text(crear_informe(resultado), encoding="utf-8")
    with RUTA_PREDICCIONES.open("w", encoding="utf-8", newline="") as salida:
        writer = csv.DictWriter(
            salida,
            fieldnames=["test_row", "actual_revenue", "purchase_score", "predicted_revenue", "correct"],
        )
        writer.writeheader()
        for indice, (real, puntaje, predicho) in enumerate(
            zip(etiquetas_prueba, puntajes, predicciones), start=1
        ):
            writer.writerow({
                "test_row": indice,
                "actual_revenue": bool(real),
                "purchase_score": round(float(puntaje), 6),
                "predicted_revenue": bool(predicho),
                "correct": bool(real == predicho),
            })
    joblib.dump(modelo, RUTA_MODELO)

    print(crear_informe(resultado))
    print(f"\nDetalle JSON: {RUTA_INFORME_JSON}")
    print(f"Predicciones: {RUTA_PREDICCIONES}")
    print(f"Modelo guardado: {RUTA_MODELO}")


if __name__ == "__main__":
    principal()
