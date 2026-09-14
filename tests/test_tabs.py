import pytest

from kdp_mcp import server


async def test_tabs_excludes_other_sites_and_strips_query(monkeypatch):
    async def pages(*_):
        return (
            "5: Other (https://example.com/?secret=never-return-this)\n"
            "8: KDP (https://kdp.amazon.com/en_US/print-setup/paperback/"
            "TESTDRAFT01/content?token=private)"
        )

    monkeypatch.setattr(server, "devtools_call", pages)
    assert await server.kdp_tabs() == (
        "8: KDP (https://kdp.amazon.com/en_US/print-setup/paperback/TESTDRAFT01/content)"
    )


async def test_tabs_explains_when_no_kdp_tab_exists(monkeypatch):
    async def pages(*_):
        return "1: Other (https://example.com/)"

    monkeypatch.setattr(server, "devtools_call", pages)
    assert "No KDP tab found" in await server.kdp_tabs()


@pytest.mark.parametrize("page_id", [0, -4])
async def test_status_rejects_nonpositive_page_id(page_id):
    with pytest.raises(ValueError, match="page ID"):
        await server.kdp_draft_status(page_id, "TESTDRAFT01")
