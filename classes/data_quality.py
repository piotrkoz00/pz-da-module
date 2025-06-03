# data_quality.py

import pandas as pd
import numpy as np
from scipy.stats import zscore, skew

class DataQualityAnalyzer:
    def __init__(self, df: pd.DataFrame, expected_types: dict = None):
        self.df = df.copy()
        self.expected_types = expected_types if expected_types is not None else {}

    def missing_values(self):
        missing_per_col = self.df.isnull().mean() * 100
        total_missing = self.df.isnull().sum().sum()
        total_values = self.df.size
        percent_missing_total = (total_missing / total_values) * 100
        return {
            'missing_per_column_%': missing_per_col,
            'percent_missing_total': percent_missing_total
        }

    def duplicate_rows(self):
        num_duplicates = self.df.duplicated().sum()
        percent_duplicates = (num_duplicates / len(self.df)) * 100 if len(self.df) > 0 else 0
        return {
            'num_duplicates': num_duplicates,
            'percent_duplicates': percent_duplicates
        }

    def outliers(self, method='iqr', zscore_threshold=3):
        outlier_summary = {}
        total_outliers = 0
        total_values = 0

        for col in self.df.select_dtypes(include=np.number).columns:
            col_values = self.df[col].dropna()
            n = len(col_values)
            if n == 0:
                continue

            if method == 'iqr':
                q1 = col_values.quantile(0.25)
                q3 = col_values.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outlier_mask = (col_values < lower_bound) | (col_values > upper_bound)
            elif method == 'zscore':
                zscores = zscore(col_values)
                outlier_mask = np.abs(zscores) > zscore_threshold
            else:
                raise ValueError("Invalid method for outlier detection")

            num_outliers = outlier_mask.sum()
            outlier_summary[col] = {
                'Liczba obserwacji odstających': num_outliers,
                'Procent obserwacji odstających': (num_outliers / n) * 100
            }
            total_outliers += num_outliers
            total_values += n

        percent_total_outliers = (total_outliers / total_values) * 100 if total_values > 0 else 0

        return {
            'outliers_per_column': outlier_summary,
            'percent_outliers_total': percent_total_outliers
        }

    def type_conformance(self):
        results = {}
        for col, expected_type in self.expected_types.items():
            if col in self.df.columns:
                actual_type = self.df[col].dtype
                # Zwracaj nazwy typów zamiast klasy!
                conformance = np.issubdtype(actual_type, expected_type)
                results[col] = {
                    'Oczekiwany typ': str(expected_type),
                    'Rzeczywisty typ': str(actual_type),
                    'Zgodność typów': conformance
                }
            else:
                results[col] = {
                    'Oczekiwany typ': str(expected_type),
                    'Rzeczywisty typ': None,
                    'Zgodność typów': False
                }
        return results

    def distributions(self, bins=20):
        """
        Analiza rozkładów dla zmiennych ciągłych (float).
        Zwraca słownik: nazwa kolumny -> histogram (counts, bin_edges)
        """
        distributions = {}
        for col in self.df.select_dtypes(include=[np.floating]).columns:
            data = self.df[col].dropna()
            counts, bin_edges = np.histogram(data, bins=bins)
            distributions[col] = {
                'counts': counts.tolist(),
                'bin_edges': bin_edges.tolist(),
                'min': float(data.min()) if len(data) > 0 else None,
                'max': float(data.max()) if len(data) > 0 else None,
                'mean': float(data.mean()) if len(data) > 0 else None,
                'median': float(data.median()) if len(data) > 0 else None,
                'skewness': skew(data)
            }
        return distributions

    def basic_stats(self):
        desc = self.df.describe(include='all').transpose()
        desc.insert(0, "typ", self.df.dtypes.astype(str))
        return desc

    def generate_report(self):
        report = {
            'missing_values': self.missing_values(),
            'duplicates': self.duplicate_rows(),
            'outliers': self.outliers(),
            'type_conformance': self.type_conformance(),
            'basic_stats': self.basic_stats(),
            'distributions': self.distributions()
        }
        return report
