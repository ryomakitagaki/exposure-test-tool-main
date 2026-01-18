import json
import os
from datetime import datetime
from typing import List

from internal.interface import Experiment, MeasurementData


def read_interface(file_path):
    """
    Read and parse a JSON file into an Experiment dataclass object.

    Args:
        file_path (str): Path to the JSON file containing experiment data.

    Returns:
        Experiment: The parsed experiment data.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
        Exception: For other parsing errors.
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read JSON file
        with open(file_path, 'r') as f:
            json_data = json.load(f)

        # Create Experiment object
        experiment = Experiment(
            id=json_data.get('id', ''),
            sample_name=json_data.get('sample_name', ''),
            thickness_mm=json_data.get('thickness_mm', 0.0),
            initial_density=json_data.get('initial_density', 0.0),
            temperature=json_data.get('temperature', 0.0),
            humidity_memo=json_data.get('humidity_memo', '')
        )

        # Add measurements
        for m_data in json_data.get('measurements', []):
            # Parse measurement date
            measurement_date = datetime.fromisoformat(m_data.get('measurement_date', datetime.now().isoformat()))

            measurement = MeasurementData(
                id=m_data.get('id', 0),
                measurement_date=measurement_date,
                elapsed_days=m_data.get('elapsed_days', 0),
                thermal_conductivity=m_data.get('thermal_conductivity', 0.0),
                thermal_conductivity_increase=m_data.get('thermal_conductivity_increase', 0.0)
            )
            experiment.measurements.append(measurement)

        return experiment

    except FileNotFoundError as e:
        raise e
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in file {file_path}: {str(e)}", e.doc, e.pos)
    except Exception as e:
        raise Exception(f"Error parsing experiment data: {str(e)}")


def write_interface(experiment, file_path):
    """
    Write an Experiment dataclass object to a JSON file.

    Args:
        experiment (Experiment): The experiment data to write.
        file_path (str): Path where the JSON file should be written.

    Raises:
        TypeError: If experiment is not an Experiment dataclass object.
        Exception: For other writing errors.
    """
    try:
        # Verify input is an Experiment object
        if not isinstance(experiment, Experiment):
            raise TypeError("experiment must be an Experiment dataclass object")

        # Convert experiment to dictionary
        experiment_dict = {
            'id': experiment.id,
            'sample_name': experiment.sample_name,
            'thickness_mm': experiment.thickness_mm,
            'initial_density': experiment.initial_density,
            'temperature': experiment.temperature,
            'humidity_memo': experiment.humidity_memo,
            'measurements': []
        }

        # Add measurements
        for measurement in experiment.measurements:
            measurement_dict = {
                'id': measurement.id,
                'measurement_date': measurement.measurement_date.isoformat(),
                'elapsed_days': measurement.elapsed_days,
                'thermal_conductivity': measurement.thermal_conductivity,
                'thermal_conductivity_increase': measurement.thermal_conductivity_increase
            }
            experiment_dict['measurements'].append(measurement_dict)

        # Write JSON to file
        with open(file_path, 'w') as f:
            json.dump(experiment_dict, f, indent=2)

    except TypeError as e:
        raise e
    except Exception as e:
        raise Exception(f"Error writing experiment data: {str(e)}")


def create_experiment(sample_name, thickness_mm, initial_density, temperature, humidity_memo=None):
    """
    Create a new Experiment dataclass object with the given parameters.

    Args:
        sample_name (str): Name of the sample.
        thickness_mm (float): Thickness of the sample in millimeters.
        initial_density (float): Initial density of the sample.
        temperature (float): Temperature at which the experiment was conducted.
        humidity_memo (str, optional): Notes about humidity conditions.

    Returns:
        Experiment: A new experiment object.
    """
    experiment = Experiment(
        sample_name=sample_name,
        thickness_mm=thickness_mm,
        initial_density=initial_density,
        temperature=temperature
    )

    if humidity_memo:
        experiment.humidity_memo = humidity_memo

    return experiment


def create_measurement(measurement_date, thermal_conductivity):
    """
    Create a new MeasurementData dataclass object.

    Args:
        measurement_date (datetime): Date of the measurement.
        thermal_conductivity (float): Measured thermal conductivity.

    Returns:
        MeasurementData: A new measurement object.
    """
    measurement = MeasurementData(
        measurement_date=measurement_date,
        thermal_conductivity=thermal_conductivity
    )

    return measurement


def add_measurement(experiment, measurements: List[MeasurementData]):
    """
    Add MeasurementData objects to an Experiment.

    Args:
        experiment (Experiment): The experiment to which the measurements will be added.
        measurements (List[MeasurementData]): The measurement data to add.

    Raises:
        TypeError: If the provided experiment or measurement is of incorrect type.
    """
    if not isinstance(experiment, Experiment):
        raise TypeError("experiment must be an Experiment dataclass object")

    if not measurements:
        return experiment

    first_measurement = measurements[0]
    for i, measurement in enumerate(measurements):
        if not isinstance(measurement, MeasurementData):
            raise TypeError("measurement must be a MeasurementData dataclass object")

        if i > 0:
            # Calculate elapsed days from the first measurement
            days_diff = (measurement.measurement_date - first_measurement.measurement_date).total_seconds() / 86400
            measurement.elapsed_days = int(days_diff)
            measurement.thermal_conductivity_increase = measurement.thermal_conductivity - first_measurement.thermal_conductivity

        experiment.measurements.append(measurement)

    return experiment
