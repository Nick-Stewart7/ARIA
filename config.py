import os
from dotenv import load_dotenv

load_dotenv()

USER_ID = os.getenv("USER_ID", "user")
DEFAULT_CONVERSATION_ID = os.getenv("DEFAULT_CONVERSATION_ID", "main")
