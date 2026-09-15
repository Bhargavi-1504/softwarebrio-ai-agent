from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

LINKEDIN_PATTERN = re.compile(
    r"https?://(?:www\.)?linkedin\.com/"
    r"(?:in|company)/[A-Za-z0-9\-_%]+"
)


@dataclass
class ExtractedPage:
    """Clean information extracted from one webpage."""

    url: str
    title: str
    description: str
    text: str
    headings: list[str]
    emails: list[str]
    linkedin_urls: list[str]
    word_count: int
    character_count: int


def normalize_whitespace(text: str) -> str:
    """Normalize excessive whitespace."""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_html(html: str) -> str:
    """
    Convert raw HTML into clean text.

    Removes elements that generally don't provide useful
    company intelligence or unnecessarily increase LLM tokens.
    """

    soup = BeautifulSoup(html, "html.parser")

    # Remove technical/non-content elements.
    elements_to_remove = [
        "script",
        "style",
        "svg",
        "noscript",
        "iframe",
        "canvas",
        "template",
        "nav",
        "footer",
    ]

    for element in soup(elements_to_remove):
        element.decompose()

    # Remove common cookie/consent elements.
    for element in soup.find_all(
        attrs={
            "id": re.compile(
                r"cookie|consent|privacy",
                re.IGNORECASE,
            )
        }
    ):
        element.decompose()

    for element in soup.find_all(
        attrs={
            "class": re.compile(
                r"cookie|consent|privacy",
                re.IGNORECASE,
            )
        }
    ):
        element.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True,
    )

    return normalize_whitespace(text)


def extract_emails(text: str) -> list[str]:
    """Extract unique email addresses."""

    emails = EMAIL_PATTERN.findall(text)

    return sorted(
        {
            email.lower()
            for email in emails
        }
    )


def extract_linkedin_urls(html: str) -> list[str]:
    """Extract LinkedIn profile/company URLs."""

    urls = LINKEDIN_PATTERN.findall(html)

    normalized_urls = []

    for url in urls:
        url = url.rstrip("/")

        if url not in normalized_urls:
            normalized_urls.append(url)

    return sorted(normalized_urls)


def extract_title(html: str) -> str:
    """Extract webpage title."""

    soup = BeautifulSoup(html, "html.parser")

    if soup.title and soup.title.string:
        return normalize_whitespace(
            soup.title.string
        )

    return ""


def extract_description(html: str) -> str:
    """Extract meta description."""

    soup = BeautifulSoup(html, "html.parser")

    description = soup.find(
        "meta",
        attrs={"name": "description"},
    )

    if description:
        content = description.get("content", "")

        return normalize_whitespace(content)

    return ""


def extract_headings(
    html: str,
    max_headings: int = 30,
) -> list[str]:
    """Extract meaningful H1/H2/H3 headings."""

    soup = BeautifulSoup(html, "html.parser")

    headings = []

    for heading in soup.find_all(
        ["h1", "h2", "h3"]
    ):
        text = normalize_whitespace(
            heading.get_text(
                separator=" ",
                strip=True,
            )
        )

        if text and text not in headings:
            headings.append(text)

        if len(headings) >= max_headings:
            break

    return headings


def remove_duplicate_sentences(
    text: str,
) -> str:
    """
    Remove duplicate sentences/phrases that frequently occur
    because of repeated website components.
    """

    # Websites don't always use proper sentence punctuation,
    # so we use a conservative approach here.
    parts = re.split(
        r"(?<=[.!?])\s+",
        text,
    )

    seen = set()
    unique_parts = []

    for part in parts:
        normalized = normalize_whitespace(part)

        if not normalized:
            continue

        key = normalized.lower()

        if key in seen:
            continue

        seen.add(key)
        unique_parts.append(normalized)

    return " ".join(unique_parts)


def truncate_text(
    text: str,
    max_characters: int = 20_000,
) -> str:
    """
    Limit context size before sending it to an LLM.

    This protects against extremely large pages and helps
    control token usage.
    """

    if len(text) <= max_characters:
        return text

    truncated = text[:max_characters]

    # Avoid cutting halfway through a word.
    last_space = truncated.rfind(" ")

    if last_space > 0:
        truncated = truncated[:last_space]

    return (
        truncated
        + "\n\n[Content truncated for token efficiency.]"
    )


def build_llm_context(
    page: ExtractedPage,
) -> str:
    """
    Build a compact, structured context for the LLM.
    """

    sections = []

    if page.title:
        sections.append(
            f"PAGE TITLE:\n{page.title}"
        )

    if page.description:
        sections.append(
            f"META DESCRIPTION:\n"
            f"{page.description}"
        )

    if page.headings:
        sections.append(
            "HEADINGS:\n"
            + "\n".join(
                f"- {heading}"
                for heading in page.headings
            )
        )

    if page.emails:
        sections.append(
            "EMAILS:\n"
            + "\n".join(
                f"- {email}"
                for email in page.emails
            )
        )

    if page.linkedin_urls:
        sections.append(
            "LINKEDIN URLS:\n"
            + "\n".join(
                f"- {url}"
                for url in page.linkedin_urls
            )
        )

    if page.text:
        sections.append(
            f"PAGE CONTENT:\n{page.text}"
        )

    return "\n\n".join(sections)


def extract_page(
    url: str,
    html: str,
    max_characters: int = 20_000,
) -> ExtractedPage:
    """
    Run the complete preprocessing pipeline on a webpage.
    """

    title = extract_title(html)

    description = extract_description(html)

    text = clean_html(html)

    text = remove_duplicate_sentences(text)

    text = truncate_text(
        text,
        max_characters=max_characters,
    )

    headings = extract_headings(html)

    emails = extract_emails(text)

    # Extract LinkedIn URLs from HTML rather than cleaned text
    # because BeautifulSoup text extraction removes href values.
    linkedin_urls = extract_linkedin_urls(html)

    return ExtractedPage(
        url=url,
        title=title,
        description=description,
        text=text,
        headings=headings,
        emails=emails,
        linkedin_urls=linkedin_urls,
        word_count=len(text.split()),
        character_count=len(text),
    )