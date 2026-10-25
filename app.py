import streamlit as st
import pandas as pd

from foundation import (
    design_foundation,
    plot_foundation,
    plot_building_plan
)

# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="Pile Foundation Layout Generator",
    layout="wide"
)

st.title("Pile Foundation Layout Generator")

st.write(
    "Upload an Excel file containing column loads and pile properties."
)

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

# --------------------------------------------------
# RUN DESIGN
# --------------------------------------------------

if uploaded_file is not None:

    try:

        # Read Excel sheets
        columns_df = pd.read_excel(
            uploaded_file,
            sheet_name="Columns"
        )

        pile_df = pd.read_excel(
            uploaded_file,
            sheet_name="PileProperties"
        )

        # Extract pile properties
        pile_capacity = float(
            pile_df.loc[
                pile_df["Parameter"] == "Compression Capacity",
                "Value"
            ].iloc[0]
        )

        pile_diameter = float(
            pile_df.loc[
                pile_df["Parameter"] == "Pile Diameter",
                "Value"
            ].iloc[0]
        )

        spacing_factor = float(
            pile_df.loc[
                pile_df["Parameter"] == "Pile Spacing Factor",
                "Value"
            ].iloc[0]
        )

        # Store results
        results = []

        for _, row in columns_df.iterrows():

            foundation = design_foundation(
                row=row,
                pile_capacity=pile_capacity,
                spacing_factor=spacing_factor,
                pile_diameter=pile_diameter
            )

            results.append(foundation)

        # --------------------------------------------------
        # SCHEDULE
        # --------------------------------------------------

        schedule = pd.DataFrame([
            {
                "Column ID": r["Column ID"],
                "X": r["X"],
                "Y": r["Y"],
                "Load (kN)": round(r["Load"], 1),
                "No. Piles": r["Piles"],
                "Max Pile Load (kN)": r["Max Pile Load"],
                "Min Pile Load (kN)": r["Min Pile Load"]
            }
            for r in results
        ])

        st.subheader("Foundation Schedule")

        st.dataframe(
            schedule,
            use_container_width=True
        )

        # --------------------------------------------------
        # BUILDING PLAN
        # --------------------------------------------------

        st.subheader("Building Foundation Plan")

        fig_plan = plot_building_plan(results)

        st.pyplot(fig_plan)

        # --------------------------------------------------
        # FOUNDATION VIEWER
        # --------------------------------------------------

        st.subheader("Individual Foundation")

        selected_column = st.selectbox(
            "Select Column",
            schedule["Column ID"]
        )

        selected_foundation = next(
            f for f in results
            if f["Column ID"] == selected_column
        )

        col1, col2 = st.columns([2, 1])

        with col1:

            fig_foundation = plot_foundation(
                selected_foundation
            )

            st.pyplot(fig_foundation)

        with col2:

            st.markdown("### Foundation Details")

            st.write(
                f"**Column:** {selected_foundation['Column ID']}"
            )

            st.write(
                f"**Number of Piles:** {selected_foundation['Piles']}"
            )

            st.write(
                f"**Foundation Load:** "
                f"{selected_foundation['Load']:.1f} kN"
            )

            st.write(
                f"**Maximum Pile Reaction:** "
                f"{selected_foundation['Max Pile Load']:.1f} kN"
            )

            st.write(
                f"**Minimum Pile Reaction:** "
                f"{selected_foundation['Min Pile Load']:.1f} kN"
            )

        # --------------------------------------------------
        # DOWNLOAD RESULTS
        # --------------------------------------------------

        st.subheader("Download Schedule")

        csv = schedule.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            label="Download CSV Schedule",
            data=csv,
            file_name="foundation_schedule.csv",
            mime="text/csv"
        )

    except Exception as e:

        st.error(
            f"Error reading file: {e}"
        )

else:

    st.info(
        "Upload an Excel file to begin."
    )
