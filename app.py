import streamlit as st
import pandas as pd

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

st.set_page_config(page_title="Bring Nordic Master", layout="wide", page_icon="🌍")

st.title("🌍 Bring Nordic Master-Beregner")
st.markdown("Upload én stor nordisk fil, eller flere filer (én pr. land). Værktøjet samler det hele automatisk.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Upload Data")
    uploaded_files = st.file_uploader("Upload CSV-rapporter", type="csv", accept_multiple_files=True)
    
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
        temp_df = pd.read_csv(f)
        # Rens kolonnenavne (fjern mellemrum)
        temp_df.columns = [c.strip() for c in temp_df.columns]
        dfs.append(temp_df)
    
    master_df = pd.concat(dfs, ignore_index=True)
    
    # --- DATA RENSNING ---
    with st.expander("🛠️ Se data-rensning (håndtering af tomme celler)"):
        missing_report = master_df.isna().sum()
        st.write("Fundne tomme celler pr. kolonne:", missing_report[missing_report > 0])
        
        # Fyld standardværdier
        master_df['Land leveringsadresse'] = master_df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().upper()
        master_df['Vægt (kg)'] = pd.to_numeric(master_df['Vægt (kg)'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        master_df['Aftalepris'] = pd.to_numeric(master_df['Aftalepris'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        master_df['Modtagers postnummer'] = master_df['Modtagers postnummer'].fillna('0000').astype(str).str.strip()
        master_df['Produkt'] = master_df['Produkt'].fillna('Ukendt').astype(str).str.strip()
        
        st.success("Data er renset og klar til analyse.")

    if 'Land leveringsadresse' in master_df.columns:
        aktive_lande = master_df['Land leveringsadresse'].unique().tolist()
        # Fjern 'UKENDT' fra aktive lande hvis vi ikke vil konfigurere priser for det
        if 'UKENDT' in aktive_lande: aktive_lande.remove('UKENDT')
    else:
        st.error("Kunne ikke finde kolonnen 'Land leveringsadresse'. Tjek formatet.")
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
                service_navn = zone if zone in pris_tabel.index else pris_tabel.index[0]
            else:
                service_navn = "PickUp Parcel" if "PickUp" in produkt else pris_tabel.index[0]
            
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
    
    # Skalering og pæn formatering
    pivot_table = (pivot_table * vol_multiplier).round(0).astype(int)
    
    st.dataframe(pivot_table.style.background_gradient(cmap='Blues', axis=None), use_container_width=True)

    # 7. DOWNLOAD
    st.divider()
    st.download_button("📥 Hent samlet Excel-rapport for Norden", master_df.to_csv(index=False), "Bring_Nordic_Total.csv", "text/csv")

else:
    st.info("👈 Upload en eller flere filer for at starte (f.eks. både SE, NO og FI).")