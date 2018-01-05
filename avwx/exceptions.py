"""
Contains avwx custom exceptions
"""


class BadStation(Exception):
    """
    Station does not exist
    """
    pass


class InvalidRequest(Exception):
    """
    Unable to fetch data
    """
    pass
