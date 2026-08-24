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
_MAX_ERROR_BODY_BYTES = 8192
_MAX_ERROR_BODY_CHARS = 600


class StatzWebAPIError(Exception):
    """Base class for all Supplier Portal API client errors."""


class StatzWebNotConfigured(StatzWebAPIError):
    """SUPPLIER_PORTAL_API_BASE_URL / _API_KEY / _HMAC_SECRET missing."""


class StatzWebUnavailable(StatzWebAPIError):
    """Network failure, timeout, or an unexpected non-2xx/404 response."""


class StatzWebHTTPError(StatzWebUnavailable):
    """
    Non-404 HTTP response from STATZWeb (or an intervening proxy/WAF).

    Carries structured diagnostic fields so callers can distinguish application
    contract errors from non-JSON infrastructure responses. Safe to render:
    never includes API key or HMAC secret material.
    """

    def __init__(
        self,
        *,
        status,
        request_url,
        content_type='',
        body_snippet='',
        error_code=None,
        error_message=None,
        method='GET',
        path='',
    ):
        self.status = status
        self.request_url = request_url
        self.content_type = content_type or ''
        self.body_snippet = body_snippet or ''
        self.error_code = error_code
        self.error_message = error_message
        self.method = method
        self.path = path or urllib.parse.urlparse(request_url).path
        super().__init__(str(self))

    def __str__(self):
        ct = self.content_type or '(none)'
        return (
            f"STATZWeb API returned HTTP {self.status} for "
            f"{self.method} {self.path} (content-type: {ct})"
        )


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
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'statzcorp-com/1.0 (+supplier-portal-client)')
    if body_bytes:
        req.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        raw = exc.read(_MAX_ERROR_BODY_BYTES)
        content_type = ''
        if exc.headers is not None:
            content_type = exc.headers.get('Content-Type', '') or ''
        body_snippet = raw.decode('utf-8', errors='replace')[:_MAX_ERROR_BODY_CHARS]
        payload = {}
        error_code = None
        error_message = None
        try:
            payload = json.loads(raw) if raw else {}
            err = payload.get('error') if isinstance(payload, dict) else None
            if isinstance(err, dict):
                error_code = err.get('code')
                error_message = err.get('message')
        except (json.JSONDecodeError, TypeError, ValueError):
            payload = {}
        if exc.code == 404:
            return 404, payload
        raise StatzWebHTTPError(
            status=exc.code,
            request_url=full_url,
            content_type=content_type,
            body_snippet=body_snippet,
            error_code=error_code,
            error_message=error_message,
            method=method.upper(),
            path=path,
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


def get_supplier_contracts(cage_code):
    """
    GET /suppliers/{cage_code}/contracts/

    Returns {"contracts": [...]} on success, or None if STATZWeb has no supplier
    for that CAGE code (unknown or archived — a real "doesn't exist", matching
    verify_supplier; distinct from StatzWebUnavailable/StatzWebNotConfigured,
    which mean the lookup itself couldn't be performed).

    Returns the raw parsed JSON. Presentation/allowlisting belongs in
    presenters.present_supplier_contracts. See
    docs/supplier-portal-api-contract.md §4.4.
    """
    path = f"/suppliers/{urllib.parse.quote(cage_code, safe='')}/contracts/"
    status, data = _request('GET', path)
    if status == 404:
        return None
    return data


def get_supplier(cage_code):
    """
    GET /suppliers/{cage_code}/

    Returns the supplier profile on success, or None if STATZWeb has no active
    supplier for that CAGE code.
    """
    path = f"/suppliers/{urllib.parse.quote(cage_code, safe='')}/"
    status, data = _request('GET', path)
    if status == 404:
        return None
    return data


def get_document_download_url(cage_code, document_id):
    """
    GET /suppliers/{cage_code}/documents/{document_id}/download/

    Returns the short-lived document URL on success, or None if the document
    does not exist for this supplier.
    """
    try:
        document_id = int(document_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("document_id must be an integer") from exc
    path = (
        f"/suppliers/{urllib.parse.quote(cage_code, safe='')}/"
        f"documents/{document_id}/download/"
    )
    status, data = _request('GET', path)
    if status == 404:
        return None
    url = data.get('url') if isinstance(data, dict) else None
    if not isinstance(url, str) or not url.strip():
        raise StatzWebUnavailable(
            "STATZWeb document download response did not contain a URL."
        )
    return url


def send_email(to, subject, body_html):
    """
    POST /send-email/

    STATZWeb sends this via Microsoft Graph (always From
    GRAPH_MAIL_SENDER_CONTRACT) — direct SMTP to external supplier addresses
    isn't reliable from GCCH direct-send, so all supplier-facing portal email
    (set-password links, etc.) routes through here instead of Django's
    send_mail. Body must be exactly {to, subject, body} — STATZWeb rejects
    (403) any extra key, so don't add fields here without updating that view.

    Raises StatzWebAPIError on failure (bad payload, Graph failure, network
    issue) — callers decide how to surface that to the user.
    """
    payload = json.dumps({'to': to, 'subject': subject, 'body': body_html}).encode('utf-8')
    status, data = _request('POST', '/send-email/', body_bytes=payload)
    if status != 200 or not data.get('ok'):
        raise StatzWebUnavailable(f"send-email did not confirm success: {data}")
    return True
