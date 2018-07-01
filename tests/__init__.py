"""
Michael duPont - michael@mdupont.com
tests - avwx test cases
"""

# stdlib
import sys
from os import path

# Add the parent directory to the test path
_loc = path.dirname(path.abspath(__file__))
parent_dir = path.join(_loc, '..')
sys.path.insert(0, parent_dir)
