# Contributing to KDP Studio MCP

Thank you for improving this experimental connector. It operates through an
owner's signed-in browser and KDP's unpublished web endpoints, so safety and
reviewability matter more than adding broad automation quickly.

## Development setup

Use Python 3.11 or newer and a current Node.js LTS release.

```sh
git clone https://github.com/fatoh2/kdp-mcp.git
cd kdp-mcp
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
ruff check .
ruff format --check .
```

The tests use mocked browser and KDP responses. They must never need an Amazon
account, a real draft, or credentials. CI runs the same commands on supported
Python versions.

## Change rules

- Keep session cookies, CSRF tokens, signed URLs, draft IDs, ISBNs, and account
  payloads out of commits, tests, issues, and logs.
- Add narrowly scoped tools. Do not add an arbitrary URL, JavaScript, HTTP, or
  browser-execution tool.
- Mutations must be opt-in, validate the current draft state, submit at most
  once, and read back the result. A transport failure after submission must
  return `unknown`, never invite an automatic retry.
- Preserve unmodified fields from the fresh KDP response. Add tests that prove
  the outgoing payload preserves them and that unsafe states make zero POSTs.
- Keep publishing, purchases, deletion, and credential management out of scope.

## Pull requests

Explain the KDP UI flow observed, the exact data assumptions, the failure
behavior, and the tests added. Do not include raw network captures. Run the
commands above before opening a pull request; GitHub Actions must pass.

KDP can change its web application without notice. If a change may have become
incompatible, open an issue with sanitized behavior and disable the affected
write path until it is revalidated.
