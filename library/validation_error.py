from library_error import LibraryError


class ValidationError(LibraryError):
    """Raised when a library business rule is violated."""
