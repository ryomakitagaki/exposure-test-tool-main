import streamlit as st

from internal.form import create_experiment_form
from internal.visualization import create_thermal_conductivity_plot

# Set page configuration
st.set_page_config(
    page_title="Thermal Conductivity Prediction Model",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Title and description
st.title("Thermal Conductivity Prediction Model")
st.markdown("""
This tool helps analyze thermal conductivity measurements and optimize parameters for thermal conductivity estimation.
""")

# Initialize session state for storing experiment data
if 'experiment' not in st.session_state:
    st.session_state.experiment = None
if 'calculate_table_1' not in st.session_state:
    st.session_state.calculate_table_1 = None
if 'calculate_table_2' not in st.session_state:
    st.session_state.calculate_table_2 = None
if 'optimized_params' not in st.session_state:
    st.session_state.optimized_params = None

# Create Experiment Page
submitted, experiment_1, experiment_2, calculate_table_1, calculate_table_2, optimized_params = create_experiment_form()
if submitted:
    # Update session state with form results
    st.session_state.experiment_1 = experiment_1
    st.session_state.experiment_2 = experiment_2
    st.session_state.calculate_table_1 = calculate_table_1
    st.session_state.calculate_table_2 = calculate_table_2
    st.session_state.optimized_params = optimized_params

# Display optimization results if available
if st.session_state.optimized_params is not None and st.session_state.calculate_table_1 is not None:
    st.header("Optimization Results")

    # Extract parameters
    optimized_params = st.session_state.optimized_params

    st.subheader("Thermal Conductivity: Actual vs. Estimated")

    # Display parameter values
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"sample01 condition: {st.session_state.experiment_1.sample_name}")
        result_thermal_conductivity = optimized_params.lamda_gas.actual_value + \
                                      st.session_state.experiment_1.measurements[0].thermal_conductivity
        fig = create_thermal_conductivity_plot(
            calculate_table=st.session_state.calculate_table_1,
        )
        st.pyplot(fig)
        results_1 = {
            str(st.session_state.experiment_1.temperature) + "(°C)"+ "暴露:長期経過後の収束値 Lconv[W/(m･K)]": f"{result_thermal_conductivity:.4f} W/(m･K)",
            "λgas[W/(m･K)]": f"{optimized_params.lamda_gas.actual_value:.4f} W/(m･K)",
            "E[J/mol]": f"{optimized_params.e_dash.actual_value:.1f} J/mol",
            "k₀[-]": f"{optimized_params.k_0.actual_value:.6f} -",
        }
        st.table(results_1, border="horizontal")
    with col2:
        st.info(f"sample02 condition: {st.session_state.experiment_2.sample_name}")
        result_thermal_conductivity = optimized_params.lamda_gas.actual_value + \
                                      st.session_state.experiment_2.measurements[0].thermal_conductivity
        fig = create_thermal_conductivity_plot(
            calculate_table=st.session_state.calculate_table_2,
        )
        st.pyplot(fig)
        results_2 = {
            str(st.session_state.experiment_2.temperature) + "(°C)"+ "暴露：長期経過後の収束値 Lconv[W/(m･K)]": f"{result_thermal_conductivity:.4f} W/(m･K)",
            "λgas[W/(m･K)]": f"{optimized_params.lamda_gas.actual_value:.4f} W/(m･K)",
            "E[J/mol]": f"{optimized_params.e_dash.actual_value:.1f} J/mol",
            "k₀[-]": f"{optimized_params.k_0.actual_value:.6f} -",
        }
        st.table(results_2, border="horizontal")
