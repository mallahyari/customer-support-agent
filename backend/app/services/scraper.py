"""
Web scraping service for content ingestion.

Fetches and extracts clean text from web pages for embedding generation.
Implements security measures to prevent SSRF and resource abuse.
"""

import logging
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Security constants
MAX_CONTENT_LENGTH = 10_000_000  # 10MB max response size
REQUEST_TIMEOUT = 30  # seconds
MAX_WORDS = 10_000  # Limit extracted text to 10,000 words

# Blocked hosts/IPs to prevent SSRF
BLOCKED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",  # GCP metadata
}


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """
    Validate URL for security and format.

    Args:
        url: URL to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            return False, "Only HTTP and HTTPS URLs are supported"

        # Check hostname exists
        if not parsed.netloc:
            return False, "Invalid URL: missing hostname"

        # Check for blocked hosts (SSRF prevention)
        hostname = parsed.hostname
        if hostname and hostname.lower() in BLOCKED_HOSTS:
            return False, "Access to this host is not allowed"

        # Check for private IP ranges (basic check)
        if hostname:
            if hostname.startswith("10.") or hostname.startswith("192.168."):
                return False, "Access to private IP addresses is not allowed"
            if hostname.startswith("172."):
                # Check 172.16.0.0 - 172.31.255.255 range
                try:
                    second_octet = int(hostname.split(".")[1])
                    if 16 <= second_octet <= 31:
                        return False, "Access to private IP addresses is not allowed"
                except (ValueError, IndexError):
                    pass

        return True, None

    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


async def fetch_page(url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Fetch HTML content from URL with security measures.

    Args:
        url: URL to fetch

    Returns:
        Tuple of (html_content, error_message)
    """
    # Validate URL first
    is_valid, error = validate_url(url)
    if not is_valid:
        logger.warning(f"URL validation failed: {error} - {url}")
        return None, error

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=REQUEST_TIMEOUT,
            limits=httpx.Limits(max_connections=10),
        ) as client:
            # Add user agent to avoid being blocked
            headers = {
                "User-Agent": "Chirp AI Bot/1.0 (+https://github.com/yourusername/chirp-app)"
            }

            response = await client.get(url, headers=headers)

            # Check response status
            if response.status_code != 200:
                error_msg = f"HTTP {response.status_code}: {response.reason_phrase}"
                logger.warning(f"Failed to fetch {url}: {error_msg}")
                return None, error_msg

            # Check content length
            content_length = len(response.content)
            if content_length > MAX_CONTENT_LENGTH:
                error_msg = f"Response too large: {content_length} bytes (max {MAX_CONTENT_LENGTH})"
                logger.warning(f"Failed to fetch {url}: {error_msg}")
                return None, error_msg

            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                error_msg = f"Unsupported content type: {content_type}"
                logger.warning(f"Failed to fetch {url}: {error_msg}")
                return None, error_msg

            logger.info(f"Successfully fetched {url} ({content_length} bytes)")
            return response.text, None

    except httpx.TimeoutException:
        error_msg = f"Request timed out after {REQUEST_TIMEOUT} seconds"
        logger.warning(f"Failed to fetch {url}: {error_msg}")
        return None, error_msg

    except httpx.ConnectError as e:
        error_msg = f"Connection failed: {str(e)}"
        logger.warning(f"Failed to fetch {url}: {error_msg}")
        return None, error_msg

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Failed to fetch {url}: {error_msg}")
        return None, error_msg


def extract_text(html: str) -> str:
    """
    Extract clean text from HTML content.

    Removes scripts, styles, navigation, and other non-content elements.
    Limits output to MAX_WORDS to prevent resource abuse.

    Args:
        html: HTML content

    Returns:
        Cleaned text content
    """
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()

        # Get text
        text = soup.get_text(separator=" ", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = " ".join(lines)

        # Limit to MAX_WORDS
        words = text.split()
        if len(words) > MAX_WORDS:
            logger.info(f"Truncating text from {len(words)} to {MAX_WORDS} words")
            words = words[:MAX_WORDS]
            text = " ".join(words)

        logger.info(f"Extracted {len(words)} words from HTML")
        return text

    except Exception as e:
        logger.error(f"Failed to extract text from HTML: {e}")
        return ""


async def scrape_url(url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Scrape URL and extract clean text content.

    High-level function that combines fetching and text extraction.

    Args:
        url: URL to scrape

    Returns:
        Tuple of (text_content, error_message)
    """
    logger.info(f"Scraping URL: {url}")

    # Fetch page
    html, error = await fetch_page(url)
    if error:
        return None, error

    if not html:
        return None, "No content received"

    # Extract text
    text = extract_text(html)

    if not text:
        return None, "No text content could be extracted from page"

    logger.info(f"Successfully scraped {url}: {len(text)} characters")
    return text, None
