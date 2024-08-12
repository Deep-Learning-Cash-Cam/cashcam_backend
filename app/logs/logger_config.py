import logging
import os
from logging.handlers import RotatingFileHandler

def setup_global_logger(level=logging.INFO):
    # Create logs directory if it doesn't exist (log_dir is set to the parent directory of the current file)
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create handlers
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'cashcam_log.log'), 
        maxBytes=10*1024*1024,  # 10MB max file size
        backupCount=4
    )
    file_handler.setFormatter(formatter)

    # Create logger
    logger = logging.getLogger('cashcam')
    logger.setLevel(level)
    logger.addHandler(file_handler)

    return logger

def log_message(logger, level, message):
    if level == 'DEBUG':
        logger.debug(message)
    elif level == 'INFO':
        logger.info(message)
    elif level == 'WARNING':
        logger.warning(message)
    elif level == 'ERROR':
        logger.error(message)
    elif level == 'CRITICAL':
        logger.critical(message)
    else:
        logger.info(f"Unknown level '{level}': {message}")
        
# Set up the global logger object
global_logger = setup_global_logger()

# Function to import for logging
def log(message, level=logging.INFO):
    log_message(global_logger, level, message)
