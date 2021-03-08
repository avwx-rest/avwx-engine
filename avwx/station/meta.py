"""
Shared list and metadata
"""

from avwx.load_utils import LazyLoad

__LAST_UPDATED__ = "2021-01-24"

# Lazy data loading to speed up import times for unused features
STATIONS = LazyLoad("stations")
