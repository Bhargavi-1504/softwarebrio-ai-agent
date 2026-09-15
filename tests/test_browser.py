from app.browser import BrowserCrawler


def test_normalize_domain():
    assert (
        BrowserCrawler.normalize_domain(
            "https://www.postman.com/"
        )
        == "postman.com"
    )


def test_homepage_url():
    assert (
        BrowserCrawler.homepage_url("postman.com")
        == "https://postman.com/"
    )


def test_internal_url():
    assert BrowserCrawler.is_internal_url(
        "https://postman.com/about",
        "postman.com",
    )

    assert not BrowserCrawler.is_internal_url(
        "https://linkedin.com/company/postman",
        "postman.com",
    )


def test_ignore_url():
    assert BrowserCrawler.should_ignore_url(
        "https://example.com/login"
    )

    assert BrowserCrawler.should_ignore_url(
        "https://example.com/file.pdf"
    )

    assert not BrowserCrawler.should_ignore_url(
        "https://example.com/about"
    )


def test_score_url():
    assert BrowserCrawler.score_url(
        "https://example.com/about"
    ) > BrowserCrawler.score_url(
        "https://example.com/random-page"
    )