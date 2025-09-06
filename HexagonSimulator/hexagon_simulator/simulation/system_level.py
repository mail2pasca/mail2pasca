import numpy as np
import json
from numpy.linalg import inv, det
from hexagon_simulator.utils.config_parser import ConfigParser
from hexagon_simulator.network_elements.base_station import BaseStation
from hexagon_simulator.network_elements.user_equipment import UserEquipment
from hexagon_simulator.network_elements.packet import Packet
from hexagon_simulator.channel_models import g_3gpp_38_901
from hexagon_simulator.traffic.full_buffer import FullBuffer
from hexagon_simulator.traffic.ftp_model import FTPModel3
from hexagon_simulator.traffic.xr_model import XRModel
from hexagon_simulator.scheduler.round_robin import RoundRobinScheduler
from hexagon_simulator.scheduler.proportional_fair import ProportionalFairScheduler

class SystemLevelSimulation:
    def __init__(self, config_file):
        self.config = ConfigParser(config_file)
        self.sim_params = self.config.get_simulation_parameters()
        self.net_params = self.config.get_network_parameters()
        self.ch_params = self.config.get_channel_parameters()
        self.out_params = self.config.get_output_parameters()
        self.traffic_params = self.config.get_traffic_parameters()
        self.scheduler_params = self.config.get_scheduler_parameters()
        self.mimo_params = self.config.get_mimo_parameters()

        self.base_stations = []
        self.user_equipments = []
        self.scheduler = self._create_scheduler()
        self.delivered_packets = []

    def _create_scheduler(self):
        scheduler_type = self.scheduler_params['type']
        if scheduler_type == 'RoundRobin':
            return RoundRobinScheduler()
        elif scheduler_type == 'ProportionalFair':
            return ProportionalFairScheduler(alpha=self.scheduler_params['pf_alpha'])
        else:
            raise ValueError(f"Unknown scheduler type: {scheduler_type}")

    def setup(self):
        self._create_bs_layout()
        self._create_ue_layout()
        self._associate_ues()

    def run(self):
        print("Setting up simulation environment...")
        self.setup()

        print(f"Running time-stepped simulation with {self.scheduler_params['type']} scheduler...")
        duration_ms = self.sim_params['simulation_duration_ms']
        time_step_ms = self.sim_params['time_step_ms']

        for time_ms in np.arange(0, duration_ms, time_step_ms):
            for ue in self.user_equipments:
                ue.generate_packet(time_ms, Packet)

            for bs in self.base_stations:
                self._schedule_and_transmit(bs, time_ms, time_step_ms)

        print("Simulation finished. Aggregating and saving results...")
        self._save_results()
        print("Results saved.")

    def _schedule_and_transmit(self, bs, time_ms, time_step_ms):
        ue_ids_with_data = [ue_id for ue_id, queue in bs.ue_queues.items() if queue]
        if not ue_ids_with_data:
            return

        if isinstance(self.scheduler, RoundRobinScheduler):
            scheduled_ue_id = self.scheduler.schedule(bs.bs_id, ue_ids_with_data)
            if scheduled_ue_id is None: return

            scheduled_ue = self.user_equipments[scheduled_ue_id]
            self._update_ue_metrics(scheduled_ue)
            self._transmit_data(scheduled_ue, time_ms, time_step_ms)

        elif isinstance(self.scheduler, ProportionalFairScheduler):
            ue_potential_throughputs = {ue_id: self._get_potential_throughput(self.user_equipments[ue_id])
                                        for ue_id in ue_ids_with_data}

            scheduled_ue_id = self.scheduler.schedule(ue_potential_throughputs)
            if scheduled_ue_id is None: return

            scheduled_ue = self.user_equipments[scheduled_ue_id]
            achieved_throughput = ue_potential_throughputs[scheduled_ue_id]
            scheduled_ue.throughput_mbps = achieved_throughput

            self._transmit_data(scheduled_ue, time_ms, time_step_ms)
            self.scheduler.update_avg_throughput(scheduled_ue_id, achieved_throughput, ue_ids_with_data)

    def _get_potential_throughput(self, ue):
        self._update_ue_metrics(ue)
        return ue.throughput_mbps

    def _transmit_data(self, ue, time_ms, time_step_ms):
        data_transmitted_bytes = (ue.throughput_mbps * 1e6 / 8) * (time_step_ms / 1000.0)
        queue = ue.serving_bs.ue_queues[ue.ue_id]

        while data_transmitted_bytes > 0 and queue:
            packet = queue[0]
            if packet.size_bytes <= data_transmitted_bytes:
                data_transmitted_bytes -= packet.size_bytes
                packet.mark_delivered(time_ms + time_step_ms)
                self.delivered_packets.append(queue.popleft())
            else:
                packet.size_bytes -= data_transmitted_bytes
                data_transmitted_bytes = 0

    def _create_bs_layout(self):
        center = (0, 0, self.net_params['bs_height_m'])
        self.base_stations.append(BaseStation(0, center, self.net_params['bs_tx_power_dbm'], self.net_params['bs_height_m'], self.mimo_params['num_bs_antennas']))
        isd = self.net_params['inter_site_distance_m']
        for i in range(self.net_params['num_base_stations'] - 1):
            angle = 2 * np.pi * i / 6
            x = center[0] + isd * np.cos(angle)
            y = center[1] + isd * np.sin(angle)
            pos = (x, y, self.net_params['bs_height_m'])
            self.base_stations.append(BaseStation(i + 1, pos, self.net_params['bs_tx_power_dbm'], self.net_params['bs_height_m'], self.mimo_params['num_bs_antennas']))

    def _create_ue_layout(self):
        max_dist = self.net_params['inter_site_distance_m']
        for i in range(self.sim_params['num_ues']):
            x = np.random.uniform(-max_dist, max_dist)
            y = np.random.uniform(-max_dist, max_dist)
            pos = (x, y, self.net_params['ue_height_m'])
            traffic_model = self._create_traffic_model()
            self.user_equipments.append(UserEquipment(i, pos, self.net_params['ue_height_m'], traffic_model, self.mimo_params['num_ue_antennas']))

    def _create_traffic_model(self):
        model_type = self.traffic_params['model']
        if model_type == 'FullBuffer':
            return FullBuffer()
        elif model_type == 'FTPModel3':
            return FTPModel3(file_size_bytes=self.traffic_params['ftp_file_size_bytes'], mean_inter_arrival_ms=self.traffic_params['ftp_mean_inter_arrival_ms'])
        elif model_type == 'XRModel':
            return XRModel(fps=self.traffic_params['xr_fps'], packet_size_mean_bytes=self.traffic_params['xr_packet_size_mean_bytes'])
        else:
            raise ValueError(f"Unknown traffic model: {model_type}")

    def _associate_ues(self):
        for ue in self.user_equipments:
            path_losses = [(bs, self._calculate_siso_path_loss(ue, bs)) for bs in self.base_stations]
            serving_bs, _ = min(path_losses, key=lambda x: x[1])
            ue.attach_to_bs(serving_bs)

    def _calculate_siso_path_loss(self, ue, bs):
        d_2d = np.linalg.norm(ue.position[:2] - bs.position[:2])
        d_3d = np.linalg.norm(ue.position - bs.position)
        return g_3gpp_38_901._get_path_loss_siso(self.sim_params['scenario'], d_2d, d_3d, self.sim_params['frequency_ghz'], bs.height, ue.height)

    def _calculate_mimo_channel(self, ue, bs):
        d_2d = np.linalg.norm(ue.position[:2] - bs.position[:2])
        d_3d = np.linalg.norm(ue.position - bs.position)
        return g_3gpp_38_901.get_mimo_channel(self.sim_params['scenario'], d_2d, d_3d, self.sim_params['frequency_ghz'], bs.height, ue.height, bs.num_antennas, ue.num_antennas)

    def _update_ue_metrics(self, ue):
        channels = {bs.bs_id: self._calculate_mimo_channel(ue, bs) for bs in self.base_stations}
        serving_channel = channels[ue.serving_bs.bs_id]

        ue.sinr_dB = self._calculate_sinr(ue, serving_channel, channels)
        ue.throughput_mbps = self._calculate_throughput(ue, ue.sinr_dB, serving_channel)

    def _calculate_sinr(self, ue, serving_channel, all_channels):
        # Placeholder for a more complex SINR calculation with a ZF receiver.
        # For now, we calculate an effective SINR from the channel matrix.
        # This is a simplification.
        signal_power = np.sum(np.abs(serving_channel)**2)

        interference_power = 0
        for bs_id, channel in all_channels.items():
            if bs_id != ue.serving_bs.bs_id:
                interference_power += np.sum(np.abs(channel)**2)

        tx_power_watts = 10**((self.net_params['bs_tx_power_dbm'] - 30) / 10)
        noise_watts = 10**((self.ch_params['noise_figure_db'] - 174) / 10) * self.sim_params['bandwidth_mhz'] * 1e6

        sinr_linear = (tx_power_watts * signal_power) / (tx_power_watts * interference_power + noise_watts)
        return 10 * np.log10(sinr_linear) if sinr_linear > 0 else -np.inf

    def _calculate_throughput(self, ue, sinr_db, h_matrix):
        if sinr_db == -np.inf: return 0

        sinr_linear = 10**(sinr_db / 10)
        B_Hz = self.sim_params['bandwidth_mhz'] * 1e6

        n_t = h_matrix.shape[1] # Number of transmit antennas
        n_r = h_matrix.shape[0] # Number of receive antennas

        # MIMO capacity formula (Shannon-Hartley generalization)
        identity = np.eye(n_r)
        h_h_hermitian = h_matrix @ h_matrix.conj().T

        # The term (sinr_linear / n_t) represents the SNR per transmit antenna
        capacity = B_Hz * np.log2(np.abs(det(identity + (sinr_linear / n_t) * h_h_hermitian)))

        return capacity / 1e6 # Convert to Mbps

    def _save_results(self):
        total_delivered_bytes = sum(p.size_bytes for p in self.delivered_packets)
        simulation_duration_s = self.sim_params['simulation_duration_ms'] / 1000.0
        app_throughput_mbps = (total_delivered_bytes * 8 / simulation_duration_s) / 1e6 if simulation_duration_s > 0 else 0

        packet_delays = [p.delivery_time_ms - p.generation_time_ms for p in self.delivered_packets if p.delivery_time_ms != -1]
        avg_packet_delay_ms = np.mean(packet_delays) if packet_delays else 0

        results = {
            'simulation_summary': {
                'application_throughput_mbps': app_throughput_mbps,
                'average_packet_delay_ms': avg_packet_delay_ms,
                'total_packets_delivered': len(self.delivered_packets)
            },
            'ue_final_state': [{'ue_id': ue.ue_id, 'serving_bs_id': ue.serving_bs.bs_id if ue.serving_bs else -1, 'final_sinr_dB': ue.sinr_dB, 'final_throughput_mbps': ue.throughput_mbps} for ue in self.user_equipments]
        }

        with open(self.out_params['results_file'], 'w') as f:
            json.dump(results, f, indent=4)
