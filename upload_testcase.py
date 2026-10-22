"""Upload a test case to TestCaseLab.

Why the previous attempt got 404 "Route not found":
  * There is no /api/v1 namespace. The resource path is /api/test_cases (underscore, no version).
  * https://testcaselab.com is the marketing site, not an API host. Requests must go to the
    tenant subdomain, e.g. https://olm.testcaselab.com.
  * TestCaseLab's web API authenticates with a Devise session (cookie + CSRF token), not with a
    Bearer JWT. A JWT in the Authorization header is rejected with 401.

Auth flow (same one the OLM C# and TypeScript integrations use):
  GET  /users/sign_in              -> cookie + <meta name="csrf-token">
  POST /users/sign_in              -> form-encoded credentials, CSRF rotates
  GET  /api/current_resources      -> verify the session

Configuration (environment variables, same names as the existing OLM integration):
  TCL_BASE_URL      default https://pro1115oktatas.testcaselab.com/
  TCL_EMAIL         required
  TCL_PASSWORD      required
  TCL_PROJECT_KEY   default OLM

Usage:
  python upload_testcase.py --list-categories        # pick a destination category id
  python upload_testcase.py --category-id 138811     # dry run: show what would be sent
  python upload_testcase.py --category-id 138811 --create
"""

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

from dotenv import load_dotenv

# encoding='utf-8-sig' strips a UTF-8 BOM; without it the first key in the file parses with a
# '﻿' prefix and os.getenv misses it.
load_dotenv(encoding='utf-8-sig')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DEFAULT_BASE_URL = "https://pro1115oktatas.testcaselab.com"
DEFAULT_PROJECT_KEY = ""
DEFAULT_JSON = "testcase_mistral_large_4.json"
CSRF_META = re.compile(r'<meta name="csrf-token" content="([^"]+)"')


class TestCaseLabClient:
    """Devise-session client for TestCaseLab's web API."""

    def __init__(self, base_url, project_key):
        self.base_url = base_url.rstrip('/')
        self.project_key = project_key
        self.csrf = ""
        self.resources = {}
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(CookieJar()))
        self.opener.addheaders = [('User-Agent', 'upload_testcase.py')]

    def _read(self, response):
        return response.read().decode('utf-8', 'replace')

    def login(self, email, password):
        page = self._read(self.opener.open(f"{self.base_url}/users/sign_in"))
        found = CSRF_META.search(page)
        if not found:
            raise RuntimeError("No CSRF token on the sign-in page - is TCL_BASE_URL the tenant "
                               "subdomain (e.g. https://olm.testcaselab.com)?")
        self.csrf = html.unescape(found.group(1))

        body = urllib.parse.urlencode({
            'user[email]': email,
            'user[password]': password,
            'user[remember_me]': '0',
            'authenticity_token': self.csrf,
        }).encode()
        page = self._read(self.opener.open(f"{self.base_url}/users/sign_in", data=body))
        rotated = CSRF_META.search(page)
        if rotated:
            self.csrf = html.unescape(rotated.group(1))

        status, text = self.get("/api/current_resources")
        if status != 200:
            raise RuntimeError(f"Session check failed (HTTP {status}). Check TCL_EMAIL/TCL_PASSWORD.")

        # A login with an account that does not belong to this tenant still returns HTTP 200:
        # TestCaseLab silently redirects every request to the account's own company dashboard and
        # serves HTML. Detecting that here turns a confusing "no categories" result into a clear
        # message about the account being in the wrong company.
        try:
            self.resources = json.loads(text)
        except json.JSONDecodeError:
            raise RuntimeError(
                f"Signed in, but {self.base_url} served HTML instead of JSON for "
                "/api/current_resources. That means this account has no access to this tenant - "
                "TestCaseLab bounced the request to the account's own company. Use credentials "
                "belonging to this subdomain.") from None

        subdomain = (self.resources.get('company') or {}).get('subdomain', '')
        host = urllib.parse.urlparse(self.base_url).hostname or ''
        if subdomain and not host.startswith(f"{subdomain}."):
            raise RuntimeError(
                f"Signed in to company '{subdomain}' but TCL_BASE_URL points at '{host}'. "
                "These credentials belong to a different tenant.")

    def projects(self):
        return self.resources.get('projects', [])

    def get(self, path):
        try:
            response = self.opener.open(self.base_url + path)
            return response.status, self._read(response)
        except urllib.error.HTTPError as exc:
            return exc.code, self._read(exc)

    def post_json(self, path, payload):
        request = urllib.request.Request(
            self.base_url + path, data=json.dumps(payload).encode('utf-8'), method='POST',
            headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                     'X-CSRF-Token': self.csrf})
        try:
            response = self.opener.open(request)
            return response.status, self._read(response)
        except urllib.error.HTTPError as exc:
            return exc.code, self._read(exc)

    def categories(self):
        status, text = self.get(f"/api/categories?project_key={self.project_key}")
        if status != 200:
            raise RuntimeError(f"Could not list categories (HTTP {status}): {text[:200]}")
        return json.loads(text)


def build_payload(source, category_id):
    """Map the local JSON file onto the fields TestCaseLab's test_case resource exposes.

    Field names were read off a real case via GET /api/test_cases/{id}: title, category_id,
    description, steps, expected_result, priority, test_type, tag_list.
    """
    steps_text = "\n".join(
        f"{step.get('step_number', index)}. {step.get('action', '').strip()}"
        + (f" [{step['input_field']} = {step.get('value', '')}]" if step.get('input_field') else "")
        + (f" ({step['url']})" if step.get('url') else "")
        + (f"\n   Expected: {step['expected_result']}" if step.get('expected_result') else "")
        for index, step in enumerate(source.get('steps', []), 1))

    return {
        'title': source['name'],
        'category_id': category_id,
        'description': source.get('description', ''),
        'steps': steps_text,
        'expected_result': source.get('expected_outcome', ''),
        'priority': 'Normal',
        'test_type': 'Functional',
        # tag_list must be a JSON array; a comma-separated string is accepted by the API but
        # silently stored as no tags at all.
        'tag_list': ['automated', 'llm-price-calculator'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--json', default=DEFAULT_JSON, help=f"source file (default {DEFAULT_JSON})")
    parser.add_argument('--category-id', type=int, help="destination category (suite) id")
    parser.add_argument('--list-projects', action='store_true', help="print this tenant's projects and exit")
    parser.add_argument('--list-categories', action='store_true', help="print categories and exit")
    parser.add_argument('--create', action='store_true',
                        help="actually POST the case; without it the script only shows the payload")
    args = parser.parse_args()

    base_url = os.getenv('TCL_BASE_URL', DEFAULT_BASE_URL)
    project_key = os.getenv('TCL_PROJECT_KEY', DEFAULT_PROJECT_KEY)
    email, password = os.getenv('TCL_EMAIL'), os.getenv('TCL_PASSWORD')
    if not email or not password:
        raise SystemExit(
            "TCL_EMAIL and TCL_PASSWORD must be set.\n"
            "TestCaseLab's web API uses email+password session auth, not the JWT in "
            "TESTCASELAB_API_KEY - that token is rejected with 401.")

    client = TestCaseLabClient(base_url, project_key)
    print(f"Signing in to {base_url}...")
    client.login(email, password)
    company = (client.resources.get('company') or {}).get('name', '?')
    print(f"Signed in to company '{company}'.")

    if args.list_projects:
        for project in client.projects():
            print(f"  key={project['key']:<8} id={project['id']:<8} {project['name']}")
        return 0

    if not project_key:
        keys = ", ".join(p['key'] for p in client.projects()) or "(none visible)"
        raise SystemExit(f"TCL_PROJECT_KEY is not set. Projects on this tenant: {keys}\n"
                         "Run --list-projects for details.")

    if args.list_categories:
        for category in sorted(client.categories(), key=lambda c: c['name']):
            parent = f"  (parent {category['parent_id']})" if category.get('parent_id') else ""
            print(f"{category['id']:>8}  {category['name']}{parent}")
        return 0

    if not args.category_id:
        raise SystemExit("--category-id is required. Run --list-categories to see the options.")

    valid_ids = {c['id'] for c in client.categories()}
    if args.category_id not in valid_ids:
        raise SystemExit(f"Category {args.category_id} is not in project {project_key}. "
                         "Run --list-categories.")

    with open(args.json, encoding='utf-8') as handle:
        source = json.load(handle)
    payload = build_payload(source, args.category_id)

    print(f"\nPayload for POST {base_url}/api/test_cases?project_key={project_key}")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    if not args.create:
        print("\nDry run - nothing was uploaded. Re-run with --create to POST it.")
        return 0

    status, text = client.post_json(f"/api/test_cases?project_key={project_key}", payload)
    print(f"\nHTTP {status}")
    if status in (200, 201):
        try:
            created = json.loads(text)
            inner = created.get('test_case', created)
            print(f"Created: id={inner.get('id')} key={inner.get('key')} title={inner.get('title')!r}")
        except json.JSONDecodeError:
            print(text[:500])
        return 0

    # The exact request shape for creating a case is not publicly documented; if the server
    # rejects it, its response body names the offending field.
    print(text[:800])
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as error:
        # Configuration and access problems are reported as a message, not a traceback.
        print(f"\n{error}", file=sys.stderr)
        sys.exit(2)
