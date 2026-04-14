import pdfplumber
import re
import pandas as pd
import os

def get_no_intervals(pdf_path, marker):
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            ext = page.extract_text()
            if ext: text += ext + '\n'
            
    if marker in text:
        no_text = text.split(marker)[1]
    else:
        print(f"Marker '{marker}' not found in {pdf_path}")
        return []
        
    matches = re.findall(r'\b\d{4}\b', no_text)
    
    intervals = []
    for i in range(0, len(matches)-1, 2):
        intervals.append({
            'Fra': int(matches[i]), 
            'Til': int(matches[i+1])
        })
    return intervals

def update_master_file(csv_path, pdf_path, marker, zone, desc, country='NO'):
    if not os.path.exists(csv_path):
        print(f"File {csv_path} does not exist.")
        return

    # Read existing CSV
    df = pd.read_csv(csv_path, sep=';')
    
    # Filter out existing NO intervals to avoid duplicates
    df_non_no = df[df['Land'] != country].copy()
    
    # Extract new NO intervals from PDF
    extracted = get_no_intervals(pdf_path, marker)
    
    if not extracted:
        print(f"No intervals extracted for {csv_path}.")
        return

    # Build new dataframe
    new_data = []
    for interval in extracted:
        new_data.append({
            'Zone': zone,
            'Land': country,
            'Beskrivelse': desc,
            'Fra': interval['Fra'],
            'Til': interval['Til']
        })
    df_new = pd.DataFrame(new_data)
    
    # Combine and save
    df_final = pd.concat([df_non_no, df_new], ignore_index=True)
    df_final.to_csv(csv_path, sep=';', index=False)
    
    print(f"Successfully updated {csv_path} with {len(df_new)} intervals for {country}.")

if __name__ == '__main__':
    print("Updating City Surcharge...")
    update_master_file(
        'Master_City_Surcharge.csv', 
        'Postnummerliste-City-Surcharge_01012026.pdf', 
        'Oslo (NO)', 
        'OSL', 
        'Oslo'
    )
    
    print("\nUpdating Remote Area Surcharge...")
    update_master_file(
        'Master_Remote_Surcharge.csv', 
        'Postnummerliste-Remote-Area-Surcharge_01012026.pdf', 
        'Surcharge: Norge', 
        'REMOTE', 
        'Remote Norge'
    )
