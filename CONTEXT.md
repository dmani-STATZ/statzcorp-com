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
| Contact form → DB + email notification | Done | `apps/contact/` |
| Surveys with classification field + public manager | Done | `apps/surveys/` |
| Admin for contact messages and surveys | Done | `apps/*/admin.py` |
| Custom site chrome + CSS/JS | Done | `templates/base.html`, `static/css/style.css`, `static/js/main.js` |
| Env template for Azure/GCCH-oriented deploy | Documented | `.env.example`, `requirements.txt` comments |
| Azure App Service (Linux) startup script | Done | `startup.sh` (collectstatic → migrate → gunicorn on `$PORT`) |
| Redesign / feature roadmap | Written, not implemented as code | `rebuild_migration_plan.md` |
| Resources guides (CAGE / JCP / shipping) | Done | `public:resources`, `templates/public/resources.html`, nav/footer in `templates/base.html` |
| Brand palette navy + gold | Done | `static/css/style.css` `:root` (`--primary`, `--accent`, …) |

**Frontend styling decision (owner-stated):** Stick with project CSS in `static/css/style.css`. No Tailwind. No Bootstrap. No django-crispy-forms. Keep CSS in templates minimal; prefer classes defined in the shared stylesheet. Crispy/Bootstrap packages were removed from `requirements.txt` and `statzcorp/settings/base.py` with owner approval.

**In progress / transitional:**

- None currently tracked for visual identity (navy/gold palette applied 2026-07-13).

**Not started (roadmap only — `rebuild_migration_plan.md`):**

- `NewsPost` model / news engine
- Microsoft Bookings embeds
- Content rewrites (NSN/FSC emphasis, condensed history, team group-photo approach, cert PDF downloads)
- LinkedIn / video production program (mostly off-site)
- Migrate database from SQLite to Microsoft SQL Server (MSSQL) — packages/settings only stubbed in comments

**Legacy / non-Django leftovers:**

- Root `css/` and `js/` — tracked; byte-identical to `static/css` and `static/js`; not referenced by Django templates.
- `php/`, `config/`, `composer.json` — gitignored as “Legacy static-site files”; may exist on a developer machine but are not part of the git tree.

**Missing tooling:** No README, no automated tests, no linter config, no CI workflows, no full Azure pipeline / App Service infrastructure-as-code in-repo. Azure Linux App Service startup is covered by checked-in `startup.sh` (set as Startup Command in the portal / CLI); ops must still configure App Settings (`DJANGO_SETTINGS_MODULE`, secrets, hosts, SMTP).

## Architecture Overview

```
Browser
  → Django URLConf (statzcorp/urls.py)
       → apps.public     TemplateViews → templates/public/*
       → apps.contact    FormView → ContactMessage DB + email to CONTACT_EMAIL_TO
       → apps.surveys    List/detail → Survey/Question/Submission/Answer
       → /admin/         Django admin
  ← templates/base.html + static/ (WhiteNoise in middleware for static files)
```

**Data stores:**

- **Current:** SQLite via `statzcorp/settings/base.py` defaults / `.env.example` (`django.db.backends.sqlite3`, file `db.sqlite3`, gitignored).
- **Planned later:** Microsoft SQL Server (MSSQL). Transition notes live in `.env.example` and commented deps in `requirements.txt` (`mssql-django`, `pyodbc`). Not configured yet.
- **Not used:** PostgreSQL — removed from project guidance and deps (owner-stated).

**Email:** Console backend forced in `statzcorp/settings/local.py`. Production uses SMTP settings from env (Office 365 host defaults in `base.py` / `.env.example`).

**Auth for public site:** Anonymous public pages. Optional `Submission.user` FK if authenticated. Entra ID / MSAL packages are commented out in `requirements.txt` (“add when ready for internal views”) — not active.

**Deeper docs:** Product/design roadmap → `rebuild_migration_plan.md`. Agent operating rules → `AGENTS.md`.

## Terminology / Glossary

| Term | Meaning in this project |
|------|-------------------------|
| **SDVOSB** | Service-Disabled Veteran-Owned Small Business — company designation shown site-wide |
| **CAGE** | Commercial and Government Entity code; STATZ value `3WGD1` |
| **CMMC** | Cybersecurity Maturity Model Certification — referenced in site badges/content and roadmap |
| **CUI / CTI / CDI** | Controlled Unclassified Information / Controlled Technical Information / Covered Defense Information — values of `security_classification` on survey models; must not appear on public survey surfaces |
| **`public_objects`** | Custom manager on `ClassifiedModel` that excludes CUI/CTI/CDI (`apps/surveys/models.py`) |
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
5. **Video asset not in git.** `*.mp4` ignored; commit message documents removing a large video from the initial commit.
6. **No automated tests or CI.** Confirmed by absence of test modules and `.github/workflows`.
7. **MSSQL migration not implemented.** Only documented as future in `.env.example` / `requirements.txt` comments.

## Stakeholders / Points of Contact

| Role | Who | Source |
|------|-----|--------|
| Primary technical / IT & Manufacturing Operations contact for this site | **Dion** | `rebuild_migration_plan.md` (Bookings: “Dion (IT & Manufacturing Operations)”); GitHub remote org/user `dmani-STATZ`; local workspace owner |
| Accounting & Contract Administration (Bookings targets in plan) | Jenny / Chad | `rebuild_migration_plan.md` only — not encoded in app config |
| Public contact inbox (runtime) | `CONTACT_EMAIL_TO` (default `info@statzcorp.com`) | `statzcorp/settings/base.py`, `.env.example` |

> Not yet established. Do not assume — confirm with Dion before acting: formal product-owner vs. developer split; production Azure subscription/App Service names; who approves content vs. infrastructure changes.
