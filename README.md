# KDP Studio MCP

Independent, experimental MCP for reading KDP paperback drafts and making one
guarded draft change through a user-authorized Chrome session. It is not
affiliated with Amazon or KDP.

It deliberately has a small surface: it cannot publish a book, buy a proof,
upload files, delete a draft, assign an ISBN, or expose cookies and tokens.

## How it works

Your MCP client starts this local Python server. The server starts Chrome
DevTools MCP, which attaches to a Chrome browser you have already launched with
remote debugging and where you are already signed in to KDP. Requests run inside
that browser session. Credentials and CSRF tokens stay in the browser and are
never returned by this MCP or written to disk.

```text
MCP client → KDP Studio MCP → Chrome DevTools MCP → signed-in Chrome → KDP
```

KDP does not provide a public API for this workflow. This project uses narrowly
observed KDP web requests and may require updates when KDP changes its site.

## Setup

Clone [the public repository](https://github.com/fatoh2/kdp-mcp), then run setup
from its root. Use an isolated Python virtual environment.

Requires Python 3.11+, Node.js/npm (for `npx`), and a current Chrome version.

1. Launch Chrome with remote debugging enabled. On Windows, close every Chrome
   process first, then start:

   ```powershell
   & "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```

   On macOS/Linux, start Chrome with `--remote-debugging-port=9222`.
2. Sign in to KDP in that Chrome profile and open the draft's **Content** page.
3. Clone and install the server:

```sh
git clone https://github.com/fatoh2/kdp-mcp.git
cd kdp-mcp
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
python -m kdp_mcp.server
```

The MCP uses the official Python SDK 1.30.0 and Chrome DevTools MCP 1.9.0.
No Bookforge imports or services are required. Reads work by default; set
`KDP_ENABLE_WRITES=1` in the server environment to expose executable draft writes.

Add it to your MCP client's configuration (replace the Python path with your
virtual environment):

```json
{"mcpServers":{"kdp":{"command":"/absolute/path/to/venv/bin/python","args":["-m","kdp_mcp.server"],"env":{"KDP_ENABLE_WRITES":"1"}}}}
```

On Windows use the virtual environment's `Scripts/python.exe`. Omit the environment
flag for read-only operation. Reload the MCP client after changing configuration.

## Using it safely

Call `kdp_tabs` first and use the returned page ID. Then call
`kdp_draft_status` with that page ID and the KDP draft ID to inspect its state.
The read-only tools are always available.

`kdp_set_cover_finish` is only exposed when `KDP_ENABLE_WRITES=1`. It accepts a
page ID, draft ID, target `MATTE` or `GLOSSY` finish, and the finish you expect
to be set now. The MCP rejects live/certified drafts and mismatched tabs, checks
the current finish, saves once, then reads back the result. Treat an `unknown`
outcome as potentially saved: inspect the draft manually before doing anything
else.

| Tool | Behavior |
| --- | --- |
| `kdp_tabs` | Returns only KDP tabs, stripping URL queries |
| `kdp_draft_status` | Reads draft title, ISBN, page count and preview/certification state |
| `kdp_set_cover_finish` | Saves MATTE/GLOSSY on an existing uncertified DRAFT and verifies it |

Write calls require a matching content tab, draft ID, and expected current finish.
They read the latest settings, retain unrelated print/ISBN fields, acquire a fresh
CSRF token in Chrome, submit once, and read back. No token or cookie is exported.
Timeouts after submission produce `unknown`: inspect before retrying. The expected
value check is optimistic, not a server-side atomic lock; do not edit the same book
from another tab while saving. Writes are serialized within this MCP instance.

No publication, deletion, proof purchase, ISBN assignment, or general-purpose
HTTP tool is exposed. Uploads and metadata/pricing writes are not yet implemented.
An available preview is not a passing preview. Internal endpoints can change.

See [network evidence](docs/00-network-evidence.md), [contributing](CONTRIBUTING.md),
and [tasks](TASKS.md).

## Tests

```sh
pytest -q
```

Tests execute generated JavaScript in Node with mocked KDP responses, checking
write guards, payload preservation, read-back and uncertain-submission handling.

Validated September 14, 2026: unit tests cover read/write responses, input
validation, payload preservation, unsafe states, and uncertain writes; CI runs
them on every pull request. A live save of an existing
uncertified draft preserving its MATTE finish, verified through a fresh read.
An actual MATTE-to-GLOSSY transition remains unverified against live KDP.
