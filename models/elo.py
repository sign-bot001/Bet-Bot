import numpy as np

def win_probs_from_strength(home_strength: float, away_strength: float, home_adv: float=0.15):
    diff = (home_strength + home_adv) - away_strength
    p_home = 1/(1+np.exp(-3*diff))
    p_away = 1 - 1/(1+np.exp(-3*(-diff)))
    parity = np.exp(-abs(diff)*2.5)
    p_draw = 0.22*parity
    s = p_home + p_draw + p_away
    return p_home/s, p_draw/s, p_away/s

def poisson_prob_over(lambda_total: float, threshold: float=2.5):
    p = 1 - sum(np.exp(-lambda_total)*lambda_total**k/np.math.factorial(k) for k in range(0,3))
    return float(p)

def poisson_tail(lmbda: float, k_threshold: int):
    k_req = k_threshold + 1
    cdf = 0.0
    for k in range(0, k_req):
        cdf += np.exp(-lmbda) * (lmbda**k)/np.math.factorial(k)
    return float(1 - cdf)
