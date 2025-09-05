class Packet:
    """
    Represents a data packet in the simulation.
    """
    _next_id = 0

    def __init__(self, size_bytes, generation_time_ms):
        """
        Initializes a Packet object.

        Args:
            size_bytes (int): The size of the packet in bytes.
            generation_time_ms (float): The simulation time when the packet was generated.
        """
        self.packet_id = Packet._next_id
        Packet._next_id += 1

        self.size_bytes = size_bytes
        self.generation_time_ms = generation_time_ms
        self.delivery_time_ms = -1 # -1 indicates not yet delivered

    def __repr__(self):
        return (f"Packet(id={self.packet_id}, size={self.size_bytes}, "
                f"gen_time={self.generation_time_ms})")

    def mark_delivered(self, time_ms):
        """Marks the packet as delivered at a specific time."""
        self.delivery_time_ms = time_ms
