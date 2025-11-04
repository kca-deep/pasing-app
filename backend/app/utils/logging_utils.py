"""
Standardized Logging Utilities for Document Parsing

Provides consistent logging format across all parsing strategies.
All parsers use the ParserLogger class for uniform log structure,
emojis, indentation, and log levels.

Example:
    from app.utils.logging_utils import ParserLogger

    parser_logger = ParserLogger("Docling", logger)
    parser_logger.start(filename, output_format="markdown", ocr_enabled=True)
    parser_logger.step(1, 3, "Processing document...")
    parser_logger.detail("Extracted 100 elements")
    parser_logger.success("Parsing complete", pages=10, tables=5)
"""

import logging
from typing import Dict, Any, Optional


class ParserLogger:
    """
    Standardized logger wrapper for parsing strategies

    Provides consistent logging methods with:
    - Standard emojis for visual clarity
    - Hierarchical indentation (4-space based)
    - Consistent format across all parsers

    Attributes:
        parser_name: Name of the parsing strategy (e.g., "Docling", "Dolphin Remote")
        logger: Python logging.Logger instance
        EMOJIS: Dictionary of standard emojis for different log types
    """

    EMOJIS = {
        'start': '🎯',
        'config': '📋',
        'document': '📄',
        'analysis': '🔍',
        'process': '⚙️',
        'page': '📖',
        'remote': '🌐',
        'save': '💾',
        'merge': '🔗',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }

    def __init__(self, parser_name: str, logger: logging.Logger):
        """
        Initialize parser logger

        Args:
            parser_name: Name of the parsing strategy (e.g., "Docling", "Dolphin Remote")
            logger: Python logger instance
        """
        self.parser_name = parser_name
        self.logger = logger

    def start(self, filename: str, **config):
        """
        Log parser start with configuration

        Logs the beginning of a parsing operation with configuration details.

        Args:
            filename: Document filename being parsed
            **config: Configuration key-value pairs (e.g., output_format="markdown")

        Example:
            parser_logger.start("doc.pdf", output_format="markdown", ocr_enabled=True)

            Output:
            🎯 [Docling] Parsing: doc.pdf
                📋 Output Format: markdown
                📋 Ocr Enabled: True
        """
        self.logger.info(f"{self.EMOJIS['start']} [{self.parser_name}] Parsing: {filename}")
        for key, value in config.items():
            # Convert snake_case to Title Case for display
            display_key = key.replace('_', ' ').title()
            self.logger.info(f"    {self.EMOJIS['config']} {display_key}: {value}")

    def step(self, current: int, total: int, description: str):
        """
        Log main processing step

        Args:
            current: Current step number (1-indexed)
            total: Total number of steps
            description: Step description

        Example:
            parser_logger.step(1, 4, "Creating dataset...")

            Output:
            ⚙️ Step 1/4: Creating dataset...
        """
        self.logger.info(f"    {self.EMOJIS['process']} Step {current}/{total}: {description}")

    def sub_step(self, description: str, emoji: Optional[str] = None):
        """
        Log sub-step (Level 2 indentation)

        Args:
            description: Sub-step description
            emoji: Optional emoji key from EMOJIS dict (e.g., 'document', 'remote')

        Example:
            parser_logger.sub_step("Calling remote OCR service...", emoji='remote')

            Output:
                ├─ 🌐 Calling remote OCR service...
        """
        prefix = f"{self.EMOJIS[emoji]} " if emoji and emoji in self.EMOJIS else ""
        self.logger.info(f"        ├─ {prefix}{description}")

    def detail(self, description: str, last: bool = False):
        """
        Log detail information (Level 2 indentation)

        Args:
            description: Detail description
            last: If True, use └─ instead of ├─ (visual indicator for last item)

        Example:
            parser_logger.detail("Converted: 10 pages", last=True)

            Output:
                └─ Converted: 10 pages
        """
        symbol = "└─" if last else "├─"
        self.logger.info(f"        {symbol} {description}")

    def page(self, current: int, total: int):
        """
        Log page processing

        Args:
            current: Current page number (1-indexed)
            total: Total number of pages

        Example:
            parser_logger.page(5, 10)

            Output:
            📖 Processing Page 5/10
        """
        self.logger.info(f"    {self.EMOJIS['page']} Processing Page {current}/{total}")

    def remote_call(self, endpoint: str, description: Optional[str] = None):
        """
        Log remote API call

        Args:
            endpoint: API endpoint or server name
            description: Optional description of the call

        Example:
            parser_logger.remote_call("GPU Server", "Layout analysis")

            Output:
                🌐 Calling GPU Server: Layout analysis
        """
        msg = f"        {self.EMOJIS['remote']} Calling {endpoint}"
        if description:
            msg += f": {description}"
        self.logger.info(msg)

    def success(self, summary: str, **metrics):
        """
        Log successful completion with metrics

        Args:
            summary: Success summary message
            **metrics: Metric key-value pairs (e.g., pages=10, tables=5)

        Example:
            parser_logger.success("Parsing complete", pages=10, tables=5, duration="45.2s")

            Output:
            ✅ Complete: Parsing complete
                └─ Pages: 10
                └─ Tables: 5
                └─ Duration: 45.2s
        """
        self.logger.info(f"    {self.EMOJIS['success']} Complete: {summary}")
        if metrics:
            for key, value in metrics.items():
                display_key = key.replace('_', ' ').title()
                self.logger.info(f"        └─ {display_key}: {value}")

    def warning(self, message: str, **details):
        """
        Log warning message

        Args:
            message: Warning message
            **details: Additional detail key-value pairs

        Example:
            parser_logger.warning("Fallback to local OCR", reason="Remote server unavailable")

            Output:
            ⚠️ Fallback to local OCR
                └─ Reason: Remote server unavailable
        """
        self.logger.warning(f"    {self.EMOJIS['warning']} {message}")
        if details:
            for key, value in details.items():
                display_key = key.replace('_', ' ').title()
                self.logger.warning(f"        └─ {display_key}: {value}")

    def error(self, summary: str, exc_info: bool = False, **details):
        """
        Log error message

        Args:
            summary: Error summary
            exc_info: If True, include exception traceback
            **details: Additional detail key-value pairs (e.g., file="path", reason="...")

        Example:
            parser_logger.error("Parsing failed", exc_info=True, reason="Connection timeout")

            Output:
            ❌ Failed: Parsing failed
                └─ Reason: Connection timeout
        """
        self.logger.error(f"    {self.EMOJIS['error']} Failed: {summary}", exc_info=exc_info)
        if details:
            for key, value in details.items():
                display_key = key.replace('_', ' ').title()
                self.logger.error(f"        └─ {display_key}: {value}")

    def resource_check(self, resource_name: str, available: bool, **info):
        """
        Log resource availability check

        Typically used at module level to check external dependencies,
        servers, or libraries.

        Args:
            resource_name: Name of resource (e.g., "GPU Server", "MinerU")
            available: Whether resource is available
            **info: Additional information (version, location, error, etc.)

        Example:
            parser_logger.resource_check("GPU Server", True, url="http://server:8005", status="healthy")

            Output:
            ✅ [GPU Server] Available
                └─ Url: http://server:8005
                └─ Status: healthy
        """
        emoji = self.EMOJIS['success'] if available else self.EMOJIS['warning']
        status = "Available" if available else "Not Available"
        self.logger.info(f"{emoji} [{resource_name}] {status}")

        if info:
            for key, value in info.items():
                display_key = key.replace('_', ' ').title()
                self.logger.info(f"    └─ {display_key}: {value}")


# Convenience functions for resource checks at module level
def log_resource_available(logger: logging.Logger, resource_name: str, **info):
    """
    Convenience function to log that a resource is available

    Args:
        logger: Python logger instance
        resource_name: Name of the resource
        **info: Additional information key-value pairs

    Example:
        log_resource_available(logger, "Dolphin GPU Server",
                                url="http://server:8005", version="1.0")
    """
    temp_logger = ParserLogger(resource_name, logger)
    temp_logger.resource_check(resource_name, True, **info)


def log_resource_unavailable(logger: logging.Logger, resource_name: str, **info):
    """
    Convenience function to log that a resource is not available

    Args:
        logger: Python logger instance
        resource_name: Name of the resource
        **info: Additional information key-value pairs (typically 'reason' or 'error')

    Example:
        log_resource_unavailable(logger, "Dolphin GPU Server",
                                 reason="Connection timeout",
                                 url="http://server:8005")
    """
    temp_logger = ParserLogger(resource_name, logger)
    temp_logger.resource_check(resource_name, False, **info)
