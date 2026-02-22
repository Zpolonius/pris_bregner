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
- **Norge (NO)**:
  - 00-10: `OSL`
  - 13-20: `NOR2`
  - 40: `NOR3`
  - 80: `NOR4`
  - 90: `NORS`
- **Finland (FI)**:
  - 00: `FI00`
  - 45: `FI01`
  - 80: `FI02`
  - 94: `FI04`

---

## Udvikling & Kørsel

### Installation af afhængigheder
```bash
pip install streamlit pandas openpyxl
```

### Kørsel af applikationen
```bash
streamlit run app.py
```

### Generering af ny priskonfiguration
Hvis `Pris_Konfiguration.xlsx` mangler eller skal nulstilles:
```bash
python add_files.py
```

---

## Udviklingsretningslinjer
- **Navngivning**: Brug danske termer i UI, men engelske variabelnavne i koden (f.eks. `ny_pris` vs `new_price`).
- **Dataflow**: Streamlit genindlæser hele scriptet ved hver interaktion. Brug `st.cache_data` til tunge beregninger eller filindlæsning, hvis ydeevnen bliver et problem.
- **Testdata**: Brug `test_bring_data.csv` til validering af beregningslogik.

---

## TODO / Kommende Funktioner
- [ ] Implementer fuld `enrich_and_calculate` logik i `app.py` (synkronisering med `calculator.py`).
- [ ] Tilføj Heatmap-visualisering af pakkemix (vægt vs. land).
- [ ] Mulighed for at eksportere den færdige analyse til en samlet Excel-rapport.
