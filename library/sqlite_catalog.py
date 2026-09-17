from sqlite3 import IntegrityError

from book import Book
from book_copy import Copy
from copy_status import CopyStatus
from domain_mapper import DomainMapper
from reader import Reader
from reader_status import ReaderStatus
from validation_error import ValidationError


class SQLiteCatalog:
    """Persist and query readers, books, and physical copies."""

    def __init__(self, library):
        """Create a catalogue repository using the shared SQLite library."""
        self.library = library

    def add_reader(self, name, email=None, phone=None):
        """Persist an active reader."""
        if not name or not name.strip():
            raise ValidationError("Reader name is required")
        registered = self.library._clock()
        with self.library._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO readers (name, email, phone, registration_date, status) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), email, phone, registered.isoformat(), ReaderStatus.ACTIVE.value),
            )
            return Reader(cursor.lastrowid, name.strip(), email, phone, registered, ReaderStatus.ACTIVE)

    def add_book(self, title, author=None, isbn=None, description=None, publication_date=None):
        """Persist a book and reject duplicate ISBN values."""
        if not title or not title.strip():
            raise ValidationError("Book title is required")
        try:
            with self.library._connection() as connection:
                cursor = connection.execute(
                    "INSERT INTO books (title, author, isbn, description, publication_date) VALUES (?, ?, ?, ?, ?)",
                    (title.strip(), author, isbn, description, publication_date.isoformat() if publication_date else None),
                )
                return Book(cursor.lastrowid, title.strip(), author, isbn, description, publication_date)
        except IntegrityError as error:
            if isbn:
                raise ValidationError(f"ISBN {isbn} already exists") from error
            raise

    def add_copy(self, book_id, location=None, acquisition_date=None):
        """Persist an available copy and update inventory counters."""
        acquired = acquisition_date or self.library._clock().date()
        with self.library._connection() as connection:
            book = self.library._require(connection, "books", book_id, "Book")
            cursor = connection.execute(
                "INSERT INTO copies (book_id, status, location, acquisition_date) VALUES (?, ?, ?, ?)",
                (book_id, CopyStatus.AVAILABLE.value, location, acquired.isoformat()),
            )
            connection.execute(
                "UPDATE books SET total_copies = total_copies + 1, available_copies = available_copies + 1 WHERE id = ?",
                (book_id,),
            )
            return Copy(cursor.lastrowid, book["id"], CopyStatus.AVAILABLE, location, acquired)

    def get_book(self, book_id):
        """Load one book by ID."""
        with self.library._connection() as connection:
            return DomainMapper.book(self.library._require(connection, "books", book_id, "Book"))

    def list_books(self):
        """Load all books."""
        return list(self.library.books.values())
