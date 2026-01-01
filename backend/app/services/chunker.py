"""
Text chunking service for RAG.

Splits text into overlapping chunks suitable for embedding generation.
Implements sentence-aware splitting to avoid breaking mid-sentence.
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Chunking parameters
CHUNK_SIZE = 500  # Target tokens per chunk (approx)
CHUNK_OVERLAP = 50  # Overlap between chunks (approx tokens)
CHARS_PER_TOKEN = 4  # Rough estimate: 1 token ≈ 4 characters


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Uses simple heuristic: ~4 characters per token.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // CHARS_PER_TOKEN


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.

    Uses regex to identify sentence boundaries while handling common
    abbreviations and edge cases.

    Args:
        text: Text to split

    Returns:
        List of sentences
    """
    # Pattern matches sentence endings: . ! ? followed by space/newline/end
    # Negative lookbehind for common abbreviations
    sentence_pattern = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s+'

    sentences = re.split(sentence_pattern, text)

    # Filter out empty sentences and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    return sentences


def create_chunks(text: str) -> List[dict]:
    """
    Split text into overlapping chunks.

    Creates chunks of approximately CHUNK_SIZE tokens with CHUNK_OVERLAP
    overlap. Respects sentence boundaries to avoid breaking mid-sentence.

    Args:
        text: Text to chunk

    Returns:
        List of chunk dictionaries with keys:
            - text: Chunk text content
            - index: Chunk index (0-based)
            - token_count: Estimated token count
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for chunking")
        return []

    # Split into sentences
    sentences = split_into_sentences(text)

    if not sentences:
        logger.warning("No sentences found in text")
        return []

    logger.info(f"Split text into {len(sentences)} sentences")

    chunks = []
    current_chunk = []
    current_tokens = 0

    # Target sizes in characters
    target_chunk_chars = CHUNK_SIZE * CHARS_PER_TOKEN
    overlap_chars = CHUNK_OVERLAP * CHARS_PER_TOKEN

    for i, sentence in enumerate(sentences):
        sentence_tokens = estimate_tokens(sentence)

        # If single sentence exceeds chunk size, split it anyway
        if sentence_tokens > CHUNK_SIZE and not current_chunk:
            logger.warning(
                f"Sentence {i} is very long ({sentence_tokens} tokens), "
                f"will create oversized chunk"
            )
            chunks.append({
                "text": sentence,
                "index": len(chunks),
                "token_count": sentence_tokens,
            })
            continue

        # Check if adding this sentence would exceed chunk size
        if current_tokens + sentence_tokens > CHUNK_SIZE and current_chunk:
            # Save current chunk
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "index": len(chunks),
                "token_count": estimate_tokens(chunk_text),
            })

            # Start new chunk with overlap
            # Keep last few sentences for overlap
            overlap_text = ""
            overlap_tokens = 0

            for prev_sentence in reversed(current_chunk):
                sentence_tokens_overlap = estimate_tokens(prev_sentence)
                if overlap_tokens + sentence_tokens_overlap <= CHUNK_OVERLAP:
                    overlap_text = prev_sentence + " " + overlap_text
                    overlap_tokens += sentence_tokens_overlap
                else:
                    break

            # Start new chunk with overlap sentences
            if overlap_text:
                current_chunk = [s for s in current_chunk if s in overlap_text]
                current_tokens = overlap_tokens
            else:
                current_chunk = []
                current_tokens = 0

        # Add sentence to current chunk
        current_chunk.append(sentence)
        current_tokens += sentence_tokens

    # Add final chunk if it has content
    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "text": chunk_text,
            "index": len(chunks),
            "token_count": estimate_tokens(chunk_text),
        })

    logger.info(
        f"Created {len(chunks)} chunks "
        f"(avg {sum(c['token_count'] for c in chunks) / len(chunks):.0f} tokens/chunk)"
    )

    return chunks


def chunk_text(text: str, source: str = "") -> List[dict]:
    """
    High-level function to chunk text with metadata.

    Args:
        text: Text to chunk
        source: Source identifier (URL or description)

    Returns:
        List of chunk dictionaries with metadata
    """
    logger.info(f"Chunking text from source: {source or 'direct input'}")

    chunks = create_chunks(text)

    # Add source metadata
    for chunk in chunks:
        chunk["source"] = source

    logger.info(f"Chunking complete: {len(chunks)} chunks created")

    return chunks
