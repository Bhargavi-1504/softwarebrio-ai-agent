from __future__ import annotations

import json
import time

from groq import Groq

from app.config import settings
from app.schemas import (
    CompanyIntelligence,
    LLMExtraction,
)


MODEL_NAME = "openai/gpt-oss-20b"

# Groq pricing for openai/gpt-oss-20b
# Prices are USD per 1 million tokens.
INPUT_COST_PER_1M = 0.075
OUTPUT_COST_PER_1M = 0.30


class LLMExtractionError(Exception):
    """Raised when structured LLM extraction fails."""


class CompanyLLM:
    """
    Groq-powered structured extraction client.

    The model receives cleaned website content rather than
    raw HTML.
    """

    def __init__(
        self,
        model: str = MODEL_NAME,
        max_retries: int = 3,
    ) -> None:

        if not settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is not configured. "
                "Add it to your .env file."
            )

        self.client = Groq(
            api_key=settings.groq_api_key
        )

        self.model = model
        self.max_retries = max_retries

    @staticmethod
    def _json_schema() -> dict:
        """
        JSON Schema used for Groq Structured Outputs.
        """

        return {
            "type": "object",

            "properties": {
                "company_overview": {
                    "type": "string"
                },

                "target_audience": {
                    "type": "string"
                },

                "contact_points": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },

                "leadership": {
                    "type": "array",
                    "items": {
                        "type": "object",

                        "properties": {
                            "name": {
                                "type": "string"
                            },
                            "role": {
                                "type": "string"
                            },
                            "linkedin_url": {
                                "type": [
                                    "string",
                                    "null"
                                ]
                            }
                        },

                        "required": [
                            "name",
                            "role",
                            "linkedin_url"
                        ],

                        "additionalProperties": False
                    }
                },

                "data_confidence_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0
                }
            },

            "required": [
                "company_overview",
                "target_audience",
                "contact_points",
                "leadership",
                "data_confidence_score"
            ],

            "additionalProperties": False
        }

    @staticmethod
    def _system_prompt() -> str:
        return """
You are a company intelligence extraction system.

Your job is to extract factual information from publicly
available website content.

STRICT RULES:

1. Use ONLY information present in the supplied content.
2. Never invent company facts.
3. Never invent people's names.
4. Never invent job titles.
5. Never invent LinkedIn URLs.
6. If information is missing, return an empty list.
7. Contact points must only contain email addresses
   supported by the supplied content.
8. Leadership members must be explicitly supported by
   the supplied content.
9. The company overview must be concise and approximately
   two sentences.
10. Target audience should describe who the company
    appears to build for.
11. Confidence must be a number between 0.0 and 1.0.

12. Calculate confidence based on the quality, completeness,
    and directness of the evidence in the supplied website content.

13. Do NOT reduce confidence heavily just because a field is
    legitimately unavailable on the public website.

14. Missing leadership information should only reduce confidence
    moderately when no leadership information is present in the
    supplied content.

15. Do NOT increase confidence simply because more pages were
    provided. Confidence must reflect the actual evidence supporting
    the extracted facts.

16. Use the following guidance:
    - 0.90-1.00: Strong direct evidence for nearly all requested fields.
    - 0.75-0.89: Good evidence for most fields, with one or two
      fields incomplete.
    - 0.50-0.74: Moderate evidence with several incomplete fields.
    - 0.25-0.49: Limited evidence or important fields unsupported.
    - 0.00-0.24: Very little usable evidence.

17. Never invent information to increase the confidence score.

Do not use outside knowledge.

Return only the requested structured output.
"""

    @staticmethod
    def _build_user_prompt(
        domain: str,
        context: str,
    ) -> str:

        return f"""
Extract company intelligence for:

DOMAIN:
{domain}

The following content was collected from the company's
public website and cleaned before being provided to you.

        IMPORTANT:

        - Do not assume facts that are not in this content.
        - LinkedIn URLs must come directly from the supplied content.
        - Do not manufacture contact emails.
        - Do not infer a person's identity from a LinkedIn URL alone.
        - Do not infer a person's job title.
        - Only add a leadership/team member when the supplied content
          explicitly associates a person's name with a role/title.
        - Include the LinkedIn URL only when that URL is explicitly
          associated with that person in the supplied content.
        - A company LinkedIn page is NOT a leadership profile.
        - If leadership names and roles cannot be established from the
          supplied content, return an empty leadership list.
        - If no public emails are available, return [].

WEBSITE CONTENT:
{context}
"""

    @staticmethod
    def _calculate_usage(response) -> dict:
        """
        Extract token usage and estimate API cost from the provider response.
        """

        usage = getattr(
            response,
            "usage",
            None
        )

        if usage is None:
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
            }

        prompt_tokens = getattr(
            usage,
            "prompt_tokens",
            0
        )

        completion_tokens = getattr(
            usage,
            "completion_tokens",
            0
        )

        total_tokens = getattr(
            usage,
            "total_tokens",
            prompt_tokens + completion_tokens
        )

        input_cost = (
            prompt_tokens / 1_000_000
        ) * INPUT_COST_PER_1M

        output_cost = (
            completion_tokens / 1_000_000
        ) * OUTPUT_COST_PER_1M

        estimated_cost = (
            input_cost + output_cost
        )

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": round(
                estimated_cost,
                8
            
            ),
        }

    def extract(
        self,
        domain: str,
        context: str,
        pages_visited: list[str],
        errors: list[str],
    ) -> tuple[CompanyIntelligence, dict]:

        if not context.strip():
            raise LLMExtractionError(
                "Cannot perform extraction because "
                "the LLM context is empty."
            )

        system_prompt = self._system_prompt()

        user_prompt = self._build_user_prompt(
            domain,
            context
        )

        last_error: Exception | None = None

        for attempt in range(
            1,
            self.max_retries + 1
        ):

            try:

                print(
                    f"  → LLM extraction "
                    f"(attempt {attempt}/{self.max_retries})"
                )

                start_time = time.perf_counter()

                response = (
                    self.client.chat.completions.create(
                        model=self.model,

                        messages=[
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                            }
                        ],

                        response_format={
                            "type": "json_schema",
                            "json_schema": {
                                "name": "company_intelligence",
                                "strict": True,
                                "schema": self._json_schema()
                            }
                        },

                        temperature=0,

                        max_completion_tokens=1500
                    )
                )

                elapsed = (
                    time.perf_counter()
                    - start_time
                )

                content = (
                    response
                    .choices[0]
                    .message
                    .content
                )

                if not content:
                    raise LLMExtractionError(
                        "LLM returned empty content."
                    )

                raw_data = json.loads(content)

                extracted = (
                    LLMExtraction.model_validate(
                        raw_data
                    )
                )

                usage = self._calculate_usage(
                    response
                )

                metadata = {
                    "model": self.model,
                    "latency_seconds": round(
                        elapsed,
                        3
                    ),
                    **usage
                }

                final_result = CompanyIntelligence(
                    domain=domain,

                    company_overview=(
                        extracted.company_overview
                    ),

                    target_audience=(
                        extracted.target_audience
                    ),

                    contact_points=(
                        extracted.contact_points
                    ),

                    leadership=(
                        extracted.leadership
                    ),

                    data_confidence_score=(
                        extracted.data_confidence_score
                    ),

                    pages_visited=pages_visited,

                    errors=errors
                )

                print(
                    "  ✓ Structured LLM extraction complete"
                )

                return (
                    final_result,
                    metadata
                )

            except Exception as exc:

                last_error = exc

                error_text = str(exc).lower()

                is_request_too_large = (
                    "request too large" in error_text
                    or "tokens per minute" in error_text
                    or "413" in error_text
                    or "rate_limit_exceeded" in error_text
                )

                print(
                    f"  ⚠ LLM attempt {attempt} failed: "
                    f"{type(exc).__name__}: {exc}"
                )

                if attempt < self.max_retries:

                    if is_request_too_large:

                        print(
                            "  → Request too large; "
                            "reducing context before retry."
                        )

                        # Keep the beginning of the context and reduce it
                        # substantially for the next attempt.
                        context = context[:15_000]

                        user_prompt = self._build_user_prompt(
                            domain,
                            context
                        )

                        continue

                    wait_seconds = 2 ** (
                        attempt - 1
                    )

                    print(
                        f"  → Retrying in "
                        f"{wait_seconds}s..."
                    )

                    time.sleep(
                        wait_seconds
                    )

        raise LLMExtractionError(
            "LLM extraction failed after "
            f"{self.max_retries} attempts: "
            f"{last_error}"
        )