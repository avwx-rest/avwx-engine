"""
General aviation data fetch and updates
"""

# from avwx.data.build_aircraft import main as update_aircraft
from avwx.data.build_navaids import main as update_navaids
from avwx.data.build_stations import main as update_stations


def update_all() -> bool:
    """Update all local data. Requires a reimport to guarentee update"""
    for func in (update_navaids, update_stations):
        if func():
            return False
    return True


if __name__ == "__main__":
    update_all()
