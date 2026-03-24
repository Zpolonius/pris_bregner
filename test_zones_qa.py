import zones
import pandas as pd

def test_mapping():
    test_cases = [
        # Sverige
        {"nr": "111 15", "land": "SE", "exp_zone": "CITY-1", "exp_city": True},  # Stockholm City
        {"nr": "190 00", "land": "SE", "exp_zone": "CITY-1", "exp_city": True},  # Stockholm Greater (City Surcharge)
        {"nr": "211 20", "land": "SE", "exp_zone": "CITY-3", "exp_city": False}, # Malmö
        {"nr": "981 30", "land": "SE", "exp_zone": "NORTH-3", "exp_rem": True},  # Kiruna (Remote)
        {"nr": "652 21", "land": "SE", "exp_zone": "NORTH-1", "exp_rem": False}, # Karlstad
        
        # Norge
        {"nr": "0010", "land": "NO", "exp_zone": "OSL", "exp_city": True},   # Oslo City
        {"nr": "1404", "land": "NO", "exp_zone": "NOR2", "exp_rem": True},  # Siggerud (Remote)
        {"nr": "5003", "land": "NO", "exp_zone": "NOR3", "exp_rem": False}, # Bergen
        {"nr": "9008", "land": "NO", "exp_zone": "NORS", "exp_rem": False}, # Tromsø
    ]
    
    print(f"{'Postnr':<10} | {'Land':<5} | {'Zone':<10} | {'City':<6} | {'Remote':<6} | Status")
    print("-" * 65)
    
    for tc in test_cases:
        row = {'Modtagers postnummer': tc['nr']}
        zone, remote, city = zones.get_zone_info(row, tc['land'])
        
        # Valider
        z_ok = zone == tc['exp_zone']
        c_ok = city == tc.get('exp_city', False)
        r_ok = remote == tc.get('exp_rem', False)
        
        status = "✅ OK" if (z_ok and c_ok and r_ok) else "❌ FEJL"
        print(f"{tc['nr']:<10} | {tc['land']:<5} | {zone:<10} | {str(city):<6} | {str(remote):<6} | {status}")
        if not z_ok: print(f"   -> Forventede zone: {tc['exp_zone']}")

if __name__ == "__main__":
    test_mapping()
