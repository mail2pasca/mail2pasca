import numpy as np

class ChannelEstimator:
    """
    A simplified channel estimator that models estimation errors.
    Instead of implementing a full LS or MMSE estimator, it simulates the
    result by adding a complex Gaussian error to the true channel matrix.
    """
    def __init__(self, error_variance=0.01):
        """
        Initializes the Channel Estimator.

        Args:
            error_variance (float): The variance of the channel estimation error.
                                    A value of 0 means perfect channel estimation.
        """
        self.error_variance = error_variance

    def estimate(self, h_true):
        """
        Estimates the channel by adding a random error to the true channel matrix.

        Args:
            h_true (np.ndarray): The true channel matrix.

        Returns:
            np.ndarray: The estimated channel matrix.
        """
        if self.error_variance == 0:
            return h_true

        # Generate a complex Gaussian error matrix with the specified variance
        error_matrix = (np.random.randn(*h_true.shape) + 1j * np.random.randn(*h_true.shape)) \
                       * np.sqrt(self.error_variance / 2)

        h_est = h_true + error_matrix

        return h_est
