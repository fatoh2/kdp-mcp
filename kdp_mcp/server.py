"""Local stdio MCP. Uses Chrome DevTools MCP; never exports session credentials."""

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

from kdp_mcp.writes import cover_finish_script

_session = None
_write_lock = asyncio.Lock()


def status_script(draft_id: str) -> str:
    if not re.fullmatch(r"[A-Z0-9]{10,16}", draft_id):
        raise ValueError("Invalid KDP draft ID")
    path = f"/print-setup/print-book/{draft_id}/paperback/en-US/v2/get-setup-page"
    return """async () => {
      if (location.origin !== 'https://kdp.amazon.com')
        return {error:'Select a signed-in KDP tab'};
      const r = await fetch(PATH, {credentials:'same-origin', redirect:'error'});
      if (!r.ok) return {error:'KDP request failed', httpStatus:r.status};
      if (!(r.headers.get('content-type') || '').includes('application/json'))
        return {error:'KDP returned a login page or unexpected response'};
      const d = await r.json();
      return {draftId:DRAFT, title:d.book?.title, pageCount:d.derivedAssets?.pageCount,
        certified:d.derivedAssets?.certified === true,
        previewStatus:d.derivedAssetsSpec?.printPreviewerAvailability?.status,
        status:d.publishingState?.status, coverFinish:d.manufacturingSpecs?.cover?.finish,
        proofAvailable:d.publishingState?.proofAvailable === true,
        isbn:d.isbn?.freeIsbn,
        source:'unofficial KDP endpoint via signed-in Chrome'};
    }""".replace("PATH", json.dumps(path)).replace("DRAFT", json.dumps(draft_id))


@asynccontextmanager
async def lifespan(server):
    global _session
    command = "cmd.exe" if os.name == "nt" else "npx"
    args = (["/c", "npx.cmd"] if os.name == "nt" else []) + [
        "-y",
        "chrome-devtools-mcp@1.9.0",
        "--autoConnect",
        "--no-usage-statistics",
        "--no-performance-crux",
    ]
    async with (
        stdio_client(StdioServerParameters(command=command, args=args)) as (
            read,
            write,
        ),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        _session = session
        try:
            yield {}
        finally:
            _session = None


mcp = FastMCP(
    "KDP Studio",
    lifespan=lifespan,
    instructions=(
        "Experimental KDP draft tools. Requires signed-in Chrome with remote debugging. "
        "Preview AVAILABLE is not approval. Writes require explicit user authorization. "
        "Never blindly retry an unknown write. No publishing or purchase tools are exposed."
    ),
)


async def devtools_call(name: str, arguments: dict):
    if _session is None:
        raise ValueError("Start the MCP server before calling tools")
    result = await _session.call_tool(name, arguments)
    if result.isError:
        raise ValueError("Chrome connection failed; check its debugging permission")
    return "\n".join(c.text for c in result.content if c.type == "text")


@mcp.tool()
async def kdp_tabs() -> str:
    """List only KDP tabs. Chrome may ask the owner to allow the connection."""
    result = await devtools_call("list_pages", {})
    # Exclude unrelated tabs and query strings (which can contain auth tokens).
    return (
        "\n".join(
            line.split("?", 1)[0]
            for line in result.splitlines()
            if "(https://kdp.amazon.com/" in line
        )
        or "No KDP tab found. Open KDP in Chrome and sign in."
    )


@mcp.tool()
async def kdp_draft_status(page_id: int, draft_id: str) -> str:
    """Read an existing paperback draft. Does not certify, save, upload or publish."""
    if page_id < 1:
        raise ValueError("Choose a page ID returned by kdp_tabs")
    return await devtools_call(
        "evaluate_script",
        {
            "pageId": page_id,
            "function": status_script(draft_id),
            "waitForStableDom": False,
        },
    )


def main():
    mcp.run(transport="stdio")


@mcp.tool()
async def kdp_set_cover_finish(
    page_id: int, draft_id: str, finish: str, expected_finish: str
) -> str:
    """Save MATTE/GLOSSY on an uncertified existing draft, then verify. User-authorized writes only."""
    if os.environ.get("KDP_ENABLE_WRITES") != "1":
        raise ValueError(
            "Draft writes disabled; set KDP_ENABLE_WRITES=1 in server configuration"
        )
    if page_id < 1:
        raise ValueError("Invalid page ID")
    script = cover_finish_script(draft_id, finish, expected_finish)
    async with _write_lock:
        try:
            return await devtools_call(
                "evaluate_script",
                {
                    "pageId": page_id,
                    "function": script,
                    "waitForStableDom": False,
                },
            )
        except Exception:  # noqa: BLE001 -- Any transport failure can hide a completed write.
            return json.dumps(
                {
                    "outcome": "unknown",
                    "reason": "Browser response unavailable; inspect draft before retrying",
                }
            )


if __name__ == "__main__":
    main()
