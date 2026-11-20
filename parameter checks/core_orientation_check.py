from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


N = 50_000
rng = np.random.default_rng(20261116)

# A uniform draw of cos(i) gives the orbital pole an isotropic tilt.
cos_i = rng.uniform(-1, 1, N)

# Draw from the two half-circle ranges in the notes.
node_half = rng.uniform(-np.pi / 2, np.pi / 2, N)
periapsis_half = rng.uniform(-np.pi / 2, np.pi / 2, N)

# Independently add either 0 or pi to cover the full circle.
node = (node_half + np.pi * rng.integers(0, 2, N)) % (2 * np.pi)
periapsis = (periapsis_half + np.pi * rng.integers(0, 2, N)) % (2 * np.pi)

fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.2), layout="constrained")
fig.suptitle(f"Milky Way core flyby orientations | {N:,} draws")

panels = [
    (cos_i, -1, 1, "Orbital pole height", r"$\cos i_\star$"),
    (node, 0, 2 * np.pi, "Longitude of ascending node", r"$\Omega_\star$ (rad)"),
    (periapsis, 0, 2 * np.pi, "Argument of periapsis", r"$\omega_\star$ (rad)"),
]

for ax, (values, low, high, title, xlabel) in zip(axes, panels):
    bins = np.linspace(low, high, 31)
    ax.hist(values, bins=bins, density=True,
            color="#b4d1e5", label="Sampled draws")
    ax.axhline(1 / (high - low), color="#153c57", linewidth=2,
               label="Expected density")
    ax.set(title=title, xlabel=xlabel, ylabel="Probability density",
           xlim=(low, high))
    ax.set_ylim(bottom=0)

axes[0].set_xticks([-1, -0.5, 0, 0.5, 1])
axes[0].legend(loc="lower right")

for ax in axes[1:]:
    ax.set_xticks(
        [0, np.pi / 2, np.pi, 3 * np.pi / 2, 2 * np.pi],
        ["0", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"],
    )
    ax.set_ylim(0, 0.20)

output = Path(__file__).resolve().with_name("core_orientation_final.png")
fig.savefig(output, dpi=200)
plt.close(fig)
print(f"Saved {output}")