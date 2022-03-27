import numpy as np


def get_root_mean_square_deviation(x):
    rmsd = np.sqrt((x ** 2).mean())
    return rmsd


def get_geometric_mean(x):
    n = x.shape[0] - 1
    x0 = x.iloc[0]
    x1 = x.iloc[-1]
    geometric_mean = (x1 / x0) ** (1 / n) - 1 if n > 0 else 0
    geometric_mean *= 100
    return geometric_mean


def get_ema(x):
    N_ema = x.shape[0]
    alpha = 2 / (N_ema + 1)
    k = np.array(range(0, N_ema))
    weights = [alpha * (1 - alpha) ** p for p in k]
    weights = np.array(weights[::-1])
    ema = weights * x
    ema = ema.sum()
    return ema
