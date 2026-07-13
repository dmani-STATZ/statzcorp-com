# AGENTS.md

Operating rules for AI agents in this repo. Read `CONTEXT.md` for project narrative. Do not invent tooling, scripts, or conventions that are not listed here.

## Setup

Verified against `manage.py`, `requirements.txt`, `.env.example`, and a local `.venv` (Python 3.14.3 / Django 5.2.16 observed on this machine).

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edit .env: set DJANGO_SECRET_KEY (required by statzcorp/settings/base.py via decouple).
# manage.py already defaults DJANGO_SETTINGS_MODULE to statzcorp.settings.local
python manage.py migrate
python manage.py runserver
```

- Settings modules: `statzcorp.settings.local` (default in `manage.py`) or `statzcorp.settings.production` (set via env / Azure App Settings — see `.env.example`).
- Secrets live in `.env` (gitignored). Template: `.env.example`.

## Build / Test / Lint

**Configured in repo:**

| Action | Command | Source |
|--------|---------|--------|
| Install deps | `pip install -r requirements.txt` | `requirements.txt` |
| Migrate | `python manage.py migrate` | Django |
| Run local | `python manage.py runserver` | Django |
| System check | `python manage.py check` | Django |
| Collect static | `python manage.py collectstatic` | Django + WhiteNoise (`statzcorp/settings/base.py`) |
| Prod WSGI | `gunicorn` (listed for Azure App Service startup) | `requirements.txt` |
| Azure startup | `startup.sh` (collectstatic → migrate → gunicorn) | Azure App Service Configuration → Startup Command |

**Not configured — do not invent:**

- No test suite (`apps/**/tests.py`, `pytest.ini`, `tox.ini` absent)
- No linter/formatter config (no ruff, flake8, black, pre-commit)
- No CI (no `.github/workflows`)
- No `package.json` / frontend build pipeline
- No `Makefile` / `pyproject.toml` scripts

## Code Conventions

Observed in the current codebase — match these when editing:

- **Layout:** Django project package `statzcorp/`; apps under `apps/` (`public`, `contact`, `surveys`); project templates in `templates/`; served static assets in `static/` (`statzcorp/settings/base.py` `STATICFILES_DIRS`).
- **URLs:** Each app sets `app_name`; root include in `statzcorp/urls.py`. Named routes like `public:index`, `public:resources`, `contact:contact_us`, `surveys:list`.
- **Views:** `apps.public` uses `TemplateView`; `apps.contact` uses `FormView`; `apps.surveys` mixes `ListView` + FBV (`survey_detail_view`).
- **Models:** App models in `apps/*/models.py`. Surveys use abstract `ClassifiedModel` + `public_objects` manager (`apps/surveys/models.py`).
- **Forms:** Contact uses `ModelForm` + honeypot field `website` (`apps/contact/forms.py`). Templates render fields manually with `{% csrf_token %}`. Style forms in `static/css/style.css`.
- **CSS/JS (owner rule):** Custom CSS only. Active stylesheet/script are `static/css/style.css` and `static/js/main.js` (linked from `templates/base.html` via `{% static %}`). Put new styles in `static/css/style.css` (use existing `:root` variables: `--primary`, `--primary-dark`, `--accent`, `--navy`, etc. — `--red` / `--red-dark` no longer exist). Keep `<style>` blocks and inline styles in templates to a minimum — prefer classes in the shared CSS file. Fonts: Oswald + Open Sans via Google Fonts `@import` in `static/css/style.css`.
- **No Tailwind. No Bootstrap. No crispy-forms.** Do not add Tailwind, Bootstrap CSS/JS, django-crispy-forms, utility-class frameworks, or CDN UI kits.
- **Duplicate assets:** Root `css/style.css` and `js/main.js` are byte-identical to the `static/` copies and are also tracked in git. Templates do **not** reference the root copies. Prefer editing `static/` only; do not diverge the duplicates without human direction.
- **Admin:** Models registered in `apps/contact/admin.py` and `apps/surveys/admin.py`.
- **Config:** `python-decouple` `config()` for secrets and env (`statzcorp/settings/base.py`).
- **Database:** SQLite now (`django.db.backends.sqlite3`, default `db.sqlite3`). Plan to migrate to Microsoft SQL Server (MSSQL) later. Do not introduce PostgreSQL.
- **New public page:** Add view in `apps/public/views.py`, route in `apps/public/urls.py`, template under `templates/public/`, styles in `static/css/style.css`, nav link in `templates/base.html` if discoverable.

> Not yet established. Do not assume — confirm with Dion (IT & Manufacturing Operations) before acting: Python formatting/lint rules; whether to delete root `css/` / `js/` duplicates.

## Boundaries — Things Agents Must NOT Do

- Do not commit `.env`, secrets, keys, or credentials (`.gitignore`, `.env.example` warnings).
- Do not commit large video files (`*.mp4` etc. gitignored; initial commit message: “Initial commit without large video file.”).
- Do not revive or extend ignored legacy PHP mail stack for new features: `php/`, `config/`, `composer.json` are gitignored under “Legacy static-site files” (`.gitignore`). They may exist only locally.
- Do not expose CUI / CTI / CDI on public survey routes. Public list/detail must use `Survey.public_objects` and must not submit/display classified questions (`apps/surveys/models.py`, `apps/surveys/views.py`).
- Do not weaken `statzcorp/settings/production.py` SSL/HSTS/secure-cookie settings without explicit human sign-off.
- Do not edit already-shipped migration files in place; add new migrations via `makemigrations`.
- Do not invent test/lint/CI scripts or npm tooling that are not in the repo.
- Do not add Tailwind, Bootstrap, or other CSS/UI frameworks; do not grow inline/`{% block extra_css %}` styles when the rule can live in `static/css/style.css`.
- Do not introduce PostgreSQL or `psycopg*` packages. Database is SQLite now; MSSQL is the planned later target (see `requirements.txt` comments / `.env.example`).
- Do not implement the MSSQL migration (or add `mssql-django` / `pyodbc` as required deps) unless the user asks.
- Do not implement roadmap items from `rebuild_migration_plan.md` unless the user asks for that work.
- Do not commit unless the user explicitly asks.

## Commit / PR Conventions

> Not yet established. Do not assume — confirm with Dion (IT & Manufacturing Operations) before acting.

No `CONTRIBUTING.md`, commit hooks, or CI checks found. Only one commit on `main` exists (`777246d`).

## Known Gotchas

- **`DJANGO_SECRET_KEY` is required** even locally — `statzcorp/settings/base.py` calls `config('DJANGO_SECRET_KEY')` with no default; missing `.env` key crashes startup.
- **Some templates still contain page-local `<style>` blocks** (e.g. `templates/contact/contact-us.html`, `templates/public/accreditations.html`). Django messages styles were moved out of `templates/base.html` into `static/css/style.css`. Migrate remaining template CSS when touching those pages.
- **Survey GET may still load classified questions.** `survey_detail_view` fetches `survey.questions.all()` (default related manager). POST skips CUI/CTI/CDI; GET filtering is incomplete relative to the manager design (`apps/surveys/views.py` comment acknowledges this).
- **Local media directory is absent.** `MEDIA_ROOT` is `BASE_DIR / 'media'` and `media/` is gitignored; directory not present on disk until created.
- **Promo video is local-only.** `static/images/Team-Statz_Fine-Cut_02-16x9-.mp4` is ignored by `*.mp4` in `.gitignore`; templates may reference it but it will not be in git.
- **GCCH / Azure deploy.** Deployment target is documented in `.env.example`, `requirements.txt`, and `production.py` comments. Checked-in `startup.sh` is the Azure App Service (Linux) Startup Command (collectstatic → migrate → gunicorn). No full Azure pipeline / App Service ARM/Bicep config in-repo yet — set Startup Command to `startup.sh` in the portal (or `az webapp config set --startup-file "startup.sh"`).
- **SQLite on Azure App Service is ephemeral unless under `/home`.** Linux App Service only persists `/home`. Default `DB_NAME` (`BASE_DIR/db.sqlite3`) lives in the ephemeral app root and is lost on restart/redeploy. Point `DB_NAME` under `/home` via App Settings for persistence until the planned MSSQL migration. Flagged in `startup.sh`; do not change the DB engine without an explicit request.
- **MSSQL not wired yet.** `.env.example` and `requirements.txt` only document the future MSSQL path; active engine is SQLite.
