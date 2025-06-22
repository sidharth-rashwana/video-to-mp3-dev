import os
from dotenv import load_dotenv
load_dotenv()

PORT = os.environ.get('PORT', 8000)
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
MONGO_URI = os.environ.get('MONGO_URI', os.getenv("MONGO_URI"))
LOG_FILE_NAME = os.environ.get('LOG_FILE_NAME', 'app')