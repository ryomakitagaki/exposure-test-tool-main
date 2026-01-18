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
        experiment_temperature: int,
        measurement_time_sec: int,
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
    # numerator = 1 - np.exp(middle_term)
    # denominator = np.exp(middle_term)
    # result = -lamda_gas.actual_value * (numerator / denominator) + initial_thermal_conductivity
    
    # --- 変更後（数式変形：割り算を回避）---
    # (1 - exp(x)) / exp(x) は exp(-x) - 1 と等価です。
    # xが巨大になっても、exp(-x)は0に近づくだけなのでエラーになりません。
    term = np.exp(-middle_term) - 1
    result = -lamda_gas.actual_value * term + initial_thermal_conductivity

    return result


@dataclass
class CalculateRow:
    elapsed_sec: int
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
        # |誤差1 + 誤差2| / 2 * Δt
        area = (prev_row.diff_conductivity + row.diff_conductivity) / 2 * time_delta
        row.diff_area = abs(area)

    def total_area(self):
        total = 0
        for row in self.rows:
            total += row.diff_area
        return total

    def estimate_thermal_conductivity(self, e_dash: Edash, lamda_gas: LamdaGas, experiment_temperature: int, k_0: K_0):
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
                    experiment_temperature: int) -> OptimizeParam:
    """
    Find the optimal solver parameters that minimize the difference between 
    estimated and actual thermal conductivity measurements.

    Args:
        calculate_table (CalculateTable): Table containing thermal conductivity measurements
        experiment_temperature (int): Temperature at which the experiment was conducted

    Returns:
        OptimizeParam: Optimized parameters for LamdaGas and Edash
    """
    # Initial parameter guesses
    # initial_params = np.array([6.0, 3.0])

    # Parameter bounds (adjust as needed)
    # lamda_gas, e_dash, k0の範囲設定
    bounds = [(0.0001, 0.01), (100, 100000), (0.000001, 1), ]

    # Define the objective function to minimize
    def objective_function(params: List[float]) -> float:
        lamda_gas_param, e_dash_param, k0_param = params

        # Create parameter objects with the current values
        lamda_gas = LamdaGas(digit_conf=1, solver_param=lamda_gas_param)
        e_dash = Edash(digit_conf=1, solver_param=e_dash_param)
        k_0 = K_0(digit_conf=1, solver_param=k0_param)

        # Update the actual values
        lamda_gas.update_actual_value()
        e_dash.update_actual_value()
        k_0.update_actual_value()

        # --- エラー回避用の try-except ブロックを追加 ---
        try:

            # Calculate estimated thermal conductivity for each row
            calculate_table_1.estimate_thermal_conductivity(
                e_dash=e_dash,
                lamda_gas=lamda_gas,
                experiment_temperature=experiment_temperature,
                k_0=k_0,
            )

            # Update metrics and calculate total difference area
            calculate_table_1.update_all_metrix()
            total_diff_area_1 = calculate_table_1.total_area()
            # Calculate estimated thermal conductivity for each row
            calculate_table_2.estimate_thermal_conductivity(
                e_dash=e_dash,
                lamda_gas=lamda_gas,
                experiment_temperature=experiment_temperature,
                k_0=k_0,
            )

            # Update metrics and calculate total difference area
            calculate_table_2.update_all_metrix()
            total_diff_area_2 = calculate_table_2.total_area()

            total_diff_area = total_diff_area_1 + total_diff_area_2

            elapsed_sec = calculate_table_1.rows[-1].elapsed_sec
            
            #return total_diff_area / elapsed_sec

            final_score = total_diff_area / elapsed_sec

                # もし計算結果が NaN や Inf になっていたらエラー扱いにする
            if not np.isfinite(final_score):
                return 1e20 # 巨大な値を返して、このパラメータを却下させる

            return final_score

        except Exception:
            # 計算中にエラー（オーバーフローなど）が起きた場合も
            # 巨大な値を返して回避させる
            return 1e20

    # Run the optimization
    result = optimize.differential_evolution(
        func=objective_function,
        bounds=bounds,

        # --- 追加・変更箇所 ---
        strategy='best1bin',   # デフォルト'best1bin' もう少し広くランダムに見る：rand1bin
        maxiter=1000,          # 10000は多すぎたので、1000回で十分です
        popsize=50,            # デフォルト(15)の数倍。個体数を増やして探索密度を上げる
        mutation=(0.5, 1.0),   # 変異率を高く設定し、広く探索させる
        recombination=0.7,     # 交叉率
        tol=1e-6,              # 収束判定を厳しくする（相対許容誤差）
        atol=1e-6,             # 収束判定を厳しくする（絶対許容誤差）
        polish=True,           # 【最重要】最後に局所探索で「仕上げ」をする
        workers=1,              # 1：CPUコア１個で計算，-1：全CPUコアを使って並列化する
        disp=True              # 【追加】黒い画面（コンソール）に進捗状況が表示される
    )

    # Extract the optimized parameters
    optimized_lamda_gas_param, optimized_e_dash_param, optimized_k_0_param = result.x
    # Create and return the optimized parameters
    lamda_gas = LamdaGas(digit_conf=1, solver_param=optimized_lamda_gas_param)
    e_dash = Edash(digit_conf=1, solver_param=optimized_e_dash_param)
    k_0 = K_0(digit_conf=1, solver_param=optimized_k_0_param)

    # Update the actual values
    lamda_gas.update_actual_value()
    e_dash.update_actual_value()
    k_0.update_actual_value()

    return OptimizeParam(lamda_gas=lamda_gas, e_dash=e_dash, k_0=k_0)
