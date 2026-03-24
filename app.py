import streamlit as st
import pandas as pd
import numpy as np
import io
import zones
import calculator
from typing import List, Any, Dict, Optional, cast

st.set_page_config(page_title="Bring Nordic Master", layout="wide", page_icon="logo/favicon.ico")

# --- LOGO & TITEL ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try:
        st.image("logo/bring_new_logo.png", width=150)
    except:
        st.write("🚛 **Bring Nordic Master**")

with col_title:
    st.title("🌍 Bring Nordic Master-Beregner")
    st.markdown("*Det ultimative salgsværktøj til nordiske fragtsimuleringer.*")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Vælg Datakilde")
    data_source = st.radio(
        "Hvordan vil du indlæse data?",
        ["Upload Rapport (CSV/Excel)", "Manuel Estimering (Indtast volumen)"]
    )
    
    master_df: Optional[pd.DataFrame] = None
    uploaded_files_raw: List[Any] = []
    aktive_lande: List[str] = []
    
    if data_source == "Upload Rapport (CSV/Excel)":
        files = st.file_uploader("Upload rapporter", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
        if files:
            uploaded_files_raw = list(files)
    else:
        st.info("Indtast volumen (antal pakker) direkte i fanerne under punkt 3.")
        valgte_lande = st.multiselect("Vælg lande til estimering:", ["DK", "SE", "NO", "FI"], default=["DK"])
        if valgte_lande:
            aktive_lande = [str(l) for l in valgte_lande]
    
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
        adj_val = float(st.slider("Generel prisjustering (%)", -20.0, 40.0, 0.0, 0.5))
    else:
        adj_val = float(st.number_input("Fast beløb pr. pakke (kr.)", -50.0, 100.0, 0.0, 1.0))

    vol_adj_pct = float(st.slider("Forventet volumen-vækst (%)", -50.0, 200.0, 0.0, 5.0))
    vol_multiplier = float(1.0 + (vol_adj_pct / 100.0))

# --- DATA INDLÆSNING ---
@st.cache_data
def load_and_preprocess_data(files_list: List[Any]) -> Optional[pd.DataFrame]:
    if not files_list: return None
    dfs = []
    for f in files_list:
        try:
            if str(f.name).endswith('.csv'):
                temp_df = pd.read_csv(f, sep=None, engine='python', encoding_errors='replace')
            else:
                temp_df = pd.read_excel(f)
            temp_df.columns = [str(c).strip() for c in temp_df.columns]
            dfs.append(temp_df)
        except Exception as e:
            st.error(f"Kunne ikke læse filen: {f.name}")
            print(f"Debug: {e}")
    if not dfs: return None
    df = pd.concat(dfs, ignore_index=True)
    df['Mængde'] = 1.0
    return df

# --- HOVEDPROGRAM ---
if uploaded_files_raw or (data_source == "Manuel Estimering (Indtast volumen)" and aktive_lande):
    if data_source == "Upload Rapport (CSV/Excel)":
        master_df = load_and_preprocess_data(uploaded_files_raw)
        
        if master_df is not None:
            # Mapping
            required_cols = {
                'Land leveringsadresse': ['Land leveringsadresse', 'Country', 'Land', 'Mottakerland', 'Mottagarland', 'Receiver Country', 'Land (leveringsadresse)'],
                'Vægt (kg)': ['Vægt (kg)', 'Vægt', 'Weight', 'Vekt', 'Vikt', 'Weight (kg)', 'Vekt (kg)', 'Vikt (kg)'],
                'Aftalepris': ['Aftalepris', 'Pris', 'Price', 'Faktureret beløb', 'Avtalspris', 'Avtalepris', 'Beløp', 'Belopp', 'Amount', 'Nettobeløp'],
                'Modtagers postnummer': ['Modtagers postnummer', 'Postnummer', 'Zip', 'Zip code', 'Mottakers postnr', 'Mottagarens postnr', 'Postnr', 'Postal code', 'Mottakers postnummer'],
                'Produkt': ['Produkt', 'Product', 'Service', 'Tjeneste', 'Tjänst', 'Tjenestetype']
                'Land leveringsadresse': ['Land leveringsadresse', 'Country', 'Land', 'Mottakerland', 'Mottagarland', 'Receiver Country', 'Land (leveringsadresse)'],
                'Vægt (kg)': ['Vægt (kg)', 'Vægt', 'Weight', 'Vekt', 'Vikt', 'Weight (kg)', 'Vekt (kg)', 'Vikt (kg)'],
                'Aftalepris': ['Aftalepris', 'Pris', 'Price', 'Faktureret beløb', 'Avtalspris', 'Avtalepris', 'Beløp', 'Belopp', 'Amount', 'Nettobeløp'],
                'Modtagers postnummer': ['Modtagers postnummer', 'Postnummer', 'Zip', 'Zip code', 'Mottakers postnr', 'Mottagarens postnr', 'Postnr', 'Postal code', 'Mottakers postnummer'],
                'Produkt': ['Produkt', 'Product', 'Service', 'Tjeneste', 'Tjänst', 'Tjenestetype']
            }
            
            mapping: Dict[str, str] = {}
            missing_cols = []
            for key, alts in required_cols.items():
                found_col = ""
                for alt in alts:
                    if alt in master_df.columns:
                        found_col = str(alt)
                        break
                if found_col: mapping[key] = found_col
                else: missing_cols.append(key)

            if missing_cols:
                with st.expander("⚠️ Hjælp os med at finde kolonnerne", expanded=True):
                    for col in missing_cols:
                        mapping[col] = st.selectbox(f"Vælg kolonne for '{col}':", master_df.columns, key=f"map_{col}")
            
            master_df = master_df.rename(columns={v: k for k, v in mapping.items()})

            # Rens
            master_df['Land leveringsadresse'] = master_df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().str.upper()
            for col in ['Vægt (kg)', 'Aftalepris']:
                if col in master_df.columns:
                    master_df[col] = pd.to_numeric(master_df[col].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0.0)
            master_df['Modtagers postnummer'] = master_df['Modtagers postnummer'].fillna('0000').astype(str).str.strip()
            master_df['Produkt'] = master_df['Produkt'].fillna('Ukendt').astype(str).str.strip()

            aktive_lande = sorted([str(l) for l in master_df['Land leveringsadresse'].unique() if str(l) not in ['UKENDT', '0.0']])
            
            # Præ-beregning
            if isinstance(uploaded_files_raw, list) and len(uploaded_files_raw) > 0:
                f_names = [getattr(f, 'name', 'file') for f in uploaded_files_raw]
                file_hash = "-".join(f_names)
                if 'master_df_precalc' not in st.session_state or st.session_state.get('current_file_hash') != file_hash:
                    with st.spinner("Forbereder data..."):
                        master_df['_Zone'] = master_df.apply(lambda r: zones.get_zone(r, r['Land leveringsadresse']), axis=1)
                        master_df['_W_Idx'] = 0
                        master_df['Vægtklasse'] = "0 kg (Gebyr/Info)"
                        
                        for land_code in aktive_lande:
                            mask = master_df['Land leveringsadresse'] == land_code
                            if not mask.any(): continue
                            # TYPE FIX: Brug .to_numpy() for eksplict Numpy-type
                            steps_list = calculator.PRIS_STEPS.get(land_code, calculator.PRIS_STEPS["DK"])
                            steps_arr = np.asarray(steps_list, dtype=np.float64)
                            w_vals = master_df.loc[mask, 'Vægt (kg)'].to_numpy(dtype=np.float64)
                            
                            indices = np.searchsorted(steps_arr, w_vals, side='left')
                            indices = np.clip(indices, 0, len(steps_arr) - 1)
                            indices = np.where(w_vals == 0, -1, indices)
                            master_df.loc[mask, '_W_Idx'] = indices
                            master_df.loc[mask, 'Vægtklasse'] = master_df.loc[mask, 'Vægt (kg)'].apply(lambda w: calculator.get_weight_bracket(w, steps_list))
                        
                        st.session_state['master_df_precalc'] = master_df.copy()
                        st.session_state['current_file_hash'] = file_hash
                        
                        # Matricer
                        for l_code in aktive_lande:
                            l_prices = master_df[(master_df['Land leveringsadresse'] == l_code) & (master_df['Aftalepris'] > 0)]
                            w_steps = calculator.PRIS_STEPS.get(l_code, calculator.PRIS_STEPS["DK"])
                            
                            if l_code == "SE": s_list = ["0342 PickUp Parcel Bulk", "CITY-1", "CITY-2", "SOUTH-2"]
                            elif l_code == "NO": s_list = ["0342 PickUp Parcel Bulk", "OSL", "NOR2", "NOR3", "NOR4", "NORS"]
                            elif l_code == "FI": s_list = ["0342 PickUp Parcel Bulk", "FI00", "FI01", "FI02", "FI04"]
                            else: s_list = ["PickUp Parcel", "Home Delivery", "Business Parcel"]
                            
                            m_template = pd.DataFrame(0.0, index=s_list, columns=[f"{w}kg" for w in w_steps])
                            if not l_prices.empty:
                                avg_map = l_prices.groupby(['_Zone', '_W_Idx'])['Aftalepris'].mean().to_dict()
                                for s in s_list:
                                    for idx, w_col in enumerate(m_template.columns):
                                        v_avg = avg_map.get((s, idx), l_prices['Aftalepris'].mean())
                                        m_template.loc[s, w_col] = round(float(v_avg), 2)
                            else: m_template[:] = 45.0
                            st.session_state[f"m_data_{l_code}_{model_type}"] = m_template
                else:
                    precalc = st.session_state.get('master_df_precalc')
                    if precalc is not None:
                        master_df = cast(pd.DataFrame, precalc).copy()
    else:
        master_df = pd.DataFrame(columns=['Land leveringsadresse', 'Vægt (kg)', 'Aftalepris', 'Modtagers postnummer', 'Produkt', 'Mængde'])

    # --- TABS ---
    if aktive_lande and master_df is not None:
        st.subheader("3. Konfigurer priser og volumen pr. land")
        tabs = st.tabs(aktive_lande)
        edited_prices_dict = {}
        manual_volume_data = []
        
        for i, land in enumerate(aktive_lande):
            with tabs[i]:
                l_code = str(land).upper().strip()
                w_steps = calculator.PRIS_STEPS.get(l_code, calculator.PRIS_STEPS["DK"])
                
                if l_code == "SE": s_list = ["0342 PickUp Parcel Bulk", "CITY-1", "CITY-2", "SOUTH-2"]
                elif l_code == "NO": s_list = ["0342 PickUp Parcel Bulk", "OSL", "NOR2", "NOR3", "NOR4", "NORS"]
                elif l_code == "FI": s_list = ["0342 PickUp Parcel Bulk", "FI00", "FI01", "FI02", "FI04"]
                else: s_list = ["PickUp Parcel", "Home Delivery", "Business Parcel"]
                
                m_key = f"m_data_{l_code}_{model_type}"
                if m_key not in st.session_state:
                    if "Enhedspris" in model_type: df_init = pd.DataFrame({"Pris pr. pakke (DKK)": ["45,00"] * len(s_list)}, index=s_list)
                    else: df_init = pd.DataFrame("45,00", index=s_list, columns=[f"{w}kg" for w in w_steps])
                    st.session_state[m_key] = df_init.astype(str)

                up_col, dl_col = st.columns([1, 1])
                with up_col:
                    up_m = st.file_uploader(f"Importér {l_code}", type=["xlsx", "xls"], key=f"up_{l_code}")
                    if up_m:
                        try:
                            l_df = pd.read_excel(up_m, index_col=0)
                            st.session_state[m_key] = l_df.map(lambda x: str(x).replace('.', ','))
                            st.toast(f"✅ {l_code} indlæst!")
                        except: st.error("Fejl ved indlæsning.")
                
                edited_prices_dict[l_code] = st.data_editor(st.session_state[m_key], key=f"edit_p_{l_code}", use_container_width=True)
                
                if data_source == "Manuel Estimering (Indtast volumen)":
                    st.divider()
                    st.markdown(f"**📦 Indtast volumen for {l_code}**")
                    v_matrix = pd.DataFrame(0, index=s_list, columns=[f"{w}kg" for w in w_steps])
                    ed_vol = st.data_editor(v_matrix, key=f"edit_v_{l_code}")
                    for s_item in s_list:
                        for j, w_col in enumerate(v_matrix.columns):
                            try:
                                raw_v = ed_vol.loc[s_item, w_col]
                                val_v = pd.to_numeric(raw_v, errors='coerce')
                                mængde_v = float(val_v) if not pd.isna(val_v) else 0.0
                            except: mængde_v = 0.0
                            if mængde_v > 0:
                                manual_volume_data.append({
                                    'Land leveringsadresse': l_code, 'Vægt (kg)': w_steps[j], 'Aftalepris': 0.0,
                                    'Modtagers postnummer': '0000', 'Produkt': s_item, 'Mængde': mængde_v,
                                    '_Zone': s_item, '_W_Idx': j, 'Vægtklasse': w_col
                                })

        if data_source == "Manuel Estimering (Indtast volumen)" and manual_volume_data:
            master_df = pd.DataFrame(manual_volume_data)

        # Beregning
        if master_df is not None:
            if len(master_df) > 500:
                if st.button("🔥 Opdater Beregning", use_container_width=True, type="primary"):
                    master_df = calculator.calculate_results(master_df, edited_prices_dict, model_type, adj_type, adj_val)
                    if master_df is not None:
                        st.session_state['last_calc'] = master_df.copy()
                        st.rerun()
                last_calc = st.session_state.get('last_calc')
                if last_calc is not None:
                    master_df = cast(pd.DataFrame, last_calc).copy()
            else:
                master_df = calculator.calculate_results(master_df, edited_prices_dict, model_type, adj_type, adj_val)

            # Vis Resultater
            if master_df is not None and 'Ny_Pris' in master_df.columns:
                st.divider()
                # TYPE FIX: Brug .to_numpy() for alle matematiske arrays
                old_arr = master_df['Aftalepris'].to_numpy(dtype=np.float64)
                new_arr = master_df['Ny_Pris'].to_numpy(dtype=np.float64)
                qty_arr = master_df['Mængde'].to_numpy(dtype=np.float64)
                
                # Brug np.multiply for at undgå operator-fejl i type-checkeren
                t_old = np.sum(np.multiply(old_arr, qty_arr)) * vol_multiplier
                t_new = np.sum(np.multiply(new_arr, qty_arr)) * vol_multiplier
                t_diff = t_new - t_old
                t_cnt = np.sum(qty_arr) * vol_multiplier
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Antal Pakker", f"{int(t_cnt):,}")
                c2.metric("Nuværende Omsætning", f"{t_old:,.0f} kr.")
                c3.metric("Ny Aftale", f"{t_new:,.0f} kr.", delta=f"{t_diff:,.0f} kr.", delta_color="inverse")
                if t_old > 0:
                    with c4:
                        p_chg = (t_diff/t_old)*100.0
                        if p_chg <= 0: st.success(f"Besparelse: {abs(p_chg):.1f}%")
                        else: st.error(f"Stigning: {p_chg:.1f}%")

                st.subheader("Oversigt pr. Land")
                # Eksplicit Numpy multiplikation for at undgå Pandas ExtensionArray type-fejl
                master_df['W_Old'] = np.multiply(master_df['Aftalepris'].to_numpy(dtype=np.float64), master_df['Mængde'].to_numpy(dtype=np.float64)) * vol_multiplier
                master_df['W_New'] = np.multiply(master_df['Ny_Pris'].to_numpy(dtype=np.float64), master_df['Mængde'].to_numpy(dtype=np.float64)) * vol_multiplier
                
                brk = master_df.groupby('Land leveringsadresse')[['W_Old', 'W_New']].sum()
                st.dataframe(brk.style.format("{:,.0f}"), use_container_width=True)

                if st.button("🚀 Forbered Rapport"):
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                        brk.to_excel(writer, sheet_name='Oversigt')
                        master_df.to_excel(writer, sheet_name='Rådata', index=False)
                    st.download_button("📥 Hent Rapport", buf.getvalue(), "Bring_Analyse.xlsx")
    else:
        st.info("👈 Indtast data eller vælg manuel estimering.")
else:
    st.info("👈 Start her.")
