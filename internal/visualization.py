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

    # Extract data for plotting
    elapsed_days = [row.elapsed_sec / 86400 for row in calculate_table.rows]
    actual_conductivity = [row.thermal_conductivity for row in calculate_table.rows]
    estimated_conductivity = [row.estimated_conductivity for row in calculate_table.rows]

    # --- 【追加】最大値を計算してY軸の上限を決める ---
    # 1. それぞれのリストから最大値を取り出す（データが空の場合のエラー回避のため default=0 を入れています）
    max_actual = max(actual_conductivity, default=0)
    max_estimated = max(estimated_conductivity, default=0)

    # 2. 両方を比べて、より大きい方を採用する
    overall_max = max(max_actual, max_estimated)

    # 3. 少し余裕（1.2倍 = 20%の余白）を持たせて軸の値を設定する
    # ※もし最大値が0だった場合は、とりあえず1.0にしておくという安全策も入れています
    top_limit = overall_max * 1.2 if overall_max > 0 else 1.0
    ax.set_ylim(bottom=0, top=top_limit)
    # --------------------------------------------------

    # Plot actual and estimated values
    ax.plot(elapsed_days, actual_conductivity, 'o-', label='Actual Measurements', color='blue', zorder=2, alpha=0.5)
    ax.plot(elapsed_days, estimated_conductivity, 's--', label='Estimated (Optimized Model)', color='red', zorder=1)

    # Add labels and legend
    ax.set_xlabel('経過日数 (days)')
    ax.set_ylabel('熱伝導率 (W/(m･K))')
    ax.set_title('熱伝導率の実測値と推定値の比較')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)

    return fig
