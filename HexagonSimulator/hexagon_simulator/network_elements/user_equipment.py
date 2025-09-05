import numpy as np

class UserEquipment:
    def __init__(self, ue_id, position, height):
        """
        Initializes a UserEquipment object.

        Args:
            ue_id (int): Unique identifier for the user equipment.
            position (np.ndarray): 3D coordinates of the UE (x, y, z).
            height (float): Height of the UE antenna.
        """
        self.ue_id = ue_id
        self.position = np.array(position)
        self.height = height
        self.serving_bs = None
        self.sinr_dB = None
        self.throughput_mbps = None

    def __repr__(self):
        return f"UserEquipment(id={self.ue_id}, position={self.position})"

    def attach_to_bs(self, bs):
        self.serving_bs = bs
