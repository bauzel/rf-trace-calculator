# Professional RF & Power PCB Trace Analysis Tool

A Python-based engineering tool designed for calculating PCB trace widths based on IPC-2141 and IPC-2221 standards.  This tool has been specifically designed to calculate the difference between theoretical RF design and practical manufacturing constraints, such as acid etching and industrial production tolerances.

## Features

- Dual-Standard Analysis: Simultaneously calculates trace requirements for RF signal integrity (Impedance) and Power delivery (Current capacity).
- Manufacturing Modes: Provides distinct outputs for:
    - Industrial Fabrication (Class 3): Tight tolerances for professional PCB houses.
    - Home Prototyping (DIY): Includes 'Etch-Compensation' for undercutting and manual production warnings.
- Critical RF Safety Checks:
    - Calculates Maximum Safe Trace Length (lambda/10) to prevent signal degradation.
    - Automated suitability check for high frequencies (warns above 500 MHz).
    - Checks for minimum width constraints (0.3mm for toner transfer).
- Physical Insights: Calculates skin depth and propagation velocity.

## Standards
This tool has been verified by comparing it with the IPC standards and mathematical equations listed below. Although it is not 100% accurate, there is, in THEORY, a margin of error of approximately 2–3%.

| Parameter    | Standard Applied  | Impact                                                          |
| -----        | --------          | ------------------                                              |
| Impedance    | IPC-2141          | It determines the RF geometry for reflection-free transmission. |
| Current      | IPC-2221          | Ensures trace does not overheat (based on 10°C rise).           |
| Trace Length | lambda/10 Rule    | Identifies the limit where a trace becomes a transmission line. |

### Manufacturing Warnings
- DIY Limit: High frequencies are marked as unsuitable for home etching due to high precision requirements.
- Etch Compensation: DIY mode automatically adds +0.15mm to the drawing width to account for the lateral erosion of copper (undercutting).

## Disclaimer

This code is an analytical solver designed for rapid prototyping and pre-layout analysis. While mathematically accurate according to IPC standards, it is NOT a 3D EM full-wave solver. 
- Important Note: For designs exceeding high speeds like 2.4 GHz, professional VNA (Vector Network Analyzer) measurement and high-precision fabrication are strictly recommended.
- Material Difference: Actual substrate er may vary; always consult your manufacturer's datasheet.


## License
MIT License - Feel free to use and improve!
No liability, whether financial or otherwise, is accepted by the author. All risks and liabilities rest entirely with the person or people who download, modify, or use this code in their hardware designs. While the formulas are based on industry standards (IPC), the author does NOT guarantee the final results of manufactured PCB. Changing the code or using it for commercial purposes is permitted.
