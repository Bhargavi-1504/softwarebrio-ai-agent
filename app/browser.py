from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)


# Pages that are highly relevant for company intelligence.
PAGE_KEYWORDS = {
    "about": 10,
    "company": 10,
    "team": 10,
    "leadership": 10,
    "people": 9,
    "contact": 9,
    "pricing": 7,
    "product": 7,
    "products": 7,
    "solutions": 7,
    "customers": 6,
    "careers": 5,
}


# URLs that are generally not useful for company enrichment.
IGNORED_PATH_KEYWORDS = {
    "login",
    "signin",
    "sign-in",
    "signup",
    "sign-up",
    "register",
    "checkout",
    "cart",
    "privacy",
    "terms",
    "cookie",
}


@dataclass
class PageResult:
    """Result of crawling a single web page."""

    url: str
    success: bool
    status_code: int | None = None
    title: str = ""
    html: str = ""
    error: str | None = None


@dataclass
class CrawlResult:
    """Complete crawling result for one company domain."""

    domain: str
    homepage: PageResult | None = None
    pages: list[PageResult] = field(default_factory=list)
    discovered_urls: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BrowserCrawler:
    """
    Playwright-based crawler for discovering and collecting
    relevant public company pages.
    """

    def __init__(
        self,
        max_pages: int = 6,
        timeout_ms: int = 30_000,
    ) -> None:
        self.max_pages = max_pages
        self.timeout_ms = timeout_ms

        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def start(self) -> None:
        """Start Playwright and launch a Chromium browser."""

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=True
        )

        self.context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            viewport={
                "width": 1440,
                "height": 900,
            },
        )

    async def close(self) -> None:
        """Cleanly close browser resources."""

        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        self.context = None
        self.browser = None
        self.playwright = None

    @staticmethod
    def normalize_domain(domain: str) -> str:
        """
        Convert a domain or URL into a clean domain.

        Examples:
            postman.com
            https://postman.com/
            https://www.postman.com/about
        """

        domain = domain.strip()

        if not domain.startswith(("http://", "https://")):
            domain = f"https://{domain}"

        parsed = urlparse(domain)

        hostname = parsed.netloc.lower()

        if hostname.startswith("www."):
            hostname = hostname[4:]

        return hostname

    @staticmethod
    def homepage_url(domain: str) -> str:
        """Create the homepage URL for a domain."""

        return f"https://{BrowserCrawler.normalize_domain(domain)}/"

    @staticmethod
    def is_internal_url(url: str, domain: str) -> bool:
        """Return True if URL belongs to the target domain."""

        try:
            parsed = urlparse(url)

            hostname = parsed.netloc.lower()

            if hostname.startswith("www."):
                hostname = hostname[4:]

            target = BrowserCrawler.normalize_domain(domain)

            return hostname == target or hostname.endswith(
                f".{target}"
            )

        except Exception:
            return False

    @staticmethod
    def should_ignore_url(url: str) -> bool:
        """Filter URLs that are unlikely to contain useful data."""

        try:
            parsed = urlparse(url)

            path = parsed.path.lower()

            # Ignore non-web documents.
            ignored_extensions = (
                ".pdf",
                ".zip",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".svg",
                ".webp",
                ".mp4",
                ".mp3",
                ".doc",
                ".docx",
            )

            if path.endswith(ignored_extensions):
                return True

            path_parts = set(
                part for part in path.split("/") if part
            )

            if path_parts.intersection(IGNORED_PATH_KEYWORDS):
                return True

            return False

        except Exception:
            return True

    @staticmethod
    def score_url(url: str) -> int:
        """
        Score a URL according to how useful it is likely to be
        for company intelligence.
        """

        try:
            parsed = urlparse(url)

            path = parsed.path.lower()

            score = 0

            for keyword, points in PAGE_KEYWORDS.items():
                if keyword in path:
                    score += points

            # Root-level pages are slightly more useful than
            # deeply nested pages.
            depth = len(
                [part for part in path.split("/") if part]
            )

            if depth == 1:
                score += 2

            return score

        except Exception:
            return 0

    async def fetch_page(
        self,
        page: Page,
        url: str,
    ) -> PageResult:
        """
        Fetch a single page safely.

        Errors are returned as PageResult objects instead of
        crashing the complete crawler.
        """

        try:
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=self.timeout_ms,
            )

            # Give JavaScript-rendered content a short opportunity
            # to finish loading.
            try:
                await page.wait_for_load_state(
                    "networkidle",
                    timeout=5_000,
                )
            except Exception:
                # networkidle can legitimately never occur on sites
                # with continuous network activity.
                pass

            status_code = response.status if response else None

            title = await page.title()

            html = await page.content()

            if status_code is not None and status_code >= 400:
                return PageResult(
                    url=url,
                    success=False,
                    status_code=status_code,
                    title=title,
                    html=html,
                    error=f"HTTP {status_code}",
                )

            return PageResult(
                url=url,
                success=True,
                status_code=status_code,
                title=title,
                html=html,
            )

        except Exception as exc:
            return PageResult(
                url=url,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            )

    async def discover_links(
        self,
        page: Page,
        domain: str,
    ) -> list[str]:
        """
        Discover relevant internal links from the current page.
        """

        try:
            links = await page.locator("a[href]").evaluate_all(
                """
                elements => elements.map(
                    element => element.href
                )
                """
            )

        except Exception:
            return []

        discovered: set[str] = set()

        for link in links:
            if not link:
                continue

            # Remove URL fragments.
            clean_url = link.split("#")[0].rstrip("/")

            if not clean_url:
                continue

            if not clean_url.startswith(("http://", "https://")):
                continue

            if not self.is_internal_url(clean_url, domain):
                continue

            if self.should_ignore_url(clean_url):
                continue

            discovered.add(clean_url)

        return sorted(
            discovered,
            key=self.score_url,
            reverse=True,
        )

    async def crawl(self, domain: str) -> CrawlResult:
        """
        Crawl a company website and collect relevant pages.
        """

        domain = self.normalize_domain(domain)

        result = CrawlResult(domain=domain)

        if not self.context:
            raise RuntimeError(
                "BrowserCrawler has not been started. "
                "Call await crawler.start() first."
            )

        page = await self.context.new_page()

        try:
            homepage = self.homepage_url(domain)

            print(f"  → Opening {homepage}")

            homepage_result = await self.fetch_page(
                page,
                homepage,
            )

            result.homepage = homepage_result

            if not homepage_result.success:
                result.errors.append(
                    f"Homepage failed: "
                    f"{homepage_result.error}"
                )

                return result

            print(
                f"  ✓ Homepage loaded "
                f"(HTTP {homepage_result.status_code})"
            )

            # Discover internal links from homepage.
            discovered_urls = await self.discover_links(
                page,
                domain,
            )

            result.discovered_urls = discovered_urls

            print(
                f"  ✓ Discovered "
                f"{len(discovered_urls)} relevant internal URLs"
            )

            # Homepage counts as one processed page.
            remaining_pages = max(
                self.max_pages - 1,
                0,
            )

            selected_urls = discovered_urls[
                :remaining_pages
            ]

            for url in selected_urls:

                print(f"  → Visiting {url}")

                page_result = await self.fetch_page(
                    page,
                    url,
                )

                if page_result.success:
                    result.pages.append(page_result)

                    print(
                        f"  ✓ Collected "
                        f"{url}"
                    )

                else:
                    error_message = (
                        f"{url}: "
                        f"{page_result.error}"
                    )

                    result.errors.append(error_message)

                    print(
                        f"  ⚠ Skipped: "
                        f"{page_result.error}"
                    )

        except Exception as exc:
            # Absolute last-resort protection.
            result.errors.append(
                f"Crawler error: "
                f"{type(exc).__name__}: {exc}"
            )

        finally:
            await page.close()

        return result


async def crawl_domain(
    domain: str,
    max_pages: int = 6,
) -> CrawlResult:
    """
    Convenience function for crawling one domain.
    """

    crawler = BrowserCrawler(
        max_pages=max_pages
    )

    await crawler.start()

    try:
        return await crawler.crawl(domain)

    finally:
        await crawler.close()