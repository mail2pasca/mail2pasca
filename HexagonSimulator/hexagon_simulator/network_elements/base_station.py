import numpy as np

class BaseStation:
    def __init__(self, bs_id, position, tx_power_dBm, height):
        """
        Initializes a BaseStation object.

        Args:
            bs_id (int): Unique identifier for the base station.
            position (np.ndarray): 3D coordinates of the base station (x, y, z).
            tx_power_dBm (float): Transmission power in dBm.
            height (float): Height of the base station antenna.
        """
        self.bs_id = bs_id
        self.position = np.array(position)
        self.tx_power_dBm = tx_power_dBm
        self.height = height

    def __repr__(self):
        return f"BaseStation(id={self.bs_id}, position={self.position})"
