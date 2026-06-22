import streamlit as st
import pandas as pd
import json
import io
from fpdf import FPDF

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
    "sol_name": "REL", "vol_ml": 1.0, "temp": 10.0, "ph": 7.10, "buffer_name": "Imidazl",
    "ionic_strength": 200.0, "buffer_conc": 100.0, "egta": 20.0, "hdta": 0.0, "pca": 9.0,
    "free_mg": 1.0, "mg_atp": 5.0, "mg_adp": 0.0, "free_pi": 0.0, "total_crp": 15.0,
    "dtt": 10.0, "cage": 0.0, "k_conc": 0.0, "na_conc": 0.0, "cl_conc": 0.0,
    "cage_type": "Caged ATP", "cage_stock": 100.0
}

for key, value in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = value

BUFFERS = ["MES", "Cacodyl", "Bistris", "ADA", "ACES", "PIPES", "BES", "Imidazl", "MOPS", "TES", "HEPES", "HEPPS", "Tris"]

# --- HELPER FUNCTION: FORMAT NUMBERS TO STRINGS ---
def format_val(x):
    """
    Formate proprement les valeurs en texte pour éviter les crashs PyArrow
    et garantir l'affichage propre des zéros (cellules vides).
    """
    if isinstance(x, (int, float)):
        if abs(x) < 1e-9: # Si c'est 0.0, on retourne une case vide
            return ""
        return f"{x:.4f}"
    return str(x)

# --- HELPER FUNCTION: GENERATE PDF ---
def generate_pdf_report(sol_name, ph, temp, vol, df_conc, df_recipe):
    pdf = FPDF()
    pdf.add_page()
    # Utilisation de Helvetica au lieu de Arial pour éviter le warning de dépréciation
    pdf.set_font("Helvetica", "B", 16)
    
    # Title Block
    pdf.cell(0, 10, f"MAGIC SOLUTION REPORT: {sol_name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, f"Generated automatically - pH {ph} @ {temp}C - Volume: {vol} mL", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    
    # Section 1: Final Concentrations
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Final Concentrations (mM)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    
    headers_conc = ["Component", "Total", "Free", "Ca-L", "Mg-L", "K-L", "Na-L"]
    widths_conc = [40, 25, 25, 25, 25, 25, 25]
    
    for header, width in zip(headers_conc, widths_conc):
        pdf.cell(width, 7, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in df_conc.iterrows():
        for col, width in zip(headers_conc, widths_conc):
            val = str(row[col])
            pdf.cell(width, 6, val, border=1, align="C")
        pdf.ln()
        
    pdf.ln(10)
    
    # Section 2: Recipe
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "Recipe Instructions", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    
    headers_rec = ["Component", "Concn. (mM)", "Stock (M)", "Vol. (ul)"]
    widths_rec = [50, 40, 40, 60]
    
    for header, width in zip(headers_rec, widths_rec):
        pdf.cell(width, 7, header, border=1, align="C")
    pdf.ln()
    
    pdf.set_font("Helvetica", "", 9)
    for _, row in df_recipe.iterrows():
        for col, width in zip(headers_rec, widths_rec):
            val = str(row[col])
            pdf.cell(width, 6, val, border=1, align="C")
        pdf.ln()
        
    # Retour propre sous forme de bytes (fpdf2 natif)
    return bytes(pdf.output())

# =====================================================================
# STEP 1: INITIAL SETUP & LOAD
# =====================================================================
if st.session_state.step == 1:
    st.subheader("Step 1: Basic Parameters")
    
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
        st.session_state.buffer_name = st.selectbox("Select a buffer:", BUFFERS, index=BUFFERS.index(st.session_state.buffer_name))

    if st.button("Next ➔"):
        st.session_state.step = 2
        st.rerun()

# =====================================================================
# STEP 2: TARGET CONCENTRATIONS
# =====================================================================
elif st.session_state.step == 2:
    st.subheader("Step 2: Selected Conc. (mM)")
    
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
        if st.button("Next ➔"):
            st.session_state.step = 3 if st.session_state.cage > 0 else 4
            st.rerun()

# =====================================================================
# STEP 3: CAGED COMPOUNDS
# =====================================================================
elif st.session_state.step == 3:
    st.subheader("Step 3: Caged Compound Selection")
    st.session_state.cage_type = st.radio("Select the type of cage:", ["Caged ATP", "Caged ADP", "Caged Pi"], horizontal=True)
    st.session_state.cage_stock = st.number_input("Input concentration of caged stock (mM):", value=st.session_state.cage_stock)

    col_btn1, col_btn2 = st.columns([1, 10])
    with col_btn1:
        if st.button("⬅ Back"):
            st.session_state.step = 2
            st.rerun()
    with col_btn2:
        if st.button("Calculate Results ➔"):
            st.session_state.step = 4
            st.rerun()

# =====================================================================
# STEP 4: OUTPUT TABLES, JSON & PDF EXPORT
# =====================================================================
elif st.session_state.step == 4:
    st.write(f"**{st.session_state.sol_name}** | **pH {st.session_state.ph} @ {st.session_state.temp}°C - {st.session_state.vol_ml} ml**")
    
    # 1. PARAMÈTRES
    vol = st.session_state.vol_ml
    buf_tot = st.session_state.buffer_conc
    pca_target = st.session_state.pca
    ca_free_mM = (10 ** -pca_target) * 1000
    mg_free = st.session_state.free_mg
    
    egta_tot = st.session_state.egta
    hdta_tot = st.session_state.hdta
    crp_tot = st.session_state.total_crp
    dtt_tot = st.session_state.dtt
    cage_tot = st.session_state.cage
    mg_atp = st.session_state.mg_atp
    mg_adp = st.session_state.mg_adp
    pi_free = st.session_state.free_pi
    
    # 2. CONSTANTES DYNAMIQUES UNIVERSELLES
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
    K_KATP = 0.0065  # Affinité estimée
    K_NaATP = 0.0108

    # 3. SPÉCIATION ET TOTALISATION DYNAMIQUE (Aucune valeur figée)
    # Estimation des libres pour K et Na
    est_k_free = st.session_state.k_conc + (egta_tot * 2) + (hdta_tot * 2) + (pi_free * 2)
    est_na_free = st.session_state.na_conc + (mg_atp * 2) + (mg_adp * 2) + (crp_tot * 2)

    egta_f = egta_tot / (1.0 + K_CaEGTA * ca_free_mM + K_MgEGTA * mg_free)
    ca_egta = K_CaEGTA * ca_free_mM * egta_f
    mg_egta = K_MgEGTA * mg_free * egta_f

    hdta_f = hdta_tot / (1.0 + K_CaHDTA * ca_free_mM + K_MgHDTA * mg_free)
    ca_hdta = K_CaHDTA * ca_free_mM * hdta_f
    mg_hdta = K_MgHDTA * mg_free * hdta_f

    atp_f = mg_atp / (K_MgATP * mg_free) if mg_free > 0 else 0.0
    k_atp = K_KATP * est_k_free * atp_f
    na_atp = K_NaATP * est_na_free * atp_f
    ca_atp = K_CaATP * ca_free_mM * atp_f
    atp_tot = atp_f + mg_atp + ca_atp + k_atp + na_atp

    adp_f = mg_adp / (K_MgADP * mg_free) if mg_free > 0 else 0.0
    k_adp = K_KATP * est_k_free * adp_f * 0.5  # Estimation d'affinité pour ADP
    na_adp = K_NaATP * est_na_free * adp_f * 0.5
    ca_adp = K_CaADP * ca_free_mM * adp_f
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

    # 4. CONCENTRATIONS TABLE
    st.subheader("Final Concentrations (mM)")
    
    data_conc = {
        "Component": ["Ionic strength", f"[{st.session_state.buffer_name}]", "[EGTA]", "[HDTA]", "pCa", "[free Mg]", "[Mg-ATP]", "[Mg-ADP]", "[Free Pi]", "[total CrP]", "[DTT]", "[cage]", "[K]", "[Na]", "[Cl]"],
        "Total": [st.session_state.ionic_strength, buf_tot, egta_tot, hdta_tot, ca_tot, mg_tot, atp_tot, adp_tot, pi_tot, crp_tot, dtt_tot, cage_tot, k_tot, na_tot, st.session_state.cl_conc],
        "Free": ["", "", egta_f, hdta_f, pca_target, mg_free, atp_f, adp_f, pi_f, crp_f, "", "", est_k_free, est_na_free, ""],
        "Ca-L": ["", "", ca_egta, ca_hdta, "", "", ca_atp, ca_adp, ca_pi, ca_crp, "", "", "", "", ""],
        "Mg-L": ["", "", mg_egta, mg_hdta, "", "", mg_atp, mg_adp, mg_pi, mg_crp, "", "", "", "", ""],
        "K-L": ["", "", "", "", "", "", k_atp, k_adp, "", "", "", "", "", "", ""],
        "Na-L": ["", "", "", "", "", "", na_atp, na_adp, "", "", "", "", "", "", ""]
    }
    
    df_conc = pd.DataFrame(data_conc)
    # Remplacement sécurisé : Tout devient du format STR ("1.2345" ou "") pour ne pas froisser PyArrow
    df_conc_clean = df_conc.map(format_val)
    st.dataframe(df_conc_clean, hide_index=True, width="stretch")
    
    # 5. DYNAMIC RECIPE TABLE
    st.subheader("Recipe")
    
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
    v_adp = (adp_tot/0.1)*vol
    v_pi = (pi_tot/0.1)*vol
    v_dtt = (dtt_tot/0.3)*vol
    v_crp = (crp_tot/0.1)*vol
    
    v_cage = (cage_tot/(st.session_state.cage_stock/1000.0))*vol if (cage_tot > 0 and st.session_state.cage_stock > 0) else 0.0
    
    vol_water = vol * 1000 - (v_buf + v_mg + v_hdta + v_kegta + v_caegta + v_cacl2 + v_atp + v_adp + v_pi + v_dtt + v_crp + v_cage)

    data_recipe = {
        "Component": [st.session_state.buffer_name, "MgAc2", "K-HDTA", "K-EGTA", "K-CaEGTA", "CaCl2", "Na-ATP", "Na-ADP", "K-Pi", "DTT", "Na-CrP", "PCK", cage_label, "Water", "Total"],
        "Concn. (mM)": [buf_tot, mg_tot, hdta_tot, recipe_k_egta, recipe_ca_egta, recipe_cacl2, atp_tot, adp_tot, pi_tot, dtt_tot, crp_tot, "1 mg/ml", cage_tot, "", ""],
        "Stock (M)": [1.000, 0.100, 0.100, 0.100, 0.100, 0.100, 0.100, 0.100, 0.100, 0.300, 0.100, "", (st.session_state.cage_stock/1000 if cage_tot > 0 else 0), "", ""],
        "Vol. (ul)": [v_buf, v_mg, v_hdta, v_kegta, v_caegta, v_cacl2, v_atp, v_adp, v_pi, v_dtt, v_crp, "1 mg", v_cage, vol_water, vol * 1000]
    }
    
    df_recipe = pd.DataFrame(data_recipe)
    df_recipe_clean = df_recipe.map(format_val)
    st.dataframe(df_recipe_clean, hide_index=True, width="stretch")

    # --- EXPORTS ---
    save_dict = {key: st.session_state[key] for key in default_values.keys()}
    json_string = json.dumps(save_dict, indent=4)
    pdf_bytes = generate_pdf_report(st.session_state.sol_name, st.session_state.ph, st.session_state.temp, vol, df_conc_clean, df_recipe_clean)

    st.write("---")
    col_btn1, col_btn2, col_btn3, col_btn4 = st.columns([1, 2, 2, 6])
    with col_btn1:
        if st.button("⬅ Back"):
            st.session_state.step = 3 if st.session_state.cage > 0 else 2
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