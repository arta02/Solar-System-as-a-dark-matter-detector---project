from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


N = 50_000
B_MAX_AU = 10_000.0
rng = np.random.default_rng(20261117)

# Draw uniformly in area and convert to an impact parameter in AU.
b_au = B_MAX_AU * np.sqrt(rng.random(N))

# Reconstruct the enclosed area fraction from the sampled impact parameters.
area_fraction = (b_au / B_MAX_AU) ** 2

half_radius_au = B_MAX_AU / 2
inside_half_radius = np.count_nonzero(b_au <= half_radius_au)

print(
    f"b <= {half_radius_au:,.0f} AU: "
    f"{inside_half_radius:,}/{N:,} ({inside_half_radius / N:.2%})"
)
print(f"Expected: {N // 4:,}/{N:,} (25.00%)")

fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
ax.hist(
    area_fraction, bins=np.linspace(0, 1, 31), density=True,
    color="#b4d1e5", label="Sampled draws",
)
ax.axhline(1, color="#153c57", lw=2, label="Uniform in area")
#ax.axvline(
 #   0.25, color="#555555", ls="--", lw=1.5,
  #  label=r"$b=5{,}000$ AU",
#)
ax.set(
    title=f"Milky Way core impact parameters | {N:,} draws",
    xlabel=r"Enclosed area fraction $(b/b_{\max})^2$",
    ylabel="Probability density",
    xlim=(0, 1),
    ylim=(0, 1.3),
    xticks=[0, 0.25, 0.5, 0.75, 1],
)
ax.legend(loc="lower right")

output = Path(__file__).resolve().with_name("core_impact_parameter_squared.png")
fig.savefig(output, dpi=200)
plt.close(fig)
print(f"Saved {output}")