"""Fixed-route mutations; credentials stay inside the browser."""

import json
import re


def cover_finish_script(draft_id: str, finish: str, expected_finish: str) -> str:
    if not re.fullmatch(r"[A-Z0-9]{10,16}", draft_id):
        raise ValueError("Invalid draft ID")
    if finish not in {"MATTE", "GLOSSY"} or expected_finish not in {"MATTE", "GLOSSY"}:
        raise ValueError("Finish must be MATTE or GLOSSY")
    return (
        """async () => {
      const draft = DRAFT_ID, finish = FINISH, expected = EXPECTED;
      const base = '/print-setup/print-book/' + draft + '/paperback/en-US/v2/';
      if (location.origin !== 'https://kdp.amazon.com' ||
          !location.pathname.endsWith('/paperback/' + draft + '/content'))
        return {outcome:'rejected', reason:'Open the matching draft content page'};
      let submitted = false;
      try {
        const response = await fetch(base+'get-setup-page', {redirect:'error'});
        if (!response.ok) return {outcome:'rejected', reason:'Read failed', httpStatus:response.status};
        const csrf = response.headers.get('anti-csrftoken-a2z');
        const d = await response.json();
        if (!csrf || d.publishingState?.status !== 'DRAFT' || d.derivedAssets?.certified === true)
          return {outcome:'rejected', reason:'Requires CSRF and an uncertified draft'};
        if (d.manufacturingSpecs?.cover?.finish !== expected)
          return {outcome:'conflict', reason:'Cover finish changed; refresh status'};
        const cover = d.publisherAssets?.coverAsset;
        if (cover?.coverChoice !== 'UPLOAD' || typeof cover.uploaded?.hasPublisherBarcode !== 'boolean')
          return {outcome:'rejected', reason:'Unsupported cover schema'};
        const specs = d.manufacturingSpecs;
        if (!d.isbn || !specs?.trimSize || !specs?.cover || !specs?.interior)
          return {outcome:'rejected', reason:'Incomplete KDP draft schema'};
        const body = {isbn:d.isbn, manufacturingSpecs:{trimSize:specs.trimSize,
          cover:{...specs.cover,finish},interior:specs.interior},
          coverAssetConfig:{coverChoice:'UPLOAD',hasPublisherBarcode:cover.uploaded.hasPublisherBarcode},
          updateInfo:{operation:'content_save-draft'}};
        submitted = true;
        const saved = await fetch(base+'save-draft', {method:'POST',redirect:'error',
          headers:{'content-type':'application/json','anti-csrftoken-a2z':csrf},
          body:JSON.stringify(body)});
        if (!saved.ok) return {outcome:'unknown', httpStatus:saved.status,
          reason:'Save was submitted; inspect before retrying'};
        const verify = await fetch(base+'get-setup-page',{redirect:'error'});
        if (!verify.ok) return {outcome:'unknown',reason:'Save accepted; read-back failed'};
        const after = await verify.json();
        if (after.manufacturingSpecs?.cover?.finish !== finish || after.publishingState?.status !== 'DRAFT')
          return {outcome:'unknown',reason:'Read-back differs from expected draft state'};
        return {outcome:'verified',draftId:draft,previousFinish:expected,finish,status:'DRAFT'};
      } catch (_) {
        return {outcome:submitted?'unknown':'rejected',reason:submitted?
          'Save may have completed; inspect before retrying':'Session read failed'};
      }
    }""".replace("DRAFT_ID", json.dumps(draft_id))
        .replace("FINISH", json.dumps(finish))
        .replace("EXPECTED", json.dumps(expected_finish))
    )
