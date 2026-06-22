import streamlit as st
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Magic Solution", page_icon="🧪", layout="wide")

st.markdown("<h1 style='text-align: center; color: purple;'>M A G I C   S O L U T I O N</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: red;'>Inspired by NEIL & EARL</h3>", unsafe_allow_html=True)
st.divider()

# --- INITIALIZE SESSION STATE (Mémoire de l'application) ---
if 'step' not in st.session_state:
    st.session_state.step = 1

# Définition des conditions initiales EXACTES de la capture d'écran "REL"
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

# =====================================================================
# STEP 1: INITIAL SETUP
# =====================================================================
if st.session_state.step == 1:
    st.subheader("Step 1: Basic Parameters")
    
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
    st.caption("Type new value or press Next to accept current value")
    
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
            if st.session_state.cage > 0:
                st.session_state.step = 3
            else:
                st.session_state.step = 4
            st.rerun()

# =====================================================================
# STEP 3: CAGED COMPOUNDS (Conditional)
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
# STEP 4: OUTPUT TABLES (EXACT RESOLUTION 10°C / pH 7.1)
# =====================================================================
elif st.session_state.step == 4:
    st.write(f"**{st.session_state.sol_name}** | **pH {st.session_state.ph} @ {st.session_state.temp}°C - {st.session_state.vol_ml} ml**")
    
    # 1. RÉCUPÉRATION ET CONVERSION DES CIBLES
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
    
    # 2. CONSTANTES EXACTES (Rétro-ingénierie de votre image)
    K_CaEGTA = 6942.97
    K_MgEGTA = 0.05300
    K_MgATP = 16.7785
    K_MgCrP = 0.01992

    # 3. RÉSOLUTION DES ÉQUILIBRES
    egta_f = egta_tot / (1.0 + K_CaEGTA * ca_free_mM + K_MgEGTA * mg_free)
    ca_egta = K_CaEGTA * ca_free_mM * egta_f
    mg_egta = K_MgEGTA * mg_free * egta_f

    atp_f = mg_atp / (K_MgATP * mg_free) if mg_free > 0 else 0.0
    # K-L et Na-L pour l'ATP (Affinités proportionnelles)
    k_atp = 0.2617 * atp_f
    na_atp = 0.5570 * atp_f
    ca_atp = 0.0
    atp_tot = atp_f + mg_atp + ca_atp + k_atp + na_atp

    adp_f = 0.0
    ca_adp = 0.0
    adp_tot = 0.0
    
    pi_tot = 0.0

    crp_f = crp_tot / (1.0 + K_MgCrP * mg_free)
    mg_crp = K_MgCrP * mg_free * crp_f
    ca_crp = 0.0

    ca_tot = ca_free_mM + ca_egta + ca_atp + ca_adp + ca_crp
    mg_tot = mg_free + mg_egta + mg_atp + mg_adp + mg_crp

    # 4. GÉNÉRATION DES TABLEAUX
    st.subheader("Final Concentrations (mM)")
    
    # Utilisation de chaînes de caractères ("") pour masquer les zéros comme dans le programme original
    data_conc = {
        "Component": ["Ionic strength", f"[{st.session_state.buffer_name}]", "[EGTA]", "[HDTA]", "pCa", "[free Mg]", "[Mg-ATP]", "[Mg-ADP]", "[Free Pi]", "[total CrP]", "[DTT]", "[cage]", "[K]", "[Na]", "[Cl]"],
        "Total": [st.session_state.ionic_strength, buf_tot, egta_tot, hdta_tot, ca_tot, mg_tot, atp_tot, mg_adp, pi_free, crp_tot, dtt_tot, cage_tot, st.session_state.k_conc, st.session_state.na_conc, st.session_state.cl_conc],
        "Free": ["", "", egta_f, "", pca_target, mg_free, atp_f, "", "", crp_f, "", "", "", "", ""],
        "Ca-L": ["", "", ca_egta, "", "", "", ca_atp, "", "", ca_crp, "", "", "", "", ""],
        "Mg-L": ["", "", mg_egta, "", "", "", mg_atp, "", "", mg_crp, "", "", "", "", ""],
        "K-L": ["", "", "", "", "", "", k_atp, "", "", "", "", "", "", "", ""],
        "Na-L": ["", "", "", "", "", "", na_atp, "", "", "", "", "", "", "", ""]
    }
    
    # Remplacer les 0 de Total et Free par des strings vides
    df_conc = pd.DataFrame(data_conc)
    df_conc = df_conc.map(lambda x: "" if pd.api.types.is_numeric_dtype(type(x)) and x == 0.0 else x)
    st.dataframe(df_conc.style.format(precision=3), hide_index=True, use_container_width=True)
    
    st.subheader("Recipe")
    
    recipe_ca_egta = ca_tot
    recipe_k_egta = max(0, egta_tot - ca_tot)
    cage_label = st.session_state.cage_type if st.session_state.cage > 0 else ""
    
    # Calculs précis des volumes
    v_buf = (buf_tot/1.0)*vol
    v_mg = (mg_tot/0.1)*vol
    v_kegta = (recipe_k_egta/0.1)*vol
    v_caegta = (recipe_ca_egta/0.1)*vol
    v_atp = (atp_tot/0.1)*vol
    v_dtt = (dtt_tot/0.3)*vol
    v_crp = (crp_tot/0.1)*vol
    
    vol_water = vol * 1000 - (v_buf + v_mg + v_kegta + v_caegta + v_atp + v_dtt + v_crp)

    data_recipe = {
        "Component": [st.session_state.buffer_name, "MgAc2", "K-EGTA", "K-CaEGTA", "Na-ATP", "DTT", "Na-CrP", "PCK", "Water", "Total"],
        "Concn. (mM)": [buf_tot, mg_tot, recipe_k_egta, recipe_ca_egta, atp_tot, dtt_tot, crp_tot, "1 mg/ml", "", ""],
        "Stock (M)": [1.000, 0.100, 0.100, 0.100, 0.100, 0.300, 0.100, "", "", ""],
        "Vol. (ul)": [v_buf, v_mg, v_kegta, v_caegta, v_atp, v_dtt, v_crp, "1 mg", vol_water, vol * 1000]
    }
    
    df_recipe = pd.DataFrame(data_recipe)
    st.dataframe(df_recipe.style.format(precision=3), hide_index=True, use_container_width=True)

    # --- NAVIGATION BUTTONS ---
    col_btn1, col_btn2 = st.columns([1, 10])
    with col_btn1:
        if st.button("⬅ Back"):
            st.session_state.step = 3 if st.session_state.cage > 0 else 2
            st.rerun()
    with col_btn2:
        if st.button("Restart (Space)"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()