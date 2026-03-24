import pandas as pd
import numpy as np
import streamlit as st

# --- KONFIGURATION (Zoner & Vægttrin) ---
PRIS_STEPS = {
    "DK": [1, 3, 5, 10, 15, 20, 25, 30, 35],
    "SE": [1, 3, 6, 10, 15, 20, 30, 50, 60, 70],
    "NO": [1, 2, 5, 8, 12, 16, 20, 30, 40, 50],
    "FI": [1, 3, 6, 10, 15, 20, 30, 40, 50, 63]
}

def get_weight_bracket(weight, w_steps):
    """Beregner hvilken vægtklasse pakken tilhører til oversigten"""
    if weight == 0: return "0 kg (Gebyr/Info)"
    prev = 0
    for step in w_steps:
        if weight <= step:
            return f"{prev}-{step} kg"
        prev = step
    return f">{w_steps[-1]} kg"

def calculate_results(df, prices_dict, model_type, adj_type, adj_val):
    """Den store beregningsmotor (Vektoriseret for hastighed)"""
    if df is None: return None
    
    try:
        # Konverter priser fra tekst (med komma) til float
        numeric_prices_dict = {}
        for k, p_df in prices_dict.items():
            numeric_prices_dict[k] = p_df.copy()
            for col in numeric_prices_dict[k].columns:
                numeric_prices_dict[k][col] = numeric_prices_dict[k][col].apply(
                    lambda x: float(str(x).replace(',', '.').strip() or 0) if isinstance(x, (str, float, int)) else 0.0
                )

        # Kopier for at undgå mutations-problemer
        df = df.copy()
        df['Ny_Pris'] = df['Aftalepris'].copy()
        df['Beregnet_Zone'] = df['_Zone'].copy()
        
        # Beregn land for land
        for land in numeric_prices_dict.keys():
            mask = df['Land leveringsadresse'] == land
            if not mask.any(): continue
            
            pris_tabel = numeric_prices_dict[land]
            if pris_tabel is None: continue
            
            price_matrix = pris_tabel.values
            services_list = pris_tabel.index.tolist()
            
            land_subset = df[mask].copy()
            
            def fast_service_map(p, z):
                if z in services_list: return services_list.index(z)
                p_str = str(p)
                if "PickUp" in p_str:
                    if "0342 PickUp Parcel Bulk" in services_list: return services_list.index("0342 PickUp Parcel Bulk")
                    if "PickUp Parcel" in services_list: return services_list.index("PickUp Parcel")
                return 0

            s_indices = np.array([fast_service_map(p, z) for p, z in zip(land_subset['Produkt'], land_subset['_Zone'])])
            w_indices = land_subset['_W_Idx'].values.astype(int)
            
            valid_mask = (land_subset['Vægt (kg)'].values > 0) & (land_subset['Aftalepris'].values > 0)
            
            if valid_mask.any():
                row_idx = s_indices[valid_mask]
                col_idx = w_indices[valid_mask]
                if "Enhedspris" in model_type: col_idx = 0 
                
                bases = price_matrix[row_idx, col_idx]
                if adj_type == "Procent (%)":
                    new_vals = bases * (1 + adj_val / 100)
                else:
                    new_vals = bases + adj_val
                
                final_prices = land_subset['Aftalepris'].values.copy()
                final_prices[valid_mask] = new_vals
                df.loc[mask, 'Ny_Pris'] = final_prices
        
        return df
    except Exception as e:
        st.error("💣 **Ups! Der skete en fejl i beregnings-motoren.**")
        st.info("Dette skyldes oftest ugyldige værdier i dine priseditorer. Prøv at tjekke dine priser igennem.")
        print(f"Calculation error: {e}")
        return df
