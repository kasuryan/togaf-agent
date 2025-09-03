"""Configuration management for TOGAF Agent."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_chat_model: str = "gpt-4.1"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Application Configuration
    app_name: str = "TOGAF Tutor Agent"
    debug: bool = False
    
    # Directory Configuration
    data_dir: Path = Path("./data")
    users_dir: Path = Path("./users")
    knowledge_base_dir: Path = Path("./knowledge_base")
    
    # Processing Configuration
    chunk_size: int = 2000
    chunk_overlap: int = 200
    max_tokens_per_chunk: int = 3000
    
    # ChromaDB Configuration
    chroma_persist_directory: Path = Path("./knowledge_base/chroma_db")
    
    @validator('data_dir', 'users_dir', 'knowledge_base_dir', 'chroma_persist_directory', pre=True)
    def convert_to_path(cls, v):
        return Path(v) if not isinstance(v, Path) else v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_settings(env_file: Optional[str] = None) -> Settings:
    """Load application settings from environment variables."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()
    
    return Settings()


def ensure_directories(settings: Settings) -> None:
    """Create necessary directories if they don't exist."""
    directories = [
        settings.users_dir,
        settings.knowledge_base_dir,
        settings.chroma_persist_directory,
        settings.knowledge_base_dir / "embeddings",
        settings.knowledge_base_dir / "processed",
        settings.knowledge_base_dir / "metadata"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)