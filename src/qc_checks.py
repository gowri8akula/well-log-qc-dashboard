
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


def check_flat_lines(df, depth_col="DEPT", window=10, threshold=0.001):
    """
    Detect stuck-sensor segments where values barely change.
    
    Args:
        df: pandas DataFrame with well log data
        depth_col: name of the depth column
        window: number of consecutive samples to check
        threshold: max standard deviation to call it "flat"
        
    Returns:
        issues: list of dictionaries describing each flat segment found
    """
    issues = []
    
    for col in df.columns:
        if col == depth_col:
            continue
        
        # Calculate rolling standard deviation
        rolling_std = df[col].rolling(window=window).std()
        
        # Flag windows where std deviation is below threshold
        is_flat = rolling_std < threshold
        
        # Skip if no flat segments found
        if not is_flat.any():
            continue
        
        # Find where flat segments start and end
        flat_indices = df.index[is_flat]
        
        # Group consecutive flat indices into segments
        groups = []
        current_group = [flat_indices[0]]
        
        for idx in flat_indices[1:]:
            if idx == current_group[-1] + 1:
                current_group.append(idx)
            else:
                groups.append(current_group)
                current_group = [idx]
        groups.append(current_group)
        
        # Create one issue per flat segment
        for group in groups:
            start_idx = group[0]
            end_idx = group[-1]
            
            issues.append({
                "curve":        col,
                "issue_type":   "flat_line",
                "severity":     "warning",
                "count":        len(group),
                "depth_start":  float(df.loc[start_idx, depth_col]),
                "depth_end":    float(df.loc[end_idx, depth_col]),
                "message":      f"{col} is flat for {len(group)} samples (possible stuck sensor)"
            })
    
    return issues
