"""
Pile option comparison - core logic (no Streamlit imports).

Re-uses design_foundation() from foundation.py, runs it once per pile option
and collects comparison metrics.

Units: loads in kN, moments in kNm, X/Y and pile coordinates in metres,
pile diameter in mm.
"""

import numpy as np
import pandas as pd

from foundation import (  # noqa: F401  (re-exported for the comparison page)
    design_foundation,
    load_columns_sheet,
    overlapping_caps,
)

# metric name -> (number format, "low" / "high" = which value is best)
METRICS = {
    "Total piles": ("{:,.0f}", "low"),
    "Avg piles / column": ("{:,.2f}", "low"),
    "Max piles in a column": ("{:,.0f}", "low"),
    "Total pile length (m)": ("{:,.0f}", "low"),
    "Pile concrete (m³)": ("{:,.1f}", "low"),
    "Cap plan area (m²)": ("{:,.1f}", "low"),
    "Avg pile utilisation (%)": ("{:,.1f}", "high"),
    "Max pile utilisation (%)": ("{:,.1f}", "low"),
    "Columns with a pile > 100% capacity": ("{:,.0f}", "low"),
    "Columns with pile uplift (tension)": ("{:,.0f}", "low"),
    "Overlapping cap pairs": ("{:,.0f}", "low"),
    "Columns needing > 9 piles (not designed)": ("{:,.0f}", "low"),
    "Relative cost index": ("{:,.0f}", "low"),
}


def run_option(opt, columns_df, load_increase_percent=0.0, edge_factor=1.0):
    """
    Design every column for one pile option.

    opt: dict-like with Diameter (mm), Capacity (kN), Length (m), Spacing (D)
    edge_factor: pile-centre to cap-edge distance, as a multiple of D
    Returns (results, failed_ids).
    """
    cap = float(opt["Capacity (kN)"])
    results, failed = [], []
    for _, row in columns_df.iterrows():
        try:
            f = design_foundation(
                row=row,
                pile_capacity=cap,
                spacing_factor=float(opt["Spacing (D)"]),
                pile_diameter=float(opt["Diameter (mm)"]),
                load_increase_percent=load_increase_percent,
                edge_factor=edge_factor,
            )
        except ValueError:  # more than 9 piles needed
            failed.append(str(row["Column ID"]))
            continue
        f["Utilisation"] = [r / cap for r in f["Pile Reactions"]]
        results.append(f)
    return results, failed


def summarise(opt, results, failed, rate_per_m=0.0, rate_per_pile=0.0):
    """One column of the comparison table."""
    cap = float(opt["Capacity (kN)"])
    length = float(opt["Length (m)"])
    dia_m = float(opt["Diameter (mm)"]) / 1000.0

    n_piles = int(sum(f["Piles"] for f in results))
    n_cols = len(results)
    util = (
        np.concatenate([f["Utilisation"] for f in results])
        if results else np.array([0.0])
    )

    return {
        "Total piles": n_piles,
        "Avg piles / column": n_piles / n_cols if n_cols else 0.0,
        "Max piles in a column": max((f["Piles"] for f in results), default=0),
        "Total pile length (m)": n_piles * length,
        "Pile concrete (m³)": n_piles * np.pi * dia_m ** 2 / 4.0 * length,
        "Cap plan area (m²)": sum(f["CapArea"] for f in results),
        "Avg pile utilisation (%)": float(util.mean()) * 100.0,
        "Max pile utilisation (%)": float(util.max()) * 100.0,
        "Columns with a pile > 100% capacity": sum(
            1 for f in results if f["Max Pile Load"] > cap
        ),
        "Columns with pile uplift (tension)": sum(
            1 for f in results if f["Min Pile Load"] < 0
        ),
        "Overlapping cap pairs": len(overlapping_caps(results)),
        "Columns needing > 9 piles (not designed)": len(failed),
        "Relative cost index": n_piles * (length * rate_per_m + rate_per_pile),
    }


def per_column_tables(runs, columns_df):
    """
    Piles per column and max utilisation per column, one column per option.
    runs: {option_name: (opt, results, failed)}
    """
    base = columns_df[["Column ID", "X", "Y"]].copy()
    base["Service load (kN)"] = (
        columns_df["Dead Load"] + columns_df["Live Load"] + columns_df["Wind Load"]
    )
    piles = base.set_index("Column ID")
    util = base.set_index("Column ID")[[]].copy()
    for name, (opt, results, _failed) in runs.items():
        cap = float(opt["Capacity (kN)"])
        piles[name] = pd.Series({f["Column ID"]: f["Piles"] for f in results})
        util[name] = pd.Series(
            {f["Column ID"]: f["Max Pile Load"] / cap * 100.0 for f in results}
        )
    return piles, util
