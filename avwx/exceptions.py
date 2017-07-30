"""
Michael duPont - michael@mdupont.com
AVWX-Engine : avwx/exceptions.py

Contains avwx custom exceptions
"""


class BadStation(Exception):
    """Station does not exists"""
    pass


class InvalidRequest(Exception):
    """Unable to fetch data"""
    pass
