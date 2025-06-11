# pages/02_AI_Compliance.py

import streamlit as st
import pandas as pd
import numpy as np
from classes.ai_compliance import AIComplianceAnalyzer

st.set_page_config(page_title="Zgodność z AI Act", layout="wide")
st.title("Analiza zgodności z AI Act")

if "df" not in st.session_state:
    st.warning("Nie znaleziono danych! Wróć do strony głównej i wczytaj dane.")
    st.stop()

df = st.session_state["df"]
analyzer = AIComplianceAnalyzer(df)

st.markdown("""
### 🔍 Co mierzymy?
Celem tej sekcji jest analiza potencjalnych uprzedzeń (biasu) w danych. 
Sprawdzamy, czy dana cecha (np. kraj klienta, metoda płatności) nie powoduje nierównego traktowania różnych grup — np. czy jedna grupa nie otrzymuje znacznie większych rabatów niż inne.

Analiza składa się z dwóch części:
- 📊 **Rozkład kategorii** - czy jedna grupa dominuje liczebnie nad innymi?
- 📈 **Średnie wartości zmiennych liczbowych w grupach** - czy np. rabaty, ceny transakcyjne lub inne miary są różne w zależności od grupy?
""")

st.markdown("## Wykrywanie potencjalnych uprzedzeń w danych")

with st.expander("Wybierz parametry analizy biasu"):
    st.markdown("""
    #### ℹ️ Kolumny grupujące
    Są to kolumny kategoryczne, które dzielą dane na grupy, np.:
    - `COUNTRYNAME` - umożliwia sprawdzenie, czy klienci z różnych krajów są traktowani inaczej,
    - `ChannelName` - pozwala porównać sprzedaż przez różne kanały,
    - `PaymentMethodName` - można sprawdzić, czy metoda płatności wpływa np. na wysokość rabatu.
    """)

    group_cols = st.multiselect("Kolumny grupujące (kategorie):", 
                                 options=df.select_dtypes(include="object").columns.tolist(),
                                 default=[col for col in ["COUNTRYNAME", "ChannelName", "PaymentMethodName"] if col in df.columns])

    st.markdown("""
    #### ℹ️ Kolumny celu
    To zmienne liczbowe, które mogą różnić się między grupami, np.:
    - `TRANSACTIONPRICE` - rzeczywista cena zakupu,
    - `DISCOUNTPCTG` - procentowy rabat udzielony klientowi.
    """)

    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    default_targets = [col for col in ["TRANSACTIONPRICE", "DISCOUNTPCTG"] if col in numeric_cols]

    target_cols = st.multiselect("Kolumny celu (np. cena, rabat):", 
                                  options=numeric_cols,
                                  default=default_targets)

if st.button("Wykonaj analizę biasu"):
    bias_result = analyzer.analyze_bias(group_cols=group_cols, target_cols=target_cols)

    st.subheader("📊 Podsumowanie rozkładu kategorii")
    summary_rows = []
    for group_col, results in bias_result.items():
        if isinstance(results, dict) and "Rozkład kategorii" in results:
            cat = results["Rozkład kategorii"]
            summary_rows.append({
                "Kolumna": group_col,
                "Entropia": cat["Entropia"],
                "Max udział": cat["Max udział"],
                "Min udział": cat["Min udział"],
                "Rozstęp udziałów": cat["Rozstęp udziałów"],
                "Liczba grup": cat["Liczba grup"]
            })

    if summary_rows:
        st.dataframe(pd.DataFrame(summary_rows))

    st.markdown("---")
    st.subheader("📈 Szczegółowe średnie wg grup")

    for group_col, results in bias_result.items():
        for key, val in results.items():
            if key.startswith("Średnia"):
                st.markdown(f"#### {key} ({group_col})")
                df_avg = pd.DataFrame.from_dict(val, orient="index", columns=[key.split(" ")[-1]])
                st.dataframe(df_avg)

else:
    st.info("Wybierz kolumny i uruchom analizę, aby zobaczyć wyniki.")

st.markdown("---")
st.markdown("## 🔐 Analiza danych osobowych i wrażliwych")

st.markdown("""Ta sekcja wykrywa dane mogące naruszać prywatność użytkowników lub ujawniać wrażliwe informacje.
Zwracamy uwagę na dane osobowe (np. imię, adres, PESEL) oraz dane szczególnej kategorii (np. zdrowie, pochodzenie etniczne).""")

if st.button("Wykryj dane osobowe i wrażliwe"):
    sensitive_report = analyzer.analyze_sensitive_data()

    st.subheader("📋 Wykryte dane osobowe")
    personal = sensitive_report["Dane osobowe"]
    if personal:
        for col in personal:
            st.markdown(f"- `{col}`")
    else:
        st.info("Brak danych osobowych.")


    st.subheader("🩺 Wykryte dane wrażliwe")
    sensitive = sensitive_report["Dane wrażliwe"]
    if sensitive:
        for col in sensitive:
            st.markdown(f"- `{col}`")
    else:
        st.info("Brak danych wrażliwych.")


    st.subheader("🛡️ Poziom ryzyka")
    st.success(sensitive_report["Poziom ryzyka"])

st.markdown("---")
st.markdown("## 🌐 Mapowanie przepływu danych (Data Lineage)")

st.markdown("""Ta sekcja pokazuje, z jakiego źródła pochodzi każda kolumna w analizowanym zbiorze:
- Czy została bezpośrednio zaimportowana z danych źródłowych,
- Czy pochodzi z tabel wymiarów (przez joiny),
- Czy została wyliczona (pochodna z innych kolumn).""")

lineage_info = analyzer.get_data_lineage()
df_lineage = pd.DataFrame(lineage_info)

st.dataframe(df_lineage)

st.markdown("---")
st.markdown("## 🧾 Ocena końcowego ryzyka zgodności z AI Act")

st.markdown("""Na podstawie zidentyfikowanych danych osobowych i wrażliwych, potencjalnych stronniczości oraz przejrzystości pochodzenia danych — określamy poziom ryzyka wykorzystania zbioru w systemie AI.""")

if st.button("Przeprowadź ocenę ryzyka"):
    final_risk = analyzer.evaluate_risk()

    st.subheader("📌 Ocena ogólna")
    if "wysokie" in final_risk["Ocena ogólna"].lower():
        st.error(final_risk["Ocena ogólna"])
    elif "średnie" in final_risk["Ocena ogólna"].lower():
        st.warning(final_risk["Ocena ogólna"])
    else:
        st.success(final_risk["Ocena ogólna"])

    st.subheader("📋 Szczegóły:")
    st.markdown(f"- **Prywatność**: {final_risk['Prywatność']}")
    st.markdown(f"- **Stronniczość**: {final_risk['Stronniczość']}")
    st.markdown(f"- **Pochodzenie danych**: {final_risk['Pochodzenie danych']}")

    st.session_state["kpi_ai_compliance"] = {
        "Ocena ogólna": final_risk["Ocena ogólna"],
        "Prywatność": final_risk["Prywatność"],
        "Stronniczość": final_risk["Stronniczość"],
        "Pochodzenie danych": final_risk["Pochodzenie danych"]
    }