"""Clases que nos ayudan a descargar, revisar, explorar y dividir los datos."""

import csv
import json
import random
import sys
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


class RutasProyecto:
    """Reúne las carpetas del proyecto para no repetir sus rutas por todas partes."""

    def __init__(self, carpeta_proyecto=None):
        self.raiz_proyecto = Path(carpeta_proyecto) if carpeta_proyecto else Path(__file__).resolve().parents[1]

    @property
    def carpeta_datos_originales(self):
        return self.raiz_proyecto / "datos" / "originales"

    @property
    def carpeta_datos_preparados(self):
        return self.raiz_proyecto / "datos" / "preparados"

    @property
    def carpeta_informes(self):
        return self.raiz_proyecto / "informes"


class AuditorDatos:
    """Se encarga de conseguir el CSV oficial y revisar sus datos principales."""

    URL_DESCARGA = (
        "https://archive.ics.uci.edu/static/public/468/"
        "online+shoppers+purchasing+intention+dataset.zip"
    )
    COLUMNAS_ESPERADAS = [
        "Administrative", "Administrative_Duration", "Informational",
        "Informational_Duration", "ProductRelated", "ProductRelated_Duration",
        "BounceRates", "ExitRates", "PageValues", "SpecialDay", "Month",
        "OperatingSystems", "Browser", "Region", "TrafficType", "VisitorType",
        "Weekend", "Revenue",
    ]

    def __init__(self, rutas=None):
        self.rutas = rutas or RutasProyecto()
        self.ruta_zip = self.rutas.carpeta_datos_originales / "archivo_original_uci.zip"
        self.ruta_csv = self.rutas.carpeta_datos_originales / "online_shoppers_intention.csv"
        self.ruta_informe = self.rutas.carpeta_informes / "auditoria_datos.json"

    def descargar_y_extraer(self):
        """Descarga el archivo de UCI solo si todavía no está guardado localmente."""
        self.rutas.carpeta_datos_originales.mkdir(parents=True, exist_ok=True)
        if self.ruta_csv.exists():
            return

        if not self.ruta_zip.exists():
            print(f"Descargando archivo oficial de UCI: {self.URL_DESCARGA}")
            solicitud = urllib.request.Request(
                self.URL_DESCARGA,
                headers={"User-Agent": "OnlineShoppersAcademicProject/1.0"},
            )
            with urllib.request.urlopen(solicitud, timeout=60) as response:
                self.ruta_zip.write_bytes(response.read())

        with zipfile.ZipFile(self.ruta_zip) as archive:
            member = next(
                (
                    nombre for nombre in archive.namelist()
                    if Path(nombre).name.lower() == "online_shoppers_intention.csv"
                ),
                None,
            )
            if member is None:
                raise FileNotFoundError("El ZIP de UCI no contiene el CSV esperado.")
            with archive.open(member) as origen, self.ruta_csv.open("wb") as objetivo:
                objetivo.write(origen.read())

    def crear_informe(self):
        """Cuenta filas, campos vacíos, duplicados, etiquetas y valores de PageValues."""
        filas = 0
        missing_by_column = Counter()
        revenue_counts = Counter()
        duplicate_rows = 0
        seen_rows = set()
        python_string_bytes = 0
        pagevalues_by_revenue = {
            "True": {"rows": 0, "nonzero_pagevalues": 0},
            "False": {"rows": 0, "nonzero_pagevalues": 0},
        }

        with self.ruta_csv.open("r", encoding="utf-8-sig", newline="") as origen:
            reader = csv.DictReader(origen)
            columnas = reader.fieldnames or []
            for fila in reader:
                filas += 1
                normalizado = tuple((fila.get(columna) or "").strip() for columna in columnas)
                python_string_bytes += sum(sys.getsizeof(valor) for valor in normalizado)
                for columna, valor in zip(columnas, normalizado):
                    if not valor or valor == "?":
                        missing_by_column[columna] += 1

                if normalizado in seen_rows:
                    duplicate_rows += 1
                else:
                    seen_rows.add(normalizado)

                revenue = (fila.get("Revenue") or "").strip().title()
                revenue_counts[revenue] += 1
                bucket = pagevalues_by_revenue.setdefault(
                    revenue, {"rows": 0, "nonzero_pagevalues": 0}
                )
                bucket["rows"] += 1
                raw_value = (fila.get("PageValues") or "").strip()
                if raw_value and raw_value != "?":
                    try:
                        if float(raw_value) > 0:
                            bucket["nonzero_pagevalues"] += 1
                    except ValueError:
                        pass

        file_bytes = self.ruta_csv.stat().st_size
        return {
            "source_file": self.ruta_csv.name,
            "rows": filas,
            "columns": columnas,
            "column_count": len(columnas),
            "expected_columns_match": columnas == self.COLUMNAS_ESPERADAS,
            "missing_or_unknown_by_column": dict(missing_by_column),
            "revenue_counts": dict(revenue_counts),
            "revenue_percentages": {
                label: round(cantidad / filas * 100, 2)
                for label, cantidad in revenue_counts.items()
            } if filas else {},
            "duplicate_full_rows_after_first": duplicate_rows,
            "file_bytes": file_bytes,
            "file_megabytes_decimal": round(file_bytes / 1_000_000, 2),
            "approx_python_field_strings_mib": round(python_string_bytes / 1024**2, 2),
            "pagevalues_by_revenue": pagevalues_by_revenue,
        }

    def ejecutar(self):
        """Realiza la auditoría completa y guarda el resumen para poder revisarlo después."""
        self.descargar_y_extraer()
        resultado = self.crear_informe()
        self.rutas.carpeta_informes.mkdir(parents=True, exist_ok=True)
        self.ruta_informe.write_text(
            json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        print(f"\nInforme guardado en: {self.ruta_informe}")
        return resultado


class AnalizadorExploratorio:
    """Prepara un resumen claro para entender mejor los datos de las sesiones."""

    ETIQUETA_OBJETIVO = "Revenue"
    COLUMNAS_CATEGORICAS = {
        "Month", "OperatingSystems", "Browser", "Region", "TrafficType",
        "VisitorType", "Weekend",
    }

    def __init__(self, rutas=None):
        self.rutas = rutas or RutasProyecto()
        self.ruta_csv = self.rutas.carpeta_datos_originales / "online_shoppers_intention.csv"
        self.ruta_informe = self.rutas.carpeta_informes / "resumen_exploratorio.md"

    @staticmethod
    def mediana(valores):
        ordered = sorted(valores)
        middle = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[middle]
        return (ordered[middle - 1] + ordered[middle]) / 2

    @staticmethod
    def formatear_valor(valor):
        if valor is None:
            return "—"
        return f"{valor:,.3f}".rstrip("0").rstrip(".")

    def cargar_filas(self):
        with self.ruta_csv.open("r", encoding="utf-8-sig", newline="") as origen:
            reader = csv.DictReader(origen)
            return list(reader), reader.fieldnames or []

    def valor_objetivo(self, fila):
        return fila[self.ETIQUETA_OBJETIVO].strip().title()

    def crear_informe(self, filas, columnas):
        target_counts = Counter(self.valor_objetivo(fila) for fila in filas)
        positives = target_counts.get("True", 0)
        negatives = target_counts.get("False", 0)
        total = len(filas)
        lines = [
            "# Análisis exploratorio inicial", "",
            f"Filas analizadas: **{total:,} sesiones**. La variable objetivo es `{self.ETIQUETA_OBJETIVO}`.",
            "", "## 1. ¿Qué queremos predecir?", "",
            "`Revenue=True` significa que la sesión terminó en compra; `False`, que no. "
            "El modelo principal se plantea antes de que termine la sesión, así que `PageValues` "
            "se deja fuera del conjunto principal de predictores.",
            "", "## 2. Distribución de la etiqueta", "",
            "| Resultado | Sesiones | Porcentaje |", "|---|---:|---:|",
            f"| Sin compra (`False`) | {negatives:,} | {negatives / total * 100:.2f}% |",
            f"| Con compra (`True`) | {positives:,} | {positives / total * 100:.2f}% |", "",
            "**Cómo leerlo:** hay aproximadamente una compra por cada "
            f"{negatives / positives:.1f} sesiones sin compra. Si un modelo dijera siempre "
            "`False`, acertaría mucho por simple mayoría, pero no detectaría ninguna compra. "
            "Por eso luego miraremos también métricas que evalúan la detección de compras.",
            "", "## 3. Tipos de variables", "",
            "Las variables categóricas representan grupos. Por ejemplo, `Month=Feb` es un mes, "
            "no un valor menor que `Month=Nov`. Algunos códigos numéricos también son categorías "
            "(por ejemplo, `Browser` y `Region`); no deben interpretarse como cantidades.",
            "", "### Variables categóricas: frecuencia y tasa de compra", "",
        ]

        for columna in sorted(self.COLUMNAS_CATEGORICAS.intersection(columnas)):
            grupos = defaultdict(Counter)
            for fila in filas:
                grupos[fila[columna].strip()][self.valor_objetivo(fila)] += 1
            lines.extend([
                f"#### `{columna}`", "",
                "| Categoría | Sesiones | Compras | Tasa de compra |",
                "|---|---:|---:|---:|",
            ])
            ordered_groups = sorted(
                grupos.items(), key=lambda item: sum(item[1].values()), reverse=True
            )
            for valor, conteos in ordered_groups:
                group_total = sum(conteos.values())
                purchases = conteos.get("True", 0)
                lines.append(
                    f"| {valor or '(vacío)'} | {group_total:,} | {purchases:,} | "
                    f"{purchases / group_total * 100:.2f}% |"
                )
            lines.append("")

        numeric_columns = [
            columna for columna in columnas
            if columna != self.ETIQUETA_OBJETIVO and columna not in self.COLUMNAS_CATEGORICAS
        ]
        lines.extend([
            "### Variables numéricas: comparación por resultado", "",
            "La **mediana** es el valor central y suele describir mejor una variable sesgada "
            "que el promedio. El promedio sigue siendo útil como referencia, pero unos pocos "
            "valores muy grandes pueden elevarlo.", "",
            "| Variable | Sin compra: mediana | Sin compra: promedio | Con compra: mediana | Con compra: promedio |",
            "|---|---:|---:|---:|---:|",
        ])
        for columna in numeric_columns:
            values_by_label = {"False": [], "True": []}
            for fila in filas:
                try:
                    values_by_label[self.valor_objetivo(fila)].append(float(fila[columna]))
                except (ValueError, KeyError):
                    continue
            false_values = values_by_label["False"]
            true_values = values_by_label["True"]
            lines.append(
                f"| `{columna}` | {self.formatear_valor(self.mediana(false_values)) if false_values else '—'} | "
                f"{self.formatear_valor(sum(false_values) / len(false_values)) if false_values else '—'} | "
                f"{self.formatear_valor(self.mediana(true_values)) if true_values else '—'} | "
                f"{self.formatear_valor(sum(true_values) / len(true_values)) if true_values else '—'} |"
            )

        pagevalues = defaultdict(Counter)
        for fila in filas:
            label = self.valor_objetivo(fila)
            pagevalues[label]["total"] += 1
            try:
                if float(fila["PageValues"]) > 0:
                    pagevalues[label]["nonzero"] += 1
            except (ValueError, KeyError):
                pass
        lines.extend([
            "", "## 4. `PageValues`: variable reservada para comparación posterior", "",
            "Se informa aparte, aunque no se usará en el modelo principal:", "",
            "| Resultado | `PageValues > 0` | Total | Porcentaje del grupo |",
            "|---|---:|---:|---:|",
        ])
        for label in ("False", "True"):
            group = pagevalues[label]
            rate = group["nonzero"] / group["total"] * 100 if group["total"] else 0
            lines.append(
                f"| `{label}` | {group['nonzero']:,} | {group['total']:,} | {rate:.2f}% |"
            )
        lines.extend([
            "", "Una diferencia entre grupos indica asociación, no demuestra por sí sola que una "
            "variable cause una compra ni que exista fuga de información.",
            "", "## 5. Plan de evaluación antes del entrenamiento", "",
            "- Reservar **20%** como conjunto de prueba final; el otro **80%** se usará para "
            "desarrollar el modelo.",
            "- Usar una división **estratificada**: conserva aproximadamente el porcentaje de "
            "compras y no compras en ambos grupos. Así evitamos que la prueba quede con una "
            "proporción de compras accidentalmente muy distinta.",
            "- Elegir modelos y ajustes solo con los datos de entrenamiento, mediante validación "
            "cruzada; abrir el conjunto de prueba para la evaluación final una sola vez.",
            "- Ajustar cualquier transformación (por ejemplo, escalado o codificación) usando "
            "solo entrenamiento. Si aprende de toda la tabla antes de dividir, información de "
            "la prueba se filtra al proceso.",
            "- Mantener por ahora las 125 filas idénticas reportadas. Antes de dividir, revisar "
            "si las filas repetidas podrían quedar a ambos lados; si ocurre, eso puede hacer que "
            "la evaluación parezca mejor. Más adelante decidiremos una estrategia de grupo o "
            "una comparación con y sin esas repeticiones, sin borrarlas silenciosamente.",
            "", "### Ejemplo sencillo de fuga de información", "",
            "Imagina que estudias para un examen y una copia de las respuestas aparece también "
            "en la prueba. La nota ya no mide bien si puedes resolver preguntas nuevas. En un "
            "modelo ocurre algo parecido si el entrenamiento y la prueba contienen sesiones "
            "idénticas, o si una transformación se calcula usando ambos grupos.",
            "", "## Alcance de este informe", "",
            "Este resumen describe los datos y propone una evaluación. No elimina filas, no "
            "entrena un modelo y no afirma causalidad. Los conteos y estadísticas son "
            "descriptivos; las asociaciones no son explicaciones causales.", "",
        ])
        return "\n".join(lines)

    def ejecutar(self):
        if not self.ruta_csv.exists():
            raise FileNotFoundError(
                f"No se encontró {self.ruta_csv}. Ejecuta antes ejecutables/revisar_datos.py"
            )
        filas, columnas = self.cargar_filas()
        informe = self.crear_informe(filas, columnas)
        self.rutas.carpeta_informes.mkdir(parents=True, exist_ok=True)
        self.ruta_informe.write_text(informe, encoding="utf-8")
        print(f"Análisis exploratorio guardado en: {self.ruta_informe}")
        print(f"Sesiones: {len(filas):,} | Variables: {len(columnas) - 1} + objetivo")


class DivisorDatos:
    """Crea una partición estratificada que mantiene juntas filas parecidas."""

    ETIQUETA_OBJETIVO = "Revenue"
    VARIABLES_EXCLUIDAS = {"PageValues"}
    FRACCION_PRUEBA = 0.20
    SEMILLA_ALEATORIA = 42

    def __init__(self, rutas=None):
        self.rutas = rutas or RutasProyecto()
        self.ruta_origen = self.rutas.carpeta_datos_originales / "online_shoppers_intention.csv"
        self.ruta_entrenamiento = self.rutas.carpeta_datos_preparados / "entrenamiento.csv"
        self.ruta_prueba = self.rutas.carpeta_datos_preparados / "prueba.csv"
        self.ruta_informe = self.rutas.carpeta_informes / "resumen_division.json"

    @classmethod
    def normalizar_objetivo(cls, fila):
        return fila[cls.ETIQUETA_OBJETIVO].strip().title()

    def leer_origen(self):
        with self.ruta_origen.open("r", encoding="utf-8-sig", newline="") as origen:
            reader = csv.DictReader(origen)
            filas = list(reader)
            columnas = reader.fieldnames or []
        if not filas:
            raise ValueError("El CSV de origen no contiene filas.")
        if self.ETIQUETA_OBJETIVO not in columnas:
            raise ValueError(f"No se encontró la columna objetivo {self.ETIQUETA_OBJETIVO!r}.")
        return filas, columnas

    def asignar_grupos(self, filas, columnas_predictoras):
        grouped = defaultdict(list)
        for fila in filas:
            key = tuple(fila[columna] for columna in columnas_predictoras)
            grouped[key].append(fila)
        grupos = list(grouped.items())
        target_counts = Counter(self.normalizar_objetivo(fila) for fila in filas)
        desired = {
            label: target_counts[label] * self.FRACCION_PRUEBA for label in target_counts
        }

        # Busca una asignación que conserve las proporciones de ambas clases.
        best_assignment = None
        best_error = float("inf")
        for attempt in range(100):
            rng = random.Random(self.SEMILLA_ALEATORIA + attempt)
            order = grupos[:]
            rng.shuffle(order)
            order.sort(key=lambda item: len(item[1]), reverse=True)
            test_keys = set()
            current = Counter()

            def class_balance_error(conteos):
                return sum(
                    ((conteos[label] - desired[label]) / max(desired[label], 1)) ** 2
                    for label in desired
                )

            for key, group_rows in order:
                contribution = Counter(self.normalizar_objetivo(fila) for fila in group_rows)
                proposed = current + contribution
                if class_balance_error(proposed) < class_balance_error(current):
                    test_keys.add(key)
                    current = proposed
            error = class_balance_error(current)
            if error < best_error:
                best_error = error
                best_assignment = test_keys

        if not best_assignment:
            raise RuntimeError("No se pudo construir un conjunto de prueba.")
        filas_entrenamiento, filas_prueba = [], []
        for fila in filas:
            key = tuple(fila[columna] for columna in columnas_predictoras)
            (filas_prueba if key in best_assignment else filas_entrenamiento).append(fila)
        return filas_entrenamiento, filas_prueba, len(grupos), len(best_assignment)

    @classmethod
    def resumir_clases(cls, filas):
        conteos = Counter(cls.normalizar_objetivo(fila) for fila in filas)
        total = len(filas)
        return {
            label: {
                "rows": conteos[label],
                "percentage": round(conteos[label] / total * 100, 2) if total else 0,
            }
            for label in ("False", "True")
        }

    @staticmethod
    def escribir_csv(ruta, filas, columnas):
        with ruta.open("w", encoding="utf-8", newline="") as destino:
            writer = csv.DictWriter(destino, fieldnames=columnas)
            writer.writeheader()
            writer.writerows({columna: fila[columna] for columna in columnas} for fila in filas)

    def ejecutar(self):
        if not self.ruta_origen.exists():
            raise FileNotFoundError(
                f"No se encontró {self.ruta_origen}. Ejecuta antes ejecutables/revisar_datos.py"
            )
        source_rows, source_columns = self.leer_origen()
        columnas_predictoras = [
            columna for columna in source_columns
            if columna != self.ETIQUETA_OBJETIVO and columna not in self.VARIABLES_EXCLUIDAS
        ]
        output_columns = columnas_predictoras + [self.ETIQUETA_OBJETIVO]
        filas_entrenamiento, filas_prueba, group_count, test_group_count = self.asignar_grupos(
            source_rows, columnas_predictoras
        )

        train_keys = {tuple(fila[columna] for columna in columnas_predictoras) for fila in filas_entrenamiento}
        test_keys = {tuple(fila[columna] for columna in columnas_predictoras) for fila in filas_prueba}
        overlap = train_keys & test_keys
        if overlap:
            raise RuntimeError(f"La partición tiene {len(overlap)} grupos superpuestos.")

        self.rutas.carpeta_datos_preparados.mkdir(parents=True, exist_ok=True)
        self.rutas.carpeta_informes.mkdir(parents=True, exist_ok=True)
        self.escribir_csv(self.ruta_entrenamiento, filas_entrenamiento, output_columns)
        self.escribir_csv(self.ruta_prueba, filas_prueba, output_columns)
        resultado = {
            "source_file": self.ruta_origen.name,
            "target": self.ETIQUETA_OBJETIVO,
            "excluded_features": sorted(self.VARIABLES_EXCLUIDAS),
            "test_fraction_requested": self.FRACCION_PRUEBA,
            "random_seed": self.SEMILLA_ALEATORIA,
            "split_method": (
                "deterministic greedy stratified group split by identical feature vectors; "
                "100 seeded candidate assignments, seed base 42"
            ),
            "rows_total": len(source_rows),
            "rows_train": len(filas_entrenamiento),
            "rows_test": len(filas_prueba),
            "train_class_balance": self.resumir_clases(filas_entrenamiento),
            "test_class_balance": self.resumir_clases(filas_prueba),
            "unique_feature_groups_total": group_count,
            "unique_feature_groups_test": test_group_count,
            "identical_feature_groups_in_both_splits": len(overlap),
            "output_columns": output_columns,
            "files": {
                "train": str(self.ruta_entrenamiento.relative_to(self.rutas.raiz_proyecto)),
                "test": str(self.ruta_prueba.relative_to(self.rutas.raiz_proyecto)),
            },
        }
        self.ruta_informe.write_text(
            json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        print(f"\nInforme guardado en: {self.ruta_informe}")
        return resultado
