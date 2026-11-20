"""Plot the Milky Way core stellar-mass sample and its Chabrier subset."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm


N_SAMPLES = 50_000
SEED = 20261116
MASS_MIN = 0.1  # Solar masses
MASS_MAX = 10.0

# x = log10(mass / solar mass). Chabrier (2003), Eq. (17).
X_MIN = np.log10(MASS_MIN)
X_MAX = np.log10(MASS_MAX)
CHABRIER_CENTER = np.log10(0.079)
CHABRIER_WIDTH = 0.69
CHABRIER = norm(loc=CHABRIER_CENTER, scale=CHABRIER_WIDTH)

# Salpeter: dN/dm is proportional to m^(-2.35), so dN/dx uses -1.35.
SALPETER_LOG_SLOPE = 1.35
TAIL_END = MASS_MAX ** (-SALPETER_LOG_SLOPE)
JOIN_HEIGHT = CHABRIER.pdf(0.0)

# Both branches use the same unnormalized density at x = 0 (one solar mass).
LOW_CDF_EDGE = CHABRIER.cdf(X_MIN)
LOW_AREA = CHABRIER.cdf(0.0) - LOW_CDF_EDGE
HIGH_AREA = JOIN_HEIGHT * (1 - TAIL_END) / (SALPETER_LOG_SLOPE * np.log(10))
TOTAL_AREA = LOW_AREA + HIGH_AREA


def sample_log_masses(rng, count):
    """Draw log10(mass / solar mass) from the joined IMF."""
    draws = rng.uniform(0, TOTAL_AREA, size=count)
    low_branch = draws < LOW_AREA
    log_masses = np.empty(count)

    # Invert the Chabrier CDF within the interval from 0.1 to 1 solar mass.
    log_masses[low_branch] = CHABRIER.ppf(LOW_CDF_EDGE + draws[low_branch])

    # Invert the power-law CDF within the interval from 1 to 10 solar masses.
    tail_fraction = (draws[~low_branch] - LOW_AREA) / HIGH_AREA
    log_masses[~low_branch] = -np.log10(1 - tail_fraction * (1 - TAIL_END)) / SALPETER_LOG_SLOPE
    return log_masses


def plot_mass_histogram(log_masses, upper_edge, area, title, subtitle, output):
    log_bins = np.linspace(X_MIN, upper_edge, 41 if upper_edge > 0 else 40)
    counts, _ = np.histogram(log_masses, bins=log_bins)
    sample_density = counts / (log_masses.size * np.diff(log_bins))

    x = np.linspace(X_MIN, upper_edge, 501)
    curve = np.where(
        x <= 0,
        CHABRIER.pdf(x),
        JOIN_HEIGHT * 10 ** (-SALPETER_LOG_SLOPE * x),
    ) / area

    # Compute the logarithms explicitly. Zero-count bins have no finite log.
    with np.errstate(divide="ignore"):
        log_density = np.log10(np.where(counts > 0, sample_density, np.nan))
    log_curve = np.log10(curve)
    y_min = min(log_curve.min(), np.nanmin(log_density)) - 0.09
    y_max = max(log_curve.max(), np.nanmax(log_density)) + 0.09

    fig, ax = plt.subplots(figsize=(8.8, 5.1), layout="constrained")
    ax.stairs(
        log_density, log_bins, baseline=y_min, fill=True,
        color="#b4d1e5", label="Sampled masses",
    )
    ax.plot(x, log_curve, color="#153c57", lw=2.1, label="Theoretical IMF")

    if upper_edge > 0:
        ax.axvline(0, color="#71828f", lw=1.05, ls="--", label=r"Join at $1\,M_\odot$")

    ax.set(
        xlim=(X_MIN - 0.025, upper_edge + 0.025),
        ylim=(y_min, y_max),
        xlabel=r"$\log_{10}(m_\star/M_\odot)$",
        ylabel=r"$\log_{10}(\mathrm{probability\ density\ per\ dex})$",
    )
    ax.set_xticks(np.linspace(X_MIN, upper_edge, 9 if upper_edge > 0 else 6))
    ax.set_title(subtitle, loc="left", fontsize=11, color="#435967", pad=11)
    fig.suptitle(title, fontsize=18, fontweight="semibold", color="#1b3446")
    ax.legend(loc="upper right", frameon=False)
    ax.set_axisbelow(True)
    ax.grid(axis="y", alpha=0.16)

    fig.savefig(output, dpi=210)
    plt.close(fig)
    print(f"Saved {output}")


def main():
    plt.rcParams.update({
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
    log_masses = sample_log_masses(np.random.default_rng(SEED), N_SAMPLES)
    chabrier_masses = log_masses[log_masses <= 0]

    print(
        f"At or below 1 solar mass: {len(chabrier_masses):,}/{N_SAMPLES:,} "
        f"({len(chabrier_masses) / N_SAMPLES:.2%}, "
        f"expected {LOW_AREA / TOTAL_AREA:.2%})"
    )

    plot_mass_histogram(
        log_masses, X_MAX, TOTAL_AREA,
        "Chabrier + Salpeter",
        f"Milky Way core sampling · {N_SAMPLES:,} draws from 0.1 to 10 solar masses",
        Path("core_mass_chabrier_salpeter_loglog.png"),
    )
    plot_mass_histogram(
        chabrier_masses, 0.0, LOW_AREA,
        "Chabrier low-mass branch",
        f"Milky Way core sampling · {len(chabrier_masses):,} draws from 0.1 to 1 solar mass",
        Path("core_mass_chabrier_only_loglog.png"),
    )


if __name__ == "__main__":
    main()