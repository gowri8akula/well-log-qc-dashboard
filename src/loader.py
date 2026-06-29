
# src/loader.py
# -------------
# Reads LAS files and returns a pandas DataFrame + metadata.
# This is the entry point for all data in the project.

import lasio
import pandas as pd
import numpy as np
import os

def load_las(filepath):
    """
    Read a LAS file and return curve data and metadata.
    
    Args:
        filepath: path to the LAS file
        
    Returns:
        df: pandas DataFrame with DEPT as index, curves as columns
        metadata: dictionary with well information
    """
    # Check file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"LAS file not found: {filepath}")
    
    # Read the LAS file
    las = lasio.read(filepath)
    
    # Convert to pandas DataFrame
    df = las.df()
    
    # Reset index so DEPT becomes a regular column
    df = df.reset_index()
    
    # Extract metadata from the LAS header
    metadata = {
        "well_name":   _safe_get(las, "WELL"),
        "start_depth": _safe_get(las, "STRT"),
        "stop_depth":  _safe_get(las, "STOP"),
        "step":        _safe_get(las, "STEP"),
        "null_value":  _safe_get(las, "NULL"),
        "curves":      [c.mnemonic for c in las.curves],
        "filepath":    filepath,
    }
    
    return df, metadata


def _safe_get(las, key):
    """
    Safely get a value from the LAS header.
    Returns None if the key doesn't exist.
    
    Args:
        las: lasio LASFile object
        key: header key to look up
        
    Returns:
        value or None
    """
    try:
        return las.well[key].value
    except:
        return None


def get_curve_inventory(df, null_value=-999.25):
    """
    Generate a summary of all curves in the DataFrame.
    Shows how much data is missing for each curve.
    
    Args:
        df: pandas DataFrame from load_las()
        null_value: the null value used in the LAS file
        
    Returns:
        inventory_df: DataFrame with curve name, count, missing%, min, max
    """
    inventory = []
    
    for col in df.columns:
        # Replace null values with NaN
        series = df[col].replace(null_value, np.nan)
        
        total      = len(series)
        missing    = series.isna().sum()
        pct_miss   = round((missing / total) * 100, 2)
        valid      = total - missing
        
        inventory.append({
            "curve":      col,
            "total":      total,
            "valid":      valid,
            "missing":    missing,
            "missing_%":  pct_miss,
            "min":        round(series.min(), 4) if valid > 0 else None,
            "max":        round(series.max(), 4) if valid > 0 else None,
        })
    
    return pd.DataFrame(inventory)
