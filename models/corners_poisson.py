from .elo import poisson_tail

def corners_over_under_probs(home_corners_rate, away_corners_rate, line=8.5, pace=1.0):
    lam = (home_corners_rate + away_corners_rate) * pace
    k_threshold = int(line - 0.5)
    p_over = poisson_tail(lam, k_threshold)
    return p_over, 1 - p_over
