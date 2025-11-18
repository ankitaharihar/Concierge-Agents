# Concierge-Agents
Capstone

## Overview

`Concierge-Agents` is a small CLI Smart Study & Productivity Concierge Agent that helps
students manage tasks and generate short study plans. It uses Google's Generative AI
client to parse natural language commands and map them to task actions.

## Quick Setup

- Create and activate a Python virtual environment in the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

- Install dependencies:

```powershell
pip install -r requirements.txt
```

- Copy or create a `.env` file at the project root with the following keys:

```dotenv
GOOGLE_API_KEY=your_api_key_here
MODEL_NAME=models/gemini-2.5-pro   # optional; any supported model from the list_models script
```

## Running the app

Start the interactive CLI:

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

Type messages like:

- `I have a DBMS assignment due on 2025-11-25, it will take around 3 hours. Please add it.`
- `Show me all my tasks.`
- `I will study for 2 hours today, make a plan.`

The assistant will respond and may create/list/update tasks in the local storage.

## Model selection & troubleshooting

- If you see errors mentioning `models/... not found` or `unexpected model name format`, run the included
	script to list available models for your API key:

```powershell
python list_models_lowlevel.py
```

- Pick a model name from the output (it will look like `models/gemini-2.5-pro`) and set it in your `.env` as
	`MODEL_NAME=`.

- If Python raises `ModuleNotFoundError` for `google` imports, ensure your venv is activated and required
	packages are installed. You can install the main packages with:

```powershell
.\.venv\Scripts\python.exe -m pip install google-generativeai google-ai-generativelanguage google-api-core
```

## Development notes

- `agent.py` contains the LLM integration and maps model responses into JSON actions.
- `tools.py` implements `create_task`, `list_tasks`, `update_task_status`, and `generate_plan` used by the agent.
- `list_models_lowlevel.py` enumerates models available to your API key.

## Security

- Do not commit `.env` with secret API keys to public repositories. Keep the `.env` listed in `.gitignore`.

## Troubleshooting quick checklist

- Activate the project's venv before running scripts.
- Verify `.env` contains `GOOGLE_API_KEY` and optional `MODEL_NAME`.
- If the model request fails, run `list_models_lowlevel.py` and set a supported `MODEL_NAME`.

If you'd like, I can also add a `requirements.txt` or make the README more detailed for contributors.

