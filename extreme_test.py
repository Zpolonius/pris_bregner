
import pandas as pd
import numpy as np
import time
import io

# Konfiguration fra app.py
PRIS_STEPS = {
    "DK": [1, 3, 5, 10, 15, 20, 25, 30, 35],
    "SE": [1, 3, 6, 10, 15, 20, 30, 50, 60, 70],
    "NO": [1, 2, 5, 8, 12, 16, 20, 30, 40, 50],
    "FI": [1, 3, 6, 10, 15, 20, 30, 40, 50, 63]
}

def test_extreme_performance(file_path):
    print(f"--- EXTREME PERFORMANCE TEST: {file_path} ---")
    
    # 1. Loading
    start_load = time.time()
    df = pd.read_excel(file_path)
    print(f"1. Loading time: {time.time() - start_load:.2f}s ({len(df):,} rows)")
    
    # 2. Cleaning & Pre-calc (The part that happens once)
    start_pre = time.time()
    df['Land leveringsadresse'] = df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().str.upper()
    df['Vægt (kg)'] = pd.to_numeric(df['Vægt (kg)'].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0.0)
    df['Aftalepris'] = pd.to_numeric(df['Aftalepris'].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0.0)
    df['Produkt'] = df['Produkt'].fillna('Ukendt').astype(str).str.strip()
    df['_Zone'] = "Standard" # Simuleret zone mapping (get_zone)
    
    df['_W_Idx'] = 0
    aktive_lande = df['Land leveringsadresse'].unique()
    for land in aktive_lande:
        mask = df['Land leveringsadresse'] == land
        steps = PRIS_STEPS.get(land, PRIS_STEPS["DK"])
        weights = df.loc[mask, 'Vægt (kg)'].values
        indices = np.searchsorted(steps, weights, side='left')
        indices = np.clip(indices, 0, len(steps) - 1)
        indices = np.where(weights == 0, -1, indices)
        df.loc[mask, '_W_Idx'] = indices
    print(f"2. Pre-calc time (Vectorized): {time.time() - start_pre:.2f}s")
    
    # 3. Calculation Simulation (The part that happens on button click/slider change)
    # This simulates the new calculate_results logic with Advanced Indexing
    adj_val = 10.0 # 10% adjustment
    adj_type = "Procent (%)"
    model_type = "Vægtbaseret pris (Matrix)"
    
    # Mock prices_dict
    prices_dict = {}
    for land in aktive_lande:
        w_steps = PRIS_STEPS.get(land, PRIS_STEPS["DK"])
        services = ["Standard", "PickUp Parcel", "Home Delivery"]
        prices_dict[land] = pd.DataFrame(50.0, index=services, columns=[f"{w}kg" for w in w_steps])

    print(f"3. Starting Extreme Calculation Simulation...")
    start_calc = time.time()
    
    # --- ACTUAL APP LOGIC SIMULATION ---
    df['Ny_Pris'] = df['Aftalepris'].copy()
    
    for land in prices_dict.keys():
        mask = df['Land leveringsadresse'] == land
        if not mask.any(): continue
        
        pris_tabel = prices_dict[land]
        price_matrix = pris_tabel.values
        services_list = pris_tabel.index.tolist()
        
        land_subset = df[mask].copy()
        service_map = {s: i for i, s in enumerate(services_list)}
        
        def fast_service_map(p, z):
            if z in service_map: return service_map[z]
            p_str = str(p)
            if "PickUp" in p_str:
                if "0342 PickUp Parcel Bulk" in service_map: return service_map["0342 PickUp Parcel Bulk"]
                if "PickUp Parcel" in service_map: return service_map["PickUp Parcel"]
            return 0

        # Fast mapping via zip/array
        s_indices = np.array([fast_service_map(p, z) for p, z in zip(land_subset['Produkt'], land_subset['_Zone'])])
        w_indices = land_subset['_W_Idx'].values.astype(int)
        
        valid_mask = (land_subset['Vægt (kg)'].values > 0) & (land_subset['Aftalepris'].values > 0)
        
        if valid_mask.any():
            row_idx = s_indices[valid_mask]
            col_idx = w_indices[valid_mask]
            bases = price_matrix[row_idx, col_idx]
            
            if adj_type == "Procent (%)":
                new_vals = bases * (1 + adj_val / 100)
            else:
                new_vals = bases + adj_val
            
            final_prices = land_subset['Aftalepris'].values.copy()
            final_prices[valid_mask] = new_vals
            df.loc[mask, 'Ny_Pris'] = final_prices

    print(f"4. Total Calculation Time for {len(df):,} rows: {time.time() - start_calc:.2f}s")
    print(f"--- TEST COMPLETED ---")

if __name__ == "__main__":
    test_extreme_performance('C:/Users/zacha/Downloads/Forelobigfragtberegning_20000185940_01_01_2025-31_12_2025 (1).xlsx')
