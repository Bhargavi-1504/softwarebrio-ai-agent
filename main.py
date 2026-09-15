from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from app.agent import LeadEnrichmentAgent
from app.utils import save_json


DEFAULT_DOMAINS = [
    "postman.com",
    "supabase.com",
    "vapi.ai",
]


async def run(domains: list[str]) -> None:

    agent = LeadEnrichmentAgent(
        max_pages=6,
        max_context_characters=20_000,
    )

    results = []

    try:

        await agent.start()

        total = len(domains)

        for index, domain in enumerate(
            domains,
            start=1,
        ):

            print(
                f"\n[{index}/{total}] "
                f"Starting {domain}"
            )

            try:

                result = (
                    await agent.process_domain(
                        domain
                    )
                )

                results.append(
                    {
                        "company": (
                            result.intelligence
                            .model_dump(
                                mode="json"
                            )
                        ),
                        "llm_usage": (
                            result.llm_metadata
                        ),
                    }
                )

            except Exception as exc:

                # Absolute protection at company level.
                # One company must never stop the complete run.

                print(
                    f"\n  ✗ Unexpected failure "
                    f"for {domain}: "
                    f"{type(exc).__name__}: {exc}"
                )

                results.append(
                    {
                        "company": {
                            "domain": domain,
                            "company_overview": (
                                "Processing failed."
                            ),
                            "target_audience": (
                                "Not available."
                            ),
                            "contact_points": [],
                            "leadership": [],
                            "data_confidence_score": 0.0,
                            "pages_visited": [],
                            "errors": [
                                (
                                    f"Unexpected error: "
                                    f"{type(exc).__name__}: "
                                    f"{exc}"
                                )
                            ],
                        },
                        "llm_usage": {},
                    }
                )

    finally:

        await agent.close()

    output = {
        "run_summary": {
            "total_domains": len(domains),
            "successful_results": sum(
                1
                for item in results
                if item["company"][
                    "data_confidence_score"
                ]
                > 0
            ),
            "failed_results": sum(
                1
                for item in results
                if item["company"][
                    "data_confidence_score"
                ]
                == 0
            ),
        },
        "results": results,
    }

    output_path = Path(
        "output/output.json"
    )

    save_json(
        output,
        output_path,
    )

    print("\n" + "=" * 70)
    print("RUN COMPLETE")
    print("=" * 70)

    print(
        f"Output saved to: "
        f"{output_path}"
    )

    print(
        f"Companies processed: "
        f"{len(results)}"
    )


def parse_args() -> list[str]:

    parser = argparse.ArgumentParser(
        description=(
            "Autonomous Lead Enrichment Agent"
        )
    )

    parser.add_argument(
        "domains",
        nargs="*",
        help=(
            "Company domains to process. "
            "Defaults to the three assignment domains."
        ),
    )

    args = parser.parse_args()

    if args.domains:
        return args.domains

    return DEFAULT_DOMAINS


if __name__ == "__main__":

    domains = parse_args()

    asyncio.run(
        run(domains)
    )