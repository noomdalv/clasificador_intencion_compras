"""Herramientas reutilizables para preparar y comparar nuestros modelos."""

from dataclasses import dataclass

from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


@dataclass(frozen=True)
class ConfiguracionModelo:
    """Guarda en un solo lugar las decisiones que comparten nuestros modelos.

    Al ser inmutable (`frozen=True`), una etapa no puede cambiar por accidente
    la semilla o las variables que otra etapa ya está usando.
    """

    objetivo: str = "Revenue"
    semilla: int = 42
    pliegues: int = 5
    umbral_final: float = 0.60
    variables_categoricas: tuple = (
        "Month",
        "OperatingSystems",
        "Browser",
        "Region",
        "TrafficType",
        "VisitorType",
        "Weekend",
    )
    variables_numericas: tuple = (
        "Administrative",
        "Administrative_Duration",
        "Informational",
        "Informational_Duration",
        "ProductRelated",
        "ProductRelated_Duration",
        "BounceRates",
        "ExitRates",
        "SpecialDay",
    )
    variables_excluidas: tuple = ("PageValues",)

    @property
    def variables_modelo(self):
        """Devuelve los predictores permitidos en el modelo principal."""
        return self.variables_numericas + self.variables_categoricas


class FabricaModelos:
    """Crea los preprocesadores, clasificadores y pliegues que usamos al comparar.

    Piensa en esta clase como una pequeña fábrica: le pedimos un modelo y lo
    prepara con las mismas variables y reglas que el resto de los experimentos.
    """

    def __init__(self, configuracion=None):
        self.configuracion = configuracion or ConfiguracionModelo()

    def crear_preprocesador(self, escalar_numericas=True):
        """Codifica categorías y, si se solicita, escala columnas numéricas."""
        numeric_transformer = StandardScaler() if escalar_numericas else "passthrough"
        return ColumnTransformer(
            transformers=[
                (
                    "numeric",
                    numeric_transformer,
                    list(self.configuracion.variables_numericas),
                ),
                (
                    "categorical",
                    OneHotEncoder(handle_unknown="ignore"),
                    list(self.configuracion.variables_categoricas),
                ),
            ],
            remainder="drop",
        )

    def crear_regresion_logistica(self, balancear_clases=False):
        """Crea una regresión logística con el balanceo de clases solicitado."""
        return Pipeline([
            ("preprocess", self.crear_preprocesador(escalar_numericas=True)),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced" if balancear_clases else None,
                    max_iter=2000,
                    random_state=self.configuracion.semilla,
                ),
            ),
        ])

    def crear_arbol_decision(self, balancear_clases=True):
        """Crea un árbol pequeño; los árboles no necesitan escalar valores."""
        return Pipeline([
            ("preprocess", self.crear_preprocesador(escalar_numericas=False)),
            (
                "classifier",
                DecisionTreeClassifier(
                    max_depth=5,
                    min_samples_leaf=20,
                    class_weight="balanced" if balancear_clases else None,
                    random_state=self.configuracion.semilla,
                ),
            ),
        ])

    def crear_referencia_mayoritaria(self):
        """Crea la referencia sencilla que siempre predice la clase mayoritaria."""
        return Pipeline([
            ("preprocess", self.crear_preprocesador(escalar_numericas=False)),
            ("classifier", DummyClassifier(strategy="most_frequent")),
        ])

    def crear_validador_cruzado(self):
        """Crea pliegues estratificados y agrupados con la semilla del proyecto."""
        return StratifiedGroupKFold(
            n_splits=self.configuracion.pliegues,
            shuffle=True,
            random_state=self.configuracion.semilla,
        )

    @staticmethod
    def codificar_objetivo(valores):
        """Convierte las etiquetas TRUE/FALSE del CSV a las clases 1/0."""
        return valores.astype(str).str.upper().eq("TRUE").astype(int)

    @staticmethod
    def crear_ids_grupo(variables):
        """Asigna el mismo ID a predictores idénticos para evitar fuga entre pliegues."""
        import pandas as pd

        return pd.MultiIndex.from_frame(variables).factorize()[0]
