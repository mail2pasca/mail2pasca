import numpy as np

class FTPModel3:
    """
    Represents the FTP Model 3 traffic model from 3GPP specifications.
    This model simulates file transfers with a fixed file size and Poisson arrivals
    (i.e., exponential inter-arrival times).
    """
    def __init__(self, file_size_bytes=500000, mean_inter_arrival_ms=50):
        """
        Initializes the FTP Model 3.

        Args:
            file_size_bytes (int): The size of each file transfer in bytes.
                                     Default is 0.5 Mbytes.
            mean_inter_arrival_ms (float): The mean time between file arrivals in ms.
                                             Default is 50 ms.
        """
        self.file_size_bytes = file_size_bytes
        self.mean_inter_arrival_ms = mean_inter_arrival_ms
        self.next_arrival_time_ms = 0
        self._schedule_next_arrival(0)

    def _schedule_next_arrival(self, current_time_ms):
        """
        Schedules the next file arrival time using an exponential distribution.
        """
        inter_arrival_time = np.random.exponential(self.mean_inter_arrival_ms)
        self.next_arrival_time_ms = current_time_ms + inter_arrival_time

    def generate_packet(self, time_ms):
        """
        Generates a new file transfer (as a large packet) if the scheduled time has come.

        Args:
            time_ms (float): The current simulation time in milliseconds.

        Returns:
            int: The size of the file in bytes if a transfer starts, otherwise 0.
        """
        if time_ms >= self.next_arrival_time_ms:
            self._schedule_next_arrival(self.next_arrival_time_ms)
            return self.file_size_bytes
        return 0
