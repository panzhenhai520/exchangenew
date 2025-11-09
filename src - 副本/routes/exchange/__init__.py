"""
Exchange module package.

Provides the shared blueprint, logger and common constants so that individual
route handlers can live in lightweight modules.
"""

from decimal import Decimal
import logging

from flask import Blueprint

# Get logger instance - DO NOT call basicConfig() here as it will override
# the logging configuration already set in main.py
logger = logging.getLogger(__name__)

exchange_bp = Blueprint('exchange', __name__, url_prefix='/api/exchange')

# Keep the original constant available for any module that might rely on it.
RATE_PRECISION = Decimal('0.0001')

# Import route modules so their view functions register with the shared
# blueprint. noqa comments silence lint complaints about unused imports.
from . import perform  # noqa: E402,F401
from . import validation  # noqa: E402,F401
from . import transactions  # noqa: E402,F401
from . import dual_direction  # noqa: E402,F401

__all__ = ['exchange_bp', 'logger', 'RATE_PRECISION']
