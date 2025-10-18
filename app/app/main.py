import yaml
import streamlit as st
from utils.data import ensure_today_demo, load_today_matches

st.set_page_config(page_title="Football Edge", page_icon="⚽", layout="centered")

with open("config/settings.yaml", "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

st.title("⚽ Football Edge — Matchs du jour")
st.caption("1 pari conseillé par match + combiné du jour")

raw_demo = "data/raw/matches_demo.csv"
processed_today = "data/processed/matches_today.csv"

if CFG.get("autorefresh_on_start", True):
    ensure_today_demo(raw_demo, processed_today)

df = load_today_matches(processed_today)

if df.empty:
    st.info("Aucun match programmé aujourd'hui (démo).")
else:
    df_show = df[['league','home','away']].copy()
    df_show.index = [f"Match #{i+1}" for i in range(len(df_show))]

    st.subheader("Matchs du jour")
    st.dataframe(df_show, use_container_width=True)
    idx = st.number_input("Numéro du match (1..{})".format(len(df_show)),
                          min_value=1, max_value=len(df_show), value=1, step=1)
    if st.button("Voir le pari conseillé"):
        st.session_state['selected_match_idx'] = int(idx)
        st.switch_page("pages/2_Fiche_match.py")  # chemin relatif à app/

st.markdown("---")
if st.button("🎟️ Combiné du jour"):
    st.switch_page("pages/1_Combine_du_jour.py")

st.markdown("— *Données de démonstration. Branche une API pour les cotes réelles.*")
