class FullBuffer:
    """
    Represents a Full Buffer traffic model.
    This model generates a packet of a fixed size at each simulation time step,
    simulating a continuous stream of data.
    """
    def __init__(self, packet_size_bytes=1500):
        """
        Initializes the Full Buffer traffic model.

        Args:
            packet_size_bytes (int): The size of the packets to be generated, in bytes.
                                     Default is 1500 bytes (a common MTU size).
        """
        self.packet_size_bytes = packet_size_bytes

    def generate_packet(self, time_ms):
        """
        Generates a new packet.
        For the Full Buffer model, a packet is always generated at each time step.

        Args:
            time_ms (float): The current simulation time in milliseconds.

        Returns:
            int: The size of the generated packet in bytes.
        """
        # In a full buffer model, we assume there is always data to send.
        return self.packet_size_bytes
