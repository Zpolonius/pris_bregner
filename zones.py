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
        with open("Master_City_Surcharge.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                try:
                    s, t = int(row['Fra']), int(row['Til'])
                    if row['Land'] == "SE":
                        if "Stockholm" in row['Beskrivelse']: intervals["SE_STOCKHOLM"].append((min(s,t), max(s,t)))
                        else: intervals["SE_GOTEBORG"].append((min(s,t), max(s,t)))
                    else: intervals["NO_OSLO"].append((min(s,t), max(s,t)))
                except: continue
    if os.path.exists("Master_Remote_Surcharge.csv"):
        with open("Master_Remote_Surcharge.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                try:
                    s, t = int(row['Fra']), int(row['Til'])
                    key = "REMOTE_SE" if row['Land'] == "SE" else "REMOTE_NO"
                    intervals[key].append((min(s,t), max(s,t)))
                except: continue
    return intervals

def check_intervals(p_int, intervals_list):
    for start, end in intervals_list:
        if start <= p_int <= end: return True
    return False

def get_zone_info(row, country):
    raw_val = str(row.get('Modtagers postnummer', '0')).replace(' ', '')
    try: p_int = int("".join(filter(str.isdigit, raw_val)))
    except: p_int = 0
        
    data = get_all_intervals()
    is_remote = False
    is_city = False
    geo_zone = "Standard"
    
    if country == "DK":
        geo_zone = "Standard"
    elif country == "SE":
        # Surcharge tjek (KUN mod listerne)
        is_city = check_intervals(p_int, data["SE_STOCKHOLM"]) or check_intervals(p_int, data["SE_GOTEBORG"])
        is_remote = check_intervals(p_int, data["REMOTE_SE"])
        # Geografisk zone (Prefix)
        prefix = int(str(p_int).zfill(5)[:2])
        if 10 <= prefix <= 19: geo_zone = "CITY-1"
        elif 20 <= prefix <= 24: geo_zone = "CITY-3"
        elif 25 <= prefix <= 39: geo_zone = "SOUTH-1"
        elif 40 <= prefix <= 44: geo_zone = "CITY-2"
        elif 45 <= prefix <= 59: geo_zone = "SOUTH-2"
        elif 60 <= prefix <= 69: geo_zone = "NORTH-1"
        elif 70 <= prefix <= 79: geo_zone = "NORTH-2"
        elif 80 <= prefix <= 98: geo_zone = "NORTH-3"
        else: geo_zone = "SOUTH-3"
    elif country == "NO":
        is_city = check_intervals(p_int, data["NO_OSLO"])
        is_remote = check_intervals(p_int, data["REMOTE_NO"])
        if p_int <= 1299: geo_zone = "OSL"
        elif p_int <= 3999: geo_zone = "NOR2"
        elif p_int <= 7999: geo_zone = "NOR3"
        elif p_int <= 8999: geo_zone = "NOR4"
        else: geo_zone = "NORS"
    elif country == "FI":
        prefix = str(p_int).zfill(5)[:2]
        maps = _CONFIG.get("ZONE_MAPS", {}).get("FI", {"00": "FI00", "DEFAULT": "FI01"})
        geo_zone = maps.get(prefix, maps.get("DEFAULT", "FI01"))
        
    return geo_zone, is_remote, is_city

def get_zone(row, country):
    z, r, c = get_zone_info(row, country)
    return z
