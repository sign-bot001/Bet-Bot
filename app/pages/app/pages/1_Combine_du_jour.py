import yaml
import streamlit as st
import pandas as pd
from utils.data import load_today_matches
from models.elo import win_probs_from_strength
from models.goals_poisson import ou25_probs
from models.shots_poisson import team_shots_over_under_probs
from models.corners_poisson import corners_over_under_probs
from models.player_shots import player_shots_probs
from models.chooser import BetOption, ev_from_p_odds, confidence_from

st.set_page_config(page_title="Combiné du jour", page_icon="🎟️", layout="centered")

with open("config/settings.yaml", "r", encoding="utf-8") as f:
    CFG = yaml.safe_load(f)

df = load_today_matches("data/processed/matches_today.csv")
st.title("🎟️ Combiné du jour")

if df.empty:
    st.info("Aucun match aujourd'hui (démo).")
    st.stop()

def generate_single_bets(df: pd.DataFrame):
    singles = []
    for _, r in df.iterrows():
        mid = f"{r.home}-{r.away}"

        # 1X2
        p_home, p_draw, p_away = win_probs_from_strength(r.home_strength, r.away_strength)
        for sel, p, odds in [
            ("Home (1)", p_home, float(r.odds_home)),
            ("Draw (X)", p_draw, float(r.odds_draw)),
            ("Away (2)", p_away, float(r.odds_away)),
        ]:
            ev = ev_from_p_odds(p, odds)
            conf = confidence_from(p, ev, 1.0)
            singles.append(BetOption("1X2", f"{r.home} vs {r.away} — {sel}", odds, p, ev, conf, {"match_id": mid}))

        # O/U 2.5
        p_over, p_under = ou25_probs(r.home_strength, r.away_strength)
        for sel, p, odds in [
            ("Over 2.5", p_over, float(r.odds_ou25_over)),
            ("Under 2.5", p_under, float(r.odds_ou25_under)),
        ]:
            ev = ev_from_p_odds(p, odds)
            conf = confidence_from(p, ev, 1.0)
            singles.append(BetOption("OU2.5", f"{r.home} vs {r.away} — {sel}", odds, p, ev, conf, {"match_id": mid}))

        # Tirs équipe (Over 4.5 home)
        p_over, p_under = team_shots_over_under_probs(r.home_shots_rate, r.away_shots_rate, side='home', line=4.5, pace=1.0)
        ev = ev_from_p_odds(p_over, float(r.odds_teamshots_home_over45))
        conf = confidence_from(p_over, ev, 1.0)
        singles.append(BetOption("TeamShots", f"{r.home} — Over 4.5 tirs", float(r.odds_teamshots_home_over45), p_over, ev, conf, {"match_id": mid}))

        # Corners (O/U 8.5)
        p_over, p_under = corners_over_under_probs(r.home_corners_rate, r.away_corners_rate, line=8.5, pace=1.0)
        for sel, p, odds in [
            ("Over 8.5 corners", p_over, float(r.odds_corners_over85)),
            ("Under 8.5 corners", p_under, float(r.odds_corners_under85)),
        ]:
            ev = ev_from_p_odds(p, odds)
            conf = confidence_from(p, ev, 1.0)
            singles.append(BetOption("Corners", f"{r.home} vs {r.away} — {sel}", odds, p, ev, conf, {"match_id": mid}))

        # Tirs par joueur (home Over 1.5)
        p_over, p_under, lam = player_shots_probs(r.player_home_shots90, line=1.5, minutes_expected=85)
        ev = ev_from_p_odds(p_over, float(r.odds_player_home_over15))
        conf = confidence_from(p_over, ev, 1.0)
        singles.append(BetOption("PlayerShots", f"{r.player_home} — Over 1.5 tirs", float(r.odds_player_home_over15), p_over, ev, conf, {"match_id": mid}))

    return singles

# Générer et filtrer
singles = generate_single_bets(df)
ev_min_team = CFG["ev_min_team"]
ev_min_player = CFG["ev_min_player_shots"]
max_odds_team = CFG["max_odds_team"]
max_odds_player = CFG["max_odds_player_shots"]
odds_min = CFG["combo_odds_min"]
odds_max = CFG["combo_odds_max"]

valid = []
for s in singles:
    if s.market == "PlayerShots":
        if s.ev < ev_min_player or s.odds > max_odds_player:
            continue
    else:
        if s.ev < ev_min_team or s.odds > max_odds_team:
            continue
    valid.append(s)

valid.sort(key=lambda x: (x.ev, x.confidence), reverse=True)

# Construction gloutonne (1 leg max par match)
combo = []
combo_odds = 1.0
combo_p = 1.0
used = set()

for s in valid:
    mid = s.meta["match_id"]
    if mid in used:
        continue
    potential = combo_odds * s.odds
    if potential > odds_max:
        continue
    combo.append(s)
    used.add(mid)
    combo_odds *= s.odds
    combo_p *= s.p
    if combo_odds >= odds_min:
        break

st.subheader("Sélection proposée")
if not combo:
    st.info("Aucune combinaison propre trouvée. On propose le meilleur pari simple de la journée.")
    if valid:
        best = valid[0]
        combo = [best]
        combo_odds = best.odds
        combo_p = best.p
    else:
        st.warning("Aucun pari disponible aujourd'hui (démo).")
        st.stop()

for i, leg in enumerate(combo, 1):
    st.markdown(f"**Leg {i}** — {leg.market}: {leg.selection}  •  Cote **{leg.odds:.2f}**  •  Confiance **{leg.confidence}/100**")

st.markdown(f"**Cote totale** : **{combo_odds:.2f}**")
ev_combo = combo_p * combo_odds - (1 - combo_p)
st.markdown(f"**EV combiné** : {ev_combo:.3f}  •  **Proba de gain** ≈ {combo_p*100:.1f}%")

# Mise conseillée: Kelly 25% capé 0.5%
b = combo_odds - 1.0
edge = (combo_odds * combo_p - (1 - combo_p)) / b if b>0 else 0.0
stake = max(CFG["combo_stake_min_pct"], min(CFG["combo_stake_max_pct"], edge * CFG["combo_kelly_fraction"]))
st.markdown(f"**Mise conseillée** : {stake*100:.2f}% de la bankroll")

st.markdown("---")
if st.button("⬅️ Retour aux matchs du jour"):
    st.switch_page("app/main.py")
