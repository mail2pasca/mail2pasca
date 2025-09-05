import sys
import os

# Add the project root to the Python path
# This is necessary to resolve the imports correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hexagon_simulator.main import main

if __name__ == '__main__':
    main()
