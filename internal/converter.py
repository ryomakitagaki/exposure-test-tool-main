from internal.calculator import CalculateTable, CalculateRow
from internal.interface import Experiment


def experiment_converter(experiment_data: Experiment) -> CalculateTable:
    rows = []
    for measurement in experiment_data.measurements:
        row = CalculateRow(
            elapsed_sec=measurement.elapsed_sec,
            thermal_conductivity=measurement.thermal_conductivity,
        )
        rows.append(row)
    return CalculateTable(rows=rows)
