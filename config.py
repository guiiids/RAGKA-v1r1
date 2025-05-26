import os
from dotenv import load_dotenv
load_dotenv()

# Load environment variables from .env file
# This is useful for local development
# OpenAI Configuration
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_KEY = os.getenv("OPENAI_KEY")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")

OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION")
# Azure OpenAI Deployment Names
EMBEDDING_DEPLOYMENT = os.getenv("EMBEDDING_DEPLOYMENT")
CHAT_DEPLOYMENT = os.getenv("CHAT_DEPLOYMENT")
# Azure Cognitive Search Configuration
SEARCH_ENDPOINT = os.getenv("SEARCH_ENDPOINT")
SEARCH_INDEX = os.getenv("SEARCH_INDEX")
SEARCH_KEY = os.getenv("SEARCH_KEY")
VECTOR_FIELD = os.getenv("VECTOR_FIELD")
# Logging Configuration
LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(levelname)s - %(message)s")
LOG_FILE = os.getenv("LOG_FILE", "app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# Feedback Configuration
FEEDBACK_DIR = os.getenv("FEEDBACK_DIR", "feedback_data")
FEEDBACK_FILE = os.getenv("FEEDBACK_FILE", "feedback.json") 
# Searches for .env file in the current directory or parent directories
# This is useful for local development
# --- Database Configuration ---
# Get database credentials from environment variables loaded from .env
# Provide default values if needed, though .env should ideally contain them
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost") # Look for POSTGRES_HOST
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")      # Look for POSTGRES_PORT
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")      # Look for POSTGRES_DB
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")    # Look for POSTGRES_USER
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")        # Look for POSTGRES_PASSWORD
POSTGRES_SSL_MODE = os.getenv("POSTGRES_SSL_MODE", "require") # Default to 'require' for Render