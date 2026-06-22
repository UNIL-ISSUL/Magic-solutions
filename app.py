import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Magic Solution Calculator", page_icon="🧪", layout="centered")

st.title("🧪 Magic Solution Program")
st.markdown("*Une version moderne et portable de l'outil classique de Neil & Earl.*")
st.divider()

# --- BASE DE DONNÉES DES TAMPONS ---
# Format : "Nom du tampon": [pK à 25°C, dpK/dT]
BUFFERS = {
    "MES": [6.1, -0.011],
    "Cacodyl": [6.2, 0.002],
    "Bistris": [6.5, -0.020],
    "ADA": [6.6, -0.011],
    "ACES": [6.6, -0.020],
    "PIPES": [6.9, -0.008],
    "BES": [7.1, -0.016],
    "Imidazl": [7.1, -0.021],
    "MOPS": [7.2, -0.013],
    "TES": [7.5, -0.020],
    "HEPES": [7.5, -0.014],
    "HEPPS": [8.1, -0.015],
    "Tris": [8.15, -0.021]
}

# --- INTERFACE UTILISATEUR ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Paramètres Généraux")
    temp = st.number_input("Température (°C)", value=10.0, step=1.0)
    target_ph = st.number_input("pH désiré", value=7.10, step=0.01)
    buffer_name = st.selectbox("Choix du Tampon", list(BUFFERS.keys()), index=list(BUFFERS.keys()).index("BES"))
    buffer_conc = st.number_input(f"Concentration [{buffer_name}] (mM)", value=100.0, step=1.0)

with col2:
    st.subheader("Sels et Ligands (mM)")
    kcl_conc = st.number_input("[KCl]", value=0.0, step=1.0)
    mgcl2_conc = st.number_input("[MgCl2]", value=0.0, step=1.0)
    nacrp_conc = st.number_input("[Na-CrP]", value=15.0, step=1.0)

# --- CALCULS (La recette de Neil & Earl) ---
# 1. Ajustement Thermique du pK
pk_25, dpk_dt = BUFFERS[buffer_name]
pk_t = pk_25 + (temp - 25) * dpk_dt

# 2. Proportion de la forme basique du tampon (Henderson-Hasselbalch)
# Note : La forme basique contribue à la force ionique.
fraction_basique = (10 ** (target_ph - pk_t)) / (1 + 10 ** (target_ph - pk_t))
buffer_ionic_strength = buffer_conc * fraction_basique

# 3. Calcul de la force ionique des sels (I = 1/2 * somme(c * z^2))
# - KCl est un sel 1:1 -> Force ionique = Concentration
# - MgCl2 est un sel 2:1 -> Force ionique = 3 * Concentration
# - Na2-CrP (Créatine phosphate disodique) est 2:1 -> Force ionique = 3 * Concentration
salt_ionic_strength = (kcl_conc * 1) + (mgcl2_conc * 3) + (nacrp_conc * 3)

# 4. Force ionique totale
total_ionic_strength = buffer_ionic_strength + salt_ionic_strength

# --- AFFICHAGE DES RÉSULTATS ---
st.divider()
st.subheader("📊 Résultats")

res_col1, res_col2 = st.columns(2)
with res_col1:
    st.metric(label=f"pK du {buffer_name} à {temp}°C", value=f"{pk_t:.2f}")

with res_col2:
    st.metric(label="Force Ionique Totale (mM)", value=f"{total_ionic_strength:.1f}")

st.info(f"**Détail de la Force Ionique :** Contribution du tampon : {buffer_ionic_strength:.1f} mM | Contribution des sels : {salt_ionic_strength:.1f} mM")
