import asyncio

from app.browser import BrowserCrawler


async def main():
    crawler = BrowserCrawler(max_pages=5)

    await crawler.start()

    try:
        result = await crawler.crawl("postman.com")

        print("\n" + "=" * 60)
        print("CRAWL RESULT")
        print("=" * 60)

        print(f"Domain: {result.domain}")

        if result.homepage:
            print(
                f"Homepage success: {result.homepage.success}"
            )
            print(
                f"Homepage status: {result.homepage.status_code}"
            )
            print(
                f"Homepage title: {result.homepage.title}"
            )

        print("\n" + "-" * 60)
        print("DISCOVERED INTERNAL URLS")
        print("-" * 60)

        if result.discovered_urls:
            for index, url in enumerate(
                result.discovered_urls,
                start=1,
            ):
                print(f"{index}. {url}")
        else:
            print("No relevant internal URLs discovered.")

        print("\n" + "-" * 60)
        print("COLLECTED PAGES")
        print("-" * 60)

        if result.pages:
            for index, page in enumerate(
                result.pages,
                start=1,
            ):
                print(
                    f"{index}. {page.url} "
                    f"| HTTP {page.status_code} "
                    f"| title={page.title!r}"
                )
        else:
            print("No additional pages collected.")

        print("\n" + "-" * 60)
        print("ERRORS")
        print("-" * 60)

        if result.errors:
            for error in result.errors:
                print(f"- {error}")
        else:
            print("No errors.")

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        print(
            f"Discovered URLs: "
            f"{len(result.discovered_urls)}"
        )

        print(
            f"Successfully collected pages: "
            f"{len(result.pages)}"
        )

        print(
            f"Errors: "
            f"{len(result.errors)}"
        )

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())