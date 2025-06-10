import sys
from pathlib import Path

# Ensure package can be imported without installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
