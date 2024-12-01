import os
import pandas as pd
from logger import setup_logger
from feature_engineering import FeatureEngineering
import logging

logger = setup_logger(__name__, level=logging.INFO)

class ProcessingManager:
    def __init__(self, baseline_file="baseline.csv", processed_dir="processed_data", h5_file="data/data.h5"):
        self.processed_dir = processed_dir
        self.h5_file = h5_file
        self.baseline_file = baseline_file
        self.feature_engineering = FeatureEngineering()

        os.makedirs(self.processed_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.h5_file), exist_ok=True)

        self.baseline_data = self.load_baseline()

    def load_baseline(self):
        try:
            if os.path.exists(self.baseline_file):
                baseline_data = pd.read_csv(self.baseline_file)
                logger.info("Baseline data loaded successfully.")
                return baseline_data
            else:
                logger.warning(f"Baseline file '{self.baseline_file}' not found. Continuing without baseline.")
                return None
        except Exception as e:
            logger.error(f"Error loading baseline data: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise

    def validate_raw_data(self, raw_data):
        required_columns = [
            "Frequency (Hz)", "S11 Real", "S11 Imaginary",
            "S21 Real", "S21 Imaginary", "S12 Real", "S12 Imaginary",
            "S22 Real", "S22 Imaginary"
        ]
        if not all(col in raw_data.columns for col in required_columns):
            missing_cols = set(required_columns) - set(raw_data.columns)
            raise ValueError(f"Input raw_data is missing required columns: {missing_cols}")

    def apply_baseline_correction(self, data):
        try:
            logger.info("Applying baseline correction...")
            if self.baseline_data is not None:
                data = pd.merge(data, self.baseline_data, on="Frequency (Hz)", how="left")

                if "Baseline_Permittivity" not in data.columns or "Baseline_Conductivity" not in data.columns:
                    logger.warning("Baseline data columns are missing. Defaulting to zeros.")
                    data["Baseline_Permittivity"] = 0
                    data["Baseline_Conductivity"] = 0

                data["Permittivity_Corrected"] = data["S11_Mag"] - data["Baseline_Permittivity"]
                data["Conductivity_Corrected"] = data["S11_Phase"] - data["Baseline_Conductivity"]
            else:
                logger.warning("Baseline data not available. Using default corrections.")
                data["Permittivity_Corrected"] = data["S11_Mag"]
                data["Conductivity_Corrected"] = data["S11_Phase"]

            logger.info("Baseline correction applied.")
            return data
        except Exception as e:
            logger.error(f"Error during baseline correction: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise

    def preprocess(self, raw_data):
        try:
            logger.info("Starting preprocessing...")
            self.validate_raw_data(raw_data)
            processed_data = raw_data.copy()

            # Call feature engineering methods that generate required columns
            self.feature_engineering.calculate_magnitude_and_phase(processed_data)  # Produces S11_Mag, etc.

            # Apply baseline correction after required columns are available
            processed_data = self.apply_baseline_correction(processed_data)

            # Continue with the rest of the feature engineering
            self.feature_engineering.unwrap_phase(processed_data)
            self.feature_engineering.calculate_impedance(processed_data)
            self.feature_engineering.calculate_resistance_capacitance_inductance(processed_data)
            self.feature_engineering.calculate_q_factor(processed_data)
            self.feature_engineering.calculate_skin_depth(processed_data)
            self.feature_engineering.calculate_loss_tangent(processed_data)
            self.feature_engineering.calculate_effective_dielectric_constant(processed_data)

            logger.info("Preprocessing completed successfully.")
            return processed_data
        except Exception as e:
            logger.error(f"Error during preprocessing: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise

    def save_to_csv(self, data):
        try:
            logger.info("Saving data to CSV...")
            csv_path = os.path.join(self.processed_dir, "processed_data.csv")

            # Convert complex values to separate real and imaginary parts
            for column in data.select_dtypes(include=[complex]).columns:
                data[f"{column}_Real"] = data[column].apply(np.real)
                data[f"{column}_Imag"] = data[column].apply(np.imag)
                data.drop(columns=[column], inplace=True)

            data.to_csv(csv_path, mode='a', index=False, header=not os.path.exists(csv_path))
            logger.info(f"Processed data saved to {csv_path}.")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise

    def append_to_h5(self, data):
        try:
            logger.info("Appending data to HDF5...")
            h5_path = self.h5_file

            # Convert complex values to separate real and imaginary parts for HDF5 compatibility
            for column in data.select_dtypes(include=[complex]).columns:
                data[f"{column}_Real"] = data[column].apply(np.real)
                data[f"{column}_Imag"] = data[column].apply(np.imag)
                data.drop(columns=[column], inplace=True)

            # Replace spaces in column names for compatibility
            data.columns = [col.replace(" ", "_") for col in data.columns]

            with pd.HDFStore(h5_path) as store:
                store.append("processed_data", data, format="table", data_columns=True)
            logger.info(f"Processed data appended to {h5_path}.")
        except Exception as e:
            logger.error(f"Error saving to HDF5: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise

    def process_and_save(self, raw_data):
        try:
            logger.info("Starting processing and saving...")
            # Preprocess the raw data
            processed_data = self.preprocess(raw_data)

            # Save processed data to CSV
            self.save_to_csv(processed_data)

            # Append processed data to HDF5
            self.append_to_h5(processed_data)

            logger.info("Processing and saving completed successfully.")
        except Exception as e:
            logger.error(f"Error during process_and_save: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise
