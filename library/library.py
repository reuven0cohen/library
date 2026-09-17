"""Compatibility exports for the library domain model."""

from book import Book
from book_copy import Copy
from borrowing import Borrowing, BorrowingStatus, BorrowingService
from copy_status import CopyStatus
from library_error import LibraryError
from not_found_error import NotFoundError
from order import Order, OrderService, OrderStatus
from reader import Reader
from reader_status import ReaderStatus
from validation_error import ValidationError

MAX_ACTIVE_BORROWINGS = 4
RESERVATION_DAYS = 3

__all__ = [
    "Book", "Borrowing", "BorrowingStatus", "Copy", "CopyStatus",
    "LibraryError", "NotFoundError", "Order", "OrderStatus", "Reader",
    "ReaderStatus", "ValidationError", "MAX_ACTIVE_BORROWINGS", "RESERVATION_DAYS",
]
