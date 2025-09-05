import numpy as np
import json
from hexagon_simulator.utils.config_parser import ConfigParser
from hexagon_simulator.network_elements.base_station import BaseStation
from hexagon_simulator.network_elements.user_equipment import UserEquipment
from hexagon_simulator.channel_models import g_3gpp_38_901

class SystemLevelSimulation:
    """
    This class orchestrates the system-level simulation.
    It sets up the network, runs the simulation, calculates results, and saves them.
    """
    def __init__(self, config_file):
        """
        Initializes the simulation with parameters from a config file.
        """
        self.config = ConfigParser(config_file)
        self.sim_params = self.config.get_simulation_parameters()
        self.net_params = self.config.get_network_parameters()
        self.ch_params = self.config.get_channel_parameters()
        self.out_params = self.config.get_output_parameters()

        self.base_stations = []
        self.user_equipments = []

    def setup(self):
        """
        Sets up the simulation environment by creating and placing BSs and UEs.
        """
        self._create_bs_layout()
        self._create_ue_layout()

    def run(self):
        """
        Runs the main simulation loop.
        For now, this is a single snapshot simulation (one "drop").
        """
        print("Setting up simulation environment...")
        self.setup()

        print("Running simulation...")
        results = []
        for ue in self.user_equipments:
            # For each UE, calculate path loss to all BSs
            path_losses = []
            for bs in self.base_stations:
                d_2d = np.linalg.norm(ue.position[:2] - bs.position[:2])
                d_3d = np.linalg.norm(ue.position - bs.position)

                pl = g_3gpp_38_901.get_path_loss(
                    self.sim_params['scenario'],
                    d_2d,
                    d_3d,
                    self.sim_params['frequency_ghz'],
                    bs.height,
                    ue.height
                )
                path_losses.append((bs, pl))

            # Associate UE with the BS with the minimum path loss
            serving_bs, min_pl = min(path_losses, key=lambda x: x[1])
            ue.attach_to_bs(serving_bs)

            # Calculate SINR and throughput for the UE
            ue.sinr_dB = self._calculate_sinr(ue, min_pl, path_losses)
            ue.throughput_mbps = self._calculate_throughput(ue.sinr_dB)

            # Store results for this UE
            results.append({
                'ue_id': ue.ue_id,
                'serving_bs_id': serving_bs.bs_id,
                'sinr_dB': ue.sinr_dB,
                'throughput_mbps': ue.throughput_mbps
            })

        print(f"Simulation finished. Saving results to {self.out_params['results_file']}...")
        self._save_results(results)
        print("Results saved.")

    def _create_bs_layout(self):
        """
        Creates a hexagonal layout of base stations.
        A central BS is placed at (0,0), and the rest are placed in a hexagonal grid around it.
        """
        center = (0, 0, self.net_params['bs_height_m'])
        self.base_stations.append(BaseStation(0, center, self.net_params['bs_tx_power_dbm'], self.net_params['bs_height_m']))

        isd = self.net_params['inter_site_distance_m']
        # Create one tier of 6 BSs around the center
        for i in range(self.net_params['num_base_stations'] - 1):
            angle = 2 * np.pi * i / 6
            x = center[0] + isd * np.cos(angle)
            y = center[1] + isd * np.sin(angle)
            pos = (x, y, self.net_params['bs_height_m'])
            self.base_stations.append(BaseStation(i + 1, pos, self.net_params['bs_tx_power_dbm'], self.net_params['bs_height_m']))

    def _create_ue_layout(self):
        """
        Randomly places UEs within the simulation area.
        The area is defined as a square around the central BS.
        """
        max_dist = self.net_params['inter_site_distance_m']
        for i in range(self.sim_params['num_ues']):
            x = np.random.uniform(-max_dist, max_dist)
            y = np.random.uniform(-max_dist, max_dist)
            pos = (x, y, self.net_params['ue_height_m'])
            self.user_equipments.append(UserEquipment(i, pos, self.net_params['ue_height_m']))

    def _calculate_sinr(self, ue, serving_pl, all_path_losses):
        """
        Calculates the Signal-to-Interference-plus-Noise Ratio (SINR) for a given UE.
        SINR = S / (I + N)
        """
        # Convert serving BS Tx power from dBm to watts
        tx_power_watts = 10**((self.net_params['bs_tx_power_dbm'] - 30) / 10)

        # Received power from serving BS (S) in watts
        received_power_watts = tx_power_watts / (10**(serving_pl / 10))

        # Total interference from other BSs (I) in watts
        interference_watts = 0
        for bs, pl in all_path_losses:
            if bs != ue.serving_bs:
                interference_watts += tx_power_watts / (10**(pl / 10))

        # Thermal noise (N) in watts
        k = 1.38e-23  # Boltzmann constant
        T = 290       # Temperature in Kelvin (room temperature)
        B = self.sim_params['bandwidth_mhz'] * 1e6 # Bandwidth in Hz
        noise_watts = k * T * B

        # Receiver noise figure
        noise_figure_linear = 10**(self.ch_params['noise_figure_db'] / 10)
        total_noise_watts = noise_watts * noise_figure_linear

        # SINR in linear scale and then converted to dB
        sinr_linear = received_power_watts / (interference_watts + total_noise_watts)
        return 10 * np.log10(sinr_linear)

    def _calculate_throughput(self, sinr_db):
        """
        Calculates throughput using the Shannon-Hartley theorem (a simplified model).
        Throughput = B * log2(1 + SINR)
        """
        sinr_linear = 10**(sinr_db / 10)
        B_Hz = self.sim_params['bandwidth_mhz'] * 1e6

        # Shannon-Hartley theorem gives the theoretical upper bound on channel capacity
        throughput_bps = B_Hz * np.log2(1 + sinr_linear)

        return throughput_bps / 1e6 # Convert from bps to Mbps

    def _save_results(self, results):
        """
        Saves the simulation results to a JSON file.
        """
        with open(self.out_params['results_file'], 'w') as f:
            json.dump(results, f, indent=4)
