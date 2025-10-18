from .elo import poisson_prob_over

def expected_goals(home_strength, away_strength):
    base = 1.35
    home = base * home_strength * 1.05
    away = base * away_strength * 0.95
    return home, away

def ou25_probs(home_strength, away_strength):
    gh, ga = expected_goals(home_strength, away_strength)
    lam_total = gh + ga
    p_over = poisson_prob_over(lam_total, 2.5)
    return p_over, 1 - p_over
