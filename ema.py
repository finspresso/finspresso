import matplotlib.pyplot as plt
import numpy as np

# EMA weights

N_ema = 5
alpha = 2 / (N_ema + 1)
k = np.array(range(0, N_ema))
weights = [alpha * (1 - alpha) ** p for p in k]
plt.bar(x=k + 1, height=weights)
plt.title(f"Exponential moving average (N={N_ema})")
plt.xlabel("Year")
plt.xticks(k + 1)
plt.ylabel("Weight")
plt.grid(axis="y", alpha=0.3)
plt.show()
