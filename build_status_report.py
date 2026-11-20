from io import BytesIO
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt


folder = Path(__file__).resolve().parent
deck = Presentation()
deck.slide_width = Inches(13.333)
deck.slide_height = Inches(7.5)

navy = "142F45"
ink = "173246"
muted = "4A6274"
teal = "007B80"
light = "E7F0F3"
paper = "F7FAFC"
white = "FFFFFF"
missing = set()


def rgb(hex_color):
    return RGBColor.from_string(hex_color)


def text(slide, value, x, y, w, h, size=18, color=ink, bold=False):
    frame = slide.shapes.add_textbox(
        Inches(x), Inches(y), Inches(w), Inches(h)
    ).text_frame
    frame.word_wrap = True
    frame.margin_left = frame.margin_right = Pt(0)
    frame.margin_top = frame.margin_bottom = Pt(0)
    for index, line in enumerate(value.split("\n")):
        paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
        paragraph.text = line
        paragraph.space_after = Pt(5)
        paragraph.font.name = "DejaVu Sans"
        paragraph.font.size = Pt(size)
        paragraph.font.bold = bold
        paragraph.font.color.rgb = rgb(color)


def rect(slide, x, y, w, h, fill):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.fill.background()


def new_slide(section, title, notes, source=""):
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(paper)
    rect(slide, 0, 0, 13.333, 0.08, teal)
    text(slide, section.upper(), 0.65, 0.37, 11.9, 0.24, 10, teal, True)
    text(slide, title, 0.65, 0.79, 12.0, 0.75, 28, navy, True)
    rect(slide, 0.65, 6.98, 12.05, 0.015, "CAD8E0")
    text(slide, source or "Quantum Universe · University of Hamburg",
         0.65, 7.09, 11.35, 0.24, 9, muted)
    text(slide, str(len(deck.slides)), 12.28, 7.09, 0.42, 0.24, 9, muted)
    slide.notes_slide.notes_text_frame.text = notes
    return slide


def card(slide, x, y, w, h, title, body, title_size=19, body_size=16):
    rect(slide, x, y, w, h, light)
    text(slide, title, x + 0.23, y + 0.22, w - 0.46, 0.65,
         title_size, navy, True)
    text(slide, body, x + 0.23, y + 0.99, w - 0.46, h - 1.08,
         body_size, ink)


def fit_image(slide, image, x, y, w, h):
    scale = min(w / image.width, h / image.height)
    width, height = image.width * scale, image.height * scale
    stream = BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    slide.shapes.add_picture(
        stream, Inches(x + (w - width) / 2), Inches(y + (h - height) / 2),
        width=Inches(width), height=Inches(height),
    )


def load_image(filename):
    path = folder / filename
    if not path.is_file():
        missing.add(filename)
        return None
    with Image.open(path) as opened:
        return opened.convert("RGB")


def picture_or_card(slide, filename, x, y, w, h, heading, description):
    image = load_image(filename)
    if image is None:
        card(slide, x, y, w, h, heading, description)
    else:
        fit_image(slide, image, x, y, w, h)


def top_panel_with_time_axis(image):
    """Keep the upper subplot and transplant the shared x-axis labels."""
    width, height = image.size
    gray = image.convert("L")

    def horizontal_axis(low, high):
        xs = range(int(0.20 * width), int(0.85 * width), 4)
        found = [
            y for y in range(int(low * height), int(high * height))
            if sum(gray.getpixel((x, y)) < 95 for x in xs) >= 0.85 * len(xs)
        ]
        return found[-1] if found else None

    upper = horizontal_axis(0.38, 0.49)
    lower = horizontal_axis(0.78, 0.96)
    if upper is None or lower is None:
        return None

    panel = image.crop((0, 0, width, upper + 6))
    tick_labels = image.crop((0, lower + 4, width, height))
    out = Image.new("RGB", (width, panel.height + tick_labels.height), "white")
    out.paste(panel, (0, 0))
    out.paste(tick_labels, (0, panel.height))
    return out


# Shared introduction. Insert the partner's analytical section after slide 3.
slide = new_slide(
    "Project Seminar Part I · Status reports",
    "Solar System as a Dark Matter Detector",
    "Introduce the shared project title. The long-term question concerns compact "
    "objects passing through the Solar System. Today we report progress on the "
    "analytical work and the numerical stellar-flyby baseline.",
)
rect(slide, 0.65, 1.95, 12.05, 3.88, navy)
text(slide, "Compact-object flybys\nand planetary stability",
     1.02, 2.57, 10.9, 1.38, 32, white, True)
text(slide, "Arta Iljazi · Numerical status report",
     1.04, 4.53, 11, 0.46, 19, "BFE8E8")

slide = new_slide(
    "Shared introduction",
    "What could a passing compact object tell us?",
    "The broader goal is to understand whether planetary orbital stability can "
    "constrain populations of compact objects. Neptune’s semimajor axis is the "
    "observable in the numerical baseline. Mercury’s long-term response is a "
    "later stage of the project.",
    "Project scope · Brown & Rein (2022)",
)
card(slide, 0.65, 1.91, 3.85, 3.40, "Passing object",
     "A flyby gravitationally perturbs the orbits of planets.")
card(slide, 4.75, 1.91, 3.85, 3.40, "Measurable response",
     "Track the fractional change in Neptune’s semimajor axis, Δa/a₀.")
card(slide, 8.85, 1.91, 3.85, 3.40, "Long-term question",
     "Investigate what planetary stability can tell us about compact flybys.")

slide = new_slide(
    "Shared introduction",
    "Two parts of today’s status report",
    "Hand off to the analytical presenter after this slide. After the partner’s "
    "slides, resume with Milky Way core inputs and the REBOUND setup.",
)
card(slide, 0.65, 2.02, 5.86, 3.45, "Analytical work",
     "Estimate the perturbation from a passing object and identify which "
     "encounter parameters control the response.")
card(slide, 6.83, 2.02, 5.87, 3.45, "Numerical work",
     "Generate stellar flybys in the Milky Way core and follow Neptune "
     "through a sequence of overlapping encounters.")

# Arta's numerical section.
slide = new_slide(
    "Numerical setup",
    "Milky Way core inputs",
    "The stellar population is the baseline for this status report. We chose "
    "0.1–10 solar masses. We interpreted 170 km/s as the standard deviation "
    "of the Maxwell speed magnitude, giving a mean of 402.83 km/s. The 10,000 AU "
    "impact-parameter limit sets the cross-section. Stars enter the integrator "
    "at 15,000 AU.",
    "Brown & Rein (2022), Table 1 and §2.2 · Project sampling choices",
)
card(slide, 0.65, 1.75, 5.86, 2.14, "Stellar population",
     "Density 10,000 pc⁻³ · masses 0.1–10 M☉")
card(slide, 6.83, 1.75, 5.87, 2.14, "Incoming speeds",
     "Maxwell–Boltzmann · standard deviation 170 km/s")
card(slide, 0.65, 4.12, 5.86, 2.14, "Encounter geometry",
     "Uniform in area · bₘₐₓ = 10,000 AU · isotropic orientations")
card(slide, 6.83, 4.12, 5.87, 2.14, "Numerical model",
     "Sun + Neptune + active flyby stars · REBOUND / IAS15")

slide = new_slide(
    "Input checks",
    "The sampled masses and speeds follow the target curves",
    "On the mass plot, the Chabrier lognormal curves below one solar mass and "
    "the Salpeter tail is a straight line. Its plotted slope is −1.35 for "
    "density per dex, equivalent to −2.35 per unit mass. On the speed plot, "
    "the peak is about 357 km/s and the theoretical mean is 402.83 km/s. "
    "The faster stars in the tail pull the mean to the right of the peak.",
    "Chabrier (2003), Eq. 17 · Salpeter (1955) · 50,000 draws per check",
)
picture_or_card(slide, "core_mass_chabrier_salpeter_loglog.png",
                0.65, 1.74, 5.87, 3.69, "Chabrier + Salpeter",
                "88.55% sampled at or below 1 M☉ · 88.61% expected")
picture_or_card(slide, "core_velocity_distribution.png",
                6.83, 1.74, 5.87, 3.69, "Maxwell–Boltzmann",
                "402.59 km/s sampled mean · 402.83 km/s expected")
text(slide, "Masses · 44,277 of 50,000 draws at or below 1 M☉",
     0.76, 5.69, 5.64, 0.56, 14, muted)
text(slide, "Speeds · 402.59 km/s sampled mean · KS p = 0.953",
     6.94, 5.69, 5.64, 0.56, 14, muted)

slide = new_slide(
    "Numerical method",
    "Random flyby arrivals, continuous Neptune phase",
    "Each line marks an accepted time step. For the live integration, that "
    "time is when the star enters the 15,000 AU sphere. The catalogue step "
    "is 0.25 years and IAS15 takes its own internal steps. Neptune’s starting "
    "mean anomaly was 129.49 degrees for this seed. Its actual state evolves "
    "continuously, including when multiple stars are active.",
    "Zink, Batygin & Adams (2020), §2.3 · REBOUND / IAS15",
)
picture_or_card(slide, "core_flyby_timeline.png",
                0.65, 1.63, 12.05, 2.80, "First 1,000 years of arrival times",
                "25 arrivals in this window · expected 30.4 · gaps vary randomly")
card(slide, 0.65, 4.60, 5.86, 2.05, "Arrival rule",
     "Accept if U < ΓΔt · Δt = 0.25 yr\nMean gap 1/Γ = 32.87 yr", body_size=14)
card(slide, 6.83, 4.60, 5.87, 2.05, "Neptune’s phase",
     "Draw the initial phase once.\nCarry position and velocity forward.", body_size=14)

slide = new_slide(
    "Numerical checks",
    "The control and close-flyby checks agree",
    "The no-star Sun–Neptune control stayed constant at printed precision. "
    "For the controlled close flyby, we used a one-solar-mass star, "
    "402.83 km/s and nominal q = 60 AU. We adjusted the initial phase "
    "when changing the start radius to match the nominal encounter geometry. "
    "The long run then reproduced the pilot at year 1,000 for the same seed.",
)
card(slide, 0.65, 1.94, 3.85, 3.75, "No-star control",
     "Δa/a₀ = 0 at the printed precision")
card(slide, 4.75, 1.94, 3.85, 3.75, "One close flyby",
     "Δa/a₀ ≈ −1.48%\nStarting at 3,000 vs 6,000 AU changed Δa/a₀ by 4.69 × 10⁻⁷")
card(slide, 8.85, 1.94, 3.85, 3.75, "100 kyr replay check",
     "At year 1,000 the run reproduced the pilot:\nΔa/a₀ = +2.371642 × 10⁻⁶",
     title_size=17, body_size=15)

slide = new_slide(
    "Main numerical result",
    "One 100,000-year history reached 63% of the threshold",
    "Show the signed change in Neptune’s semimajor axis. The largest absolute "
    "excursion was 6.254796 × 10⁻⁴. There was no sampled crossing of 10⁻³. "
    "We drew 3,061 arrivals versus 3,042.1 expected, with at most 26 stars "
    "active at once. At the endpoint Δa/a₀ was +5.833626 × 10⁻⁴, with 13 "
    "stars still active. This is one history.",
    "Full Milky Way core run · bₘₐₓ = 10,000 AU · 0.25 yr sampling cadence",
)
raw = load_image("core_live_flyby_100k.png")
main_figure = top_panel_with_time_axis(raw) if raw is not None else None
if main_figure is not None:
    fit_image(slide, main_figure, 0.65, 1.72, 8.35, 4.69)
else:
    if raw is not None:
        print("Could not isolate the upper panel in core_live_flyby_100k.png.")
    text(slide, "Peak relative to the project threshold",
         0.82, 2.27, 8.0, 0.6, 22, navy, True)
    rect(slide, 0.83, 3.20, 7.88, 0.52, light)
    rect(slide, 0.83, 3.20, 7.88 * 0.6254796, 0.52, teal)
    text(slide, "0", 0.83, 3.88, 1.3, 0.4, 14, muted)
    text(slide, "Threshold 10⁻³", 6.65, 3.88, 2.15, 0.4, 14, muted)
    text(slide, "Observed peak · 62.5% of threshold",
         0.83, 4.52, 7.9, 0.7, 20, navy, True)
card(slide, 9.29, 1.94, 3.41, 4.22, "Run summary",
     "3,061 stellar arrivals\n3,042 expected\n\nPeak |Δa/a₀| = 6.25 × 10⁻⁴\n\n"
     "No sampled crossing of 10⁻³", body_size=15)

slide = new_slide(
    "Status and next steps",
    "From one history to first-crossing statistics",
    "The 100 kyr run is an individual outcome. Across many independent histories "
    "we will record the first time the threshold is exceeded, or the simulated "
    "duration when no crossing is seen. A same-catalogue replay with tighter "
    "IAS15 accuracy can check the measured peak and threshold outcome.",
)
card(slide, 0.65, 1.96, 5.86, 3.80, "Completed",
     "Input sampling checks\nControlled close-flyby check\n"
     "Full 100 kyr live history with overlapping encounters")
card(slide, 6.83, 1.96, 5.87, 3.80, "Next",
     "Check numerical sensitivity on a fixed catalogue\n"
     "Run independent histories\nEstimate the distribution of first-crossing times")

# Backup slides.
slide = new_slide(
    "Backup · geometry",
    "Orientation and impact-parameter checks",
    "Cosine of inclination is uniform on [−1,1]. The node and argument of "
    "periapsis are uniform over the full circle. Drawing b = b_max sqrt(U) "
    "makes b squared uniform and samples equal areas equally. Half the "
    "maximum radius encloses one-quarter of the sampling area.",
)
picture_or_card(slide, "core_orientation_final.png",
                0.65, 1.67, 12.05, 2.19, "Isotropic orientations",
                "Uniform cos i and full-circle Ω and ω")
picture_or_card(slide, "core_impact_parameter_squared.png",
                2.22, 3.96, 6.55, 2.84, "Uniform in area",
                "(b/bₘₐₓ)² is flat from 0 to 1")
text(slide, "Half the radius\n→ one-quarter of the area",
     9.10, 4.72, 3.57, 1.19, 18, teal, True)

slide = new_slide(
    "Backup · pilot",
    "The 1,000-year run exercised overlapping flybys",
    "The upper panel shows Neptune’s signed response. The lower panel is the "
    "number of stars inside the integration sphere. The number of active stars "
    "peaked at 14. Two prominent changes are visible near years 380 and 925.",
)
picture_or_card(slide, "core_live_flyby_pilot.png",
                0.65, 1.60, 8.74, 5.16, "Pilot orbit and active stars",
                "Peak |Δa/a₀| = 4.48 × 10⁻⁶")
card(slide, 9.62, 2.05, 3.08, 3.83, "Pilot summary",
     "25 arrivals\n14 stars active at once\nPeak |Δa/a₀| = 4.48 × 10⁻⁶",
     body_size=15)

slide = new_slide(
    "Backup · runtime",
    "The screening test used one short history",
    "The full 1,000-year replay recovered the live result. Keeping only the "
    "two b ≤ 2,000 AU stars reproduced the major changes in that history. "
    "The maximum difference was 2.193 × 10⁻⁷, 4.9% of the full pilot peak. "
    "The 100 kyr run used the full 10,000 AU catalogue.",
)
picture_or_card(slide, "core_flyby_screening_check.png",
                0.65, 1.63, 8.73, 5.12, "Pilot screening comparison",
                "Maximum difference 2.19 × 10⁻⁷")
card(slide, 9.62, 2.07, 3.08, 3.85, "Pilot result",
     "2 of 25 stars retained\n4.9% maximum difference relative to the pilot peak\n"
     "Full range used in 100 kyr", body_size=14)

slide = new_slide(
    "Backup · assumptions",
    "Encounter rate and the published benchmark",
    "The rate here follows the geometric cross-section and our stated speed "
    "interpretation. Brown and Rein’s Table 1 lists a core waiting time of "
    "11.7 years for their setup. We still need to resolve the difference "
    "before presenting a direct quantitative comparison.",
    "Brown & Rein (2022), Table 1 · Zink et al. (2020), Eq. 2",
)
card(slide, 0.65, 1.89, 5.86, 3.93, "Rate in this run",
     "Γ = nπbₘₐₓ²⟨v∞⟩\nΓ = 0.03042 yr⁻¹\nMean gap = 32.87 yr")
card(slide, 6.83, 1.89, 5.87, 3.93, "Published comparison",
     "Brown & Rein core entry: 11.7 yr\n"
     "The difference in rate conventions is an open comparison.")

slide = new_slide(
    "Backup · sources",
    "References",
    "Brown and Rein provide the project’s starting point for weak stellar "
    "flybys. Zink and collaborators provide the arrival rule. Chabrier and "
    "Salpeter define the two pieces of our adopted stellar mass distribution.",
)
text(slide,
     "Brown & Rein (2022), MNRAS 515, 5942–5950 · doi.org/10.1093/mnras/stac1763\n"
     "Zink, Batygin & Adams (2020), AJ 160, 232 · doi.org/10.3847/1538-3881/abb8de\n"
     "Chabrier (2003), PASP 115, 763–795 · Eq. 17\n"
     "Salpeter (1955), ApJ 121, 161\n"
     "Rein & Liu (2012), A&A 537, A128 · REBOUND",
     0.77, 1.95, 11.8, 3.9, 18)

output = folder / "Quantum_Universe_Status_Report_Arta.pptx"
deck.save(output)
print(f"Saved {output}")
for filename in sorted(missing):
    print(f"Used an editable summary in place of {filename}.")
