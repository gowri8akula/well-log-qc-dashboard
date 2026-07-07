import streamlit as st
import pandas as pd
import sys
import os

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.loader import load_las, get_curve_inventory
from src.qc_checks import run_all_checks
from src.visualizer import (
    plot_log_tracks,
    add_xaxis_style,
    add_grid,
    add_qc_flags,
    add_legend,
    fix_large_xaxis,
    plot_completeness_heatmap
)

# PAGE CONFIG
st.set_page_config(
    page_title="Well Log QC Dashboard",
    layout="wide"
)

# TITLE
st.title("Well Log QC Dashboard")
st.markdown("Automated quality control for LAS well log files.")
st.divider()

# FILE UPLOAD
st.sidebar.header("Upload Well Log")
uploaded_file = st.sidebar.file_uploader(
    "Choose a LAS file",
    type=["las"],
    help="Upload a LAS 2.0 format well log file"
)

if uploaded_file is None:
    st.info("Upload a LAS file from the sidebar to get started.")
    st.stop()

# LOAD DATA
import tempfile

with tempfile.NamedTemporaryFile(delete=False, suffix=".las") as tmp:
    tmp.write(uploaded_file.read())
    tmp_path = tmp.name

try:
    df, metadata = load_las(tmp_path)
    issues_df = run_all_checks(df)
    inventory_df = get_curve_inventory(df)
    st.success(f"Successfully loaded: {uploaded_file.name}")
except Exception as e:
    st.error(f"Error loading file: {e}")
    st.stop()

# WELL METADATA
st.subheader("Well Information")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Well Name",   metadata.get("well_name", "Unknown"))
col2.metric("Start Depth", f"{metadata.get('start_depth', 0):.2f} m")
col3.metric("Stop Depth",  f"{metadata.get('stop_depth', 0):.2f} m")
col4.metric("Curves",      len(metadata.get("curves", [])))
st.divider()

# QC SUMMARY METRICS
st.subheader("QC Summary")
total    = len(issues_df)
critical = len(issues_df[issues_df["severity"] == "critical"]) if total > 0 else 0
warning  = len(issues_df[issues_df["severity"] == "warning"])  if total > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Issues",    total)
col2.metric("Critical Issues", critical)
col3.metric("Warnings",        warning)
st.divider()

# TABS
tab1, tab2, tab3 = st.tabs([
    "Log Viewer",
    "QC Issues",
    "Completeness"
])

# TAB 1 - Log Viewer
with tab1:
    st.subheader("Interactive Log Tracks")
    curves = [c for c in df.columns if c != "DEPT"]
    fig = plot_log_tracks(df, title=f"{metadata.get('well_name', 'Well')} - Log QC")
    fig = add_xaxis_style(fig, curves)
    fig = add_grid(fig, curves)
    fig = add_qc_flags(fig, df, issues_df, curves)
    fig = add_legend(fig)
    fig = fix_large_xaxis(fig, df, curves)
    st.plotly_chart(fig, use_container_width=True)

# TAB 2 - QC Issues Table
with tab2:
    st.subheader("QC Issues Found")
    if len(issues_df) == 0:
        st.success("No QC issues found - data looks clean!")
    else:
        st.dataframe(issues_df, use_container_width=True)
        csv = issues_df.to_csv(index=False)
        st.download_button(
            label="Download QC Report (CSV)",
            data=csv,
            file_name=f"{uploaded_file.name}_qc_report.csv",
            mime="text/csv"
        )

# TAB 3 - Completeness
with tab3:
    st.subheader("Data Completeness by Curve")
    fig2 = plot_completeness_heatmap(df)
    st.plotly_chart(fig2, use_container_width=True)
    st.subheader("Curve Inventory")
    st.dataframe(inventory_df, use_container_width=True)
