import streamlit as st
import numpy as np
from scipy.optimize import root_scalar

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Magic Solution Pro", page_icon="🧪", layout="wide")

st.title("🧪 Magic Solution Program (SciPy Edition)")
st.markdown("*Non-linear resolution engine for charge balancing and buffer preparation.*")
st.divider()

# --- BUFFER DATABASE ---
# Format: "Name": [pK_25, dpK_dT, Molar_Mass_g_mol]
BUFFERS = {
    "MES": [6.1, -0.011, 195.2],
    "Cacodyl": [6.2, 0.002, 138.0],
    "Bistris": [6.5, -0.020, 209.2],
    "ADA": [6.6, -0.011, 190.2],
    "ACES": [6.6, -0.020, 182.2],
    "PIPES": [6.9, -0.008, 302.4],
    "BES": [7.1, -0.016, 213.2],
    "Imidazl": [7.1, -0.021, 68.1],
    "MOPS": [7.2, -0.013, 209.3],
    "TES": [7.5, -0.020, 229.2],
    "HEPES": [7.5, -0.014, 238.3],
    "HEPPS": [8.1, -0.015, 252.3],
    "Tris": [8.15, -0.021, 121.14]
}

# --- USER INTERFACE ---
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Target Parameters")
    temp = st.number_input("Temperature (°C)", value=10.0, step=1.0)
    target_ph = st.number_input("Target pH", value=7.10, step=0.01)
    vol_ml = st.number_input("Final Volume (mL)", value=1.0, step=0.1)

with col2:
    st.subheader("Composition (mM)")
    buffer_name = st.selectbox("Buffer (Free Acid Form)", list(BUFFERS.keys()), index=list(BUFFERS.keys()).index("BES"))
    buffer_conc = st.number_input(f"[{buffer_name}] Total", value=100.0, step=1.0)
    
with col3:
    st.subheader("Salts (mM)")
    kcl_conc = st.number_input("[KCl]", value=0.0, step=1.0)
    nacrp_conc = st.number_input("[Na-CrP]", value=15.0, step=1.0)

# --- SCIPY RESOLUTION ENGINE ---

pk_25, dpk_dt, molar_mass = BUFFERS[buffer_name]
pk_t = pk_25 + (temp - 25) * dpk_dt

def charge_balance_equation(base_added):
    """
    Objectif : Trouver la concentration de titrant (en mM) pour équilibrer les charges.
    """
    # Constantes en Molar (M) pour les calculs d'équilibre
    h_plus_M = 10 ** (-target_ph)
    oh_minus_M = (10 ** -14) / h_plus_M
    ka = 10 ** (-pk_t)
    
    # Conversion en mM pour la somme finale
    h_plus_mM = h_plus_M * 1000
    oh_minus_mM = oh_minus_M * 1000
    
    # Spéciation du tampon (Sortie en mM)
    a_minus = buffer_conc * (ka / (ka + h_plus_M))
    
    # Balance des charges (Cations - Anions = 0)
    net_charge = base_added + h_plus_mM - a_minus - oh_minus_mM
    
    return net_charge

# Launching the fsolve optimizer
# Providing an initial guess of 50 mM
solution = root_scalar(charge_balance_equation, bracket=[-1000, 1000], method='brentq')
added_reagent_mm = solution.root

# --- POST-RESOLUTION CALCULATIONS ---
fraction_basique = (10 ** (target_ph - pk_t)) / (1 + 10 ** (target_ph - pk_t))
buffer_ionic_strength = buffer_conc * fraction_basique
salt_ionic_strength = (kcl_conc * 1) + (nacrp_conc * 3)

# Adding the ionic strength of the KOH or HCl found by SciPy
# A 1:1 salt like KOH or HCl has an ionic strength equal to its concentration
titrant_ionic_strength = abs(added_reagent_mm)
total_ionic_strength = buffer_ionic_strength + salt_ionic_strength + titrant_ionic_strength

# --- DISPLAY RESULTS ---
st.divider()

res_col1, res_col2 = st.columns(2)

with res_col1:
    st.subheader("📊 Physico-Chemical Properties")
    st.metric(label=f"Thermodynamic pK at {temp}°C", value=f"{pk_t:.3f}")
    st.metric(label="Total Ionic Strength (mM)", value=f"{total_ionic_strength:.1f}")
    st.caption(f"Including pH adjustment: {titrant_ionic_strength:.1f} mM")

with res_col2:
    st.subheader("🧪 Lab Recipe (Calculated by SciPy)")
    st.info(f"To prepare **{vol_ml} mL** of solution at pH {target_ph}:")
    
    # Powder mass calculation
    mass_mg = (buffer_conc / 1000) * molar_mass * vol_ml
    st.markdown(f"**1.** Weigh **{mass_mg:.2f} mg** of {buffer_name} powder (free form).")
    
    # Titrant determination (Acid or Base)
    if added_reagent_mm > 0:
        vol_1m_ul = added_reagent_mm * vol_ml
        st.markdown(f"**2.** Add **{vol_1m_ul:.1f} uL** of **1M KOH** (or 1M NaOH) solution.")
    else:
        vol_1m_ul = abs(added_reagent_mm) * vol_ml
        st.markdown(f"**2.** Add **{vol_1m_ul:.1f} uL** of **1M HCl** solution.")
        
    st.markdown("**3.** Fill with ultra-pure water (Milli-Q) to the calibration mark.")

st.divider()

st.subheader("ℹ️ Notes")
st.markdown(
    """
- The app assumes a 1:1 titrant such as KOH/NaOH or HCl for pH adjustment.  
- Buffer mass is calculated from total buffer concentration, molar mass, and final volume.  
- Ionic strength is estimated from buffer speciation, salts, and titrant addition.
"""
)
