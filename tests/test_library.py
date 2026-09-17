from datetime import datetime, timedelta

from borrowing import BorrowingStatus
from copy_status import CopyStatus
from order import OrderStatus
from sqlite_library import Library


def test_add_reader_book_and_copy_creates_inventory(tmp_path):
    library = Library(database_path=tmp_path / "library.db")

    reader = library.add_reader("Ada Lovelace", "ada@example.com", "555-0101")
    book = library.add_book("The Pragmatic Programmer", "David Thomas and Andrew Hunt", "978-0135957059")
    copy = library.add_copy(book.id, "A-01")

    assert reader.name == "Ada Lovelace"
    assert book.title == "The Pragmatic Programmer"
    assert copy.status == CopyStatus.AVAILABLE
    assert library.books[book.id].available_copies == 1
    assert library.books[book.id].total_copies == 1


def test_borrow_and_return_updates_availability(tmp_path):
    library = Library(database_path=tmp_path / "library.db")

    reader = library.add_reader("Grace Hopper", "grace@example.com", "555-0102")
    book = library.add_book("Algorithms", "Robert Sedgewick", "978-0201398298")
    copy = library.add_copy(book.id, "B-01")

    borrowing = library.borrow(reader.id, copy.id)

    assert borrowing.status == BorrowingStatus.ACTIVE
    assert library.copies[copy.id].status == CopyStatus.BORROWED
    assert library.books[book.id].available_copies == 0

    returned = library.return_book(borrowing.id)

    assert returned.status == BorrowingStatus.RETURNED
    assert library.copies[copy.id].status == CopyStatus.AVAILABLE
    assert library.books[book.id].available_copies == 1


def test_order_is_reserved_and_expired_reservations_are_cancelled(tmp_path):
    now = datetime(2024, 1, 1, 9, 0, 0)
    library = Library(database_path=tmp_path / "library.db", clock=lambda: now)

    reader_one = library.add_reader("Alan Turing", "alan@example.com", "555-0103")
    reader_two = library.add_reader("Margaret Hamilton", "margaret@example.com", "555-0104")
    book = library.add_book("Computer Architecture", "John L.Hennessy", "978-0123704900")
    copy = library.add_copy(book.id, "C-01")

    order = library.create_order(reader_two.id, book.id)
    borrowing = library.borrow(reader_one.id, copy.id)

    library.return_book(borrowing.id)

    assert library.orders[order.id].reserved_copy_id == copy.id
    assert library.copies[copy.id].status == CopyStatus.RESERVED
    assert library.orders[order.id].reservation_expiry_date is not None

    now = now + timedelta(days=4)
    expired = library.process_expired_reservations()

    assert len(expired) == 1
    assert expired[0].status == OrderStatus.CANCELLED
    assert library.orders[order.id].status == OrderStatus.CANCELLED
    assert library.copies[copy.id].status == CopyStatus.AVAILABLE


def test_reader_name_is_required(tmp_path):
    library = Library(database_path=tmp_path / "library.db")

    try:
        library.add_reader("   ")
        assert False, "Expected ValidationError"
    except Exception as exc:  # noqa: BLE001
        assert "Reader name is required" in str(exc)


def test_duplicate_isbn_is_rejected(tmp_path):
    library = Library(database_path=tmp_path / "library.db")
    library.add_book("Clean Code", "Robert Martin", "978-0132350884")

    try:
        library.add_book("Another Title", "Another Author", "978-0132350884")
        assert False, "Expected ValidationError"
    except Exception as exc:  # noqa: BLE001
        assert "already exists" in str(exc)


def test_reader_cannot_borrow_more_than_four_active_books(tmp_path):
    library = Library(database_path=tmp_path / "library.db")
    reader = library.add_reader("Linus Torvalds", "linus@example.com", "555-9999")
    book_ids = []
    for index in range(4):
        book = library.add_book(f"Book {index}", "Author", f"978-00000000{index:02d}")
        book_ids.append(book.id)
        library.add_copy(book.id, f"Shelf-{index}")

    copy_ids = list(library.copies.keys())[:4]
    for copy_id in copy_ids:
        library.borrow(reader.id, copy_id)

    extra_book = library.add_book("Fifth Book", "Author", "978-1111111111")
    extra_copy = library.add_copy(extra_book.id, "Shelf-5")

    try:
        library.borrow(reader.id, extra_copy.id)
        assert False, "Expected ValidationError"
    except Exception as exc:  # noqa: BLE001
        assert "at most 4 active borrowings" in str(exc)


def test_cancel_pending_order_releases_reserved_copy(tmp_path):
    library = Library(database_path=tmp_path / "library.db")
    reader = library.add_reader("Grace Murray", "grace2@example.com", "555-0105")
    other_reader = library.add_reader("John Smith", "john@example.com", "555-0115")
    book = library.add_book("Operating Systems", "Abraham Silberschatz", "978-1118063330")
    copy = library.add_copy(book.id, "D-01")

    order = library.create_order(reader.id, book.id)
    borrowing = library.borrow(other_reader.id, copy.id)
    library.return_book(borrowing.id)

    assert library.orders[order.id].reserved_copy_id == copy.id

    cancelled = library.cancel_order(order.id)

    assert cancelled.status.value == OrderStatus.CANCELLED.value
    assert library.orders[order.id].status == OrderStatus.CANCELLED
    assert library.copies[copy.id].status == CopyStatus.AVAILABLE


def test_inactive_reader_cannot_create_order_or_borrow(tmp_path):
    library = Library(database_path=tmp_path / "library.db")
    reader = library.add_reader("Jane Doe", "jane@example.com", "555-0110")
    with library._connection() as connection:
        connection.execute("UPDATE readers SET status = ? WHERE id = ?", ("inactive", reader.id))

    book = library.add_book("Data Structures", "Narasimha", "978-0132576272")
    copy = library.add_copy(book.id, "E-01")

    try:
        library.create_order(reader.id, book.id)
        assert False, "Expected ValidationError"
    except Exception as exc:  # noqa: BLE001
        assert "Inactive readers cannot create orders" in str(exc)

    try:
        library.borrow(reader.id, copy.id)
        assert False, "Expected ValidationError"
    except Exception as exc:  # noqa: BLE001
        assert "Inactive readers cannot borrow books" in str(exc)
