"""
Qdrant vector database client service.

Provides initialization and management of Qdrant collections for storing
and retrieving embeddings with bot-specific filtering.
"""

import logging
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global client instance
_qdrant_client: Optional[QdrantClient] = None

# Collection configuration
COLLECTION_NAME = "chirp_embeddings"
VECTOR_SIZE = 1536  # OpenAI text-embedding-3-small dimension
DISTANCE_METRIC = models.Distance.COSINE


def get_qdrant_client() -> QdrantClient:
    """
    Get or create Qdrant client singleton.

    Returns:
        QdrantClient: Configured Qdrant client instance

    Raises:
        ConnectionError: If unable to connect to Qdrant
    """
    global _qdrant_client

    if _qdrant_client is None:
        try:
            if settings.qdrant_url:
                # Server mode: connect to remote Qdrant instance
                logger.info(f"Connecting to Qdrant server at {settings.qdrant_url}")
                _qdrant_client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key,
                    timeout=30,
                )
            else:
                # Local mode: use persistent storage
                logger.info(f"Initializing local Qdrant at {settings.qdrant_path}")
                _qdrant_client = QdrantClient(path=settings.qdrant_path)

            logger.info("Qdrant client initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise ConnectionError(f"Unable to connect to Qdrant: {e}")

    return _qdrant_client


async def init_collection() -> None:
    """
    Initialize Qdrant collection for embeddings.

    Creates collection if it doesn't exist, with proper vector configuration
    and payload indexes for efficient bot_id filtering.

    Raises:
        Exception: If collection creation fails
    """
    client = get_qdrant_client()

    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_exists = any(col.name == COLLECTION_NAME for col in collections)

        if collection_exists:
            logger.info(f"Collection '{COLLECTION_NAME}' already exists")
            return

        # Create collection with vector configuration
        logger.info(f"Creating collection '{COLLECTION_NAME}'")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=DISTANCE_METRIC,
            ),
        )

        # Create payload index for bot_id filtering
        logger.info("Creating payload index for bot_id")
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="bot_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

        logger.info(f"Collection '{COLLECTION_NAME}' created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize collection: {e}")
        raise


async def health_check() -> dict:
    """
    Check Qdrant health and connectivity.

    Returns:
        dict: Health status information with keys:
            - healthy (bool): Overall health status
            - collections (int): Number of collections
            - mode (str): "local" or "server"
            - error (str, optional): Error message if unhealthy

    """
    try:
        client = get_qdrant_client()

        # Try to get collections as a basic health check
        collections = client.get_collections()

        mode = "server" if settings.qdrant_url else "local"

        return {
            "healthy": True,
            "collections": len(collections.collections),
            "mode": mode,
        }

    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e),
        }


async def upsert_vectors(
    bot_id: str,
    vectors: list[tuple[str, list[float], dict]],
) -> None:
    """
    Upsert vectors into Qdrant collection.

    Args:
        bot_id: Bot UUID for filtering
        vectors: List of tuples (point_id, embedding, payload)
            - point_id: Unique identifier for the vector (UUID string)
            - embedding: Vector embeddings (list of 1536 floats)
            - payload: Additional metadata (dict)

    Raises:
        Exception: If upsert operation fails
    """
    client = get_qdrant_client()

    try:
        # Prepare points for upsert
        points = []
        for point_id, embedding, payload in vectors:
            # Merge bot_id into payload
            full_payload = {"bot_id": bot_id, **payload}

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=full_payload,
                )
            )

        # Upsert points
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
        )

        logger.info(f"Upserted {len(points)} vectors for bot {bot_id}")

    except Exception as e:
        logger.error(f"Failed to upsert vectors: {e}")
        raise


async def search_vectors(
    bot_id: str,
    query_embedding: list[float],
    limit: int = 5,
    similarity_threshold: float = 0.7,
) -> list[dict]:
    """
    Search for similar vectors in Qdrant collection.

    Args:
        bot_id: Bot UUID to filter results
        query_embedding: Query vector (1536 floats)
        limit: Maximum number of results to return
        similarity_threshold: Minimum cosine similarity score (0.0-1.0)

    Returns:
        List of search results, each containing:
            - id: Point ID
            - score: Similarity score
            - payload: Associated metadata

    Raises:
        Exception: If search operation fails
    """
    client = get_qdrant_client()

    try:
        # Query points with bot_id filter
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="bot_id",
                        match=models.MatchValue(value=bot_id),
                    )
                ]
            ),
            limit=limit,
            score_threshold=similarity_threshold,
        )

        # Format results
        formatted_results = []
        for point in results.points:
            formatted_results.append(
                {
                    "id": point.id,
                    "score": point.score,
                    "payload": point.payload,
                }
            )

        logger.info(
            f"Found {len(formatted_results)} vectors for bot {bot_id} "
            f"(threshold={similarity_threshold})"
        )

        return formatted_results

    except Exception as e:
        logger.error(f"Failed to search vectors: {e}")
        raise


async def delete_vectors(bot_id: str) -> int:
    """
    Delete all vectors for a specific bot.

    Args:
        bot_id: Bot UUID

    Returns:
        Number of vectors deleted

    Raises:
        Exception: If delete operation fails
    """
    client = get_qdrant_client()

    try:
        # Delete all points with matching bot_id
        result = client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="bot_id",
                            match=models.MatchValue(value=bot_id),
                        )
                    ]
                )
            ),
        )

        logger.info(f"Deleted vectors for bot {bot_id}")

        # Return operation status (Qdrant returns status, not count)
        return 1 if result else 0

    except Exception as e:
        logger.error(f"Failed to delete vectors: {e}")
        raise


async def close_client() -> None:
    """
    Close Qdrant client connection.

    Called during application shutdown to cleanup resources.
    """
    global _qdrant_client

    if _qdrant_client is not None:
        try:
            _qdrant_client.close()
            logger.info("Qdrant client closed")
        except Exception as e:
            logger.error(f"Error closing Qdrant client: {e}")
        finally:
            _qdrant_client = None
