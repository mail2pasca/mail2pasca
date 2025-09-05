import argparse
from hexagon_simulator.simulation.system_level import SystemLevelSimulation

def main():
    """
    Main function to run the Hexagon Simulator.
    """
    parser = argparse.ArgumentParser(description='Hexagon Simulator for 5G Networks')
    parser.add_argument('--config', type=str, default='configs/default_config.ini',
                        help='Path to the configuration file.')
    args = parser.parse_args()

    # Create and run the simulation
    simulation = SystemLevelSimulation(args.config)
    simulation.run()

    print(f"Simulation finished. Results saved to {simulation.out_params['results_file']}")

if __name__ == '__main__':
    main()
