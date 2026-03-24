import json
import os

# Indlæs konfiguration (Fallback til standard hvis filen mangler)
def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

_CONFIG = load_config()
ZONE_MAPS = _CONFIG.get("ZONE_MAPS", {
    "SE": {"00": "CITY-1", "10": "CITY-1", "20": "CITY-2", "40": "CITY-2", "DEFAULT": "SOUTH-2"},
    "FI": {"00": "FI00", "45": "FI01", "80": "FI02", "94": "FI04", "DEFAULT": "FI01"}
})

def get_zone(row, country):
    """Beregner zone baseret på land og postnummer"""
    if country == "DK": return "Standard"
    
    # Rens postnummer (fjern mellemrum og sørg for tekst)
    raw_postnr = str(row.get('Modtagers postnummer', '')).replace(' ', '').strip()
    
    if country == "SE":
        prefix = raw_postnr[:2]
        maps = ZONE_MAPS.get("SE", {})
        return maps.get(prefix, maps.get("DEFAULT", "SOUTH-2"))
        
    elif country == "NO":
        # Norge: Baseret på numeriske intervaller (0000-1299=OSL, 1300-3999=NOR2, osv.)
        try:
            # Vi tager kun de første 4 cifre hvis der er flere
            clean_nr = "".join(filter(str.isdigit, raw_postnr))[:4].zfill(4)
            p_int = int(clean_nr)
            
            if p_int <= 1299: return "OSL"
            elif p_int <= 3999: return "NOR2"
            elif p_int <= 7999: return "NOR3"
            elif p_int <= 8999: return "NOR4"
            else: return "NORS"
        except:
            return "NOR2" # Default for Norge
            
    elif country == "FI":
        prefix = raw_postnr[:2]
        maps = ZONE_MAPS.get("FI", {})
        return maps.get(prefix, maps.get("DEFAULT", "FI01"))
        
    return f"Zone 1 ({country})"
