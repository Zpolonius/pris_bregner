import pandas as pd
import os

def load_price_matrix(config_file):
    """Indlæser alle priser fra din Excel-konfiguration."""
    all_prices = {}
    with pd.ExcelFile(config_file) as xls:
        for sheet_name in xls.sheet_names:
            # Læs fanen (f.eks. 'SE' eller 'NO')
            df_price = pd.read_excel(xls, sheet_name, index_col=0)
            all_prices[sheet_name] = {
                'weights': [float(w) for w in df_price.columns],
                'matrix': df_price.to_dict('index')
            }
    return all_prices

def get_dynamic_price(weight, service, country_code, price_config):
    """Finder prisen i den indlæste matrix."""
    land_data = price_config.get(country_code)
    if not land_data or service not in land_data['matrix']:
        return None
    
    weights = land_data['weights']
    # Vi henter rækken med priser for den specifikke service
    prices_row = list(land_data['matrix'][service].values())
    
    for i, limit in enumerate(weights):
        if weight <= limit:
            return prices_row[i]
    return prices_row[-1]

def process_shipping_data(data_file, country_code, price_config):
    """Hovedfunktion til beregning."""
    df = pd.read_csv(data_file)
    
    def calculate_new_price(row):
        old_price = row.get('Aftalepris', 0)
        weight = row.get('Vægt (kg)', 0)
        
        if old_price == 0: return 0
        if weight == 0: return old_price
        
        # Mapping logik (Hvilken zone/service er det?)
        # Her kan du tilføje din zone-mapping logik baseret på postnummer
        service_key = str(row.get('Produkt', '')) 
        
        new_price = get_dynamic_price(weight, service_key, country_code, price_config)
        return new_price if new_price is not None else old_price

    df['Ny_Pris'] = df.apply(calculate_new_price, axis=1)
    df['Forskel'] = df['Ny_Pris'] - df['Aftalepris']
    return df

# --- KØRSEL AF PROGRAMMET ---
config_path = 'Pris_Konfiguration.xlsx'
rapport_path = 'din_bring_rapport.csv'
land = 'SE'

if os.path.exists(config_path):
    # 1. Hent de nyeste priser fra din Excel-konfiguration
    print("Henter priser fra konfigurationsfilen...")
    aktuelle_priser = load_price_matrix(config_path)
    
    # 2. Beregn konsekvensen på din rapport
    print(f"Beregner priser for {land}...")
    resultat = process_shipping_data(rapport_path, land, aktuelle_priser)
    
    # 3. Gem resultatet
    resultat.to_csv(f'analyse_resultat_{land}.csv', index=False)
    print(f"Færdig! Resultat gemt i 'analyse_resultat_{land}.csv'")
else:
    print("FEJL: Kunne ikke finde Pris_Konfiguration.xlsx")