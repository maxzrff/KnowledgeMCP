"""
Configuration management with Pydantic validation.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    """Storage configuration."""

    documents_path: Path = Path("./data/documents")
    vector_db_path: Path = Path("./data/chromadb")
    model_cache_path: Path = Path.home() / ".cache" / "huggingface"

    @field_validator("documents_path", "vector_db_path", "model_cache_path")
    @classmethod
    def ensure_absolute_path(cls, v: Path) -> Path:
        return v.expanduser().resolve()


class EmbeddingSettings(BaseSettings):
    """Embedding model configuration."""

    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = Field(default=32, ge=1, le=128)
    device: Literal["cpu", "cuda"] = "cpu"


class ChunkingSettings(BaseSettings):
    """Text chunking configuration."""

    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)
    strategy: Literal["sentence", "paragraph", "fixed"] = "sentence"

    @field_validator("chunk_overlap")
    @classmethod
    def validate_overlap(cls, v: int, info: any) -> int:
        chunk_size = info.data.get("chunk_size", 500)
        if v >= chunk_size:
            raise ValueError("Chunk overlap must be less than chunk size")
        return v


class ProcessingSettings(BaseSettings):
    """Document processing configuration."""

    max_concurrent_tasks: int = Field(default=3, ge=1, le=10)
    ocr_confidence_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    max_file_size_mb: int = Field(default=100, ge=1, le=1000)


class MCPSettings(BaseSettings):
    """MCP server configuration."""

    host: str = "0.0.0.0"
    port: int = Field(default=3000, ge=1024, le=65535)
    transport: Literal["http", "websocket"] = "http"


class Settings(BaseSettings):
    """Main configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="KNOWLEDGE_",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    storage: StorageSettings = Field(default_factory=StorageSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)

    @classmethod
    def load_from_yaml(cls, config_path: Path | None = None) -> "Settings":
        """Load configuration from YAML file with environment variable overrides."""
        if config_path is None:
            # Try to find config.yaml in current directory or use default
            if Path("config.yaml").exists():
                config_path = Path("config.yaml")
            else:
                config_path = Path(__file__).parent / "default_config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        # Environment variables will override YAML values automatically
        return cls(**config_data)

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        self.storage.documents_path.mkdir(parents=True, exist_ok=True)
        self.storage.vector_db_path.mkdir(parents=True, exist_ok=True)
        self.storage.model_cache_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.load_from_yaml()
        _settings.ensure_directories()
    return _settings


def reload_settings(config_path: Path | None = None) -> Settings:
    """Reload settings from configuration file."""
    global _settings
    _settings = Settings.load_from_yaml(config_path)
    _settings.ensure_directories()
    return _settings
