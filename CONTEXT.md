# CONTEXT.md

Project narrative for humans and AI agents with zero prior context. Operating commands and boundaries live in `AGENTS.md`.

## What This Project Is

**STATZ Corporation** public website (repo: `statzcorp-com`, remote: `https://github.com/dmani-STATZ/statzcorp-com.git`).

STATZ is a Service-Disabled Veteran-Owned Small Business (SDVOSB) that provides supply-chain support to government, military, and commercial customers. The site markets capabilities, team, products, accreditations, contact intake, and public surveys.

Company facts shown in `templates/base.html` / contact templates:

| Fact | Value | Source |
|------|--------|--------|
| Phone | 608-798-4500 | `templates/base.html` |
| Fax | 608-798-4503 | `templates/base.html` |
| Email | info@statzcorp.com, quotes@statzcorp.com | `templates/base.html` |
| Address | 2120 W Greenview Drive, Suite 3, Middleton, WI 53562 | `templates/contact/contact-us.html` |
| CAGE | 3WGD1 | `templates/base.html` |
| Timezone setting | America/Chicago | `statzcorp/settings/base.py` |

The active application is **Django 5.2** (`requirements.txt`, installed 5.2.16 in local `.venv`). A prior static/PHP mail approach is treated as legacy (see Current State).

## Current State

**Git:** Branch `main`, tracking `origin/main`. Single commit: `777246d` — “Initial commit without large video file.” `AGENTS.md` / `CONTEXT.md` were untracked at last inspection.

**Built and present in code:**

| Area | Status | Evidence |
|------|--------|----------|
| Project settings split (base / local / production) | Done | `statzcorp/settings/` |
| Marketing pages (home, about, team, products, capabilities, accreditations, resources) | Done | `apps/public/`, `templates/public/` |
| Contact form → DB + email notification | Done | `apps/contact/` — `ContactMessage` + admin-managed `ContactRecipient` list (queried at send-time); `CONTACT_EMAIL_TO` is a comma-separated fallback only when no active recipients exist |
| Surveys with classification field + public manager | Done | `apps/surveys/` |
| Video hosting (Azure Blob / local filesystem) | Done | `apps/videos/` — `VideoAsset`, public `/videos/<slug>/`, admin upload |
| Admin for contact messages and surveys | Done | `apps/*/admin.py` |
| Custom site chrome + CSS/JS | Done | `templates/base.html`, `static/css/style.css`, `static/js/main.js` |
| Env template for Azure/GCCH-oriented deploy | Documented | `.env.example`, `requirements.txt` comments |
| Azure App Service (Linux) startup script | Done | `startup.sh` (collectstatic → migrate → gunicorn on `$PORT`) |
| Redesign / feature roadmap | Written, not implemented as code | `rebuild_migration_plan.md` |
| Resources guides (CAGE / JCP / shipping / supplier success) | Done | `public:resources`, `templates/public/resources.html` (`#cage-code`, `#jcp`, `#shipping`, `#supplier-success`), nav/footer in `templates/base.html` |
| Brand palette navy + gold | Done | `static/css/style.css` `:root` (`--primary`, `--accent`, …) |
| Supplier Portal — Phase 1a shell (login/session only, no supplier data yet) | Done | `apps/supplier_portal/` — `SupplierPortalAccount` model (hashed password, lockout, session key `supplier_portal_account_id`, intentionally separate from `django.contrib.auth`); `supplier_portal:login`/`logout`/`dashboard` views; "Supplier Portal" tab added to `public:resources` jump-nav. Dashboard is an empty shell — see Phase 1b below. |
| Supplier Portal — self-service passwords (staff out of the password chain) | Done | `apps/supplier_portal/` — request-access/forgot-password flow: supplier enters CAGE → sees masked on-file email → confirms → gets a signed 1-hour single-use set-password link (`tokens.py`, `emails.py`; token embeds a password-hash fragment so it dies on use). Cooldown 1 request/15 min per account. Admin has **no password field** — staff creates accounts with CAGE + contact email only; an admin action emails the same link. Passwords validated with `AUTH_PASSWORD_VALIDATORS`. |
| Supplier Portal — Phase 1b STATZWeb API client | Done | `apps/supplier_portal/statzweb_client.py` — signs every call with `X-API-Key` + HMAC-SHA256 (`X-Timestamp`/`X-Signature`) exactly matching STATZWeb's `suppliers/portal/auth.py`. `verify_supplier(cage_code)` calls STATZWeb's live `GET .../verify/` endpoint; `RequestAccessForm` (`forms.py`) now auto-provisions/refreshes `SupplierPortalAccount.contact_email` from that response instead of relying on staff-entered data — a CAGE code that exists in STATZWeb "just works" on the portal with no manual account-creation step. Verified 2026-07-20 against a live local STATZWeb instance on real SQL Server: correct data returned, wrong HMAC secret correctly rejected, unknown CAGE code correctly returns nothing. STATZWeb's API contract: `docs/supplier-portal-api-contract.md`. |

**Frontend styling decision (owner-stated):** Stick with project CSS in `static/css/style.css`. No Tailwind. No Bootstrap. No django-crispy-forms. Keep CSS in templates minimal; prefer classes defined in the shared stylesheet. Crispy/Bootstrap packages were removed from `requirements.txt` and `statzcorp/settings/base.py` with owner approval. Main nav (`.nav-inner`) is centered (`justify-content: center`) — was `flex-end` from the legacy static design.

**In progress / transitional:**

- None currently tracked for visual identity (navy/gold palette applied 2026-07-13).

**Not started (roadmap only — `rebuild_migration_plan.md`):**

- `NewsPost` model / news engine
- Microsoft Bookings embeds
- Content rewrites (NSN/FSC emphasis, condensed history, team group-photo approach, cert PDF downloads)
- LinkedIn / video production program (mostly off-site)
- Migrate database from SQLite to Microsoft SQL Server (MSSQL) — attempted 2026-07-14 and reverted; blocked on ODBC Driver 18 persistence on App Service Linux and VNet Integration to the private DB host (not just Django config). Packages/settings remain stubbed in comments for resume.
- Supplier Portal Phase 1b (remaining) — STATZWeb already fully implements the API server-side (`STATZWeb/STATZCorp/suppliers/portal/` — confirmed 2026-07-20, both read and Phase 2 write endpoints exist, matching `docs/supplier-portal-api-contract.md` closely). `statzweb_client.py` on this side currently only calls `verify/` (used by the request-access flow). Still to build: the dashboard (`supplier_portal:dashboard`) needs to call `GET .../suppliers/{cage_code}/` and actually render the profile/contacts/certifications/classifications/documents instead of the placeholder shell.
- Supplier Portal Phase 2 (remaining) — client-side forms/views on this project to call STATZWeb's already-existing write endpoints (profile PATCH, contact CRUD, document upload). STATZWeb enforces the editable-field allowlist and audits/notifies staff per write; no approval queue.

**Legacy / non-Django leftovers:**

- Root `css/` and `js/` — tracked; byte-identical to `static/css` and `static/js`; not referenced by Django templates.
- `php/`, `config/`, `composer.json` — gitignored as “Legacy static-site files”; may exist on a developer machine but are not part of the git tree.

**Missing tooling:** No README, no automated tests, no linter config, no CI workflows, no full Azure pipeline / App Service infrastructure-as-code in-repo. Azure Linux App Service startup is covered by checked-in `startup.sh` (set as Startup Command in the portal / CLI); ops must still configure App Settings (`DJANGO_SETTINGS_MODULE`, secrets, hosts, SMTP).

## Architecture Overview

```
Browser
  → Django URLConf (statzcorp/urls.py)
       → apps.public     TemplateViews → templates/public/* (+ HeroSlide admin hero slideshow)
       → apps.contact    FormView → ContactMessage DB + email to ContactRecipient (fallback: CONTACT_EMAIL_TO)
       → apps.surveys    List/detail → Survey/Question/Submission/Answer
       → apps.videos     DetailView → VideoAsset (Blob Storage or local media)
       → apps.supplier_portal  Session-based login (own SupplierPortalAccount, not django.contrib.auth) → dashboard shell (Phase 1b will call the STATZWeb API for real data)
       → /admin/         Django admin
  ← templates/base.html + static/ (WhiteNoise in middleware for static files)
```

**Data stores:**

- **Current:** SQLite via `statzcorp/settings/base.py` defaults / `.env.example` (`django.db.backends.sqlite3`, file `db.sqlite3`, gitignored).
- **Planned later:** Microsoft SQL Server (MSSQL). Transition notes live in `.env.example` and commented deps in `requirements.txt` (`mssql-django`, `pyodbc`). Not configured yet.
- **Media / video files:** Local `FileSystemStorage` when `AZURE_CONNECTION_STRING` is unset; Azure Blob Storage (`storages.backends.azure_storage.AzureStorage`, GCCH-compatible connection string, container `media`) when set. Models: `VideoAsset` in `apps/videos/`; `HeroSlide` in `apps/public/` (admin-managed home page hero slideshow images on the same Blob-or-local storage path). Django caps large admin uploads at `DATA_UPLOAD_MAX_MEMORY_SIZE` = 1 GB (`statzcorp/settings/base.py`). When zero published `HeroSlide` rows exist, `templates/public/index.html` falls back to the legacy static slider images so the hero never renders blank.
- **Not used:** PostgreSQL — removed from project guidance and deps (owner-stated).

**Admin:** Branded via `PublicConfig.ready()` + `templates/admin/login.html`. Public footer includes a discreet Log In link to `/admin/`. Staff retrieve public video Blob URLs and landing-page links from the VideoAsset admin **Share Links** fieldset (and the list-view Copy URL column) — not from the Azure portal.

**Azure App Service / large video uploads:** Gunicorn’s `--timeout` may need to stay high enough for Blob uploads through admin (e.g. 300s or more). This is a deployment setting on the Azure startup command — `startup.sh` in-repo already uses `--timeout=600`; re-check if ops changes the Startup Command in the portal.

**Email:** Console backend forced in `statzcorp/settings/local.py`. Production uses SMTP settings from env (Office 365 host defaults in `base.py` / `.env.example`).

**Auth for public site:** Anonymous public pages. Optional `Submission.user` FK if authenticated. Entra ID / MSAL packages are commented out in `requirements.txt` (“add when ready for internal views”) — not active. Supplier Portal (`apps/supplier_portal`) is a third, separate identity system: session key `supplier_portal_account_id` against `SupplierPortalAccount`, deliberately not `django.contrib.auth` — a supplier login is a company (CAGE code), not a staff/admin identity. Passwords are entirely self-service (signed emailed set-password links); staff never sets, sees, or resets a password — by design (“chain of custody” decision, 2026-07-20). The on-file `contact_email` is sourced live from STATZWeb's `verify/` endpoint (`statzweb_client.py`) on every request-access attempt, auto-provisioning/refreshing the local `SupplierPortalAccount` — no separate staff account-creation step for a supplier that already exists in STATZWeb.

**Documentation:** Staff guide for uploading, sharing, and embedding videos → [`docs/how-to-add-videos.md`](docs/how-to-add-videos.md) (canonical). Supplier Portal API contract (spec for the STATZWeb-side API, not yet built) → [`docs/supplier-portal-api-contract.md`](docs/supplier-portal-api-contract.md). Product/design roadmap → `rebuild_migration_plan.md`. Agent operating rules → `AGENTS.md`.

## Terminology / Glossary

| Term | Meaning in this project |
|------|-------------------------|
| **SDVOSB** | Service-Disabled Veteran-Owned Small Business — company designation shown site-wide |
| **CAGE** | Commercial and Government Entity code; STATZ value `3WGD1` |
| **CMMC** | Cybersecurity Maturity Model Certification — referenced in site badges/content and roadmap |
| **CUI / CTI / CDI** | Controlled Unclassified Information / Controlled Technical Information / Covered Defense Information — values of `security_classification` on survey models; must not appear on public survey surfaces |
| **`public_objects`** | Custom manager on `ClassifiedModel` that excludes CUI/CTI/CDI (`apps/surveys/models.py`) |
| **`published_objects`** | Custom manager on `VideoAsset` that returns only `is_published=True` (`apps/videos/models.py`) |
| **GCCH** | Azure Government Community Cloud High — stated target environment in settings/requirements comments |
| **NSN / FSC** | National Stock Number / Federal Stock Class — domain terms in roadmap content for capabilities copy |
| **JCP** | Joint Certification Program (DD Form 2345) — covered on the Resources page (`public:resources`) |
| **Legacy static-site files** | `.gitignore` label for `php/`, `config/`, `composer.json` — not the active stack |
| **Custom CSS stack** | Owner rule: style via `static/css/style.css` only — no Tailwind, no Bootstrap, no crispy-forms; minimize template-embedded CSS |
| **SQLite to MSSQL** | Current DB is SQLite; planned production database is Microsoft SQL Server — not PostgreSQL |

## Known Issues / Tech Debt

Only items with a concrete source:

1. **Brand palette migration complete in active assets.** Live `static/css/style.css` uses navy/gold (`--primary`, `--accent`, …). Untouched root `css/` / `js/` duplicates still contain legacy `#c9222a` / `--red` until Dion decides whether to delete or resync them.
2. **Page-local CSS in some templates.** `templates/contact/contact-us.html` and `templates/public/accreditations.html` still embed `<style>` blocks; Django messages styles in `templates/base.html` were moved to `static/css/style.css` (`.site-message*`). Preference remains consolidating remaining template CSS into the shared stylesheet.
3. **Duplicate CSS/JS trees.** Root `css/` + `js/` identical to `static/` copies at last full sync; risk of editing the wrong tree (and they have diverged after the 2026-07-13 palette work on `static/` only).
4. **Survey detail GET vs classification.** `survey_detail_view` uses `survey.questions.all()`; POST skips classified questions, but GET does not filter via `public_objects` (`apps/surveys/views.py`).
5. **~~About Us legacy static MP4~~ (resolved).** About Us embeds via `{% get_video 'team-statz' %}` + `videos/_video_embed.html` (`apps/videos/templatetags/video_tags.py`). Missing/unpublished video omits the section (no 500). Standard pattern for page-embedded videos: `get_video` + `_video_embed.html` — never `{% static %}` for `.mp4`. `*.mp4` remains gitignored; upload via admin `VideoAsset`.
6. **No automated tests or CI.** Confirmed by absence of test modules and `.github/workflows`.
7. **MSSQL migration not implemented.** Only documented as future in `.env.example` / `requirements.txt` comments.
8. **Supplier Portal emails to external recipients unverified in production.** The set-password flow (`apps/supplier_portal/emails.py`) emails supplier (external) addresses. GCCH *direct send* endpoints (`*.mail.protection.office365.us`, port 25) generally deliver only to recipients inside the tenant; external delivery needs authenticated SMTP submission (the port-587 + TLS config `base.py` env vars already support) or an Exchange connector relay configured by ops. Must be tested against a real external address before the portal launches. Local dev uses the console email backend (`settings/local.py`).
9. **STATZWeb dev-DB suppliers have no `primary_email` populated.** Confirmed 2026-07-20 against the shared SQL Server dev DB — no `Supplier` row (including the `TEST1` fixture) has a non-empty `primary_email`, so the request-access "masked email" screen can't be demoed end-to-end against real data yet; the "no contact email on file" branch is what actually fires today. Needs either a real supplier's data or a deliberately-set test value before that specific screen can be shown live.

## Stakeholders / Points of Contact

| Role | Who | Source |
|------|-----|--------|
| Primary technical / IT & Manufacturing Operations contact for this site | **Dion** | `rebuild_migration_plan.md` (Bookings: “Dion (IT & Manufacturing Operations)”); GitHub remote org/user `dmani-STATZ`; local workspace owner |
| Accounting & Contract Administration (Bookings targets in plan) | Jenny / Chad | `rebuild_migration_plan.md` only — not encoded in app config |
| Public contact inbox (runtime) | Admin-managed `ContactRecipient` rows; `CONTACT_EMAIL_TO` is comma-separated fallback only (default `info@statzcorp.com`) | `apps/contact/`, `statzcorp/settings/base.py`, `.env.example` |

> Not yet established. Do not assume — confirm with Dion before acting: formal product-owner vs. developer split; production Azure subscription/App Service names; who approves content vs. infrastructure changes.
