import unittest
import os
import json
from hexagon_simulator.simulation.system_level import SystemLevelSimulation
from hexagon_simulator.utils.config_parser import ConfigParser

class TestSystemLevelSimulation(unittest.TestCase):

    def setUp(self):
        self.config_file = 'configs/default_config.ini'
        # Check if the config file exists in the parent directory
        if not os.path.exists(self.config_file):
            # If not, assume we are running from the root of the HexagonSimulator project
            self.config_file = 'HexagonSimulator/configs/default_config.ini'

        self.simulation = SystemLevelSimulation(self.config_file)
        self.config = ConfigParser(self.config_file)

    def test_simulation_run(self):
        """
        Tests that the simulation runs without errors and produces a results file.
        """
        self.simulation.run()

        output_params = self.config.get_output_parameters()
        results_file = output_params['results_file']

        # Check if results file exists
        self.assertTrue(os.path.exists(results_file), f"Results file '{results_file}' not found.")

        # Check if results file is not empty
        self.assertTrue(os.path.getsize(results_file) > 0, "Results file is empty.")

        # Check content of the results file
        with open(results_file, 'r') as f:
            results = json.load(f)

        sim_params = self.config.get_simulation_parameters()
        self.assertEqual(len(results), sim_params['num_ues'], "Number of results does not match number of UEs.")

    def tearDown(self):
        """
        Clean up the results file after tests.
        """
        output_params = self.config.get_output_parameters()
        results_file = output_params['results_file']
        if os.path.exists(results_file):
            os.remove(results_file)

if __name__ == '__main__':
    unittest.main()
