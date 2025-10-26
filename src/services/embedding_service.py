"""
Embedding service with model loading and caching.
"""

from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings with caching."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: str = "cpu",
        cache_folder: Path | None = None,
    ):
        """
        Initialize embedding service.

        Args:
            model_name: HuggingFace model name
            device: Device to use (cpu or cuda)
            cache_folder: Optional cache folder for model
        """
        self.model_name = model_name
        self.device = device
        self.cache_folder = str(cache_folder) if cache_folder else None
        self._model: SentenceTransformer | None = None

        logger.info(f"Embedding service initialized with model: {model_name}")

    def _load_model(self) -> SentenceTransformer:
        """Load the embedding model (lazy loading)."""
        if self._model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_folder,
            )
            logger.info(f"Model loaded successfully on device: {self.device}")
        return self._model

    async def encode(
        self,
        texts: list[str],
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar

        Returns:
            List of embedding vectors
        """
        model = self._load_model()

        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress,
            convert_to_tensor=False,
            normalize_embeddings=True,  # For cosine similarity
        )

        # Convert to list of lists
        if isinstance(embeddings, torch.Tensor):
            embeddings = embeddings.cpu().tolist()
        else:
            embeddings = embeddings.tolist()

        logger.debug(f"Generated {len(embeddings)} embeddings")
        return embeddings

    async def encode_single(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text string to embed

        Returns:
            Embedding vector
        """
        embeddings = await self.encode([text], batch_size=1)
        return embeddings[0]

    @property
    def dimension(self) -> int:
        """Get the embedding dimension."""
        model = self._load_model()
        return model.get_sentence_embedding_dimension()
