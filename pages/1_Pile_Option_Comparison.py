import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st
from matplotlib import cm
from matplotlib.colors import Normalize
from matplotlib.patches import Circle, Rectangle

from comparison import (
    METRICS,
    load_columns_sheet,
    overlapping_caps,
    per_column_tables,
    run_option,
    summarise,
)

st.set_page_config(page_title="Pile Option Comparison", layout="wide")
st.title("Pile Option Comparison")
st.caption(
    "Runs the same column loads through several pile options and compares "
    "pile numbers, material quantities, utilisation and cap clashes."
)

# =====================================================
# SIDEBAR - settings common to all options
# =====================================================
st.sidebar.header("Common settings")

load_increase = st.sidebar.number_input(
    "Additional Load Increase (%)", value=10.0, step=1.0
)
edge_factor = st.sidebar.number_input(
    "Pile centre to cap edge (x D)",
    value=1.0, step=0.1, min_value=0.5,
    help="Used to size the pile cap in plan and check for cap overlaps."
)

st.sidebar.header("Cost index (optional)")
st.sidebar.caption("Placeholder rates - replace with your own.")
rate_per_m = st.sidebar.number_input("Cost per metre of pile", value=100.0, step=10.0)
rate_per_pile = st.sidebar.number_input(
    "Fixed cost per pile (set-up, cut-off, testing)", value=500.0, step=50.0
)

# =====================================================
# PILE OPTIONS TABLE
# =====================================================
st.subheader("1. Pile options")
st.caption(
    "Edit the table or add rows. Capacities below are placeholders - "
    "enter your own design capacities."
)

default_options = pd.DataFrame({
    "Option": ["600 mm", "750 mm", "900 mm"],
    "Diameter (mm)": [600.0, 750.0, 900.0],
    "Capacity (kN)": [1800.0, 2800.0, 4000.0],
    "Length (m)": [20.0, 20.0, 20.0],
    "Spacing (D)": [3.0, 3.0, 3.0],
})

options_df = st.data_editor(
    default_options,
    num_rows="dynamic",
    use_container_width=True,
    key="options_editor",
)

options_df = options_df.dropna().reset_index(drop=True)
if options_df.empty:
    st.warning("Add at least one pile option.")
    st.stop()

# make option names unique and non-empty
seen = {}
names = []
for i, n in enumerate(options_df["Option"].astype(str)):
    n = n.strip() or f"Option {i + 1}"
    seen[n] = seen.get(n, 0) + 1
    names.append(n if seen[n] == 1 else f"{n} ({seen[n]})")
options_df["Option"] = names

if (options_df[["Diameter (mm)", "Capacity (kN)", "Length (m)", "Spacing (D)"]] <= 0).any().any():
    st.error("Diameter, capacity, length and spacing must all be greater than zero.")
    st.stop()

# =====================================================
# FILE UPLOAD
# =====================================================
st.subheader("2. Column loads")
uploaded_file = st.file_uploader(
    "Upload the same Excel file used in the layout generator (sheet 'Columns')",
    type=["xlsx"],
)

if uploaded_file is None:
    st.info(
        "Expected columns: Column ID, X, Y, Dead Load, Live Load, Wind Load "
        "(Moment X / Moment Y are optional and default to 0)."
    )
    st.stop()

try:
    raw_df = pd.read_excel(uploaded_file, sheet_name="Columns")
except Exception as e:
    st.error(f"Could not read sheet 'Columns': {e}")
    st.stop()

columns_df, err = load_columns_sheet(raw_df)
if err:
    st.error(err)
    st.stop()

# =====================================================
# RUN ALL OPTIONS
# =====================================================
runs = {}
for _, opt in options_df.iterrows():
    results, failed = run_option(
        opt, columns_df,
        load_increase_percent=load_increase,
        edge_factor=edge_factor,
    )
    runs[opt["Option"]] = (opt, results, failed)

summary = pd.DataFrame({
    name: summarise(opt, results, failed, rate_per_m, rate_per_pile)
    for name, (opt, results, failed) in runs.items()
})

incomplete = [n for n, (_o, _r, f) in runs.items() if f]
if incomplete:
    st.warning(
        "Totals for "
        + ", ".join(incomplete)
        + " exclude columns that would need more than 9 piles "
        "(the largest pattern in foundation.py). Compare these options with care."
    )

# =====================================================
# SUMMARY TABLE
# =====================================================
st.subheader("3. Comparison summary")
st.caption("Green = best value in that row.")

text_table = summary.copy().astype(object)
for metric, (fmt, _best) in METRICS.items():
    text_table.loc[metric] = summary.loc[metric].map(lambda v, f=fmt: f.format(v))


def highlight_best(_):
    css = pd.DataFrame("", index=summary.index, columns=summary.columns)
    for metric, (_fmt, best) in METRICS.items():
        row = summary.loc[metric]
        if row.max() == row.min():
            continue
        target = row.min() if best == "low" else row.max()
        css.loc[metric, row[row == target].index] = (
            "background-color:#d4edda;color:#155724;font-weight:600"
        )
    return css


st.dataframe(
    text_table.style.apply(highlight_best, axis=None),
    use_container_width=True,
    height=36 * (len(METRICS) + 1),
)

# =====================================================
# CHARTS
# =====================================================
st.subheader("4. Charts")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("**Total piles**")
    st.bar_chart(summary.loc["Total piles"])
with c2:
    st.markdown("**Pile concrete (m³)**")
    st.bar_chart(summary.loc["Pile concrete (m³)"])
with c3:
    st.markdown("**Relative cost index**")
    st.bar_chart(summary.loc["Relative cost index"])

st.markdown("**How many columns need 1, 2, 3 ... piles**")
dist = pd.DataFrame({
    name: pd.Series([f["Piles"] for f in results]).value_counts()
    for name, (_o, results, _f) in runs.items()
}).reindex(range(1, 10)).fillna(0)
dist.index = dist.index.astype(str)
dist.index.name = "Piles per column"
st.bar_chart(dist)

# =====================================================
# PER-COLUMN TABLES
# =====================================================
st.subheader("5. Column by column")
piles_tbl, util_tbl = per_column_tables(runs, columns_df)
tab_piles, tab_util = st.tabs(["Piles per column", "Max pile utilisation (%)"])
with tab_piles:
    st.dataframe(piles_tbl, use_container_width=True)
with tab_util:
    st.caption("Highest pile load / capacity in each group, including moments. Above 100% = overstressed.")
    st.dataframe(
        util_tbl.style
        .background_gradient(cmap="RdYlGn_r", vmin=40, vmax=120, axis=None)
        .format("{:.0f}"),
        use_container_width=True,
    )

# =====================================================
# PLAN VIEW
# =====================================================
st.subheader("6. Plan view by option")
chosen = st.selectbox("Option", list(runs.keys()))
opt, results, failed = runs[chosen]

if not results:
    st.info("No columns could be designed for this option.")
else:
    dia_m = float(opt["Diameter (mm)"]) / 1000.0
    overlaps = overlapping_caps(results)
    in_overlap = {c for pair in overlaps for c in pair}
    norm = Normalize(vmin=0.0, vmax=1.2)
    cmap = cm.get_cmap("RdYlGn_r")

    fig, ax = plt.subplots(figsize=(11, 8))
    for f in results:
        x0, y0, x1, y1 = f["Bbox"]
        ax.add_patch(Rectangle(
            (x0, y0), x1 - x0, y1 - y0, fill=False,
            edgecolor="red" if f["Column ID"] in in_overlap else "grey",
            linewidth=1.8 if f["Column ID"] in in_overlap else 1.0,
        ))
        ax.plot(f["X"], f["Y"], marker="s", color="black", markersize=4)
        ax.text(f["X"], y1, f["Column ID"], ha="center", va="bottom", fontsize=7)
        for (px, py), u in zip(f["Coordinates"], f["Utilisation"]):
            ax.add_patch(Circle(
                (f["X"] + px, f["Y"] + py), dia_m / 2,
                facecolor=cmap(norm(max(u, 0.0))),
                edgecolor="blue" if u < 0 else "black",
                linewidth=2.0 if u < 0 else 0.6,
            ))
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_title(
        f"{chosen}: pile utilisation (red cap outline = overlaps a neighbour, "
        "blue pile outline = uplift)"
    )
    fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax,
                 label="Pile load / capacity", shrink=0.8)
    st.pyplot(fig)

    if overlaps:
        st.warning(
            "Overlapping caps: "
            + ", ".join(f"{a}-{b}" for a, b in overlaps[:20])
            + (" ..." if len(overlaps) > 20 else "")
        )
    if failed:
        st.warning("Not designed (> 9 piles): " + ", ".join(failed))

# =====================================================
# DOWNLOADS
# =====================================================
st.subheader("7. Export")
d1, d2 = st.columns(2)
with d1:
    st.download_button(
        "Download comparison summary (CSV)",
        summary.round(2).to_csv().encode("utf-8"),
        file_name="pile_option_comparison.csv",
        mime="text/csv",
    )
with d2:
    st.download_button(
        "Download piles per column (CSV)",
        piles_tbl.to_csv().encode("utf-8"),
        file_name="piles_per_column_by_option.csv",
        mime="text/csv",
    )

with st.expander("Assumptions"):
    st.markdown(
        "- Uses `design_foundation()` from `foundation.py` unchanged: service load "
        "= dead + live + wind, plus the % increase, plus 50 kN cap allowance per pile.\n"
        "- Pile number is found from vertical load only; moments are then used to get "
        "the max/min pile load, so a pile can exceed 100% even though the count was 'enough'.\n"
        "- Max 9 piles per column (largest pattern in `foundation.py`).\n"
        "- Cap size is the bounding rectangle of the piles plus the edge distance; "
        "overlap checks compare these rectangles in plan.\n"
        "- Units: kN, kNm, metres for X/Y, mm for diameter.\n"
        "- Cost index is only a relative indicator from the rates in the sidebar."
    )
