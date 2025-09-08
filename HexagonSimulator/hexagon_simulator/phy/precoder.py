import numpy as np
from numpy.linalg import inv

class ZFPrecoder:
    """
    Implements a Zero-Forcing (ZF) precoder.
    The ZF precoder aims to nullify inter-stream interference by inverting
    the channel at the transmitter.
    """
    def get_precoding_matrix(self, h_est):
        """
        Calculates the ZF precoding matrix (W).

        The formula for the ZF precoding matrix is:
        W = H_hermitian * (H * H_hermitian)^-1

        Args:
            h_est (np.ndarray): The estimated channel matrix (N_r x N_t).

        Returns:
            np.ndarray: The ZF precoding matrix (N_t x N_r).
        """
        h_hermitian = h_est.conj().T

        # To avoid singularity issues with the matrix inversion, a small identity
        # matrix scaled by a very small number is added (regularization).
        num_rx_antennas = h_est.shape[0]
        identity = np.eye(num_rx_antennas)
        regularization_term = 1e-6 * identity

        # Calculate the precoding matrix
        # Note: The result of (h_est @ h_hermitian) is a square matrix of size N_r x N_r
        try:
            w = h_hermitian @ inv(h_est @ h_hermitian + regularization_term)
        except np.linalg.LinAlgError:
            # If the matrix is singular even with regularization, fall back to a simpler scheme
            # For simplicity, we just use the hermitian transpose (Matched Filter)
            w = h_hermitian

        return w
