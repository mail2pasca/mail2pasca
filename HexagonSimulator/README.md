# Hexagon Simulator

This project is a Python-based system-level simulator for 5G networks. It is designed to simulate a hexagonal cellular network with various traffic models and calculate key performance indicators.

## Features

-   **Time-Stepped Simulation:** The simulation runs over a configurable duration with discrete time steps, allowing for dynamic traffic modeling.
-   **Channel Model:** Implements channel models based on 3GPP TR 38.901 for UMa, UMi, and RMa scenarios, including probabilistic Line-of-Sight (LOS) / Non-Line-of-Sight (NLOS) conditions.
-   **Traffic Models:** Includes multiple application traffic models:
    -   **Full Buffer:** A continuous stream of data.
    -   **FTP Model 3:** Simulates bursty file transfers based on 3GPP specifications.
    -   **XR Model:** Simulates periodic traffic with jitter for Extended Reality applications.
-   **Queuing and Scheduling:** Implements packet queues at the base stations and a basic Round Robin scheduler to allocate resources.
-   **Key Performance Indicators (KPIs):** Calculates and reports:
    -   Application-level throughput.
    -   Average packet delay.
    -   Final SINR and physical layer throughput for each user.
-   **Configurability:** All key parameters are configurable via a `.ini` file.

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

-   `[simulation]`: General parameters like scenario, simulation duration, and number of users.
-   `[traffic]`: Select and configure the traffic model (FullBuffer, FTPModel3, or XRModel).
-   `[network]`: Network layout parameters like number of base stations, inter-site distance, and antenna heights.
-   `[channel]`: Channel model parameters like shadowing standard deviation and noise figure.
-   `[output]`: Output configuration, including the results file path.

## How to Run

To run the simulation, use the `run.py` script located in the root of the project directory.

```bash
python run.py --config configs/default_config.ini
```

If you do not specify a config file, it will use `configs/default_config.ini` by default.

The simulation will run, printing progress to the console. The final results will be saved to the file specified in the `results_file` parameter in your config file (by default, `simulation_results.json`).

The results file contains a summary of the simulation, including application throughput and average packet delay, as well as the final state of each user.
