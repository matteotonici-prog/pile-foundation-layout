import streamlit as st
import pandas as pd

from foundation import (
    design_foundation,
    plot_foundation,
    plot_building_plan
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
    "Pile Diameter (mm)",
    value=600.0,
    step=50.0
)

pile_capacity = st.sidebar.number_input(
    "Pile Capacity (kN)",
    value=1800.0,
    step=100.0
)

spacing_factor = st.sidebar.number_input(
    "Pile Spacing (D)",
    value=3.0,
    step=0.5
)

load_increase_percent = st.sidebar.number_input(
    "Additional Load Increase (%)",
    value=10.0,
    step=1.0
)

pile_spacing = (
    pile_diameter / 1000
) * spacing_factor

# =====================================================
# FILE UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# =====================================================
# MAIN
# =====================================================

if uploaded_file is not None:

    try:

        columns_df = pd.read_excel(
            uploaded_file,
            sheet_name="Columns"
        )

        # ===================================
        # PARAMETERS TABLE
        # ===================================

        st.subheader("Pile Parameters")

        parameters_df = pd.DataFrame({

            "Parameter": [

                "Pile Diameter",

                "Pile Capacity",

                "Pile Spacing",

                "Centre to Centre Spacing",

                "Pile Cap Allowance",

                "Load Increase"
            ],

            "Value": [

                f"{pile_diameter:.0f} mm",

                f"{pile_capacity:.0f} kN",

                f"{spacing_factor:.1f} D",

                f"{pile_spacing:.2f} m",

                "50 kN per pile",

                f"{load_increase_percent:.1f} %"
            ]
        })

        st.dataframe(
            parameters_df,
            hide_index=True,
            use_container_width=True
        )

        # ===================================
        # DESIGN FOUNDATIONS
        # ===================================

        results = []

        for _, row in columns_df.iterrows():

            foundation = design_foundation(
                row=row,
                pile_capacity=pile_capacity,
                spacing_factor=spacing_factor,
                pile_diameter=pile_diameter,
                load_increase_percent=load_increase_percent
            )

            results.append(foundation)

        # ===================================
        # FOUNDATION SCHEDULE
        # ===================================

        schedule = pd.DataFrame([
            {
                "Column ID":
                    f["Column ID"],

                "X":
                    f["X"],

                "Y":
                    f["Y"],

                "Load (kN)":
                    round(f["Load"], 1),

                "No. Piles":
                    f["Piles"],

                "Max Pile Load (kN)":
                    round(f["Max Pile Load"], 1),

                "Min Pile Load (kN)":
                    round(f["Min Pile Load"], 1)

            }
            for f in results
        ])

        st.subheader("Foundation Schedule")

        st.dataframe(
            schedule,
            use_container_width=True
        )

        # ===================================
        # BUILDING PLAN
        # ===================================

        st.subheader("Building Foundation Plan")

        fig_plan = plot_building_plan(
            results
        )

        st.pyplot(fig_plan)

        # ===================================
        # INDIVIDUAL FOUNDATION
        # ===================================

        st.subheader(
            "Individual Foundation Layout"
        )

        selected_column = st.selectbox(
            "Select Column",
            schedule["Column ID"]
        )

        selected_foundation = next(
            f for f in results
            if f["Column ID"] == selected_column
        )

        col1, col2 = st.columns([3, 1])

        with col1:

            fig = plot_foundation(
                selected_foundation
            )

            st.pyplot(fig)

        with col2:

            st.markdown("### Foundation Summary")

            st.write(
                f"**Column:** "
                f"{selected_foundation['Column ID']}"
            )

            st.write(
                f"**No. Piles:** "
                f"{selected_foundation['Piles']}"
            )

            st.write(
                f"**Total Load:** "
                f"{selected_foundation['Load']:.1f} kN"
            )

            st.write(
                f"**Maximum Pile Load:** "
                f"{selected_foundation['Max Pile Load']:.1f} kN"
            )

            st.write(
                f"**Minimum Pile Load:** "
                f"{selected_foundation['Min Pile Load']:.1f} kN"
            )

        # ===================================
        # DOWNLOAD SCHEDULE
        # ===================================

        csv = schedule.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download Schedule CSV",
            data=csv,
            file_name="foundation_schedule.csv",
            mime="text/csv"
        )

    except Exception as e:

        st.error(f"Error: {e}")

else:

    st.info(
        "Upload an Excel file with a sheet named 'Columns'."
    )
