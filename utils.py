"""Small helper utilities."""

from typing import Iterable, List


def chunk(items: List, size: int) -> List[List]:
    """Split a sequence into chunks of at most size items."""
    if size <= 0:
        raise ValueError('size must be positive')
    return [list(items[i:i + size]) for i in range(0, len(items), size)]


def slugify(text: str) -> str:
    """Convert text to a lowercase dash-separated slug."""
    out = [c.lower() if c.isalnum() else '-' for c in text.strip()]
    return ''.join(out).strip('-')


def unique(items: Iterable) -> List:
    """Return items with duplicates removed, preserving order."""
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
