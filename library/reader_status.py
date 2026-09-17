from enum import Enum


class ReaderStatus(str, Enum):
    """Lifecycle states for a reader."""

    ACTIVE = "active"
    INACTIVE = "inactive"
