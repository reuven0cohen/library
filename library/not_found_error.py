from library_error import LibraryError


class NotFoundError(LibraryError):
    """Raised when a requested library record does not exist."""
