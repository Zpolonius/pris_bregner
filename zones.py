import csv
import os
import streamlit as st

def load_config():
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

_CONFIG = load_config()

@st.cache_data
def get_all_intervals():
    intervals = {
        "SE_STOCKHOLM": [], "SE_GOTEBORG": [], "NO_OSLO": [],
        "REMOTE_SE": [], "REMOTE_NO": []
    }
    if os.path.exists("Master_City_Surcharge.csv"):
        with open("Master_City_Surcharge.csv", "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                try:
                    s, e = int(row['Fra']), int(row['Til'])
                    if row['Land'] == "SE":
                        if "Stockholm" in row['Beskrivelse']: intervals["SE_STOCKHOLM"].append((s, e))
                        else: intervals["SE_GOTEBORG"].append((s, e))
                    else: intervals["NO_OSLO"].append((s, e))
                except: continue
    if os.path.exists("Master_Remote_Surcharge.csv"):
        with open("Master_Remote_Surcharge.csv", "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                try:
                    s, e = int(row['Fra']), int(row['Til'])
                    key = "REMOTE_SE" if row['Land'] == "SE" else "REMOTE_NO"
                    intervals[key].append((s, e))
                except: continue
    return intervals

def check_intervals(postnr, intervals_list):
    if not intervals_list: return False
    try:
        p_int = int("".join(filter(str.isdigit, str(postnr))))
        for start, end in intervals_list:
            if min(start, end) <= p_int <= max(start, end): return True
    except: pass
    return False

def get_zone_info(row, country):
    """Returnerer både geografisk zone og om der er surcharge (is_remote, is_city)"""
    raw_postnr = str(row.get('Modtagers postnummer', '')).replace(' ', '').strip()
    data = get_all_intervals()
    
    is_remote = False
    is_city = False
    geo_zone = "Standard"
    
    if country == "DK":
        geo_zone = "Standard"
        
    elif country == "SE":
        # 1. Tjek Surcharges
        is_city_st = check_intervals(raw_postnr, data["SE_STOCKHOLM"])
        is_city_go = check_intervals(raw_postnr, data["SE_GOTEBORG"])
        is_remote = check_intervals(raw_postnr, data["REMOTE_SE"])
        is_city = is_city_st or is_city_go
        
        # 2. Geografisk Mapping
        try:
            prefix = int(raw_postnr[:2])
            if 10 <= prefix <= 19: geo_zone = "CITY-1"
            elif 20 <= prefix <= 24: geo_zone = "CITY-3"
            elif 25 <= prefix <= 39: geo_zone = "SOUTH-1"
            elif 40 <= prefix <= 44: geo_zone = "CITY-2"
            elif 45 <= prefix <= 59: geo_zone = "SOUTH-2"
            elif 60 <= prefix <= 69: geo_zone = "NORTH-1"
            elif 70 <= prefix <= 79: geo_zone = "NORTH-2"
            elif 80 <= prefix <= 98: geo_zone = "NORTH-3"
            else: geo_zone = "SOUTH-3"
        except:
            geo_zone = "SOUTH-2"
            
    elif country == "NO":
        is_city = check_intervals(raw_postnr, data["NO_OSLO"])
        is_remote = check_intervals(raw_postnr, data["REMOTE_NO"])
        try:
            p_int = int("".join(filter(str.isdigit, raw_postnr))[:4].zfill(4))
            if p_int <= 1299: geo_zone = "OSL"
            elif p_int <= 3999: geo_zone = "NOR2"
            elif p_int <= 7999: geo_zone = "NOR3"
            elif p_int <= 8999: geo_zone = "NOR4"
            else: geo_zone = "NORS"
        except:
            geo_zone = "NOR2"
            
    elif country == "FI":
        prefix = raw_postnr[:2]
        maps = _CONFIG.get("ZONE_MAPS", {}).get("FI", {"00": "FI00", "DEFAULT": "FI01"})
        geo_zone = maps.get(prefix, maps.get("DEFAULT", "FI01"))
        
    return geo_zone, is_remote, is_city

def get_zone(row, country):
    """Fallback for eksisterende kode - returnerer kun geografisk zone"""
    z, r, c = get_zone_info(row, country)
    return z
