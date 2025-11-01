import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    SCREENSHOTS_PATH = os.getenv("SCREENSHOTS_PATH", "./data/screenshots")
    TEMPLATES_PATH = os.getenv("TEMPLATES_PATH", "./data/templates.json")
    
    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in your environment.")
        return True

config = Config()
