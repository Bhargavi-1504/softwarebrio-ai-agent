from app.schemas import CompanyIntelligence, LeadershipMember


def test_valid_company_intelligence():
    result = CompanyIntelligence(
        domain="example.com",
        company_overview="Example is a technology company. It builds software products.",
        target_audience="Software developers",
        contact_points=["hello@example.com"],
        leadership=[
            LeadershipMember(
                name="John Doe",
                role="CEO",
                linkedin_url="https://www.linkedin.com/in/johndoe",
            )
        ],
        data_confidence_score=0.9,
        pages_visited=["https://example.com/"],
        errors=[],
    )

    assert result.domain == "example.com"
    assert result.data_confidence_score == 0.9


def test_confidence_score_bounds():
    try:
        CompanyIntelligence(
            domain="example.com",
            company_overview="Test",
            target_audience="Developers",
            data_confidence_score=1.5,
        )
        assert False, "Expected validation error"
    except Exception:
        assert True