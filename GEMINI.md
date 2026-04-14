# GEMINI.md - Bring Nordic Master-Beregner

Dette dokument fungerer som den primære instruktionskontekst for AI-interaktioner i dette projekt.

## Projektoversigt
**Bring Nordic Master-Beregner** er et internt salgsværktøj udviklet i Python og Streamlit. Værktøjet gør det muligt for sælgere at uploade historiske Bring-fakturaer (CSV-format) og simulere konsekvenserne af nye prisaftaler på tværs af de nordiske lande (DK, SE, NO, FI).

### Hovedteknologier
- **Python 3.x**
- **Streamlit**: Web-interface og interaktive data-editorer.
- **Pandas**: Databehandling og beregning af pris-matricer.
- **Openpyxl**: Håndtering af Excel-baserede priskonfigurationer.

### Arkitektur
1.  **UI (`app.py`)**: Håndterer upload af filer, lande-specifikke faner, interaktive priseditorer og visualisering af resultater.
2.  **Logik (`calculator.py`)**: Indeholder kerne-beregningsmotoren, der mapper forsendelser til zoner og vægttrin.
3.  **Konfiguration (`Pris_Konfiguration.xlsx`)**: Gemmer vægtbaserede pris-matricer pr. land og service.
4.  **Utility (`add_files.py`)**: Script til generering af den initiale Excel-priskonfiguration.

---

## Forretningsregler & Konventioner

### 1. Prisberegning
- **0-kilos reglen**: Hvis en pakkes vægt er 0 kg, eller den oprindelige pris er 0 kr, skal prisen bevares uændret (håndtering af gebyrer, toldlinjer osv.).
- **Vægttrin**: Priser beregnes som "op til"-værdier (f.eks. 1kg, 3kg, 5kg). Pakker over det højeste trin tildeles prisen for det maksimale trin.

### 2. Zone-mapping (Postnumre)
- **Danmark (DK)**: Kører som standard "Standard" zone.
- **Sverige (SE)**:
  - 00-10: `CITY-1`
  - 20-40: `CITY-2`
  - DEFAULT: `SOUTH-2`
  - *Surcharges*: Fuld understøttelse af Stockholm og Göteborg.
- **Norge (NO)**:
  - 00-10: `OSL`
  - 13-20: `NOR2`
  - 40: `NOR3`
  - 80: `NOR4`
  - 90: `NORS`
  - *Surcharges*: Fuld 2026-integration med 85 City-intervaller (Oslo) og 265 Remote-intervaller udtrukket fra officielle PDF-lister.
- **Finland (FI)**:
  - 00: `FI00`
  - 45: `FI01`
  - 80: `FI02`
  - 94: `FI04`

### 3. Data-input & Normalisering
- **Auto-mapping**: Systemet genkender automatisk kolonner som `WEIGHT`, `RECEIVER_ZIP_CODE`, `CARRIER_SERVICE` m.fl.
- **Land-normalisering**: Navne som "Norge", "Sverige", "Danmark" konverteres automatisk til ISO-koder ("NO", "SE", "DK").

---

## Udvikling & Kørsel

### Installation af afhængigheder
```bash
pip install streamlit pandas openpyxl pdfplumber
```

### Kørsel af applikationen
```bash
streamlit run app.py
```

### Vedligeholdelse af Surcharge-data
Hvis de officielle PDF-lister opdateres, kan de nye data udtrækkes til CSV-filerne via:
```bash
python update_master_files.py
```

---

## Udviklingsretningslinjer
- **Navngivning**: Brug danske termer i UI, men engelske variabelnavne i koden (f.eks. `ny_pris` vs `new_price`).
- **Dataflow**: Streamlit genindlæser hele scriptet ved hver interaktion. Brug `@st.cache_data` (især i `zones.py`) til tunge beregninger eller filindlæsning for at bevare performance.
- **Testdata**: Brug `shipmentdata.xlsx` til validering af norske surcharge-beregninger.

---

## TODO / Kommende Funktioner
- [x] Implementer fuld `enrich_and_calculate` logik i `app.py`.
- [x] Tilføj Procentvis visning af surcharge-pakker i dashboard.
- [ ] Tilføj Heatmap-visualisering af pakkemix (vægt vs. land).
- [ ] Mulighed for at eksportere den færdige analyse til en samlet Excel-rapport.
