from order import Order, OrderStatus
from copy_status import CopyStatus
from domain_mapper import DomainMapper
from validation_error import ValidationError


class SQLiteOrders:
    """Persist order, cancellation, and reservation-expiry workflows."""

    def __init__(self, library):
        """Create an order repository using the shared SQLite library."""
        self.library = library

    def get_order(self, order_id):
        """Load one order by ID."""
        with self.library._connection() as connection:
            return DomainMapper.order(self.library._require(connection, "orders", order_id, "Order"))

    def get_reader_orders(self, reader_id):
        """Load all orders belonging to a reader."""
        with self.library._connection() as connection:
            self.library._require(connection, "readers", reader_id, "Reader")
            return [DomainMapper.order(row) for row in connection.execute("SELECT * FROM orders WHERE reader_id = ? ORDER BY id", (reader_id,))]

    def _release_copy(self, connection, copy_id, book_id):
        """Release a reserved copy and restore book availability."""
        connection.execute("UPDATE copies SET status = ? WHERE id = ?", (CopyStatus.AVAILABLE.value, copy_id))
        connection.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = ?", (book_id,))

    def create_order(self, reader_id, book_id):
        """Create a pending order for an existing book."""
        now = self.library._clock()
        with self.library._connection() as connection:
            reader = self.library._require(connection, "readers", reader_id, "Reader")
            self.library._require(connection, "books", book_id, "Book")
            if reader["status"] != "active":
                raise ValidationError("Inactive readers cannot create orders")
            duplicate = connection.execute("SELECT 1 FROM orders WHERE reader_id = ? AND book_id = ? AND status = ?", (reader_id, book_id, OrderStatus.PENDING.value)).fetchone()
            if duplicate:
                raise ValidationError("Reader already has a pending order for this book")
            cursor = connection.execute("INSERT INTO orders (reader_id, book_id, order_date, status) VALUES (?, ?, ?, ?)", (reader_id, book_id, now.isoformat(), OrderStatus.PENDING.value))
            return Order(cursor.lastrowid, reader_id, book_id, now)

    def cancel_order(self, order_id):
        """Cancel a pending order and release its reserved copy."""
        now = self.library._clock()
        with self.library._connection() as connection:
            order = self.library._require(connection, "orders", order_id, "Order")
            if order["status"] != OrderStatus.PENDING.value:
                raise ValidationError("Only pending orders can be cancelled")
            if order["reserved_copy_id"] is not None:
                copy = self.library._require(connection, "copies", order["reserved_copy_id"], "Copy")
                self._release_copy(connection, copy["id"], copy["book_id"])
            connection.execute("UPDATE orders SET status = ?, cancellation_date = ?, reserved_copy_id = NULL, reservation_expiry_date = NULL WHERE id = ?", (OrderStatus.CANCELLED.value, now.isoformat(), order_id))
            return DomainMapper.order(connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone())

    def process_expired_reservations(self):
        """Cancel expired reservations and release their copies."""
        now = self.library._clock()
        with self.library._connection() as connection:
            expired = connection.execute("SELECT * FROM orders WHERE status = ? AND reservation_expiry_date IS NOT NULL AND reservation_expiry_date < ?", (OrderStatus.PENDING.value, now.isoformat())).fetchall()
            result = []
            for order in expired:
                if order["reserved_copy_id"] is not None:
                    copy = self.library._require(connection, "copies", order["reserved_copy_id"], "Copy")
                    self._release_copy(connection, copy["id"], copy["book_id"])
                connection.execute("UPDATE orders SET status = ?, cancellation_date = ?, reserved_copy_id = NULL, reservation_expiry_date = NULL WHERE id = ?", (OrderStatus.CANCELLED.value, now.isoformat(), order["id"]))
                result.append(DomainMapper.order(connection.execute("SELECT * FROM orders WHERE id = ?", (order["id"],)).fetchone()))
            return result
