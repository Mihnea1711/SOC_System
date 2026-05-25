import logging
import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from .config import settings

ENGINE_DIR = Path(__file__).resolve().parent.parent.parent
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

    # File handler (Creates a new file for every run based on timestamp)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = LOG_DIR / f"detection_engine_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Export a default logger instance
logger = setup_logger()
