import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "SentinelX EDR Backend"
    API_V1_STR: str = "/api"
    
    # Security & Auth
    JWT_SECRET: str = "supersecretkeychangeinproduction1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 Hours for lab ease
    
    # Database
    DATABASE_URL: str = "sqlite:///C:/Users/Mayur/.gemini/antigravity/scratch/sentinelx-edr/sentinelx.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    
    # AI Configuration (OpenAI or Ollama)
    AI_PROVIDER: str = "ollama"  # "openai", "ollama", or None
    AI_API_KEY: str = ""
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"

    # Agent configs
    AGENT_HEARTBEAT_TIMEOUT_SECONDS: int = 60  # Agent offline if no heartbeat for 60s

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
