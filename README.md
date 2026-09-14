# KDP Studio MCP

Independent, experimental MCP for reading KDP paperback drafts and saving supported
draft changes through a user-authorized Chrome session. Not affiliated with Amazon.

## Setup

Clone [the public repository](https://github.com/fatoh2/kdp-mcp), then run setup
from its root. Use an isolated Python virtual environment.

Requires Python 3.11+, Node/npx and Chrome 144+ with remote debugging enabled.
Sign in to KDP in Chrome and accept its debugging connection prompt.

```sh
pip install -e ".[dev]"
python -m kdp_mcp.server
```

The MCP uses the official Python SDK 1.30.0 and Chrome DevTools MCP 1.9.0.
No Bookforge imports or services are required. Reads work by default; set
`KDP_ENABLE_WRITES=1` in the server environment to expose executable draft writes.

Example MCP client configuration (replace the Python path with your virtual environment):

```json
{"mcpServers":{"kdp":{"command":"/absolute/path/to/venv/bin/python","args":["-m","kdp_mcp.server"],"env":{"KDP_ENABLE_WRITES":"1"}}}}
```

On Windows use the virtual environment's `Scripts/python.exe`. Omit the environment
flag for read-only operation. Reload the MCP client after changing configuration.

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

See [network evidence](docs/00-network-evidence.md) and [tasks](TASKS.md).

## Tests

```sh
pytest -q
```

Tests execute generated JavaScript in Node with mocked KDP responses, checking
write guards, payload preservation, read-back and uncertain-submission handling.

Validated September 14, 2026: 17 tests passed, plus a live save of an existing
uncertified draft preserving its MATTE finish, verified through a fresh read.
An actual MATTE-to-GLOSSY transition remains unverified against live KDP.
