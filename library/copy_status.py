from enum import Enum


class CopyStatus(str, Enum):
    """Availability states for a physical book copy."""

    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"
