import numpy as np

class UserEquipment:
    def __init__(self, ue_id, position, height, traffic_model):
        """
        Initializes a UserEquipment object.

        Args:
            ue_id (int): Unique identifier for the user equipment.
            position (np.ndarray): 3D coordinates of the UE (x, y, z).
            height (float): Height of the UE antenna.
            traffic_model: An instance of a traffic model class.
        """
        self.ue_id = ue_id
        self.position = np.array(position)
        self.height = height
        self.traffic_model = traffic_model

        self.serving_bs = None
        self.sinr_dB = None
        self.throughput_mbps = None

    def __repr__(self):
        return f"UserEquipment(id={self.ue_id}, position={self.position})"

    def attach_to_bs(self, bs):
        """Attaches the UE to a serving BS and initializes its queue."""
        self.serving_bs = bs
        if self.serving_bs:
            self.serving_bs.add_ue_queue(self.ue_id)

    def generate_packet(self, time_ms, Packet):
        """
        Generates a packet using the assigned traffic model and enqueues it
        at the serving base station.
        """
        packet_size = self.traffic_model.generate_packet(time_ms)
        if packet_size > 0 and self.serving_bs:
            packet = Packet(size_bytes=packet_size, generation_time_ms=time_ms)
            self.serving_bs.enqueue_packet(self.ue_id, packet)
