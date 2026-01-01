"""
Chat service with RAG (Retrieval-Augmented Generation).

Provides intelligent chatbot responses by:
1. Embedding user questions
2. Retrieving relevant context from Qdrant
3. Generating responses using OpenAI with context
"""

import logging
from typing import AsyncGenerator, List

from openai import AsyncOpenAI

from app.config import get_settings
from app.models import Bot, Message
from app.services.embeddings import generate_query_embedding
from app.services.qdrant_client import search_vectors

settings = get_settings()
logger = logging.getLogger(__name__)

# OpenAI client singleton (reuse from embeddings service)
_openai_client = None

# Chat configuration
CHAT_MODEL = "gpt-4o-mini"
MAX_CONTEXT_CHUNKS = 3  # Top N chunks to include in context
SIMILARITY_THRESHOLD = 0.6  # Minimum similarity score
MAX_CONVERSATION_HISTORY = 10  # Last N messages to include


def get_openai_client() -> AsyncOpenAI:
    """Get or create OpenAI client singleton."""
    global _openai_client

    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.info("OpenAI client initialized for chat")

    return _openai_client


def build_system_prompt(bot: Bot, context_chunks: List[dict]) -> str:
    """
    Build system prompt with bot context and retrieved knowledge.

    Args:
        bot: Bot configuration
        context_chunks: Retrieved chunks from Qdrant

    Returns:
        System prompt string
    """
    bot_name = bot.name or "Assistant"

    # Build context section from retrieved chunks
    context_text = ""
    if context_chunks:
        context_text = "Context from knowledge base:\n\n"
        for i, chunk in enumerate(context_chunks, 1):
            text = chunk["payload"].get("text", "")
            score = chunk.get("score", 0)
            context_text += f"[{i}] (relevance: {score:.2f})\n{text}\n\n"

    # Build system prompt
    prompt = f"""You are {bot_name}, a helpful customer support assistant.

{context_text}

Instructions:
- Answer the user's question using ONLY the context provided above
- Be helpful, concise, and friendly
- If the answer is not in the context, respond: "I don't have that information in my knowledge base. Please contact our support team for assistance."
- Do not make up information or use knowledge outside the provided context
- If multiple pieces of context are relevant, synthesize them into a coherent answer
"""

    return prompt


def build_messages(
    system_prompt: str,
    conversation_history: List[Message],
    current_question: str,
) -> List[dict]:
    """
    Build messages array for OpenAI chat completion.

    Args:
        system_prompt: System prompt with context
        conversation_history: Previous messages (last N)
        current_question: Current user question

    Returns:
        List of message dictionaries for OpenAI API
    """
    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history (last N messages)
    for msg in conversation_history[-MAX_CONVERSATION_HISTORY:]:
        messages.append({"role": msg.role, "content": msg.content})

    # Add current question
    messages.append({"role": "user", "content": current_question})

    return messages


async def retrieve_context(bot_id: str, question: str) -> List[dict]:
    """
    Retrieve relevant context chunks for a question.

    Args:
        bot_id: Bot UUID
        question: User question

    Returns:
        List of relevant chunks with scores and payloads
    """
    logger.info(f"Retrieving context for question: {question[:100]}...")

    # Generate embedding for question
    query_embedding = await generate_query_embedding(question)

    # Search Qdrant for similar chunks
    results = await search_vectors(
        bot_id=bot_id,
        query_embedding=query_embedding,
        limit=MAX_CONTEXT_CHUNKS,
        similarity_threshold=SIMILARITY_THRESHOLD,
    )

    if results:
        scores_str = ", ".join([f"{r['score']:.2f}" for r in results])
        logger.info(
            f"Retrieved {len(results)} chunks "
            f"(scores: {scores_str})"
        )
    else:
        logger.warning(f"No relevant context found for bot {bot_id}")

    return results


async def generate_response(
    bot: Bot,
    question: str,
    conversation_history: List[Message],
) -> AsyncGenerator[str, None]:
    """
    Generate streaming chat response using RAG.

    Args:
        bot: Bot configuration
        question: User question
        conversation_history: Previous messages in conversation

    Yields:
        Response tokens as they are generated
    """
    logger.info(f"Generating response for bot {bot.id} ({bot.name})")

    # Retrieve relevant context
    context_chunks = await retrieve_context(bot.id, question)

    # Build system prompt with context
    system_prompt = build_system_prompt(bot, context_chunks)

    # Build messages array
    messages = build_messages(system_prompt, conversation_history, question)

    logger.info(
        f"Calling OpenAI with {len(messages)} messages, "
        f"{len(context_chunks)} context chunks"
    )

    # Get OpenAI client
    client = get_openai_client()

    # Stream response from OpenAI
    try:
        stream = await client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=500,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

        logger.info(f"Response generation complete for bot {bot.id}")

    except Exception as e:
        logger.error(f"OpenAI streaming failed: {e}")
        yield f"I apologize, but I encountered an error: {str(e)}"
