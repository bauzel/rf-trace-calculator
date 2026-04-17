import math

def rf_pcb_pro_calculator():
    """
    Professional RF & Power PCB Trace Calculator
    Supports IPC-2141 (Impedance) and IPC-2221 (Current) standards.
    """
    print("--- Professional RF & PCB Trace Analysis Tool ---")
    
    # ---------------------------------------------------------
    # 1. INPUT PARAMETERS
    # ---------------------------------------------------------
    f_mhz = float(input("Operating Frequency (MHz): "))
    target_z0 = float(input("Target Impedance (Ohm): "))
    h_mm = float(input("Substrate Height (H) [mm]: "))
    er = float(input("Dielectric Constant (er): "))
    t_oz = float(input("Copper Thickness (t) [oz]: "))
    i_amp = float(input("Max Load Current [Amps]: "))

    t_mm = t_oz * 0.035 # Convert oz to mm
    f_hz = f_mhz * 1e6

    # ---------------------------------------------------------
    # 2. CORE ENGINEERING CALCULATIONS
    # ---------------------------------------------------------
    
    # A. RF Trace Width (IPC-2141 Microstrip Equation)
    term_sqrt = math.sqrt(er + 1.41)
    exponent = (target_z0 * term_sqrt) / 87
    w_rf = (((5.98 * h_mm) / math.exp(exponent)) - t_mm) / 0.8

    # B. Power Trace Width (IPC-2221 based on 10C Temp Rise)
    k, b, c = 0.048, 0.44, 0.725
    area_sq_mils = (i_amp / (k * (10**b)))**(1/c)
    w_current = (area_sq_mils / (t_oz * 1.378)) * 0.0254

    # C. Maximum Length Before Signal Degradation (Lambda / 10)
    v_p = 3e8 / math.sqrt(er) # Propagation velocity
    wavelength_mm = (v_p / f_hz) * 1000
    max_len_mm = wavelength_mm / 10 

    # D. Skin Depth Calculation
    skin_depth_um = (66 / math.sqrt(f_mhz / 1e6)) * 1000 # Rough approx for Copper in um

    # ---------------------------------------------------------
    # 3. MANUFACTURING TOLERANCE ANALYSIS
    # ---------------------------------------------------------
    
    # Determine the "Engineering Ideal" (the larger of RF vs Power requirements)
    ideal_w = max(w_rf, w_current)

    # FABRICATION (Industrial) - Tight Tolerance
    fab_min, fab_max = ideal_w * 0.95, ideal_w * 1.05
    
    # PROTOTYPE (Home/Acid Etching) - Wide Tolerance + Etch Compensation
    home_w = ideal_w + 0.15 # 0.15mm compensation for undercutting
    home_min, home_max = home_w * 0.85, home_w * 1.20

    # ---------------------------------------------------------
    # 4. FINAL OUTPUT GENERATION
    # ---------------------------------------------------------
    print("\n" + "="*60)
    print(f"{'ENGINEERING ANALYSIS REPORT':^60}")
    print("="*60)
    print(f"Primary Design Goal: {target_z0} Ohm @ {f_mhz} MHz")
    print(f"Calculated Ideal Width: {ideal_w:.4f} mm")
    print(f"Max Safe Trace Length: {max_len_mm:.2f} mm (Critical for RF stability)")
    print("-" * 60)

    # OUTPUT 1: INDUSTRIAL FABRICATION
    print(f"[OPTION A] INDUSTRIAL FABRICATION (Class 3)")
    print(f"  > Recommended Trace Width: {ideal_w:.3f} mm")
    print(f"  > Tolerance Range: {fab_min:.3f} mm - {fab_max:.3f} mm")
    print(f"  > Suitability: HIGH (Guaranteed Impedance Control)")

    print("\n" + "-" * 60)

    # OUTPUT 2: HOME PROTOTYPING (ACID ETCHING)
    print(f"[OPTION B] HOME PROTOTYPING (DIY Acid Etching)")
    
    # Critical Threshold Check for DIY
    diy_suitable = True
    reasons = []
    
    if f_mhz > 500:
        diy_suitable = False
        reasons.append("Frequency exceeds safe DIY limit (Signal Loss)")
    if ideal_w < 0.3:
        diy_suitable = False
        reasons.append("Trace too thin for toner transfer (< 0.3mm)")
    if (max_len_mm < 10):
        diy_suitable = False
        reasons.append("Trace length limit too tight for manual soldering")

    if diy_suitable:
        print(f"  > Recommended Drawing Width: {home_w:.3f} mm (Etch-Compensated)")
        print(f"  > Expected Etched Range: {home_min:.3f} mm - {home_max:.3f} mm")
        print(f"  > Suitability: SUITABLE (Follow precision etching protocol)")
    else:
        print(f"  > STATUS: NOT RECOMMENDED FOR HOME PRODUCTION")
        print(f"  > ALERT: {', '.join(reasons)}")
        print(f"  > Advice: Switch to professional PCB house for this frequency/pitch.")
    
    print("="*60)

if __name__ == "__main__":
    rf_pcb_pro_calculator()