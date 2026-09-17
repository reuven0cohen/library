from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from copy_status import CopyStatus


@dataclass
class Copy:
    """A physical copy of a catalogue book."""

    id: int
    book_id: int
    status: CopyStatus = CopyStatus.AVAILABLE
    location: Optional[str] = None
    acquisition_date: date = field(default_factory=date.today)
