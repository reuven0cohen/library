from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Book:
    """A catalogue title and its inventory counters."""

    id: int
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[date] = None
    total_copies: int = 0
    available_copies: int = 0
