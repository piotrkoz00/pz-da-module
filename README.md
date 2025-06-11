# System Data Governance i Oceny Jakości Danych dla AI

## Autorzy

- Piotr Mariusz Kozikowski
- Kacper Dulewicz
- Anna Kaczmarek

### Matematyka stosowana, semestr III, studia II stopnia

---

## Cel projektu

Celem projektu jest stworzenie prototypu systemu umożliwiającego analizę jakości danych, ocenę ich zgodności z przepisami AI Act oraz przydatności do trenowania modeli AI, zgodnie z zasadami Data Governance. System jest przeznaczony do pracy **lokalnej** i oferuje interaktywne dashboardy analityczne.

---

## Architektura rozwiązania

- **Lokalność**: System działa wyłącznie na infrastrukturze przedsiębiorstwa, nie korzysta z chmury.
- **Budowa modułowa**: Każdy etap analizy to osobny moduł/strona Streamlit.
- **Integracja z bazą danych SQLite** (możliwość łatwego rozszerzenia).
- **Bezpieczeństwo i prywatność**: Dane pozostają wyłącznie lokalnie; system nie przechowuje danych po zakończeniu sesji.
- **Łatwość rozszerzania**: Możliwość dodania nowych modułów oraz źródeł danych.

---

## Etapy analizy danych

### 1. Podstawowa analiza jakości danych (`01_Data_Quality.py`)

- **Cel:** Ocena kompletności i poprawności danych.
- **KPI:**
  - Procent brakujących wartości
  - Procent wartości odstających (outliers)
  - Procent duplikatów
  - Zgodność typów danych z oczekiwaniami
- **Funkcjonalności:**
  - Automatyczne wykrywanie braków danych
  - Identyfikacja wartości odstających
  - Analiza rozkładów zmiennych (interaktywne histogramy)
  - Raportowanie podstawowych statystyk opisowych (z typami kolumn)
- **Moduły:**  
  - `pages/01_Data_Quality.py` – dashboard  
  - `classes/data_quality.py` – logika analizy jakości

---

### 2. Analiza zgodności z wymaganiami AI Act (`02_AI_Compliance.py`)

- **Cel:** Weryfikacja, czy dane mogą być użyte do AI zgodnie z wymogami prawnymi.
- **KPI:**
  - Wskaźnik potencjalnej stronniczości (bias)
  - Przejrzystość pochodzenia danych (data lineage)
  - Ochrona danych wrażliwych
  - Zgodność z przepisami prywatności
- **Funkcjonalności:**
  - Analiza uprzedzeń w danych (bias)
  - Identyfikacja danych osobowych/wrażliwych
  - Mapowanie przepływu i pochodzenia danych
  - Ocena ryzyka zgodności z AI Act
- **Moduły:**  
  - `pages/02_AI_Compliance.py` – dashboard  
  - `classes/ai_compliance.py` – logika analizy zgodności

---

### 3. Zaawansowana analiza przydatności do trenowania AI (`03_AI_Readiness_Analyzer.py`)

- **Cel:** Ocena, jak dobrze dane nadają się do trenowania modeli AI.
- **KPI:**
  - Wskaźnik reprezentatywności danych
  - Jakość metadanych
  - Zbilansowanie klas (dla klasyfikacji)
  - Szacowana wydajność modeli trenowanych na tych danych
- **Funkcjonalności:**
  - Analiza reprezentatywności i jakości metadanych
  - Analiza korelacji oraz rozkładów warunkowych
  - Rekomendacje dotyczące przygotowania danych
  - Symulacja trenowania prostych modeli AI
- **Moduły:**  
  - `pages/03_AI_Readiness_Analyzer.py` – dashboard  
  - `classes/ai_readiness_analyzer.py` – logika analizy

---

## Implementacja dashboardów

- **Panel główny:** Podsumowanie wszystkich KPI.
- **Szczegółowe widoki:** Osobne dashboardy dla każdego etapu.
- **Drill-down:** Przechodzenie od ogólnych wskaźników do szczegółowych informacji o danych.
- **System alertów:** Automatyczne ostrzeżenia dla wykrytych problemów.
- **Rekomendacje:** Moduł rekomendacji naprawczych i raportowanie zgodności z AI Act.

---

## Uruchomienie aplikacji

1. **Instalacja wymaganych bibliotek:**

```
pip install -r requirements.txt
```

2. **Uruchom aplikację Streamlit:**

```
streamlit run Data_Analysis_Modules.py
```

3. **Obsługa danych:**
- Wybierz lub załaduj dane do bazy (np. SQLite) na stronie głównej.
- Przechodź do kolejnych zakładek analitycznych.

---

## Wymagania i bezpieczeństwo

- **Dane nie są przesyłane na zewnątrz** — analiza w całości lokalna.
- **Brak trwałego przechowywania danych po zakończeniu sesji.**
- System można łatwo rozszerzyć o nowe źródła danych i etapy analizy.

---

## Licencja

Wykorzystanie w celach komercyjnych wymaga uzyskania zgody autorów.

---