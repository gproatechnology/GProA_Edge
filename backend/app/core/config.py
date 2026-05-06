import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Define ROOT_DIR as the backend root (parent of app)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database Config
MONGO_URL = os.getenv('MONGO_URL')
DB_NAME = os.getenv('DB_NAME', 'gproa_edge')

# OpenAI Config
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY') or os.getenv('EMERGENT_LLM_KEY')
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

# Google Drive Config (Placeholder for future sync)
GOOGLE_DRIVE_CREDENTIALS = os.getenv('GOOGLE_DRIVE_CREDENTIALS')  # JSON string or path to file

# Initialize OpenAI Client
openai_client = None
if OPENAI_API_KEY and not DEMO_MODE:
    from openai import AsyncOpenAI
    openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    logger.info("Using OpenAI API")
else:
    logger.info("Demo mode: using mock AI responses")
