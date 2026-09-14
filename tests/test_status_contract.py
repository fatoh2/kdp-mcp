import json
import subprocess

import pytest

from kdp_mcp.server import status_script


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("success", {"status": "DRAFT", "coverFinish": "MATTE", "certified": False}),
        ("wrong-origin", {"error": "Select a signed-in KDP tab"}),
        ("http-error", {"error": "KDP request failed", "httpStatus": 403}),
        ("login-page", {"error": "KDP returned a login page or unexpected response"}),
    ],
)
def test_status_script_contract(mode, expected):
    script = status_script("TESTDRAFT01")
    harness = """
const mode=MODE;
global.location={origin:mode==='wrong-origin'?'https://example.com':'https://kdp.amazon.com'};
global.fetch=async (url, options) => ({
  ok:mode!=='http-error', status:403,
  headers:{get:(name)=>name==='content-type' ? (mode==='login-page'?'text/html':'application/json') : null},
  json:async()=>({book:{title:'Example'},isbn:{freeIsbn:'isbn'},derivedAssets:{pageCount:32,certified:false},
    derivedAssetsSpec:{printPreviewerAvailability:{status:'AVAILABLE'}},
    publishingState:{status:'DRAFT',proofAvailable:false},manufacturingSpecs:{cover:{finish:'MATTE'}}})
});
(SCRIPT)().then(value=>process.stdout.write(JSON.stringify(value)));
""".replace("MODE", json.dumps(mode)).replace("SCRIPT", script)
    completed = subprocess.run(
        ["node", "-"], input=harness, text=True, capture_output=True, check=False
    )
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result.items() >= expected.items()
