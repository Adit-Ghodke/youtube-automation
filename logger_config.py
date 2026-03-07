import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from pathlib import Path  # <--- This line was missing

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """Setup logger with file and console handlers that support UTF-8."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Define a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create a logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # File handler with rotation and UTF-8 encoding
    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # Specify encoding for the file
    )
    file_handler.setFormatter(formatter)
    
    # Console handler with UTF-8 encoding
    # Use a custom stream that forces UTF-8, especially for Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except TypeError:
        # In some environments (like non-interactive scripts), this may fail.
        # It's a best-effort attempt.
        pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

