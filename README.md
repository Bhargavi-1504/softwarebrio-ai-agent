# SoftwareBrio AI Agent

An AI-powered company intelligence agent that crawls public company websites, extracts relevant business information, and uses an LLM to generate structured company intelligence.

The pipeline is designed for automated lead research and prospecting by combining web crawling, content extraction, LLM-based structured extraction, confidence scoring, error handling, and API usage tracking.

---

## Features

- Automated website crawling using Playwright
- Discovers relevant internal company pages
- Extracts and cleans website content before sending it to the LLM
- Extracts company overview
- Identifies target audience / Ideal Customer Profile
- Extracts publicly available contact email addresses
- Extracts leadership and team information when explicitly available
- Extracts LinkedIn profile URLs when explicitly associated with people
- Uses structured LLM output with JSON schema validation
- Confidence scoring based on evidence quality
- Retry handling for LLM failures and rate limits
- Context reduction for request-too-large errors
- Continues processing even if one company fails
- Tracks LLM token usage
- Tracks LLM latency
- Estimates API cost per domain
- Saves structured results to JSON
- Includes automated pytest tests

---

## Extracted Information

For every processed company, the pipeline extracts:

- Company overview
- Target audience / Ideal Customer Profile
- Public contact email addresses
- Leadership / team members
- Leadership roles
- LinkedIn URLs when explicitly available
- Data confidence score
- Pages visited
- Errors encountered during processing
- LLM model
- Prompt token usage
- Completion token usage
- Total token usage
- LLM latency
- Estimated API cost

---

## Architecture

```text
                    ┌──────────────────────┐
                    │      User Input      │
                    │  Company Domain(s)   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       Main.py        │
                    │  Pipeline Controller │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Browser         │
                    │     Playwright       │
                    │                      │
                    │ • Open website       │
                    │ • Discover URLs      │
                    │ • Visit pages        │
                    │ • Collect content    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │     Extractor        │
                    │                      │
                    │ • Clean HTML         │
                    │ • Remove JS/CSS      │
                    │ • Extract emails     │
                    │ • Extract LinkedIn   │
                    │ • Prepare context    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       CompanyLLM     │
                    │                      │
                    │    Groq API + LLM    │
                    │ openai/gpt-oss-20b   │
                    │                      │
                    │ • Structured output  │
                    │ • Retry handling     │
                    │ • Token tracking     │
                    │ • Cost estimation   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Pydantic        │
                    │       Schemas        │
                    │                      │
                    │ • Validate output    │
                    │ • Enforce structure │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      output.json     │
                    │                      │
                    │ Structured company   │
                    │ intelligence data   │
                    └──────────────────────┘
```

---

## Technologies Used

- Python 3.12
- Playwright
- Groq API
- `openai/gpt-oss-20b`
- Pydantic
- pytest
- python-dotenv

---

## Project Structure

```text
softwarebrio-ai-agent/
│
├── app/
│   ├── __init__.py
│   ├── agent.py
│   ├── browser.py
│   ├── config.py
│   ├── extractor.py
│   ├── llm.py
│   ├── schemas.py
│   └── utils.py
│
├── tests/
│   ├── __init__.py
│   ├── test_browser.py
│   ├── test_extractor.py
│   ├── test_llm_schema.py
│   └── test_schemas.py
│
├── output/
│   ├── .gitkeep
│   └── output.json
│
├── main.py
├── run_llm_check.py
├── test_browser_run.py
├── test_extraction_run.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd softwarebrio-ai-agent
```

### 2. Create a virtual environment

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browser

```bash
playwright install chromium
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Do not commit the `.env` file to GitHub.

---

## Running the Agent

### Run the default assignment domains

```bash
python main.py
```

The default test domains are:

```text
postman.com
supabase.com
vapi.ai
```

### Run a specific domain

```bash
python main.py supabase.com
```

### Run multiple custom domains

```bash
python main.py example.com anothercompany.com
```

---

## Output

The generated result is written to:

```text
output/output.json
```

Example structure:

```json
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
```

---

## Token Optimization

The pipeline does not send raw HTML directly to the LLM.

Before extraction, website content is processed to remove unnecessary information such as:

- JavaScript
- CSS
- SVG elements
- Navigation boilerplate
- Other irrelevant DOM content

Only cleaned textual content from relevant pages is provided to the LLM.

This reduces unnecessary token usage and helps improve extraction latency.

---

## Structured LLM Extraction

The LLM output is constrained using a structured JSON schema.

The extraction schema contains:

```text
company_overview
target_audience
contact_points
leadership
data_confidence_score
```

Leadership entries contain:

```text
name
role
linkedin_url
```

The implementation validates the generated structured data before producing the final company result.

The system also enforces strict extraction rules to prevent hallucination. Information is only extracted when supported by the supplied website content.

---

## Resilience and Error Handling

The pipeline is designed to continue processing even when individual pages or companies encounter problems.

Examples of handled conditions include:

- HTTP errors
- Missing pages
- Navigation failures
- Page timeouts
- Missing website elements
- LLM API failures
- Request-too-large errors
- Rate limits

LLM extraction uses retry logic with progressively reduced context when the request exceeds the available token limit.

A failure for one company does not stop processing of the remaining domains.

---

## Confidence Scoring

The extraction process generates a confidence score between `0.0` and `1.0`.

The score considers:

- Quality of the collected evidence
- Completeness of the extracted fields
- Directness of the supporting website content

The LLM is instructed not to invent information simply to increase the confidence score.

Missing information is not automatically treated as a major failure. For example, if leadership information is not publicly available in the collected content, the system can still assign a reasonable confidence score when the other company information is strongly supported.

Example:

```json
"data_confidence_score": 0.90
```

---

## Cost Tracking

The pipeline records:

- Prompt tokens
- Completion tokens
- Total tokens
- LLM latency
- Estimated API cost

Example:

```json
"llm_usage": {
  "model": "openai/gpt-oss-20b",
  "latency_seconds": 3.945,
  "prompt_tokens": 5014,
  "completion_tokens": 603,
  "total_tokens": 5617,
  "estimated_cost_usd": 0.00055695
}
```

The estimated cost is calculated from the recorded token usage and the configured model pricing.

---

## Testing

Run the complete automated test suite:

```bash
pytest
```

The test suite covers:

- Browser functionality
- Content extraction
- LLM schema validation
- Company schema validation

Final test result:

```text
16 passed
```

---

## Assignment Test Run

The agent was tested against the three assignment domains:

```text
postman.com
supabase.com
vapi.ai
```

All three domains completed successfully in the final test run.

```text
Companies processed: 3
```

The resulting structured data is available in:

```text
output/output.json
```

---

## Example Execution

Running:

```bash
python main.py
```

produces output similar to:

```text
[1/3] Starting postman.com

======================================================================
PROCESSING: postman.com
======================================================================
  → Opening https://postman.com/
  ✓ Homepage loaded (HTTP 200)
  ✓ Discovered relevant internal URLs
  ✓ Collected relevant pages

  → Preprocessing collected pages...
  ✓ Preprocessed pages
  ✓ Found public email(s)
  ✓ Found LinkedIn URL(s)
  ✓ LLM context prepared

  → LLM extraction (attempt 1/3)
  ✓ Structured LLM extraction complete
  ✓ Evidence confidence: 1.00
  ✓ Final confidence: 0.90
```

The same pipeline is applied to the remaining domains.

---

## Security

API credentials are loaded through environment variables.

Never commit:

```text
.env
```

or any API key to the repository.

The repository should contain:

```text
.env.example
```

with placeholder values only.

The `.gitignore` file excludes sensitive and unnecessary local files such as:

```text
.venv/
.env
__pycache__/
*.pyc
.pytest_cache/
.vscode/
```

---

## Manual Operations Confirmation

I am comfortable spending approximately 40% of my working hours on manual lead prospecting, email discovery, and account handling alongside my AI engineering responsibilities.

I understand that the internship combines manual prospecting and operational execution with AI agent engineering, and I am comfortable with this hybrid work structure.

---

## Future Improvements

Potential future improvements include:

- Better leadership page discovery
- More advanced relevance scoring for internal URLs
- Parallel page crawling
- Additional LLM providers
- More comprehensive unit and integration tests
- Persistent crawl caching
- Improved cost reporting across multiple domains
- More advanced evidence-based confidence scoring
- Support for additional structured company intelligence fields

---

## Author

**Bhargavi Vanipenta**

LinkedIn: https://www.linkedin.com/in/bhargavi-vanipenta-9a9717271

