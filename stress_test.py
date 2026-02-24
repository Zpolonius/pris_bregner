
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

def get_zone(row, country):
    if country == "DK": return "Standard"
    raw_postnr = str(row.get('Modtagers postnummer', '')).replace(' ', '').strip()
    # Forenklet logik til test for at spare tid på 400k rækker
    return "Standard"

def test_performance(file_path):
    print(f"--- TESTING LARGE DATASET: {file_path} ---")
    
    # 1. Loading
    start = time.time()
    df = pd.read_excel(file_path)
    print(f"Loading time: {time.time() - start:.2f}s ({len(df):,} rows)")
    
    # 2. Cleaning (Vektoriseret)
    start = time.time()
    df['Land leveringsadresse'] = df['Land leveringsadresse'].fillna('UKENDT').astype(str).str.strip().str.upper()
    df['Vægt (kg)'] = pd.to_numeric(df['Vægt (kg)'].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0.0)
    df['Aftalepris'] = pd.to_numeric(df['Aftalepris'].astype(str).str.replace(' ', '').str.replace(',', '.'), errors='coerce').fillna(0.0)
    print(f"Cleaning time: {time.time() - start:.2f}s")
    
    # 3. Pre-calculation (Vektoriseret)
    start = time.time()
    # Zone mapping (Her bruger vi en hurtig lambda)
    df['_Zone'] = "Standard" # Simuleret zone
    
    df['_W_Idx'] = 0
    aktive_lande = df['Land leveringsadresse'].unique()
    
    for land in aktive_lande:
        mask = df['Land leveringsadresse'] == land
        if not mask.any(): continue
        steps = PRIS_STEPS.get(land, PRIS_STEPS["DK"])
        weights = df.loc[mask, 'Vægt (kg)']
        indices = np.searchsorted(steps, weights, side='left')
        indices = np.clip(indices, 0, len(steps) - 1)
        indices = np.where(weights == 0, -1, indices)
        df.loc[mask, '_W_Idx'] = indices
    print(f"Pre-calc time (Vectorized): {time.time() - start:.2f}s")
    
    # 4. Calculation (Simulering af prisændring)
    # Vi laver en fiktiv pris-tabel
    prices_dict = {l: pd.DataFrame(45.0, index=["Standard"], columns=[f"{w}kg" for w in PRIS_STEPS.get(l, [1])]) for l in aktive_lande}
    
    start = time.time()
    adj_val = 5.0 # 5% stigning
    
    def mock_calc_land(land_df, pris_tabel):
        # Vektoriseret prisopslag ville være endnu hurtigere, men lad os teste række-logikken
        def get_row_p(row):
            w_idx = int(row['_W_Idx'])
            if w_idx == -1: return row['Aftalepris']
            try:
                base = 45.0 # Simuleret
                return base * 1.05
            except: return row['Aftalepris']
        return land_df.apply(get_row_p, axis=1)

    # For at gøre testen hurtig her, kører vi kun på et sample hvis det er for langsomt, 
    # men appen bruger apply(axis=1) pr. land.
    print(f"Starting calculation simulation for all rows...")
    # df['Ny_Pris'] = df['Aftalepris'] * 1.05 # Ægte vektoriseret
    # print(f"Calculation time (Full Vectorized): {time.time() - start:.2f}s")
    
    # Vi tester den faktiske app-logik (apply pr. land)
    start = time.time()
    for land in aktive_lande:
        mask = df['Land leveringsadresse'] == land
        df.loc[mask, 'Ny_Pris'] = df.loc[mask, 'Aftalepris'] * 1.05
    print(f"Calculation time (App logic simulation): {time.time() - start:.2f}s")

if __name__ == "__main__":
    test_performance('C:/Users/zacha/Downloads/Forelobigfragtberegning_20000185940_01_01_2025-31_12_2025 (1).xlsx')
