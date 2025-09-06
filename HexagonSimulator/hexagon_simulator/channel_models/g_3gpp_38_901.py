import numpy as np

def get_mimo_channel(scenario, d_2d, d_3d, f_c_GHz, h_bs, h_ut, num_bs_ant, num_ue_ant):
    """
    Calculates the MIMO channel matrix H based on 3GPP TR 38.901 path loss models
    and a simplified uncorrelated Rayleigh fading model.

    Args:
        scenario (str): 'UMa', 'UMi', or 'RMa'.
        d_2d (float): 2D distance between BS and UE in meters.
        d_3d (float): 3D distance between BS and UE in meters.
        f_c_GHz (float): Carrier frequency in GHz.
        h_bs (float): Base station height in meters.
        h_ut (float): User equipment height in meters.
        num_bs_ant (int): Number of antennas at the BS.
        num_ue_ant (int): Number of antennas at the UE.

    Returns:
        np.ndarray: A `num_ue_ant x num_bs_ant` complex numpy array representing the channel matrix H.
    """
    # First, calculate the path loss in dB
    path_loss_db = _get_path_loss_siso(scenario, d_2d, d_3d, f_c_GHz, h_bs, h_ut)

    # Convert path loss from dB to a linear scale
    path_loss_linear = 10**(path_loss_db / 10)

    # Generate the small-scale fading component (Rayleigh fading)
    # H_w is a matrix of i.i.d. complex Gaussian random variables with zero mean and unit variance
    h_w = (np.random.randn(num_ue_ant, num_bs_ant) + 1j * np.random.randn(num_ue_ant, num_bs_ant)) / np.sqrt(2)

    # The final channel matrix H is the fading component scaled by the path loss
    # The path loss is divided among the antenna pairs
    h = h_w / np.sqrt(path_loss_linear)

    return h

def _get_path_loss_siso(scenario, d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    """
    Internal function to calculate the SISO path loss based on 3GPP TR 38.901 models.
    This is the same as the old get_path_loss function.
    """
    if scenario == 'UMa':
        return uma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    elif scenario == 'UMi':
        return umi_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    elif scenario == 'RMa':
        return rma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

# --- The rest of the file remains the same, containing the helper functions for path loss ---

def los_probability(scenario, d_2d):
    if d_2d == 0: return 1.0
    if scenario in ['UMa', 'RMa']:
        return min(18.0 / d_2d + np.exp(-d_2d / 63.0) * (1 - 18.0 / d_2d), 1.0)
    elif scenario == 'UMi':
        return min(18.0 / d_2d + np.exp(-d_2d / 36.0) * (1 - 18.0 / d_2d), 1.0)
    return 0.5

def uma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    if np.random.rand() < los_probability('UMa', d_2d):
        return uma_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    else:
        return uma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut)

def umi_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    if np.random.rand() < los_probability('UMi', d_2d):
        return umi_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut)
    else:
        return umi_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut)

def rma_path_loss(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    return rma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut)

def uma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    pl_los = 28.0 + 22 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    pl_prime_nlos = 13.54 + 39.08 * np.log10(d_3d) + 20 * np.log10(f_c_GHz) - 0.6 * (h_ut - 1.5)
    return max(pl_los, pl_prime_nlos)

def umi_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    pl_los = 32.4 + 21 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    pl_prime_nlos = 35.3 * np.log10(d_3d) + 22.4 + 21.3 * np.log10(f_c_GHz) - 0.3 * (h_ut - 1.5)
    return max(pl_los, pl_prime_nlos)

def rma_path_loss_nlos(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    W = 20
    h = 5
    pl_los = 20 * np.log10(40 * np.pi * d_3d * f_c_GHz / 3) + min(0.03 * h**1.72, 10) * np.log10(d_3d) \
        - min(0.044 * h**1.72, 14.77) + 0.002 * np.log10(h) * d_3d
    pl_prime_nlos = 161.04 - 7.1 * np.log10(W) + 7.5 * np.log10(h) \
        - (24.37 - 3.7 * (h/h_bs)**2) * np.log10(h_bs) \
        + (43.42 - 3.1 * np.log10(h_bs)) * (np.log10(d_3d) - 3) \
        + 20 * np.log10(f_c_GHz) - (3.2 * (np.log10(11.75 * h_ut))**2 - 4.97)
    return max(pl_los, pl_prime_nlos)

def get_breakpoint_distance(h_bs, h_ut, f_c_GHz):
    c = 3e8
    return 2 * np.pi * h_bs * h_ut * (f_c_GHz * 1e9) / c

def uma_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    d_bp = get_breakpoint_distance(h_bs, h_ut, f_c_GHz)
    if d_2d <= d_bp:
        return 28.0 + 22 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    else:
        return 28.0 + 40 * np.log10(d_3d) + 20 * np.log10(f_c_GHz) - 9 * np.log10((d_bp)**2 + (h_bs - h_ut)**2)

def umi_path_loss_los(d_2d, d_3d, f_c_GHz, h_bs, h_ut):
    d_bp = get_breakpoint_distance(h_bs, h_ut, f_c_GHz)
    if d_2d <= d_bp:
        return 32.4 + 21 * np.log10(d_3d) + 20 * np.log10(f_c_GHz)
    else:
        return 32.4 + 40 * np.log10(d_3d) + 20 * np.log10(f_c_GHz) - 9.5 * np.log10((d_bp)**2 + (h_bs - h_ut)**2)
