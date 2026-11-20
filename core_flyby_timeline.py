from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


DURATION_YR = 100_000        # 0.1 Myr
DT_YR = 0.25                 # Step for deciding whether a flyby occurs
DISPLAY_YR = 1_000           # Show the first 1,000 years in the figure

DENSITY_PC3 = 10_000
B_MAX_AU = 10_000
MEAN_SPEED_KMS = 402.83
AU_PER_PC = 206_264.806
KMS_TO_PC_PER_YR = 1.022712e-6

NEPTUNE_A_AU = 30.069
NEPTUNE_MASS_MSUN = 5.15e-5

# Geometric encounter rate in encounters per year.
b_max_pc = B_MAX_AU / AU_PER_PC
mean_speed_pc_per_yr = MEAN_SPEED_KMS * KMS_TO_PC_PER_YR
gamma = DENSITY_PC3 * np.pi * b_max_pc**2 * mean_speed_pc_per_yr

# Draw one uniform random number per step and apply Zink's short-step rule.
timing_rng = np.random.default_rng(20261117)
n_steps = round(DURATION_YR / DT_YR)
accepted = timing_rng.random(n_steps) < gamma * DT_YR
event_times_yr = (np.flatnonzero(accepted) + 1) * DT_YR

# Draw one initial mean anomaly for Neptune, then advance it on the
# original orbit to compute the unperturbed reference phase for each event.
phase_rng = np.random.default_rng(20261118)
initial_phase_rad = phase_rng.uniform(0, 2 * np.pi)
period_yr = np.sqrt(NEPTUNE_A_AU**3 / (1 + NEPTUNE_MASS_MSUN))
reference_phase_rad = (
    initial_phase_rad + (2 * np.pi / period_yr) * event_times_yr
) % (2 * np.pi)

print(f"Encounter rate: {gamma:.6f} per year")
print(f"Flybys: {len(event_times_yr):,} (expected {gamma * DURATION_YR:,.0f})")
print(f"Mean gap: {np.diff(event_times_yr).mean():.2f} yr (expected {1/gamma:.2f})")
print(f"Initial Neptune mean anomaly: {np.degrees(initial_phase_rad):.2f} deg")

output_dir = Path(__file__).resolve().parent
csv_path = output_dir / "core_flyby_timeline.csv"
np.savetxt(
    csv_path,
    np.column_stack((event_times_yr, np.degrees(reference_phase_rad))),
    delimiter=",",
    header="nominal_periapsis_time_yr,unperturbed_neptune_mean_anomaly_deg",
    comments="",
    fmt="%.6f",
)

# Draw a vertical line only at an accepted encounter time.
visible_times = event_times_yr[event_times_yr <= DISPLAY_YR]
fig, ax = plt.subplots(figsize=(10, 2.3), layout="constrained")
ax.vlines(visible_times, 0, 1, color="#153c57", linewidth=1.2)
ax.set(
    title="Milky Way core flyby timeline | first 1,000 years",
    xlabel="Time (years)",
    xlim=(0, DISPLAY_YR),
    ylim=(0, 1.08),
    yticks=[],
)
ax.spines[["top", "left", "right"]].set_visible(False)

png_path = output_dir / "core_flyby_timeline.png"
fig.savefig(png_path, dpi=200)
plt.close(fig)
print(f"Saved {csv_path.name} and {png_path.name}")