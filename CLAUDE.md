# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A QA exercise built around one public web page, the [Artificial Analysis LLM price
calculator](https://artificialanalysis.ai/tools/llm-price-calculator). It holds three independent
pieces, not an application:

- `agent.py` — a Playwright check that drives the calculator and asserts a known price.
- `upload_testcase.py` — pushes `testcase_mistral_large_4.json` into TestCaseLab over its web API.
- `LLM_Price_Calculator_Uzleti_Specifikacio.md` — a Hungarian business specification of the page
  (`BA-SPEC-LLMPC-001`) with numbered requirements `FR-01`–`FR-10` and acceptance criteria
  `AC-01`–`AC-07`. Cite these IDs when deriving test cases; it is the written oracle for the page's
  behaviour, and it is explicitly *not* an official Artificial Analysis document.

There is no package, no `requirements.txt`, no test framework, and no linter. The two scripts share
nothing but the subject under test.

## Commands

Setup (once; the venv already exists in-tree):

```bash
source venv/Scripts/activate      # Git Bash on Windows; see steps.md for CMD/PowerShell/POSIX
pip install playwright python-dotenv
playwright install chromium       # separate from the pip install; without it the run fails on launch
```

Run the check — this is the whole test suite; there is no single-test selector:

```bash
python agent.py                   # exit 0 = all validations passed, 1 = at least one failed
```

Upload a test case to TestCaseLab (needs `TCL_EMAIL`, `TCL_PASSWORD`, `TCL_PROJECT_KEY` in `.env`):

```bash
python upload_testcase.py --list-projects
python upload_testcase.py --list-categories
python upload_testcase.py --category-id <id>            # dry run: prints the payload only
python upload_testcase.py --category-id <id> --create   # actually POSTs
```

## agent.py

Pipeline: `scrape()` fills and submits the form and returns the target table row as
`{column: text}` → `validate()` compares it to the expected constants → `build_report()` renders a
markdown report into `results/price_check_<timestamp>.md`. The `step()` context manager wraps every
browser interaction so each one lands in the report as PASS, or as FAIL with its exception, before
the error propagates.

Three page behaviours are encoded in the script and must survive any edit:

- **The page resets all four inputs to their defaults the instant `Calculate` is clicked**, while
  the results table keeps the submitted figures. The read-back assertion before the click is the
  only moment the entered values can be verified — do not move it after the click.
- **The page has two `API calls` inputs**, one per section. The "Calculate by tokens" form is
  located as the one containing `input[name="reasoning"]`. Element ids are React-generated
  (`_r_14_-form-item`) and change between renders, so they are deliberately never used.
- **The `Model` cell renders the model name and the provider on separate lines**; `validate()`
  compares only the first line.

`EXPECTED_TOTAL_COST = "$7.63"` and `EXPECTED_COST_PER_CALL = "$0.01"` are the test's oracle,
verified against the live page on 2026-10-21 for inputs 1000/500/1000/1000. Changing any input
constant without updating these two will correctly fail the run. A reported `$34.80` means the form
was submitted holding the page's defaults (1000/3000/5000/1000), i.e. the values never landed — a
real defect, not a pricing change. Genuine pricing drift is refreshed by running the calculator by
hand with the same inputs and copying the row's new values in.

**No LLM is involved.** An earlier version drove the page with `browser-use` and a Mistral model
deciding each step; it took 22–83s and filled the form correctly on one run in three, against ~1.4s
and deterministic now. `langchain` and `langchain_mistralai` are still installed in `venv/` and
`MISTRAL_API_KEY` is still in `.env`, but nothing in the repo reads them. `TARGET_MODEL =
"Mistral Large 4 Preview"` is the row being priced on the page, not an API being called.

## upload_testcase.py

TestCaseLab's web API is undocumented publicly; the contract below was established against the live
tenant and the comments in the file record why each detail matters.

- Requests go to the **tenant subdomain** (`https://pro1115oktatas.testcaselab.com`, override with
  `TCL_BASE_URL`). `testcaselab.com` is the marketing site.
- The resource path is `/api/test_cases` — underscore, **no `/api/v1`** namespace.
- Auth is a **Devise session** (cookie + `<meta name="csrf-token">`, rotated on login), not a Bearer
  token. The JWT in `TESTCASELAB_API_KEY` is rejected with 401, which is why `TCL_EMAIL` /
  `TCL_PASSWORD` are required instead.
- `tag_list` must be a **JSON array**; a comma-separated string is accepted and then silently
  stored as no tags.
- Signing in with an account belonging to a different company still returns HTTP 200 and serves
  HTML for `/api/current_resources`. `login()` detects that and the subdomain mismatch explicitly —
  keep those checks, they turn a confusing empty category list into a clear message.

## Repository gotchas

- **`venv/`, `__pycache__/` and `.playwright-mcp/` are tracked in git** (22k+ files) even though
  `.gitignore` lists them — they were committed before the ignore rules existed. `git ls-files` and
  wide diffs are dominated by the venv. Never `git add -A`; stage project files by name.
- `.env` carries a UTF-8 BOM, so `upload_testcase.py` loads it with `encoding='utf-8-sig'`; without
  that the first key parses with a `\ufeff` prefix and `os.getenv` misses it.
- Both scripts call `sys.stdout.reconfigure(encoding='utf-8')` because Windows consoles default to
  cp1252 and raise on non-ASCII output.
- `steps.md` and `steps_hun.md` are the same setup guide in English and Hungarian. They document
  `agent.py`'s constants, its step list, its exit codes and its troubleshooting cases — a behaviour
  change in `agent.py` means updating **both**.
