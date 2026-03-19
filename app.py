import streamlit as st
import pandas as pd
import numpy as np
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
    1. **Vælg Datakilde:** Hent Foreløbelig fragtberegning fra MyBring og upload den eller brug Manuel estimering.
    2. **Tjek Kolonner:** Hvis du uploader en fil, så tjek at appen har fundet de rigtige kolonner (Vægt, Pris, Postnummer).
    3. **Konfigurer Priser:** Gå til fanerne for hvert land og ret i pris-matricerne. 
       *   **TIP:** Du kan **Copy-Paste** direkte fra Excel ind i skemaerne herunder!
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

            # --- DATA RENSNING & OPTIMERING ---
            master_df['Land leveringsadresse'] = master_df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().str.upper()
            
            # Hurtig numerisk konvertering
            for col in ['Vægt (kg)', 'Aftalepris']:
                if col in master_df.columns:
                    master_df[col] = pd.to_numeric(master_df[col].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0.0)

            master_df['Modtagers postnummer'] = master_df['Modtagers postnummer'].fillna('0000').astype(str).str.strip()
            master_df['Produkt'] = master_df['Produkt'].fillna('Ukendt').astype(str).str.strip()

            aktive_lande = sorted([l for l in master_df['Land leveringsadresse'].unique().tolist() if l != 'UKENDT' and l != '0.0'])
            
            # --- PRÆ-BEREGNING (VEKTORISERET OPTIMERING) ---
            file_hash = "-".join([f.name for f in files_to_process])
            if 'master_df_precalc' not in st.session_state or st.session_state.get('current_file_hash') != file_hash:
                with st.spinner("Præ-beregner zoner og vægtklasser (Vektoriseret)..."):
                    # 1. Zone mapping (Vektoriseret hvor muligt)
                    # For simpelhed beholder vi get_zone til de komplekse regler, men kører den kun én gang
                    master_df['_Zone'] = master_df.apply(lambda r: get_zone(r, r['Land leveringsadresse']), axis=1)
                    
                    # 2. Vægt-indeks (Vektoriseret opslag)
                    master_df['_W_Idx'] = 0
                    master_df['Vægtklasse'] = "0 kg (Gebyr/Info)"
                    
                    for land_code in aktive_lande:
                        mask = master_df['Land leveringsadresse'] == land_code
                        if not mask.any(): continue
                        
                        steps = PRIS_STEPS.get(land_code, PRIS_STEPS["DK"])
                        weights = master_df.loc[mask, 'Vægt (kg)']
                        
                        # Find indeks lynhurtigt via searchsorted
                        indices = np.searchsorted(steps, weights, side='left')
                        # Cap ved max indeks
                        indices = np.clip(indices, 0, len(steps) - 1)
                        # Sæt indeks til -1 for 0 kg
                        indices = np.where(weights == 0, -1, indices)
                        
                        master_df.loc[mask, '_W_Idx'] = indices
                        
                        # Generer vægtklasse navne (også hurtigere)
                        def bulk_bracket(w, s_list):
                            if w == 0: return "0 kg (Gebyr/Info)"
                            prev = 0
                            for s in s_list:
                                if w <= s: return f"{prev}-{s} kg"
                                prev = s
                            return f">{s_list[-1]} kg"
                        
                        master_df.loc[mask, 'Vægtklasse'] = weights.apply(lambda w: bulk_bracket(w, steps))
                    
                    st.session_state['master_df_precalc'] = master_df.copy()
                    st.session_state['current_file_hash'] = file_hash
                    
                    # --- NYT: GENERER START-MATRICER BASERET PÅ HISTORIK ---
                    for l_code in aktive_lande:
                        l_df = master_df[master_df['Land leveringsadresse'] == l_code]
                        # Vi kigger kun på fragt-linjer (pris > 0)
                        l_df_prices = l_df[l_df['Aftalepris'] > 0]
                        
                        w_steps = PRIS_STEPS.get(l_code, PRIS_STEPS["DK"])
                        # Definer services baseret på land (samme logik som i tabs)
                        if l_code == "SE": s_list = ["0342 PickUp Parcel Bulk", "CITY-1", "CITY-2", "SOUTH-2"]
                        elif l_code == "NO": s_list = ["0342 PickUp Parcel Bulk", "OSL", "NOR2", "NOR3", "NOR4", "NORS"]
                        elif l_code == "FI": s_list = ["0342 PickUp Parcel Bulk", "FI00", "FI01", "FI02", "FI04"]
                        else: s_list = ["PickUp Parcel", "Home Delivery", "Business Parcel"]
                        
                        # Lav tom matrix
                        m_template = pd.DataFrame(0.0, index=s_list, columns=[f"{w}kg" for w in w_steps])
                        
                        # Beregn gennemsnit pr. zone og vægt-indeks
                        if not l_df_prices.empty:
                            avg_map = l_df_prices.groupby(['_Zone', '_W_Idx'])['Aftalepris'].mean().to_dict()
                            
                            for s in s_list:
                                for idx, w_col in enumerate(m_template.columns):
                                    # Find gennemsnit for denne specifikke celle
                                    val = avg_map.get((s, idx))
                                    if val is None:
                                        # Fallback 1: Gennemsnit for hele zonen
                                        val = l_df_prices[l_df_prices['_Zone'] == s]['Aftalepris'].mean()
                                    if pd.isna(val) or val == 0:
                                        # Fallback 2: Gennemsnit for hele landet
                                        val = l_df_prices['Aftalepris'].mean()
                                    if pd.isna(val) or val == 0:
                                        val = 45.0 # Absolut fallback
                                        
                                    m_template.loc[s, w_col] = round(float(val), 2)
                        else:
                            m_template.fill(45.0)

                        # Gem den intelligente start-matrix i session state (overskriv eksisterende ved nyt upload)
                        st.session_state[f"m_data_{l_code}_Vægtbaseret pris (Matrix)"] = m_template
                        
                        # Enhedspris fallback
                        st.session_state[f"m_data_{l_code}_Enhedspris (Fast pris)"] = pd.DataFrame(
                            {"Pris pr. pakke (DKK)": [round(l_df_prices['Aftalepris'].mean(), 2) if not l_df_prices.empty else 45.0] * len(s_list)}, 
                            index=s_list
                        )
            else:
                master_df = st.session_state['master_df_precalc']

            with st.expander("🛠️ Se detaljer om data-rensning"):
                st.write("Kolonne-mapping anvendt:", mapping)
                st.success("Data er præ-beregnet og klar.")
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
                # Kun fallback her (primært til Manuel Mode)
                if "Enhedspris" in model_type:
                    df_init = pd.DataFrame({"Pris pr. pakke (DKK)": ["45,00"] * len(services)}, index=services)
                else:
                    df_init = pd.DataFrame("45,00", index=services, columns=[f"{w}kg" for w in w_steps])
                st.session_state[matrix_key] = df_init.astype(str) # Tving som tekst for komma-support

            # Upload/Download knapper i en lille kolonne-layout
            up_col, dl_col = st.columns([1, 1])
            with up_col:
                uploaded_m = st.file_uploader(f"Importér {land_code} (Excel)", type=["xlsx", "xls"], key=f"up_{land_code}")
                if uploaded_m:
                    try:
                        loaded_df = pd.read_excel(uploaded_m, index_col=0)
                        # Konverter alle værdier til tekst med komma for ensartethed på en sikker måde
                        st.session_state[matrix_key] = loaded_df.map(lambda x: str(x).replace('.', ','))
                        st.toast(f"✅ Matrix for {land_code} indlæst!")
                    except Exception as e:
                        st.error(f"Fejl: {e}")
            
            # Edit Matrix (Nu som tekst for at tillade kommaer)
            edited_prices_dict[land_code] = st.data_editor(
                st.session_state[matrix_key], 
                key=f"edit_p_{land_code}", 
                use_container_width=True
            )
            
            with dl_col:
                # Excel export
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    edited_prices_dict[land_code].to_excel(writer, index=True)
                
                st.download_button(
                    label=f"📥 Eksportér {land_code} (Excel)",
                    data=buffer.getvalue(),
                    file_name=f"Bring_Matrix_{land_code}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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

    # 3. DEN STORE BEREGNING (EKSTREMT HURTIG & FULDT VEKTORISERET)
    def calculate_results(df, prices_dict):
        if df is None: return None
        
        with st.spinner("Beregner nye priser (Vektoriseret)..."):
            # Konverter priser fra tekst (med komma) til float (med punktum)
            numeric_prices_dict = {}
            for k, p_df in prices_dict.items():
                # Brug .map() på hver kolonne for at være sikker (virker på både Series og DF)
                numeric_prices_dict[k] = p_df.copy()
                for col in numeric_prices_dict[k].columns:
                    numeric_prices_dict[k][col] = numeric_prices_dict[k][col].apply(
                        lambda x: float(str(x).replace(',', '.').strip() or 0) if isinstance(x, (str, float, int)) else 0.0
                    )

            # Kopier for at undgå mutations-problemer
            df = df.copy()
            df['Ny_Pris'] = df['Aftalepris'].copy()
            df['Beregnet_Zone'] = df['_Zone'].copy()
            
            # Vi beregner land for land for at udnytte vektorisering
            for land in numeric_prices_dict.keys():
                mask = df['Land leveringsadresse'] == land
                if not mask.any(): continue
                
                pris_tabel = numeric_prices_dict[land]
                if pris_tabel is None: continue
                
                # Præ-konverter matrix til en flad dictionary for hurtigt opslag
                # Dette er meget hurtigere end .loc inde i en loop
                price_matrix = pris_tabel.values
                services_list = pris_tabel.index.tolist()
                
                # Vi finder servicen for alle rækker i dette land én gang
                land_subset = df[mask].copy()
                
                # 1. Præ-beregn zone/service mapping (meget hurtigere end vectorize)
                # Vi skaber en mapping serie fra Produkterne
                service_map = {}
                for s in services_list:
                    service_map[s] = services_list.index(s)
                
                # Default mapping
                def fast_service_map(p, z):
                    if z in service_map: return service_map[z]
                    p_str = str(p)
                    if "PickUp" in p_str:
                        if "0342 PickUp Parcel Bulk" in service_map: return service_map["0342 PickUp Parcel Bulk"]
                        if "PickUp Parcel" in service_map: return service_map["PickUp Parcel"]
                    return 0

                # Hurtig række-baseret mapping (kun for dette lands subset)
                s_indices = np.array([fast_service_map(p, z) for p, z in zip(land_subset['Produkt'], land_subset['_Zone'])])
                w_indices = land_subset['_W_Idx'].values.astype(int)
                
                # Kun beregn for pakker med vægt > 0
                valid_mask = (land_subset['Vægt (kg)'].values > 0) & (land_subset['Aftalepris'].values > 0)
                
                if valid_mask.any():
                    # Træk priserne direkte fra den rå numpy matrix (Lynhurtigt!)
                    row_idx = s_indices[valid_mask]
                    col_idx = w_indices[valid_mask]
                    
                    if "Enhedspris" in model_type:
                        col_idx = 0 
                    
                    # Hent priserne fra matrix via advanced indexing
                    bases = price_matrix[row_idx, col_idx]
                    
                    # Anvend justeringer
                    if adj_type == "Procent (%)":
                        new_vals = bases * (1 + adj_val / 100)
                    else:
                        new_vals = bases + adj_val
                    
                    # Skriv tilbage
                    final_prices = land_subset['Aftalepris'].values.copy()
                    final_prices[valid_mask] = new_vals
                    df.loc[mask, 'Ny_Pris'] = final_prices
            
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
                st.rerun() # Tving UI til at genindlæse med de nye tal
        
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
    
    # Sikr numerisk subtraktion
    breakdown['Nuværende'] = pd.to_numeric(breakdown['Nuværende'], errors='coerce').fillna(0.0)
    breakdown['Ny Pris'] = pd.to_numeric(breakdown['Ny Pris'], errors='coerce').fillna(0.0)
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

    # 6b. IMPACT HEATMAP (Hvor flytter pengene sig?)
    st.markdown(f"**💰 Pris-Impact (Gns. forskel i kr. pr. pakke for {valgt_land_oversigt})**")
    st.caption("Grøn = Besparelse for kunden, Rød = Meromkostning for kunden")
    
    # Beregn gennemsnitlig forskel pr. celle
    # Vi sikrer os at værdierne er numeriske før subtraktion
    df_land_numeric = df_land.copy()
    df_land_numeric['Ny_Pris'] = pd.to_numeric(df_land_numeric['Ny_Pris'], errors='coerce').fillna(0.0)
    df_land_numeric['Aftalepris'] = pd.to_numeric(df_land_numeric['Aftalepris'], errors='coerce').fillna(0.0)
    
    # Beregn forskellen først (meget mere robust)
    df_land_numeric['Price_Diff'] = df_land_numeric['Ny_Pris'] - df_land_numeric['Aftalepris']
    
    impact_pivot = pd.pivot_table(
        df_land_numeric,
        values='Price_Diff',
        index='Beregnet_Zone',
        columns='Vægtklasse',
        aggfunc='mean',
        fill_value=0
    )
    
    # Sorter kolonnerne efter vægt igen
    impact_pivot = impact_pivot[sorted_cols[:-1]] # Fjern 'Total' fra impact
    
    # Styling: Rød for positive tal (dyrere), Grøn for negative (billigere)
    # Vi bruger en 'RdYlGn' (Red-Yellow-Green) skala, men omvendt (reversed '_r') 
    # så Grøn er negativ (besparelse) og Rød er positiv (stigning)
    st.dataframe(
        impact_pivot.style.background_gradient(cmap='RdYlGn_r', axis=None)
        .format("{:+.1f} kr"), 
        use_container_width=True
    )


    # 7. EKSPORT TIL EXCEL
    st.divider()
    st.subheader("📥 Generer Rapport")
    
    def sanitize_for_excel(df):
        clean_df = df.copy()
        # Kun tjek objekt-kolonner (tekst)
        for col in clean_df.select_dtypes(include=['object']):
            # Vektoriseret sanitering (meget hurtigere end .apply)
            mask = clean_df[col].astype(str).str.startswith(('=', '+', '-', '@'), na=False)
            if mask.any():
                clean_df.loc[mask, col] = "'" + clean_df.loc[mask, col].astype(str)
        return clean_df

    def create_excel_report(df, breakdown_df, settings):
        output = io.BytesIO()
        
        # Forbered data til eksport (Omdøbning og beregning af linje-forskel)
        export_df = df.copy()
        
        # Sikr numeriske typer før beregning
        export_df['Ny_Pris'] = pd.to_numeric(export_df['Ny_Pris'], errors='coerce').fillna(0.0)
        export_df['Aftalepris'] = pd.to_numeric(export_df['Aftalepris'], errors='coerce').fillna(0.0)
        export_df['Forskel (kr.)'] = export_df['Ny_Pris'] - export_df['Aftalepris']
        
        # Vælg og omdøb kolonner
        rename_map = {
            'Aftalepris': 'Førpris (Nuværende)',
            'Ny_Pris': 'Ny Pris (Efter)',
            'Beregnet_Zone': 'Zone',
            'Land leveringsadresse': 'Land'
        }
        export_df = export_df.rename(columns=rename_map)
        
        export_cols = [
            'Land', 'Produkt', 'Modtagers postnummer', 'Zone',
            'Vægt (kg)', 'Førpris (Nuværende)', 'Ny Pris (Efter)', 'Forskel (kr.)', 'Vægtklasse', 'Mængde'
        ]
        
        # Behold originale kolonner hvis de findes og ikke er i listen (undgå interne _ kolonner)
        for col in export_df.columns:
            if col not in export_cols and not col.startswith('_') and col not in rename_map.values():
                export_cols.append(col)
        
        # Filtrer og saniter
        final_export_df = sanitize_for_excel(export_df[export_cols])
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            settings_df = pd.DataFrame(list(settings.items()), columns=['Parameter', 'Værdi'])
            settings_df.to_excel(writer, sheet_name='Dashboard', index=False)
            breakdown_df.to_excel(writer, sheet_name='Land Oversigt')
            final_export_df.to_excel(writer, sheet_name='Data Grundlag', index=False)
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
        settings_summary["Forskel (%)"] = f"{(total_diff/total_old*100):.1f}%"

    # UI til rapportgenerering
    if is_large_file:
        st.warning("⚠️ Da du har et meget stort datasæt, skal rapporten forberedes manuelt.")
        if st.button("🚀 Forbered Excel Rapport (kan tage 30-60 sek.)"):
            with st.spinner("Genererer komplet Excel-fil..."):
                excel_data = create_excel_report(master_df, breakdown, settings_summary)
                st.session_state['report_data'] = excel_data
                st.success("✅ Rapport er klar!")

        if 'report_data' in st.session_state:
            st.download_button(
                label="📥 Hent Forberedt Excel-rapport (.xlsx)",
                data=st.session_state['report_data'],
                file_name=f"Bring_Analyse_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        # For små filer genererer vi den stadig automatisk for bekvemmelighed
        excel_data = create_excel_report(master_df, breakdown, settings_summary)
        st.download_button(
            label="📥 Hent Excel-rapport (.xlsx)",
            data=excel_data,
            file_name=f"Bring_Analyse_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("👈 Upload en eller flere filer for at starte (f.eks. både SE, NO og FI).")