# Python Static Code Analyzer

A small Python static analyzer and linter built with the `ast` module. It provides a command-line interface for checking Python files and a Flask web interface for analyzing pasted code.

## Features

- Parses Python source and reports syntax errors.
- Detects calls to `eval()` and `exec()`.
- Warns about empty `except` blocks and unused local variables.
- Tracks symbols across function scopes, including nested functions.
- Displays results in the browser or exports them as JSON from the CLI.

## Requirements

- Python 3.9 or newer
- Dependencies listed in [`requirements.txt`](requirements.txt)

## Setup

Create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

## Web interface

Start the local Flask development server:

```bash
python app.py
```

Open <http://127.0.0.1:5000> in a browser, paste Python code, and select **Analyze Code**.

The `POST /api/lint` endpoint accepts JSON:

```json
{
  "code": "def example():\n    value = 1\n    return value"
}
```

It responds with a JSON object containing an `errors` array. Each diagnostic includes the file, line, column, severity level, and message.

## Command-line interface

Analyze a Python file:

```bash
python linter.py test_target.py
```

Export diagnostics to a JSON file:

```bash
python linter.py test_target.py --output report.json
```

The sample `test_target.py` intentionally includes code that triggers analyzer warnings and an `eval()` diagnostic.

## Project files

- `app.py` — Flask web interface and lint API.
- `linter.py` — AST-based analyzer and command-line interface.
- `test_target.py` — sample input for trying the analyzer.
- `requirements.txt` — Python package dependencies.

## Limitations

This is a small educational analyzer, not a replacement for a production linter or security review. Its scope and unused-variable checks are intentionally limited.
