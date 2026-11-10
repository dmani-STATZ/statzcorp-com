import logging
from dataclasses import dataclass
from datetime import datetime

from django.core.cache import cache
from django.utils import timezone

from apps.public.inventory_presenters import present_public_inventory_item
from apps.supplier_portal.statzweb_client import (
    StatzWebAPIError,
    fetch_public_inventory_page,
)

logger = logging.getLogger(__name__)

FRESH_KEY = 'public_inventory:fresh:v1'
LAST_GOOD_KEY = 'public_inventory:last_good:v1'
FRESH_TTL = 900
LAST_GOOD_TTL = 86400
PAGE_SIZE = 200
MAX_PAGES = 25


class _InvalidInventoryPage(Exception):
    """STATZWeb returned a page that is not the documented list shape."""


@dataclass(frozen=True)
class InventorySnapshot:
    items: list[dict]
    fetched_at: datetime | None
    is_stale: bool
    available: bool


def _sort_key(item):
    digits = item['nsn_digits']
    return (not digits, digits, item['description'].lower(), item['id'])


def _page_results(payload):
    if not isinstance(payload, dict):
        raise _InvalidInventoryPage()
    results = payload.get('results')
    if not isinstance(results, list):
        raise _InvalidInventoryPage()
    return results


def _collect_items():
    first = fetch_public_inventory_page(1, PAGE_SIZE)
    if not isinstance(first, dict):
        raise _InvalidInventoryPage()
    num_pages = first.get('num_pages')
    if isinstance(num_pages, bool) or not isinstance(num_pages, int) or num_pages < 0:
        raise _InvalidInventoryPage()
    collected = list(_page_results(first))
    if num_pages > MAX_PAGES:
        logger.warning('public_inventory_truncated num_pages=%s', num_pages)
    last_page = min(num_pages, MAX_PAGES)
    for page in range(2, last_page + 1):
        collected.extend(_page_results(fetch_public_inventory_page(page, PAGE_SIZE)))

    items = []
    for raw in collected:
        presented = present_public_inventory_item(raw)
        if presented is not None and presented['quantity'] != 0:
            items.append(presented)
    items.sort(key=_sort_key)
    return items


def _snapshot_from_cache(payload, *, is_stale):
    if not isinstance(payload, dict):
        return None
    items = payload.get('items')
    if not isinstance(items, list):
        return None
    fetched_at = payload.get('fetched_at')
    if not isinstance(fetched_at, datetime):
        fetched_at = None
    return InventorySnapshot(
        items=list(items),
        fetched_at=fetched_at,
        is_stale=is_stale,
        available=True,
    )


def get_public_inventory_snapshot() -> InventorySnapshot:
    fresh = _snapshot_from_cache(cache.get(FRESH_KEY), is_stale=False)
    if fresh is not None:
        return fresh
    try:
        items = _collect_items()
    except (StatzWebAPIError, _InvalidInventoryPage) as exc:
        logger.warning('public_inventory_fetch_failed %s', type(exc).__name__)
        last_good = _snapshot_from_cache(cache.get(LAST_GOOD_KEY), is_stale=True)
        if last_good is not None:
            return last_good
        return InventorySnapshot(
            items=[],
            fetched_at=None,
            is_stale=False,
            available=False,
        )
    fetched_at = timezone.now()
    payload = {'items': items, 'fetched_at': fetched_at}
    cache.set(FRESH_KEY, payload, FRESH_TTL)
    cache.set(LAST_GOOD_KEY, payload, LAST_GOOD_TTL)
    return InventorySnapshot(
        items=items,
        fetched_at=fetched_at,
        is_stale=False,
        available=True,
    )
