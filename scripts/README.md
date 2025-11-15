# Scripts Directory

Organized utility scripts that are NOT part of the production runtime.

## Structure
- diagnostics/: One-off environment, connectivity, and health verification scripts.
- migration/: Data migration or transitional scripts to move / transform stored data.

## Diagnostics Scripts
| Script | Purpose |
|--------|---------|
| diagnostics/check_railway.py | Pre-deployment readiness checklist for Railway. |
| diagnostics/check_drafts.py | Quick inspection of stored drafts for a user. |
| diagnostics/database_url_fix.py | Explanation + guidance for resolving local vs internal DATABASE_URL host issues. |
| diagnostics/test_profile.py | Inspect user profile record existence/content. |
| diagnostics/test_draft_history.py | Verify draft persistence path (DB vs JSON) & create test draft. |

## Migration Scripts
(Currently empty; add future data migration tools here.)

## Conventions
- No script here should be imported by production `src/` modules.
- Safe to execute locally or in a sandbox; do not rely on them in deployment.
- Keep credentials out of committed script code; rely on `.env`.

## Adding a New Script
1. Choose folder: `diagnostics` for environment checks / quick state inspection; `migration` for data transforms.
2. Add clear top-level docstring with intent, usage, and safety notes.
3. Update the table above.

