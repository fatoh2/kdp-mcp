import json

import pytest

from kdp_mcp import server


async def test_write_disabled_by_default(monkeypatch):
    monkeypatch.delenv("KDP_ENABLE_WRITES", raising=False)
    with pytest.raises(ValueError, match="disabled"):
        await server.kdp_set_cover_finish(1, "TESTDRAFT01", "MATTE", "MATTE")


async def test_transport_failure_is_unknown(monkeypatch):
    monkeypatch.setenv("KDP_ENABLE_WRITES", "1")

    async def failed(*args):
        raise RuntimeError("private transport detail")

    monkeypatch.setattr(server, "devtools_call", failed)
    result = await server.kdp_set_cover_finish(1, "TESTDRAFT01", "MATTE", "MATTE")
    assert json.loads(result)["outcome"] == "unknown"
    assert "private" not in result
