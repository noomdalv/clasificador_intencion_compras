"""Compara dos opciones iniciales usando únicamente los datos de entrenamiento."""

import json
import sys
from pathlib import Path

import pandas as pd
import sklearn
from sklearn.metrics import make_scorer, precision_score, f1_score
from sklearn.model_selection import cross_validate

CARPETA_PROYECTO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CARPETA_PROYECTO))
from clasificador_compras.modelado import ConfiguracionModelo, FabricaModelos  # noqa: E402


RUTA_ENTRENAMIENTO = CARPETA_PROYECTO / "datos" / "preparados" / "entrenamiento.csv"
RUTA_JSON = CARPETA_PROYECTO / "informes" / "validacion_inicial.json"
RUTA_MARKDOWN = CARPETA_PROYECTO / "informes" / "validacion_inicial.md"
METRICAS = {
    "accuracy": "accuracy",
    "precision": make_scorer(precision_score, zero_division=0),
    "recall": "recall",
    "f1": make_scorer(f1_score, zero_division=0),
    "roc_auc": "roc_auc",
    "average_precision": "average_precision",
}


def resumir_puntajes(estimador, X, y, grupos, cv):
    puntajes = cross_validate(
        estimador,
        X,
        y,
        groups=grupos,
        cv=cv,
        scoring=METRICAS,
        n_jobs=1,
        return_train_score=False,
    )
    resumen = {}
    for metric in METRICAS:
        valores = puntajes[f"test_{metric}"]
        resumen[metric] = {
            "fold_scores": [round(float(valor), 4) for valor in valores],
            "mean": round(float(valores.mean()), 4),
            "std": round(float(valores.std()), 4),
        }
    return resumen


def crear_informe_markdown(resultado):
    lines = [
        "# Primera comparación de modelos (validación cruzada)",
        "",
        f"Se usaron solo las {resultado['training_rows']:,} filas de entrenamiento. "
        "El conjunto de prueba final no se abrió.",
        "",
        f"Validación: {resultado['folds']} particiones agrupadas, "
        f"semilla `{resultado['random_seed']}`. "
        "Las filas con los mismos predictores permanecen juntas también dentro "
        "de cada partición.",
        "",
        "| Modelo | Exactitud | Precisión | Recall de compra | F1 | ROC-AUC | Average precision |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    labels = {
        "majority_baseline": "Siempre predice no compra",
        "logistic_regression_balanced": "Regresión logística (pesos balanceados)",
    }
    display_metrics = [
        "accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"
    ]
    for key, label in labels.items():
        metrics = resultado["models"][key]
        cells = [f"{metrics[nombre]['mean']:.3f}" for nombre in display_metrics]
        lines.append("| " + label + " | " + " | ".join(cells) + " |")
    lines.extend([
        "",
        "## Cómo leer las métricas",
        "",
        "- **Exactitud (accuracy):** fracción total de predicciones correctas. Puede "
        "parecer alta aunque se ignoren las compras, debido al desbalance de clases.",
        "- **Precisión:** de las sesiones que el modelo marca como compra, qué proporción "
        "realmente compró.",
        "- **Recall de compra:** de todas las sesiones que sí compraron, qué proporción "
        "detectó el modelo.",
        "- **F1:** equilibrio entre precisión y recall.",
        "- **ROC-AUC** y **average precision:** resumen cómo separa y ordena los casos "
        "positivos y negativos al variar el umbral. Average precision pone el foco en la "
        "clase minoritaria.",
        "",
        "Cada valor de la tabla es el promedio de cinco particiones; la desviación "
        "estándar está en el JSON. Son resultados de referencia, no la evaluación final.",
        "La regresión logística es un primer modelo lineal: estima una probabilidad a "
        "partir de una combinación ponderada de variables. `class_weight=balanced` da "
        "más peso a la clase de compras, que aparece menos; esto puede elevar el recall "
        "y también producir más falsas alarmas.",
        "",
        "El preprocesamiento vive dentro de un `Pipeline`. En cada partición, el escalado "
        "y la codificación se ajustan solo con la parte de entrenamiento de esa partición, "
        "para que los datos de validación no filtren información.",
        "",
        "## Límites",
        "",
        "Esta comparación no usa el conjunto de prueba reservado. No demuestra causalidad "
        "ni el rendimiento en cualquier tienda real; estima rendimiento en particiones "
        "de este dataset. El siguiente análisis revisará métricas por pliegue y decidirá "
        "qué modelo probar antes de usar la prueba final.",
        "",
    ])
    return "\n".join(lines)


def principal():
    if not RUTA_ENTRENAMIENTO.exists():
        raise FileNotFoundError(
            "No existe datos/preparados/entrenamiento.csv. Ejecuta primero ejecutables/preparar_division.py"
        )
    configuracion = ConfiguracionModelo()
    fabrica = FabricaModelos(configuracion)
    datos = pd.read_csv(RUTA_ENTRENAMIENTO)
    X = datos[list(configuracion.variables_modelo)]
    y = fabrica.codificar_objetivo(datos[configuracion.objetivo])
    grupos = fabrica.crear_ids_grupo(X)
    cv = fabrica.crear_validador_cruzado()

    modelos = {
        "majority_baseline": fabrica.crear_referencia_mayoritaria(),
        "logistic_regression_balanced": fabrica.crear_regresion_logistica(balancear_clases=True),
    }

    resultados = {
        "training_rows": len(datos),
        "test_rows_used": 0,
        "target_positive_label": f"{configuracion.objetivo}=True",
        "excluded_features": list(configuracion.variables_excluidas),
        "folds": configuracion.pliegues,
        "random_seed": configuracion.semilla,
        "cv_method": "StratifiedGroupKFold; identical feature vectors stay together",
        "scikit_learn_version": sklearn.__version__,
        "models": {},
    }
    for nombre, estimador in modelos.items():
        resultados["models"][nombre] = resumir_puntajes(
            estimador, X, y, grupos, cv
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
