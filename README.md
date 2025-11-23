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

**Important:** If an API key was ever committed, a history-rewrite was prepared and a backup of the pre-purge state was pushed to
`origin/backup-before-purge-20251123-175400`. Do **not** share keys — rotate/revoke any exposed keys in the Cloud Console.

## Streamlit UI (optional)

A small Streamlit prototype UI is included at `ui_streamlit.py` to chat with the local agent implementation. There are three recommended ways to run it on Windows:

- Recommended (easiest on Windows): use Conda/Miniconda and install Streamlit from `conda-forge` (prebuilt `pyarrow` wheels):

```powershell
# Install Miniconda/Miniforge if you don't have it, then:
conda create -n concierge python=3.10 -c conda-forge streamlit
conda activate concierge
cd 'C:\Users\Aditya\OneDrive\Desktop\Capstone\Concierge-Agents'
streamlit run ui_streamlit.py
```

- If you prefer the project's venv (pip): installing `streamlit` with pip on Windows may trigger a `pyarrow` source build which
	requires CMake + Visual Studio Build Tools. If you want to use the venv, install the native build tools first, then:

```powershell
.\.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.venv\Scripts\python.exe -m pip install streamlit
.venv\Scripts\python.exe -m streamlit run ui_streamlit.py
```

- Quick local test (uses system `streamlit` if installed):

```powershell
streamlit run ui_streamlit.py
```

Notes about the included UI
- The UI calls the same `handle_user_message` function in `agent.py` so it uses the same `.env` keys (`GOOGLE_API_KEY` and `MODEL_NAME`).
- If Streamlit isn't available in your project venv, the editor may show a missing-import diagnostic; this repo includes a temporary
	Pylance ignore on the `streamlit` import to avoid a distracting editor error while you install Streamlit in a chosen environment.
- A now-removed call to `st.experimental_rerun()` caused an AttributeError on some Streamlit versions; `ui_streamlit.py` was patched
	to be compatible across common Streamlit releases.

## Troubleshooting Streamlit install (pyarrow errors)

- If `pip install streamlit` fails building `pyarrow` with errors mentioning `cmake` or Visual Studio, prefer the Conda approach above.
- Alternatively install Visual Studio Build Tools (select C++ workload) and install CMake before retrying pip.

## Final notes

- Always keep secrets out of source control. Use `.env.template` to document required variables and instruct collaborators to create their own `.env` files.
- If you want, I can help create a small Dockerfile or a `requirements-conda.txt` to make reproducible installs on Windows.

## Troubleshooting quick checklist

- Activate the project's venv before running scripts.
- Verify `.env` contains `GOOGLE_API_KEY` and optional `MODEL_NAME`.
- If the model request fails, run `list_models_lowlevel.py` and set a supported `MODEL_NAME`.

If you'd like, I can also add a `requirements.txt` or make the README more detailed for contributors.

