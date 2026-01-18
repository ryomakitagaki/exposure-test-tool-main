import pandas as pd
import streamlit as st

from internal.calculator import minimize_solver
from internal.converter import experiment_converter
from internal.interface import create_experiment_with_measurement


def create_experiment_form():
    """
    Create and display the experiment submission form with two sample tabs.
    
    Returns:
        tuple: A tuple containing (submitted, experiment_1, calculate_table_1, calculate_table_2, optimized_params)
               where submitted is a boolean indicating if the form was submitted,
               and the other values are the created objects (None if not submitted).
    """
    st.header("Create New Experiment")
    tab1, tab2 = st.tabs(["sample1", "sample2"])

    with st.form("experiment_form"):
        with tab1:
            sample_name = st.text_input("Sample Name", help="Required field", key="sample_name_1")
            thickness_mm = st.number_input("Thickness (mm)", min_value=0.0, value=1.0, step=0.1, key="thickness_mm_1")
            initial_density = st.number_input("Initial Density (kg/m³)", min_value=0.0, value=10.0, step=0.1,
                                              key="initial_density_1")
            temperature = st.number_input("Temperature (°C)", value=25.0, step=0.1, key="temperature_1")
            humidity_memo = st.text_input("Humidity Notes", help="Optional field", key="humidity_memo_1")

            df = pd.DataFrame({
                "測定日": pd.to_datetime(['2025-01-01', '2025-02-01', '2025-03-01']),
                "熱伝導率": [0.15, 0.14, 0.13],
            })
            config = {
                "測定日": st.column_config.DateColumn(
                    "測定日",
                    help="測定日を入力してください",
                ),
                "熱伝導率": st.column_config.NumberColumn(
                    "熱伝導率",
                    required=True,
                    format='%.6f'
                ),
            }
            edited_df_1 = st.data_editor(
                df,
                column_config=config,
                num_rows="dynamic",
                key="data_editor_1"
            )

        with tab2:
            sample_name_2 = st.text_input("Sample Name", help="Required field", key="sample_name_2")
            thickness_mm_2 = st.number_input("Thickness (mm)", min_value=0.0, value=1.0, step=0.1, key="thickness_mm_2")
            initial_density_2 = st.number_input("Initial Density (kg/m³)", min_value=0.0, value=10.0, step=0.1,
                                                key="initial_density_2")
            temperature_2 = st.number_input("Temperature (°C)", value=25.0, step=0.1, key="temperature_2")
            humidity_memo_2 = st.text_input("Humidity Notes", help="Optional field", key="humidity_memo_2")

            df_2 = pd.DataFrame({
                "測定日": pd.to_datetime(['2025-01-01', '2025-02-01', '2025-03-01']),
                "熱伝導率": [0.15, 0.14, 0.13],
            })
            config = {
                "測定日": st.column_config.DateColumn(
                    "測定日",
                    help="測定日を入力してください",
                ),
                "熱伝導率": st.column_config.NumberColumn(
                    "熱伝導率",
                    required=True,
                    format='%.6f'
                ),
            }
            edited_df_2 = st.data_editor(
                df_2,
                column_config=config,
                num_rows="dynamic",
                key="data_editor_2"
            )

        submitted = st.form_submit_button("Create Experiment")

        if submitted:
            # Create experiment 1
            experiment_1 = create_experiment_with_measurement(
                sample_name=sample_name,
                thickness_mm=thickness_mm,
                initial_density=initial_density,
                temperature=temperature,
                humidity_memo=humidity_memo,
                measurements=edited_df_1
            )
            calculate_table_1 = experiment_converter(experiment_1)

            # Create experiment 2
            experiment_2 = create_experiment_with_measurement(
                sample_name=sample_name_2,
                thickness_mm=thickness_mm_2,
                initial_density=initial_density_2,
                temperature=temperature_2,
                humidity_memo=humidity_memo_2,
                measurements=edited_df_2
            )
            calculate_table_2 = experiment_converter(experiment_2)

            # Optimize parameters
            optimized_params = minimize_solver(calculate_table_1, calculate_table_2, temperature)

            # Show success message
            st.success(f"Experiment created successfully!")

            return submitted, experiment_1, experiment_2, calculate_table_1, calculate_table_2, optimized_params

    return False, None, None, None, None, None
