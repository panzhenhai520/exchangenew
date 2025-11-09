"""Backwards compatibility shim for exchange blueprint.

Historically the main application imported ``exchange_bp`` from this module.
After refactoring the large monolithic file into the ``routes.exchange`` package
we keep this file as a thin re-export to avoid touching existing imports.
"""

from .exchange import exchange_bp  # noqa: F401

__all__ = ['exchange_bp']
