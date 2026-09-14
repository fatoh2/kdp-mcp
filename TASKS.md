# Tasks — KDP MCP

**Updated:** 2026-09-14 · **Phase:** Experimental draft read/write connector

| Phase | Progress | State |
| --- | --- | --- |
| Separate repository and reads | `████████████` 100% | Done |
| Scoped draft writes | `████████████` 100% | 17 tests; live same-value save verified |
| Uploads and broader fields | `░░░░░░░░░░░░` 0% | Not started |

## Waiting on you
None for the current implementation.

## Next up (mine)
Validate an actual finish transition and capture upload/metadata flows.

## Backlog
Capture and validate upload and metadata/pricing flows. Improve status schemas.
Verify compatibility after KDP changes. No automatic publication or proof purchase.

## Done
- 2026-09-14: Created standalone repository and made it public at the owner's request; reads have no Bookforge dependency.
- 2026-09-14: Captured actual save-draft request; implemented guarded cover-finish write.
- 2026-09-14: 17 tests and lint passed; live same-value draft save verified; CI added. Codex registration points at standalone installation (reload required).
