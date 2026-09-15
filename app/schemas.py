from pydantic import BaseModel, Field, HttpUrl


class LeadershipMember(BaseModel):
    """A company leadership/team member."""

    name: str = Field(
        description="Full name of the team member"
    )

    role: str = Field(
        description="Job title or role"
    )

    linkedin_url: HttpUrl | None = Field(
        default=None,
        description="LinkedIn profile URL if found"
    )


class LLMExtraction(BaseModel):
    """
    Structured information extracted by the LLM.

    Website metadata such as domain and visited pages is
    added by our application rather than hallucinated by
    the model.
    """

    company_overview: str = Field(
        description=(
            "A concise two-sentence summary of what "
            "the company does"
        )
    )

    target_audience: str = Field(
        description=(
            "The company's ideal customer profile or "
            "primary target audience"
        )
    )

    contact_points: list[str] = Field(
        default_factory=list,
        description=(
            "Public generic/company email addresses "
            "found in the provided website content"
        )
    )

    leadership: list[LeadershipMember] = Field(
        default_factory=list,
        description=(
            "Important founders, executives, or team "
            "members explicitly supported by the content"
        )
    )

    data_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Estimated confidence in the completeness "
            "and reliability of the extracted information"
        )
    )


class CompanyIntelligence(BaseModel):
    """Final validated company intelligence."""

    domain: str

    company_overview: str

    target_audience: str

    contact_points: list[str] = Field(
        default_factory=list
    )

    leadership: list[LeadershipMember] = Field(
        default_factory=list
    )

    data_confidence_score: float = Field(
        ge=0.0,
        le=1.0
    )

    pages_visited: list[str] = Field(
        default_factory=list
    )

    errors: list[str] = Field(
        default_factory=list
    )