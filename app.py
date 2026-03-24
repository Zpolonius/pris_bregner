import streamlit as st
import pandas as pd
import numpy as np
import io
import zones
import calculator
from typing import Any, cast

# Sæt side-konfiguration
st.set_page_config(page_title="Bring Nordic Master", layout="wide", page_icon="logo/favicon.ico")

# --- HJÆLPEFUNKTIONER ---
def generate_matrix_template() -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for land, steps in calculator.PRIS_STEPS.items():
            services = calculator._CONFIG.get("SERVICES", {}).get(land, calculator._CONFIG.get("SERVICES", {}).get("DEFAULT", []))
            cols = [f"{w}kg" for w in steps]
            df = pd.DataFrame("45,00", index=services, columns=cols)
            df.index.name = "Zone / Service"
            df.to_excel(writer, sheet_name=land)
    return output.getvalue()

@st.cache_data
def load_and_preprocess_data(files_list: list[Any]) -> pd.DataFrame | None:
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
    if not dfs: return None
    df = pd.concat(dfs, ignore_index=True)
    df['Mængde'] = 1.0
    return df

# --- LOGO & TITEL ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    try: st.image("logo/bring_new_logo.png", width=150)
    except: st.write("🚛 **Bring Nordic Master**")

with col_title:
    st.title("🌍 Bring Nordic Master-Beregner")
    st.markdown("*Det ultimative salgsværktøj til nordiske fragtsimuleringer.*")

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Værktøjer")
    st.download_button("📥 Download Matrix Skabelon", generate_matrix_template(), "Bring_Nordic_Template.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    
    st.divider()
    st.header("2. Datakilde")
    data_source = st.radio("Vælg input-type:", ["Upload Rapport (CSV/Excel)", "Manuel Estimering"])
    
    master_df: pd.DataFrame | None = None
    uploaded_files_raw: list[Any] = []
    
    if data_source == "Upload Rapport (CSV/Excel)":
        files = st.file_uploader("Upload MyBring rapporter", type=["csv", "xlsx", "xls"], accept_multiple_files=True)
        if files: uploaded_files_raw = list(files)
        aktive_lande_valg = []
    else:
        valgte_lande = st.multiselect("Vælg lande:", ["DK", "SE", "NO", "FI"], default=["DK"])
        aktive_lande_valg = [str(l) for l in valgte_lande] if valgte_lande else []
    
    st.divider()
    st.header("3. Pris-import")
    global_matrix_file = st.file_uploader("Indlæs Hoved-prisliste", type=["xlsx"])
    
    st.divider()
    st.header("4. Indstillinger & Tillæg")
    model_type = st.radio("Prismodel:", ["Enhedspris (Fast pris)", "Vægtbaseret pris (Matrix)"], index=1)
    adj_type = st.radio("Justering:", ["Procent (%)", "Fast beløb (kr.)"], horizontal=True)
    adj_val = float(st.slider("Generel Justering", -20.0, 40.0, 0.0, 0.5)) if adj_type == "Procent (%)" else float(st.number_input("Kr. pr. pakke", -50.0, 100.0, 0.0, 1.0))
    
    # --- NYE TILLÆG SLIDERS ---
    st.markdown("**Sær-tillæg (kr. pr. pakke)**")
    remote_fee = float(st.number_input("Remote Area Surcharge", 0.0, 500.0, 0.0, 5.0))
    city_fee = float(st.number_input("City Surcharge", 0.0, 500.0, 0.0, 5.0))
    
    vol_adj_pct = float(st.slider("Volumen-vækst (%)", -50.0, 200.0, 0.0, 5.0))
    vol_multiplier = float(1.0 + (vol_adj_pct / 100.0))

# --- HOVEDPROGRAM ---
aktive_lande = aktive_lande_valg

if uploaded_files_raw or (data_source == "Manuel Estimering" and aktive_lande):
    if data_source == "Upload Rapport (CSV/Excel)":
        master_df = load_and_preprocess_data(uploaded_files_raw)
        
        if master_df is not None:
            required_cols = {
                'Land leveringsadresse': ['Land leveringsadresse', 'Country', 'Land', 'Mottakerland', 'Mottagarland', 'Receiver Country'],
                'Vægt (kg)': ['Vægt (kg)', 'Vægt', 'Weight', 'Vekt', 'Vikt'],
                'Aftalepris': ['Aftalepris', 'Pris', 'Price', 'Faktureret beløb', 'Nettobeløp'],
                'Modtagers postnummer': ['Modtagers postnummer', 'Postnummer', 'Zip', 'Zip code', 'Postnr'],
                'Produkt': ['Produkt', 'Product', 'Service', 'Tjeneste', 'Tjänst']
            }
            
            mapping: dict[str, str] = {}
            missing_cols = []
            for key, alts in required_cols.items():
                found_col = next((str(alt) for alt in alts if alt in master_df.columns), "")
                if found_col: mapping[key] = found_col
                else: missing_cols.append(key)

            if missing_cols:
                with st.expander("⚠️ Hjælp os med at finde kolonnerne", expanded=True):
                    for col in missing_cols: mapping[col] = st.selectbox(f"Vælg kolonne for '{col}':", master_df.columns, key=f"map_{col}")
            
            master_df = master_df.rename(columns={v: k for k, v in mapping.items()})

            # Rens
            master_df['Land leveringsadresse'] = master_df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().str.upper()
            for col in ['Vægt (kg)', 'Aftalepris']:
                if col in master_df.columns:
                    master_df[col] = pd.to_numeric(master_df[col].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0.0)
            master_df['Modtagers postnummer'] = master_df['Modtagers postnummer'].fillna('0000').astype(str).str.strip()
            master_df['Produkt'] = master_df['Produkt'].fillna('Ukendt').astype(str).str.strip()

            aktive_lande = sorted([str(l) for l in master_df['Land leveringsadresse'].unique() if str(l) not in ['UKENDT', '0.0']])

            # --- 📊 DATA HEALTH DASHBOARD ---
            st.subheader("📊 Data Health Dashboard")
            with st.expander("Se analyse af datakvalitet", expanded=False):
                col_h1, col_h2, col_h3 = st.columns(3)
                # Kør den avancerede zonelogik her
                res = master_df.apply(lambda r: zones.get_zone_info(r, r['Land leveringsadresse']), axis=1)
                master_df['_Zone'] = [x[0] for x in res]
                master_df['_Is_Remote'] = [x[1] for x in res]
                master_df['_Is_City'] = [x[2] for x in res]
                
                remote_count = master_df['_Is_Remote'].sum()
                city_count = master_df['_Is_City'].sum()
                
                with col_h1:
                    st.metric("Remote Area Pakker", int(remote_count))
                    st.caption(f"ℹ️ {int(remote_count)} pakker udløser Remote tillæg.")
                with col_h2:
                    st.metric("City Surcharge Pakker", int(city_count))
                    st.caption(f"ℹ️ {int(city_count)} pakker udløser City tillæg.")
                with col_h3:
                    health_pct = int(((len(master_df) - master_df['Aftalepris'].isna().sum()) / len(master_df)) * 100) if len(master_df) > 0 else 0
                    st.metric("Data Sundhed", f"{health_pct}%")
            
            # Præ-beregning
            if isinstance(uploaded_files_raw, list) and len(uploaded_files_raw) > 0:
                f_hash = "-".join([getattr(f, 'name', 'file') for f in uploaded_files_raw])
                if 'master_df_precalc' not in st.session_state or st.session_state.get('current_file_hash') != f_hash:
                    with st.spinner("Forbereder data..."):
                        master_df['_W_Idx'] = 0
                        master_df['Vægtklasse'] = "0 kg"
                        for land_code in aktive_lande:
                            mask = master_df['Land leveringsadresse'] == land_code
                            if not mask.any(): continue
                            steps = calculator.PRIS_STEPS.get(land_code, calculator.PRIS_STEPS["DK"])
                            w_vals = master_df.loc[mask, 'Vægt (kg)'].to_numpy(dtype=np.float64)
                            indices = np.searchsorted(np.asarray(steps, dtype=np.float64), w_vals, side='left')
                            indices = np.clip(indices, 0, len(steps) - 1)
                            indices = np.where(w_vals == 0, -1, indices)
                            master_df.loc[mask, '_W_Idx'] = indices
                            master_df.loc[mask, 'Vægtklasse'] = master_df.loc[mask, 'Vægt (kg)'].apply(lambda w: calculator.get_weight_bracket(w, steps))
                        st.session_state['master_df_precalc'] = master_df.copy()
                        st.session_state['current_file_hash'] = f_hash
                        # Start-matricer
                        for l_code in aktive_lande:
                            m_key = f"m_data_{l_code}_{model_type}"
                            if m_key not in st.session_state:
                                l_prices = master_df[(master_df['Land leveringsadresse'] == l_code) & (master_df['Aftalepris'] > 0)]
                                w_steps = calculator.PRIS_STEPS.get(l_code, calculator.PRIS_STEPS["DK"])
                                s_list = calculator._CONFIG.get("SERVICES", {}).get(l_code, calculator._CONFIG.get("SERVICES", {}).get("DEFAULT", []))
                                m_template = pd.DataFrame(0.0, index=s_list, columns=[f"{w}kg" for w in w_steps])
                                if not l_prices.empty:
                                    avg_map = l_prices.groupby(['_Zone', '_W_Idx'])['Aftalepris'].mean().to_dict()
                                    for s in s_list:
                                        for idx, w_col in enumerate(m_template.columns):
                                            v_avg = avg_map.get((s, idx), l_prices['Aftalepris'].mean())
                                            m_template.loc[s, w_col] = round(float(v_avg), 2)
                                else: m_template[:] = 45.0
                                st.session_state[m_key] = m_template.astype(str).map(lambda x: str(x).replace('.', ','))
                else:
                    precalc = st.session_state.get('master_df_precalc')
                    if precalc is not None: master_df = cast(pd.DataFrame, precalc).copy()
    else:
        master_df = pd.DataFrame(columns=['Land leveringsadresse', 'Vægt (kg)', 'Aftalepris', 'Modtagers postnummer', 'Produkt', 'Mængde'])

    # --- 🔑 GLOBAL MATRIX IMPORT ---
    if global_matrix_file:
        try:
            xl = pd.ExcelFile(global_matrix_file)
            sheet_names = xl.sheet_names
            with st.container(border=True):
                st.markdown("### 🔑 Hoved-prisliste fundet")
                if 'auto_matched' not in st.session_state or st.session_state.get('last_matrix_name') != global_matrix_file.name:
                    for l_code in aktive_lande:
                        m_key = f"m_data_{l_code}_{model_type}"
                        for s_name in sheet_names:
                            if str(l_code).upper() in str(s_name).upper():
                                try:
                                    new_m = pd.read_excel(global_matrix_file, sheet_name=s_name, index_col=0)
                                    st.session_state[m_key] = new_m.map(lambda x: str(x).replace('.', ','))
                                except: pass
                    st.session_state['auto_matched'] = True
                    st.session_state['last_matrix_name'] = global_matrix_file.name
                col_m1, col_m2 = st.columns(2)
                for i, l_code in enumerate(aktive_lande):
                    t_col = col_m1 if i % 2 == 0 else col_m2
                    with t_col:
                        c_sheet = st.selectbox(f"Ark for {l_code}:", sheet_names, key=f"sh_{l_code}")
                        if st.button(f"Opdater {l_code} fra {c_sheet}", key=f"bt_{l_code}", use_container_width=True):
                            new_m = pd.read_excel(global_matrix_file, sheet_name=c_sheet, index_col=0)
                            st.session_state[f"m_data_{l_code}_{model_type}"] = new_m.map(lambda x: str(x).replace('.', ','))
                            st.rerun()
        except Exception as e: st.error(f"Fejl ved indlæsning: {e}")

    # --- TABS & PRIS EDITERING ---
    if aktive_lande and master_df is not None:
        st.subheader("3. Konfigurer priser og volumen pr. land")
        tabs = st.tabs(aktive_lande)
        edited_prices_dict = {}
        manual_volume_data = []
        
        for i, land in enumerate(aktive_lande):
            with tabs[i]:
                l_code = str(land).upper().strip()
                w_steps = calculator.PRIS_STEPS.get(l_code, calculator.PRIS_STEPS["DK"])
                s_list = calculator._CONFIG.get("SERVICES", {}).get(l_code, calculator._CONFIG.get("SERVICES", {}).get("DEFAULT", []))
                m_key = f"m_data_{l_code}_{model_type}"
                if m_key not in st.session_state:
                    if "Enhedspris" in model_type: df_i = pd.DataFrame({"Pris": ["45,00"] * len(s_list)}, index=s_list)
                    else: df_i = pd.DataFrame("45,00", index=s_list, columns=[f"{w}kg" for w in w_steps])
                    st.session_state[m_key] = df_i.astype(str)
                uc, dc = st.columns([1, 1])
                with uc:
                    u_m = st.file_uploader(f"Importér {l_code} ark", type=["xlsx"], key=f"u_{l_code}")
                    if u_m:
                        l_df = pd.read_excel(u_m, index_col=0)
                        st.session_state[m_key] = l_df.map(lambda x: str(x).replace('.', ','))
                edited_prices_dict[l_code] = st.data_editor(st.session_state[m_key], key=f"ed_p_{l_code}", use_container_width=True)
                if data_source == "Manuel Estimering":
                    st.divider()
                    st.markdown(f"**📦 Volumen for {l_code}**")
                    v_m = pd.DataFrame(0, index=s_list, columns=[f"{w}kg" for w in w_steps])
                    ed_v = st.data_editor(v_m, key=f"ed_v_{l_code}")
                    for s_item in s_list:
                        for j, w_col in enumerate(v_m.columns):
                            try:
                                m_v = float(pd.to_numeric(ed_v.loc[s_item, w_col], errors='coerce'))
                                if m_v > 0:
                                    # AUTO-DETEKTER CITY/REMOTE I MANUEL MODE
                                    is_c_man = True if "CITY" in str(s_item).upper() or "OSL" in str(s_item).upper() else False
                                    is_r_man = True if "REMOTE" in str(s_item).upper() else False
                                    
                                    manual_volume_data.append({
                                        'Land leveringsadresse': l_code, 'Vægt (kg)': w_steps[j], 'Aftalepris': 0.0,
                                        'Modtagers postnummer': '0000', 'Produkt': s_item, 'Mængde': m_v,
                                        '_Zone': s_item, '_W_Idx': j, 'Vægtklasse': w_col, 
                                        '_Is_Remote': is_r_man, '_Is_City': is_c_man
                                    })
                            except: pass

        if data_source == "Manuel Estimering" and manual_volume_data: master_df = pd.DataFrame(manual_volume_data)

        # BEREGNING
        if master_df is not None:
            if len(master_df) > 500:
                if st.button("🔥 Opdater Beregning", use_container_width=True, type="primary"):
                    master_df = calculator.calculate_results(master_df, edited_prices_dict, model_type, adj_type, adj_val, remote_fee, city_fee)
                    if master_df is not None:
                        st.session_state['last_calc'] = master_df.copy()
                        st.rerun()
                last_calc = st.session_state.get('last_calc')
                if last_calc is not None: master_df = cast(pd.DataFrame, last_calc).copy()
            else:
                master_df = calculator.calculate_results(master_df, edited_prices_dict, model_type, adj_type, adj_val, remote_fee, city_fee)

            # VIS RESULTATER
            if master_df is not None and 'Ny_Pris' in master_df.columns:
                st.divider()
                old_a = master_df['Aftalepris'].to_numpy(dtype=np.float64)
                new_a = master_df['Ny_Pris'].to_numpy(dtype=np.float64)
                qty_a = master_df['Mængde'].to_numpy(dtype=np.float64)
                t_old = np.sum(np.multiply(old_a, qty_a)) * vol_multiplier
                t_new = np.sum(np.multiply(new_a, qty_a)) * vol_multiplier
                t_diff = t_new - t_old
                t_cnt = np.sum(qty_a) * vol_multiplier
                
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
                master_df['W_Old'] = np.multiply(master_df['Aftalepris'].to_numpy(dtype=np.float64), master_df['Mængde'].to_numpy(dtype=np.float64)) * vol_multiplier
                master_df['W_New'] = np.multiply(master_df['Ny_Pris'].to_numpy(dtype=np.float64), master_df['Mængde'].to_numpy(dtype=np.float64)) * vol_multiplier
                brk = master_df.groupby('Land leveringsadresse')[['W_Old', 'W_New']].sum()
                st.dataframe(brk.style.format("{:,.0f}"), use_container_width=True)

                if st.button("🚀 Forbered Rapport"):
                    buf = io.BytesIO()
                    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
                        brk.to_excel(writer, sheet_name='Oversigt')
                        master_df.to_excel(writer, sheet_name='Rådata', index=False)
                    st.download_button("📥 Download Resultat (.xlsx)", buf.getvalue(), "Bring_Nordic_Analyse.xlsx", use_container_width=True)
    else: st.info("👈 Upload data eller vælg Manuel Estimering.")
else: st.info("👈 Start her.")
