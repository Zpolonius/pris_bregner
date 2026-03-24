# 🚚 Bring Nordic Master-Beregner

**Bring Nordic Master-Beregner** er et avanceret internt salgsværktøj udviklet i Python og Streamlit. Værktøjet gør det muligt for Bring-sælgere i hele Norden lynhurtigt at analysere historiske fragtrapporter og simulere konsekvenserne af nye prisaftaler med ekstrem præcision.

---

## 🚀 Kernefunktioner

### 🌍 Intelligent Nordisk Zone-Mapping
Applikationen indeholder en sofistikeret zone-motor, der håndterer over 1.100 specifikke postnummer-regler for Danmark, Sverige, Norge og Finland:
*   **Sverige:** Opdelt i 9 geografiske zoner (`CITY-1-3`, `SOUTH-1-3`, `NORTH-1-3`).
*   **Norge:** Fuld integration af Oslo-regionen samt standardzonerne `NOR2` til `NORS`.
*   **Tillægshåndtering:** Automatisk identifikation af **City Surcharge** og **Remote Area Surcharge** områder via præcise interval-opslag fra officielle Master-filer.

### 💰 Avanceret Pris-simulering
*   **Multi-model Support:** Vælg mellem enhedspriser eller komplekse vægt-matricer.
*   **Vektoriseret Beregning:** Drevet af Numpy for lynhurtig behandling af selv meget store Excel/CSV-rapporter (10.000+ rækker).
*   **Forhandlings-værktøjer:** Globale skydere til justering af procenter, faste tillæg og forventet volumen-vækst.
*   **Specifikke Tillæg:** Justér prisen på City- og Remote Area-tillæg uafhængigt af grundprisen.

### 📊 Data Health & Rapportering
*   **Data Health Dashboard:** Giver øjeblikkelig feedback på datakvaliteten, herunder identifikation af gebyr-linjer (0-kilos reglen) og ukendte postnumre.
*   **Eksport:** Generer professionelle Excel-rapporter med fuldt gennemsigtige beregninger, klar til præsentation for kunden.

---

## 🛠️ Teknisk Setup

### Installation
Appen kræver Python 3.9+ og de nødvendige biblioteker:
```bash
pip install streamlit pandas numpy openpyxl
```

### Kør applikationen
```bash
streamlit run app.py
```

### Projektstruktur
*   `app.py`: Hovedbrugerfladen og Streamlit-logik.
*   `calculator.py`: Vektoriseret beregningsmotor.
*   `zones.py`: Intelligent zone-mapping og postnummer-validering.
*   `config.json`: Dynamisk konfiguration af vægttrin, services og zoner.
*   `Master_*.csv`: Officielle lister over postnumre til surcharge-identifikation.

---

## 🔑 For Sælgere: Hurtig Start
1.  **Download Skabelon:** Hent den færdige Excel-matrix fra sidebar'en.
2.  **Upload Data:** Indlæs en "Foreløbelig fragtberegning" fra MyBring (CSV eller Excel).
3.  **Indlæs Priser:** Upload din færdige prisaftale i skabelon-formatet.
4.  **Simulér & Eksportér:** Justér tillæg og procenter, og download den færdige analyse.

---

*Udviklet som et specialværktøj til optimering af nordiske fragtberegninger.* 🚛✨
