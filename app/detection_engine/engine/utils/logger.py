import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import settings

ENGINE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = ENGINE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def setup_logger(name="detection-engine"):
    logger = logging.getLogger(name)
    
    # Set log level from config
    log_level_str = settings.app.get('log_level', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Prevent adding handlers multiple times if instantiated repeatedly
    if logger.handlers:
        return logger

    # Log format: [Time] [Level] [Module]: Message
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(module)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (10 MB per file, keep 5 backups)
    log_file_path = LOG_DIR / "detection_engine.log"
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=10*1024*1024, backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Export a default logger instance
logger = setup_logger()
