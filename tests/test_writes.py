import json
import subprocess

import pytest

from kdp_mcp.writes import cover_finish_script


@pytest.mark.parametrize(
    "draft,finish,expected",
    [("../x", "MATTE", "MATTE"), ("TESTDRAFT01", "BAD", "MATTE")],
)
def test_rejects_injection(draft, finish, expected):
    with pytest.raises(ValueError):
        cover_finish_script(draft, finish, expected)


@pytest.mark.parametrize(
    "mode,outcome,posts",
    [
        ("success", "verified", 1),
        ("conflict", "conflict", 0),
        ("live", "rejected", 0),
        ("certified", "rejected", 0),
        ("csrf", "rejected", 0),
        ("wrongpage", "rejected", 0),
        ("timeout", "unknown", 1),
        ("verifyfail", "unknown", 1),
    ],
)
def test_write_contract(mode, outcome, posts):
    script = cover_finish_script("TESTDRAFT01", "GLOSSY", "MATTE")
    harness = """
const mode=MODE; let posts=0,finish=mode==='conflict'?'GLOSSY':'MATTE';
global.location={origin:'https://kdp.amazon.com',pathname:mode==='wrongpage'?'/account':'/en_US/print-setup/paperback/TESTDRAFT01/content'};
global.fetch=async(url,options={})=>{
 if(options.method==='POST'){
  posts++;
  const b=JSON.parse(options.body);
  if(!url.endsWith('/save-draft') || options.headers['anti-csrftoken-a2z']!=='secret')throw Error('contract');
  if(b.manufacturingSpecs.interior.bleed!==false || b.isbn.freeIsbn!=='isbn')throw Error('lost fields');
  finish=b.manufacturingSpecs.cover.finish;
  if(mode==='timeout')throw Error('timeout');
  return {ok:true};
 }
 return {ok:!(posts&&mode==='verifyfail'),headers:{get:()=>mode==='csrf'?null:'secret'},json:async()=>({
  publishingState:{status:mode==='live'?'LIVE':'DRAFT'},derivedAssets:{certified:mode==='certified'},
  isbn:{freeIsbn:'isbn'}, manufacturingSpecs:{trimSize:{width:8.5,height:11},cover:{finish},interior:{bleed:false}},
  publisherAssets:{coverAsset:{coverChoice:'UPLOAD',uploaded:{hasPublisherBarcode:false}}}
 })};
};
(SCRIPT)().then(result=>process.stdout.write(JSON.stringify({result,posts})));
""".replace("MODE", json.dumps(mode)).replace("SCRIPT", script)
    result = json.loads(
        subprocess.run(
            ["node", "-"], input=harness, text=True, capture_output=True, check=True
        ).stdout
    )
    assert result["result"]["outcome"] == outcome
    assert result["posts"] == posts
    assert "secret" not in json.dumps(result)
