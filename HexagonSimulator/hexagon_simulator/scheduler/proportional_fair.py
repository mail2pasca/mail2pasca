import numpy as np

class ProportionalFairScheduler:
    """
    A Proportional Fair (PF) scheduler.
    It aims to balance fairness and system throughput by prioritizing users
    with high instantaneous channel quality relative to their own average throughput.
    """
    def __init__(self, alpha=0.1):
        """
        Initializes the PF scheduler.

        Args:
            alpha (float): The smoothing factor for the EWMA of throughput.
                           A smaller alpha results in slower changes to the average.
        """
        self.alpha = alpha
        # Key: ue_id, Value: average throughput in Mbps
        self.avg_throughput = {}

    def schedule(self, ue_potential_throughputs):
        """
        Schedules the next UE based on the Proportional Fair metric.

        Args:
            ue_potential_throughputs (dict): A dictionary where keys are ue_ids and
                                             values are their potential throughputs
                                             in the current time step (in Mbps).

        Returns:
            int: The ID of the scheduled UE, or None if no UEs can be scheduled.
        """
        if not ue_potential_throughputs:
            return None

        best_ue_id = -1
        max_metric = -1

        for ue_id, potential_throughput in ue_potential_throughputs.items():
            # Initialize average throughput for new UEs with a small non-zero value
            if ue_id not in self.avg_throughput:
                self.avg_throughput[ue_id] = 1e-6

            # PF metric = potential_throughput / avg_throughput
            # Add a small epsilon to avoid division by zero if avg_throughput is 0
            metric = potential_throughput / (self.avg_throughput[ue_id] + 1e-9)

            if metric > max_metric:
                max_metric = metric
                best_ue_id = ue_id

        return best_ue_id

    def update_avg_throughput(self, scheduled_ue_id, achieved_throughput, all_ue_ids_with_data):
        """
        Updates the average throughput for all UEs with data using an EWMA.

        Args:
            scheduled_ue_id (int): The ID of the UE that was scheduled and transmitted data.
            achieved_throughput (float): The throughput achieved by the scheduled UE in Mbps.
            all_ue_ids_with_data (list): A list of all UE IDs that had data in the queue.
        """
        for ue_id in all_ue_ids_with_data:
            # The throughput for non-scheduled UEs is 0 in this time step
            current_throughput = achieved_throughput if ue_id == scheduled_ue_id else 0

            # Update EWMA for the UE's average throughput
            self.avg_throughput[ue_id] = (1 - self.alpha) * self.avg_throughput.get(ue_id, 1e-6) + self.alpha * current_throughput
