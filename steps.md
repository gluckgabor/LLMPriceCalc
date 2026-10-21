# Setup Guide: Running agent.py

## Overview

`agent.py` is a Playwright script that checks the
[Artificial Analysis LLM price calculator](https://artificialanalysis.ai/tools/llm-price-calculator).
It fills the "Calculate by tokens" form with fixed inputs, submits it, reads one model's row out of
the results table, and compares the scraped values against expected values hardcoded in the script.
It exits `0` when everything matches and `1` when anything does not, so it can be used as a CI check.

**No LLM is involved.** Earlier versions of this project drove the page with the `browser-use`
library and a Mistral model deciding each step. That was replaced with plain Playwright because the
task has fixed inputs and a known expected result: an LLM only added nondeterminism (runs took
22–83 seconds and filled the form correctly on one run in three), while the Playwright version
takes about 1.4 seconds and does the same thing every time. `MISTRAL_API_KEY` and the `.env` file
are no longer read by `agent.py`.

Note that "Mistral" still appears in the script as `TARGET_MODEL = "Mistral Large 4 Preview"` —
that is simply the row being priced on the website, not an API being called.

## Optional: VS Code Setup

For the best experience viewing and editing this guide in VS Code:

1. **Install Markdown Preview Enhanced Extension:**
   - Open VS Code
   - Go to Extensions view (Ctrl+Shift+X or Cmd+Shift+X)
   - Search for "Markdown Preview Enhanced"
   - Click Install

## Prerequisites

### 1. Python Runtime

- **Required**: Python 3.10 or higher (this project is running on 3.11.9)
- **Check**: `python --version`
- **Install**: Download from [python.org](https://www.python.org/downloads/)

### 2. Playwright and a Chromium Browser

Playwright needs both a Python package and a downloaded browser binary. Installing the package is
not enough on its own — the browser download is a separate command, covered in Step 3 below.
Chromium is roughly 120 MB and lands in `%LOCALAPPDATA%\ms-playwright` on Windows.

## Setup Steps

### Step 1: Create a Virtual Environment (recommended)

```bash
cd "C:/Users/Gluck Gabor/Mistral_projects/LLMPriceCalc"
python -m venv venv
```

**Activate it:**

- Windows (CMD): `venv\Scripts\activate`
- Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
- Windows (Git Bash): `source venv/Scripts/activate`
- macOS/Linux: `source venv/bin/activate`

### Step 2: Install the Python Package

```bash
pip install playwright
```

That is the only direct dependency. It pulls in `greenlet` and `pyee` automatically. The versions
currently installed here are `playwright==1.64.0`, `greenlet==3.5.6`, `pyee==13.0.1`.

### Step 3: Install the Chromium Browser

```bash
playwright install chromium
```

This is a required prerequisite, not an optional extra — without it the script fails on launch with
`Executable doesn't exist at ...`. Only Chromium is needed; `playwright install` with no argument
also downloads Firefox and WebKit, which this project does not use.

### Step 4: Review the Configuration

Everything configurable sits in constants near the top of `agent.py`. No `.env` file and no API key
are needed.

| Constant | Purpose |
|---|---|
| `HEADLESS` | `True` runs invisibly. Set to `False` to watch the browser work. |
| `TARGET_MODEL` | Which row to read from the results table. |
| `INPUT_TOKENS`, `RESPONSE_TOKENS`, `REASONING_TOKENS`, `API_CALLS` | The four values typed into the form. |
| `EXPECTED_TOTAL_COST`, `EXPECTED_COST_PER_CALL` | The expected result the scrape is checked against. |
| `RESULTS_TIMEOUT_MS` | How long to wait for the results table after clicking Calculate. |

**If you change any of the four input values, you must also update the two expected values**, or
the run will correctly fail. See "Updating the expected values" below.

### Step 5: Run It

```bash
python agent.py
```

## What the Script Does

1. Opens the calculator
2. Locates the "Calculate by tokens" form
3. – 6. Sets `Input tokens`, `Response tokens`, `Reasoning tokens` and `API calls`
7. Reads all four fields back and asserts they hold what was entered
8. Clicks "Calculate"
9. Waits for the `Mistral Large 4 Preview` row to appear
10. Reads the row and compares it against the expected values

Step 7 exists because the page **resets all four inputs to their defaults the moment Calculate is
clicked**, while the results table keeps showing the submitted run's figures. Before the click is
the only point at which the entered values can be verified.

## Output

Console output lists each step as PASS or FAIL, then the validations:

```
--- Validations ---
[PASS] Scrape produced a row: {...}
[PASS] Model name: expected 'Mistral Large 4 Preview', actual 'Mistral Large 4 Preview'
[PASS] Total cost: expected '$7.63', actual '$7.63'
[PASS] Cost per call: expected '$0.01', actual '$0.01'
[PASS] API calls: expected 1000, actual 1000
0 failed, 5 passed.  (1.4s)
```

A timestamped markdown report is written to `results/price_check_<timestamp>.md` with the inputs,
the expected values, the result, the validation table and the step table.

Exit codes: `0` = all validations passed, `1` = at least one failed.

## Updating the Expected Values

`EXPECTED_TOTAL_COST` and `EXPECTED_COST_PER_CALL` are the test's oracle. They were verified against
the live page on 2026-10-21. A failure on either means one of two things:

- **The scrape read the wrong row or the wrong inputs were submitted** — a real defect, investigate.
- **Artificial Analysis changed this model's pricing** — not a defect; open the calculator by hand,
  enter the same four inputs, and copy the row's new values into the two constants.

Reference figures measured on 2026-10-21 for `Mistral Large 4 Preview`:

| Inputs (input / response / reasoning / calls) | Cost per call | Total cost |
|---|---|---|
| 1000 / 500 / 1000 / 1000 (what the script uses) | $0.01 | $7.63 |
| 1000 / 3000 / 5000 / 1000 (the page's own defaults) | $0.03 | $34.80 |
| 1000 / 500 / 1000 / 10000 | $0.01 | $76.30 |

The middle row matters: if the script ever reports `$34.80`, the form was submitted before the
values were entered.

## Troubleshooting

**1. `Executable doesn't exist at ...chrome-headless-shell.exe`**
The browser binary was never downloaded. Run `playwright install chromium`. Installing the pip
package alone does not do this.

**2. `ModuleNotFoundError: No module named 'playwright'`**
The virtual environment is not active, or the package went into a different interpreter. Activate
the venv and re-run `pip install playwright`. To check which interpreter is in use:
`python -c "import sys; print(sys.executable)"`.

**3. `TimeoutError` waiting for the target row**
The results table did not render within `RESULTS_TIMEOUT_MS` (30 seconds). Usually a slow network
or a page change. Set `HEADLESS = False` and watch what happens; the step table in the report shows
exactly which step timed out.

**4. `expect(locator).to_have_count(1)` fails on the form**
The page's markup changed. The form is located as the one containing `input[name="reasoning"]`,
because the page has two "API calls" inputs — one per section. The element ids are React-generated
(for example `_r_14_-form-item`) and change between renders, so they are deliberately not used.

**5. Validations fail with `$34.80` instead of `$7.63`**
The form was submitted holding the page defaults. Check that step 7 passed in the report.

**6. The run passes but you want to see it happen**
Set `HEADLESS = False` in `agent.py`.

## Notes

- There is no `requirements.txt`; the single dependency and the browser download are the two
  commands in Steps 2 and 3, and they are repeated in the module docstring of `agent.py`.
- The first `playwright install chromium` takes a while — it downloads about 120 MB.
- A full run is about 1.4 seconds headless.
- `.env` is still present in the project directory but `agent.py` no longer reads it. It can be
  removed unless something else in the project uses it.
- On Linux, Playwright may need extra system libraries: `playwright install-deps chromium`.
