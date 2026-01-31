"""Configuration loading from environment."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key from environment. Returns None if not set or empty."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    return key if key else None
