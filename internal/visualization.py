import japanize_matplotlib
import matplotlib.pyplot as plt


def create_thermal_conductivity_plot(calculate_table):
    """
    Create a plot comparing actual vs. estimated thermal conductivity.
    
    Args:
        calculate_table: The calculation table containing measurement data
        optimized_params: The optimized parameters
        temperature: The experiment temperature
        
    Returns:
        A matplotlib figure object
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_ylim(0, 0.03)  # y軸の範囲を0から0.1に設定

    # Extract data for plotting
    elapsed_days = [row.elapsed_sec / 86400 for row in calculate_table.rows]
    actual_conductivity = [row.thermal_conductivity for row in calculate_table.rows]
    estimated_conductivity = [row.estimated_conductivity for row in calculate_table.rows]

    # Plot actual and estimated values
    ax.plot(elapsed_days, actual_conductivity, 'o-', label='Actual Measurements', color='blue')
    ax.plot(elapsed_days, estimated_conductivity, 's--', label='Estimated (Optimized Model)', color='red')

    # Add labels and legend
    ax.set_xlabel('経過日数 (days)')
    ax.set_ylabel('熱伝導率 (W/(m･K))')
    ax.set_title('熱伝導率の実測値と推定値の比較')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)

    return fig
