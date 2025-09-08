class SRS:
    """
    Represents a Sounding Reference Signal (SRS) transmission.
    In this system-level simulation, this class acts as a container for the
    properties of the SRS signal, rather than generating the actual sequence.
    """
    def __init__(self, ue_id, transmission_power_dbm):
        """
        Initializes an SRS object.

        Args:
            ue_id (int): The ID of the UE transmitting the SRS.
            transmission_power_dbm (float): The power at which the SRS is transmitted.
        """
        self.ue_id = ue_id
        self.transmission_power_dbm = transmission_power_dbm

    def __repr__(self):
        return f"SRS(ue_id={self.ue_id}, power={self.transmission_power_dbm} dBm)"
