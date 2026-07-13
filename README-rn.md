# STATZ Corporation Website — Release Notes

## 2026-07-13
### Added
- Added video hosting via Azure Blob Storage — staff can now upload promotional videos through Django admin, with public shareable landing pages for use in emails and embeddable players for other site pages.
- `startup.sh` — Azure App Service (Linux) startup command that runs collectstatic, applies migrations, and launches gunicorn bound to Azure's injected $PORT.
- New **Resources** section at `/resources/` with guides for CAGE Code registration, the Joint Certification Program (DD Form 2345), and shipping/packaging preparation.
### Changed
- Site-wide brand palette migrated from red (#c9222a) to deep navy (#1a2540) with military gold accents (#d4af37), per the 2026 redesign plan.
- Django messages styling moved from inline template styles into the shared stylesheet.
### Fixed
- `startup.sh` now refuses to start unless `DJANGO_SETTINGS_MODULE=statzcorp.settings.production`, preventing silent fallback to local settings (`DEBUG=True`) when the Azure App Setting is missing.
