import logging
import urllib.parse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

logger = logging.getLogger(__name__)

FORBIDDEN_KEYS = frozenset({
    'probation',
    'probation_on',
    'probation_by',
    'conditional',
    'conditional_on',
    'conditional_by',
    'special_terms',
    'special_terms_on',
    'notes',
    'prime',
    'ppi',
    'iso',
    'allows_gsi',
    'packhouse',
    'files_url',
    'supplier_type',
    'dodaac',
    'archived',
})
PROFILE_FIELDS = (
    ('name', 'Company Name'),
    ('cage_code', 'CAGE Code'),
    ('business_phone', 'Business Phone'),
    ('business_fax', 'Business Fax'),
    ('business_email', 'Business Email'),
    ('website_url', 'Website'),
    ('primary_phone', 'Primary Phone'),
    ('primary_email', 'Primary Email'),
)
ADDRESS_SLOTS = (
    ('billing', 'Billing Address'),
    ('shipping', 'Shipping Address'),
    ('physical', 'Physical Address'),
)
ADDRESS_KEY_ORDER = ('line1', 'line2', 'city', 'state', 'zip', 'country')
CONTACT_FIELDS = (
    ('salutation', 'Salutation'),
    ('name', 'Name'),
    ('title', 'Title'),
    ('phone', 'Phone'),
    ('email', 'Email'),
)
DOC_TYPE_LABELS = {
    'CERT': 'Certification',
    'CLASS': 'Classification',
    'GENERAL': 'General',
}
EXPIRING_SOON_DAYS = 60

_EXCLUDED_ADDRESS_KEYS = frozenset({'id', 'pk'})
_URL_VALIDATOR = URLValidator(schemes=('http', 'https'))


def _parse_date(value):
    if not isinstance(value, str):
        return None
    try:
        return parse_date(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value):
    if not isinstance(value, str):
        return None
    try:
        return parse_datetime(value)
    except (TypeError, ValueError):
        return None


def _date_value(value):
    parsed = _parse_date(value)
    return {
        'value': parsed if parsed is not None else value,
        'is_date': parsed is not None,
        'sort_value': parsed.toordinal() if parsed is not None else None,
    }


def _datetime_value(value):
    parsed = _parse_datetime(value)
    sort_value = None
    if parsed is not None:
        sort_value = (
            parsed.toordinal() * 86400
            + parsed.hour * 3600
            + parsed.minute * 60
            + parsed.second
            + parsed.microsecond / 1_000_000
        )
        offset = parsed.utcoffset()
        if offset is not None:
            sort_value -= offset.total_seconds()
    return {
        'value': parsed if parsed is not None else value,
        'is_datetime': parsed is not None,
        'sort_value': sort_value,
    }


def _expiration_status(parsed_expiration):
    if parsed_expiration is None:
        return 'none', ''
    days_remaining = (parsed_expiration - timezone.localdate()).days
    if days_remaining < 0:
        return 'expired', 'Expired'
    if days_remaining <= EXPIRING_SOON_DAYS:
        return 'soon', 'Expiring soon'
    return 'ok', 'Current'


def _safe_website(value):
    href = None
    if value:
        try:
            _URL_VALIDATOR(value)
            if urllib.parse.urlparse(value).scheme.lower() in {'http', 'https'}:
                href = value
        except (AttributeError, TypeError, ValidationError, ValueError):
            pass
    return {'text': value, 'href': href}


def _address_lines(address):
    if not isinstance(address, dict):
        return []

    remaining_keys = sorted(
        key
        for key in address
        if key not in ADDRESS_KEY_ORDER
        and key not in _EXCLUDED_ADDRESS_KEYS
        and not key.endswith(('_id', '_at', '_on'))
    )
    lines = []
    for key in (*ADDRESS_KEY_ORDER, *remaining_keys):
        value = address.get(key)
        if value is not None and value != '':
            lines.append(value)
    return lines


def _normalize_certification(item):
    if not isinstance(item, dict):
        item = {}
    certified = _date_value(item.get('certification_date'))
    expiration = _date_value(item.get('certification_expiration'))
    status_code, status_label = _expiration_status(
        expiration['value'] if expiration['is_date'] else None
    )
    return {
        'type': item.get('type'),
        'certification_date': certified['value'],
        'certification_date_is_date': certified['is_date'],
        'certification_expiration': expiration['value'],
        'certification_expiration_is_date': expiration['is_date'],
        'expiration_sort_value': expiration['sort_value'],
        'compliance_status': item.get('compliance_status'),
        'status_code': status_code,
        'status_label': status_label,
    }


def _normalize_classification(item):
    if not isinstance(item, dict):
        item = {}
    effective = _date_value(item.get('classification_date'))
    expiration = _date_value(item.get('classification_expiration'))
    status_code, status_label = _expiration_status(
        expiration['value'] if expiration['is_date'] else None
    )
    return {
        'type': item.get('type'),
        'classification_date': effective['value'],
        'classification_date_is_date': effective['is_date'],
        'classification_expiration': expiration['value'],
        'classification_expiration_is_date': expiration['is_date'],
        'expiration_sort_value': expiration['sort_value'],
        'status_code': status_code,
        'status_label': status_label,
    }


def _expiration_sort_key(item):
    sort_value = item['expiration_sort_value']
    return sort_value is None, sort_value or 0


def _normalize_document(item):
    if not isinstance(item, dict):
        item = {}
    uploaded = _datetime_value(item.get('uploaded_on'))
    return {
        'id': item.get('id'),
        'doc_type': item.get('doc_type'),
        'doc_type_label': DOC_TYPE_LABELS.get(item.get('doc_type'), item.get('doc_type')),
        'description': item.get('description'),
        'linked_to': item.get('linked_certification') or item.get('linked_classification'),
        'uploaded_on': uploaded['value'],
        'uploaded_on_is_datetime': uploaded['is_datetime'],
        'uploaded_sort_value': uploaded['sort_value'],
    }


def _document_sort_key(item):
    sort_value = item['uploaded_sort_value']
    return sort_value is None, -(sort_value or 0)


def present_supplier(raw):
    cage_code = raw.get('cage_code') if isinstance(raw, dict) else None
    raw = raw if isinstance(raw, dict) else {}
    forbidden = sorted(
        key
        for key in raw
        if key in FORBIDDEN_KEYS or key.startswith('archived')
    )
    if forbidden:
        logger.warning(
            "STATZWeb supplier payload contained forbidden keys for CAGE %r: %s",
            cage_code,
            ', '.join(forbidden),
        )

    profile_fields = []
    for key, label in PROFILE_FIELDS:
        value = raw.get(key)
        profile_fields.append({
            'key': key,
            'label': label,
            'value': _safe_website(value) if key == 'website_url' else value,
        })

    raw_addresses = raw.get('addresses')
    raw_addresses = raw_addresses if isinstance(raw_addresses, dict) else {}
    addresses = []
    for key, label in ADDRESS_SLOTS:
        lines = _address_lines(raw_addresses.get(key))
        if lines:
            addresses.append({'key': key, 'label': label, 'lines': lines})

    contacts = []
    raw_contacts = raw.get('contacts')
    for item in raw_contacts if isinstance(raw_contacts, list) else []:
        item = item if isinstance(item, dict) else {}
        contact = {key: item.get(key) for key, _label in CONTACT_FIELDS}
        categories = item.get('categories')
        contact['categories'] = (
            [str(category) for category in categories if category not in (None, '')]
            if isinstance(categories, list)
            else []
        )
        contacts.append(contact)
    contacts.sort(key=lambda item: str(item.get('name') or '').casefold())

    raw_certifications = raw.get('certifications')
    certifications = [
        _normalize_certification(item)
        for item in (
            raw_certifications if isinstance(raw_certifications, list) else []
        )
    ]
    certifications.sort(key=_expiration_sort_key)

    raw_classifications = raw.get('classifications')
    classifications = [
        _normalize_classification(item)
        for item in (
            raw_classifications if isinstance(raw_classifications, list) else []
        )
    ]
    classifications.sort(key=_expiration_sort_key)

    raw_documents = raw.get('documents')
    documents = [
        _normalize_document(item)
        for item in (
            raw_documents if isinstance(raw_documents, list) else []
        )
    ]
    documents.sort(key=_document_sort_key)

    return {
        'name': raw.get('name'),
        'cage_code': raw.get('cage_code'),
        'profile_fields': profile_fields,
        'addresses': addresses,
        'contacts': contacts,
        'certifications': certifications,
        'classifications': classifications,
        'documents': documents,
    }


def _plain_text(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _present_clin(item):
    if not isinstance(item, dict):
        return None
    clin_number = _plain_text(item.get('clin_number'))
    if clin_number is None:
        return None
    return {
        'clin_number': clin_number,
        'nsn': _plain_text(item.get('nsn')),
        'po_number': _plain_text(item.get('po_number')),
        'due_date': _plain_text(item.get('due_date')),
    }


def _present_contract(item):
    if not isinstance(item, dict):
        return None
    contract_number = _plain_text(item.get('contract_number'))
    if contract_number is None:
        return None
    raw_clins = item.get('clins')
    clins = []
    for clin in raw_clins if isinstance(raw_clins, list) else []:
        presented = _present_clin(clin)
        if presented is not None:
            clins.append(presented)
    return {
        'contract_number': contract_number,
        'award_date': _plain_text(item.get('award_date')),
        'po_number': _plain_text(item.get('po_number')),
        'status': _plain_text(item.get('status')),
        'clins': clins,
    }


def present_supplier_contracts(raw_data):
    """
    Allowlist STATZWeb contract payloads for template context.

    Reads only contract_number, award_date, po_number, status, and per-CLIN
    clin_number, nsn, po_number, and due_date. Contract-level and CLIN-level
    po_number are distinct fields and are both copied even when they match.
    Skips malformed contract/CLIN entries rather than raising.
    Dollar/price/funding keys are never copied even if STATZWeb sends them.
    """
    if not isinstance(raw_data, dict):
        return []
    raw_contracts = raw_data.get('contracts')
    if not isinstance(raw_contracts, list):
        return []
    contracts = []
    for item in raw_contracts:
        presented = _present_contract(item)
        if presented is not None:
            contracts.append(presented)
    return contracts
