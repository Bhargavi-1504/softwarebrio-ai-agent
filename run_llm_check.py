from app.llm import CompanyLLM


def main():

    llm = CompanyLLM()

    context = """
    PAGE TITLE:
    Example Cloud

    META DESCRIPTION:
    Example Cloud provides cloud infrastructure
    for software development teams.

    HEADINGS:
    - Cloud Infrastructure
    - For Developers
    - Contact Us

    EMAILS:
    - hello@examplecloud.com
    - sales@examplecloud.com

    LINKEDIN URLS:
    - https://www.linkedin.com/in/jane-doe

    PAGE CONTENT:
    Example Cloud provides infrastructure tools
    for software developers and engineering teams.

    Jane Doe is the Chief Executive Officer.

    Contact our team at hello@examplecloud.com
    or sales@examplecloud.com.
    """

    result, metadata = llm.extract(
        domain="examplecloud.com",
        context=context,
        pages_visited=[
            "https://examplecloud.com/"
        ],
        errors=[],
    )

    print("\n")
    print("=" * 70)
    print("LLM RESULT")
    print("=" * 70)

    print(
        result.model_dump_json(
            indent=2
        )
    )

    print("\n")
    print("=" * 70)
    print("USAGE / METADATA")
    print("=" * 70)

    print(metadata)


if __name__ == "__main__":
    main()