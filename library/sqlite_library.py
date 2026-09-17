from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from library import NotFoundError
from domain_mapper import DomainMapper
from sqlite_borrowing import SQLiteBorrowing
from sqlite_catalog import SQLiteCatalog
from sqlite_database import SQLiteDatabase
from sqlite_orders import SQLiteOrders


class Library:
    """SQLite-backed library catalogue and workflow implementation."""

    def __init__(self, database_path=None, clock=None):
        """Create a repository and initialize its SQLite schema."""
        self._clock = clock or datetime.now
        self.database_path = Path(database_path or Path(__file__).with_name("library.db"))
        self.database = SQLiteDatabase(self.database_path)
        self.catalog_repository = SQLiteCatalog(self)
        self.borrowing_repository = SQLiteBorrowing(self)
        self.order_repository = SQLiteOrders(self)

    @contextmanager
    def _connection(self):
        """Open a foreign-key-enabled connection with transaction handling."""
        with self.database.connection() as connection:
            yield connection

    @property
    def readers(self):
        """Return all readers keyed by their database ID."""
        return self._collection("readers", self._reader)

    @property
    def books(self):
        """Return all books keyed by their database ID."""
        return self._collection("books", self._book)

    @property
    def copies(self):
        """Return all copies keyed by their database ID."""
        return self._collection("copies", self._copy)

    @property
    def borrowings(self):
        """Return all borrowings keyed by their database ID."""
        return self._collection("borrowings", self._borrowing)

    @property
    def orders(self):
        """Return all orders keyed by their database ID."""
        return self._collection("orders", self._order)

    def _collection(self, table, converter):
        """Load a table and convert each row into a domain object."""
        with self._connection() as connection:
            rows = connection.execute(f"SELECT * FROM {table} ORDER BY id")
            return {row["id"]: converter(row) for row in rows}

    def _require(self, connection, table, identifier, entity):
        """Load one row or raise a domain not-found error."""
        row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (identifier,)).fetchone()
        if row is None:
            raise NotFoundError(f"{entity} {identifier} was not found")
        return row

    def _reader(self, row):
        """Convert a reader row into a Reader dataclass."""
        return DomainMapper.reader(row)

    def _book(self, row):
        """Convert a book row into a Book dataclass."""
        return DomainMapper.book(row)

    def _copy(self, row):
        """Convert a copy row into a Copy dataclass."""
        return DomainMapper.copy(row)

    def _borrowing(self, row):
        """Convert a borrowing row into a Borrowing dataclass."""
        return DomainMapper.borrowing(row)

    def _order(self, row):
        """Convert an order row into an Order dataclass."""
        return DomainMapper.order(row)

    def add_reader(self, name, email=None, phone=None):
        """Delegate reader creation to the catalogue service."""
        return self.catalog_repository.add_reader(name, email, phone)

    def add_book(self, title, author=None, isbn=None, description=None, publication_date=None):
        """Delegate book creation to the catalogue service."""
        return self.catalog_repository.add_book(title, author, isbn, description, publication_date)

    def add_copy(self, book_id, location=None, acquisition_date=None):
        """Delegate copy creation to the catalogue service."""
        return self.catalog_repository.add_copy(book_id, location, acquisition_date)

    def get_book(self, book_id):
        """Delegate book lookup to the catalogue service."""
        return self.catalog_repository.get_book(book_id)

    def list_books(self):
        """Delegate book listing to the catalogue service."""
        return self.catalog_repository.list_books()

    def get_borrowing(self, borrowing_id):
        """Delegate borrowing lookup to the borrowing service."""
        return self.borrowing_repository.get_borrowing(borrowing_id)

    def get_order(self, order_id):
        """Delegate order lookup to the order service."""
        return self.order_repository.get_order(order_id)

    def get_reader_borrowings(self, reader_id, active_only=True):
        """Delegate reader borrowing lookup to the borrowing service."""
        return self.borrowing_repository.get_reader_borrowings(reader_id, active_only)

    def get_reader_orders(self, reader_id):
        """Delegate reader order lookup to the order service."""
        return self.order_repository.get_reader_orders(reader_id)

    def borrow(self, reader_id, copy_id, order_id=None, due_date=None):
        """Delegate borrowing to the borrowing service."""
        return self.borrowing_repository.borrow(reader_id, copy_id, order_id, due_date)

    def create_order(self, reader_id, book_id):
        """Delegate order creation to the order service."""
        return self.order_repository.create_order(reader_id, book_id)

    def cancel_order(self, order_id):
        """Delegate order cancellation to the order service."""
        return self.order_repository.cancel_order(order_id)

    def return_book(self, borrowing_id):
        """Delegate returns to the borrowing service."""
        return self.borrowing_repository.return_book(borrowing_id)

    def process_expired_reservations(self):
        """Delegate reservation expiry to the order service."""
        return self.order_repository.process_expired_reservations()

