from borrowing import Borrowing, BorrowingStatus
from copy_status import CopyStatus
from domain_mapper import DomainMapper
from library import MAX_ACTIVE_BORROWINGS, OrderStatus, ReaderStatus, RESERVATION_DAYS
from datetime import timedelta
from validation_error import ValidationError


class SQLiteBorrowing:
    """Persist borrowing and return workflows."""

    def __init__(self, library):
        """Create a borrowing repository using the shared SQLite library."""
        self.library = library

    def get_borrowing(self, borrowing_id):
        """Load one borrowing by ID."""
        with self.library._connection() as connection:
            return DomainMapper.borrowing(self.library._require(connection, "borrowings", borrowing_id, "Borrowing"))

    def get_reader_borrowings(self, reader_id, active_only=True):
        """Load borrowings for one reader."""
        with self.library._connection() as connection:
            self.library._require(connection, "readers", reader_id, "Reader")
            query = "SELECT * FROM borrowings WHERE reader_id = ?"
            parameters = [reader_id]
            if active_only:
                query += " AND status = ?"
                parameters.append(BorrowingStatus.ACTIVE.value)
            return [DomainMapper.borrowing(row) for row in connection.execute(query + " ORDER BY id", parameters)]

    def _validate_borrow(self, connection, reader_id, copy_id, order_id):
        """Validate reader, copy, limit, and optional order."""
        reader = self.library._require(connection, "readers", reader_id, "Reader")
        copy = self.library._require(connection, "copies", copy_id, "Copy")
        book = self.library._require(connection, "books", copy["book_id"], "Book")
        if reader["status"] != ReaderStatus.ACTIVE.value:
            raise ValidationError("Inactive readers cannot borrow books")
        active = connection.execute("SELECT COUNT(*) FROM borrowings WHERE reader_id = ? AND status = ?", (reader_id, BorrowingStatus.ACTIVE.value)).fetchone()[0]
        if active >= MAX_ACTIVE_BORROWINGS:
            raise ValidationError(f"A reader can hold at most {MAX_ACTIVE_BORROWINGS} active borrowings")
        order = None
        if order_id is not None:
            order = self.library._require(connection, "orders", order_id, "Order")
            if order["reader_id"] != reader_id or order["book_id"] != book["id"] or order["status"] != OrderStatus.PENDING.value:
                raise ValidationError("Order does not belong to this reader or book")
            if copy["status"] == CopyStatus.RESERVED.value and order["reserved_copy_id"] != copy_id:
                raise ValidationError("Copy is reserved for another order")
        allowed = (CopyStatus.AVAILABLE.value, CopyStatus.RESERVED.value) if order else (CopyStatus.AVAILABLE.value,)
        if copy["status"] not in allowed:
            raise ValidationError("Copy is not available")
        return copy, book

    def _save_borrowing(self, connection, reader_id, copy_id, order_id, due_date, now, copy, book):
        """Persist borrowing and update related inventory and order state."""
        cursor = connection.execute("INSERT INTO borrowings (reader_id, copy_id, order_id, borrow_date, due_date, status) VALUES (?, ?, ?, ?, ?, ?)", (reader_id, copy_id, order_id, now.isoformat(), due_date.isoformat() if due_date else None, BorrowingStatus.ACTIVE.value))
        connection.execute("UPDATE copies SET status = ? WHERE id = ?", (CopyStatus.BORROWED.value, copy_id))
        if copy["status"] == CopyStatus.AVAILABLE.value:
            connection.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = ?", (book["id"],))
        if order_id is not None:
            connection.execute("UPDATE orders SET status = ?, fulfilled_date = ?, reserved_copy_id = NULL, reservation_expiry_date = NULL WHERE id = ?", (OrderStatus.FULFILLED.value, now.isoformat(), order_id))
        return Borrowing(cursor.lastrowid, reader_id, copy_id, order_id, now, due_date, None, BorrowingStatus.ACTIVE)

    def borrow(self, reader_id, copy_id, order_id=None, due_date=None):
        """Borrow an available copy and optionally fulfil an order."""
        now = self.library._clock()
        with self.library._connection() as connection:
            copy, book = self._validate_borrow(connection, reader_id, copy_id, order_id)
            return self._save_borrowing(connection, reader_id, copy_id, order_id, due_date, now, copy, book)

    def _reserve_returned_copy(self, connection, copy_id, book_id, now):
        """Reserve a returned copy for the oldest pending order."""
        pending = connection.execute("SELECT * FROM orders WHERE book_id = ? AND status = ? AND reserved_copy_id IS NULL ORDER BY order_date, id LIMIT 1", (book_id, OrderStatus.PENDING.value)).fetchone()
        if pending is None:
            return False
        connection.execute("UPDATE copies SET status = ? WHERE id = ?", (CopyStatus.RESERVED.value, copy_id))
        connection.execute("UPDATE orders SET reserved_copy_id = ?, reservation_expiry_date = ? WHERE id = ?", (copy_id, (now + timedelta(days=RESERVATION_DAYS)).isoformat(), pending["id"]))
        return True

    def _release_copy(self, connection, copy_id, book_id):
        """Release a copy and increment available inventory."""
        connection.execute("UPDATE copies SET status = ? WHERE id = ?", (CopyStatus.AVAILABLE.value, copy_id))
        connection.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = ?", (book_id,))

    def return_book(self, borrowing_id):
        """Return a copy and reserve it for the oldest matching order."""
        now = self.library._clock()
        with self.library._connection() as connection:
            borrowing = self.library._require(connection, "borrowings", borrowing_id, "Borrowing")
            if borrowing["status"] != BorrowingStatus.ACTIVE.value:
                raise ValidationError("Borrowing has already been returned")
            copy = self.library._require(connection, "copies", borrowing["copy_id"], "Copy")
            reserved = self._reserve_returned_copy(connection, copy["id"], copy["book_id"], now)
            if not reserved:
                self._release_copy(connection, copy["id"], copy["book_id"])
            connection.execute("UPDATE borrowings SET status = ?, return_date = ? WHERE id = ?", (BorrowingStatus.RETURNED.value, now.isoformat(), borrowing_id))
            return DomainMapper.borrowing(connection.execute("SELECT * FROM borrowings WHERE id = ?", (borrowing_id,)).fetchone())
