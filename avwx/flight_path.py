"""Compatibility shim — flight path utilities moved to avwx.geo.flight_path."""

from avwx.geo.flight_path import NAVAIDS, QCoord, to_coordinates

__all__ = ["NAVAIDS", "QCoord", "to_coordinates"]
