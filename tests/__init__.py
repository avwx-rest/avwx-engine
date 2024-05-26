"""AVWX Test Suite."""

# stdlib
import sys
from pathlib import Path

# Add the parent directory to the test path
sys.path.insert(0, str(Path(__file__).parent.joinpath("..").absolute()))
