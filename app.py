import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bring Prisberegner", layout="wide")

st.title("📦 Bring Nordisk Prisberegner")
st.markdown("Upload din rapport og test dine nye vægttakster live.")

# 1. SIDEBAR - Indstillinger
st.sidebar.header("Indstillinger")
uploaded_file = st.sidebar.file_uploader("Upload Bring Rapport (CSV)", type="csv")
land = st.sidebar.selectbox("Vælg Land", ["DK", "SE", "NO", "FI"])

# 2. PRIS-EDITOR (Her kan folk ændre priserne)
st.subheader(f"Ret priser for {land}")
# Vi laver en standard matrix som folk kan rette i
default_prices = pd.DataFrame({
    "Vægt (kg)": [1, 3, 5, 10, 15, 20],
    "PickUp": [25.0, 27.0, 29.0, 35.0, 45.0, 55.0],
    "Home": [45.0, 47.0, 49.0, 55.0, 65.0, 75.0]
})

# Den magiske 'data_editor' gør at folk kan rette direkte i tabellen
edited_prices = st.data_editor(default_prices, num_rows="dynamic")

# 3. BEREGNING (Sker når filen er uploadet)
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Her kører vi den logik vi har bygget tidligere
    # (Simuleret her for eksemplets skyld)
    gammel_total = df['Aftalepris'].sum()
    ny_total = gammel_total * 1.05 # Eksempel: 5% stigning
    forskel = ny_total - gammel_total

    # 4. VISNING AF RESULTATER (De "lækre" kasser)
    col1, col2, col3 = st.columns(3)
    col1.metric("Gammel Total", f"{gammel_total:,.2f} kr.")
    col2.metric("Ny Total", f"{ny_total:,.2f} kr.", delta=f"{forskel:,.2f} kr.", delta_color="inverse")
    col3.metric("Besparelse i %", f"{-5.0}%")

    st.divider()
    st.subheader("Analyse pr. forsendelse")
    st.bar_chart(df[['Aftalepris']].head(20)) # Et lille kig på data
else:
    st.info("👋 Upload en fil i venstre side for at starte beregningen.")