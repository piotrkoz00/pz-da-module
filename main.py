# main.py

import os
import streamlit as st
import pandas as pd
import sqlite3

def load_data(
        csv_path, table_name, conn,
        sep=";", decimal=",", encoding="utf-8", header=0
):
    """
    Wczytuje plik CSV do DataFrame z zadanymi parametrami odczytu,
    sprawdza zgodność kolumn (case-insensitive),
    wykonuje konwersje typów oraz zapisuje do bazy SQLite.
    """
    df = pd.read_csv(
        csv_path, delimiter=sep, decimal=decimal, encoding=encoding, header=header, dtype=str
    )

    # Mapowanie nazw kolumn do wersji lower-case
    colmap = {c.lower(): c for c in df.columns}

    # Konwersje liczbowe (dla FactOnlineSales)
    if table_name == 'FactOnlineSales':
        float_cols = ['CatalogPrice', 'DiscountAmount', 'DiscountPctg', 'TransactionPrice', 'DeliveryCost',
                      'ProductCost']
        int_cols = [
            'Quantity', 'OrderLineNumber', 'CustomerKey', 'ProductKey',
            'SalesTerritoryKey', 'ChannelKey', 'PaymentMethodKey',
            'DeliveryMethodKey', 'OrderDateKey', 'ShipDateKey'
        ]

        # Konwersje float
        for col in float_cols:
            col_lower = col.lower()
            if col_lower in colmap:
                true_col = colmap[col_lower]
                df[true_col] = df[true_col].str.replace(',', '.', regex=False).astype(float)
            else:
                raise ValueError(
                    f"Kolumna '{col}' nie została znaleziona (ignorując wielkość liter) podczas konwersji do float.")

        # Konwersje int
        for col in int_cols:
            col_lower = col.lower()
            if col_lower in colmap:
                true_col = colmap[col_lower]
                df[true_col] = df[true_col].astype(int)
            else:
                raise ValueError(
                    f"Kolumna '{col}' nie została znaleziona (ignorując wielkość liter) podczas konwersji do int.")

    # Wstawienie danych do bazy
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    return df

st.set_page_config(page_title="Aplikacja wielostronicowa - Jakość danych", layout="wide")
st.title("Witaj w aplikacji do analizy danych!")

# Tworzenie bazy SQLite
conn = sqlite3.connect('sales.db')

# Lista tabel i ścieżek
tables = {
    'DimCustomer': 'data/DimCustomer.csv',
    'DimDate': 'data/DimDate.csv',
    'DimDeliveryMethod': 'data/DimDeliveryMethod.csv',
    'DimGeography': 'data/DimGeography.csv',
    'DimOrderChannel': 'data/DimOrderChannel.csv',
    'DimPaymentMethod': 'data/DimPaymentMethod.csv',
    'DimProduct': 'data/DimProduct.csv',
    'DimSalesTerritory': 'data/DimSalesterritory.csv',
    'FactOnlineSales': 'data/FactOnlineSales.csv',
}

with st.form("csv_options_form"):
    st.markdown("#### Opcje odczytu pliku CSV")
    col1, col2 = st.columns(2)
    sep = col1.selectbox(
        "Wybierz separator kolumn",
        options={",": "Przecinek (,)", ";": "Średnik (;)", "\t": "Tabulator (\\t)", "|": "Pionowa kreska (|)"},
        format_func=lambda x: {",": "Przecinek (,)", ";": "Średnik (;)", "\t": "Tabulator (\\t)", "|": "Pionowa kreska (|)"}[x],
        index=1  # najczęściej używany w Polsce to ;
    )
    decimal = col2.selectbox(
        "Separator dziesiętny",
        options=[".", ","],
        index=1  # najczęściej w Polsce to przecinek
    )
    encoding = col1.selectbox(
        "Kodowanie znaków",
        options=["utf-8", "latin1", "cp1250", "iso-8859-2"],
        index=0
    )
    header_row = col2.checkbox(
        "Nagłówek w pierwszym wierszu?",
        value=1
    )
    submitted = st.form_submit_button("Wczytaj dane")

if submitted:
    try:
        for table_name, file_path in tables.items():
            if os.path.exists(file_path):
                df = load_data(file_path, table_name, conn,
                               sep, decimal, encoding, header=0 if header_row else None)
                st.success(f"Załadowano tabelę `{table_name}` ({len(df)} rekordów)")
    except Exception as e:
        st.error(f"Błąd podczas wczytywania pliku: {e}")

# --- Sekcja podglądu istniejących tabel ---
st.subheader("Podgląd danych z bazy")

# Pobierz listę tabel z bazy SQLite
def get_flat_fact_table(conn):
    query = """
    SELECT
      F.*,
      (F.CATALOGPRICE * F.QUANTITY) AS TotalCatalogPrice,
      (F.DISCOUNTAMOUNT * F.QUANTITY) AS TotalDiscountAmount,
      (F.TRANSACTIONPRICE * F.QUANTITY) AS TotalTransactionPrice,
      P.ProductName,
      P.ProductSubcategoryName,
      P.ProductCategoryName,
      C.FIRSTNAME || ' ' || C.LASTNAME as CustomerName,
      D.ChannelName,
      PM.PaymentMethodName,
      DM.DeliveryMethodName,
      ST.COUNTRYNAME
    FROM FactOnlineSales F
    LEFT JOIN DimProduct P ON F.PRODUCTKEY = P.ProductKey
    LEFT JOIN DimCustomer C ON F.CUSTOMERKEY = C.CUSTOMERKEY
    LEFT JOIN DimOrderChannel D ON F.CHANNELKEY = D.ChannelKey
    LEFT JOIN DimPaymentMethod PM ON F.PAYMENTMETHODKEY = PM.PaymentMethodKey
    LEFT JOIN DimDeliveryMethod DM ON F.DELIVERYMETHODKEY = DM.DeliveryMethodKey
    LEFT JOIN DimSalesterritory ST ON F.SALESTERRITORYKEY = ST.SALESTERRITORYKEY
    """
    df_flat = pd.read_sql(query, conn)
    cols_to_drop = [col for col in df_flat.columns if 'key' in col.lower()]
    df_flat = df_flat.drop(columns=cols_to_drop + ['CATALOGPRICE', 'DISCOUNTAMOUNT', 'TRANSACTIONPRICE', 'QUANTITY'])
    return df_flat

if st.button("Załaduj i wyświetl spłaszczoną tabelę"):
    df_flat = get_flat_fact_table(conn)
    st.session_state["df"] = df_flat
    st.success("Spłaszczona tabela została załadowana do analizy!")
    st.dataframe(df_flat.head())
else:
    st.info("Brak tabel w bazie danych. Wgraj dane, aby pojawiły się tutaj.")
