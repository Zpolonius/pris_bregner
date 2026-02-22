# 🚚 Bring Nordic Master-Beregner v1.0 - PROD READY

Dette dokument markerer overdragelsen af den færdige version af salgsværktøjet. Værktøjet er udviklet til at give Bring-sælgere et kraftfuldt "Salgs-cockpit" til analyse og forhandling af nordiske fragtaftaler.

---

## 🚀 Hovedfunktioner

### 1. Dobbelt Datakilde (Fleksibilitet)
- **Upload Rapport:** Håndterer rå Bring "Foreløbig fragtberegning"-filer (CSV/Excel).
- **Manuel Estimering:** Gør det muligt at indtaste forventet volumen pr. tjeneste og vægtklasse manuelt, når kunden endnu ikke har trukket en rapport.

### 2. Intelligent Beregningsmotor
- **0-kilos reglen:** Bevarer automatisk prisen på tillægsgebyrer og information (0kg/0kr linjer).
- **Zone-mapping:** Automatisk postnummer-identifikation for SE, NO og FI.
- **Vægtet Mængde:** Hele motoren bagved bruger en `Mængde`-kolonne, der gør, at både række-baserede fakturaer og manuelt indtastede mængder summeres korrekt.

### 3. Forhandling & Simulering (Live)
- **Global Prisjustering (%):** Simuler lynhurtigt en generel prisstigning eller rabat på tværs af alle lande.
- **Volumen-vækst (%):** Vis kunden konsekvensen af deres forventede vækst (f.eks. +25% pakker næste år).
- **Prismodeller:** Skift mellem "Enhedspris" og "Vægtbaseret Matrix" med ét klik.

### 4. Visualisering & Eksport
- **Pakkeprofil (Heatmap):** Viser præcis hvor kundens pakker ligger (Zone vs. Vægtklasse) med blåt farve-overlay.
- **Multi-ark Excel Rapport:** Genererer en professionel .xlsx-fil med Dashboard, Lande-oversigt og detaljeret data-grundlag (inkl. sikkerhed mod Excel Formula Injection).

---

## 🛠️ Teknisk Setup (Senior QA Status)

- **Sikkerhed:** Alle tekstfelter i Excel-eksporten "escapes" med en enkelt pløk (`'`) for at undgå ondsindede formler.
- **Robusthed:** Inkluderer en "Kolonne-Mapper", der lader brugeren manuelt vælge kolonner, hvis filens navne afviger fra standarden.
- **Type-sikker:** Koden er gennemtestet for type-fejl og bruger eksplicit casting (`float()`, `pd.to_numeric()`) for at undgå beregningsfejl.
- **Branding:** Fuldt integreret med Bring logoer, favicon og officielle farver.

---

## 📖 Hurtig Guide til Sælgeren

1.  **Vælg lande:** Vælg hvilke nordiske lande kunden sender til.
2.  **Data:** Upload kundens faktura eller indtast deres forventede volumen i fanerne.
3.  **Hjælp appen:** Hvis appen spørger om kolonner (gul boks), så vælg de rigtige felter fra din fil.
4.  **Simuler:** Juster priserne i tabellerne, træk i sliderne for pris/volumen, og se den samlede Nordiske besparelse i toppen.
5.  **Lever:** Tryk på "Hent Excel-rapport" og vedhæft den til dit tilbud eller brug den som internt beslutningsgrundlag.

---

*Projektet er nu afsluttet og klar til brug.* 🚛✨
