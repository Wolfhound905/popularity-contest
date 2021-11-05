class Error(Exception):
    """Base class for other exceptions"""

    pass


class NoResults(Error):
    """Raised when the database returns nothing"""

    pass
