import logging
from colorama import Fore, Style, init

from config import IS_DEBUG

# Initialize colorama for cross-platform compatibility
init(autoreset=True)

# Create a logger
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

# Create a custom formatter with color for error messages
class CustomFormatter(logging.Formatter):
    """Custom formatter to add color to error messages."""

    def format(self, record):
        if record.levelno == logging.ERROR:
            # Add red color for ERROR level logs
            record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        if record.levelno == logging.DEBUG:
            record.msg = f"{Fore.YELLOW}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Create a file handler to write logs to a file
file_handler = logging.FileHandler('logs/app.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Create a stream handler to print logs to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG if IS_DEBUG else logging.INFO)

# Use the custom formatter for the console output
console_formatter = CustomFormatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

