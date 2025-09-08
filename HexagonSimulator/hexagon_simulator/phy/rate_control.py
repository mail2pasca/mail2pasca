from .mcs_table import MCS_TABLE

class RateControl:
    """
    Implements a simple rate control (link adaptation) mechanism.
    """
    def __init__(self):
        """
        Initializes the Rate Control mechanism with a predefined MCS table.
        """
        self.mcs_table = MCS_TABLE

    def select_mcs(self, sinr_db):
        """
        Selects an MCS based on the given SINR.
        It finds the highest MCS level that can be supported by the SINR.

        Args:
            sinr_db (float): The SINR in dB.

        Returns:
            tuple: A tuple containing the modulation order and coding rate.
                   Returns (0, 0) if no MCS is supported.
        """
        supported_mcs = (0, 0) # Default to no transmission if SINR is too low
        for min_sinr, mod_order, code_rate in self.mcs_table:
            if sinr_db >= min_sinr:
                supported_mcs = (mod_order, code_rate)
            else:
                # The table is sorted by SINR, so we can stop here
                break
        return supported_mcs
