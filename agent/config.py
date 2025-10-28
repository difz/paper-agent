from pydantic import BaseModel
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseModel):
    locale: str = os.getenv("APP_LOCALE", "id-ID")
    tz: str = os.getenv("APP_TZ", "Asia/Jakarta")
    chroma_dir: str = os.getenv("CHROMA_DIR", "./store/chroma")
    llm_model: str = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-004")
    top_k: int = int(os.getenv("TOP_K", "6"))
