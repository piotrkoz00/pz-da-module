# pages/01_Data_Quality.py

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from classes.data_quality import DataQualityAnalyzer

st.set_page_config(page_title="Analiza jakości danych", layout="wide")
st.title("Analiza jakości danych")

# Sprawdź, czy dane zostały już wczytane w app.py
if "df" not in st.session_state:
    st.warning("Nie znaleziono danych! Wróć do strony głównej i wczytaj dane.")
    st.stop()

df = st.session_state["df"]

st.subheader("Podgląd danych")
st.dataframe(df.head())

st.markdown("---")
st.subheader("Oczekiwane typy danych (opcjonalnie)")

expected_types = {}
type_map = {
    'integer': np.integer,
    'float': np.floating,
    'object': np.object_,
    'string': np.str_,
    'bool': np.bool_,
    'datetime': np.datetime64
}

with st.expander("Kliknij aby ustawić typy kolumn"):
    for col in df.columns:
        selected_type = st.selectbox(
            f"{col} (obecnie: {df[col].dtype})",
            options=["(nie ustawiaj)", "integer", "float", "object", "string", "bool", "datetime"],
            key=f"type_{col}"
        )
        if selected_type != "(nie ustawiaj)":
            expected_types[col] = type_map[selected_type]

st.markdown("---")
analyzer = DataQualityAnalyzer(df, expected_types)
report = analyzer.generate_report()

st.subheader("KPI - Podstawowe wskaźniki jakości")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Procent braków", f"{report['missing_values']['percent_missing_total']:.2f}%")
col2.metric("Procent duplikatów", f"{report['duplicates']['percent_duplicates']:.2f}%")
col3.metric("Procent outlierów", f"{report['outliers']['percent_outliers_total']:.2f}%")
col4.metric("Liczba duplikatów", f"{report['duplicates']['num_duplicates']}")

st.markdown("---")
st.subheader("Procent brakujących wartości (per kolumna)")
st.dataframe(report['missing_values']['missing_per_column_%'].to_frame("Procent braków"))

st.markdown("---")
st.subheader("Outliery (per kolumna)")
outlier_df = pd.DataFrame(report['outliers']['outliers_per_column']).T
outlier_df["Procent obserwacji odstających"] = outlier_df["Procent obserwacji odstających"].apply(lambda x: f"{x:.2f}%")
st.dataframe(outlier_df)

st.markdown("---")
st.subheader("Zgodność typów danych z oczekiwaniami")
if expected_types:
    type_conf_df = pd.DataFrame(report['type_conformance']).T
    st.dataframe(type_conf_df)
else:
    st.info("Nie ustawiono oczekiwanych typów kolumn.")

st.markdown("---")
st.subheader("Podstawowe statystyki opisowe")
st.dataframe(report['basic_stats'])

st.markdown("---")
st.subheader("Rozkłady zmiennych ciągłych (histogramy)")

dists = report["distributions"]
if dists:
    # Mapowanie nazw na polskie
    stat_labels = {
        "min": "Minimum",
        "max": "Maksimum",
        "mean": "Średnia",
        "median": "Mediana"
    }

    stat_colors = {
        "Minimum": "#FFA500",   # pomarańczowy
        "Maksimum": "#FF0000",  # czerwony
        "Średnia": "#008000",   # zielony
        "Mediana": "#800080"    # fioletowy
    }

    for col, dist in dists.items():
        # Przygotowanie DataFrame do histogramu
        hist_df = pd.DataFrame({
            "interval_start": dist["bin_edges"][:-1],
            "interval_end": dist["bin_edges"][1:],
            "count": dist["counts"]
        })
        hist_df['bin_label'] = hist_df.apply(
            lambda row: f"{row['interval_start']:.2f} – {row['interval_end']:.2f}", axis=1
        )

        # Bazowy wykres słupkowy
        base = alt.Chart(hist_df).mark_bar(color="lightblue").encode(
            x=alt.X('interval_start:Q', bin='binned', title=col),
            x2='interval_end:Q',
            y=alt.Y('count:Q', title="Liczność"),
            tooltip=['bin_label', 'count']
        )

        # Przygotowanie danych do linii statystyk
        stats = []
        for name in ["min", "max", "mean", "median"]:
            val = dist.get(name)
            if val is not None:
                label = stat_labels[name]
                color = stat_colors[label]
                stats.append({'value': val, 'label': label, 'color': color})

        # Dodanie linii statystyk do wykresu
        if stats:
            rules = alt.Chart(pd.DataFrame(stats)).mark_rule(size=2).encode(
                x='value:Q',
                color=alt.Color('label:N',
                    scale=alt.Scale(
                        domain=list(stat_colors.keys()),
                        range=list(stat_colors.values())
                    ),
                    legend=alt.Legend(title="Statystyka")
                ),
                tooltip=['label', alt.Tooltip('value:Q', format='.2f')]
            )
            chart = (base + rules).properties(
                width=600,
                height=350,
                title=f"Histogram zmiennej: {col}"
            )
        else:
            chart = base.properties(
                width=600,
                height=350,
                title=f"Histogram zmiennej: {col}"
            )

        st.altair_chart(chart, use_container_width=True)
else:
    st.info("Brak zmiennych ciągłych do analizy rozkładu.")