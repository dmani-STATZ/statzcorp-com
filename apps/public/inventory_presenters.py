PUBLIC_INVENTORY_FIELDS = (
    'id',
    'nsn',
    'description',
    'part_number',
    'manufacturer',
    'quantity',
)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _text(value):
    if isinstance(value, str):
        return value.strip()
    return ''


def _quantity(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return 0
    return value


def _nsn_display(nsn, nsn_digits):
    if len(nsn_digits) == 13:
        return (
            f'{nsn_digits[0:4]}-{nsn_digits[4:6]}-'
            f'{nsn_digits[6:9]}-{nsn_digits[9:13]}'
        )
    return nsn


def present_public_inventory_item(raw: dict) -> dict | None:
    """Allowlist one STATZWeb inventory item. Drop malformed items."""
    if not isinstance(raw, dict):
        return None
    values = {key: raw.get(key) for key in PUBLIC_INVENTORY_FIELDS}
    if not _is_int(values['id']):
        return None
    nsn = _text(values['nsn'])
    nsn_digits = ''.join(ch for ch in nsn if ch.isdigit())
    return {
        'id': values['id'],
        'nsn_display': _nsn_display(nsn, nsn_digits),
        'nsn_digits': nsn_digits,
        'description': _text(values['description']),
        'part_number': _text(values['part_number']),
        'manufacturer': _text(values['manufacturer']),
        'quantity': _quantity(values['quantity']),
    }
