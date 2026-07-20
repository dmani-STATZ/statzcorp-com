"""
Thin client for the STATZWeb Supplier Portal API (docs/supplier-portal-api-contract.md).

Signs every request with X-API-Key + HMAC-SHA256 (X-Timestamp/X-Signature) per
suppliers/portal/auth.py on the STATZWeb side. Uses stdlib urllib only — this
is a handful of low-frequency server-to-server calls, not worth a new dependency.
"""
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

DEFAULT_TIMEOUT = 8


class StatzWebAPIError(Exception):
    """Base class for all Supplier Portal API client errors."""


class StatzWebNotConfigured(StatzWebAPIError):
    """SUPPLIER_PORTAL_API_BASE_URL / _API_KEY / _HMAC_SECRET missing."""


class StatzWebUnavailable(StatzWebAPIError):
    """Network failure, timeout, or an unexpected non-2xx/404 response."""


def _canonical_string(method, path, timestamp, body_bytes):
    body_text = body_bytes.decode('utf-8') if body_bytes else ''
    return f"{method.upper()}\n{path}\n{timestamp}\n{body_text}"


def _sign(secret, canonical_string):
    return hmac.new(
        secret.encode('utf-8'),
        canonical_string.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def _request(method, path, body_bytes=b'', timeout=DEFAULT_TIMEOUT):
    base_url = settings.SUPPLIER_PORTAL_API_BASE_URL
    api_key = settings.SUPPLIER_PORTAL_API_KEY
    secret = settings.SUPPLIER_PORTAL_HMAC_SECRET
    if not (base_url and api_key and secret):
        raise StatzWebNotConfigured(
            "Supplier Portal API is not configured — set SUPPLIER_PORTAL_API_BASE_URL, "
            "SUPPLIER_PORTAL_API_KEY, and SUPPLIER_PORTAL_HMAC_SECRET."
        )

    full_url = base_url.rstrip('/') + path
    request_path = urllib.parse.urlparse(full_url).path

    timestamp = str(int(time.time()))
    signed_body = b'' if method.upper() == 'GET' else body_bytes
    signature = _sign(secret, _canonical_string(method, request_path, timestamp, signed_body))

    req = urllib.request.Request(
        full_url,
        data=body_bytes if method.upper() != 'GET' else None,
        method=method,
    )
    req.add_header('X-API-Key', api_key)
    req.add_header('X-Timestamp', timestamp)
    req.add_header('X-Signature', signature)
    if body_bytes:
        req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read())
        except Exception:
            payload = {}
        if exc.code == 404:
            return 404, payload
        raise StatzWebUnavailable(
            f"STATZWeb API returned HTTP {exc.code} for {method} {path}: "
            f"{payload.get('error', {}).get('message', '(no message)')}"
        ) from exc
    except urllib.error.URLError as exc:
        raise StatzWebUnavailable(f"Could not reach STATZWeb API: {exc.reason}") from exc


def verify_supplier(cage_code):
    """
    GET /suppliers/{cage_code}/verify/

    Returns {"cage_code", "name", "is_active", "contact_email"} on success,
    or None if STATZWeb has no supplier for that CAGE code (a real "doesn't
    exist" — distinct from StatzWebUnavailable/StatzWebNotConfigured, which
    mean the lookup itself couldn't be performed).
    """
    path = f"/suppliers/{urllib.parse.quote(cage_code, safe='')}/verify/"
    status, data = _request('GET', path)
    if status == 404:
        return None
    return data
