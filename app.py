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
    
    # Rens postnummer (fjern mellemrum og sørg for tekst)
    raw_postnr = str(row.get('Modtagers postnummer', '')).replace(' ', '').strip()
    
    if country == "SE":
        prefix = raw_postnr[:2]
        maps = ZONE_MAPS.get("SE", {})
        return maps.get(prefix, maps.get("DEFAULT", "SOUTH-2"))
        
    elif country == "NO":
        # Norge: Sørg for 4 cifre (f.eks. 512 -> 0512)
        try:
            # Vi tager kun de første 4 cifre hvis der er flere (f.eks. ved fejl-data)
            clean_nr = "".join(filter(str.isdigit, raw_postnr))[:4].zfill(4)
            p_int = int(clean_nr)
            
            if p_int <= 1299: return "OSL"
            elif p_int <= 1999: return "NOR2"
            elif p_int <= 3999: return "NOR2" # Resten af NOR2 intervallet
            elif p_int <= 7999: return "NOR3"
            elif p_int <= 8999: return "NOR4"
            else: return "NORS"
        except:
            return "NOR2" # Default for Norge
            
    elif country == "FI":
        prefix = raw_postnr[:2]
        maps = ZONE_MAPS.get("FI", {})
        return maps.get(prefix, maps.get("DEFAULT", "FI01"))
        
    return f"Zone 1 ({country})"

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

# --- QUICK GUIDE ---
with st.expander("📖 Sådan bruger du værktøjet (Quick Guide)"):
    st.markdown("""
    1. **Vælg Datakilde:** Upload dine Bring-fakturaer (CSV/Excel) eller vælg 'Manuel Estimering' for at indtaste volumen manuelt.
    2. **Tjek Kolonner:** Hvis du uploader en fil, så tjek at appen har fundet de rigtige kolonner (Vægt, Pris, Postnummer).
    3. **Konfigurer Priser:** Gå til fanerne for hvert land og ret i pris-matricerne så de matcher det nye tilbud.
    4. **Juster & Forhandl:** Brug sidebar'en til at simulere generelle prisstigninger eller volumen-vækst.
    5. **Download Rapport:** Hent den færdige analyse som en professionel Excel-rapport nederst på siden.
    """)

# --- SIDEBAR ---
with st.sidebar:
    st.image("logo/bring_new_logo.png", width=200)
    st.header("1. Vælg Datakilde")
    data_source = st.radio(
        "Hvordan vil du indlæse data?",
        ["Upload Rapport (CSV/Excel)", "Manuel Estimering (Indtast volumen)"]
    )
    
    master_df = None
    
    if data_source == "Upload Rapport (CSV/Excel)":
        uploaded_files = st.file_uploader("Upload rapporter", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
    else:
        st.info("Indtast volumen (antal pakker) direkte i fanerne under punkt 3.")
        valgte_lande = st.multiselect("Vælg lande til estimering:", ["DK", "SE", "NO", "FI"], default=["DK"])
        uploaded_files = None
    
    st.divider()
    model_type = st.radio(
        "2. Vælg Prismodel",
        ["Enhedspris (Fast pris)", "Vægtbaseret pris (Matrix)"],
        index=1
    )
    
    st.divider()
    st.header("📈 Forhandling & Justering")
    
    adj_type = st.radio("Justeringstype", ["Procent (%)", "Fast beløb (kr.)"], horizontal=True)
    
    if adj_type == "Procent (%)":
        adj_val = st.slider(
            "Generel prisjustering (%)",
            min_value=-20.0,
            max_value=40.0,
            value=0.0,
            step=0.5,
            help="Simuler en prisstigning eller nedsættelse på tværs af alle priser."
        )
    else:
        adj_val = st.number_input(
            "Fast beløb pr. pakke (kr.)",
            min_value=-50.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
            help="Læg et fast beløb til eller træk det fra alle priser."
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
if uploaded_files or (data_source == "Manuel Estimering (Indtast volumen)" and valgte_lande):
    if data_source == "Upload Rapport (CSV/Excel)":
        with st.spinner("Indlæser og renser data..."):
            # 1. Saml alle uploadede filer
            dfs = []
            # Sikkerhedstjek for at undgå linter-fejl (None type not iterable)
            files_to_process = uploaded_files if uploaded_files is not None else []
            for f in files_to_process:
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
            master_df['Mængde'] = 1 # Hver række i filen er 1 pakke

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
            master_df['Land leveringsadresse'] = master_df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().str.upper()
            
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
            
            # --- PRÆ-BEREGNING (OPTIMERING: Kører kun én gang pr. upload) ---
            # Vi bruger et hash af filnavnene til at se om vi skal genberegne
            file_hash = "-".join([f.name for f in files_to_process])
            if 'current_file_hash' not in st.session_state or st.session_state['current_file_hash'] != file_hash:
                with st.spinner("Præ-beregner zoner og vægtklasser for hurtig redigering..."):
                    def get_weight_index(row, country_steps):
                        w = row.get('Vægt (kg)', 0)
                        if w == 0: return -1
                        for idx, step in enumerate(country_steps):
                            if w <= step: return idx
                        return len(country_steps) - 1

                    master_df['_Zone'] = master_df.apply(lambda r: get_zone(r, r['Land leveringsadresse']), axis=1)
                    
                    def map_w_idx(row):
                        steps = PRIS_STEPS.get(row['Land leveringsadresse'], PRIS_STEPS["DK"])
                        return get_weight_index(row, steps)
                    
                    master_df['_W_Idx'] = master_df.apply(map_w_idx, axis=1)
                    master_df['Vægtklasse'] = master_df.apply(lambda r: get_weight_bracket(r['Vægt (kg)'], PRIS_STEPS.get(r['Land leveringsadresse'], PRIS_STEPS["DK"])), axis=1)
                    
                    # Gem i session state så vi ikke gør det igen
                    st.session_state['master_df_precalc'] = master_df.copy()
                    st.session_state['current_file_hash'] = file_hash
            else:
                # Hent fra session state hvis filen er den samme
                master_df = st.session_state['master_df_precalc']
    else:
        # Manuel mode
        aktive_lande = valgte_lande
        master_df = pd.DataFrame(columns=['Land leveringsadresse', 'Vægt (kg)', 'Aftalepris', 'Modtagers postnummer', 'Produkt', 'Mængde'])

    if not aktive_lande:
        st.warning("Ingen gyldige lande fundet.")
        st.stop()
        
    st.success(f"Fandt data for følgende lande: {', '.join(aktive_lande)}")
    
    # 2. DYNAMISKE FANER TIL PRIS-EDITERING OG MANUEL VOLUMEN
    st.subheader("3. Konfigurer priser og volumen pr. land")
    tabs = st.tabs(aktive_lande)
    
    edited_prices_dict = {}
    manual_volume_data = [] # Bruges kun hvis data_source er manuel
    
    for i, land in enumerate(aktive_lande):
        with tabs[i]:
            land_code = land.upper().strip()
            w_steps = PRIS_STEPS.get(land_code, PRIS_STEPS["DK"])
            
            if land_code == "SE": 
                services = ["0342 PickUp Parcel Bulk", "CITY-1", "CITY-2", "SOUTH-2"]
            elif land_code == "NO": 
                services = ["0342 PickUp Parcel Bulk", "OSL", "NOR2", "NOR3", "NOR4", "NORS"]
            elif land_code == "FI": 
                services = ["0342 PickUp Parcel Bulk", "FI00", "FI01", "FI02", "FI04"]
            else: 
                services = ["PickUp Parcel", "Home Delivery", "Business Parcel"]
            
            # --- PRIS EDITOR ---
            st.markdown(f"**Priser for {land_code}**")
            
            # Init session state til matricen (afhængig af land og model-type)
            matrix_key = f"m_data_{land_code}_{model_type}"
            if matrix_key not in st.session_state:
                if "Enhedspris" in model_type:
                    st.session_state[matrix_key] = pd.DataFrame({"Pris pr. pakke (DKK)": [45.0] * len(services)}, index=services)
                else:
                    st.session_state[matrix_key] = pd.DataFrame(45.0, index=services, columns=[f"{w}kg" for w in w_steps])

            # Upload/Download knapper i en lille kolonne-layout
            up_col, dl_col = st.columns([1, 1])
            with up_col:
                uploaded_m = st.file_uploader(f"Importér {land_code} CSV", type="csv", key=f"up_{land_code}")
                if uploaded_m:
                    try:
                        st.session_state[matrix_key] = pd.read_csv(uploaded_m, index_col=0)
                        st.toast(f"✅ Matrix for {land_code} indlæst!")
                    except Exception as e:
                        st.error(f"Fejl: {e}")
            
            # Edit Matrix
            edited_prices_dict[land_code] = st.data_editor(st.session_state[matrix_key], key=f"edit_p_{land_code}", use_container_width=True)
            
            with dl_col:
                csv_m = edited_prices_dict[land_code].to_csv().encode('utf-8')
                st.download_button(
                    label=f"📥 Eksportér {land_code} CSV",
                    data=csv_m,
                    file_name=f"Bring_Matrix_{land_code}.csv",
                    mime="text/csv",
                    key=f"dl_{land_code}"
                )

            # --- VOLUMEN EDITOR (Kun i manuel mode) ---
            if data_source == "Manuel Estimering (Indtast volumen)":
                st.divider()
                st.markdown(f"**📦 Indtast antal pakker pr. vægtklasse for {land_code}**")
                vol_matrix = pd.DataFrame(0, index=services, columns=[f"{w}kg" for w in w_steps])
                edited_vol = st.data_editor(vol_matrix, key=f"edit_v_{land_code}")
                
                # Konverter den udfyldte matrix til rækker i master_df format
                for service in services:
                    for j, w_col in enumerate(vol_matrix.columns):
                        # Brug pd.to_numeric for at sikre at linteren er glad
                        val = edited_vol.loc[service, w_col]
                        try:
                            mængde = float(pd.to_numeric(val, errors='coerce'))
                        except:
                            mængde = 0.0
                            
                        if mængde > 0:
                            weight_val = w_steps[j]
                            manual_volume_data.append({
                                'Land leveringsadresse': land_code,
                                'Vægt (kg)': weight_val,
                                'Aftalepris': 0.0,
                                'Modtagers postnummer': '0000',
                                'Produkt': service,
                                'Mængde': mængde,
                                '_Zone': service, # I manuel mode er servicen selve zonen
                                '_W_Idx': j,      # Vi kender indekset direkte fra kolonnen
                                'Vægtklasse': w_col
                            })

    # Hvis vi er i manuel mode, skal vi bygge master_df nu
    if data_source == "Manuel Estimering (Indtast volumen)":
        if manual_volume_data:
            master_df = pd.DataFrame(manual_volume_data)
        else:
            st.warning("Indtast venligst nogle pakkemængder i fanerne ovenfor for at se beregningen.")
            st.stop()

    # 3. DEN STORE BEREGNING (OPTIMERET & VEKTORISERET)
    def calculate_results(df, prices_dict):
        if df is None: return None
        
        with st.spinner("Beregner nye priser... En krone her, en krone der..."):
            # Vi bruger de præ-beregnede zoner og indekser
            def get_price(row):
                land_code = row['Land leveringsadresse']
                old_p = row['Aftalepris']
                w_idx = int(row['_W_Idx'])
                zone = row['_Zone']
                produkt = row['Produkt']
                
                # 0-kilos reglen (Gemmes som de er)
                if row['Vægt (kg)'] == 0 or old_p == 0:
                    return old_p

                if land_code in prices_dict:
                    pris_tabel = prices_dict[land_code]
                    if pris_tabel is None: return old_p
                    
                    # Find den rigtige række i tabellen
                    if zone in pris_tabel.index:
                        service_navn = zone
                    elif "PickUp" in produkt and "0342 PickUp Parcel Bulk" in pris_tabel.index:
                        service_navn = "0342 PickUp Parcel Bulk"
                    elif "PickUp" in produkt and "PickUp Parcel" in pris_tabel.index:
                        service_navn = "PickUp Parcel"
                    else:
                        service_navn = pris_tabel.index[0] if not pris_tabel.empty else "Standard"
                    
                    try:
                        if "Enhedspris" in model_type:
                            col = pris_tabel.columns[0]
                            base_val = float(pris_tabel.loc[service_navn, col])
                        else:
                            # Præ-beregnet w_idx bruges her
                            base_val = float(pris_tabel.loc[service_navn].iloc[w_idx])
                        
                        # Justering (Procent eller Fast beløb)
                        if adj_type == "Procent (%)":
                            return base_val * (1 + adj_val / 100)
                        else:
                            return base_val + adj_val
                    except:
                        return old_p
                return old_p

            # Kør beregning på hele df
            df['Ny_Pris'] = df.apply(get_price, axis=1)
            # Beregnet Zone bruges kun til visning i heatmap
            df['Beregnet_Zone'] = df['_Zone']
            return df

    # UI LOGIK: For store filer skal man trykke på en knap for at undgå lag
    dataset_size = len(master_df) if master_df is not None else 0
    is_large_file = dataset_size > 500
    
    if is_large_file:
        st.info(f"📊 Datasæt på {dataset_size:,} pakker. Tryk på knappen for at opdatere beregningen efter du har rettet priserne.")
        if st.button("🔥 Opdater Beregning & Dashboards", use_container_width=True, type="primary"):
            master_df = calculate_results(master_df, edited_prices_dict)
            if master_df is not None:
                st.session_state['last_calc'] = master_df.copy()
        
        # Hent sidste resultat fra session state hvis det findes
        if 'last_calc' in st.session_state:
            master_df = st.session_state['last_calc']
        elif master_df is not None:
            # Første gang viser vi bare grundlaget uden beregning
            master_df['Ny_Pris'] = master_df['Aftalepris']
            master_df['Beregnet_Zone'] = master_df['_Zone']
    else:
        # For små filer kører vi live-update
        master_df = calculate_results(master_df, edited_prices_dict)

    if master_df is None:
        st.error("Kunne ikke generere data. Prøv at uploade igen.")
        st.stop()

    # 4. SAMLET NORDISK DASHBOARD (Vægtet Sum)
    st.divider()
    # Tjek om vi rent faktisk har lavet en beregning endnu
    has_calc = 'Ny_Pris' in master_df.columns and (master_df['Ny_Pris'] != master_df['Aftalepris']).any()
    
    st.header(f"📊 Samlet Nordisk Resultat ({'+' if vol_adj_pct >= 0 else ''}{vol_adj_pct}% volumen)")
    
    # Vægtet beregning (Pris * Mængde)
    # Vi bruger pd.to_numeric for at sikre at linteren ikke klager over "complex" typer i unionen
    total_old = float(pd.to_numeric((master_df['Aftalepris'] * master_df['Mængde']).sum() * vol_multiplier))
    total_new = float(pd.to_numeric((master_df['Ny_Pris'] * master_df['Mængde']).sum() * vol_multiplier))
    total_diff = total_new - total_old
    total_count = float(pd.to_numeric(master_df['Mængde'].sum() * vol_multiplier))
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Antal Pakker (Est.)", f"{int(total_count):,}")
    col2.metric("Nuværende Omsætning", f"{total_old:,.0f} kr." if total_old > 0 else "N/A")
    col3.metric("Ny Aftale (Est.)", f"{total_new:,.0f} kr.", delta=f"{total_diff:,.0f} kr." if total_old > 0 and has_calc else None, delta_color="inverse")
    
    with col4:
        if total_old > 0 and has_calc:
            if total_diff <= 0:
                st.success(f"BESPARELSE: {abs((total_diff/total_old)*100):.1f}%")
            else:
                st.error(f"MEROMKOSTNING: {(total_diff/total_old*100):.1f}%")
        elif not has_calc and is_large_file:
            st.warning("Tryk på 'Opdater Beregning' for analyse.")
        else:
            st.info("Ingen historisk sammenligning.")

    # 5. BREAKDOWN PR. LAND
    st.subheader("Oversigt pr. Land (Skaleret)")
    master_df['Weighted_Old'] = master_df['Aftalepris'] * master_df['Mængde'] * vol_multiplier
    master_df['Weighted_New'] = master_df['Ny_Pris'] * master_df['Mængde'] * vol_multiplier
    
    breakdown = master_df.groupby('Land leveringsadresse').agg({
        'Weighted_Old': 'sum',
        'Weighted_New': 'sum'
    }).rename(columns={'Weighted_Old': 'Nuværende', 'Weighted_New': 'Ny Pris'})
    breakdown['Forskel'] = breakdown['Ny Pris'] - breakdown['Nuværende']
    st.dataframe(breakdown.style.format("{:,.0f}"), use_container_width=True)
    
    # 6. PAKKEFORDELING (HEATMAP)
    st.divider()
    st.subheader("📦 Pakkeprofil (Antal pakker pr. Zone og Vægtklasse)")
    valgt_land_oversigt = st.selectbox("Vælg land til pakkeprofil:", aktive_lande)
    df_land = master_df[master_df['Land leveringsadresse'] == valgt_land_oversigt]
    
    pivot_table = pd.pivot_table(
        df_land, 
        values='Mængde', 
        index='Beregnet_Zone', 
        columns='Vægtklasse', 
        aggfunc='sum', 
        fill_value=0,
        margins=True, 
        margins_name="Total"
    )
    
    cols = [c for c in pivot_table.columns if c != 'Total']
    def weight_sort_key(s):
        if '>' in s: return 999
        try: return float(s.split('-')[0])
        except: return 0
    sorted_cols = sorted(cols, key=weight_sort_key) + ['Total']
    pivot_table = pivot_table[sorted_cols]
    
    pivot_table = (pivot_table * vol_multiplier).round(0).astype(int)
    st.dataframe(pivot_table.style.background_gradient(cmap='Blues', axis=None), use_container_width=True)


    # 7. EKSPORT TIL EXCEL
    st.divider()
    st.subheader("📥 Generer Rapport")
    
    def sanitize_for_excel(df):
        clean_df = df.copy()
        for col in clean_df.select_dtypes(include=['object']):
            clean_df[col] = clean_df[col].apply(lambda x: f"'{x}" if str(x).startswith(('=', '+', '-', '@')) else x)
        return clean_df

    def create_excel_report(df, breakdown_df, settings):
        output = io.BytesIO()
        safe_df = sanitize_for_excel(df)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            settings_df = pd.DataFrame(list(settings.items()), columns=['Parameter', 'Værdi'])
            settings_df.to_excel(writer, sheet_name='Dashboard', index=False)
            breakdown_df.to_excel(writer, sheet_name='Land Oversigt')
            safe_df.to_excel(writer, sheet_name='Data Grundlag', index=False)
        return output.getvalue()

    settings_summary = {
        "Projekt": "Bring Nordic Master Analyse",
        "Kilde": data_source,
        "Dato": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "Prismodel": model_type,
        f"Justering ({adj_type})": adj_val,
        "Volumen-vækst (%)": vol_adj_pct,
        "Est. Antal Pakker": int(total_count),
        "Samlet Ny Omsætning": int(total_new)
    }
    if total_old > 0:
        settings_summary["Samlet Besparelse (%)"] = f"{(total_diff/total_old*100):.1f}%"

    excel_data = create_excel_report(master_df, breakdown, settings_summary)
    
    st.download_button(
        label="📥 Hent komplet Excel-rapport (.xlsx)",
        data=excel_data,
        file_name=f"Bring_Analyse_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.info("👈 Upload en eller flere filer for at starte (f.eks. både SE, NO og FI).")