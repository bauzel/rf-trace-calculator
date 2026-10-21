"""
RF & Power PCB Trace Calculator (v2) - aimed at DIY / home RF PCB makers

Models
  * Microstrip width/impedance : IPC-2141 (approximate, valid for ~0.1 < w/h < 2)
  * Effective permittivity     : Hammerstad-style formula used in class (Pozar 3.195)
  * Current capacity           : IPC-2221, EXTERNAL layer (home boards only have outer layers)

Run:            python rfcalculator_v2.py
Self-test:      python rfcalculator_v2.py --selftest
"""
import math
import sys

# ---------------------------------------------------------------------
# Tunable constants (tweak these for your own process)
# ---------------------------------------------------------------------
C0 = 3e8                  # speed of light [m/s]
OZ_TO_MM = 0.035          # 1 oz copper ~ 35 um
TEMP_RISE_C = 10          # allowed trace temperature rise for current calc [C]

FAB_TOL = 0.05            # +/- width tolerance, professional fab
UNDERCUT_NOM_MM = 0.15    # total width lost to etching (both edges) - nominal
UNDERCUT_MIN_MM = 0.10    # best case etch
UNDERCUT_MAX_MM = 0.20    # worst case etch

DIY_MAX_MHZ = 500         # above this, home FR4 boards get unreliable
DIY_MIN_TRACE_MM = 0.3    # thinnest trace that transfers/etches reliably at home
DIY_MAX_Z_ERROR = 0.10    # accept +/-10 % impedance error at home


# ---------------------------------------------------------------------
# Core formulas
# ---------------------------------------------------------------------
def microstrip_width(z0, h_mm, er, t_mm):
    """IPC-2141 inverted: trace width [mm] for a target Z0."""
    exponent = z0 * math.sqrt(er + 1.41) / 87.0
    return ((5.98 * h_mm) / math.exp(exponent) - t_mm) / 0.8


def microstrip_z0(w_mm, h_mm, er, t_mm):
    """IPC-2141 forward: impedance [ohm] for a given trace width."""
    return 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * h_mm / (0.8 * w_mm + t_mm))


def eps_eff(w_mm, h_mm, er):
    """Effective dielectric constant of a microstrip line (w/h dependent)."""
    return (er + 1) / 2 + (er - 1) / 2 / math.sqrt(1 + 12 * h_mm / w_mm)


def skin_depth_um(f_mhz):
    """Skin depth of copper in micrometers (approx: 66 um / sqrt(f[MHz]))."""
    return 66.0 / math.sqrt(f_mhz)


def current_width_mm(i_amp, t_oz, dt=TEMP_RISE_C):
    """IPC-2221 external layer: minimum trace width [mm] for a current."""
    k, b, c = 0.048, 0.44, 0.725
    area_mil2 = (i_amp / (k * dt ** b)) ** (1 / c)
    return area_mil2 / (t_oz * 1.378) * 0.0254


def max_current_amp(w_mm, t_oz, dt=TEMP_RISE_C):
    """IPC-2221 external layer: current [A] a given width can carry."""
    k, b, c = 0.048, 0.44, 0.725
    area_mil2 = (w_mm / 0.0254) * (t_oz * 1.378)
    return k * dt ** b * area_mil2 ** c


# ---------------------------------------------------------------------
# Input helper (accepts "4,6" as well as "4.6")
# ---------------------------------------------------------------------
def ask(prompt, minimum=0.0):
    while True:
        raw = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw)
        except ValueError:
            print("  ! Please enter a number.")
            continue
        if value <= minimum:
            print(f"  ! Value must be greater than {minimum}.")
            continue
        return value


# ---------------------------------------------------------------------
# Main tool
# ---------------------------------------------------------------------
def rf_pcb_calculator():
    print("--- RF & PCB Trace Analysis Tool (v2) ---")
    f_mhz = ask("Operating Frequency (MHz): ")
    z0_target = ask("Target Impedance (Ohm): ")
    h_mm = ask("Substrate Height (H) [mm]: ")
    er = ask("Dielectric Constant (er): ", minimum=1.0)
    t_oz = ask("Copper Thickness (t) [oz]: ")
    i_amp = ask("Max Load Current [Amps]: ", minimum=-1)  # 0 A allowed

    t_mm = t_oz * OZ_TO_MM
    f_hz = f_mhz * 1e6

    # ---- RF geometry -------------------------------------------------
    w_rf = microstrip_width(z0_target, h_mm, er, t_mm)
    if w_rf <= 0:
        print("\nERROR: No valid microstrip width for this impedance/substrate.")
        print("Use a thinner substrate or a lower impedance.")
        return
    wh = w_rf / h_mm
    ee = eps_eff(w_rf, h_mm, er)
    lam_g_mm = C0 / (f_hz * math.sqrt(ee)) * 1000
    long_line_mm = lam_g_mm / 10                       # electrically-long threshold
    f_max_ghz = C0 / (10 * (h_mm / 1000) * math.sqrt(ee)) / 1e9   # h <= lambda_g/10
    delta_um = skin_depth_um(f_mhz)

    # ---- current -----------------------------------------------------
    w_current = current_width_mm(i_amp, t_oz) if i_amp > 0 else 0.0
    i_capacity = max_current_amp(w_rf, t_oz)
    current_conflict = w_current > w_rf

    # ---- warnings ----------------------------------------------------
    warnings = []
    if not (0.1 <= wh <= 2.0):
        warnings.append(f"w/h = {wh:.2f} is outside IPC-2141's valid range (0.1-2.0): "
                        "result is only approximate, verify with a field solver / KiCad PCB Calculator.")
    if f_mhz / 1000 > f_max_ghz:
        warnings.append(f"Frequency is above the substrate limit ({f_max_ghz:.1f} GHz): "
                        "h > lambda_g/10, higher-order modes possible.")
    if current_conflict:
        warnings.append(f"{i_amp} A needs >= {w_current:.2f} mm, but the {z0_target:g} ohm line is "
                        f"{w_rf:.2f} mm wide (carries ~{i_capacity:.2f} A). Widening it would shift the "
                        "impedance: use a separate wider power trace, or change H/er.")

    # ---- report ------------------------------------------------------
    line = "=" * 64
    print("\n" + line)
    print(f"{'ENGINEERING ANALYSIS REPORT':^64}")
    print(line)
    print(f"Goal                  : {z0_target:g} ohm @ {f_mhz:g} MHz")
    print(f"RF trace width        : {w_rf:.3f} mm  (w/h = {wh:.2f}, IPC-2141)")
    print(f"Effective er          : {ee:.3f}   (substrate er = {er:g})")
    print(f"Guided wavelength     : {lam_g_mm:.1f} mm")
    print(f"Controlled-impedance  : traces longer than {long_line_mm:.1f} mm (lambda_g/10) must be")
    print(f"  threshold             treated as transmission lines (keep Z0 and terminations right)")
    print(f"Substrate fmax        : {f_max_ghz:.2f} GHz  (rule: H <= lambda_g/10)")
    print(f"Skin depth (copper)   : {delta_um:.2f} um  (copper thickness = {t_mm * 1000:.0f} um)")
    if i_amp > 0:
        print(f"{'Current (' + format(i_amp, 'g') + ' A)':<22}: needs >= {w_current:.3f} mm for {TEMP_RISE_C} C rise; "
              f"RF width carries ~{i_capacity:.2f} A")
    for w in warnings:
        print(f"\n [!] {w}")
    print("-" * 64)

    # ---- Option A: professional fab ----------------------------------
    z_a_hi = microstrip_z0(w_rf * (1 - FAB_TOL), h_mm, er, t_mm)
    z_a_lo = microstrip_z0(w_rf * (1 + FAB_TOL), h_mm, er, t_mm)
    print("[OPTION A] PROFESSIONAL FABRICATION (impedance-controlled order)")
    print(f"  > Trace width: {w_rf:.3f} mm  (+/-{FAB_TOL * 100:.0f} % = "
          f"{w_rf * (1 - FAB_TOL):.3f} - {w_rf * (1 + FAB_TOL):.3f} mm)")
    print(f"  > Resulting Z0: {z_a_lo:.1f} - {z_a_hi:.1f} ohm (width tolerance only)")
    print("  > Tell the fab your target Z0 and let them adjust to their real stackup.")
    print("\n" + "-" * 64)

    # ---- Option B: home etching --------------------------------------
    drawn = w_rf + UNDERCUT_NOM_MM
    etched_min = drawn - UNDERCUT_MAX_MM
    etched_max = drawn - UNDERCUT_MIN_MM
    reasons = []
    if etched_min <= 0:
        z_b_lo = z_b_hi = float("nan")
        reasons.append("Trace would be etched away in the worst case")
    else:
        z_b_lo = microstrip_z0(etched_max, h_mm, er, t_mm)
        z_b_hi = microstrip_z0(etched_min, h_mm, er, t_mm)
        worst = max(abs(z_b_lo - z0_target), abs(z_b_hi - z0_target)) / z0_target
        if worst > DIY_MAX_Z_ERROR:
            reasons.append(f"Etch variation gives about +/-{worst * 100:.0f} % impedance error "
                           f"(limit {DIY_MAX_Z_ERROR * 100:.0f} %)")
    if f_mhz > DIY_MAX_MHZ:
        reasons.append(f"Frequency above {DIY_MAX_MHZ} MHz (FR4 loss, unreliable home process)")
    if w_rf < DIY_MIN_TRACE_MM:
        reasons.append(f"Trace thinner than {DIY_MIN_TRACE_MM} mm (toner transfer/etching unreliable)")

    print("[OPTION B] HOME PROTOTYPING (DIY acid etching)")
    if not math.isnan(z_b_lo):
        print(f"  > Draw trace at: {drawn:.3f} mm  (target + {UNDERCUT_NOM_MM} mm undercut compensation)")
        print(f"  > Expected etched width: {etched_min:.3f} - {etched_max:.3f} mm")
        print(f"  > Expected Z0: {z_b_lo:.1f} - {z_b_hi:.1f} ohm")
    if reasons:
        print("  > STATUS: NOT RECOMMENDED FOR HOME PRODUCTION")
        for r in reasons:
            print(f"    - {r}")
        print("  > Advice: use a professional PCB house for this design.")
    else:
        print("  > STATUS: SUITABLE (measure the first board: width with calipers, Z0/S11 with a NanoVNA)")
    print(line)


# ---------------------------------------------------------------------
# Self-test against the numbers worked out in class (L03 / L02 / L05)
# ---------------------------------------------------------------------
def selftest():
    w = microstrip_width(50, 1.5, 4.6, 0.035)
    assert abs(w - 2.70) < 0.02, w                       # class: 2.73 (AppCAD), 2.77 (Pozar)
    assert abs(microstrip_z0(w, 1.5, 4.6, 0.035) - 50) < 1e-6
    assert abs(eps_eff(w, 1.5, 4.6) - 3.44) < 0.05       # class: 3.439
    assert abs(skin_depth_um(100) - 6.6) < 0.01
    assert abs(current_width_mm(1, 1) - 0.30) < 0.01     # 1 A, 1 oz, external
    f_max = C0 / (10 * 0.0015 * math.sqrt(eps_eff(w, 1.5, 4.6))) / 1e9
    assert abs(f_max - 10.8) < 0.3, f_max                # class: ~10.8 GHz
    print("Self-test passed.")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        rf_pcb_calculator()
