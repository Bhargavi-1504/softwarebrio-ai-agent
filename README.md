# Autonomous Lead Enrichment Agent

A Python-based autonomous web intelligence pipeline that crawls public company websites, extracts clean website content, and uses an LLM to generate structured company intelligence.

This project was developed as a practical take-home assignment for the **AI Engineer Intern** role at SoftwareBrio.

---

## Overview

The Autonomous Lead Enrichment Agent accepts one or more company domains as input and automatically:

1. Opens the company homepage using a headless browser.
2. Discovers relevant internal pages such as About, Company, Contact, Sales, Careers, Pricing, and similar pages.
3. Handles JavaScript-rendered website content using Playwright.
4. Collects the content from relevant pages.
5. Preprocesses the content to remove unnecessary HTML and navigation noise.
6. Extracts public emails and LinkedIn URLs.
7. Sends cleaned website content to an LLM.
8. Extracts structured company intelligence using a strict JSON schema.
9. Calculates an evidence-based confidence score.
10. Tracks LLM token usage, latency, and estimated API cost.
11. Handles failures and retries without stopping the complete pipeline.
12. Saves the final results to `output/output.json`.

---

## Features

- Automated website browsing using Playwright
- JavaScript-rendered content handling
- Homepage loading
- Relevant internal URL discovery
- Relevant subpage prioritization
- Multi-page content collection
- HTML/DOM preprocessing
- Removal of scripts, CSS, SVGs, and navigation boilerplate
- Public email extraction
- LinkedIn URL discovery
- LLM-powered company intelligence extraction
- Strict structured JSON output
- Pydantic schema validation
- Evidence-based confidence scoring
- Retry handling for LLM failures
- Request-too-large handling
- Rate-limit handling
- Graceful error handling
- Per-domain processing
- LLM token usage tracking
- LLM latency tracking
- Estimated API cost tracking
- Automated pytest test suite

---

## Architecture

```text
                    Company Domains
                           |
                           v
                +----------------------+
                |   Browser Crawler    |
                |      Playwright      |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Relevant URL         |
                | Discovery            |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Content Collection   |
                | Homepage + Subpages  |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Content Preprocessor |
                | Clean Text / DOM     |
                | Remove HTML Noise    |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | LLM Extraction       |
                | Groq API             |
                | GPT OSS 20B          |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Structured Validation|
                | Pydantic / JSON      |
                +----------+-----------+
                           |
                           v
                +----------------------+
                | Confidence + Usage   |
                | Token + Cost Tracking|
                +----------+-----------+
                           |
                           v
                +----------------------+
                | output/output.json   |
                +----------------------+

Extracted Information

For every processed company, the pipeline extracts:

Company overview
Target audience / Ideal Customer Profile
Public contact email addresses
Leadership / team members
Leadership roles
LinkedIn profile URLs when explicitly available
Data confidence score
Pages visited
Errors encountered during processing
LLM model
Prompt token usage
Completion token usage
Total token usage
LLM latency
Estimated API cost
Technologies Used
Python 3.12
Playwright
Groq API
openai/gpt-oss-20b
Pydantic
pytest
python-dotenv
Project Structure
softwarebrio-ai-agent/
│
├── app/
│   ├── __init__.py
│   ├── browser.py
│   ├── extractor.py
│   ├── llm.py
│   ├── schemas.py
│   └── config.py
│
├── tests/
│   ├── test_browser.py
│   ├── test_extractor.py
│   ├── test_llm_schema.py
│   └── test_schemas.py
│
├── output/
│   └── output.json
│
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
Setup
1. Clone the Repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd softwarebrio-ai-agent
2. Create a Virtual Environment

For Windows:

python -m venv .venv
.venv\Scripts\activate
3. Install Dependencies
pip install -r requirements.txt
4. Install Playwright Browser
playwright install chromium
5. Configure Environment Variables

Create a .env file in the project root:

GROQ_API_KEY=your_groq_api_key_here

The API key is loaded through environment variables.

Do not commit .env or any API key to GitHub.

Running the Agent
Run the Default Assignment Domains
python main.py

The default test domains are:

postman.com
supabase.com
vapi.ai
Run a Specific Domain
python main.py supabase.com
Run Multiple Custom Domains
python main.py example.com anothercompany.com
Output

The generated structured output is written to:

output/output.json

The output contains a summary of successful and failed domains along with structured company intelligence.

Example Output Structure
{
  "run_summary": {
    "total_domains": 3,
    "successful_results": 3,
    "failed_results": 0
  },
  "results": [
    {
      "company": {
        "domain": "example.com",
        "company_overview": "...",
        "target_audience": "...",
        "contact_points": [],
        "leadership": [],
        "data_confidence_score": 0.90,
        "pages_visited": [],
        "errors": []
      },
      "llm_usage": {
        "model": "openai/gpt-oss-20b",
        "latency_seconds": 3.2,
        "prompt_tokens": 5000,
        "completion_tokens": 600,
        "total_tokens": 5600,
        "estimated_cost_usd": 0.00055
      }
    }
  ]
}
Token Optimization

The pipeline does not send entire raw HTML pages directly to the LLM.

Before LLM processing, collected website content is cleaned and preprocessed.

The preprocessing stage removes unnecessary content such as:

JavaScript
CSS
SVG elements
Navigation boilerplate
Other irrelevant DOM content

Only relevant cleaned textual content is passed to the LLM.

This reduces unnecessary token usage and helps improve processing efficiency and latency.

Structured LLM Extraction

The LLM receives cleaned website content and extracts company intelligence using a strict structured JSON schema.

The extraction schema contains:

company_overview
target_audience
contact_points
leadership
data_confidence_score

Each leadership entry contains:

name
role
linkedin_url

The implementation validates the structured response before producing the final company result.

Extraction Rules

The LLM is instructed to:

Use only information present in the supplied website content.
Never invent company facts.
Never invent people's names.
Never invent job titles.
Never manufacture LinkedIn URLs.
Never manufacture contact emails.
Only include leadership members when a name and role are explicitly supported.
Include LinkedIn URLs only when explicitly associated with the corresponding person.
Return empty lists when information is unavailable.
Confidence Scoring

The pipeline produces a confidence score between 0.0 and 1.0.

The score considers:

Quality of collected evidence
Completeness of extracted information
Directness of the supporting website content

The system avoids artificially increasing confidence simply because more pages were collected.

Missing information is not treated as a reason to invent data.

Legitimately unavailable public information, such as leadership details, only reduces confidence moderately when other requested fields have strong supporting evidence.

Resilience and Error Handling

The pipeline is designed to continue processing even when individual pages or companies encounter problems.

Common conditions handled include:

HTTP errors
Missing pages
Navigation failures
Page timeouts
Missing website elements
LLM API failures
Request-too-large errors
Rate limits
LLM Retry Handling

LLM extraction uses retry logic.

When a request exceeds the available token limit, the pipeline reduces the LLM context before retrying.

This allows the system to recover from oversized requests while preserving the core extraction workflow.

A failure for one company does not stop processing of the remaining domains.

Cost Tracking

The pipeline tracks LLM usage for each processed domain.

The recorded metrics include:

Prompt tokens
Completion tokens
Total tokens
LLM latency
Estimated API cost
Example
"llm_usage": {
  "model": "openai/gpt-oss-20b",
  "latency_seconds": 3.945,
  "prompt_tokens": 5014,
  "completion_tokens": 603,
  "total_tokens": 5617,
  "estimated_cost_usd": 0.00055695
}

The estimated cost is calculated using the token usage and configured model pricing.

Testing

The project includes automated tests covering:

Browser functionality
Website content extraction
LLM structured schema validation
Company schema validation

Run the complete test suite with:

pytest
Final Test Result
16 passed
Assignment Test Run

The agent was tested against the three required domains:

postman.com
supabase.com
vapi.ai
Final Run

All three domains completed successfully.

[1/3] Starting postman.com
✓ Structured LLM extraction complete

[2/3] Starting supabase.com
✓ Structured LLM extraction complete

[3/3] Starting vapi.ai
✓ Structured LLM extraction complete

RUN COMPLETE
Output saved to: output\output.json
Companies processed: 3

The generated structured output is available at:

output/output.json
Sample Extraction Results

The final output contains structured company intelligence for all three assignment domains.

The pipeline records:

Company overview
Target audience
Public contact points
Leadership information when explicitly available
Confidence score
Pages visited
Errors
Token usage
Latency
Estimated API cost

The exact generated results are provided in:

output/output.json
Security

API credentials are loaded through environment variables.

The following files should never be committed:

.env
.venv/

The repository contains .env.example with placeholder configuration:

GROQ_API_KEY=your_groq_api_key_here

No API keys should be stored directly in the source code.

Manual Operations Confirmation

Yes. I am 100% comfortable spending roughly 40% of my working hours on manual lead prospecting, email discovery, and account handling alongside my AI engineering tasks.

I understand that the internship combines manual prospecting and operational execution with AI agent engineering, and I am comfortable with this hybrid work structure.

Author

Bhargavi Vanipenta

LinkedIn: <YOUR_LINKEDIN_URL>


### After pasting it

Only change these two things:

**1. GitHub placeholder**

```text
<https://github.com/Bhargavi-1504>

2. LinkedIn placeholder

<https://www.linkedin.com/in/bhargavi-vanipenta-9a9717271/>

Everything else can stay as above.

Then save:

Ctrl + S

and run:

pytest

You should still get:

16 passed