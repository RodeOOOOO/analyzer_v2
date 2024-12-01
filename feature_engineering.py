import numpy as np
import pandas as pd
import logging
from logger import setup_logger

logger = setup_logger(__name__, level=logging.INFO)

class FeatureEngineering:
    def normalize_frequency(self, data):
        freq_min = data["Frequency (Hz)"].min()
        freq_max = data["Frequency (Hz)"].max()
        data["Normalized_Frequency"] = (data["Frequency (Hz)"] - freq_min) / (freq_max - freq_min)
        logger.info("Frequency normalization applied.")

    def calculate_magnitude_and_phase(self, data):
        for param in ["S11", "S21", "S12", "S22"]:
            real = data[f"{param} Real"]
            imag = data[f"{param} Imaginary"]
            data[f"{param}_Mag"] = np.sqrt(real**2 + imag**2)
            data[f"{param}_Phase"] = np.arctan2(imag, real)
        logger.info("Magnitude and phase calculated.")

    def unwrap_phase(self, data):
        for param in ["S11", "S21", "S12", "S22"]:
            phase = data[f"{param}_Phase"]
            data[f"{param}_Unwrapped_Phase"] = np.unwrap(phase)
        logger.info("Phase unwrapping applied.")

    def calculate_impedance(self, data):
        z0 = 50  # Characteristic impedance
        for param in ["S11", "S21", "S12", "S22"]:
            gamma = data[f"{param}_Mag"] * np.exp(1j * data[f"{param}_Phase"])
            impedance = z0 * (1 + gamma) / (1 - gamma)
            data[f"{param}_Impedance_Real"] = np.real(impedance)
            data[f"{param}_Impedance_Imag"] = np.imag(impedance)
        logger.info("Impedance calculated.")

    def calculate_resistance_capacitance_inductance(self, data):
        for param in ["S11", "S21", "S12", "S22"]:
            z_real = data[f"{param}_Impedance_Real"]
            z_imag = data[f"{param}_Impedance_Imag"]
            freq = data["Frequency (Hz)"]
            safe_reactance = np.where(z_imag != 0, z_imag, np.nan)
            data[f"{param}_Resistance"] = z_real
            data[f"{param}_Reactance"] = z_imag
            data[f"{param}_Capacitance"] = -1 / (2 * np.pi * freq * safe_reactance)
            data[f"{param}_Inductance"] = safe_reactance / (2 * np.pi * freq)
        logger.info("Resistance, capacitance, and inductance calculated.")

    def calculate_q_factor(self, data):
        for param in ["S11", "S21", "S12", "S22"]:
            resistance = data[f"{param}_Resistance"]
            reactance = data[f"{param}_Reactance"]
            data[f"{param}_Q_Factor"] = np.abs(reactance / resistance)
        logger.info("Q-factor calculated.")

    def calculate_loss_tangent(self, data):
        for param in ["S11", "S21", "S12", "S22"]:
            real = data[f"{param}_Impedance_Real"]
            imag = data[f"{param}_Impedance_Imag"]
            data[f"{param}_Loss_Tangent"] = np.abs(imag / real)
        logger.info("Loss tangent calculated.")

    def calculate_effective_permittivity(self, data):
        z0 = 50  # Characteristic impedance
        c = 3e8  # Speed of light
        freq = data["Frequency (Hz)"]
        for param in ["S11", "S21", "S12", "S22"]:
            impedance_real = data[f"{param}_Impedance_Real"]
            impedance_imag = data[f"{param}_Impedance_Imag"]
            impedance = impedance_real + 1j * impedance_imag
            data[f"{param}_Effective_Permittivity"] = (c / (freq * np.sqrt(np.real(impedance / z0))))**2
        logger.info("Effective permittivity calculated.")

    def calculate_dielectric_constant(self, data):
        freq = data["Frequency (Hz)"]
        for param in ["S11", "S21", "S12", "S22"]:
            capacitance = data[f"{param}_Capacitance"]
            safe_capacitance = np.where(capacitance > 0, capacitance, np.nan)
            data[f"{param}_Dielectric_Constant"] = safe_capacitance * (2 * np.pi * freq)
        logger.info("Dielectric constant calculated.")

    def calculate_skin_depth(self, data):
        mu0 = 4 * np.pi * 1e-7  # Permeability of free space
        freq = data["Frequency (Hz)"]
        sigma = data["Conductivity_Corrected"]
        omega = 2 * np.pi * freq
        for param in ["S11", "S21", "S12", "S22"]:
            safe_sigma = np.where(sigma > 0, sigma, np.nan)
            data[f"{param}_Skin_Depth"] = np.sqrt(2 / (omega * mu0 * safe_sigma))
        logger.info("Skin depth calculated.")

    def calculate_bandwidth(self, data):
        # Placeholder for bandwidth calculation
        logger.info("Bandwidth calculation not implemented yet.")

    def calculate_reflection_coefficient(self, data):
        # Reflection coefficient already calculated as S11_Mag and S22_Mag
        logger.info("Reflection coefficient is available in S11_Mag and S22_Mag.")

    def calculate_normalized_s_parameters(self, data):
        for param in ["S11", "S21", "S12", "S22"]:
            max_mag = data[f"{param}_Mag"].max()
            data[f"{param}_Normalized_Mag"] = data[f"{param}_Mag"] / max_mag if max_mag != 0 else 0
        logger.info("Normalized S-parameters calculated.")
        
    def calculate_effective_dielectric_constant(self, data):
        """
        Calculate the effective dielectric constant (E_r) based on the impedance or other parameters.

        Args:
            data (pd.DataFrame): The processed data containing impedance and frequency columns.
        """
        try:
            logger.info("Calculating effective dielectric constant (E_r)...")

            # Example calculation using capacitance (update based on your specific formula)
            for param in ["S11", "S21", "S12", "S22"]:
                capacitance = data.get(f"{param}_Capacitance", None)
                if capacitance is not None:
                    # Relative permittivity calculation (example using capacitance)
                    data[f"{param}_Effective_Dielectric_Constant"] = np.abs(capacitance) * 1e12  # Placeholder formula

            logger.info("Effective dielectric constant calculated.")
        except Exception as e:
            logger.error(f"Error calculating effective dielectric constant: {e}")
            logger.debug("Exception details:", exc_info=True)
            raise