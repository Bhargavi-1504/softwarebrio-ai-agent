from app.extractor import (
    build_llm_context,
    clean_html,
    extract_emails,
    extract_headings,
    extract_linkedin_urls,
    extract_page,
    truncate_text,
)


def test_clean_html():
    html = """
    <html>
        <head>
            <style>
                .test { color: red; }
            </style>
        </head>

        <body>

            <nav>
                Navigation
            </nav>

            <h1>Example Company</h1>

            <p>
                We build software for developers.
            </p>

            <script>
                alert("hello")
            </script>

            <svg>
                fake svg content
            </svg>

            <footer>
                Footer content
            </footer>

        </body>
    </html>
    """

    result = clean_html(html)

    assert "Example Company" in result
    assert "developers" in result

    assert "alert" not in result
    assert "Navigation" not in result
    assert "Footer content" not in result


def test_extract_emails():
    text = """
    Contact us at hello@example.com.
    Sales: sales@example.com.
    HELLO@example.com
    """

    emails = extract_emails(text)

    assert "hello@example.com" in emails
    assert "sales@example.com" in emails

    # Duplicate email should be removed.
    assert emails.count("hello@example.com") == 1


def test_extract_linkedin_urls():
    html = """
    <a href="https://www.linkedin.com/in/john-doe">
        John Doe
    </a>

    <a href="https://www.linkedin.com/company/example">
        Example
    </a>
    """

    urls = extract_linkedin_urls(html)

    assert len(urls) == 2

    assert any(
        "linkedin.com/in/john-doe" in url
        for url in urls
    )

    assert any(
        "linkedin.com/company/example" in url
        for url in urls
    )


def test_extract_headings():
    html = """
    <h1>Example Company</h1>
    <h2>Our Product</h2>
    <h2>Our Product</h2>
    <h3>For Developers</h3>
    """

    headings = extract_headings(html)

    assert "Example Company" in headings
    assert "Our Product" in headings
    assert "For Developers" in headings

    # Duplicate heading should only occur once.
    assert headings.count("Our Product") == 1


def test_truncate_text():
    text = "word " * 10_000

    result = truncate_text(
        text,
        max_characters=1_000,
    )

    assert len(result) > 0
    assert len(result) <= 1_100


def test_extract_page():
    html = """
    <html>
        <head>
            <title>Example Company</title>

            <meta
                name="description"
                content="Example company description"
            >
        </head>

        <body>
            <h1>Example Company</h1>

            <h2>Our Product</h2>

            <p>
                We build software for developers.
            </p>

            <p>
                Contact hello@example.com.
            </p>

            <a href="https://www.linkedin.com/in/john-doe">
                John
            </a>
        </body>
    </html>
    """

    page = extract_page(
        "https://example.com/about",
        html,
    )

    assert page.title == "Example Company"

    assert (
        page.description
        == "Example company description"
    )

    assert "Example Company" in page.text

    assert (
        "hello@example.com"
        in page.emails
    )

    assert len(page.linkedin_urls) == 1

    assert page.word_count > 0
    assert page.character_count > 0


def test_build_llm_context():
    html = """
    <title>Example Company</title>

    <meta
        name="description"
        content="Software company"
    >

    <h1>Example Company</h1>

    <p>
        We build tools for developers.
    </p>

    <p>
        Contact hello@example.com.
    </p>
    """

    page = extract_page(
        "https://example.com",
        html,
    )

    context = build_llm_context(page)

    assert "PAGE TITLE:" in context
    assert "HEADINGS:" in context
    assert "EMAILS:" in context
    assert "PAGE CONTENT:" in context
    assert "hello@example.com" in context