import pandas as pd
import streamlit as st

from foundation import (
    design_foundation,
    load_columns_sheet,
    overlapping_caps,
    plot_building_plan,
    plot_foundation,
)

# =====================================================
# PAGE SETTINGS
# =====================================================
st.set_page_config(
    page_title="Pile Foundation Layout Generator",
    layout="wide"
)

st.title("Pile Foundation Layout Generator")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("Pile Design Parameters")

pile_diameter = st.sidebar.number_input(
    "Pile Diameter (mm)", value=600.0, step=50.0
)

pile_capacity = st.sidebar.number_input(
    "Pile Capacity (kN)", value=1800.0, step=100.0
)

spacing_factor = st.sidebar.number_input(
    "Pile Spacing (D)", value=3.0, step=0.5
)

load_increase_percent = st.sidebar.number_input(
    "Additional Load Increase (%)", value=10.0, step=1.0
)

edge_factor = st.sidebar.number_input(
    "Pile centre to cap edge (x D)",
    value=1.0, step=0.1, min_value=0.5,
    help="Sets the pile cap outline in the plans."
)

pile_spacing = (pile_diameter / 1000) * spacing_factor

# =====================================================
# FILE UPLOAD
# =====================================================
uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Upload an Excel file with a sheet named 'Columns'.")
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
# PARAMETERS TABLE
# =====================================================
st.subheader("Pile Parameters")

parameters_df = pd.DataFrame({
    "Parameter": [
        "Pile Diameter",
        "Pile Capacity",
        "Pile Spacing",
        "Centre to Centre Spacing",
        "Pile Cap Allowance",
        "Load Increase",
    ],
    "Value": [
        f"{pile_diameter:.0f} mm",
        f"{pile_capacity:.0f} kN",
        f"{spacing_factor:.1f} D",
        f"{pile_spacing:.2f} m",
        "50 kN per pile",
        f"{load_increase_percent:.1f} %",
    ]
})

st.dataframe(parameters_df, hide_index=True)

# =====================================================
# DESIGN FOUNDATIONS
# =====================================================
results = []
failed = []

for _, row in columns_df.iterrows():
    try:
        results.append(
            design_foundation(
                row=row,
                pile_capacity=pile_capacity,
                spacing_factor=spacing_factor,
                pile_diameter=pile_diameter,
                load_increase_percent=load_increase_percent,
                edge_factor=edge_factor,
            )
        )
    except ValueError as e:
        failed.append({"Column ID": row["Column ID"], "Reason": str(e)})

if failed:
    st.warning(
        "These columns were left out of the results "
        "(they need more than 9 piles with the current pile size):"
    )
    st.dataframe(pd.DataFrame(failed), hide_index=True)

if not results:
    st.error("No foundations could be designed with these parameters.")
    st.stop()

overlaps = overlapping_caps(results)
overlap_map = {}
for a, b in overlaps:
    overlap_map.setdefault(a, []).append(b)
    overlap_map.setdefault(b, []).append(a)

# =====================================================
# FOUNDATION SCHEDULE
# =====================================================
schedule = pd.DataFrame([
    {
        "Column ID": f["Column ID"],
        "X": f["X"],
        "Y": f["Y"],
        "Load (kN)": round(f["Load"], 1),
        "No. Piles": f["Piles"],
        "Max Pile Load (kN)": round(f["Max Pile Load"], 1),
        "Min Pile Load (kN)": round(f["Min Pile Load"], 1),
        "Cap Area (m2)": round(f["CapArea"], 2),
        "Cap Overlaps With": ", ".join(overlap_map.get(f["Column ID"], [])),
    }
    for f in results
])

st.subheader("Foundation Schedule")
st.dataframe(schedule)

# =====================================================
# BUILDING PLAN
# =====================================================
st.subheader("Building Foundation Plan")
st.pyplot(plot_building_plan(results))

# =====================================================
# INDIVIDUAL FOUNDATION
# =====================================================
st.subheader("Individual Foundation Layout")

selected_column = st.selectbox("Select Column", schedule["Column ID"])

selected_foundation = next(
    f for f in results if f["Column ID"] == selected_column
)

col1, col2 = st.columns([3, 1])

with col1:
    st.pyplot(plot_foundation(selected_foundation))

with col2:
    st.markdown("### Foundation Summary")
    st.write(f"**Column:** {selected_foundation['Column ID']}")
    st.write(f"**No. Piles:** {selected_foundation['Piles']}")
    st.write(f"**Total Load:** {selected_foundation['Load']:.1f} kN")
    st.write(f"**Maximum Pile Load:** {selected_foundation['Max Pile Load']:.1f} kN")
    st.write(f"**Minimum Pile Load:** {selected_foundation['Min Pile Load']:.1f} kN")
    st.write(f"**Cap Area:** {selected_foundation['CapArea']:.2f} m2")

# =====================================================
# DOWNLOAD SCHEDULE
# =====================================================
csv = schedule.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Schedule CSV",
    data=csv,
    file_name="foundation_schedule.csv",
    mime="text/csv"
)
