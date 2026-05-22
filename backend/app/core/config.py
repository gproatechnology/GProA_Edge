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
DB_NAME = os.getenv('DB_NAME', 'gproa_unified')

# Gemini Config
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('EMERGENT_LLM_KEY')
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

# CORS Config
CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000')

# Google Drive Config (Placeholder for future sync)
GOOGLE_DRIVE_CREDENTIALS = os.getenv('GOOGLE_DRIVE_CREDENTIALS')  # JSON string or path to file

# Initialize Gemini Client
gemini_client = None
is_dummy_key = GEMINI_API_KEY == "sk-your-key-here" or not GEMINI_API_KEY

if not is_dummy_key and not DEMO_MODE:
    try:
        from google import genai
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Using Gemini API")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        logger.info("Falling back to Demo mode")
else:
    logger.info("Demo mode active: using mock AI responses (Dummy key or DEMO_MODE=true)")
