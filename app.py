"""
SThM Wheatstone Bridge Simulator
---------------------------------
An interactive teaching/research tool that models the response of a
Scanning Thermal Microscopy (SThM) probe placed in one arm of a
Wheatstone bridge.

Author: open source release
License: MIT
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import streamlit as st

# ----------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="SThM Wheatstone Bridge Simulator - RISE Lab",
    page_icon="🌡️",
    layout="wide",
)

st.markdown("""<style>
/* layout */
.block-container{padding-top:3.5rem !important;padding-bottom:0 !important;max-width:100% !important;}
section[data-testid="stSidebar"] .block-container{padding-top:0.6rem !important;}

/* subheaders */
h3{margin-top:0.2rem !important;margin-bottom:0.25rem !important;font-size:1rem !important;}

/* metrics — tighter */
div[data-testid="stMetric"]{padding:0.1rem 0.25rem !important;
    background:#f8f9fb;border-radius:6px;border:1px solid #e8eaf0;}
div[data-testid="stMetricLabel"]>div{font-size:0.7rem !important;color:#555 !important;}
div[data-testid="stMetricValue"]{font-size:1.05rem !important;font-weight:600 !important;}

/* expander */
details summary{font-size:0.85rem !important;}
</style>""", unsafe_allow_html=True)

st.markdown(
    """<div style="background:#1a3a5c;border-radius:6px;padding:0.45rem 1rem;
        margin-bottom:0.4rem;display:flex;align-items:baseline;
        column-gap:1rem;flex-wrap:wrap;row-gap:0.1rem;">
      <span style="font-size:1.05rem;font-weight:700;color:#ffffff;
                   letter-spacing:0.02em;white-space:nowrap;">
        SThM Wheatstone Bridge Simulator
      </span>
      <span style="font-size:0.72rem;color:#a8c4e0;white-space:nowrap;">
        Passive SThM probe &nbsp;·&nbsp; Wheatstone bridge response
      </span>
    </div>""",
    unsafe_allow_html=True,
)

# Initialize session state for parameters
if "params" not in st.session_state:
    st.session_state.params = {
        "Vin": 1.0,
        "R1": 1000,
        "R2": 1000,
        "R3": 350,
        "Rp0": 330,
        "alpha": 3.8e-3,
        "dT0": 10,
        "Rth_MKW": 1.0,
        "k_sample": 1.4
    }


# ----------------------------------------------------------------------
# Physics
# ----------------------------------------------------------------------
def tip_sample_conductance(k_sample, G0=2.0e-9, beta=5.0e-8):
    """
    Effective tip-to-sample thermal conductance G_tip (W/K).

    Parameters
    ----------
    k_sample : float or array
        Sample thermal conductivity (W m^-1 K^-1).
    G0 : float
        Baseline conductance through air gap / radiation (no contact).
    beta : float
        Coupling slope: how strongly G_tip rises with k_sample.

    Notes
    -----
    A simple linear model. Real tip-sample conductance follows a
    constriction / ballistic / diffusive resistance network with
    saturation at high k. We capture saturation downstream by combining
    G_tip in parallel with the probe's own conductance G_probe.
    """
    return G0 + beta * np.asarray(k_sample, dtype=float)


def probe_temperature_rise(dT0, G_probe, G_tip):
    """
    Steady-state probe temperature rise above ambient (K).

    Heat balance:
        P_joule = (G_probe + G_tip) * dT
        in free air (G_tip ~ 0): dT = dT0 = P_joule / G_probe
    Therefore:
        dT = dT0 * G_probe / (G_probe + G_tip)
    """
    return dT0 * G_probe / (G_probe + G_tip)


def probe_resistance(Rp0, alpha, dT):
    """
    Linear TCR model:  R_p = R_p0 * (1 + alpha * dT).
    """
    return Rp0 * (1.0 + alpha * dT)


def bridge_imbalance(Vin, R1, R2, R3, Rp):
    """
    Wheatstone bridge with R1, R2 on the top half and R3, Rp on the
    bottom half (probe in the bottom-right arm).

        V_AB = Vin * [ R3 / (R1 + R3)  -  Rp / (R2 + Rp) ]

    Balance condition: R1 * Rp = R2 * R3.
    """
    return Vin * (R3 / (R1 + R3) - Rp / (R2 + Rp))


def simulate(Vin, R1, R2, R3, Rp0, alpha, dT0, Rth, k_sample):
    """Run the full bridge + probe model for a single operating point."""
    G_probe = 1.0 / Rth
    G_tip = tip_sample_conductance(k_sample)
    dT = probe_temperature_rise(dT0, G_probe, G_tip)
    Q = G_tip * dT                       # heat flowing into the sample (W)
    Rp = probe_resistance(Rp0, alpha, dT)
    Vab = bridge_imbalance(Vin, R1, R2, R3, Rp)
    return dict(G_probe=G_probe, G_tip=G_tip, dT=dT, Q=Q, Rp=Rp, Vab=Vab)


# ----------------------------------------------------------------------
# Sidebar controls
# ----------------------------------------------------------------------
st.sidebar.header("Bridge excitation")
st.session_state.params["Vin"] = st.sidebar.slider("Input voltage  V_in  (V)",
                        0.1, 10.0, st.session_state.params["Vin"], 0.1)
Vin = st.session_state.params["Vin"]

st.sidebar.header("Balance arms (fixed resistors)")
st.session_state.params["R1"] = st.sidebar.slider("R₁ (Ω)", 100, 5000, st.session_state.params["R1"], 10)
R1 = st.session_state.params["R1"]

if "R2_value" not in st.session_state:
    st.session_state.R2_value = st.session_state.params["R2"]
st.sidebar.slider("R₂ — null trim (Ω)", 100, 5000, step=1,
                  key="R2_value",
                  help="Real SThM bridges include a trim resistor so the "
                       "bridge can be nulled in free air before contact. "
                       "Use the Auto-null button to do that automatically.")
R2 = st.session_state.R2_value
st.session_state.params["R2"] = R2

st.session_state.params["R3"] = st.sidebar.slider("R₃ (Ω)", 100, 5000, st.session_state.params["R3"], 10)
R3 = st.session_state.params["R3"]

st.sidebar.header("SThM probe (active arm)")
st.session_state.params["Rp0"] = st.sidebar.slider("R_probe,0 at 25 °C (Ω)", 100, 3000, st.session_state.params["Rp0"], 10)
Rp0 = st.session_state.params["Rp0"]

st.session_state.params["alpha"] = st.sidebar.slider(
    "Temperature coefficient α (1/K)",
    1e-4, 5e-3, st.session_state.params["alpha"], 1e-4, format="%.4f",
    help="Pd nanowire ≈ 1.7e-3, doped Si ≈ 1.5e-3, Pt ≈ 3.9e-3"
)
alpha = st.session_state.params["alpha"]

st.session_state.params["dT0"] = st.sidebar.slider(
    "Free-air probe heating  ΔT₀ (K)",
    10, 200, st.session_state.params["dT0"], 1,
    help="Probe self-heating above ambient when no sample is touching it"
)
dT0 = st.session_state.params["dT0"]

st.session_state.params["Rth_MKW"] = st.sidebar.slider(
    "Cantilever thermal resistance R_th (MK/W)",
    0.5, 20.0, st.session_state.params["Rth_MKW"], 0.1,
    help="Heat path from probe tip up the cantilever to the chip body"
)
Rth_MKW = st.session_state.params["Rth_MKW"]
Rth = Rth_MKW * 1e6  # convert MK/W -> K/W

st.sidebar.header("Sample under tip")
preset = st.sidebar.selectbox(
    "Preset material",
    options=[
        ("Custom", None),
        ("Air (no contact)", 0.0),
        ("Aerogel", 0.02),
        ("Polymer (PMMA)", 0.19),
        ("Glass", 1.4),
        ("Sapphire", 35.0),
        ("Silicon", 150.0),
        ("Copper", 400.0),
        ("Diamond", 2000.0),
    ],
    format_func=lambda x: x[0],
    index=4,
)
if preset[1] is None:
    st.session_state.params["k_sample"] = st.sidebar.slider(
        "Sample thermal conductivity  k  (W/m·K)",
        0.0, 2500.0, st.session_state.params["k_sample"], 0.1,
    )
    k_sample = st.session_state.params["k_sample"]
else:
    k_sample = preset[1]
    st.session_state.params["k_sample"] = k_sample
    st.sidebar.caption(f"k = {k_sample} W/m·K")

def _auto_null():
    """Set R2 so the bridge is balanced when the probe is in free air."""
    G_probe = 1.0 / Rth
    G_tip_air = tip_sample_conductance(0.0)
    dT_air = probe_temperature_rise(dT0, G_probe, G_tip_air)
    Rp_air = probe_resistance(Rp0, alpha, dT_air)
    new_R2 = max(100, min(5000, int(round(R1 * Rp_air / R3))))
    st.session_state.R2_value = new_R2
    st.session_state.params["R2"] = new_R2

st.sidebar.button(
    "Auto-null bridge (in air)",
    on_click=_auto_null,
    help="Sets R₂ so V_AB = 0 with the probe in air. "
         "Then bring the tip into contact and the SThM signal is the "
         "deviation from this null.",
)


# ----------------------------------------------------------------------
# Run the simulation at the operating point
# ----------------------------------------------------------------------
state = simulate(Vin, R1, R2, R3, Rp0, alpha, dT0, Rth, k_sample)


# ----------------------------------------------------------------------
# Layout: left = schematic + metrics, right = physics + plot
# ----------------------------------------------------------------------
col_left, col_right = st.columns([1.05, 1.0], gap="large")


# ----------------------------------------------------------------------
# Bridge schematic (matplotlib)
# ----------------------------------------------------------------------
def draw_bridge(ax, R1, R2, R3, Rp, Vin, Vab, Q, k_sample):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.set_aspect("equal")
    ax.axis("off")

    top = (5.0, 6.3)
    bot = (5.0, 0.7)
    left = (1.5, 3.5)
    right = (8.5, 3.5)

    def line(p, q, **kw):
        ax.plot([p[0], q[0]], [p[1], q[1]], color="#222", lw=1.2, **kw)

    line(top, left)
    line(top, right)
    line(left, bot)
    line(right, bot)

    def res_box(center, label, val_label, color="#f2f2ee", edge="#888"):
        x, y = center
        w, h = 1.1, 0.55
        rect = mpatches.FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=0.7, edgecolor=edge, facecolor=color,
        )
        ax.add_patch(rect)
        ax.text(x, y + 0.02, label, ha="center", va="center",
                fontsize=10, fontweight="bold")
        ax.text(x, y - 0.55, val_label, ha="center", va="center",
                fontsize=8.5, color="#444")

    res_box(((top[0] + left[0]) / 2 + 0.6,
             (top[1] + left[1]) / 2 + 0.2),
            "R₁", f"{R1:.0f} Ω")
    res_box(((top[0] + right[0]) / 2 - 0.6,
             (top[1] + right[1]) / 2 + 0.2),
            "R₂", f"{R2:.0f} Ω")
    res_box(((left[0] + bot[0]) / 2 + 0.6,
             (left[1] + bot[1]) / 2 - 0.2),
            "R₃", f"{R3:.0f} Ω")
    res_box(((right[0] + bot[0]) / 2 - 0.6,
             (right[1] + bot[1]) / 2 - 0.2),
            "SThM probe", f"{Rp:.1f} Ω",
            color="#FAECE7", edge="#D85A30")

    # voltage source
    src = mpatches.Circle(top, 0.28, facecolor="white",
                          edgecolor="#222", lw=1)
    ax.add_patch(src)
    ax.text(top[0], top[1], "+", ha="center", va="center", fontsize=11)
    ax.text(top[0], top[1] + 0.55, f"V$_{{in}}$ = {Vin:.1f} V",
            ha="center", fontsize=9.5, fontweight="bold")

    gnd = mpatches.Circle(bot, 0.28, facecolor="white",
                          edgecolor="#222", lw=1)
    ax.add_patch(gnd)
    ax.text(bot[0], bot[1], "−", ha="center", va="center", fontsize=11)
    ax.text(bot[0], bot[1] - 0.5, "ground", ha="center",
            fontsize=8.5, color="#666")

    # galvanometer between A and B
    gal = mpatches.Circle((5.0, 3.5), 0.45, facecolor="white",
                          edgecolor="#222", lw=1)
    ax.add_patch(gal)
    ax.text(5.0, 3.5, "G", ha="center", va="center",
            fontsize=11, fontweight="bold")
    ax.plot([left[0], 4.55], [left[1], 3.5], "--",
            color="#444", lw=0.8)
    ax.plot([5.45, right[0]], [3.5, right[1]], "--",
            color="#444", lw=0.8)
    ax.text(left[0] - 0.05, left[1] + 0.3, "A",
            ha="right", fontsize=9, color="#444")
    ax.text(right[0] + 0.05, right[1] + 0.3, "B",
            ha="left", fontsize=9, color="#444")
    ax.text(5.0, 2.8, f"V$_{{AB}}$ = {Vab*1000:.3f} mV",
            ha="center", fontsize=9.5, color="#0C447C",
            fontweight="bold")

    # sample under probe
    sx, sy = (right[0] + bot[0]) / 2 - 0.2, (right[1] + bot[1]) / 2 - 1.5
    sw, sh = 2.1, 0.6
    sample = mpatches.FancyBboxPatch(
        (sx - sw / 2, sy - sh / 2), sw, sh,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=0.7, edgecolor="#185FA5", facecolor="#E6F1FB",
    )
    ax.add_patch(sample)
    label = sample_label(k_sample)
    ax.text(sx, sy, f"{label}  (k = {k_sample:.2f})",
            ha="center", va="center", fontsize=8.5, color="#0C447C")
    ax.plot([sx, sx], [sy + sh / 2, sy + sh / 2 + 0.45],
            "--", color="#888", lw=0.8)
    ax.text(sx + 1.1, sy + 0.55, f"Q = {Q*1e6:.2f} µW",
            ha="left", fontsize=8.5, color="#993C1D")


def sample_label(k):
    if k < 0.05:
        return "air"
    if k < 0.5:
        return "polymer"
    if k < 5:
        return "glass"
    if k < 50:
        return "ceramic"
    if k < 250:
        return "silicon"
    return "metal"


# ----------------------------------------------------------------------
# Left column — schematic + key numbers
# ----------------------------------------------------------------------
with col_left:
    st.subheader("Bridge schematic")
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    draw_bridge(ax, R1, R2, R3, state["Rp"], Vin,
                state["Vab"], state["Q"], k_sample)
    fig.tight_layout()
    st.pyplot(fig, clear_figure=True)

    m1, m2, m3 = st.columns(3)
    m1.metric("Probe ΔT", f"{state['dT']:.2f} K",
              help="Steady-state temperature rise of the heated probe "
                   "while it is in contact with the sample.")
    m2.metric("Heat flux Q", f"{state['Q']*1e6:.2f} µW",
              help="Heat leaving the probe through the tip into the sample.")
    m3.metric("V_AB", f"{state['Vab']*1000:.3f} mV",
              help="Bridge imbalance voltage — the SThM signal.")

    m4, m5 = st.columns(2)
    m4.metric("Probe resistance", f"{state['Rp']:.2f} Ω")
    m5.metric("ΔR_p / R_p,0", f"{(state['Rp']-Rp0)/Rp0*100:.3f} %")


# ----------------------------------------------------------------------
# Right column — sweep plot + collapsible equations
# ----------------------------------------------------------------------
with col_right:
    st.subheader("V_AB vs sample thermal conductivity")

    k_grid = np.logspace(-2, np.log10(2500), 240)
    Vab_grid = np.array(
        [simulate(Vin, R1, R2, R3, Rp0, alpha, dT0, Rth, kk)["Vab"]
         for kk in k_grid]
    ) * 1000.0  # mV

    fig2, ax2 = plt.subplots(figsize=(6.0, 2.8))
    ax2.semilogx(k_grid, Vab_grid, color="#D85A30", lw=1.6)
    ax2.fill_between(k_grid, Vab_grid, 0, color="#D85A30", alpha=0.10)
    ax2.axhline(0, color="#888", lw=0.5)
    ax2.scatter([max(k_sample, 1e-2)],
                [state["Vab"] * 1000],
                color="#185FA5", s=55, zorder=5,
                label=f"k = {k_sample:.2f} W/m·K")
    ax2.set_xlabel("k  (W m⁻¹ K⁻¹, log scale)", fontsize=8)
    ax2.set_ylabel("V$_{AB}$  (mV)", fontsize=8)
    ax2.tick_params(labelsize=7)
    ax2.grid(True, which="both", alpha=0.25, lw=0.4)
    ax2.legend(loc="best", frameon=False, fontsize=8)
    fig2.tight_layout()
    st.pyplot(fig2, clear_figure=True)

    with st.expander("Governing physics"):
        st.markdown("**1. Bridge imbalance**")
        st.latex(r"V_{AB} = V_{in}\!\left[\frac{R_3}{R_1+R_3} - \frac{R_p}{R_2+R_p}\right]")
        st.markdown(r"Balanced when $R_1 R_p = R_2 R_3$.")

        st.markdown("**2. Probe TCR**")
        st.latex(r"R_p = R_{p,0}(1+\alpha\,\Delta T)")

        st.markdown("**3. Heat balance**")
        st.latex(r"\Delta T = \Delta T_0\cdot\frac{G_{probe}}{G_{probe}+G_{tip}(k)}")

        st.markdown("**4. Tip-sample conductance**")
        st.latex(r"G_{tip}(k)\approx G_0+\beta\,k")

        st.markdown("**5. Small-signal output**")
        st.latex(r"V_{AB}\approx -V_{in}\frac{R_2\,R_{p,0}\,\alpha\,\Delta T}{(R_2+R_{p,0})^2}")

        st.markdown(
            "**Plot guide:** At low $k$ (air) the probe runs at $\\Delta T_0$. "
            "Rising $k$ drains heat → probe cools → $R_p$ drops → bridge "
            "unbalances. Curve saturates when $G_{tip}\\gg G_{probe}$."
        )
