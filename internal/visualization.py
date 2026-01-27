import japanize_matplotlib
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_thermal_conductivity_plot(calculate_table):
    """
    Create a plot comparing actual vs. estimated thermal conductivity.

    Args:
        calculate_table: The calculation table containing measurement data
        optimized_params: The optimized parameters
        temperature: The experiment temperature

    Returns:
        A plotly figure object
    """
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
    # --------------------------------------------------

    # Create plotly figure
    fig = go.Figure()

    # Add traces for actual and estimated values
    fig.add_trace(go.Scatter(
        x=elapsed_days,
        y=actual_conductivity,
        mode='lines+markers',
        name='Actual Measurements',
        line=dict(color='blue', width=2),
        marker=dict(symbol='circle', size=8),
        opacity=0.7
    ))

    fig.add_trace(go.Scatter(
        x=elapsed_days,
        y=estimated_conductivity,
        mode='lines+markers',
        name='Estimated (Optimized Model)',
        line=dict(color='red', width=2, dash='dash'),
        marker=dict(symbol='square', size=8)
    ))

    # Update layout
    fig.update_layout(
        title='熱伝導率の実測値と推定値の比較',
        xaxis_title='経過日数 (days)',
        yaxis_title='熱伝導率 (W/(m･K))',
        yaxis=dict(range=[0, top_limit]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        template="plotly_white",
        height=600,
        width=800
    )

    # Add grid
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(0,0,0,0.1)')

    return fig
