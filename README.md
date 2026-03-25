# agent_ai

A Python-based simulation of a software development pipeline using AI agents. Each agent represents a role in the team — PM, PO, Analyst, Developer, and Tester — and they work sequentially to turn a customer request into documented, coded, and tested output.

## Requirements

- Python 3.10+
- Google Gemini API key

## Installation

```bash
pip install google-genai python-dotenv
```

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your-api-key
MODEL_NAME=gemini-2.5-flash-lite
BASE_PROJECT_PATH=projects
COMPANY_VAULT_PATH=company_vault
```

## Usage

Create an `input.txt` file:

```
project_name: My_Project
customer_wish: Describe the customer's request here.
```

Run the pipeline:

```bash
python main.py
```

You will be prompted to enter the path to your input file. Press Enter to use the default `input.txt`, or type a custom path.

## Project Structure

```
agentic_sdlc/
├── agents/                  # Prompt files for each agent
├── company_vault/           # Past projects and coding standards
│   └── previous_projects/
├── core/
│   ├── agent.py             # Gemini API wrapper
│   └── io_manager.py        # File operations
├── projects/                # Pipeline outputs
├── config.py
├── main.py
└── input.txt
```

## Output

All outputs are saved under `projects/<project_name>/`:

- `demand.txt` — customer requirements analysis
- `tasks/001_project_tasks.json` — task list with full comment history
- `codes/` — generated Python files per task
- `tests/` — test reports

## Notes

- Add past project `.txt` files to `company_vault/previous_projects/` to give agents more context.
- The pipeline includes automatic retry and short delays between requests to handle API rate limits.
- Never commit your `.env` file.
