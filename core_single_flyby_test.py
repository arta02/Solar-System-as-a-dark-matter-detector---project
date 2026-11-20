import math

import rebound


NEPTUNE_MASS = 5.15e-5       # Solar masses
NEPTUNE_A = 30.069          # AU
NEPTUNE_E = 0.0086

STAR_MASS = 1.0             # Solar masses
V_INF_KMS = 402.83
Q_AU = 60.0
KMS_TO_AU_PER_YEAR = 365.25 * 86400 / 149_597_870.7
NEPTUNE_PHASE_AT_PASS = math.radians(45)


def run_encounter(start_radius, include_star=True):
    sim = rebound.Simulation()
    sim.units = ("yr", "AU", "Msun")
    sim.integrator = "ias15"
    sim.add(m=1.0)
    sun = sim.particles[0]

    # Set up the incoming two-body hyperbola about the Sun–Neptune barycentre.
    v_inf = V_INF_KMS * KMS_TO_AU_PER_YEAR
    mu = sim.G * (1.0 + NEPTUNE_MASS + STAR_MASS)
    abs_a = mu / v_inf**2
    e_star = 1 + Q_AU / abs_a
    cos_f = (Q_AU * (1 + e_star) / start_radius - 1) / e_star
    f_in = -math.acos(cos_f)

    # Calculate the nominal travel time from the start radius to periapsis.
    H = math.acosh((1 + start_radius / abs_a) / e_star)
    travel_time = abs_a / v_inf * (e_star * math.sinh(H) - H)

    # Match Neptune's unperturbed phase at the nominal time of the encounter.
    n_neptune = math.sqrt(sim.G * (1 + NEPTUNE_MASS) / NEPTUNE_A**3)
    initial_phase = (NEPTUNE_PHASE_AT_PASS - n_neptune * travel_time) % math.tau
    sim.add(primary=sun, m=NEPTUNE_MASS, a=NEPTUNE_A,
            e=NEPTUNE_E, M=initial_phase)

    if include_star:
        sim.add(
            primary=sim.com(), m=STAR_MASS, a=-abs_a, e=e_star,
            f=f_in, inc=math.radians(60), Omega=0.0, omega=0.0,
        )

    sim.move_to_com()
    a_before = sim.particles[1].orbit(primary=sim.particles[0]).a

    # Evolve past closest approach to the corresponding outbound time.
    sim.integrate(2 * travel_time)

    a_after = sim.particles[1].orbit(primary=sim.particles[0]).a
    return (a_after - a_before) / a_before


control = run_encounter(6000, include_star=False)
near = run_encounter(3000)
far = run_encounter(6000)

print(f"No-star control:        delta a/a = {control:+.6e}")
print(f"Start at   3,000 AU:    delta a/a = {near:+.6e}")
print(f"Start at   6,000 AU:    delta a/a = {far:+.6e}")
print(f"Absolute difference:               {abs(far - near):.6e}")