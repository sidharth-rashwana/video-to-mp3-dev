import sys
import os  # Import the os module for directory creation
import logging
from app.server.config import environment
from starlette.requests import Request
from starlette.responses import Response

# Define the log directory and file name
log_directory = 'logs'
log_file_name = 'app.log'
log_file_path = os.path.join(log_directory, log_file_name)  # Combine directory and file name

# Create the log directory if it doesn't exist
os.makedirs(log_directory, exist_ok=True)

# Initialize the logger
logger = logging.getLogger('my_logger')
logger.setLevel(environment.LOG_LEVEL)

# Create a formatter
formatter = logging.Formatter(
    '{levelname} | {asctime} | {name}:{funcName}:{lineno}\n'
    '--------------------------------------------------------------------------\n'
    '{message}\n'
    '--------------------------------------------------------------------------\n',
    style='{'
)

# Create a console handler with colorized output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(environment.LOG_LEVEL)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Create a file handler for log rotation
file_handler = logging.handlers.RotatingFileHandler(
    log_file_path,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
file_handler.setLevel(environment.LOG_LEVEL)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Create an error log handler for stderr
error_handler = logging.StreamHandler(sys.stderr)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)
logger.addHandler(error_handler)

def logging_api_requests(request: Request, response: Response):
    logs = f'{request.client.host}:{request.client.port} {request.method} {request.url} {response.status_code}'
    logs += '\n\n' + '*********Request Headers Start***********\n'
    logs += '\n'.join(f'{name} : {value}' for name, value in request.headers.items())
    logs += '\n' + '*********Request Headers End***********\n'
    logs += '\n\n' + '*********Response Headers Start***********\n'
    logs += '\n'.join(f'{name} : {value}' for name, value in response.headers.items())
    logs += '\n' + '*********Response Headers End***********\n'
    logger.debug(logs)