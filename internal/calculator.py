from dataclasses import dataclass, field
from typing import List

import numpy as np
from scipy import optimize

from internal.const import R_gas_constant, kelvin_constant
from internal.interface import Experiment


@dataclass
class LamdaGas:
    digit_conf: float
    solver_param: float
    actual_value: float = field(init=False)

    def __post_init__(self):
        self.update_actual_value()

    def update_actual_value(self):
        self.actual_value = self.digit_conf * self.solver_param


@dataclass
class Edash:
    digit_conf: float
    solver_param: float
    actual_value: float = field(init=False)

    def __post_init__(self):
        self.update_actual_value()

    def update_actual_value(self):
        self.actual_value = self.digit_conf * self.solver_param


@dataclass
class K_0:
    digit_conf: float
    solver_param: float
    actual_value: float = field(init=False)

    def __post_init__(self):
        self.update_actual_value()

    def update_actual_value(self):
        self.actual_value = self.digit_conf * self.solver_param


@dataclass
class OptimizeParam:
    lamda_gas: LamdaGas
    e_dash: Edash
    k_0: K_0


def estimate_thermal_conductivity(
        e_dash: Edash,
        experiment_temperature: float,
        measurement_time_sec: float,
        lamda_gas: LamdaGas,
        initial_thermal_conductivity: float,
        k_0: K_0,
) -> float:
    e_dash.update_actual_value()
    lamda_gas.update_actual_value()
    k_0.update_actual_value()
    abs_temperature = experiment_temperature + kelvin_constant

    inner_exponent = -e_dash.actual_value / (R_gas_constant * abs_temperature)
    middle_term = k_0.actual_value * measurement_time_sec * np.exp(inner_exponent)
    
    # --- 変更前 ---
    #numerator = 1 - np.exp(middle_term)
    #denominator = np.exp(middle_term)
    #result = -lamda_gas.actual_value * (numerator / denominator) + initial_thermal_conductivity
    
    # --- 変更後（数式変形：割り算を回避）---
    # (1 - exp(x)) / exp(x) は exp(-x) - 1 と等価です。
    # xが巨大になっても、exp(-x)は0に近づくだけなのでエラーになりません。
    term = np.exp(-middle_term) - 1
    result = -lamda_gas.actual_value * term + initial_thermal_conductivity

    return result


@dataclass
class CalculateRow:
    elapsed_sec: float
    thermal_conductivity: float
    estimated_conductivity: float = field(init=False)
    diff_conductivity: float = field(init=False)
    diff_area: float = field(init=False)

    def __post_init__(self):
        self.estimated_conductivity = 0
        self.diff_conductivity = abs(self.thermal_conductivity - self.estimated_conductivity)
        self.diff_area = 0

    def update_diff(self):
        self.diff_conductivity = abs(self.thermal_conductivity - self.estimated_conductivity)


@dataclass
class CalculateTable:
    rows: List[CalculateRow]

    def calculate_diff_area(self, row: CalculateRow, prev_row: CalculateRow):
        time_delta = row.elapsed_sec - prev_row.elapsed_sec
        # 台形の高さ（誤差の平均） × 底辺（時間）
        # |誤差1| + |誤差2| / 2 * Δt
        area = (abs(prev_row.diff_conductivity) + abs(row.diff_conductivity)) / 2 * time_delta
        row.diff_area = area

    def total_area(self):
        total = 0
        for row in self.rows:
            total += row.diff_area
        return total

    def estimate_thermal_conductivity(self, e_dash: Edash, lamda_gas: LamdaGas, experiment_temperature: float, k_0: K_0):
        initial_thermal_conductivity = self.rows[0].thermal_conductivity
        for row in self.rows:
            row.estimated_conductivity = estimate_thermal_conductivity(
                e_dash=e_dash,
                experiment_temperature=experiment_temperature,
                measurement_time_sec=row.elapsed_sec,
                lamda_gas=lamda_gas,
                initial_thermal_conductivity=initial_thermal_conductivity,
                k_0=k_0,
            )

    def update_all_metrix(self):
        for i in range(len(self.rows)):
            self.rows[i].update_diff()
            if i > 0:
                self.calculate_diff_area(self.rows[i], self.rows[i - 1])


def create_calculate_table(experiment: Experiment) -> CalculateTable:
    rows = []
    for i, measurement in enumerate(experiment.measurements):
        rows.append(CalculateRow(
            elapsed_sec=measurement.elapsed_days * 86400,
            thermal_conductivity=measurement.thermal_conductivity,
        ))
    return CalculateTable(rows=rows)


def minimize_solver(calculate_table_1: CalculateTable, calculate_table_2: CalculateTable,
                    experiment_temperature_1: float, experiment_temperature_2: float) -> OptimizeParam:
    """
    Find the optimal solver parameters that minimize the difference between 
    estimated and actual thermal conductivity measurements.

    Args:
        calculate_table (CalculateTable): Table containing thermal conductivity measurements
        experiment_temperature (float): Temperature at which the experiment was conducted

    Returns:
        OptimizeParam: Optimized parameters for LamdaGas and Edash
    """
    # Initial parameter guesses
    # initial_params = np.array([6.0, 3.0])

    # Parameter bounds (adjust as needed)
    # lamda_gas, e_dash, k0の範囲設定
    bounds = [(1.0, 100.0), (1.0, 1000.0), (1.0, 1000.0), ]


    # Define the objective function to minimize
    def objective_function(params: List[float]) -> float:
        # 【変更点1】関数の最初から try を開始します（これで準備段階のエラーも逃しません）
        try:
            lamda_gas_param, e_dash_param, k0_param = params

            # Create parameter objects with the current values
            lamda_gas = LamdaGas(digit_conf=0.0001, solver_param=lamda_gas_param)
            e_dash = Edash(digit_conf=100, solver_param=e_dash_param)
            k_0 = K_0(digit_conf=0.001, solver_param=k0_param)

            # Update the actual values
            lamda_gas.update_actual_value()
            e_dash.update_actual_value()
            k_0.update_actual_value()

            # Calculate estimated thermal conductivity for each row
            calculate_table_1.estimate_thermal_conductivity(
                e_dash=e_dash,
                lamda_gas=lamda_gas,
                experiment_temperature=experiment_temperature_1,
                k_0=k_0,
            )

            # Update metrics and calculate total difference area
            calculate_table_1.update_all_metrix()
            total_diff_area_1 = calculate_table_1.total_area()
            
            # Calculate estimated thermal conductivity for each row
            calculate_table_2.estimate_thermal_conductivity(
                e_dash=e_dash,
                lamda_gas=lamda_gas,
                experiment_temperature=experiment_temperature_2,
                k_0=k_0,
            )

            # Update metrics and calculate total difference area
            calculate_table_2.update_all_metrix()
            total_diff_area_2 = calculate_table_2.total_area()

            total_diff_area = total_diff_area_1 + total_diff_area_2

            elapsed_sec = calculate_table_1.rows[-1].elapsed_sec
            
            # スコア計算
            final_score = total_diff_area / elapsed_sec

            # 【変更点2】flush=Trueをつけて、計算中のスコアを強制表示（動作確認用）
            # ログが流れすぎるのが嫌な場合は、ここをコメントアウトしてください
            # print(f"Step Score: {final_score}", flush=True)

            # もし計算結果が NaN や Inf になっていたらエラー扱いにする
            if not np.isfinite(final_score):
                 return 1e20

            return final_score

        except Exception as e:
            # 【変更点3】エラー内容を flush=True で強制表示させる
            print(f"★計算エラー発生: {e}", flush=True) 
            import traceback
            traceback.print_exc() # 詳しいエラー場所を表示
            # ---------------------------------------
            return 1e20

    # Run the optimization
    result = optimize.differential_evolution(
        func=objective_function,
        bounds=bounds,

        # --- 追加・変更箇所 ---
        # --- 修正版（rand1bin用） ---
        strategy='rand1bin',   # 広く探す設定（OKです）
        maxiter=100,          # 収束が遅いので多めに（OKです）
        popsize=50,            # 【修正】1000→50（これで十分性能が出ます）
        mutation=(0.5, 1.0),   # 【修正】上限を1.9→1.0に（これで安定します）
        recombination=0.9,     # 交叉率高め（OKです）
        tol=0,                 # 【奥の手】収束判定を0にします（＝どんなに値が揃っても止まらない）
        atol=-1,               # 【奥の手】絶対誤差判定も無効化します（＝maxiterまで必ず走り続ける）
        polish=True,           # 必須（OKです）
        workers=1,             # OKです
        disp=True              # OKです
    )

    # Extract the optimized parameters
    optimized_lamda_gas_param, optimized_e_dash_param, optimized_k_0_param = result.x
    # Create and return the optimized parameters
    lamda_gas = LamdaGas(digit_conf=0.0001, solver_param=optimized_lamda_gas_param)
    e_dash = Edash(digit_conf=100, solver_param=optimized_e_dash_param)
    k_0 = K_0(digit_conf=0.001, solver_param=optimized_k_0_param)

    # Update the actual values
    lamda_gas.update_actual_value()
    e_dash.update_actual_value()
    k_0.update_actual_value()

    return OptimizeParam(lamda_gas=lamda_gas, e_dash=e_dash, k_0=k_0)
