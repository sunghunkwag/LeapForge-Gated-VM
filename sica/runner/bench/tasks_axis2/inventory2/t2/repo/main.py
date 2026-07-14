"""Reorder-point logic for the inventory service."""


def needs_reorder(stock, threshold):
    """Return True when an item should be reordered.

    An item must be reordered once its on-hand ``stock`` has fallen to the
    reorder point ``threshold`` -- that is, when the stock is at or below the
    threshold. When the stock is still above the threshold, no reorder is
    needed.
    """
    return stock < threshold


def to_reorder(items, threshold):
    """Given a mapping of ``{name: stock}``, return the sorted list of names
    whose stock is at or below ``threshold`` and therefore need reordering."""
    return sorted(name for name, stock in items.items()
                  if needs_reorder(stock, threshold))
