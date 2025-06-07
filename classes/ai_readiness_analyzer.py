# ai_readiness_analyzer.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.multiclass import type_of_target
import matplotlib.pyplot as plt
import seaborn as sns
import io

class AIReadinessAnalyzer:
    def __init__(self, df: pd.DataFrame, target_column: str = None):
        self.df = df.copy()
        self.target_column = target_column
        self.class_labels = None  # Dodane: etykiety klas

    def check_class_balance(self):
        if self.target_column and self.df[self.target_column].nunique() <= 20:
            return self.df[self.target_column].value_counts(normalize=True)
        return None

    def check_metadata_quality(self):
        return pd.DataFrame({
            "dtype": self.df.dtypes.astype(str),
            "nulls": self.df.isnull().sum(),
            "unique_values": self.df.nunique()
        })

    def check_representativeness(self):
        numeric = self.df.select_dtypes(include=np.number)
        if numeric.empty:
            return pd.DataFrame({"Informacja": ["Brak danych liczbowych do analizy."]})
        desc = numeric.describe().T
        desc["skośność"] = numeric.skew()
        return desc

    def train_simple_model(self):
        if self.target_column is None:
            return "Brak kolumny celu."

        df_model = self.df.dropna()
        if self.target_column not in df_model.columns:
            return "Wybrana kolumna celu nie istnieje w danych."

        X = df_model.drop(columns=[self.target_column])
        y = df_model[self.target_column]

        target_type = type_of_target(y)
        if target_type not in ["binary", "multiclass"]:
            return f"Kolumna celu ma typ '{target_type}' – wygląda na regresyjną, nie klasyfikacyjną."

        for col in X.select_dtypes(include="object").columns:
            X[col] = LabelEncoder().fit_transform(X[col].astype(str))

        if y.dtype == "object":
            le = LabelEncoder()
            y = le.fit_transform(y)
            self.class_labels = le.classes_
        else:
            self.class_labels = np.unique(y)

        try:
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
            model = LogisticRegression(max_iter=500)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
        except Exception as e:
            return f"Błąd podczas trenowania modelu: {str(e)}"

        return {
            "accuracy": accuracy_score(y_test, y_pred),
            "report": classification_report(y_test, y_pred, output_dict=True)
        }

    def conditional_distribution_plot(self, feature: str):
        if not self.target_column or feature not in self.df.columns:
            return None

        if self.df[feature].dtype not in ["int64", "float64"]:
            return None

        fig, ax = plt.subplots(figsize=(10, 6))
        sns.boxplot(x=self.target_column, y=feature, data=self.df, ax=ax)
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        buf.seek(0)
        return buf

    def correlation_heatmap(self, figsize=(14, 10)):
        numeric = self.df.select_dtypes(include=np.number)
        if numeric.shape[1] < 2:
            return None

        fig, ax = plt.subplots(figsize=figsize)
        sns.heatmap(numeric.corr(), annot=True, cmap="Greys", ax=ax, cbar=True,
                    linewidths=0.5, linecolor='white', annot_kws={"color": "white"})
        ax.set_facecolor("black")
        fig.patch.set_facecolor("black")
        plt.xticks(rotation=45, color="white")
        plt.yticks(rotation=0, color="white")
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", facecolor=fig.get_facecolor())
        buf.seek(0)
        return buf
    
    def get_correlation_insights(self, threshold=0.75):
        corr = self.df.select_dtypes(include=np.number).corr()
        high_corr = []
        for i in range(len(corr.columns)):
            for j in range(i):
                value = corr.iloc[i, j]
                if abs(value) >= threshold:
                    high_corr.append((corr.columns[i], corr.columns[j], value))
        return high_corr
