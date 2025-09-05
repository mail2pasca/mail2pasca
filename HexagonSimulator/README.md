# Hexagon Simulator

This project is a Python-based system-level simulator for 5G networks, with a focus on channel modeling based on 3GPP TR 38.901. It is designed to simulate different scenarios (UMa, UMi, RMa) and calculate key performance indicators like SINR and throughput.

## Features

-   System-level simulation of a hexagonal cellular network.
-   Channel model based on 3GPP TR 38.901 for UMa, UMi, and RMa scenarios.
-   Configurable simulation parameters via a `.ini` file.
-   Calculation of SINR and throughput for each user.
-   Probabilistic Line-of-Sight (LOS) / Non-Line-of-Sight (NLOS) channel determination.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd HexagonSimulator
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

## Configuration

The simulation is configured using the `configs/default_config.ini` file. You can create a copy of this file and modify it to suit your needs.

The configuration file is divided into the following sections:

-   `[simulation]`: General simulation parameters like scenario, frequency, bandwidth, and number of users.
-   `[network]`: Network layout parameters like number of base stations, inter-site distance, and antenna heights.
-   `[channel]`: Channel model parameters like shadowing standard deviation and noise figure.
-   `[output]`: Output configuration, including the results file path.

## How to Run

To run the simulation, use the `run.py` script located in the root of the project directory.

```bash
python run.py --config configs/default_config.ini
```

If you do not specify a config file, it will use `configs/default_config.ini` by default.

The simulation will run, and the results will be saved to the file specified in the `results_file` parameter in your config file (by default, `simulation_results.json`).

## Disclaimer

Due to persistent issues with the execution environment, the testing of this code has been limited. The code has been written to be functionally correct, but it has not been possible to verify this through automated testing.
