from contextlib import contextmanager
import sqlite3
from pathlib import Path


class SQLiteDatabase:
    """Own SQLite connections, schema creation, and transaction boundaries."""

    def __init__(self, database_path):
        """Create the database wrapper and initialize its schema."""
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    @contextmanager
    def connection(self):
        """Yield a foreign-key-enabled connection with commit or rollback."""
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize_schema(self):
        """Create all application tables and indexes if needed."""
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS readers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    registration_date TEXT NOT NULL,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    author TEXT,
                    isbn TEXT UNIQUE,
                    description TEXT,
                    publication_date TEXT,
                    total_copies INTEGER NOT NULL DEFAULT 0,
                    available_copies INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS copies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL REFERENCES books(id),
                    status TEXT NOT NULL,
                    location TEXT,
                    acquisition_date TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS borrowings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reader_id INTEGER NOT NULL REFERENCES readers(id),
                    copy_id INTEGER NOT NULL REFERENCES copies(id),
                    order_id INTEGER,
                    borrow_date TEXT NOT NULL,
                    due_date TEXT,
                    return_date TEXT,
                    status TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reader_id INTEGER NOT NULL REFERENCES readers(id),
                    book_id INTEGER NOT NULL REFERENCES books(id),
                    order_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    fulfilled_date TEXT,
                    cancellation_date TEXT,
                    reserved_copy_id INTEGER REFERENCES copies(id),
                    reservation_expiry_date TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_borrowings_reader_status
                    ON borrowings(reader_id, status);
                CREATE INDEX IF NOT EXISTS idx_orders_book_status
                    ON orders(book_id, status);
                """
            )
