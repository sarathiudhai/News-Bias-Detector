"""
Article ingestion module.
Primary: newspaper4k for URL scraping.
Fallback: BeautifulSoup4 + requests.
Also accepts raw text paste.
"""

import re
import requests
from bs4 import BeautifulSoup


class ScrapingError(Exception):
    """Raised when article extraction fails from a URL."""
    pass


def _clean_text(text: str) -> str:
    """
    Strip ads, nav text, author bios, and normalize whitespace.
    """
    if not text:
        return ""

    # Remove common ad/nav patterns
    patterns = [
        r"(?i)advertisement\s*",
        r"(?i)sponsored\s+content",
        r"(?i)click\s+here\s+to\s+subscribe",
        r"(?i)sign\s+up\s+for\s+our\s+newsletter",
        r"(?i)follow\s+us\s+on\s+(twitter|facebook|instagram)",
        r"(?i)share\s+this\s+article",
        r"(?i)related\s+articles?:?",
        r"(?i)read\s+more:?",
        r"(?i)copyright\s+©?\s*\d{4}",
        r"(?i)all\s+rights\s+reserved",
        r"(?i)terms\s+of\s+(use|service)",
        r"(?i)privacy\s+policy",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text)

    # Normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()

    return text


def scrape_from_url(url: str) -> dict:
    """
    Extract article title and body text from a URL.
    Uses newspaper4k as primary, BeautifulSoup4 as fallback.

    Returns:
        {"title": str, "text": str}

    Raises:
        ScrapingError: If extraction fails from both methods.
    """
    # Primary: newspaper4k
    try:
        from newspaper import Article

        article = Article(url)
        article.download()
        article.parse()

        if article.text and len(article.text.strip()) > 100:
            return {
                "title": article.title or "Untitled",
                "text": _clean_text(article.text),
            }
    except Exception:
        pass  # Fall through to BeautifulSoup

    # Fallback: BeautifulSoup4
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove script, style, nav, footer, aside elements
        for tag in soup(["script", "style", "nav", "footer", "aside", "header", "form"]):
            tag.decompose()

        # Try to find the main article body
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # Look for article body in common containers
        article_body = (
            soup.find("article")
            or soup.find("div", class_=re.compile(r"(article|story|content|post)-?(body|text|content)?", re.I))
            or soup.find("main")
        )

        if article_body:
            paragraphs = article_body.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        text = "\n\n".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)

        if text and len(text.strip()) > 100:
            return {
                "title": title,
                "text": _clean_text(text),
            }

        raise ScrapingError("Could not extract sufficient article text from the page.")

    except requests.RequestException as e:
        raise ScrapingError(f"Failed to fetch URL: {str(e)}")
    except ScrapingError:
        raise
    except Exception as e:
        raise ScrapingError(f"Failed to parse article: {str(e)}")


def parse_input(text: str = None, url: str = None) -> dict:
    """
    Unified entry point for article ingestion.
    Accepts either raw text or a URL.

    Returns:
        {"title": str, "text": str, "url": str | None}
    """
    if url:
        result = scrape_from_url(url)
        result["url"] = url
        return result
    elif text:
        # For raw text paste, try to extract title from first line
        lines = text.strip().split("\n")
        title = "Untitled"
        body = text

        if len(lines) > 1 and len(lines[0]) < 200:
            title = lines[0].strip()
            body = "\n".join(lines[1:]).strip()

        return {
            "title": title,
            "text": _clean_text(body),
            "url": None,
        }
    else:
        raise ScrapingError("Please provide either article text or a URL.")
