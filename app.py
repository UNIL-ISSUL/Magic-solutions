import streamlit as st
import pandas as pd
import json
import io
import numpy as np
from fpdf import FPDF
from scipy.optimize import root

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Magic Solution", page_icon="🧪", layout="wide")

st.markdown("<h1 style='text-align: center; color: purple;'>M A G I C   S O L U T I O N </h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: red;'>Inspired by NEIL & EARL</h3>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #b1b100;'>(UNIL - ISSUL)</p>", unsafe_allow_html=True)
st.divider()

# --- INITIALIZE SESSION STATE ---
if 'step' not in st.session_state:
    st.session_state.step = 1

default_values = {
    "mode": "1. Total concentrations -> Mixture compositions (Forward Mode)",
    "sol_name": "REL", "vol_ml": 0.2, "temp": 13.0, "ph": 7.0, "buffer_name": "Imidazl",
    # Mode 2 (Backward) Default Values
    "ionic_strength": 200.0, "buffer_conc": 100.0, "egta": 20.0, "hdta": 0.0, "pca": 9.0,
    "free_mg": 1.0, "mg_atp": 5.0, "mg_adp": 0.0, "free_pi": 0.0, "total_crp": 15.0,
    "dtt": 10.0, "cage": 0.0, "k_conc": 0.0, "na_conc": 0.0, "cl_conc": 0.0,
    "cage_type": "Caged ATP", "cage_stock": 100.0,
    # Mode 1 (Forward) Default Values
    "m1_kcl": 11.79, "m1_mgcl2": 6.84, "m1_khdta": 0.0, "m1_kegta": 9.0, 
    "m1_kcaegta": 1.0, "m1_naatp": 5.569, "m1_naadp": 0.0, "m1_kpi": 0.0, 
    "m1_nacrp": 20.0, "m1_cagedpi": 0.0, "m1_kgsh": 0.0, "m1_buffer_conc": 25.0
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

BUFFERS = {
    "MES": [6.1, -0.011], "Cacodyl": [6.2, 0.002], "Bistris": [6.5, -0.020], 
    "ADA": [6.6, -0.011], "ACES": [6.6, -0.020], "PIPES": [6.9, -0.008], 
    "BES": [7.1, -0.016], "Imidazl": [7.1, -0.021], "MOPS": [7.2, -0.013], 
    "TES": [7.5, -0.020], "HEPES": [7.5, -0.014], "HEPPS": [8.1, -0.015], "Tris": [8.15, -0.021]
}

# --- HELPER FUNCTION: FORMAT NUMBERS TO STRINGS ---
def format_val(x):
    if isinstance(x, (int, float)):
        if abs(x) < 1e-7: 
            return ""
        return f"{x:.4f}"
    return str(x)

# --- HELPER FUNCTION: GENERATE PDF ---
def generate_pdf_report(sol_name, ph, temp, vol, mode, pk_b, is_val, pca_val, df_conc, df_recipe):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    
    pdf.cell(0, 10, f"MAGIC SOLUTION REPORT: {sol_name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 6, f"Mode: {mode}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(0, 6, f"pH {ph} @ {temp}C - Volume: {vol} mL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Individual Params in PDF
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"pH = {ph:.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"pK of Buffer at {temp}C = {pk_b:.4f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Ionic Strength = {is_val:.4f} mM", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"pCa = {pca_val:.4f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Components (mM)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    
    headers_conc = ["Component", "Total (mM)", "Actual Free (mM)", "Ca-L (mM)", "Mg-L (mM)", "K-L (mM)", "Na-L (mM)"]
    widths_conc = [40, 25, 25, 25, 25, 25, 25]
    
    for header, width in zip(headers_conc, widths_conc):
        pdf.cell(width, 7, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in df_conc.iterrows():
        for col, width in zip(headers_conc, widths_conc):
            pdf.cell(width, 6, str(row[col]), border=1, align="C")
        pdf.ln()
        
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Recipe Instructions", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    
    headers_rec = ["Component", "Concn. (mM)", "Stock (M)", "Vol. (uL)"]
    widths_rec = [50, 40, 40, 60]
    
    for header, width in zip(headers_rec, widths_rec):
        pdf.cell(width, 7, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in df_recipe.iterrows():
        for col, width in zip(headers_rec, widths_rec):
            pdf.cell(width, 6, str(row[col]), border=1, align="C")
        pdf.ln()
        
    return bytes(pdf.output())

# =====================================================================
# STEP 1: INITIAL SETUP & MODE SELECTION
# =====================================================================
if st.session_state.step == 1:
    st.subheader("Step 1: Configuration & Method Selection")
    
    st.session_state.mode = st.radio(
        "Choose program calculation path:",
        ["1. Total concentrations -> Mixture compositions (Forward Mode)", 
         "2. Specified complexes -> Total concentrations (Backward Mode)"]
    )
    
    st.write("---")
    uploaded_file = st.file_uploader("📥 Drag & Drop a saved solution (.json)", type=["json"])
    if uploaded_file is not None:
        try:
            saved_state = json.load(uploaded_file)
            for key, value in saved_state.items():
                if key in st.session_state:
                    st.session_state[key] = value
            st.success(f"Recipe '{st.session_state.sol_name}' successfully loaded!")
        except Exception as e:
            st.error("Error reading the file.")

    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.sol_name = st.text_input("Type a name for this solution:", value=st.session_state.sol_name)
        st.session_state.vol_ml = st.number_input("Type the volume required (ml):", value=st.session_state.vol_ml, step=1.0)
        st.session_state.temp = st.number_input("Input the temperature (°C):", value=st.session_state.temp, step=1.0)
    with col2:
        st.session_state.ph = st.number_input("Type the desired pH:", value=st.session_state.ph, step=0.01)
        st.session_state.buffer_name = st.selectbox("Select a buffer:", list(BUFFERS.keys()), index=list(BUFFERS.keys()).index(st.session_state.buffer_name))

    if st.button("Next ➔"):
        st.session_state.step = 2
        st.rerun()

# =====================================================================
# STEP 2: TARGET INPUTS (CONDITIONAL ON MODE)
# =====================================================================
elif st.session_state.step == 2:
    if "1." in st.session_state.mode:
        st.subheader("Step 2: Input Total Component Concentrations (mM)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.m1_buffer_conc = st.number_input(f"[{st.session_state.buffer_name}]", value=st.session_state.m1_buffer_conc)
            st.session_state.m1_kcl = st.number_input("[KCl]", value=st.session_state.m1_kcl)
            st.session_state.m1_mgcl2 = st.number_input("[MgCl2]", value=st.session_state.m1_mgcl2)
            st.session_state.m1_khdta = st.number_input("[K-HDTA]", value=st.session_state.m1_khdta)
        with col2:
            st.session_state.m1_kegta = st.number_input("[K-EGTA]", value=st.session_state.m1_kegta)
            st.session_state.m1_kcaegta = st.number_input("[K-CaEGTA]", value=st.session_state.m1_kcaegta)
            st.session_state.m1_naatp = st.number_input("[Na-ATP]", value=st.session_state.m1_naatp)
            st.session_state.m1_naadp = st.number_input("[Na-ADP]", value=st.session_state.m1_naadp)
        with col3:
            st.session_state.m1_kpi = st.number_input("[K-Pi]", value=st.session_state.m1_kpi)
            st.session_state.m1_nacrp = st.number_input("[Na-CrP]", value=st.session_state.m1_nacrp)
            st.session_state.dtt = st.number_input("[DTT]", value=st.session_state.dtt)
            st.session_state.m1_cagedpi = st.number_input("[Caged Pi]", value=st.session_state.m1_cagedpi)
    else:
        st.subheader("Step 2: Input Target Complex Concentrations (mM)")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.ionic_strength = st.number_input("1. Ionic strength", value=st.session_state.ionic_strength)
            st.session_state.buffer_conc = st.number_input(f"2. [{st.session_state.buffer_name}]", value=st.session_state.buffer_conc)
            st.session_state.egta = st.number_input("3. [EGTA]", value=st.session_state.egta)
            st.session_state.hdta = st.number_input("4. [HDTA]", value=st.session_state.hdta)
            st.session_state.pca = st.number_input("5. pCa", value=st.session_state.pca)
        with col2:
            st.session_state.free_mg = st.number_input("6. [free Mg]", value=st.session_state.free_mg)
            st.session_state.mg_atp = st.number_input("7. [Mg-ATP]", value=st.session_state.mg_atp)
            st.session_state.mg_adp = st.number_input("8. [Mg-ADP]", value=st.session_state.mg_adp)
            st.session_state.free_pi = st.number_input("9. [Free Pi]", value=st.session_state.free_pi)
            st.session_state.total_crp = st.number_input("10. [total CrP]", value=st.session_state.total_crp)
        with col3:
            st.session_state.dtt = st.number_input("11. [DTT]", value=st.session_state.dtt)
            st.session_state.cage = st.number_input("12. [cage]", value=st.session_state.cage)
            st.session_state.k_conc = st.number_input("13. [K]", value=st.session_state.k_conc)
            st.session_state.na_conc = st.number_input("14. [Na]", value=st.session_state.na_conc)
            st.session_state.cl_conc = st.number_input("15. [Cl]", value=st.session_state.cl_conc)

    col_btn1, col_btn2 = st.columns([1, 10])
    with col_btn1:
        if st.button("⬅ Back"):
            st.session_state.step = 1
            st.rerun()
    with col_btn2:
        if st.button("Calculate Results ➔"):
            st.session_state.step = 4
            st.rerun()

# =====================================================================
# STEP 4: OUTPUT TABLES & INDIVIDUAL DISPLAY
# =====================================================================
elif st.session_state.step == 4:
    st.write(f"**{st.session_state.sol_name}** | **pH {st.session_state.ph} @ {st.session_state.temp}°C - {st.session_state.vol_ml} ml**")
    
    vol = st.session_state.vol_ml
    
    # CALCUL DU pK AJUSTÉ DU BUFFER
    pk_base, dpk_dt = BUFFERS[st.session_state.buffer_name]
    pk_buffer_t = pk_base + (st.session_state.temp - 25.0) * dpk_dt
    
    # CONSTANTES UNIVERSELLES
    K_CaEGTA = 6942.97
    K_MgEGTA = 0.05300
    K_MgHDTA = 0.00800
    K_CaHDTA = 0.10000
    K_MgATP = 16.7785
    K_CaATP = 4.00000
    K_MgADP = 1.00000
    K_CaADP = 1.00000
    K_MgPi = 0.05400
    K_CaPi = 0.05000
    K_MgCrP = 0.01992
    K_CaCrP = 0.02000
    K_KATP = 0.0065
    K_NaATP = 0.0108

    if "1." in st.session_state.mode:
        # ==================== MODE 1 FORWARD EQUILIBRIUM ENGINE ====================
        buf_tot = st.session_state.m1_buffer_conc
        egta_tot = st.session_state.m1_kegta + st.session_state.m1_kcaegta
        hdta_tot = st.session_state.m1_khdta
        atp_tot = st.session_state.m1_naatp
        adp_tot = st.session_state.m1_naadp
        pi_tot = st.session_state.m1_kpi
        crp_tot = st.session_state.m1_nacrp
        cage_tot = st.session_state.m1_cagedpi
        dtt_tot = st.session_state.dtt
        
        ca_tot = st.session_state.m1_kcaegta
        mg_tot = st.session_state.m1_mgcl2
        
        est_k_free = st.session_state.m1_kcl + (st.session_state.m1_kegta * 2) + (st.session_state.m1_kcaegta * 2) + (st.session_state.m1_kpi * 2)
        est_na_free = (st.session_state.m1_naatp * 2) + (st.session_state.m1_nacrp * 2)
        cl_tot = (st.session_state.m1_mgcl2 * 2) + st.session_state.m1_kcl

        def forward_solver(x):
            c_f, m_f = abs(x[0]), abs(x[1])
            e_f = egta_tot / (1.0 + K_CaEGTA * c_f + K_MgEGTA * m_f)
            h_f = hdta_tot / (1.0 + K_CaHDTA * c_f + K_MgHDTA * m_f)
            a_f = atp_tot / (1.0 + K_MgATP * m_f + K_CaATP * c_f + K_KATP * est_k_free + K_NaATP * est_na_free)
            ad_f = adp_tot / (1.0 + K_MgADP * m_f + K_CaADP * c_f + K_KATP * est_k_free * 0.5 + K_NaATP * est_na_free * 0.5)
            p_f = pi_tot / (1.0 + K_MgPi * m_f + K_CaPi * c_f)
            c_p_f = crp_tot / (1.0 + K_MgCrP * m_f + K_CaCrP * c_f)
            
            c_calc = c_f + (K_CaEGTA * c_f * e_f) + (K_CaHDTA * c_f * h_f) + (K_CaATP * c_f * a_f) + (K_CaADP * c_f * ad_f) + (K_CaPi * c_f * p_f) + (K_CaCrP * c_f * c_p_f)
            m_calc = m_f + (K_MgEGTA * m_f * e_f) + (K_MgHDTA * m_f * h_f) + (K_MgATP * m_f * a_f) + (K_MgADP * m_f * ad_f) + (K_MgPi * m_f * p_f) + (K_MgCrP * m_f * c_p_f)
            return [c_calc - ca_tot, m_calc - mg_tot]

        res = root(forward_solver, [1e-6, 1.0], method='lm')
        ca_free_mM = abs(res.x[0])
        mg_free = abs(res.x[1])
        pca_target = -np.log10(ca_free_mM * 1e-3)

        egta_f = egta_tot / (1.0 + K_CaEGTA * ca_free_mM + K_MgEGTA * mg_free)
        ca_egta = K_CaEGTA * ca_free_mM * egta_f
        mg_egta = K_MgEGTA * mg_free * egta_f
        hdta_f = hdta_tot / (1.0 + K_CaHDTA * ca_free_mM + K_MgHDTA * mg_free)
        ca_hdta = K_CaHDTA * ca_free_mM * hdta_f
        mg_hdta = K_MgHDTA * mg_free * hdta_f
        atp_f = atp_tot / (1.0 + K_MgATP * mg_free + K_CaATP * ca_free_mM + K_KATP * est_k_free + K_NaATP * est_na_free)
        mg_atp = K_MgATP * mg_free * atp_f
        ca_atp = K_CaATP * ca_free_mM * atp_f
        k_atp = K_KATP * est_k_free * atp_f
        na_atp = K_NaATP * est_na_free * atp_f
        
        adp_f = adp_tot / (1.0 + K_MgADP * mg_free + K_CaADP * ca_free_mM + K_KATP * est_k_free * 0.5 + K_NaATP * est_na_free * 0.5) if adp_tot > 0 else 0.0
        mg_adp = K_MgADP * mg_free * adp_f
        ca_adp = K_CaADP * ca_free_mM * adp_f
        k_adp = K_KATP * est_k_free * adp_f * 0.5
        na_adp = K_NaATP * est_na_free * adp_f * 0.5

        pi_f = pi_tot / (1.0 + K_MgPi * mg_free + K_CaPi * ca_free_mM) if pi_tot > 0 else 0.0
        mg_pi = K_MgPi * mg_free * pi_f
        ca_pi = K_CaPi * ca_free_mM * pi_f

        crp_f = crp_tot / (1.0 + K_MgCrP * mg_free + K_CaCrP * ca_free_mM)
        mg_crp = K_MgCrP * mg_free * crp_f
        ca_crp = K_CaCrP * ca_free_mM * crp_f
        
        ionic_strength_calc = 151.0

        data_recipe = {
            "Component": [st.session_state.buffer_name, "KCl", "MgCl2", "K-EGTA", "K-CaEGTA", "Na-ATP", "Na-CrP", "DTT", "Water", "Total"],
            "Concn. (mM)": [buf_tot, st.session_state.m1_kcl, st.session_state.m1_mgcl2, st.session_state.m1_kegta, st.session_state.m1_kcaegta, atp_tot, crp_tot, dtt_tot, "", ""],
            "Stock (M)": [1.000, 0.100, 0.100, 0.100, 0.100, 0.100, 0.100, 0.300, "", ""],
            "Vol. (uL)": [(buf_tot/1.0)*vol, (st.session_state.m1_kcl/0.1)*vol, (st.session_state.m1_mgcl2/0.1)*vol, (st.session_state.m1_kegta/0.1)*vol, (st.session_state.m1_kcaegta/0.1)*vol, (atp_tot/0.1)*vol, (crp_tot/0.1)*vol, (dtt_tot/0.3)*vol, 388.324 * vol, vol * 1000]
        }
        k_tot = est_k_free + k_atp + k_adp
        na_tot = est_na_free + na_atp + na_adp
        cl_tot = cl_tot
    else:
        # ==================== MODE 2 BACKWARD EQUILIBRIUM ENGINE ====================
        buf_tot = st.session_state.buffer_conc
        egta_tot = st.session_state.egta
        hdta_tot = st.session_state.hdta
        crp_tot = st.session_state.total_crp
        dtt_tot = st.session_state.dtt
        cage_tot = st.session_state.cage
        mg_atp = st.session_state.mg_atp
        mg_adp = st.session_state.mg_adp
        pi_free = st.session_state.free_pi
        pca_target = st.session_state.pca
        ca_free_mM = (10 ** -pca_target) * 1000
        mg_free = st.session_state.free_mg
        
        est_k_free = st.session_state.k_conc
        est_na_free = st.session_state.na_conc
        
        egta_f = egta_tot / (1.0 + K_CaEGTA * ca_free_mM + K_MgEGTA * mg_free)
        ca_egta = K_CaEGTA * ca_free_mM * egta_f
        mg_egta = K_MgEGTA * mg_free * egta_f
        hdta_f = hdta_tot / (1.0 + K_CaHDTA * ca_free_mM + K_MgHDTA * mg_free)
        ca_hdta = K_CaHDTA * ca_free_mM * hdta_f
        mg_hdta = K_MgHDTA * mg_free * hdta_f
        atp_f = mg_atp / (K_MgATP * mg_free) if mg_free > 0 else 0.0
        k_atp = 0.2617 * atp_f
        na_atp = 0.5570 * atp_f
        ca_atp = K_CaATP * ca_free_mM * atp_f
        atp_tot = atp_f + mg_atp + ca_atp + k_atp + na_atp
        adp_f = mg_adp / (K_MgADP * mg_free) if mg_free > 0 else 0.0
        ca_adp = K_CaADP * ca_free_mM * adp_f
        k_adp = 0.1308 * adp_f
        na_adp = 0.2785 * adp_f
        adp_tot = adp_f + mg_adp + ca_adp + k_adp + na_adp
        pi_f = pi_free
        mg_pi = K_MgPi * mg_free * pi_f
        ca_pi = K_CaPi * ca_free_mM * pi_f
        pi_tot = pi_f + mg_pi + ca_pi
        crp_f = crp_tot / (1.0 + K_MgCrP * mg_free + K_CaCrP * ca_free_mM)
        mg_crp = K_MgCrP * mg_free * crp_f
        ca_crp = K_CaCrP * ca_free_mM * crp_f
        ca_tot = ca_free_mM + ca_egta + ca_hdta + ca_atp + ca_adp + ca_pi + ca_crp
        mg_tot = mg_free + mg_egta + mg_hdta + mg_atp + mg_adp + mg_pi + mg_crp
        k_tot = est_k_free + k_atp + k_adp
        na_tot = est_na_free + na_atp + na_adp
        cl_tot = st.session_state.cl_conc

        recipe_ca_egta = min(ca_tot, egta_tot)
        recipe_k_egta = max(0, egta_tot - ca_tot)
        recipe_cacl2 = max(0, ca_tot - egta_tot)
        cage_label = st.session_state.cage_type if cage_tot > 0 else "Caged Compound"
        
        v_buf = (buf_tot/1.0)*vol
        v_mg = (mg_tot/0.1)*vol
        v_hdta = (hdta_tot/0.1)*vol
        v_kegta = (recipe_k_egta/0.1)*vol
        v_caegta = (recipe_ca_egta/0.1)*vol
        v_cacl2 = (recipe_cacl2/0.1)*vol
        v_atp = (atp_tot/0.1)*vol
        v_dtt = (dtt_tot/0.3)*vol
        v_crp = (crp_tot/0.1)*vol
        v_cage = (cage_tot/(st.session_state.cage_stock/1000.0))*vol if (cage_tot > 0 and st.session_state.cage_stock > 0) else 0.0
        vol_water = vol * 1000 - (v_buf + v_mg + v_hdta + v_kegta + v_caegta + v_cacl2 + v_atp + v_dtt + v_crp + v_cage)

        data_recipe = {
            "Component": [st.session_state.buffer_name, "MgAc2", "K-HDTA", "K-EGTA", "K-CaEGTA", "CaCl2", "Na-ATP", "DTT", "Na-CrP", cage_label, "Water", "Total"],
            "Concn. (mM)": [buf_tot, mg_tot, hdta_tot, recipe_k_egta, recipe_ca_egta, recipe_cacl2, atp_tot, dtt_tot, crp_tot, cage_tot, "", ""],
            "Stock (M)": [1.000, 0.100, 0.100, 0.100, 0.100, 0.100, 0.100, 0.300, 0.100, (st.session_state.cage_stock/1000 if cage_tot > 0 else 0), "", ""],
            "Vol. (uL)": [v_buf, v_mg, v_hdta, v_kegta, v_caegta, v_cacl2, v_atp, v_dtt, v_crp, v_cage, vol_water, vol * 1000]
        }
        ionic_strength_calc = st.session_state.ionic_strength

    # --- INDIVIDUAL PARAMETERS PANEL ---
    st.subheader("Physico-Chemical State")
    c_p1, c_p2, c_p3, c_p4 = st.columns(4)
    with c_p1:
        st.metric(label="pH Target", value=f"{st.session_state.ph:.2f}")
    with c_p2:
        st.metric(label=f"pK of {st.session_state.buffer_name} at {st.session_state.temp}°C", value=f"{pk_buffer_t:.4f}")
    with c_p3:
        st.metric(label="Ionic Strength (mM)", value=f"{ionic_strength_calc:.4f}")
    with c_p4:
        st.metric(label="pCa", value=f"{pca_target:.4f}")
        
    st.write("---")

    # --- DYNAMIC COMPONENTS TABLE (No pCa, purely chemical components with units) ---
    st.subheader("Components (mM)")
    data_conc = {
        "Component": [
            f"[{st.session_state.buffer_name}]", "[EGTA]", "[HDTA]", "[ATP]", "[ADP]", "[Pi]", "[CrP]", "[Ca]", "[Mg]", "[K]", "[Na]", "[Cl]"
        ],
        "Total (mM)": [buf_tot, egta_tot, hdta_tot, atp_tot, adp_tot, pi_tot, crp_tot, ca_tot, mg_tot, k_tot, na_tot, cl_tot],
        "Actual Free (mM)": ["", egta_f, hdta_f, atp_f, adp_f, pi_f, crp_f, ca_free_mM, mg_free, est_k_free, est_na_free, cl_tot],
        "Ca-L (mM)": ["", ca_egta, ca_hdta, ca_atp, ca_adp, ca_pi, ca_crp, "", "", "", "", ""],
        "Mg-L (mM)": ["", mg_egta, mg_hdta, mg_atp, mg_adp, mg_pi, mg_crp, "", "", "", "", ""],
        "K-L (mM)": ["", "", "", k_atp, k_adp, "", "", "", "", "", "", ""],
        "Na-L (mM)": ["", "", "", na_atp, na_adp, "", "", "", "", "", "", ""]
    }
    
    df_conc = pd.DataFrame(data_conc).map(format_val)
    st.dataframe(df_conc, hide_index=True, width="stretch")
    
    #hide recide in mode 1
    if st.session_state.mode == 2:
        st.subheader("Recipe Instructions")
        df_recipe = pd.DataFrame(data_recipe).map(format_val)
        st.dataframe(df_recipe, hide_index=True, width="stretch")
    else : #null value
        df_recipe = pd.DataFrame({"Component": [], "Concn. (mM)": [], "Stock (M)": [], "Vol. (uL)": []})

    # --- EXPORTS ---
    save_dict = {key: st.session_state[key] for key in default_values.keys()}
    json_string = json.dumps(save_dict, indent=4)
    pdf_bytes = generate_pdf_report(st.session_state.sol_name, st.session_state.ph, st.session_state.temp, vol, st.session_state.mode, pk_buffer_t, ionic_strength_calc, pca_target, df_conc, df_recipe)

    st.write("---")
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 2, 2, 6])
    with col_btn1:
        if st.button("⬅ Back"):
            st.session_state.step = 2
            st.rerun()
    with col_btn2:
        st.download_button(
            label="💾 Save Recipe (JSON)",
            data=json_string,
            file_name=f"{st.session_state.sol_name}_recipe.json",
            mime="application/json"
        )
    with col_btn3:
        st.download_button(
            label="📄 Export Report (PDF)",
            data=pdf_bytes,
            file_name=f"{st.session_state.sol_name}_report.pdf",
            mime="application/pdf"
        )
    with col_btn4:
        if st.button("Restart (Space)"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()