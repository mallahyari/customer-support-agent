"""
Embeddings service for generating and storing vector embeddings.

Integrates with OpenAI API for text-embedding-3-small and stores
embeddings in Qdrant vector database.
"""

import logging
import uuid
from typing import List

from openai import AsyncOpenAI

from app.config import get_settings
from app.services.qdrant_client import upsert_vectors

settings = get_settings()
logger = logging.getLogger(__name__)

# OpenAI client singleton
_openai_client = None

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 100  # Max embeddings per API request


def get_openai_client() -> AsyncOpenAI:
    """
    Get or create OpenAI client singleton.

    Returns:
        AsyncOpenAI: Configured OpenAI client
    """
    global _openai_client

    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("OpenAI client initialized")

    return _openai_client


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of texts using OpenAI.

    Processes texts in batches to respect API limits.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (each 1536 dimensions)

    Raises:
        Exception: If OpenAI API call fails
    """
    if not texts:
        logger.warning("Empty text list provided for embedding")
        return []

    client = get_openai_client()
    all_embeddings = []

    # Process in batches
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info(
            f"Generating embeddings for batch {batch_num}/{total_batches} "
            f"({len(batch)} texts)"
        )

        try:
            response = await client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
            )

            # Extract embeddings in order
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            logger.info(
                f"Generated {len(batch_embeddings)} embeddings "
                f"(total: {len(all_embeddings)}/{len(texts)})"
            )

        except Exception as e:
            logger.error(f"Failed to generate embeddings for batch {batch_num}: {e}")
            raise

    logger.info(f"Successfully generated {len(all_embeddings)} embeddings")
    return all_embeddings


async def embed_and_store(
    bot_id: str,
    chunks: List[dict],
) -> int:
    """
    Generate embeddings for chunks and store in Qdrant.

    Args:
        bot_id: Bot UUID
        chunks: List of chunk dictionaries with 'text', 'index', 'source', etc.

    Returns:
        Number of vectors stored

    Raises:
        Exception: If embedding generation or storage fails
    """
    if not chunks:
        logger.warning("No chunks provided for embedding")
        return 0

    logger.info(f"Embedding and storing {len(chunks)} chunks for bot {bot_id}")

    # Extract texts for embedding
    texts = [chunk["text"] for chunk in chunks]

    # Generate embeddings
    embeddings = await generate_embeddings(texts)

    if len(embeddings) != len(chunks):
        raise ValueError(
            f"Embedding count mismatch: got {len(embeddings)}, expected {len(chunks)}"
        )

    # Prepare vectors for Qdrant
    vectors = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid.uuid4())

        payload = {
            "text": chunk["text"],
            "chunk_index": chunk.get("index", i),
            "source": chunk.get("source", ""),
            "token_count": chunk.get("token_count", 0),
        }

        vectors.append((point_id, embedding, payload))

    # Store in Qdrant
    await upsert_vectors(bot_id, vectors)

    logger.info(f"Successfully stored {len(vectors)} vectors for bot {bot_id}")

    return len(vectors)


async def generate_query_embedding(query: str) -> List[float]:
    """
    Generate embedding for a query string.

    Used for searching similar chunks during chat.

    Args:
        query: Query text

    Returns:
        Embedding vector (1536 dimensions)

    Raises:
        Exception: If OpenAI API call fails
    """
    logger.info(f"Generating query embedding: {query[:100]}...")

    client = get_openai_client()

    try:
        response = await client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[query],
        )

        embedding = response.data[0].embedding

        logger.info("Query embedding generated successfully")
        return embedding

    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        raise
