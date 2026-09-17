from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from reader_status import ReaderStatus


@dataclass
class Reader:
    """A person registered to use the library."""

    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    registration_date: datetime = field(default_factory=datetime.now)
    status: ReaderStatus = ReaderStatus.ACTIVE
