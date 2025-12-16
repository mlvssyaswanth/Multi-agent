"""
Configuration management for the Multi-Agent Coding Framework.
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Central configuration class."""
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please create a .env file with OPENAI_API_KEY=your_key"
        )
    
    # Model options: "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-turbo-preview", "gpt-3.5-turbo"
    # gpt-4o is the latest and most widely available (replaces the deprecated gpt-4)
    MODEL = "gpt-4o"
    TEMPERATURE = 0.7
    MAX_ITERATIONS = 5
    MAX_TOKENS = 4000

