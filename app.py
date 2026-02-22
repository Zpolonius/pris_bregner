import streamlit as st
import pandas as pd
import io

# --- KONFIGURATION (Zoner & Vægttrin) ---
PRIS_STEPS = {
    "DK": [1, 3, 5, 10, 15, 20, 25, 30, 35],
    "SE": [1, 3, 6, 10, 15, 20, 30, 50, 60, 70],
    "NO": [1, 2, 5, 8, 12, 16, 20, 30, 40, 50],
    "FI": [1, 3, 6, 10, 15, 20, 30, 40, 50, 63]
}

# Mapping af zoner baseret på postnummer
ZONE_MAPS = {
    "SE": {"00": "CITY-1", "10": "CITY-1", "20": "CITY-2", "40": "CITY-2", "DEFAULT": "SOUTH-2"},
    "NO": {"00": "OSL", "01": "OSL", "10": "OSL", "13": "NOR2", "20": "NOR2", "40": "NOR3", "80": "NOR4", "90": "NORS", "DEFAULT": "NOR2"},
    "FI": {"00": "FI00", "45": "FI01", "80": "FI02", "94": "FI04", "DEFAULT": "FI01"}
}

def get_zone(row, country):
    if country == "DK": return "Standard"
    postnr = str(row.get('Modtagers postnummer', ''))[:2]
    maps = ZONE_MAPS.get(country, {})
    return maps.get(postnr, maps.get("DEFAULT", f"Zone 1 ({country})"))

def get_weight_bracket(weight, w_steps):
    """Beregner hvilken vægtklasse pakken tilhører til oversigten"""
    if weight == 0: return "0 kg (Gebyr/Info)"
    prev = 0
    for step in w_steps:
        if weight <= step:
            return f"{prev}-{step} kg"
        prev = step
    return f">{w_steps[-1]} kg"

st.set_page_config(page_title="Bring Nordic Master", layout="wide", page_icon="logo/favicon.ico")

# --- LOGO & TITEL ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.image("logo/bring_new_logo.png", width=150)

with col_title:
    st.title("🌍 Bring Nordic Master-Beregner")
    st.markdown("*Det ultimative salgsværktøj til nordiske fragtsimuleringer.*")

# --- SIDEBAR ---
with st.sidebar:
    st.image("logo/bring_new_logo.png", width=200)
    st.header("1. Upload Data")
    uploaded_files = st.file_uploader("Upload CSV eller Excel-rapporter", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
    
    st.divider()
    model_type = st.radio(
        "2. Vælg Prismodel",
        ["Enhedspris (Fast pris)", "Vægtbaseret pris (Matrix)"]
    )
    
    st.divider()
    st.header("📈 Forhandling & Justering")
    adj_pct = st.slider(
        "Generel prisjustering (%)",
        min_value=-20.0,
        max_value=40.0,
        value=0.0,
        step=0.5,
        help="Simuler en prisstigning eller nedsættelse på tværs af alle priser."
    )
    vol_adj_pct = st.slider(
        "Forventet volumen-vækst (%)",
        min_value=-50.0,
        max_value=200.0,
        value=0.0,
        step=5.0,
        help="Simuler hvad der sker hvis kunden øger eller sænker deres pakkemængde."
    )
    
    vol_multiplier = 1 + vol_adj_pct / 100
    st.info(f"Beregninger baseres på {vol_multiplier:.2f}x nuværende volumen.")

# --- HOVEDPROGRAM ---
if uploaded_files:
    # 1. Saml alle uploadede filer
    dfs = []
    for f in uploaded_files:
        try:
            if f.name.endswith('.csv'):
                temp_df = pd.read_csv(f, sep=None, engine='python', encoding_errors='replace')
            else:
                temp_df = pd.read_excel(f)
            temp_df.columns = [str(c).strip() for c in temp_df.columns]
            dfs.append(temp_df)
        except Exception as e:
            st.error(f"Fejl ved indlæsning af {f.name}: {e}")
    
    if not dfs:
        st.stop()
        
    master_df = pd.concat(dfs, ignore_index=True)
    
    # --- KOLONNE MAPPING (Sikkerhedsventil for sælgere) ---
    required_cols = {
        'Land leveringsadresse': ['Land leveringsadresse', 'Country', 'Land'],
        'Vægt (kg)': ['Vægt (kg)', 'Vægt', 'Weight'],
        'Aftalepris': ['Aftalepris', 'Pris', 'Price', 'Faktureret beløb'],
        'Modtagers postnummer': ['Modtagers postnummer', 'Postnummer', 'Zip', 'Zip code'],
        'Produkt': ['Produkt', 'Product', 'Service']
    }
    
    mapping = {}
    missing_cols = []
    
    for key, alts in required_cols.items():
        found = False
        for alt in alts:
            if alt in master_df.columns:
                mapping[key] = alt
                found = True
                break
        if not found:
            missing_cols.append(key)

    if missing_cols:
        st.warning("⚠️ **Vigtigt:** Vi kunne ikke finde alle de nødvendige oplysninger i din fil automatisk.")
        with st.expander("Klik her for at hjælpe appen med at finde de rigtige kolonner"):
            for col in missing_cols:
                mapping[col] = st.selectbox(f"Hvilken kolonne i din fil svarer til '{col}'?", master_df.columns, key=f"map_{col}")
    
    # Anvend mapping
    master_df = master_df.rename(columns={v: k for k, v in mapping.items() if v in master_df.columns})

    # --- DATA RENSNING ---
    # Fyld standardværdier og rens typer
    master_df['Land leveringsadresse'] = master_df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().upper()
    
    def clean_numeric(val):
        if pd.isna(val): return 0.0
        s = str(val).replace(' ', '').replace(',', '.')
        try: return float(s)
        except: return 0.0

    master_df['Vægt (kg)'] = master_df['Vægt (kg)'].apply(clean_numeric)
    master_df['Aftalepris'] = master_df['Aftalepris'].apply(clean_numeric)
    master_df['Modtagers postnummer'] = master_df['Modtagers postnummer'].fillna('0000').astype(str).str.strip()
    master_df['Produkt'] = master_df['Produkt'].fillna('Ukendt').astype(str).str.strip()

    with st.expander("🛠️ Se detaljer om data-rensning"):
        st.write("Kolonne-mapping anvendt:", mapping)
        st.success("Data er renset og klar til analyse.")

    aktive_lande = sorted([l for l in master_df['Land leveringsadresse'].unique().tolist() if l != 'UKENDT' and l != '0.0'])
    if not aktive_lande:
        st.warning("Ingen gyldige lande fundet i data (tjek kolonnen 'Land leveringsadresse').")
        st.stop()
        
    st.success(f"Fandt data for følgende lande: {', '.join(aktive_lande)}")
    
    # 2. DYNAMISKE FANER TIL PRIS-EDITERING
    st.subheader("3. Konfigurer priser pr. land")
    tabs = st.tabs(aktive_lande)
    
    edited_prices_dict = {}
    
    for i, land in enumerate(aktive_lande):
        with tabs[i]:
            land_code = land.upper().strip()
            w_steps = PRIS_STEPS.get(land_code, PRIS_STEPS["DK"])
            
            if land_code == "SE": services = ["0342 PickUp Parcel Bulk", "CITY-1", "CITY-2", "SOUTH-2"]
            elif land_code == "NO": services = ["0342 PickUp Parcel Bulk", "OSL", "NOR2", "NOR3"]
            elif land_code == "FI": services = ["0342 PickUp Parcel Bulk", "FI00", "FI01", "FI02"]
            else: services = ["PickUp Parcel", "Home Delivery", "Business Parcel"]
            
            if "Enhedspris" in model_type:
                enhed_df = pd.DataFrame({"Pris pr. pakke (DKK)": [45.0] * len(services)}, index=services)
                edited_prices_dict[land_code] = st.data_editor(enhed_df, key=f"edit_{land_code}")
            else:
                matrix_df = pd.DataFrame(45.0, index=services, columns=[f"{w}kg" for w in w_steps])
                edited_prices_dict[land_code] = st.data_editor(matrix_df, key=f"edit_{land_code}")

    # 3. DEN STORE BEREGNING
    def enrich_and_calculate(row):
        land_code = str(row.get('Land leveringsadresse', '')).upper().strip()
        old_p = row.get('Aftalepris', 0)
        weight = row.get('Vægt (kg)', 0)
        produkt = str(row.get('Produkt', ''))
        
        # Standardværdier hvis filen ikke matcher
        ny_pris = old_p
        service_navn = "Ukendt"
        bracket = get_weight_bracket(weight, PRIS_STEPS.get(land_code, PRIS_STEPS["DK"]))
        
        if land_code in edited_prices_dict:
            pris_tabel = edited_prices_dict[land_code]
            w_steps = PRIS_STEPS.get(land_code, PRIS_STEPS["DK"])
            
            # Find zone / service navn
            if "Home" in produkt or land_code not in ["DK"]:
                zone = get_zone(row, land_code)
                # Tjek om zonen findes i de indtastede priser, ellers brug den første række
                if zone in pris_tabel.index:
                    service_navn = zone
                else:
                    service_navn = pris_tabel.index[0] if not pris_tabel.empty else "Standard"
            else:
                # For DK PickUp logic
                if "PickUp" in produkt and "PickUp Parcel" in pris_tabel.index:
                    service_navn = "PickUp Parcel"
                else:
                    service_navn = pris_tabel.index[0] if not pris_tabel.empty else "Standard"
            
            # Beregn ny pris (hvis vægt og pris > 0)
            if old_p > 0 and weight > 0:
                try:
                    if "Enhedspris" in model_type:
                        base_val = pris_tabel.loc[service_navn, "Pris pr. pakke (DKK)"]
                    else:
                        prices = pris_tabel.loc[service_navn].values
                        for i, step in enumerate(w_steps):
                            if weight <= step: 
                                base_val = prices[i]
                                break
                        else:
                            base_val = prices[-1]
                    
                    # Påfør global prisjustering
                    ny_pris = base_val * (1 + adj_pct / 100)
                except:
                    ny_pris = old_p

        return pd.Series([ny_pris, service_navn, bracket])

    # Tilføj de nye data-kolonner
    master_df[['Ny_Pris', 'Beregnet_Zone', 'Vægtklasse']] = master_df.apply(enrich_and_calculate, axis=1)
    master_df['Forskel'] = master_df['Ny_Pris'] - master_df['Aftalepris']

    # 4. SAMLET NORDISK DASHBOARD
    st.divider()
    st.header(f"📊 Samlet Nordisk Resultat ({'+' if vol_adj_pct >= 0 else ''}{vol_adj_pct}% volumen)")
    
    # Skaleret data
    total_old = master_df['Aftalepris'].sum() * vol_multiplier
    total_new = master_df['Ny_Pris'].sum() * vol_multiplier
    total_diff = total_new - total_old
    total_count = len(master_df) * vol_multiplier
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Antal Pakker (Est.)", f"{int(total_count):,}")
    col2.metric("Faktureret (Tidligere)", f"{total_old:,.0f} kr.")
    col3.metric("Ny Aftale (Est.)", f"{total_new:,.0f} kr.", delta=f"{total_diff:,.0f} kr.", delta_color="inverse")
    
    with col4:
        if total_diff <= 0:
            st.success(f"BESPARELSE: {abs((total_diff/total_old)*100 if total_old else 0):.1f}%")
        else:
            st.error(f"MEROMKOSTNING: {((total_diff/total_old)*100 if total_old else 0):.1f}%")

    # 5. BREAKDOWN PR. LAND
    st.subheader("Oversigt pr. Land (Skaleret)")
    # Vi grupperer og skalerer derefter
    breakdown = master_df.groupby('Land leveringsadresse')[['Aftalepris', 'Ny_Pris']].sum() * vol_multiplier
    breakdown['Forskel'] = breakdown['Ny_Pris'] - breakdown['Aftalepris']
    breakdown['Ændring %'] = (breakdown['Forskel'] / breakdown['Aftalepris'] * 100).round(1)
    st.dataframe(breakdown.style.format("{:,.0f}"), use_container_width=True)
    
    # 6. PAKKEFORDELING (HEATMAP) - DET NYE MODUL!
    st.divider()
    st.subheader("📦 Pakkeprofil (Antal pakker pr. Zone og Vægtklasse)")
    st.markdown("Her kan du se præcis hvor kundens pakker ligger. Det gør det nemmere at målrette rabatter i forhandlingen.")
    
    # Vi laver et filter, så man kan se et land ad gangen, da de har forskellige zoner og vægtklasser
    valgt_land_oversigt = st.selectbox("Vælg land til pakkeprofil:", aktive_lande)
    
    df_land = master_df[master_df['Land leveringsadresse'] == valgt_land_oversigt]
    
    # Skab en krydstabel (Pivot) der tæller antallet af forsendelser og skalerer med volumen
    pivot_table = pd.crosstab(
        index=df_land['Beregnet_Zone'], 
        columns=df_land['Vægtklasse'], 
        margins=True, 
        margins_name="Total"
    )
    
    # Sorter kolonner numerisk (undtagen 'Total')
    cols = [c for c in pivot_table.columns if c != 'Total']
    # En simpel sorteringsnøgle der kigger på det første tal i strengen "X-Y kg"
    def weight_sort_key(s):
        if '>' in s: return 999
        try: return float(s.split('-')[0])
        except: return 0
    
    sorted_cols = sorted(cols, key=weight_sort_key) + ['Total']
    pivot_table = pivot_table[sorted_cols]
    
    # Skalering og pæn formatering
    pivot_table = (pivot_table * vol_multiplier).round(0).astype(int)
    
    st.dataframe(pivot_table.style.background_gradient(cmap='Blues', axis=None), use_container_width=True)

    # 7. EKSPORT TIL EXCEL
    st.divider()
    st.subheader("📥 Generer Rapport")
    st.markdown("Hent en komplet Excel-rapport til kunden eller internt brug.")
    
    # Sikkerheds-rensning for at undgå Excel Injection
    def sanitize_for_excel(df):
        # Vi laver en kopi for ikke at ændre i den aktive dataframe i UI'en
        clean_df = df.copy()
        for col in clean_df.select_dtypes(include=['object']):
            # Celler der starter med =, +, - eller @ kan trigge formler i Excel
            clean_df[col] = clean_df[col].apply(lambda x: f"'{x}" if str(x).startswith(('=', '+', '-', '@')) else x)
        return clean_df

    # Funktion til at skabe Excel-fil i hukommelsen
    def create_excel_report(df, breakdown_df, settings):
        output = io.BytesIO()
        # Rens data før eksport
        safe_df = sanitize_for_excel(df)
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Ark 1: Dashboard / Indstillinger
            settings_df = pd.DataFrame(list(settings.items()), columns=['Parameter', 'Værdi'])
            settings_df.to_excel(writer, sheet_name='Dashboard', index=False)
            
            # Ark 2: Oversigt pr. Land
            breakdown_df.to_excel(writer, sheet_name='Land Oversigt')
            
            # Ark 3: Detaljeret Data
            safe_df.to_excel(writer, sheet_name='Data Grundlag', index=False)
            
        return output.getvalue()

    settings_summary = {
        "Projekt": "Bring Nordic Master Analyse",
        "Dato": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "Prismodel": model_type,
        "Prisjustering (%)": adj_pct,
        "Volumen-vækst (%)": vol_adj_pct,
        "Est. Antal Pakker": int(total_count),
        "Samlet Besparelse (%)": f"{(total_diff/total_old*100):.1f}%" if total_old else "0%"
    }

    excel_data = create_excel_report(master_df, breakdown, settings_summary)
    
    st.download_button(
        label="📥 Hent komplet Excel-rapport (.xlsx)",
        data=excel_data,
        file_name=f"Bring_Nordic_Analyse_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Upload en eller flere filer for at starte (f.eks. både SE, NO og FI).")