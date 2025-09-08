import numpy as np
import json
from numpy.linalg import inv, det
from hexagon_simulator.utils.config_parser import ConfigParser
from hexagon_simulator.network_elements.base_station import BaseStation
from hexagon_simulator.network_elements.user_equipment import UserEquipment
from hexagon_simulator.network_elements.packet import Packet
from hexagon_simulator.network_elements.srs import SRS
from hexagon_simulator.channel_models import g_3gpp_38_901
from hexagon_simulator.phy.channel_estimator import ChannelEstimator
from hexagon_simulator.phy.precoder import ZFPrecoder
from hexagon_simulator.phy.rate_control import RateControl
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
        self.tdd_params = self.config.get_tdd_parameters()
        self.ul_params = self.config.get_uplink_parameters()

        self.base_stations = []
        self.user_equipments = []
        self.scheduler = self._create_scheduler()
        self.channel_estimator = ChannelEstimator(error_variance=self.ch_params['channel_estimation_error_variance'])
        self.precoder = ZFPrecoder()
        self.rate_control = RateControl()
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
        slot_duration_ms = self.sim_params['time_step_ms']
        num_slots = int(duration_ms / slot_duration_ms)

        num_dl_symbols = self.tdd_params['num_dl_symbols']
        num_guard_symbols = self.tdd_params['num_guard_symbols']

        for slot_index in range(num_slots):
            current_time_ms = slot_index * slot_duration_ms

            for bs in self.base_stations:
                bs.received_srs.clear()

            for ue in self.user_equipments:
                ue.generate_packet(current_time_ms, Packet)

            for symbol_index in range(14):
                if symbol_index < num_dl_symbols:
                    if symbol_index == 0:
                        for bs in self.base_stations:
                            self._schedule_and_transmit(bs, current_time_ms, slot_duration_ms)

                elif symbol_index >= num_dl_symbols + num_guard_symbols:
                    if symbol_index == num_dl_symbols + num_guard_symbols:
                        for ue in self.user_equipments:
                            srs = SRS(ue.ue_id, self.ul_params['srs_tx_power_dbm'])
                            if ue.serving_bs:
                                ue.serving_bs.received_srs.append(srs)

                        for bs in self.base_stations:
                            self._perform_channel_estimation(bs)

        print("Simulation finished. Aggregating and saving results...")
        self._save_results()
        print("Results saved.")

    def _perform_channel_estimation(self, bs):
        for srs in bs.received_srs:
            ue = self.user_equipments[srs.ue_id]
            h_true = self._calculate_mimo_channel(ue, bs)
            h_est = self.channel_estimator.estimate(h_true)
            bs.estimated_channels[ue.ue_id] = h_est

    def _schedule_and_transmit(self, bs, time_ms, time_step_ms):
        ue_ids_with_data = [ue_id for ue_id, queue in bs.ue_queues.items() if queue]
        if not ue_ids_with_data: return

        if isinstance(self.scheduler, RoundRobinScheduler):
            scheduled_ue_id = self.scheduler.schedule(bs.bs_id, ue_ids_with_data)
            if scheduled_ue_id is None: return

            scheduled_ue = self.user_equipments[scheduled_ue_id]
            self._update_ue_metrics(scheduled_ue)
            self._transmit_data(scheduled_ue, time_ms, time_step_ms)

        elif isinstance(self.scheduler, ProportionalFairScheduler):
            ue_potential_throughputs = {ue_id: self._get_potential_throughput(self.user_equipments[ue_id]) for ue_id in ue_ids_with_data}
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
        num_dl_symbols = self.tdd_params['num_dl_symbols']
        dl_ratio = num_dl_symbols / 14.0
        data_transmitted_bytes = (ue.throughput_mbps * dl_ratio * 1e6 / 8) * (time_step_ms / 1000.0)

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
            x, y = center[0] + isd * np.cos(angle), center[1] + isd * np.sin(angle)
            self.base_stations.append(BaseStation(i + 1, (x, y, self.net_params['bs_height_m']), self.net_params['bs_tx_power_dbm'], self.net_params['bs_height_m'], self.mimo_params['num_bs_antennas']))

    def _create_ue_layout(self):
        max_dist = self.net_params['inter_site_distance_m']
        for i in range(self.sim_params['num_ues']):
            x, y = np.random.uniform(-max_dist, max_dist), np.random.uniform(-max_dist, max_dist)
            traffic_model = self._create_traffic_model()
            self.user_equipments.append(UserEquipment(i, (x, y, self.net_params['ue_height_m']), self.net_params['ue_height_m'], traffic_model, self.mimo_params['num_ue_antennas']))

    def _create_traffic_model(self):
        model_type = self.traffic_params['model']
        if model_type == 'FullBuffer': return FullBuffer()
        if model_type == 'FTPModel3': return FTPModel3(file_size_bytes=self.traffic_params['ftp_file_size_bytes'], mean_inter_arrival_ms=self.traffic_params['ftp_mean_inter_arrival_ms'])
        if model_type == 'XRModel': return XRModel(fps=self.traffic_params['xr_fps'], packet_size_mean_bytes=self.traffic_params['xr_packet_size_mean_bytes'])
        raise ValueError(f"Unknown traffic model: {model_type}")

    def _associate_ues(self):
        for ue in self.user_equipments:
            path_losses = [(bs, self._calculate_siso_path_loss(ue, bs)) for bs in self.base_stations]
            serving_bs, _ = min(path_losses, key=lambda x: x[1])
            ue.attach_to_bs(serving_bs)

    def _calculate_siso_path_loss(self, ue, bs):
        d_2d = np.linalg.norm(np.array(ue.position[:2]) - np.array(bs.position[:2]))
        d_3d = np.linalg.norm(np.array(ue.position) - np.array(bs.position))
        return g_3gpp_38_901._get_path_loss_siso(self.sim_params['scenario'], d_2d, d_3d, self.sim_params['frequency_ghz'], bs.height, ue.height)

    def _calculate_mimo_channel(self, ue, bs):
        d_2d = np.linalg.norm(np.array(ue.position[:2]) - np.array(bs.position[:2]))
        d_3d = np.linalg.norm(np.array(ue.position) - np.array(bs.position))
        return g_3gpp_38_901.get_mimo_channel(self.sim_params['scenario'], d_2d, d_3d, self.sim_params['frequency_ghz'], bs.height, ue.height, bs.num_antennas, ue.num_antennas)

    def _update_ue_metrics(self, ue):
        h_est = ue.serving_bs.estimated_channels.get(ue.ue_id)
        if h_est is None:
            h_est = self._calculate_mimo_channel(ue, ue.serving_bs)

        precoding_matrix = self.precoder.get_precoding_matrix(h_est)

        h_true = self._calculate_mimo_channel(ue, ue.serving_bs)
        h_eff = h_true @ precoding_matrix

        interference_channels = {bs.bs_id: self._calculate_mimo_channel(ue, bs) for bs in self.base_stations if bs != ue.serving_bs}

        ue.sinr_dB = self._calculate_sinr(ue, h_eff, interference_channels)
        ue.throughput_mbps = self._calculate_throughput(ue.sinr_dB)

    def _calculate_sinr(self, ue, h_eff, interference_channels):
        signal_power = np.sum(np.abs(np.diag(h_eff))**2)
        inter_stream_interference = np.sum(np.abs(h_eff - np.diag(np.diag(h_eff)))**2)

        inter_cell_interference = 0
        for channel in interference_channels.values():
            inter_cell_interference += np.sum(np.abs(channel)**2)

        tx_power_watts = 10**((self.net_params['bs_tx_power_dbm'] - 30) / 10)
        noise_watts = 10**((self.ch_params['noise_figure_db'] - 174) / 10) * self.sim_params['bandwidth_mhz'] * 1e6

        total_interference = inter_stream_interference + inter_cell_interference
        sinr_linear = (tx_power_watts * signal_power) / (tx_power_watts * total_interference + noise_watts)
        return 10 * np.log10(sinr_linear) if sinr_linear > 0 else -np.inf

    def _calculate_throughput(self, sinr_db):
        mod_order, code_rate = self.rate_control.select_mcs(sinr_db)
        if mod_order == 0:
            return 0

        # This is a simplification. A more detailed model would consider the number of resource blocks, etc.
        # Here, we calculate spectral efficiency and multiply by bandwidth.
        spectral_efficiency = mod_order * code_rate
        B_Hz = self.sim_params['bandwidth_mhz'] * 1e6

        # For MIMO, we can potentially transmit multiple streams
        # This is a simplification; a real system would have per-stream SINR and MCS.
        num_streams = min(self.mimo_params['num_bs_antennas'], self.mimo_params['num_ue_antennas'])

        return (spectral_efficiency * B_Hz * num_streams) / 1e6

    def _save_results(self):
        total_delivered_bytes = sum(p.size_bytes for p in self.delivered_packets)
        simulation_duration_s = self.sim_params['simulation_duration_ms'] / 1000.0
        app_throughput_mbps = (total_delivered_bytes * 8 / simulation_duration_s) / 1e6 if simulation_duration_s > 0 else 0
        packet_delays = [p.delivery_time_ms - p.generation_time_ms for p in self.delivered_packets if p.delivery_time_ms != -1]
        avg_packet_delay_ms = np.mean(packet_delays) if packet_delays else 0
        results = {'simulation_summary': {'application_throughput_mbps': app_throughput_mbps, 'average_packet_delay_ms': avg_packet_delay_ms, 'total_packets_delivered': len(self.delivered_packets)}, 'ue_final_state': [{'ue_id': ue.ue_id, 'serving_bs_id': ue.serving_bs.bs_id if ue.serving_bs else -1, 'final_sinr_dB': ue.sinr_dB, 'final_throughput_mbps': ue.throughput_mbps} for ue in self.user_equipments]}
        with open(self.out_params['results_file'], 'w') as f:
            json.dump(results, f, indent=4)
