# 🚚 Bring Nordic Master-Beregner v1.0 - PROD READY

Dette værktøj er nu klar til udrulning. Det er optimeret til at håndtere både historiske Bring-fakturaer og manuelle estimater under forhandling.

---

## 🚀 Seneste Opdateringer (QA Gennemført)

### 1. Manuel Estimering & Volumen-Matrix
- Sælgeren kan nu vælge "Manuel Estimering" i sidebar'en.
- Der er tilføjet en **Volumen-Matrix** under hver lande-fane, hvor man kan indtaste antal pakker pr. tjeneste og vægt.
- Beregningsmotoren er opdateret til at bruge en vægtet `Mængde`-kolonne, så alle totaler og heatmaps afspejler de indtastede volumener.

### 2. Præcis Zone-mapping (Norge Special)
- **Norge:** Nu baseret på numeriske intervaller (0000-1299=OSL, 1300-3999=NOR2, osv.).
- **Rensning:** Automatisk håndtering af foranstillede nuller (zfill) og fjernelse af mellemrum i postnumre.
- **Zone-priser:** Alle zoner (NOR2-NORS, FI00-FI04) er nu eksplicitte rækker i priseditoren. Appen prioriterer zone-specifikke priser før produkt-standardpriser.

### 3. Valuta-politik (En krone er en krone)
- Efter analyse er al valuta-omregning fjernet for at gøre værktøjet intuitivt. 
- **Regel:** Appen antager, at alle indtastede priser er i kundens afregningsvaluta (typisk DKK).

---

## 🧠 Kerne-logik (VIGTIGT FOR AI)

- **0-kilos reglen:** Pakker med vægt = 0 eller gammel pris = 0 betragtes som gebyrer og bevarer deres oprindelige pris uændret.
- **Vægttrin:** Priser slås op som "op til" (f.eks. en 4.5kg pakke i en 1, 3, 5kg matrix får 5kg prisen).
- **Mængde-skalering:** Alle beregninger (Old/New Price) ganges med `Mængde * (1 + Volumen-vækst)`.

---

## 🛠️ Teknisk Status
- **Dependencies:** `streamlit`, `pandas`, `openpyxl`, `matplotlib` (til heatmap).
- **Sikkerhed:** Excel-eksport er beskyttet mod Formula Injection.
- **Robusthed:** Kolonne-mapper håndterer alternative navne (Weight, Price, Zip) automatisk.

*Tak for i dag! Værktøjet er gemt og klar til næste session.* 🚛✨
