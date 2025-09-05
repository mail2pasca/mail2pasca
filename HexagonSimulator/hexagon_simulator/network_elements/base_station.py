import numpy as np
from collections import deque

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

        # A dictionary to hold the data queues for each attached UE
        # Key: ue_id, Value: deque of packet sizes
        self.ue_queues = {}

    def __repr__(self):
        return f"BaseStation(id={self.bs_id}, position={self.position})"

    def add_ue_queue(self, ue_id):
        """Adds a new queue for a UE."""
        if ue_id not in self.ue_queues:
            self.ue_queues[ue_id] = deque()

    def enqueue_packet(self, ue_id, packet):
        """Enqueues a packet for a specific UE."""
        if ue_id in self.ue_queues:
            self.ue_queues[ue_id].append(packet)
