import logging
import sys

log_levels = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def setup_logging(level: str = 'INFO') -> None:
    """
    Set up logging for the application.

    Args:
    level (str): The logging level to use. Default is 'INFO'.

    - DEBUG: Detailed information, typically of interest only when diagnosing problems.
    - INFO: Confirmation that things are working as expected.
    - WARNING: An indication that something unexpected happened, or indicative of some problem in the near future.
    - ERROR: Due to a more serious problem, the software has not been able to perform some function.
    - CRITICAL: A very serious error, indicating that the program itself may be unable to continue running.
    """
    level = log_levels.get(level.upper(), logging.INFO)
    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    stderr_handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[stderr_handler])
