from datetime import date, datetime

from borrowing import Borrowing, BorrowingStatus
from book import Book
from book_copy import Copy
from copy_status import CopyStatus
from order import Order, OrderStatus
from reader import Reader
from reader_status import ReaderStatus


class DomainMapper:
    """Convert SQLite rows into the application's domain objects."""

    @staticmethod
    def reader(row):
        """Map a reader row to a Reader object."""
        return Reader(row["id"], row["name"], row["email"], row["phone"], datetime.fromisoformat(row["registration_date"]), ReaderStatus(row["status"]))

    @staticmethod
    def book(row):
        """Map a book row to a Book object."""
        publication_date = date.fromisoformat(row["publication_date"]) if row["publication_date"] else None
        return Book(row["id"], row["title"], row["author"], row["isbn"], row["description"], publication_date, row["total_copies"], row["available_copies"])

    @staticmethod
    def copy(row):
        """Map a copy row to a Copy object."""
        return Copy(row["id"], row["book_id"], CopyStatus(row["status"]), row["location"], date.fromisoformat(row["acquisition_date"]))

    @staticmethod
    def borrowing(row):
        """Map a borrowing row to a Borrowing object."""
        due_date = date.fromisoformat(row["due_date"]) if row["due_date"] else None
        return_date = datetime.fromisoformat(row["return_date"]) if row["return_date"] else None
        return Borrowing(row["id"], row["reader_id"], row["copy_id"], row["order_id"], datetime.fromisoformat(row["borrow_date"]), due_date, return_date, BorrowingStatus(row["status"]))

    @staticmethod
    def order(row):
        """Map an order row to an Order object."""
        return Order(
            row["id"], row["reader_id"], row["book_id"], datetime.fromisoformat(row["order_date"]), OrderStatus(row["status"]),
            datetime.fromisoformat(row["fulfilled_date"]) if row["fulfilled_date"] else None,
            datetime.fromisoformat(row["cancellation_date"]) if row["cancellation_date"] else None,
            row["reserved_copy_id"], datetime.fromisoformat(row["reservation_expiry_date"]) if row["reservation_expiry_date"] else None,
        )
