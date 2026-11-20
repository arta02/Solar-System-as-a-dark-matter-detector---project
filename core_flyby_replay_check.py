import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rebound


FOLDER = Path(__file__).resolve().parent
DURATION_YR = 1_000
DT_YR = 0.25
BOUNDARY_AU = 15_000.0
B_MAX_AU = 10_000
CUTOFFS_AU = (1_000, 2_000, 4_000, 6_000, 8_000)
TOLERANCE_FRACTION = 0.10

KMS_TO_AU_PER_YR = 365.25 * 86400 / 149_597_870.7
TIMES = np.arange(round(DURATION_YR / DT_YR) + 1) * DT_YR


def load_events():
    path = FOLDER / "core_live_flyby_events.csv"
    with path.open(newline="") as file:
        events = {}
        for row in csv.DictReader(file):
            event = {column: float(value) for column, value in row.items()}
            events[event["entry_time_yr"]] = event
    return events


def add_logged_star(sim, event):
    sun = sim.particles[0]
    mass = event["mass_msun"]
    v_inf = event["v_inf_kms"] * KMS_TO_AU_PER_YR
    b = event["b_au"]

    # Reconstruct the same incoming hyperbola as in the live pilot.
    abs_a = sim.G * (sun.m + mass) / v_inf**2
    eccentricity = math.hypot(1, b / abs_a)
    semilatus_rectum = b**2 / abs_a
    cos_f = (semilatus_rectum / BOUNDARY_AU - 1) / eccentricity

    sim.add(
        primary=sun,
        m=mass,
        a=-abs_a,
        e=eccentricity,
        f=-math.acos(cos_f),
        inc=event["inclination_rad"],
        Omega=event["node_rad"],
        omega=event["periapsis_rad"],
    )


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


def replay(events, max_b_au):
    sim = rebound.Simulation()
    sim.units = ("yr", "AU", "Msun")
    sim.integrator = "ias15"
    sim.add(m=1.0)

    # Reproduce the live pilot's initial Neptune phase of about 129.49 degrees.
    phase_rng = np.random.default_rng(20261118)
    phase = float(phase_rng.uniform(0, math.tau))
    sim.add(m=5.15e-5, a=30.069, e=0.0086, M=phase)
    sim.move_to_com()

    a_initial = sim.particles[1].orbit(primary=sim.particles[0]).a
    history = np.zeros(TIMES.size)

    for index, time in enumerate(TIMES[1:], start=1):
        sim.integrate(float(time))
        remove_departed_stars(sim)

        event = events.get(time)
        if event is not None and event["b_au"] <= max_b_au:
            add_logged_star(sim, event)

        a_now = sim.particles[1].orbit(primary=sim.particles[0]).a
        history[index] = (a_now - a_initial) / a_initial

    return history


def main():
    events = load_events()
    full = replay(events, B_MAX_AU)
    tolerance = TOLERANCE_FRACTION * np.max(np.abs(full))

    print(f"Events in the original catalogue: {len(events)}")
    print(f"Full replay at {DURATION_YR:,} yr: {full[-1]:+.6e}")
    print("Original live run:         +2.371642e-06")
    print(f"Allowed difference anywhere in the pilot: {tolerance:.3e}\n")

    chosen_cutoff = B_MAX_AU
    chosen_history = full
    chosen_count = len(events)

    for cutoff in CUTOFFS_AU:
        retained = sum(event["b_au"] <= cutoff for event in events.values())
        screened = replay(events, cutoff)
        error = np.max(np.abs(screened - full))
        passed = error <= tolerance
        status = "PASS" if passed else "FAIL"

        print(
            f"b <= {cutoff:>5,} AU | kept {retained:>2}/{len(events)} stars "
            f"| largest difference {error:.3e} | {status}"
        )

        if passed:
            chosen_cutoff = cutoff
            chosen_history = screened
            chosen_count = retained
            break

    print(f"\nSelected for this pilot: b <= {chosen_cutoff:,} AU "
          f"({chosen_count}/{len(events)} stars)")

    fig, ax = plt.subplots(figsize=(9, 4.6), layout="constrained")
    ax.plot(TIMES, full, color="#153c57", lw=2, label="Full catalogue")

    if chosen_cutoff < B_MAX_AU:
        ax.plot(
            TIMES, chosen_history, color="#b35c35", ls="--",
            label=f"Screened catalogue, b ≤ {chosen_cutoff:,} AU",
        )

    ax.set(
        xlabel="Time (years)",
        ylabel=r"Neptune's signed $\Delta a/a_0$",
        title="Milky Way core | automatic impact-parameter screening",
    )
    ax.legend(frameon=False)

    output = FOLDER / "core_flyby_screening_check.png"
    fig.savefig(output, dpi=200)
    plt.close(fig)
    print(f"Saved {output.name}")


if __name__ == "__main__":
    main()