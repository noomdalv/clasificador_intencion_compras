"""Herramientas para entender qué señales usa el modelo al hacer predicciones."""

import csv

import joblib
import numpy as np
import pandas as pd


class InterpreteModelo:
    """Explica los pesos del modelo con datos de entrenamiento, sin abrir la prueba."""

    CANTIDAD_SUPERIOR = 12
    VARIABLES_CATEGORICAS = [
        "Month", "OperatingSystems", "Browser", "Region",
        "TrafficType", "VisitorType", "Weekend",
    ]

    def __init__(self, rutas=None):
        from .flujo_datos import RutasProyecto

        self.rutas = rutas or RutasProyecto()
        self.ruta_modelo = self.rutas.raiz_proyecto / "modelos" / "regresion_logistica_balanceada_umbral_060.joblib"
        self.ruta_entrenamiento = self.rutas.carpeta_datos_preparados / "entrenamiento.csv"
        self.ruta_informe = self.rutas.carpeta_informes / "interpretacion_modelo.md"
        self.ruta_pesos = self.rutas.carpeta_informes / "pesos_variables.csv"

    def cargar_entradas(self):
        """Carga el artefacto y el entrenamiento; no abre el conjunto de prueba."""
        if not self.ruta_modelo.exists() or not self.ruta_entrenamiento.exists():
            raise FileNotFoundError(
                "Necesitas el modelo final y datos/preparados/entrenamiento.csv antes de interpretar."
            )
        return joblib.load(self.ruta_modelo), pd.read_csv(self.ruta_entrenamiento)

    def recopilar_coeficientes(self, modelo, entrenamiento):
        """Relaciona cada peso con su nombre y, si es categoría, su frecuencia."""
        clasificador = modelo.named_steps["classifier"]
        preprocesador = modelo.named_steps["preprocess"]
        nombres = preprocesador.get_feature_names_out()
        coeficientes = clasificador.coef_[0]
        if len(nombres) != len(coeficientes):
            raise ValueError("La cantidad de nombres y coeficientes no coincide.")

        codificador = preprocesador.named_transformers_["categorical"]
        nombres_codificados = codificador.get_feature_names_out(self.VARIABLES_CATEGORICAS)
        conteos_codificados = np.asarray(
            codificador.transform(entrenamiento[self.VARIABLES_CATEGORICAS]).sum(axis=0)
        ).ravel()
        frecuencia_categorias = {
            f"categorical__{nombre}": int(cantidad)
            for nombre, cantidad in zip(nombres_codificados, conteos_codificados)
        }
        return sorted(
            [
                {
                    "transformed_feature": str(nombre),
                    "coefficient": float(valor),
                    "training_sessions": frecuencia_categorias.get(str(nombre)),
                }
                for nombre, valor in zip(nombres, coeficientes)
            ],
            key=lambda registro: registro["coefficient"],
        )

    def guardar_pesos(self, registros):
        """Guarda la tabla completa de coeficientes como CSV."""
        self.rutas.carpeta_informes.mkdir(parents=True, exist_ok=True)
        with self.ruta_pesos.open("w", encoding="utf-8", newline="") as salida:
            writer = csv.DictWriter(
                salida,
                fieldnames=["transformed_feature", "coefficient", "training_sessions"],
            )
            writer.writeheader()
            writer.writerows(registros)

    def crear_informe(self, registros):
        """Construye una explicación legible de los pesos extremos."""
        negativos = registros[: self.CANTIDAD_SUPERIOR]
        positivos = list(reversed(registros[-self.CANTIDAD_SUPERIOR :]))
        lines = [
            "# Interpretación inicial de la regresión logística", "",
            "Esta lectura usa los coeficientes del modelo entrenado con `entrenamiento.csv`. "
            "No vuelve a leer ni a analizar `prueba.csv`.", "",
            "## ¿Qué representa un coeficiente?", "",
            "La regresión logística combina los valores transformados mediante una suma "
            "ponderada. Un coeficiente positivo empuja el score hacia `Revenue=True`; uno "
            "negativo lo empuja hacia `Revenue=False`, manteniendo lo demás fijo.", "",
            "Las variables numéricas fueron estandarizadas: su coeficiente corresponde al "
            "cambio asociado a una desviación estándar en esa variable. Las categorías se "
            "convirtieron en indicadores binarios, por ejemplo `Month_Nov` vale 1 si el mes "
            "es noviembre y 0 si no.", "",
            f"## Coeficientes más positivos (hasta {self.CANTIDAD_SUPERIOR})", "",
            "| Variable transformada | Coeficiente | Sesiones de entrenamiento |",
            "|---|---:|---:|",
        ]
        for registro in positivos:
            lines.append(self.formatear_registro(registro))
        lines.extend([
            "", f"## Coeficientes más negativos (hasta {self.CANTIDAD_SUPERIOR})", "",
            "| Variable transformada | Coeficiente | Sesiones de entrenamiento |",
            "|---|---:|---:|",
        ])
        lines.extend(self.formatear_registro(registro) for registro in negativos)
        lines.extend([
            "", "## Cómo interpretarlo con prudencia", "",
            "- Un peso describe cómo el modelo usa una variable para clasificar, no demuestra "
            "que esa variable cause una compra.",
            "- Los pesos dependen de las demás variables incluidas, del escalado y de la "
            "regularización de la regresión.",
            "- Los indicadores de categorías se interpretan como parte del conjunto de "
            "categorías codificadas; no son comparaciones causales entre grupos.",
            "- Una categoría rara puede tener un peso grande con poca evidencia. Conviene "
            "revisar sus frecuencias en el análisis exploratorio antes de sacar conclusiones.",
            "- El modelo usó pesos balanceados, por lo que los coeficientes y scores se "
            "orientan a reconocer la clase minoritaria y no equivalen automáticamente a "
            "probabilidades calibradas.",
            "- `PageValues` no aparece porque fue excluida del modelo principal.", "",
            "Esta tabla sirve para explicar el comportamiento del clasificador, no para "
            "cambiar el umbral usando el conjunto de prueba.", "",
        ])
        return "\n".join(lines)

    @staticmethod
    def formatear_registro(registro):
        frecuencia = registro["training_sessions"]
        frecuencia = frecuencia if frecuencia is not None else "—"
        return (
            f"| `{registro['transformed_feature']}` | {registro['coefficient']:.4f} | "
            f"{frecuencia} |"
        )

    def ejecutar(self):
        """Ejecuta la explicación y guarda sus dos informes."""
        modelo, entrenamiento = self.cargar_entradas()
        registros = self.recopilar_coeficientes(modelo, entrenamiento)
        self.guardar_pesos(registros)
        informe = self.crear_informe(registros)
        self.ruta_informe.write_text(informe, encoding="utf-8")
        print(f"Interpretación guardada en: {self.ruta_informe}")
        print(f"Coeficientes completos guardados en: {self.ruta_pesos}")
        print(informe)
        return registros
