
# src/config.py
# -------------
# Central settings file for the Well Log QC Dashboard.
# All QC thresholds and curve definitions live here.
# Change values here to update the entire project.

# Expected value ranges for common well log curves
# Format: "CURVE_NAME": {"min": value, "max": value, "unit": "unit_name"}
CURVE_RANGES = {
    "GR":   {"min": 0,     "max": 300,  "unit": "GAPI"},
    "RHOB": {"min": 1.0,   "max": 3.5,  "unit": "G/C3"},
    "NPHI": {"min": -0.15, "max": 0.6,  "unit": "V/V"},
    "DT":   {"min": 40,    "max": 200,  "unit": "US/F"},
    "RT":   {"min": 0.1,   "max": 5000, "unit": "OHMM"},
}

# Curve aliases — different names companies use for the same curve
# Format: "STANDARD_NAME": ["alias1", "alias2", ...]
CURVE_ALIASES = {
    "GR":   ["GRD", "GAMRAY", "HCGR", "GRC"],
    "RHOB": ["RHOZ", "ZDEN", "DEN"],
    "NPHI": ["PHIS", "PHIF", "NEU"],
    "DT":   ["AC", "SONIC", "DTC"],
    "RT":   ["RD", "RDEEP", "ILD"],
}

# QC check thresholds
QC_SETTINGS = {
    "null_value":        -999.25,  # Standard LAS null value
    "zscore_threshold":  3.5,      # How many std deviations = a spike
    "flatline_window":   10,       # Number of samples to check for flat line
    "flatline_threshold": 0.001,   # Max std deviation to call it flat
}
