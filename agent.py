"""Drive the Artificial Analysis LLM price calculator with Playwright and check the scraped
result against the expected values declared below.

Setup:
    pip install playwright
    playwright install chromium
"""

import os
import sys
from contextlib import contextmanager
from datetime import datetime

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright

# Windows consoles default to cp1252 and raise on non-ASCII output.
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

CALCULATOR_URL = "https://artificialanalysis.ai/tools/llm-price-calculator"
HEADLESS = True

# --- Inputs typed into the 'Calculate by tokens' form ---
TARGET_MODEL = "Mistral Large 4 Preview"
INPUT_TOKENS, RESPONSE_TOKENS, REASONING_TOKENS, API_CALLS = 1000, 500, 1000, 1000
FIELDS = [("Input tokens", INPUT_TOKENS), ("Response tokens", RESPONSE_TOKENS),
          ("Reasoning tokens", REASONING_TOKENS), ("API calls", API_CALLS)]

# --- Expected result for exactly those inputs ---
# Verified against the page on 2026-10-21. These are the test's oracle: a mismatch means either
# the scrape read the wrong row or Artificial Analysis changed this model's pricing.
# To refresh, run the calculator by hand with the inputs above and copy the row's values here.
EXPECTED_TOTAL_COST = "$7.63"
EXPECTED_COST_PER_CALL = "$0.01"

# The results table is rendered client-side after Calculate is clicked.
RESULTS_TIMEOUT_MS = 30_000


def to_int(text):
    """'1,000' -> 1000. None when the value is not a plain integer."""
    try:
        return int(text.strip().replace(',', ''))
    except (AttributeError, ValueError):
        return None


@contextmanager
def step(steps, description):
    """Record a step as PASS, or as FAIL with its error before letting the exception propagate."""
    try:
        yield
    except Exception as exc:
        steps.append((description, "FAIL", f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}"))
        raise
    steps.append((description, "PASS", ""))


def scrape(page, steps):
    """Fill the calculator, submit it, and return the target row as {column: text}."""
    with step(steps, f"Open {CALCULATOR_URL}"):
        page.goto(CALCULATOR_URL, wait_until="domcontentloaded")

    # The page has two 'API calls' inputs, one per section, so scope to the form that holds the
    # Reasoning tokens field - that is uniquely the 'Calculate by tokens' section.
    form = page.locator("form").filter(has=page.locator('input[name="reasoning"]'))
    with step(steps, "Locate the 'Calculate by tokens' form"):
        expect(form).to_have_count(1)

    for label, value in FIELDS:
        with step(steps, f"Set '{label}' to {value}"):
            form.get_by_label(label, exact=True).fill(str(value))

    # Read the fields back before submitting. The page resets all four to their defaults the
    # instant Calculate is clicked, so this is the only moment the entered values can be verified.
    with step(steps, "Verify all four fields hold the entered values"):
        for label, value in FIELDS:
            expect(form.get_by_label(label, exact=True)).to_have_value(str(value))

    with step(steps, "Click 'Calculate'"):
        form.get_by_role("button", name="Calculate").click()

    row = page.get_by_role("row").filter(has_text=TARGET_MODEL)
    with step(steps, f"Wait for the '{TARGET_MODEL}' row"):
        expect(row).to_have_count(1, timeout=RESULTS_TIMEOUT_MS)

    with step(steps, "Read the row"):
        headers = [h.inner_text().strip() for h in page.get_by_role("columnheader").all()]
        cells = [c.inner_text().strip() for c in row.get_by_role("cell").all()]
        if len(headers) != len(cells):
            raise AssertionError(f"{len(headers)} columns but {len(cells)} cells: {headers} / {cells}")
        return dict(zip(headers, cells))


def validate(result):
    """Return a list of (name, status, detail) comparing the scrape to the expectations."""
    if result is None:
        return [("Scrape produced a row", "FAIL", "The run failed before the row could be read.")]
    checks = [("Scrape produced a row", "PASS", str(result))]
    # The model cell renders the name and the provider on separate lines.
    model_name = result.get("Model", "").splitlines()[0].strip()
    # API calls is compared as a number, since the column renders it as '1,000'.
    for label, expected, actual in (
        ("Model name", TARGET_MODEL, model_name),
        ("Total cost", EXPECTED_TOTAL_COST, result.get("Total cost")),
        ("Cost per call", EXPECTED_COST_PER_CALL, result.get("Cost per call")),
        ("API calls", API_CALLS, to_int(result.get("API calls"))),
    ):
        checks.append((label, "PASS" if actual == expected else "FAIL",
                       f"expected {expected!r}, actual {actual!r}"))
    return checks


def build_report(result, checks, steps, seconds):
    failed = sum(1 for _, status, _ in checks if status == "FAIL")
    lines = [
        "# Price Calculator Check", "",
        f"**Timestamp:** {datetime.now():%Y-%m-%d %H:%M:%S}  |  **Duration:** {seconds:.1f}s", "",
        f"**Inputs:** input={INPUT_TOKENS}, response={RESPONSE_TOKENS}, "
        f"reasoning={REASONING_TOKENS}, calls={API_CALLS}, model={TARGET_MODEL}", "",
        f"**Expected:** total {EXPECTED_TOTAL_COST}, per call {EXPECTED_COST_PER_CALL}", "",
        "## Result", "",
        (f"**{TARGET_MODEL} - Total cost: {result['Total cost']}** "
         f"(cost per call {result['Cost per call']}, API calls {result['API calls']})"
         if result else "*The scrape did not complete; see the steps below.*"), "",
        "## Validations", "", f"**{failed} failed**, {len(checks) - failed} passed.", "",
        "| Check | Status | Evidence |", "|---|---|---|",
    ]
    lines += [f"| {n} | {s} | {d.replace('|', chr(92) + '|')} |" for n, s, d in checks]
    lines += ["", "## Steps", "", "| # | Step | Status | Details |", "|---|---|---|---|"]
    lines += [f"| {i} | {n} | {s} | {d.replace('|', chr(92) + '|')} |"
              for i, (n, s, d) in enumerate(steps, 1)]
    return chr(10).join(lines) + chr(10)


def main():
    started = datetime.now()
    steps, result = [], None
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=HEADLESS)
        try:
            result = scrape(browser.new_page(), steps)
        except (AssertionError, PlaywrightTimeoutError) as exc:
            # The failing step is already recorded; the report carries it to the validations.
            print(f"The scrape failed: {type(exc).__name__}: {str(exc).splitlines()[0]}")
        finally:
            browser.close()
    seconds = (datetime.now() - started).total_seconds()

    print("\n--- Steps ---")
    for index, (name, status, detail) in enumerate(steps, 1):
        print(f"{index:2d}. [{status}] {name}{(' - ' + detail) if detail else ''}")

    if result:
        print(f"\n{TARGET_MODEL}: total cost {result['Total cost']} "
              f"(cost per call {result['Cost per call']}, API calls {result['API calls']})")

    checks = validate(result)
    failed = [c for c in checks if c[1] == "FAIL"]
    print("\n--- Validations ---")
    for name, status, detail in checks:
        print(f"[{status}] {name}: {detail}")
    print(f"{len(failed)} failed, {len(checks) - len(failed)} passed.  ({seconds:.1f}s)")

    os.makedirs("results", exist_ok=True)
    filename = f"results/price_check_{started:%Y-%m-%d_%H-%M-%S}.md"
    with open(filename, 'w', encoding='utf-8') as handle:
        handle.write(build_report(result, checks, steps, seconds))
    print(f"\nResult saved to: {filename}")

    # A failed validation means the scraped figure did not match what was expected.
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
