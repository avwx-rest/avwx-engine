"""
Contains avwx custom exceptions
"""


class BadStation(Exception):
    """Station does not exist"""


class InvalidRequest(Exception):
    """Unable to fetch data"""


class SourceError(Exception):
    """Source servers returned an error code"""
