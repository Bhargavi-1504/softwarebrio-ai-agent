import asyncio

from app.browser import BrowserCrawler
from app.extractor import (
    build_llm_context,
    extract_page,
)


async def main():
    crawler = BrowserCrawler(max_pages=5)

    await crawler.start()

    try:
        result = await crawler.crawl("postman.com")

        print("\n" + "=" * 70)
        print("CONTENT EXTRACTION TEST")
        print("=" * 70)

        all_pages = []

        if result.homepage and result.homepage.success:
            all_pages.append(result.homepage)

        all_pages.extend(result.pages)

        for page_result in all_pages:

            print("\n" + "-" * 70)

            print(
                f"URL: {page_result.url}"
            )

            extracted = extract_page(
                page_result.url,
                page_result.html,
            )

            print(
                f"Title: {extracted.title}"
            )

            print(
                f"Words: {extracted.word_count}"
            )

            print(
                f"Characters: "
                f"{extracted.character_count}"
            )

            print(
                f"Emails: "
                f"{extracted.emails}"
            )

            print(
                f"LinkedIn URLs: "
                f"{extracted.linkedin_urls}"
            )

            print(
                f"Headings: "
                f"{extracted.headings[:10]}"
            )

            context = build_llm_context(
                extracted
            )

            print(
                "\nLLM CONTEXT PREVIEW:"
            )

            print(
                context[:2_000]
            )

            print(
                "\nContext characters:",
                len(context),
            )

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())