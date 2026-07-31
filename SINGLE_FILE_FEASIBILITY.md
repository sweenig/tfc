# Single-File HTML Feasibility (Google Drive Share)

## Short Answer
Yes, this is realistic. Your current UI is already browser-side JavaScript, and the Python backend logic is small enough to port to plain JavaScript. The main work is moving CSV parsing and report-selection logic from FastAPI into the HTML file.

## Effort Estimate
- Working prototype (single rank, upload each session): 2-4 hours
- Feature parity with current app behavior (multi-rank support, validation, error handling): 1-2 days
- Hardening and cross-device validation (iOS Safari, Android Chrome, desktop browsers): +0.5-1 day

## What Changes
1. Replace API calls (`/api/ranks`, `/api/report`, `/api/upload`) with local file input handling.
2. Parse CSV files in browser JavaScript.
3. Rebuild rank detection from filenames:
   - `ReportBuilder_<Unit>_<Rank_Parts>_<YYYYMMDD>.csv`
4. Keep all state in memory for the session (or optional `localStorage`).

## What You Lose vs Current Stack
- No shared live state between users.
- No server-side persistence unless exporting data or using browser storage.
- Every user must load CSV files locally at session start.

## What You Gain
- Zero server dependencies.
- Works from one portable HTML file.
- Easy to distribute through Google Drive.

## Browser/Drive Notes
- If users download and open the file locally, this works on all modern browsers.
- If users open from Google Drive preview mode, script execution can be restricted; users should open in a normal browser tab as a file or from a static host.

## Security/Privacy
- Data stays on-device in memory unless you intentionally save to browser storage.
- This model avoids network transport of scout data.

## Next Suggested Milestones
1. Validate prototype behavior with your real CSV exports.
2. Decide whether attendance should persist between reloads.
3. If needed, add import/export of attendance JSON for sharing records.
