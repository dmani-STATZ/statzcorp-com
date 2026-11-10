"""TEMPORARY staff diagnostic for the public inventory STATZWeb connection.

Remove this module, InventoryConnectionCheckView, its URL, its template,
and the staff button on the inventory page once the connection is confirmed.
"""
import urllib.error
import urllib.parse

from django.conf import settings
from django.core.cache import cache

from apps.public.inventory_presenters import present_public_inventory_item
from apps.public.inventory_service import FRESH_KEY, LAST_GOOD_KEY
from apps.supplier_portal.statzweb_client import (
    StatzWebHTTPError,
    StatzWebNotConfigured,
    StatzWebUnavailable,
    fetch_public_inventory_page,
)

_REQUIRED_PATH = '/api/inventory/v1'


def _redact(text, secrets):
    cleaned = ' '.join(str(text).split())
    for secret in secrets:
        if secret and secret in cleaned:
            cleaned = cleaned.replace(secret, '[redacted]')
    return cleaned[:240]


def _scheme_host(parsed):
    if not parsed.scheme or not parsed.hostname:
        return ''
    port = f':{parsed.port}' if parsed.port else ''
    return f'{parsed.scheme}://{parsed.hostname}{port}'


def _cache_summary(key):
    payload = cache.get(key)
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        return {'present': False, 'item_count': 0, 'fetched_at': None}
    return {
        'present': True,
        'item_count': len(payload['items']),
        'fetched_at': payload.get('fetched_at'),
    }


def _interpret_http(status):
    if status == 401:
        return (
            'STATZWeb rejected the signature. Check INVENTORY_API_KEY, '
            'INVENTORY_API_HMAC_SECRET, and that this server\'s clock is '
            'within 5 minutes of STATZWeb.'
        )
    if status == 403:
        return (
            'STATZWeb or a firewall returned 403. The inventory key may not be '
            'allowed, or this server\'s outbound IP may be blocked.'
        )
    if status == 404:
        return (
            'STATZWeb returned 404. INVENTORY_API_BASE_URL is probably pointed '
            'at the wrong path.'
        )
    if status == 400:
        return 'STATZWeb returned 400. The page request was rejected as invalid.'
    return f'STATZWeb returned HTTP {status}.'


def run_inventory_connection_check():
    """One page-1 probe plus cache state. Safe to render to staff."""
    base_url = settings.INVENTORY_API_BASE_URL or ''
    api_key = settings.INVENTORY_API_KEY or ''
    secret = settings.INVENTORY_API_HMAC_SECRET or ''
    secrets = (api_key, secret, settings.SUPPLIER_PORTAL_API_KEY or '', settings.SUPPLIER_PORTAL_HMAC_SECRET or '')
    parsed = urllib.parse.urlparse(base_url)
    normalized_path = urllib.parse.urlparse(base_url.rstrip('/')).path if base_url else ''
    path_ok = normalized_path == _REQUIRED_PATH
    same_key = bool(api_key) and api_key == (settings.SUPPLIER_PORTAL_API_KEY or '')
    same_secret = bool(secret) and secret == (settings.SUPPLIER_PORTAL_HMAC_SECRET or '')

    problems = []
    if not base_url:
        problems.append('INVENTORY_API_BASE_URL is empty. The Supplier Portal base URL is not used.')
    elif not path_ok:
        problems.append(
            'INVENTORY_API_BASE_URL must be the full inventory base and its path '
            'must be /api/inventory/v1/. A Supplier Portal URL will not work.'
        )
    if not api_key:
        problems.append('INVENTORY_API_KEY is empty.')
    elif same_key:
        problems.append('INVENTORY_API_KEY is the same value as SUPPLIER_PORTAL_API_KEY. Inventory needs its own key.')
    if not secret:
        problems.append('INVENTORY_API_HMAC_SECRET is empty.')
    elif same_secret:
        problems.append(
            'INVENTORY_API_HMAC_SECRET is the same value as SUPPLIER_PORTAL_HMAC_SECRET. '
            'Inventory needs its own secret.'
        )

    report = {
        'ok': False,
        'problems': problems,
        'summary': '',
        'http_status': None,
        'exception_class': '',
        'detail': '',
        'raw_count': None,
        'listed_count': None,
        'zero_quantity_count': None,
        'dropped_count': None,
        'num_pages': None,
        'base_url_configured': bool(base_url),
        'base_url_scheme_host': _scheme_host(parsed),
        'base_url_path': parsed.path,
        'path_ok': path_ok,
        'api_key_present': bool(api_key),
        'api_key_length': len(api_key),
        'hmac_secret_present': bool(secret),
        'hmac_secret_length': len(secret),
        'same_key_as_supplier_portal': same_key,
        'same_secret_as_supplier_portal': same_secret,
        'fresh_cache': _cache_summary(FRESH_KEY),
        'last_good_cache': _cache_summary(LAST_GOOD_KEY),
        'probed': False,
    }

    if not (base_url and api_key and secret and path_ok):
        report['summary'] = 'The inventory API was not called.'
        return report

    report['probed'] = True
    try:
        payload = fetch_public_inventory_page(1, 200)
    except StatzWebHTTPError as exc:
        report['http_status'] = exc.status
        report['exception_class'] = type(exc).__name__
        report['summary'] = _interpret_http(exc.status)
        report['problems'].insert(0, report['summary'])
        return report
    except StatzWebNotConfigured as exc:
        report['exception_class'] = type(exc).__name__
        report['detail'] = _redact(exc, secrets)
        report['summary'] = report['detail']
        if report['summary'] not in report['problems']:
            report['problems'].insert(0, report['summary'])
        return report
    except StatzWebUnavailable as exc:
        report['exception_class'] = type(exc).__name__
        cause = exc.__cause__
        reason = ''
        if isinstance(cause, urllib.error.URLError) and not isinstance(cause, urllib.error.HTTPError):
            reason = _redact(getattr(cause, 'reason', ''), secrets)
        report['detail'] = reason or type(exc).__name__
        report['summary'] = (
            'Could not reach STATZWeb. The host in INVENTORY_API_BASE_URL may be '
            'wrong, or the network path is blocked.'
        )
        if reason:
            report['summary'] = f"{report['summary']} ({reason})"
        report['problems'].insert(0, report['summary'])
        return report
    except Exception as exc:
        report['exception_class'] = type(exc).__name__
        report['summary'] = f'The connection check failed ({type(exc).__name__}).'
        report['problems'].insert(0, report['summary'])
        return report

    results = payload.get('results') if isinstance(payload, dict) else None
    if not isinstance(results, list):
        report['exception_class'] = 'ValueError'
        report['summary'] = 'STATZWeb returned 200, but the body was not an inventory page.'
        report['problems'].insert(0, report['summary'])
        return report

    listed = zero_quantity = dropped = 0
    for raw in results:
        presented = present_public_inventory_item(raw)
        if presented is None:
            dropped += 1
        elif presented['quantity'] == 0:
            zero_quantity += 1
        else:
            listed += 1
    num_pages = payload.get('num_pages')
    report.update({
        'http_status': 200,
        'raw_count': len(results),
        'listed_count': listed,
        'zero_quantity_count': zero_quantity,
        'dropped_count': dropped,
        'num_pages': num_pages if isinstance(num_pages, int) and not isinstance(num_pages, bool) else None,
    })
    if listed:
        report['ok'] = True
        report['summary'] = (
            f'Connection works. Page 1 returned {len(results)} items and '
            f'{listed} can be listed.'
        )
    elif results:
        report['summary'] = (
            f'STATZWeb accepted the request and returned {len(results)} items on page 1, '
            f'but none can be listed ({zero_quantity} have quantity 0, {dropped} were malformed).'
        )
        report['problems'].append(report['summary'])
    else:
        report['summary'] = (
            'STATZWeb accepted the request and returned no public items. '
            'An item appears here only when Show on public website is on and quantity is above 0.'
        )
        report['problems'].append(report['summary'])

    fresh = report['fresh_cache']
    if fresh['present'] and fresh['item_count'] == 0 and listed:
        note = (
            'The public page is still holding an empty snapshot from the last 15 minutes. '
            'This check does not clear it. Reload /inventory/ after the snapshot expires.'
        )
        report['problems'].append(note)
    elif fresh['present'] and not listed:
        report['problems'].append(
            'The public page reads the cached snapshot, not this check. '
            'An empty snapshot is reused for 15 minutes.'
        )
    return report
