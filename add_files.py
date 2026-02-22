import pandas as pd

# Vi definerer data for hvert land
data = {
    'DK': {
        'weights': [1, 3, 5, 10, 15, 20, 25, 30, 35],
        'services': {
            'PickUp Parcel Bulk': [24, 26, 28, 32, 36, 41, 48, 56, 65],
            'Home Delivery Parcel': [34, 36, 38, 42, 46, 51, 58, 66, 75],
            'Business Parcel Bulk': [38, 40, 42, 44, 48, 55, 65, 78, 94],
            'Express Nordic 09.00 Bulk': [134, 146, 158, 188, 218, 248, 278, 308, 338]
        }
    },
    'SE': {
        'weights': [1, 3, 6, 10, 15, 20, 30, 50, 60, 70],
        'services': {
            '0332 Business Parcel Bulk': [47, 48, 51, 54, 58, 64, 70, 80, 91, 105],
            '0342 PickUp Parcel Bulk': [25, 26, 28, 39, 46, 52, 63, 73, 82, 92],
            'CITY-1': [50, 52, 54, 56, 61, 65, 72, 80, 92, 104],
            'CITY-2': [61, 62, 64, 67, 71, 76, 82, 90, 102, 114],
            'SOUTH-2': [75, 75, 78, 80, 84, 88, 95, 103, 113, 125]
        }
    },
    'NO': {
        'weights': [1, 2, 5, 8, 12, 16, 20, 30, 40, 50],
        'services': {
            '0332 Business Parcel Bulk': [89, 90, 91, 93, 99, 106, 117, 129, 145, 162],
            '0342 PickUp Parcel Bulk': [51, 52, 54, 56, 62, 68, 79, 93, 109, 127],
            'OSL': [92, 92, 93, 94, 97, 101, 108, 117, 127, 138],
            'NOR2': [104, 104, 105, 107, 111, 117, 126, 137, 150, 164]
        }
    },
    'FI': {
        'weights': [1, 3, 6, 10, 15, 20, 30, 40, 50, 63],
        'services': {
            'FI00': [53, 55, 58.5, 63, 72, 84.5, 107, 132.5, 161, 193],
            'FI01': [58, 60, 63.5, 68, 77, 89, 112, 137.5, 165.5, 197.5],
            '0332 Business Parcel Bulk': [91, 92, 93, 94, 96, 100, 115, 134, 156, 179]
        }
    }
}

# Gemmer til Excel med flere faner
with pd.ExcelWriter('Pris_Konfiguration.xlsx') as writer:
    for country, info in data.items():
        df = pd.DataFrame.from_dict(info['services'], orient='index', columns=info['weights'])
        df.to_excel(writer, sheet_name=country)

print("Succes! Din Pris_Konfiguration.xlsx er nu oprettet.")