"""Data validation utilities for launch_points project.

Checks CSV marker files for header consistency, numeric lat/lon, transport normalization
and existence of referenced image files.
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple

import pandas as pd


def validate_marker_csv(path: str) -> List[str]:
    """Run validations on a single CSV file and return list of issues found."""
    issues: List[str] = []
    if not os.path.exists(path):
        return [f"file-not-found: {path}"]

    df = pd.read_csv(path)
    # normalize headers (strip whitespace) and detect if there was whitespace
    original_cols = list(df.columns)
    df.columns = [c.strip() for c in df.columns]
    if df.columns.tolist() != original_cols:
        issues.append("header-whitespace")

    # required columns
    required = {"name", "lat", "lon"}
    missing = required - set(c.strip() for c in df.columns)
    if missing:
        issues.append(f"missing-columns: {', '.join(sorted(missing))}")

    # Coerce lat/lon and report non-numeric rows
    for idx, row in df.iterrows():
        try:
            lat = float(str(row.get("lat", "")).strip())
            lon = float(str(row.get("lon", "")).strip())
        except Exception:
            issues.append(f"invalid-coordinates: row {idx}")

    # Check transport normalization: ensure values are boolean-like or empty
    if "transport" in df.columns:
        for idx, val in enumerate(df["transport"].tolist()):
            if pd.isna(val) or isinstance(val, bool):
                continue
            s = str(val).strip().lower()
            if s not in ("true", "false", "1", "0", "yes", "no", "y", "n", ""):  # allow empty
                issues.append(f"transport-unknown-format: row {idx} -> {val}")

    # Check picture paths exist if provided
    if "picture" in df.columns:
        for idx, val in enumerate(df["picture"].tolist()):
            if pd.isna(val):
                continue
            p = str(val).strip()
            if p and not os.path.exists(os.path.join(os.path.dirname(path), p)):
                issues.append(f"missing-picture: row {idx} -> {p}")

    return issues


def validate_all_marker_files(paths: List[str]) -> Dict[str, List[str]]:
    results = {}
    for p in paths:
        results[p] = validate_marker_csv(p)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    res = validate_all_marker_files(args.paths)
    for k, v in res.items():
        print(f"{k} -> {len(v)} issues")
        for issue in v:
            print("  -", issue)
