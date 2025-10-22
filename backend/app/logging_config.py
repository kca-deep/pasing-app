"""
Logging configuration for FastAPI backend

Ensures UTF-8 encoding for all log outputs to prevent Korean character corruption.
"""

import sys
import logging

def configure_logging():
    """
    Configure logging with UTF-8 encoding support.

    This prevents Korean character corruption on Windows systems.
    """
    # Force UTF-8 encoding for stdout/stderr
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

    # Configure logging format
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Ensure all loggers use UTF-8
    for handler in logging.root.handlers:
        if hasattr(handler, 'stream'):
            if hasattr(handler.stream, 'reconfigure'):
                handler.stream.reconfigure(encoding='utf-8')
