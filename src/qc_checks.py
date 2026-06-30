
# src/qc_checks.py
# -----------------
# All automated QC check functions live here.
# Each function takes a DataFrame and returns a list of issue dictionaries.

import pandas as pd
import numpy as np


def check_nulls(df, null_value=-999.25, depth_col="DEPT"):
    """
    Find missing values in each curve.
    
    Args:
        df: pandas DataFrame with well log data
        null_value: the value used to represent missing data
        depth_col: name of the depth column
        
    Returns:
        issues: list of dictionaries describing each issue found
    """
    issues = []
    
    # Loop through every column except the depth column
    for col in df.columns:
        if col == depth_col:
            continue
        
        # Find rows where this curve equals the null value
        is_null = df[col] == null_value
        
        # Also catch actual NaN values (sometimes present)
        is_null = is_null | df[col].isna()
        
        null_count = is_null.sum()
        
        if null_count > 0:
            # Find the depth range where nulls occur
            null_depths = df.loc[is_null, depth_col]
            
            issues.append({
                "curve":        col,
                "issue_type":   "missing_value",
                "severity":     "warning",
                "count":        int(null_count),
                "depth_start":  float(null_depths.min()),
                "depth_end":    float(null_depths.max()),
                "message":      f"{col} has {null_count} missing values"
            })
    
    return issues
