import numpy as np
from scipy.stats import truncnorm

class XRModel:
    """
    Represents an Extended Reality (XR) traffic model based on 3GPP discussions.
    This model simulates periodic traffic (based on FPS) with jitter on arrival times
    and variable packet sizes, both modeled using truncated Gaussian distributions.
    """
    def __init__(self, fps=60,
                 jitter_mean_ms=0, jitter_std_ms=3, jitter_trunc_ms=7,
                 packet_size_mean_bytes=10000, packet_size_std_bytes=2000, packet_size_trunc_bytes=5000):
        """
        Initializes the XR traffic model.

        Args:
            fps (int): Frames per second, determines the periodicity.
            jitter_mean_ms (float): Mean of the jitter in milliseconds.
            jitter_std_ms (float): Standard deviation of the jitter in milliseconds.
            jitter_trunc_ms (float): Truncation bound for the jitter in milliseconds.
            packet_size_mean_bytes (int): Mean of the packet size in bytes.
            packet_size_std_bytes (int): Standard deviation of the packet size in bytes.
            packet_size_trunc_bytes (int): Truncation bound for the packet size in bytes.
        """
        self.period_ms = 1000.0 / fps
        self.jitter_mean_ms = jitter_mean_ms
        self.jitter_std_ms = jitter_std_ms
        self.jitter_trunc_ms = jitter_trunc_ms
        self.packet_size_mean_bytes = packet_size_mean_bytes
        self.packet_size_std_bytes = packet_size_std_bytes
        self.packet_size_trunc_bytes = packet_size_trunc_bytes

        self.next_arrival_time_ms = self.period_ms

    def _get_truncated_normal(self, mean, std, lower_bound, upper_bound):
        """Helper function to get a random value from a truncated normal distribution."""
        return truncnorm((lower_bound - mean) / std, (upper_bound - mean) / std, loc=mean, scale=std).rvs(1)[0]

    def _schedule_next_arrival(self):
        """Schedules the next packet arrival time."""
        jitter = self._get_truncated_normal(self.jitter_mean_ms, self.jitter_std_ms, -self.jitter_trunc_ms, self.jitter_trunc_ms)
        self.next_arrival_time_ms += self.period_ms + jitter

    def generate_packet(self, time_ms):
        """
        Generates a new XR packet if the scheduled time has come.

        Args:
            time_ms (float): The current simulation time in milliseconds.

        Returns:
            int: The size of the generated packet in bytes, or 0 if no packet is generated.
        """
        if time_ms >= self.next_arrival_time_ms:
            packet_size = self._get_truncated_normal(self.packet_size_mean_bytes,
                                                     self.packet_size_std_bytes,
                                                     max(0, self.packet_size_mean_bytes - self.packet_size_trunc_bytes),
                                                     self.packet_size_mean_bytes + self.packet_size_trunc_bytes)
            self._schedule_next_arrival()
            return int(packet_size)
        return 0
