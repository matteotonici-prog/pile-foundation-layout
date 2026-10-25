import streamlit as st
import pandas as pd

from foundation import (
    design_foundation,
    plot_foundation,
    plot_building_plan
)

st.set_page_config(
    page_title="Pile Foundation Layout Generator",
    layout="wide"
)

st.title("Pile Foundation Layout Generator")

st.sidebar.header("Design Parameters")

load_increase_percent = st.sidebar.number_input(
    "Additional Load Increase (%)",
    min_value=0.0,
    max_value=100.0,
    value=10.0,
    step=1.0
)

uploaded_file = st.file_uploader(
    "Upload Excel File",
    type=["xlsx"]
)

if uploaded_file is not None:

    try:

        columns_df = pd.read_excel(
            uploaded_file,
            sheet_name="Columns"
        )

        pile_df = pd.read_excel(
            uploaded_file,
            sheet_name="PileProperties"
        )

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

        schedule = pd.DataFrame([
            {
                "Column ID": f["Column ID"],
                "X": f["X"],
                "Y": f["Y"],
                "Total Load (kN)": round(f["Load"], 1),
                "No. Piles": f["Piles"],
                "Max Pile Load (kN)": round(f["Max Pile Load"], 1),
                "Min Pile Load (kN)": round(f["Min Pile Load"], 1)
            }
            for f in results
        ])

        st.subheader("Foundation Schedule")
        st.dataframe(schedule, use_container_width=True)

        st.subheader("Building Foundation Plan")

        fig_plan = plot_building_plan(results)

        st.pyplot(fig_plan)

        st.subheader("Individual Foundation")

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

            st.markdown("### Summary")

            st.write(
                f"**Piles:** {selected_foundation['Piles']}"
            )

            st.write(
                f"**Load:** {selected_foundation['Load']:.1f} kN"
            )

            st.write(
                f"**Max Reaction:** "
                f"{selected_foundation['Max Pile Load']:.1f} kN"
            )

            st.write(
                f"**Min Reaction:** "
                f"{selected_foundation['Min Pile Load']:.1f} kN"
            )

            st.write(
                f"**Load Increase:** "
                f"{load_increase_percent:.1f}%"
            )

    except Exception as e:

        st.error(f"Error: {e}")

else:

    st.info("Upload an Excel file to begin.")
