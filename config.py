"""Configuration management for the translation pipeline."""
import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration loaded from environment variables."""
    
    # Translation backend (hardcoded to ollama for local deployment)
    translator_backend: str = "ollama"
    
    # Ollama configuration
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b"
    
    # Whisper configuration
    whisper_model: str = "medium"
    whisper_device: str = "cuda"
    
    # TTS (Text-to-Speech) configuration
    tts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"  # Coqui TTS multilingual model
    tts_device: str = "cuda"  # Use "cpu" if no GPU
    tts_language: str = "fr"  # French for translation output
    
    # Translation settings
    max_chunk_tokens: int = 800
    translation_concurrency: int = 5
    
    # File paths
    upload_dir: str = "./uploads"
    output_dir: str = "./outputs"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            translator_backend=os.getenv("TRANSLATOR_BACKEND", "ollama"),
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "mistral:7b"),
            whisper_model=os.getenv("WHISPER_MODEL", "medium"),
            whisper_device=os.getenv("WHISPER_DEVICE", "cuda"),
            tts_model=os.getenv("TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2"),
            tts_device=os.getenv("TTS_DEVICE", "cuda"),
            tts_language=os.getenv("TTS_LANGUAGE", "fr"),
            max_chunk_tokens=int(os.getenv("MAX_CHUNK_TOKENS", "800")),
            translation_concurrency=int(os.getenv("TRANSLATION_CONCURRENCY", "5")),
            upload_dir=os.getenv("UPLOAD_DIR", "./uploads"),
            output_dir=os.getenv("OUTPUT_DIR", "./outputs"),
        )
    
    def ensure_directories(self) -> None:
        """Create upload and output directories if they don't exist."""
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

