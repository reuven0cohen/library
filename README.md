# Library Management System

A Flask-based library management application for tracking books, readers, borrowings, returns, and orders.

## Features

- Manage books and copies
- Register and manage readers
- Borrow and return books
- Track active borrowing limits
- Record pending and fulfilled orders
- Demo login for quick testing

## Project structure

- `library/` - application code and templates
- `Diagrams/` - architecture and workflow diagrams
- `PROJECT.md` - project requirements and domain documentation
- `requirements.txt` - Python dependencies

## Demo login

- Username: `admin`
- Password: `library123`

## Requirements

- Python 3.12+
- Flask 3.x

## Setup

```bash
cd library
python -m pip install -r ../requirements.txt
```

If you use `uv`:

```bash
cd library
uv run --with-requirements ../requirements.txt flask --app app run --debug --host 0.0.0.0
```

## Run the app

From the project root:

```bash
cd library
flask --app app run --debug --host 0.0.0.0
```

Open the app in your browser at:

```text
http://127.0.0.1:5000
```

## Notes

This project is intended as a local library management demo and includes seeded demo data on first launch.
