
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


def check_spikes(df, depth_col="DEPT", zscore_threshold=3.5):
    """
    Detect abnormal spikes using z-score statistics.
    
    Args:
        df: pandas DataFrame with well log data
        depth_col: name of the depth column
        zscore_threshold: how many std deviations counts as a spike
        
    Returns:
        issues: list of dictionaries describing each spike found
    """
    issues = []
    
    for col in df.columns:
        if col == depth_col:
            continue
        
        series = df[col]
        
        # Skip curves with no variation (avoids division by zero)
        if series.std() == 0 or series.std() is None:
            continue
        
        # Calculate z-scores for every value in this curve
        z_scores = (series - series.mean()) / series.std()
        
        # Find rows where the absolute z-score exceeds the threshold
        is_spike = z_scores.abs() > zscore_threshold
        spike_count = is_spike.sum()
        
        if spike_count > 0:
            spike_depths = df.loc[is_spike, depth_col]
            spike_values = series[is_spike]
            
            issues.append({
                "curve":        col,
                "issue_type":   "spike",
                "severity":     "warning",
                "count":        int(spike_count),
                "depth_start":  float(spike_depths.min()),
                "depth_end":    float(spike_depths.max()),
                "message":      f"{col} has {spike_count} spike(s), values up to {spike_values.abs().max():.2f}"
            })
    
    return issues


def check_range_violations(df, curve_ranges, curve_aliases, depth_col="DEPT"):
    """
    Check if curve values fall outside expected industry-standard ranges.
    Uses curve_aliases to match non-standard curve names to standard ones.
    
    Args:
        df: pandas DataFrame with well log data
        curve_ranges: dict of standard curve names to {min, max, unit}
        curve_aliases: dict of standard curve names to list of alternate names
        depth_col: name of the depth column
        
    Returns:
        issues: list of dictionaries describing each range violation found
    """
    issues = []
    
    # Build a lookup: actual column name -> standard curve name
    column_to_standard = {}
    for col in df.columns:
        if col == depth_col:
            continue
        
        # Check if this column name IS already a standard name
        if col in curve_ranges:
            column_to_standard[col] = col
            continue
        
        # Check if this column name is an ALIAS for a standard name
        for standard_name, aliases in curve_aliases.items():
            if col in aliases:
                column_to_standard[col] = standard_name
                break
    
    # Now check each matched column against its standard range
    for col, standard_name in column_to_standard.items():
        bounds = curve_ranges[standard_name]
        series = df[col]
        
        is_violation = (series < bounds["min"]) | (series > bounds["max"])
        violation_count = is_violation.sum()
        
        if violation_count > 0:
            violation_depths = df.loc[is_violation, depth_col]
            violation_values = series[is_violation]
            
            issues.append({
                "curve":        col,
                "issue_type":   "range_violation",
                "severity":     "critical",
                "count":        int(violation_count),
                "depth_start":  float(violation_depths.min()),
                "depth_end":    float(violation_depths.max()),
                "message":      f"{col} (mapped to {standard_name}) has {violation_count} value(s) "
                                 f"outside range [{bounds['min']}, {bounds['max']}] {bounds['unit']}. "
                                 f"Extreme value: {violation_values.iloc[0]:.2f}"
            })
    
    return issues
