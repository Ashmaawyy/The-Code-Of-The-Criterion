"""Logging configuration for the pipeline package.

Delegates to the project-wide setup in al_furqan.__init__.
"""

import logging

from al_furqan import setup_logging as _pkg_setup


def setup_logging(level: int = logging.INFO) -> None:
    """Configure logging once for the current process."""
    _pkg_setup(level)
