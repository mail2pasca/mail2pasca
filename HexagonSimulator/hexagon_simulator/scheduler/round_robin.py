class RoundRobinScheduler:
    """
    A simple Round Robin scheduler.
    It serves UEs attached to a BS in a circular order, provided they have data to send.
    """
    def __init__(self):
        """
        Initializes the Round Robin scheduler.
        It keeps track of the scheduling index for each base station.
        """
        # Key: bs_id, Value: index of the next UE in the list of UEs with data
        self.bs_ue_indices = {}

    def schedule(self, bs_id, ue_ids_with_data):
        """
        Schedules the next UE to be served for a given BS from the list of UEs with data.

        Args:
            bs_id (int): The ID of the base station that is scheduling.
            ue_ids_with_data (list): A list of IDs of UEs that have data in their queue at the BS.

        Returns:
            int: The ID of the scheduled UE, or None if no UE has data to send.
        """
        if not ue_ids_with_data:
            return None

        # Initialize the index for the BS if it's not already there
        if bs_id not in self.bs_ue_indices:
            self.bs_ue_indices[bs_id] = 0

        # Get the current index and wrap it around if it goes out of bounds
        num_ues_with_data = len(ue_ids_with_data)
        current_index = self.bs_ue_indices[bs_id] % num_ues_with_data

        # Select the UE to be scheduled
        scheduled_ue_id = ue_ids_with_data[current_index]

        # Update the index for the next scheduling opportunity
        self.bs_ue_indices[bs_id] = (current_index + 1)

        return scheduled_ue_id
