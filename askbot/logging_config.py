"""File-based logging configuration with timestamps and rotation."""
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

def setup_logging(log_dir: Path = Path("logs")) -> None:
    """Configure file logging with timestamps and daily rotation."""
    log_dir.mkdir(exist_ok=True)
    
    # Main application log
    app_log = log_dir / "askbot.log"
    app_handler = logging.handlers.TimedRotatingFileHandler(
        filename=app_log,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8",
    )
    app_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    
    # Promotion-specific log
    promo_log = log_dir / "promotion.log"
    promo_handler = logging.handlers.TimedRotatingFileHandler(
        filename=promo_log,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    promo_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    
    # Error-only log
    error_log = log_dir / "errors.log"
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=error_log,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    error_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-4d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    error_handler.setLevel(logging.ERROR)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add file handlers
    root_logger.addHandler(app_handler)
    
    # Add promotion-specific logger
    promo_logger = logging.getLogger("askbot.promotion")
    promo_logger.addHandler(promo_handler)
    promo_logger.setLevel(logging.INFO)
    
    # Add error-only logger
    error_logger = logging.getLogger("askbot.errors")
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)
    
    # Keep console output for development
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root_logger.addHandler(console_handler)
    
    # Log startup
    logging.info("ASKBot logging initialized")
    logging.info(f"Log directory: {log_dir.absolute()}")
    logging.info(f"Log files: askbot.log, promotion.log, errors.log")
