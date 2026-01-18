import pandas as pd
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class MeasurementData:
    """Dataclass replacement for Protocol Buffer MeasurementData message."""
    id: int = 0
    measurement_date: datetime = field(default_factory=datetime.now)
    elapsed_days: int = 0  # output only
    thermal_conductivity: float = 0.0
    thermal_conductivity_increase: float = 0.0  # output only

    # For compatibility with converter.py
    @property
    def elapsed_sec(self) -> int:
        return self.elapsed_days * 86400


@dataclass
class Experiment:
    """Dataclass replacement for Protocol Buffer Experiment message."""
    id: str = ""  # output only
    sample_name: str = ""
    thickness_mm: float = 0.0
    initial_density: float = 0.0
    temperature: float = 0.0
    humidity_memo: str = ""
    measurements: List[MeasurementData] = field(default_factory=list)


def create_experiment_with_measurement(
        sample_name: str,
        thickness_mm: float,
        initial_density: float,
        temperature: float,
        humidity_memo: str,
        measurements: pd.DataFrame
) -> Experiment:
    """Create an Experiment with measurements from a pandas DataFrame."""
    experiment = Experiment(
        sample_name=sample_name,
        thickness_mm=thickness_mm,
        initial_density=initial_density,
        temperature=temperature,
        humidity_memo=humidity_memo
    )

    measurement_data = []
    for _, row in measurements.iterrows():
        measurement_data.append(
            MeasurementData(
                measurement_date=row['測定日'],
                thermal_conductivity=row['熱伝導率']
            ))

    # Add measurements to experiment
    experiment.measurements.extend(measurement_data)

    # Calculate elapsed_days and thermal_conductivity_increase
    if measurement_data:
        first_measurement = measurement_data[0]
        for i, measurement in enumerate(measurement_data):
            if i > 0:
                # Calculate elapsed days from the first measurement
                days_diff = (measurement.measurement_date - first_measurement.measurement_date).total_seconds() / 86400
                measurement.elapsed_days = int(days_diff)
                measurement.thermal_conductivity_increase = measurement.thermal_conductivity - first_measurement.thermal_conductivity

    return experiment
