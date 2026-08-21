"""
Ping STATZWeb's Supplier Portal API and print connection diagnostics.

Runnable from the Azure Kudu SSH console so the outbound-IP path can be tested
from inside the App Service without a browser session or staff login.
"""
from django.core.management.base import BaseCommand

from apps.supplier_portal.views import (
    CONNECTION_TEST_CAGE_CODE,
    run_api_connection_test,
)


class Command(BaseCommand):
    help = (
        "Probe STATZWeb Supplier Portal API connectivity (same diagnostics as "
        "the staff-only /supplier-portal/api-test/ page). Never prints secrets."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--cage',
            default=CONNECTION_TEST_CAGE_CODE,
            help=(
                f"CAGE code to verify (default: {CONNECTION_TEST_CAGE_CODE} — "
                "well-formed, expected not to exist)."
            ),
        )

    def handle(self, *args, **options):
        cage = options['cage']
        result = run_api_connection_test(cage)
        diagnostics = result['diagnostics']

        self.stdout.write(f"CAGE: {cage}")
        self.stdout.write(f"base_url_configured: {diagnostics['base_url_configured']}")
        self.stdout.write(f"base_url_scheme_host: {diagnostics['base_url_scheme_host'] or '(empty)'}")
        self.stdout.write(f"base_url_path: {diagnostics['base_url_path'] or '(empty)'}")
        self.stdout.write(
            f"base_url_has_expected_prefix: {diagnostics['base_url_has_expected_prefix']}"
        )
        self.stdout.write(f"request_url: {diagnostics['request_url'] or '(empty)'}")
        self.stdout.write(
            f"api_key_present: {diagnostics['api_key_present']} "
            f"(length {diagnostics['api_key_length']})"
        )
        self.stdout.write(
            f"hmac_secret_present: {diagnostics['hmac_secret_present']} "
            f"(length {diagnostics['hmac_secret_length']})"
        )
        self.stdout.write(f"http_status: {result['http_status']!s}")
        self.stdout.write(f"content_type: {result['content_type'] or '(none)'}")
        self.stdout.write(f"error_code: {result['error_code'] or '(none)'}")
        self.stdout.write(f"error_message: {result['error_message'] or '(none)'}")

        if result.get('body_snippet'):
            self.stdout.write("body_snippet:")
            self.stdout.write(result['body_snippet'][:600])

        interpretation = result.get('interpretation') or ''
        if result['success']:
            self.stdout.write(self.style.SUCCESS(interpretation))
            return

        if result['http_status'] in (401, 403):
            self.stdout.write(self.style.ERROR(interpretation))
        else:
            self.stdout.write(self.style.WARNING(interpretation or result.get('error') or 'Failed'))
        if result.get('error'):
            self.stdout.write(self.style.ERROR(result['error']))
        raise SystemExit(1)
