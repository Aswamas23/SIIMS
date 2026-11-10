"""
Logger configuration for SIIMS Monitoring Agent.
Uses rotating file handler with configurable log level.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler


def get_logger(name: str, log_file: str = "siims_agent.log", log_level: str = "INFO") -> logging.Logger:
    """
    Create and configure a logger instance with both file and console handlers.
    
    Args:
        name: Logger name (typically __name__ of calling module)
        log_file: Path to log file (relative or absolute)
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if get_logger is called repeatedly
    if logger.handlers:
        return logger
    
    # Parse log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (5MB max, 3 backups)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If file handler fails, only log to console
        print(f"Warning: Could not create file handler for {log_file}: {e}", file=sys.stderr)
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
