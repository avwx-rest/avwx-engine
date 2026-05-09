"""Geo utilities requiring the ``geo`` optional dependency group.

Install with: ``pip install avwx-engine[geo]``
"""

from avwx.geo.flight_path import to_coordinates

__all__ = ["to_coordinates"]
