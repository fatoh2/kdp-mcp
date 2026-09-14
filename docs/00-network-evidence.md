# Observed KDP requests

Verified through the owner's Chrome session on September 14, 2026:

- GET `/print-setup/print-book/{draft}/paperback/en-US/v2/get-setup-page`
- POST `/print-setup/print-book/{draft}/paperback/en-US/v2/save-draft`

The latter was captured from Save as Draft. Its JSON contains `isbn`,
`manufacturingSpecs`, `coverAssetConfig`, and `updateInfo.operation=content_save-draft`.
The GET response provides an `anti-csrftoken-a2z` header; writes use it in memory.
Success is HTTP 200 with an empty JSON object; read-back is required.

Raw cookies, signed asset URLs, account payloads and CSRF values are intentionally
not stored in this repository. This is session-backed access, not public API access.
No standalone authentication, upload, pricing or publication API was verified.
