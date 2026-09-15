from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from app.browser import (
    BrowserCrawler,
    CrawlResult,
)
from app.extractor import (
    ExtractedPage,
    build_llm_context,
    extract_page,
)
from app.llm import (
    CompanyLLM,
    LLMExtractionError,
)
from app.schemas import CompanyIntelligence
from app.utils import calculate_evidence_confidence


@dataclass
class AgentRunResult:
    """Complete result of processing one company."""

    intelligence: CompanyIntelligence

    llm_metadata: dict = field(
        default_factory=dict
    )

    extracted_pages: list[ExtractedPage] = field(
        default_factory=list
    )


class LeadEnrichmentAgent:
    """
    End-to-end autonomous lead enrichment agent.

    Pipeline:

        Domain
          ↓
        Playwright
          ↓
        Relevant pages
          ↓
        Content preprocessing
          ↓
        Deterministic extraction
          ↓
        LLM structured extraction
          ↓
        Pydantic validation
          ↓
        Evidence-based confidence
    """

    def __init__(
        self,
        max_pages: int = 6,
        max_context_characters: int = 20_000,
    ) -> None:

        self.max_pages = max_pages
        self.max_context_characters = (
            max_context_characters
        )

        self.crawler = BrowserCrawler(
            max_pages=max_pages
        )

        self.llm = CompanyLLM()

    async def start(self) -> None:
        """Start browser resources."""

        await self.crawler.start()

    async def close(self) -> None:
        """Close browser resources."""

        await self.crawler.close()

    @staticmethod
    def _successful_pages(
        crawl_result: CrawlResult,
    ) -> list:
        """Return all successfully collected pages."""

        pages = []

        if (
            crawl_result.homepage
            and crawl_result.homepage.success
        ):
            pages.append(
                crawl_result.homepage
            )

        pages.extend(
            crawl_result.pages
        )

        return pages

    def _extract_pages(
        self,
        crawl_result: CrawlResult,
    ) -> list[ExtractedPage]:
        """Run content preprocessing on all successful pages."""

        extracted_pages = []

        for page_result in self._successful_pages(
            crawl_result
        ):

            try:

                extracted = extract_page(
                    url=page_result.url,
                    html=page_result.html,
                    max_characters=7_000,
                )

                extracted_pages.append(
                    extracted
                )

            except Exception as exc:

                print(
                    f"  ⚠ Content extraction failed "
                    f"for {page_result.url}: "
                    f"{type(exc).__name__}: {exc}"
                )

        return extracted_pages

    @staticmethod
    def _build_combined_context(
        pages: list[ExtractedPage],
        max_characters: int,
    ) -> str:
        """
        Combine cleaned page contexts while enforcing an overall
        context limit.
        """

        sections = []

        current_length = 0

        for page_number, page in enumerate(
            pages,
            start=1,
        ):

            page_context = build_llm_context(
                page
            )

            section = (
                f"===== PAGE {page_number} =====\n"
                f"URL: {page.url}\n\n"
                f"{page_context}"
            )

            remaining = (
                max_characters
                - current_length
            )

            if remaining <= 0:
                break

            if len(section) > remaining:

                section = section[
                    :remaining
                ]

                section += (
                    "\n\n"
                    "[Overall context limit reached.]"
                )

            sections.append(section)

            current_length += len(section)

        return "\n\n".join(sections)

    @staticmethod
    def _collect_emails(
        pages: list[ExtractedPage],
    ) -> list[str]:
        """Collect unique emails across all pages."""

        emails = set()

        for page in pages:
            emails.update(
                page.emails
            )

        return sorted(emails)

    @staticmethod
    def _collect_linkedin_urls(
        pages: list[ExtractedPage],
    ) -> list[str]:
        """Collect unique LinkedIn URLs across all pages."""

        urls = set()

        for page in pages:
            urls.update(
                page.linkedin_urls
            )

        return sorted(urls)

    @staticmethod
    def _visited_urls(
        pages: list[ExtractedPage],
    ) -> list[str]:
        """Return successfully processed page URLs."""

        return [
            page.url
            for page in pages
        ]

    async def process_domain(
        self,
        domain: str,
    ) -> AgentRunResult:

        print("\n" + "=" * 70)
        print(
            f"PROCESSING: {domain}"
        )
        print("=" * 70)

        # ---------------------------------------------------------
        # STEP 1 — Browser crawling
        # ---------------------------------------------------------

        try:

            crawl_result = await self.crawler.crawl(
                domain
            )

        except Exception as exc:

            print(
                f"  ✗ Unexpected crawler failure: "
                f"{type(exc).__name__}: {exc}"
            )

            intelligence = CompanyIntelligence(
                domain=domain,
                company_overview=(
                    "Unable to retrieve company "
                    "website content."
                ),
                target_audience=(
                    "Not available because website "
                    "retrieval failed."
                ),
                contact_points=[],
                leadership=[],
                data_confidence_score=0.0,
                pages_visited=[],
                errors=[
                    (
                        f"Crawler failure: "
                        f"{type(exc).__name__}: {exc}"
                    )
                ],
            )

            return AgentRunResult(
                intelligence=intelligence
            )

        # ---------------------------------------------------------
        # STEP 2 — Content preprocessing
        # ---------------------------------------------------------

        print(
            "\n  → Preprocessing collected pages..."
        )

        extracted_pages = (
            self._extract_pages(
                crawl_result
            )
        )

        print(
            f"  ✓ Preprocessed "
            f"{len(extracted_pages)} pages"
        )

        if not extracted_pages:

            errors = list(
                crawl_result.errors
            )

            errors.append(
                "No usable page content was extracted."
            )

            intelligence = CompanyIntelligence(
                domain=domain,
                company_overview=(
                    "No usable company information "
                    "could be extracted."
                ),
                target_audience=(
                    "Not available."
                ),
                contact_points=[],
                leadership=[],
                data_confidence_score=0.0,
                pages_visited=[],
                errors=errors,
            )

            return AgentRunResult(
                intelligence=intelligence
            )

        # ---------------------------------------------------------
        # STEP 3 — Deterministic extraction
        # ---------------------------------------------------------

        emails = self._collect_emails(
            extracted_pages
        )

        linkedin_urls = (
            self._collect_linkedin_urls(
                extracted_pages
            )
        )

        visited_urls = self._visited_urls(
            extracted_pages
        )

        print(
            f"  ✓ Found {len(emails)} "
            f"public email(s)"
        )

        print(
            f"  ✓ Found {len(linkedin_urls)} "
            f"LinkedIn URL(s)"
        )

        # ---------------------------------------------------------
        # STEP 4 — Build optimized LLM context
        # ---------------------------------------------------------

        context = self._build_combined_context(
            extracted_pages,
            self.max_context_characters,
        )

        print(
            f"  ✓ LLM context prepared: "
            f"{len(context):,} characters"
        )

        # ---------------------------------------------------------
        # STEP 5 — LLM structured extraction
        # ---------------------------------------------------------

        try:

            # The Groq Python client is synchronous, so run it
            # in a worker thread to avoid blocking the async
            # browser event loop.
            intelligence, metadata = (
                await asyncio.to_thread(
                    self.llm.extract,
                    domain,
                    context,
                    visited_urls,
                    crawl_result.errors,
                )
            )

        except LLMExtractionError as exc:

            print(
                f"  ✗ LLM extraction failed: {exc}"
            )

            intelligence = CompanyIntelligence(
                domain=domain,
                company_overview=(
                    "LLM extraction was unsuccessful."
                ),
                target_audience=(
                    "Not available."
                ),
                contact_points=emails,
                leadership=[],
                data_confidence_score=0.0,
                pages_visited=visited_urls,
                errors=(
                    list(crawl_result.errors)
                    + [
                        f"LLM extraction error: {exc}"
                    ]
                ),
            )

            return AgentRunResult(
                intelligence=intelligence,
                extracted_pages=extracted_pages,
            )

        # ---------------------------------------------------------
        # STEP 6 — Evidence-based confidence
        # ---------------------------------------------------------

        evidence_confidence = (
            calculate_evidence_confidence(
                company_overview=(
                    intelligence.company_overview
                ),
                target_audience=(
                    intelligence.target_audience
                ),
                contact_points=emails,
                leadership=intelligence.leadership,
                linkedin_urls=linkedin_urls,
                pages_visited=visited_urls,
                errors=crawl_result.errors,
            )
        )

        # Combine LLM confidence and evidence confidence.
        final_confidence = round(
            (
                intelligence.data_confidence_score
                + evidence_confidence
            )
            / 2,
            2,
        )

        intelligence = intelligence.model_copy(
            update={
                "contact_points": emails,
                "pages_visited": visited_urls,
                "errors": crawl_result.errors,
                "data_confidence_score": (
                    final_confidence
                ),
            }
        )

        print(
            f"  ✓ Evidence confidence: "
            f"{evidence_confidence:.2f}"
        )

        print(
            f"  ✓ Final confidence: "
            f"{final_confidence:.2f}"
        )

        return AgentRunResult(
            intelligence=intelligence,
            llm_metadata=metadata,
            extracted_pages=extracted_pages,
        )