import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rebound

from core_mass_check import sample_log_masses


DURATION_YR = 100_000
DT_YR = 0.25
GAMMA_PER_YR = 0.0304211

B_MAX_AU = 10_000.0
BOUNDARY_AU = 15_000.0
KMS_TO_AU_PER_YR = 365.25 * 86400 / 149_597_870.7
MAXWELL_SCALE_KMS = 170.0 / math.sqrt(3 - 8 / math.pi)


def add_flyby(sim, rng):
    mass = float(10 ** sample_log_masses(rng, 1)[0])
    speed_kms = float(np.linalg.norm(rng.normal(0, MAXWELL_SCALE_KMS, 3)))
    b = B_MAX_AU * math.sqrt(rng.random())
    inc = math.acos(rng.uniform(-1, 1))
    node, periapsis = rng.uniform(0, math.tau, 2)

    # Set up a two-body incoming hyperbola relative to the Sun.
    sun = sim.particles[0]
    v_inf = speed_kms * KMS_TO_AU_PER_YR
    abs_a = sim.G * (sun.m + mass) / v_inf**2
    eccentricity = math.hypot(1, b / abs_a)
    semilatus_rectum = b**2 / abs_a
    nominal_q = semilatus_rectum / (1 + eccentricity)
    cos_f = (semilatus_rectum / BOUNDARY_AU - 1) / eccentricity
    inbound_f = -math.acos(cos_f)

    sim.add(
        primary=sun, m=mass, a=-abs_a, e=eccentricity, f=inbound_f,
        inc=inc, Omega=float(node), omega=float(periapsis),
    )
    return (sim.t, mass, speed_kms, b, nominal_q,
            inc, float(node), float(periapsis))


def remove_departed_stars(sim):
    for index in range(sim.N - 1, 1, -1):
        sun, star = sim.particles[0], sim.particles[index]
        dx, dy, dz = star.x - sun.x, star.y - sun.y, star.z - sun.z
        radius_sq = dx**2 + dy**2 + dz**2
        radial_motion = (
            dx * (star.vx - sun.vx)
            + dy * (star.vy - sun.vy)
            + dz * (star.vz - sun.vz)
        )
        if radius_sq >= BOUNDARY_AU**2 and radial_motion > 0:
            sim.remove(index)


timing_rng = np.random.default_rng(20261117)
phase_rng = np.random.default_rng(20261118)
flyby_rng = np.random.default_rng(20261119)

sim = rebound.Simulation()
sim.units = ("yr", "AU", "Msun")
sim.integrator = "ias15"
sim.add(m=1.0)

initial_phase = float(phase_rng.uniform(0, math.tau))
sim.add(m=5.15e-5, a=30.069, e=0.0086, M=initial_phase)
sim.move_to_com()

a_initial = sim.particles[1].orbit(primary=sim.particles[0]).a
events = []
max_active = 0
history = [(0.0, 0.0, 0)]  # time, signed delta a/a, active stars
for step in range(1, round(DURATION_YR / DT_YR) + 1):
    sim.integrate(step * DT_YR)
    remove_departed_stars(sim)

    if timing_rng.random() < GAMMA_PER_YR * DT_YR:
        events.append(add_flyby(sim, flyby_rng))

    max_active = max(max_active, sim.N - 2)
    a_now = sim.particles[1].orbit(primary=sim.particles[0]).a
    history.append((sim.t, (a_now - a_initial) / a_initial, sim.N - 2))
    if step % round(10_000 / DT_YR) == 0:
        print(f"Year {sim.t:,.0f} | stars added: {len(events):,}", flush=True)
a_final = sim.particles[1].orbit(primary=sim.particles[0]).a

log_path = Path(__file__).resolve().with_name("core_live_flyby_100k_events.csv")
with log_path.open("w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow([
        "entry_time_yr", "mass_msun", "v_inf_kms", "b_au",
        "nominal_q_au", "inclination_rad", "node_rad", "periapsis_rad",
    ])
    writer.writerows(events)

print(f"Initial Neptune phase: {math.degrees(initial_phase):.2f} deg")
print(f"Stars added: {len(events)} (expected about {GAMMA_PER_YR * DURATION_YR:.1f})")
print(f"Most stars present at once: {max_active}")
print(f"Stars still present at the end: {sim.N - 2}")
print(f"Neptune delta a/a at year {DURATION_YR}: {a_final / a_initial - 1:+.6e}")
print(f"Saved {log_path.name}")

times, delta_a, active_stars = np.asarray(history).T

# The same random streams should reproduce the first 1,000 years of the pilot.
pilot_index = round(1_000 / DT_YR)
print(f"Delta a/a at year 1,000: {delta_a[pilot_index]:+.6e}")
print(f"Largest |delta a/a|: {np.max(np.abs(delta_a)):.6e}")

threshold = 1e-3
crossings = np.flatnonzero(np.abs(delta_a) > threshold)

if crossings.size:
    index = crossings[0]
    print(
        f"First sampled crossing: year {times[index]:,.2f}, "
        f"delta a/a = {delta_a[index]:+.6e}, "
        f"active stars = {int(active_stars[index])}"
    )
else:
    print(f"No sampled crossing of {threshold:.0e} in {DURATION_YR:,} yr.")

# Match the reference's first decade and keep zero magnitudes off the log axis.
first_plot_year = 100
plot_window = times >= first_plot_year
magnitude = np.ma.masked_equal(np.abs(delta_a[plot_window]), 0.0)

fig, ax = plt.subplots(figsize=(10, 4.8), layout="constrained")
ax.loglog(times[plot_window], magnitude, color="#153c57", lw=1.4,
          label="Milky Way core")
ax.axhline(threshold, color="0.25", ls="-.", lw=1.0,
           label=r"Threshold $10^{-3}$")
ax.set(
    title="Neptune’s response to Milky Way core flybys",
    xlabel="Time [yr]",
    ylabel=r"$|\Delta a/a_0|$",
    xlim=(first_plot_year, DURATION_YR),
)
ax.set_axisbelow(True)
ax.grid(which="major", color="0.84", lw=0.7)
ax.grid(axis="x", which="minor", color="0.91", lw=0.5)
ax.legend(loc="upper left")

plot_path = Path(__file__).resolve().with_name(
    f"{Path(__file__).stem}_neptune.png"
)
fig.savefig(plot_path, dpi=200)
plt.close(fig)
print(f"Saved {plot_path.name}")


def nominal_periapsis_time(event):
    entry_year, mass, speed_kms, _, q_au, *_ = event
    v_inf = speed_kms * KMS_TO_AU_PER_YR
    abs_a = sim.G * (1.0 + mass) / v_inf**2
    eccentricity = 1.0 + q_au / abs_a
    H = math.acosh((1.0 + BOUNDARY_AU / abs_a) / eccentricity)
    travel_time = abs_a / v_inf * (eccentricity * math.sinh(H) - H)
    return entry_year + travel_time


timed_events = [(nominal_periapsis_time(event), event) for event in events]

for plot_year in (380.0, 925.0):
    print(f"\nNominal closest approaches nearest year {plot_year:.0f}")
    candidates = sorted(timed_events, key=lambda item: abs(item[0] - plot_year))
    for peri_year, event in candidates[:3]:
        entry_year, mass, speed, _, q_au, *_ = event
        print(
            f"  entry={entry_year:.2f} yr, closest approach ~{peri_year:.2f} yr, "
            f"q={q_au:.1f} AU, mass={mass:.3f} solar masses, "
            f"speed={speed:.1f} km/s"
        )
