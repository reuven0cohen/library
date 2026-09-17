from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from library import LibraryError, OrderStatus
from sqlite_library import Library


app = Flask(__name__)
app.secret_key = "library-development-key"
library = Library()
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "library123"
users = {DEMO_USERNAME: generate_password_hash(DEMO_PASSWORD)}


def seed_demo_data():
    """Insert initial demonstration records when the database is empty."""
    if library.books:
        return
    reader = library.add_reader("Ada Lovelace", "ada@example.com", "555-0101")
    book = library.add_book("The Pragmatic Programmer", "David Thomas and Andrew Hunt", "978-0135957059")
    library.add_copy(book.id, "A-01")
    library.add_copy(book.id, "A-02")
    library.add_book("Designing Data-Intensive Applications", "Martin Kleppmann", "978-1449373320")
    library.add_copy(2, "B-01")


seed_demo_data()


def login_required(view):
    """Redirect anonymous requests to the login page."""
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


@app.context_processor
def template_helpers():
    """Expose related domain lookups to dashboard templates."""
    return {
        "book_for_copy": lambda copy: library.books.get(copy.book_id),
        "reader_for": lambda reader_id: library.readers.get(reader_id),
        "book_for": lambda book_id: library.books.get(book_id),
    }


@app.route("/")
@login_required
def dashboard():
    """Render the authenticated library control panel."""
    active_borrowings = [item for item in library.borrowings.values() if item.status.value == "active"]
    pending_orders = [item for item in library.orders.values() if item.status == OrderStatus.PENDING]
    return render_template(
        "dashboard.html",
        books=library.list_books(),
        readers=list(library.readers.values()),
        copies=list(library.copies.values()),
        borrowings=list(library.borrowings.values()),
        orders=list(library.orders.values()),
        active_borrowings=active_borrowings,
        pending_orders=pending_orders,
        library=library,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate a user and redirect to the dashboard."""
    if "username" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if username in users and check_password_hash(users[username], password):
            session.clear()
            session["username"] = username
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Validate a new account and sign the user in."""
    if "username" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")
        if len(username) < 3:
            flash("Username must contain at least 3 characters.", "error")
        elif len(password) < 6:
            flash("Password must contain at least 6 characters.", "error")
        elif password != confirmation:
            flash("Passwords do not match.", "error")
        elif username in users:
            flash("That username is already registered.", "error")
        else:
            users[username] = generate_password_hash(password)
            session.clear()
            session["username"] = username
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.post("/logout")
def logout():
    """Clear the current session and return to login."""
    session.clear()
    return redirect(url_for("login"))


@app.post("/readers")
@login_required
def add_reader():
    """Create a reader from the dashboard form."""
    try:
        library.add_reader(request.form["name"], request.form.get("email"), request.form.get("phone"))
        flash("Reader added.", "success")
    except LibraryError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard"))


@app.post("/books")
@login_required
def add_book():
    """Create a book and its requested initial copies."""
    try:
        book = library.add_book(request.form["title"], request.form.get("author"), request.form.get("isbn"))
        copies = int(request.form.get("copies", 0) or 0)
        for index in range(copies):
            library.add_copy(book.id, f"{book.id}-{index + 1:02d}")
        flash("Book added.", "success")
    except (LibraryError, ValueError) as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard"))


@app.post("/copies")
@login_required
def add_copy():
    """Add one physical copy to an existing book."""
    try:
        library.add_copy(int(request.form["book_id"]), request.form.get("location"))
        flash("Copy added.", "success")
    except (LibraryError, ValueError) as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard"))


@app.post("/borrow")
@login_required
def borrow():
    """Borrow a selected available copy."""
    try:
        order_id = request.form.get("order_id")
        library.borrow(
            int(request.form["reader_id"]),
            int(request.form["copy_id"]),
            int(order_id) if order_id else None,
        )
        flash("Book borrowed.", "success")
    except (LibraryError, ValueError) as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard"))


@app.post("/return/<int:borrowing_id>")
@login_required
def return_book(borrowing_id):
    """Return one active borrowing."""
    try:
        library.return_book(borrowing_id)
        flash("Book returned and availability updated.", "success")
    except LibraryError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard"))


@app.post("/orders")
@login_required
def create_order():
    """Create a pending book order."""
    try:
        library.create_order(int(request.form["reader_id"]), int(request.form["book_id"]))
        flash("Order created.", "success")
    except (LibraryError, ValueError) as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard"))


@app.post("/orders/<int:order_id>/cancel")
@login_required
def cancel_order(order_id):
    """Cancel one pending order."""
    try:
        library.cancel_order(order_id)
        flash("Order cancelled.", "success")
    except LibraryError as error:
        flash(str(error), "error")
    return redirect(url_for("dashboard"))


@app.post("/maintenance/expire")
@login_required
def expire_reservations():
    """Process reservations that have passed their expiry date."""
    expired = library.process_expired_reservations()
    flash(f"Processed {len(expired)} expired reservation(s).", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    app.run(debug=True)
