# classes/ai_compliance.py

import numpy as np
import pandas as pd
import re

class AIComplianceAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def analyze_bias(self, group_cols=None, target_cols=None):
        """
        Wykrywa potencjalne uprzedzenia (bias) względem kolumn grupujących.
        """
        if group_cols is None:
            group_cols = ["COUNTRYNAME", "ChannelName", "PaymentMethodName"]
        if target_cols is None:
            target_cols = ["TRANSACTIONPRICE", "DISCOUNTPCTG"]

        report = {}

        for group_col in group_cols:
            if group_col in self.df.columns:
                try:
                    report[group_col] = self._compute_bias_for_column(group_col, target_cols)
                except Exception as e:
                    report[group_col] = f"Błąd analizy: {e}"

        return report

    def _compute_bias_for_column(self, group_col, target_cols):
        bias_report = {}

        value_counts = self.df[group_col].value_counts(normalize=True)
        entropia = -np.sum(value_counts * np.log2(value_counts + 1e-9))
        prop_diff = value_counts.max() - value_counts.min()

        bias_report["Rozkład kategorii"] = {
            "Entropia": round(entropia, 4),
            "Max udział": round(value_counts.max(), 4),
            "Min udział": round(value_counts.min(), 4),
            "Rozstęp udziałów": round(prop_diff, 4),
            "Liczba grup": len(value_counts)
        }

        for target in target_cols:
            if target in self.df.columns:
                grouped = self.df.groupby(group_col)[target].mean()
                bias_report[f"Średnia {target} wg grup"] = grouped.to_dict()
                bias_report[f"Rozstęp średnich {target}"] = round(grouped.max() - grouped.min(), 4)

        return bias_report

    def analyze_sensitive_data(self):
        """
        Wykrywa dane osobowe i wrażliwe oraz ocenia poziom ryzyka, z uwzględnieniem wyjątków.
        """
        sensitive_keywords = ['health', 'gender', 'religion', 'ethnicity', 'politics', 'income', 'disability', 'sexual']
        personal_keywords = ['name', 'firstname', 'lastname', 'email', 'phone', 'address', 'dob', 'pesel', 'nip', 'user', 'ip']

        # Kolumny, które mają słowo 'name', ale nie są osobowe
        name_exceptions = ['productname', 'paymentmethodname', 'deliverymethodname', 
                        'channelname', 'productsubcategoryname', 'productcategoryname']

        sensitive_cols = []
        personal_cols = []

        for col in self.df.columns:
            col_lower = col.lower()

            if col_lower in name_exceptions:
                continue  # pomijamy mylące nazwy

            if any(kw in col_lower for kw in sensitive_keywords):
                sensitive_cols.append(col)
            if any(kw in col_lower for kw in personal_keywords):
                personal_cols.append(col)

        high_risk = bool(sensitive_cols or personal_cols)

        if high_risk:
            risk_level = "🚨 Wysokie - dane wrażliwe lub identyfikujące"
        elif any("id" in col.lower() for col in self.df.columns if col.lower() not in name_exceptions):
            risk_level = "⚠️ Średnie - dane pseudonimizowane"
        else:
            risk_level = "✅ Niskie - brak danych osobowych/wrażliwych"

        return {
            "Dane osobowe": personal_cols,
            "Dane wrażliwe": sensitive_cols,
            "Poziom ryzyka": risk_level
        }
    
    def get_data_lineage(self):
        """
        Zwraca informacje o pochodzeniu danych: źródło kolumny i typ pochodzenia (oryginalna, join, wyliczona).
        """
        lineage_map = {
            # Oryginalne kolumny z tabeli faktów
            "ORDERKEY": ("FactOnlineSales", "oryginalna"),
            "ORDERLINENUMBER": ("FactOnlineSales", "oryginalna"),
            "TRANSACTIONPRICE": ("FactOnlineSales", "oryginalna"),
            "QUANTITY": ("FactOnlineSales", "oryginalna"),
            "DISCOUNTPCTG": ("FactOnlineSales", "oryginalna"),
            "DELIVERYCOST": ("FactOnlineSales", "oryginalna"),
            "PRODUCTCOST": ("FactOnlineSales", "oryginalna"),

            # Kolumny z joinów
            "CustomerName": ("DimCustomer", "join przez CustomerKey + przekształcenie (imię + nazwisko)"),
            "ProductName": ("DimProduct", "join przez ProductKey"),
            "ProductCategoryName": ("DimProduct", "join przez ProductKey"),
            "ChannelName": ("DimOrderChannel", "join przez ChannelKey"),
            "PaymentMethodName": ("DimPaymentMethod", "join przez PaymentMethodKey"),
            "DeliveryMethodName": ("DimDeliveryMethod", "join przez DeliveryMethodKey"),
            "COUNTRYNAME": ("DimSalesTerritory", "join przez SalesTerritoryKey"),
            "ProductSubcategoryName": ("DimProduct", "join przez ProductKey"),

            # Kolumny wyliczone
            "TotalTransactionPrice": ("FactOnlineSales", "wyliczona (TransactionPrice x Quantity)"),
            "TotalDiscountAmount": ("FactOnlineSales", "wyliczona (DiscountAmount x Quantity)"),
            "TotalCatalogPrice": ("FactOnlineSales", "wyliczona (CatalogPrice x Quantity)")
        }

        lineage_info = []
        for col in self.df.columns:
            source, col_type = lineage_map.get(
                col, ("❓ Nieznane", "❓ Nieokreślone"))
            lineage_info.append({
                "Kolumna": col,
                "Źródło": source,
                "Typ pochodzenia": col_type
            })

        return lineage_info
    
    def evaluate_risk(self):
        """
        Ocena końcowego ryzyka zgodności danych z AI Act.
        Analizuje: prywatność, stronniczość i pochodzenie danych.
        """
        # --- Prywatność
        privacy = self.analyze_sensitive_data()
        privacy_level = privacy["Poziom ryzyka"]

        if "wysokie" in privacy_level.lower():
            privacy_score = 2
        elif "średnie" in privacy_level.lower():
            privacy_score = 1
        else:
            privacy_score = 0

        # --- Stronniczość (na podstawie rozstępów udziałów)
        bias = self.analyze_bias()
        bias_scores = []

        for col, report in bias.items():
            if isinstance(report, dict):
                spread = report["Rozkład kategorii"]["Rozstęp udziałów"]
                if spread > 0.5:
                    bias_scores.append(2)
                elif spread > 0.2:
                    bias_scores.append(1)
                else:
                    bias_scores.append(0)

        bias_score = max(bias_scores) if bias_scores else 0

        # --- Pochodzenie danych
        lineage = self.get_data_lineage()
        unknowns = [entry for entry in lineage if "❓" in entry["Źródło"]]
        lineage_score = 2 if len(unknowns) > 3 else 1 if unknowns else 0

        total_score = privacy_score + bias_score + lineage_score

        if total_score >= 5:
            overall = "🚨 Wysokie ryzyko"
        elif total_score >= 3:
            overall = "⚠️ Średnie ryzyko"
        else:
            overall = "✅ Niskie ryzyko"

        return {
            "Ocena ogólna": overall,
            "Prywatność": privacy_level,
            "Stronniczość": f"{['✅ Niska', '⚠️ Średnia', '🚨 Wysoka'][bias_score]}",
            "Pochodzenie danych": f"{['✅ Znane', '⚠️ Częściowo nieznane', '🚨 Braki w definicji'][lineage_score]}"
        }


