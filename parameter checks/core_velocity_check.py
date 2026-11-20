from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import kstest, maxwell


N = 50_000
rng = np.random.default_rng(20261116)

speed_std = 170.0  # Standard deviation of the speed magnitude, in km/s.
scale = speed_std / np.sqrt(3 - 8 / np.pi)
theory = maxwell(scale=scale)
mean_speed = theory.mean()

# Draw three velocity components. Their vector length is the speed.
components = rng.normal(0, scale, size=(N, 3))
speeds = np.linalg.norm(components, axis=1)

ks = kstest(speeds, theory.cdf)
print(f"Largest KS gap: {100 * ks.statistic:.3f} percentage points")
print(f"Sample mean: {speeds.mean():.2f} km/s (expected {mean_speed:.2f})")
print(f"Sample standard deviation: {speeds.std(ddof=1):.2f} km/s (expected {speed_std:.2f})")
print(f"Velocity check: {bool(ks.pvalue >= 0.05)} (KS p = {ks.pvalue:.3f})")

v_max = max(speeds.max(), theory.ppf(0.999))
v = np.linspace(0, v_max, 500)

fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
ax.hist(speeds, bins=np.linspace(0, v_max, 46), density=True,
        color="#b4d1e5", label="Sampled speeds")
ax.plot(v, theory.pdf(v), color="#153c57", lw=2, label="Maxwell–Boltzmann")
ax.axvline(mean_speed, color="#555555", ls="--",
           label=f"Mean: {mean_speed:.2f} km/s")
ax.set(
    title=f"Milky Way core flyby speeds | {N:,} draws",
    xlabel=r"Incoming speed $v_\infty$ (km/s)",
    ylabel=r"Probability density $(\mathrm{km/s})^{-1}$",
    xlim=(0, v_max),
)
ax.legend(frameon=False)

output = Path(__file__).resolve().with_name("core_velocity_distribution.png")
fig.savefig(output, dpi=200)
plt.close(fig)
print(f"Saved {output}")