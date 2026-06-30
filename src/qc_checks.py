
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


def check_depth_gaps(df, depth_col="DEPT", expected_step=None, tolerance=1.5):
    """
    Find irregular depth intervals (skipped readings).
    
    Args:
        df: pandas DataFrame with well log data
        depth_col: name of the depth column
        expected_step: the normal depth step (e.g. 0.05). If None, auto-detected.
        tolerance: how many times bigger than expected_step counts as a gap
        
    Returns:
        issues: list of dictionaries describing each gap found
    """
    issues = []
    
    depths = df[depth_col].values
    
    # Calculate the difference between consecutive depths
    diffs = np.diff(depths)
    
    # Auto-detect the expected step if not provided
    if expected_step is None:
        expected_step = np.median(diffs)
    
    # A gap is any difference bigger than expected_step * tolerance
    gap_threshold = expected_step * tolerance
    gap_indices = np.where(diffs > gap_threshold)[0]
    
    for idx in gap_indices:
        gap_size = diffs[idx]
        issues.append({
            "curve":        depth_col,
            "issue_type":   "depth_gap",
            "severity":     "critical",
            "count":        1,
            "depth_start":  float(depths[idx]),
            "depth_end":    float(depths[idx + 1]),
            "message":      f"Depth gap of {gap_size:.3f} between {depths[idx]:.2f} and {depths[idx+1]:.2f}"
        })
    
    return issues
