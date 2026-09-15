from app.llm import CompanyLLM


def test_llm_json_schema_structure():

    schema = CompanyLLM._json_schema()

    assert schema["type"] == "object"

    assert (
        "company_overview"
        in schema["properties"]
    )

    assert (
        "target_audience"
        in schema["properties"]
    )

    assert (
        "contact_points"
        in schema["properties"]
    )

    assert (
        "leadership"
        in schema["properties"]
    )

    assert (
        "data_confidence_score"
        in schema["properties"]
    )

    assert (
        schema["additionalProperties"]
        is False
    )


def test_llm_schema_requires_fields():

    schema = CompanyLLM._json_schema()

    required = set(
        schema["required"]
    )

    expected = {
        "company_overview",
        "target_audience",
        "contact_points",
        "leadership",
        "data_confidence_score",
    }

    assert required == expected