"""
Logging Module for Mini DB Query
Provides centralized logging with file rotation and database storage
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

from core.config import settings


class LogColors:
    """Console log colors"""
    DEBUG = '\033[36m'    # Cyan
    INFO = '\033[32m'     # Green
    WARNING = '\033[33m'  # Yellow
    ERROR = '\033[31m'    # Red
    CRITICAL = '\033[35m' # Magenta
    RESET = '\033[0m'


class ColoredFormatter(logging.Formatter):
    """Colored log formatter for console output"""
    
    COLORS = {
        logging.DEBUG: LogColors.DEBUG,
        logging.INFO: LogColors.INFO,
        logging.WARNING: LogColors.WARNING,
        logging.ERROR: LogColors.ERROR,
        logging.CRITICAL: LogColors.CRITICAL,
    }
    
    def format(self, record):
        # Add color to level name
        if sys.stdout.isatty():
            record.levelname = f"{self.COLORS.get(record.levelno, '')}{record.levelname}{LogColors.RESET}"
        return super().format(record)


def setup_logging(
    log_dir: str = "./logs",
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True
) -> logging.Logger:
    """
    Setup logging with file rotation and console output
    
    Args:
        log_dir: Directory for log files
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Enable console output
        enable_file: Enable file output
        
    Returns:
        Configured logger
    """
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Log format
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_format = ColoredFormatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with daily rotation
    if enable_file:
        # Main log file - rotates daily
        file_handler = TimedRotatingFileHandler(
            filename=log_path / "app.log",
            when='midnight',
            interval=1,
            backupCount=30,  # Keep 30 days
            encoding='utf-8'
        )
        file_handler.setFormatter(file_format)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        
        # Error log file - only errors
        error_handler = logging.FileHandler(
            filename=log_path / "error.log",
            encoding='utf-8'
        )
        error_handler.setFormatter(file_format)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
        
        # Query log file - for query operations
        query_handler = logging.FileHandler(
            filename=log_path / "query.log",
            encoding='utf-8'
        )
        query_handler.setFormatter(file_format)
        query_logger = logging.getLogger('query')
        query_logger.addHandler(query_handler)
        query_logger.setLevel(logging.INFO)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_format)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        root_logger.addHandler(console_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)


# Query logger for database operations
def get_query_logger() -> logging.Logger:
    """Get query logger for database operations"""
    return logging.getLogger('query')


# Operation logger for user actions
def get_operation_logger() -> logging.Logger:
    """Get operation logger for user actions"""
    return logging.getLogger('operation')


# Create loggers
logger = get_logger(__name__)
query_logger = get_query_logger()
operation_logger = get_operation_logger()
