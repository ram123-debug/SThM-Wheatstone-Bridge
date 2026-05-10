# SThM Wheatstone Bridge Simulator

An interactive teaching/research app that simulates how a **Scanning Thermal Microscopy (SThM)** probe responds when used as the active arm of a **Wheatstone bridge**.

The probe is self-heated, so when its tip touches a sample, heat drains into the sample, the probe cools, its resistance drops, and the bridge produces an imbalance voltage. **That imbalance voltage is the SThM thermal signal.**

Built with [Streamlit](https://streamlit.io). One-file Python app, deployable to Streamlit Community Cloud in two clicks.

---

## Features

- Live Wheatstone bridge schematic with the probe in the bottom-right arm
- Sliders for input voltage, the three balance resistors, probe properties, and sample thermal conductivity
- Material presets (air, polymer, glass, sapphire, silicon, copper, diamond)
- Real-time readout of probe ΔT, heat flux Q, probe resistance Rₚ, and imbalance voltage V_AB
- Sweep plot of V_AB vs sample thermal conductivity *k* (log scale) with the current operating point highlighted
- All governing physics equations rendered with LaTeX inline

---

## Physics implemented

**1. Bridge imbalance**

```
V_AB = V_in · [ R₃/(R₁+R₃)  −  Rₚ/(R₂+Rₚ) ]
```

Balance condition: `R₁·Rₚ = R₂·R₃`.

**2. Probe TCR (linear)**

```
Rₚ(ΔT) = R_{p,0} · (1 + α·ΔT)
```

α is the temperature coefficient of resistance (≈ 1.7×10⁻³/K for Pd, ≈ 3.9×10⁻³/K for Pt).

**3. Steady-state probe heat balance**

The Joule power dissipated in the probe leaves through the cantilever and through the tip in parallel:

```
P_joule = (G_probe + G_tip) · ΔT
ΔT      = ΔT₀ · G_probe / (G_probe + G_tip(k))
```

with `G_probe = 1/R_th` and ΔT₀ the free-air probe heating.

**4. Tip-sample thermal conductance**

```
G_tip(k) ≈ G₀ + β·k_sample
Q       = G_tip · ΔT
```

A simple linear coupling. Real systems include constriction + ballistic resistance, water meniscus, and load-force effects.

**5. Small-signal SThM sensitivity**

```
V_AB ≈ − V_in · R₂ / (R₂ + R_{p,0})² · R_{p,0} · α · ΔT
```

Linear in V_in and in α·ΔT.

---

## Run locally

```bash
git clone https://github.com/<your-username>/sthm-bridge-simulator.git
cd sthm-bridge-simulator
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`).

Python 3.9+ recommended.

---

## Deploy to Streamlit Community Cloud (free)

1. Push this repo to GitHub (public or private).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, pick this repo, set the main file path to `app.py`, and click **Deploy**.
4. You will get a public URL like `https://<your-app>.streamlit.app` that anyone can open in a browser — no install needed.

That's it. Streamlit Cloud reads `requirements.txt` automatically.

### Other deployment options

- **Hugging Face Spaces** — create a new Space, choose the *Streamlit* template, drop `app.py` and `requirements.txt` in.
- **Docker** — see the Dockerfile snippet in [`docs/docker.md`](docs/docker.md) (optional, easy to add).
- **Local network** — `streamlit run app.py --server.address 0.0.0.0` exposes it on your LAN.

---

## Things to try in the app

- Set all four resistors to the same value and start with **air**: V_AB sits at zero (balanced).
- Sweep the sample preset from **air → copper**: V_AB grows in magnitude and then **saturates**. That saturation is the fundamental ceiling of *passive* SThM — once `G_tip ≫ G_probe`, the probe is clamped to the sample temperature and further `k` cannot change ΔT.
- Drop the cantilever thermal resistance `R_th`: the contrast between materials collapses, because heat now leaves up the cantilever instead of through the tip. This is why real SThM probes are designed for **high thermal isolation**.
- Set the TCR `α ≈ 0`: bridge still works electrically, but the probe stops being a thermometer — V_AB no longer responds to sample changes.
- Increase `V_in`: signal scales linearly, but in real probes electromigration and runaway self-heating cap V_in well below 10 V.

---

## Repository layout

```
sthm-bridge-simulator/
├── app.py              # Streamlit application
├── requirements.txt    # Python dependencies
├── README.md           # this file
└── LICENSE             # MIT
```

---

## Caveats

This is a **lumped, pedagogical model** — useful for building intuition, designing student labs, and sanity-checking instrument behaviour. It is *not* a calibrated metrology tool. Real SThM modelling needs:

- Non-linear TCR and self-heating effects at high bias
- Frequency-dependent thermal masses (3ω / AC modes)
- Constriction + ballistic + spreading tip resistances rather than a single `G_tip`
- Water-meniscus and air-gap contributions that vary with humidity and load force
- Probe-specific calibration against reference samples

PRs that extend the model in any of these directions are very welcome.

---

## License

MIT — see `LICENSE`.

## Citation

If this app is useful in teaching or in a publication, a citation or link back to the GitHub repo is appreciated.
