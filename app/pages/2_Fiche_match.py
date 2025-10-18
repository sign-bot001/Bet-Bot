import yaml
import streamlit as st
from utils.data import load_today_matches
from models.elo import win_probs_from_strength
from models.goals_poisson import ou25_probs
from models.shots_poisson import team_shots_over_under_probs
from models.corners_poisson import corners_over_under_probs
from models.player_shots import player_shots_probs
from models.chooser import BetOption, ev_from_p_odds, confidence_from

st.set_page_config(page_title="Pari conseillé", page_icon="🎯", layout="centered")

with open("config/settings.yaml", "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

df = load_today_matches("data/processed/matches_today.csv")
st.title("🎯 Pari conseillé — Fiche match")

if df.empty:
    st.info("Aucun match aujourd'hui (démo).")
    st.stop()

idx = st.session_state.get('selected_match_idx', 1)
idx = max(1, min(len(df), int(idx)))
r = df.iloc[idx-1]

st.subheader(f"{r['league']} — {r['home']} vs {r['away']}")

options = []

# 1X2
p_home, p_draw, p_away = win_probs_from_strength(r.home_strength, r.away_strength)
for sel, p, odds in [
    ("Home (1)", p_home, float(r.odds_home)),
    ("Draw (X)", p_draw, float(r.odds_draw)),
    ("Away (2)", p_away, float(r.odds_away))
]:
    ev = ev_from_p_odds(p, odds)
    conf = confidence_from(p, ev, 1.0)
    options.append(BetOption("1X2", sel, odds, p, ev, conf, {}))

# O/U 2.5
p_over, p_under = ou25_probs(r.home_strength, r.away_strength)
for sel, p, odds in [
    ("Over 2.5", p_over, float(r.odds_ou25_over)),
    ("Under 2.5", p_under, float(r.odds_ou25_under)),
]:
    ev = ev_from_p_odds(p, odds)
    conf = confidence_from(p, ev, 1.0)
    options.append(BetOption("OU2.5", sel, odds, p, ev, conf, {}))

# Tirs équipe (Over 4.5 domicile)
p_over, p_under = team_shots_over_under_probs(r.home_shots_rate, r.away_shots_rate, side='home', line=4.5, pace=1.0)
ev = ev_from_p_odds(p_over, float(r.odds_teamshots_home_over45))
conf = confidence_from(p_over, ev, 1.0)
options.append(BetOption("TeamShots", "Home — Over 4.5 tirs", float(r.odds_teamshots_home_over45), p_over, ev, conf, {}))

# Corners (Over/Under 8.5)
p_over, p_under = corners_over_under_probs(r.home_corners_rate, r.away_corners_rate, line=8.5, pace=1.0)
for sel, p, odds in [
    ("Over 8.5 corners", p_over, float(r.odds_corners_over85)),
    ("Under 8.5 corners", p_under, float(r.odds_corners_under85)),
]:
    ev = ev_from_p_odds(p, odds)
    conf = confidence_from(p, ev, 1.0)
    options.append(BetOption("Corners", sel, odds, p, ev, conf, {}))

# Tirs par joueur (joueur domicile Over 1.5)
p_over, p_under, lam = player_shots_probs(r.player_home_shots90, line=1.5, minutes_expected=85, team_multiplier=1.0, role_multiplier=1.0)
ev = ev_from_p_odds(p_over, float(r.odds_player_home_over15))
conf = confidence_from(p_over, ev, 1.0)
options.append(BetOption("PlayerShots", f"{r.player_home} — Over 1.5 tirs", float(r.odds_player_home_over15), p_over, ev, conf, {}))

# Choisir le meilleur
options.sort(key=lambda x: (x.ev, x.confidence), reverse=True)
best = options[0] if options else None

if best:
    st.success("Voici le pari conseillé du match :")
    st.markdown(f"**Type** : {best.market}")
    st.markdown(f"**Sélection** : **{best.selection}**")
    st.markdown(f"**Cote** : **{best.odds:.2f}**")
    st.markdown(f"**EV** : {best.ev:.3f}")
    st.markdown(f"**Confiance** : {best.confidence}/100")
else:
    st.warning("Aucun pari conseillé trouvé.")

st.markdown("---")
if st.button("⬅️ Retour aux matchs du jour"):
    st.switch_page("app/main.py")  # retourne à l’entrée
