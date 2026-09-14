import pytest

from kdp_mcp.server import status_script


@pytest.mark.parametrize("value", ["../account", "x';fetch('evil')", "", "A" * 100])
def test_rejects_endpoint_injection(value):
    with pytest.raises(ValueError):
        status_script(value)


def test_status_is_read_only_and_allowlisted():
    script = status_script("TESTDRAFT01")
    assert "get-setup-page" in script
    assert "location.origin !== 'https://kdp.amazon.com'" in script
    assert "return d" not in script
    assert "document.cookie" not in script
    assert "method:" not in script
