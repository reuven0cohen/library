from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Optional


class BorrowingStatus(str, Enum):
    """Lifecycle states for a borrowing."""

    ACTIVE = "active"
    RETURNED = "returned"


@dataclass
class Borrowing:
    """A reader's borrowing transaction for one physical copy."""

    id: int
    reader_id: int
    copy_id: int
    order_id: Optional[int] = None
    borrow_date: datetime = field(default_factory=datetime.now)
    due_date: Optional[date] = None
    return_date: Optional[datetime] = None
    status: BorrowingStatus = BorrowingStatus.ACTIVE


class BorrowingService:
    """Coordinate borrowing and return workflows."""

    def __init__(self, library):
        """Create a borrowing service backed by a Library facade."""
        self.library = library

    def borrow(self, reader_id, copy_id, order_id=None, due_date=None):
        """Borrow an available copy."""
        return self.library._borrow(reader_id, copy_id, order_id, due_date)

    def return_book(self, borrowing_id):
        """Return an active borrowing."""
        return self.library._return_book(borrowing_id)

    def get_borrowing(self, borrowing_id):
        """Load one borrowing."""
        return self.library._get_borrowing(borrowing_id)

    def get_reader_borrowings(self, reader_id, active_only=True):
        """Load borrowings for one reader."""
        return self.library._get_reader_borrowings(reader_id, active_only)
