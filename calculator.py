import json
import os
import pandas as pd
import numpy as np
import streamlit as st

# Indlæs konfiguration
def load_config() -> dict:
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

_CONFIG = load_config()
PRIS_STEPS = _CONFIG.get("PRIS_STEPS", {
    "DK": [1, 3, 5, 10, 15, 20, 25, 30, 35],
    "SE": [1, 3, 6, 10, 15, 20, 30, 50, 60, 70],
    "NO": [1, 2, 5, 8, 12, 16, 20, 30, 40, 50],
    "FI": [1, 3, 6, 10, 15, 20, 30, 40, 50, 63]
})

def get_weight_bracket(weight: float, w_steps: list[float]) -> str:
    """Beregner hvilken vægtklasse pakken tilhører til oversigten"""
    if weight == 0: return "0 kg (Gebyr/Info)"
    prev = 0.0
    for step in w_steps:
        if weight <= step:
            return f"{prev}-{step} kg"
        prev = step
    return f">{w_steps[-1]} kg"

def calculate_results(df: pd.DataFrame | None, prices_dict: dict, model_type: str, adj_type: str, adj_val: float) -> pd.DataFrame | None:
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
        df_res = df.copy()
        df_res['Ny_Pris'] = df_res['Aftalepris'].copy()
        
        # Beregn land for land
        for land in numeric_prices_dict.keys():
            mask = df_res['Land leveringsadresse'] == land
            if not mask.any(): continue
            
            pris_tabel = numeric_prices_dict[land]
            price_matrix = pris_tabel.to_numpy(dtype=np.float64)
            services_list = pris_tabel.index.tolist()
            
            land_subset = df_res[mask].copy()
            
            def fast_service_map(p, z):
                if z in services_list: return services_list.index(z)
                p_str = str(p)
                if "PickUp" in p_str:
                    if "0342 PickUp Parcel Bulk" in services_list: return services_list.index("0342 PickUp Parcel Bulk")
                    if "PickUp Parcel" in services_list: return services_list.index("PickUp Parcel")
                return 0

            s_indices = np.array([fast_service_map(p, z) for p, z in zip(land_subset['Produkt'], land_subset['_Zone'])])
            w_indices = land_subset['_W_Idx'].to_numpy(dtype=int)
            
            # Skudsikker valid_mask
            w_arr = land_subset['Vægt (kg)'].to_numpy(dtype=np.float64)
            p_arr = land_subset['Aftalepris'].to_numpy(dtype=np.float64)
            valid_mask = (w_arr > 0) & (p_arr > 0) & (~np.isnan(w_arr))
            
            if valid_mask.any():
                row_idx = s_indices[valid_mask]
                col_idx = w_indices[valid_mask]
                if "Enhedspris" in model_type: col_idx = 0 
                
                bases = price_matrix[row_idx, col_idx]
                if adj_type == "Procent (%)":
                    new_vals = bases * (1 + adj_val / 100)
                else:
                    new_vals = bases + adj_val
                
                final_prices = p_arr.copy()
                final_prices[valid_mask] = new_vals
                df_res.loc[mask, 'Ny_Pris'] = final_prices
        
        return df_res
    except Exception as e:
        st.error("💣 **Ups! Fejl i beregning.**")
        print(f"Calculation error: {e}")
        return df
