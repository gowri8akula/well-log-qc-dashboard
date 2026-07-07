
# src/config.py
# -------------
# Central settings file for the Well Log QC Dashboard.
# All QC thresholds and curve definitions live here.

# Expected value ranges for common well log curves
CURVE_RANGES = {
    "GR":   {"min": 0,     "max": 300,  "unit": "GAPI"},
    "RHOB": {"min": 1.0,   "max": 3.5,  "unit": "G/C3"},
    "NPHI": {"min": -0.15, "max": 0.6,  "unit": "V/V"},
    "DT":   {"min": 40,    "max": 200,  "unit": "US/F"},
    "RT":   {"min": 0.1,   "max": 5000, "unit": "OHMM"},
}

# Curve aliases — correct mappings only
CURVE_ALIASES = {
    "GR":   ["GRD", "GAMRAY", "HCGR", "GRC", "GAMN"],
    "RHOB": ["RHOZ", "ZDEN", "DEN"],
    "NPHI": ["PHIS", "PHIF"],
    "DT":   ["AC", "SONIC", "DTC"],
    "RT":   ["RD", "RDEEP", "ILD"],
}

# QC check thresholds
QC_SETTINGS = {
    "null_value":        -999.25,
    "zscore_threshold":  3.5,
    "flatline_window":   10,
    "flatline_threshold": 0.001,
}
