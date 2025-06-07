import streamlit as st
import pandas as pd
from classes.ai_readiness_analyzer import AIReadinessAnalyzer
from sklearn.utils.multiclass import type_of_target

st.set_page_config(page_title="Zaawansowana analiza danych do AI", layout="wide")
st.title("Zaawansowana analiza danych do AI")

if "df" not in st.session_state:
    st.warning("⚠️ Nie znaleziono danych! Wróć do strony głównej i wczytaj dane.")
    st.stop()

df = st.session_state["df"]
analyzer = AIReadinessAnalyzer(df)

# 📄 Podgląd danych
st.subheader("📄 Podgląd danych")
st.dataframe(df.head())

# 📊 Reprezentatywność danych
st.subheader("📊 Reprezentatywność danych")
st.dataframe(analyzer.check_representativeness())

# 🧾 Jakość metadanych
st.subheader("🧾 Jakość metadanych")
st.dataframe(analyzer.check_metadata_quality())

# 🧩 Korelacje
st.subheader("🧩 Korelacje zmiennych liczbowych")
heatmap = analyzer.correlation_heatmap(figsize=(14, 10))
if heatmap:
    st.image(heatmap)
else:
    st.info("Brak wystarczającej liczby zmiennych liczbowych do korelacji.")

# 🧠 Wnioski z korelacji
st.subheader("🧠 Wnioski na podstawie macierzy korelacji")
insights = analyzer.get_correlation_insights()

if insights:
    for var1, var2, val in insights:
        st.markdown(f"- **Silna korelacja** między `{var1}` a `{var2}`: **{val:.2f}**")
    st.markdown("➡️ Warto sprawdzić, czy silnie skorelowane zmienne nie powodują nadmiarowości w modelach (multikolinearność).")
else:
    st.markdown("- Brak silnych korelacji (>|0.75|).")
    st.markdown("➡️ Dane są potencjalnie niezależne, co może być korzystne dla niektórych modeli.")

# 💡 Rekomendacje przygotowania danych
st.subheader("💡 Rekomendacje dotyczące przygotowania danych")
recommendations = []

# Braki danych
missing_total = df.isnull().sum().sum()
if missing_total > 0:
    recommendations.append(f"- Wykryto **{missing_total}** brakujących wartości. Rozważ uzupełnienie (np. średnią/medianą) lub usunięcie rekordów.")

# Outliery
numeric_cols = df.select_dtypes(include='number')
for col in numeric_cols.columns:
    mean = df[col].mean()
    std = df[col].std()
    outliers = df[(df[col] > mean + 3*std) | (df[col] < mean - 3*std)]
    if not outliers.empty:
        recommendations.append(f"- Zmienna `{col}` zawiera **{len(outliers)} wartości odstających** poza zakresem ±3σ.")

# Ogólne rekomendacje
if numeric_cols.shape[1] >= 2:
    recommendations.append("- Zastanów się nad **standaryzacją lub normalizacją** zmiennych liczbowych.")
if df.select_dtypes(include="object").shape[1] > 0:
    recommendations.append("- Zakoduj zmienne tekstowe przy użyciu **LabelEncoder** lub **OneHotEncoder**.")
if insights:
    recommendations.append("- Zredukuj zmienne silnie skorelowane, np. używając PCA lub selekcji cech.")

if not recommendations:
    st.success("Dane wyglądają na dobrze przygotowane – brak braków i odstających wartości.")
else:
    for rec in recommendations:
        st.markdown(rec)

# 🎯 Wybór kolumny celu
st.subheader("🎯 Wybór kolumny celu (do klasyfikacji)")
st.markdown("Wybierz kolumnę, która będzie etykietą klas w modelu klasyfikacyjnym.")

target_column = st.selectbox("Kolumna celu", [None] + list(df.columns))

if target_column:
    analyzer = AIReadinessAnalyzer(df, target_column)
    target_type = type_of_target(df[target_column])

    if target_type in ["binary", "multiclass"]:
        # ⚖️ Balans klas
        st.subheader("⚖️ Balans klas")
        class_balance = analyzer.check_class_balance()
        if class_balance is not None:
            st.bar_chart(class_balance)
        else:
            st.info("Kolumna celu ma zbyt dużo unikalnych wartości.")

        # 🤖 Model
        st.subheader("🤖 Trenowanie prostego modelu")
        with st.spinner("⏳ Trwa trenowanie modelu..."):
            result = analyzer.train_simple_model()

        if isinstance(result, dict):
            st.metric("Dokładność", f"{result['accuracy']:.2%}")

            st.subheader("📋 Raport klasyfikacji")
            report = pd.DataFrame(result["report"]).drop(columns=["accuracy"], errors="ignore").T
            report = report.drop(index=["macro avg", "weighted avg"], errors="ignore")
            report = report[["precision", "recall", "f1-score", "support"]]
            report.columns = ["Trafność", "Czułość", "f1-score", "Liczebność"]
            if hasattr(analyzer, "class_labels"):
                report.index = analyzer.class_labels
            report = report.round(3)
            report.index.name = "Klasa"
            st.dataframe(report)
        else:
            st.error(result)

        # 📦 Boxplot
        st.subheader("📦 Rozkład warunkowy (boxplot)")
        numeric_options = df.select_dtypes(include='number').columns.tolist()
        if target_column in numeric_options:
            numeric_options.remove(target_column)

        if numeric_options:
            selected_numeric = st.selectbox("Wybierz zmienną liczbową", numeric_options)
            boxplot = analyzer.conditional_distribution_plot(selected_numeric)
            if boxplot:
                st.image(boxplot)
            else:
                st.info("Nie udało się wygenerować wykresu.")
        else:
            st.info("Brak dodatkowych zmiennych liczbowych.")
    else:
        st.warning(f"⚠️ Kolumna `{target_column}` wygląda na zmienną ciągłą. Wybierz zmienną kategoryczną.")
