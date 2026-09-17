from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class OrderStatus(str, Enum):
    """Lifecycle states for an order."""

    PENDING = "pending"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


@dataclass
class Order:
    """A reader's request for a book or returned reserved copy."""

    id: int
    reader_id: int
    book_id: int
    order_date: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    fulfilled_date: Optional[datetime] = None
    cancellation_date: Optional[datetime] = None
    reserved_copy_id: Optional[int] = None
    reservation_expiry_date: Optional[datetime] = None

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Return whether this pending reservation has expired."""
        return (
            self.status == OrderStatus.PENDING
            and self.reservation_expiry_date is not None
            and self.reservation_expiry_date < (now or datetime.now())
        )


class OrderService:
    """Coordinate order creation, cancellation, and expiry."""

    def __init__(self, library):
        """Create an order service backed by a Library facade."""
        self.library = library

    def create_order(self, reader_id, book_id):
        """Create a pending order."""
        return self.library._create_order(reader_id, book_id)

    def cancel_order(self, order_id):
        """Cancel a pending order."""
        return self.library._cancel_order(order_id)

    def get_order(self, order_id):
        """Load one order."""
        return self.library._get_order(order_id)

    def get_reader_orders(self, reader_id):
        """Load orders for one reader."""
        return self.library._get_reader_orders(reader_id)

    def process_expired_reservations(self):
        """Cancel expired reservations."""
        return self.library._process_expired_reservations()
