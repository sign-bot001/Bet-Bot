from .elo import poisson_tail

def team_shots_over_under_probs(home_shots_rate, away_shots_rate, side='home', line=4.5, pace=1.0):
    rate = home_shots_rate if side=='home' else away_shots_rate
    lam = rate * pace
    k_threshold = int(line - 0.5)
    p_over = poisson_tail(lam, k_threshold)
    return p_over, 1 - p_over
