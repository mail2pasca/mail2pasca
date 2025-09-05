import numpy as np

def get_path_loss(scenario, d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Calculates path loss based on 3GPP TR 38.901 models.
    This is the main entry point for path loss calculations.

    Args:
        scenario (str): 'UMa', 'UMi', or 'RMa'.
        d_2d (float): 2D distance between BS and UE in meters.
        d_3d (float): 3D distance between BS and UE in meters.
        f_c_GHz (float): Carrier frequency in GHz.
        h_bs (float): Base station height in meters.
        h_ut (float): User equipment height in meters.

    Returns:
        float: Path loss in dB.
    """
    if scenario == 'UMa':
        return uma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    elif scenario == 'UMi':
        return umi_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    elif scenario == 'RMa':
        return rma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

def los_probability(scenario, d_2d):
    """
    Calculates the Line-of-Sight (LOS) probability based on TR 38.901 Table 7.4.2-1.
    This is a simplified model. A more accurate model would depend on more parameters.
    """
    if d_2d == 0: # Avoid division by zero
        return 1.0
    if scenario in ['UMa', 'RMa']:
        # Simplified LOS probability for UMa and RMa scenarios
        return min(18.0 / d_2d + np.exp(-d_2d / 63.0) * (1 - 18.0 / d_2d), 1.0)
    elif scenario == 'UMi':
        # Simplified LOS probability for UMi scenario
        return min(18.0 / d_2d + np.exp(-d_2d / 36.0) * (1 - 18.0 / d_2d), 1.0)
    return 0.5 # Default probability

def uma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Determines if the UMa channel is LOS or NLOS and returns the corresponding path loss.
    """
    if np.random.rand() < los_probability('UMa', d_2d):
        return uma_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    else:
        return uma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut)

def umi_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Determines if the UMi channel is LOS or NLOS and returns the corresponding path loss.
    """
    if np.random.rand() < los_probability('UMi', d_2d):
        return umi_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    else:
        return umi_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut)

def rma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    For RMa, we currently only implement the NLOS case for simplicity.
    A full implementation would also include a probabilistic LOS/NLOS model.
    """
    return rma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut)

def uma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Calculates UMa NLOS path loss using formulas from TR 38.901 Table 7.4.1-1.
    """
    # Pathloss for LOS is needed for the max() operation in the NLOS case
    pl_los = 28.0 + 22 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    # The actual NLOS pathloss formula
    pl_prime_nlos = 13.54 + 39.08 * np.log10(d_3d) + 20 * np.log10(f_c_GHz) - 0.6 * (h_ut - 1.5)
    return max(pl_los, pl_prime_nlos)

def umi_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Calculates UMi-Street Canyon NLOS path loss using TR 38.901 Table 7.4.1-1.
    """
    pl_los = 32.4 + 21 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    pl_prime_nlos = 35.3 * np.log10(d_3d) + 22.4 + 21.3 * np.log10(f_c_GHz) - 0.3 * (h_ut - 1.5)
    return max(pl_los, pl_prime_nlos)

def rma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Calculates RMa NLOS path loss using TR 38.901 Table 7.4.1-1.
    NOTE: This is a simplified implementation. A full implementation would handle
    parameters like average street width (W) and building height (h) dynamically.
    """
    W = 20  # average street width
    h = 5   # average building height

    pl_los = 20 * np.log10(40 * np.pi * d_3d * f_c_GHz / 3) + min(0.03 * h**1.72, 10) * np.log10(d_3d) \
        - min(0.044 * h**1.72, 14.77) + 0.002 * np.log10(h) * d_3d

    pl_prime_nlos = 161.04 - 7.1 * np.log10(W) + 7.5 * np.log10(h) \
        - (24.37 - 3.7 * (h/h_bs)**2) * np.log10(h_bs) \
        + (43.42 - 3.1 * np.log10(h_bs)) * (np.log10(d_3d) - 3) \
        + 20 * np.log10(f_c_GHz) - (3.2 * (np.log10(11.75 * h_ut))**2 - 4.97)

    return max(pl_los, pl_prime_nlos)

def get_breakpoint_distance(h_bs, h_ut, f_c_GHz):
    """
    Calculates the breakpoint distance (d_BP).
    NOTE: This is a simplified version of the breakpoint distance calculation from TR 38.901.
    A full implementation would use effective antenna heights (h'_BS, h'_UT) which
    depend on the effective environment height (h_E).
    """
    c = 3e8  # speed of light in m/s
    # Using the simplified formula from Note 5 of Table 7.4.1-1
    return 2 * np.pi * h_bs * h_ut * (f_c_GHz * 1e9) / c

def uma_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Calculates UMa LOS path loss using formulas from TR 38.901 Table 7.4.1-1.
    It uses a breakpoint distance to switch between two formulas.
    """
    d_bp = get_breakpoint_distance(h_bs, h_ut, f_c_GHz)
    if d_2d <= d_bp:
        # Formula for d_2d <= d_BP
        return 28.0 + 22 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    else:
        # Formula for d_2d > d_BP
        return 28.0 + 40 * np.log10(d_3d) + 20 * np.log10(f_c_GHz) - 9 * np.log10((d_bp)**2 + (h_bs - h_ut)**2)

def umi_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Calculates UMi-Street Canyon LOS path loss using TR 38.901 Table 7.4.1-1.
    It uses a breakpoint distance to switch between two formulas.
    """
    d_bp = get_breakpoint_distance(h_bs, h_ut, f_c_GHz)
    if d_2d <= d_bp:
        # Formula for d_2d <= d_BP
        return 32.4 + 21 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    else:
        # Formula for d_2d > d_BP
        return 32.4 + 40 * np.log10(d_3d) + 20 * np.log10(f_c_GHz) - 9.5 * np.log10((d_bp)**2 + (h_bs - h_ut)**2)
