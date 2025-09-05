import configparser
import os

class ConfigParser:
    def __init__(self, config_file):
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found at: {config_file}")

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get_simulation_parameters(self):
        """Returns a dictionary of simulation parameters."""
        return {
            'scenario': self.config.get('simulation', 'scenario'),
            'frequency_ghz': self.config.getfloat('simulation', 'frequency_ghz'),
            'bandwidth_mhz': self.config.getfloat('simulation', 'bandwidth_mhz'),
            'simulation_duration_ms': self.config.getint('simulation', 'simulation_duration_ms'),
            'time_step_ms': self.config.getint('simulation', 'time_step_ms'),
            'num_ues': self.config.getint('simulation', 'num_ues'),
        }

    def get_traffic_parameters(self):
        """Returns a dictionary of traffic parameters."""
        return {
            'model': self.config.get('traffic', 'model'),
            'ftp_file_size_bytes': self.config.getint('traffic', 'ftp_file_size_bytes'),
            'ftp_mean_inter_arrival_ms': self.config.getint('traffic', 'ftp_mean_inter_arrival_ms'),
            'xr_fps': self.config.getint('traffic', 'xr_fps'),
            'xr_packet_size_mean_bytes': self.config.getint('traffic', 'xr_packet_size_mean_bytes'),
        }

    def get_network_parameters(self):
        """Returns a dictionary of network parameters."""
        return {
            'num_base_stations': self.config.getint('network', 'num_base_stations'),
            'inter_site_distance_m': self.config.getfloat('network', 'inter_site_distance_m'),
            'bs_height_m': self.config.getfloat('network', 'bs_height_m'),
            'ue_height_m': self.config.getfloat('network', 'ue_height_m'),
            'bs_tx_power_dbm': self.config.getfloat('network', 'bs_tx_power_dbm'),
        }

    def get_channel_parameters(self):
        """Returns a dictionary of channel parameters."""
        return {
            'shadowing_std_dev_db': self.config.getfloat('channel', 'shadowing_std_dev_db'),
            'noise_figure_db': self.config.getfloat('channel', 'noise_figure_db'),
        }

    def get_output_parameters(self):
        """Returns a dictionary of output parameters."""
        return {
            'log_level': self.config.get('output', 'log_level'),
            'results_file': self.config.get('output', 'results_file'),
        }
