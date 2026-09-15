from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def calculate_evidence_confidence(
    *,
    company_overview: str,
    target_audience: str,
    contact_points: list[str],
    leadership: list[Any],
    linkedin_urls: list[str],
    pages_visited: list[str],
    errors: list[str],
) -> float:
    """
    Calculate an application-level confidence score based on
    the amount of evidence successfully collected.

    This prevents the confidence score from relying entirely
    on the LLM's subjective estimate.
    """

    score = 0.0

    if company_overview.strip():
        score += 0.20

    if target_audience.strip():
        score += 0.20

    if contact_points:
        score += 0.15

    if leadership:
        score += 0.20

    if linkedin_urls:
        score += 0.10

    if len(pages_visited) >= 2:
        score += 0.10
    elif len(pages_visited) == 1:
        score += 0.05

    if not errors:
        score += 0.05

    return round(
        min(score, 1.0),
        2,
    )


def save_json(
    data: Any,
    output_path: str | Path,
) -> None:
    """Save Python data as formatted JSON."""

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def format_domain(domain: str) -> str:
    """Normalize a domain for display."""

    domain = domain.strip()

    domain = domain.replace(
        "https://",
        "",
    )

    domain = domain.replace(
        "http://",
        "",
    )

    domain = domain.rstrip("/")

    if domain.startswith("www."):
        domain = domain[4:]

    return domain