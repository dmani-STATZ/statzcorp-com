import urllib.parse
from datetime import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.utils import timezone

from apps.public.inventory_presenters import present_public_inventory_item
from apps.public.inventory_service import (
    FRESH_KEY,
    FRESH_TTL,
    LAST_GOOD_KEY,
    LAST_GOOD_TTL,
    get_public_inventory_snapshot,
)
from apps.supplier_portal.statzweb_client import (
    StatzWebHTTPError,
    StatzWebNotConfigured,
    StatzWebUnavailable,
    _canonical_string,
    _sign,
    fetch_public_inventory_page,
)

LOC_MEM = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
}


@override_settings(CACHES=LOC_MEM)
class PublicInventoryTestCase(SimpleTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()


def _raw_item(**overrides):
    item = {
        'id': 1,
        'nsn': '1560002194659',
        'description': 'Bolt',
        'part_number': 'P-1',
        'manufacturer': 'ACME',
        'quantity': 4,
    }
    item.update(overrides)
    return item


class PresenterTests(PublicInventoryTestCase):
    def test_allowlist_drops_price_cost_and_location(self):
        presented = present_public_inventory_item(_raw_item(
            purchaseprice='999999.99',
            totalcost='10.00',
            itemlocation='BIN-9',
        ))
        self.assertEqual(
            set(presented),
            {
                'id',
                'nsn_display',
                'nsn_digits',
                'description',
                'part_number',
                'manufacturer',
                'quantity',
            },
        )
        rendered = ' '.join(str(value) for value in presented.values())
        self.assertNotIn('999999.99', rendered)
        self.assertNotIn('BIN-9', rendered)
        self.assertNotIn('purchaseprice', presented)
        self.assertNotIn('totalcost', presented)
        self.assertNotIn('itemlocation', presented)

    def test_id_quantity_and_nsn_rules(self):
        self.assertIsNone(present_public_inventory_item(['not', 'a', 'dict']))
        self.assertIsNone(present_public_inventory_item(_raw_item(id='1')))
        self.assertIsNone(present_public_inventory_item(_raw_item(id=1.5)))
        self.assertIsNone(present_public_inventory_item(_raw_item(id=True)))
        self.assertIsNone(present_public_inventory_item(_raw_item(id=False)))

        self.assertEqual(present_public_inventory_item(_raw_item(quantity=-3))['quantity'], 0)
        self.assertEqual(present_public_inventory_item(_raw_item(quantity='5'))['quantity'], 0)
        self.assertEqual(present_public_inventory_item(_raw_item(quantity=True))['quantity'], 0)
        self.assertEqual(present_public_inventory_item(_raw_item(quantity=False))['quantity'], 0)
        self.assertEqual(present_public_inventory_item(_raw_item(quantity=None))['quantity'], 0)
        self.assertEqual(present_public_inventory_item(_raw_item(quantity=6))['quantity'], 6)

        digits = present_public_inventory_item(_raw_item(nsn='1560002194659'))
        self.assertEqual(digits['nsn_display'], '1560-00-219-4659')
        self.assertEqual(digits['nsn_digits'], '1560002194659')

        dashed = present_public_inventory_item(_raw_item(nsn='3120-01-721-6753'))
        self.assertEqual(dashed['nsn_display'], '3120-01-721-6753')
        self.assertEqual(dashed['nsn_digits'], '3120017216753')

        short = present_public_inventory_item(_raw_item(nsn='123456789012'))
        self.assertEqual(short['nsn_display'], '123456789012')
        self.assertEqual(short['nsn_digits'], '123456789012')

        blank = present_public_inventory_item(_raw_item(
            nsn=None,
            description=12,
            part_number=None,
            manufacturer=False,
        ))
        self.assertEqual(blank['nsn_display'], '')
        self.assertEqual(blank['description'], '')
        self.assertEqual(blank['part_number'], '')
        self.assertEqual(blank['manufacturer'], '')


def _page(num_pages, results, page=1):
    return {
        'count': len(results),
        'page': page,
        'page_size': 200,
        'num_pages': num_pages,
        'results': results,
    }


class ServiceTests(PublicInventoryTestCase):
    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_pages_are_combined_zero_qty_dropped_and_sorted(self, fetch):
        page_one = [
            _raw_item(id=10, nsn='', description='Bravo', quantity=2),
            _raw_item(id=11, nsn='', description='alpha', quantity=2),
            _raw_item(id=12, nsn='', description='Alpha', quantity=2),
            _raw_item(id=13, nsn='2000000000002', description='Zed', quantity=4),
            _raw_item(id=14, nsn='9999999999999', description='Dropped', quantity=0),
            _raw_item(id='nope', description='Bad id'),
            _raw_item(id=True, description='Bool id', quantity=5),
        ]
        page_two = [
            _raw_item(id=15, nsn='1000000000001', description='Mile', quantity=1),
            _raw_item(id=16, nsn='1000000000001', description='able', quantity=8),
            _raw_item(id=17, nsn='3120-01-721-6753', description='Bearing', quantity=3),
        ]

        def side_effect(page, page_size=200):
            self.assertEqual(page_size, 200)
            if page == 1:
                return _page(2, page_one, page=1)
            if page == 2:
                return _page(2, page_two, page=2)
            raise AssertionError(f'unexpected page {page}')

        fetch.side_effect = side_effect
        snapshot = get_public_inventory_snapshot()
        self.assertFalse(snapshot.is_stale)
        self.assertTrue(snapshot.available)
        self.assertEqual(
            [item['id'] for item in snapshot.items],
            [16, 15, 13, 17, 11, 12, 10],
        )
        self.assertNotIn('Dropped', [item['description'] for item in snapshot.items])
        stored = cache.get(FRESH_KEY)
        self.assertEqual([item['id'] for item in stored['items']], [16, 15, 13, 17, 11, 12, 10])
        self.assertNotIn('purchaseprice', stored['items'][0])
        self.assertIsNotNone(cache.get(LAST_GOOD_KEY))

    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_num_pages_above_max_fetches_25_and_logs_truncation(self, fetch):
        calls = []

        def side_effect(page, page_size=200):
            calls.append(page)
            return _page(30, [], page=page)

        fetch.side_effect = side_effect
        with self.assertLogs('apps.public.inventory_service', level='WARNING') as captured:
            snapshot = get_public_inventory_snapshot()
        self.assertEqual(calls, list(range(1, 26)))
        self.assertEqual(len(calls), 25)
        self.assertTrue(snapshot.available)
        self.assertTrue(any('public_inventory_truncated' in line for line in captured.output))
        self.assertTrue(any('num_pages=30' in line for line in captured.output))

    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_page_two_failure_caches_nothing_without_last_good(self, fetch):
        def side_effect(page, page_size=200):
            if page == 1:
                return _page(2, [_raw_item(id=1, description='Page one')])
            raise StatzWebUnavailable('HTTPError')

        fetch.side_effect = side_effect
        with self.assertLogs('apps.public.inventory_service', level='WARNING') as captured:
            snapshot = get_public_inventory_snapshot()
        self.assertFalse(snapshot.available)
        self.assertFalse(snapshot.is_stale)
        self.assertEqual(snapshot.items, [])
        self.assertIsNone(snapshot.fetched_at)
        self.assertIsNone(cache.get(FRESH_KEY))
        self.assertIsNone(cache.get(LAST_GOOD_KEY))
        self.assertTrue(any('public_inventory_fetch_failed' in line for line in captured.output))
        self.assertTrue(any('StatzWebUnavailable' in line for line in captured.output))

    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_failure_returns_stale_last_good(self, fetch):
        fetched_at = timezone.make_aware(datetime(2026, 11, 10, 15, 4))
        kept = present_public_inventory_item(_raw_item(id=9, description='Kept'))
        cache.set(
            LAST_GOOD_KEY,
            {'items': [kept], 'fetched_at': fetched_at},
            LAST_GOOD_TTL,
        )
        fetch.side_effect = StatzWebUnavailable('URLError')
        with self.assertLogs('apps.public.inventory_service', level='WARNING'):
            snapshot = get_public_inventory_snapshot()
        self.assertTrue(snapshot.available)
        self.assertTrue(snapshot.is_stale)
        self.assertEqual(snapshot.items, [kept])
        self.assertEqual(snapshot.fetched_at, fetched_at)
        self.assertIsNone(cache.get(FRESH_KEY))

    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_fresh_cache_skips_the_client(self, fetch):
        fetched_at = timezone.now()
        cache.set(
            FRESH_KEY,
            {'items': [], 'fetched_at': fetched_at},
            FRESH_TTL,
        )
        snapshot = get_public_inventory_snapshot()
        fetch.assert_not_called()
        self.assertTrue(snapshot.available)
        self.assertFalse(snapshot.is_stale)
        self.assertEqual(snapshot.fetched_at, fetched_at)


class _Body:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def read(self, _limit=None):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class ClientTests(PublicInventoryTestCase):
    def _assert_no_call(self, urlopen):
        with self.assertRaises(StatzWebNotConfigured):
            fetch_public_inventory_page(1)
        urlopen.assert_not_called()

    @patch('apps.supplier_portal.statzweb_client.urllib.request.urlopen')
    @override_settings(
        INVENTORY_API_BASE_URL='https://inventory.example/api/inventory/v1/',
        INVENTORY_API_KEY='',
        INVENTORY_API_HMAC_SECRET='test-secret',
    )
    def test_empty_key_makes_no_network_call(self, urlopen):
        self._assert_no_call(urlopen)

    @patch('apps.supplier_portal.statzweb_client.urllib.request.urlopen')
    @override_settings(
        INVENTORY_API_BASE_URL='https://inventory.example/api/inventory/v1/',
        INVENTORY_API_KEY='inventory-key',
        INVENTORY_API_HMAC_SECRET='',
    )
    def test_empty_secret_makes_no_network_call(self, urlopen):
        self._assert_no_call(urlopen)

    @patch('apps.supplier_portal.statzweb_client.urllib.request.urlopen')
    @override_settings(
        INVENTORY_API_BASE_URL='https://h/api/supplier-portal/v1/',
        INVENTORY_API_KEY='inventory-key',
        INVENTORY_API_HMAC_SECRET='test-secret',
    )
    def test_wrong_base_path_makes_no_network_call(self, urlopen):
        self._assert_no_call(urlopen)

    @patch('apps.supplier_portal.statzweb_client.urllib.request.urlopen')
    @override_settings(
        INVENTORY_API_BASE_URL='https://inventory.example/api/inventory/v1',
        INVENTORY_API_KEY='inventory-key',
        INVENTORY_API_HMAC_SECRET='test-secret',
        SUPPLIER_PORTAL_API_BASE_URL='https://supplier.example/api/supplier-portal/v1/',
        SUPPLIER_PORTAL_API_KEY='supplier-key',
        SUPPLIER_PORTAL_HMAC_SECRET='supplier-secret',
    )
    def test_signs_inventory_path_without_the_query(self, urlopen):
        urlopen.return_value = _Body(
            b'{"count":0,"page":3,"page_size":200,"num_pages":0,"results":[]}'
        )
        payload = fetch_public_inventory_page(3, 200)
        self.assertEqual(payload['page'], 3)
        req = urlopen.call_args.args[0]
        parsed = urllib.parse.urlparse(req.full_url)
        self.assertEqual(parsed.path, '/api/inventory/v1/items/')
        self.assertTrue(req.full_url.startswith('https://inventory.example/'))
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(query['page'], ['3'])
        self.assertEqual(query['page_size'], ['200'])
        timestamp = req.get_header('X-timestamp')
        expected = _sign(
            'test-secret',
            _canonical_string('GET', '/api/inventory/v1/items/', timestamp, ''),
        )
        self.assertEqual(req.get_header('X-signature'), expected)
        self.assertEqual(req.get_header('X-api-key'), 'inventory-key')


class PublicInventoryViewTests(PublicInventoryTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

    def _seed(self, items, *, fetched_at=None):
        cache.set(
            FRESH_KEY,
            {
                'items': items,
                'fetched_at': fetched_at or timezone.now(),
            },
            FRESH_TTL,
        )

    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_get_renders_allowlisted_fields_and_post_is_rejected(self, fetch):
        fetch.return_value = _page(1, [_raw_item(
            id=424242,
            description='Bolt <script>alert(1)</script>',
            purchaseprice='999999.99',
            totalcost='999999.99',
            itemlocation='BIN-SECRET',
        )])
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available Inventory')
        self.assertContains(response, '1560-00-219-4659')
        self.assertContains(response, 'Bolt &lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response, '999999.99')
        self.assertNotContains(response, 'BIN-SECRET')
        self.assertNotContains(response, '424242')
        self.assertNotContains(response, '<script>alert(1)</script>')
        posted = self.client.post('/inventory/')
        self.assertEqual(posted.status_code, 405)

    def test_search_truncation_and_invalid_page(self):
        items = [
            present_public_inventory_item(_raw_item(
                id=1,
                nsn='1560002194659',
                description='Brass Fitting',
                part_number='BR-1',
                manufacturer='ACME',
                quantity=2,
            )),
            present_public_inventory_item(_raw_item(
                id=2,
                nsn='9999000000000',
                description='Copper Washer',
                part_number='CU-2',
                manufacturer='OTHER',
                quantity=1,
            )),
        ]
        prefix = 'Q' * 100
        items.append(present_public_inventory_item(_raw_item(
            id=3,
            nsn='',
            description=prefix,
            quantity=1,
        )))
        for offset in range(4, 30):
            items.append(present_public_inventory_item(_raw_item(
                id=offset,
                nsn='',
                description=f'Filler {offset:02d}',
                quantity=1,
            )))
        items.append(present_public_inventory_item(_raw_item(
            id=30,
            nsn='',
            description='Only On Second',
            quantity=1,
        )))
        self._seed(items)

        brass = self.client.get('/inventory/', {'q': 'brass'})
        self.assertContains(brass, 'Brass Fitting')
        self.assertNotContains(brass, 'Copper Washer')

        nsn = self.client.get('/inventory/', {'q': '1560002'})
        self.assertContains(nsn, 'Brass Fitting')
        self.assertContains(nsn, '1560-00-219-4659')
        self.assertNotContains(nsn, 'Copper Washer')

        long_query = prefix + 'NOMATCHTAIL'
        truncated = self.client.get('/inventory/', {'q': long_query})
        self.assertContains(truncated, prefix)
        self.assertNotContains(truncated, 'NOMATCHTAIL')
        self.assertEqual(truncated.context['q'], prefix)

        invalid = self.client.get('/inventory/', {'page': 'abc'})
        self.assertEqual(invalid.context['page_obj'].number, 1)
        self.assertContains(invalid, 'Brass Fitting')
        self.assertNotContains(invalid, 'Only On Second')

    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_unavailable_and_stale_messages(self, fetch):
        fetch.side_effect = StatzWebUnavailable('URLError')
        unavailable = self.client.get('/inventory/')
        self.assertContains(
            unavailable,
            'Our inventory listing is temporarily unavailable. Please contact us for current availability.',
        )
        self.assertContains(unavailable, 'Request a Quote')
        self.assertContains(unavailable, 'href="/contact-us/"')
        self.assertNotContains(
            unavailable,
            'Showing the most recent available listing; it may be out of date.',
        )
        self.assertNotContains(unavailable, 'Listing refreshed')

        cache.clear()
        fetched_at = timezone.make_aware(datetime(2026, 11, 10, 15, 4))
        kept = present_public_inventory_item(_raw_item(id=8, description='Kept Sleeve'))
        cache.set(
            LAST_GOOD_KEY,
            {'items': [kept], 'fetched_at': fetched_at},
            LAST_GOOD_TTL,
        )
        stale = self.client.get('/inventory/')
        self.assertContains(
            stale,
            'Showing the most recent available listing; it may be out of date.',
        )
        self.assertContains(stale, 'Kept Sleeve')
        self.assertContains(stale, 'Nov 10, 2026 3:04 PM')
        self.assertNotContains(
            stale,
            'Our inventory listing is temporarily unavailable. Please contact us for current availability.',
        )


@override_settings(CACHES=LOC_MEM)
class InventoryConnectionCheckTests(TestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.staff = User.objects.create_user(
            'inv-staff',
            'inv-staff@example.com',
            'unused-test-password',
            is_staff=True,
        )

    @patch('apps.public.inventory_service.fetch_public_inventory_page', side_effect=StatzWebUnavailable('URLError'))
    def test_anonymous_gets_403_and_no_button(self, _fetch):
        listing = self.client.get('/inventory/')
        self.assertNotContains(listing, 'Check inventory connection')
        denied = self.client.get('/inventory/connection-check/')
        self.assertEqual(denied.status_code, 403)

    @patch('apps.public.inventory_service.fetch_public_inventory_page')
    def test_staff_listing_has_no_check_button_but_check_page_still_works(self, fetch):
        fetch.side_effect = StatzWebUnavailable('URLError')
        self.client.force_login(self.staff)
        response = self.client.get('/inventory/')
        self.assertNotContains(response, 'Check inventory connection')
        with patch('apps.public.inventory_diagnostics.fetch_public_inventory_page') as probe:
            probe.side_effect = StatzWebUnavailable('URLError')
            check = self.client.get('/inventory/connection-check/')
        self.assertEqual(check.status_code, 200)

    @override_settings(
        INVENTORY_API_BASE_URL='',
        INVENTORY_API_KEY='',
        INVENTORY_API_HMAC_SECRET='',
    )
    @patch('apps.public.inventory_diagnostics.fetch_public_inventory_page')
    def test_empty_settings_explain_the_failure_without_a_call(self, fetch):
        self.client.force_login(self.staff)
        response = self.client.get('/inventory/connection-check/')
        self.assertContains(response, 'INVENTORY_API_BASE_URL is empty')
        self.assertContains(response, 'INVENTORY_API_KEY is empty')
        self.assertContains(response, 'INVENTORY_API_HMAC_SECRET is empty')
        self.assertContains(response, 'The inventory API was not called.')
        fetch.assert_not_called()

    @override_settings(
        INVENTORY_API_BASE_URL='https://inventory.example/api/supplier-portal/v1/',
        INVENTORY_API_KEY='inventory-key',
        INVENTORY_API_HMAC_SECRET='inventory-secret',
    )
    @patch('apps.public.inventory_diagnostics.fetch_public_inventory_page')
    def test_wrong_path_is_reported_without_a_call(self, fetch):
        self.client.force_login(self.staff)
        response = self.client.get('/inventory/connection-check/')
        self.assertContains(response, '/api/inventory/v1/')
        self.assertContains(response, 'The inventory API was not called.')
        fetch.assert_not_called()

    @override_settings(
        INVENTORY_API_BASE_URL='https://inventory.example/api/inventory/v1/',
        INVENTORY_API_KEY='super-secret-key-value',
        INVENTORY_API_HMAC_SECRET='super-secret-hmac-value',
        SUPPLIER_PORTAL_API_KEY='super-secret-key-value',
        SUPPLIER_PORTAL_HMAC_SECRET='other-supplier-secret',
    )
    @patch('apps.public.inventory_diagnostics.fetch_public_inventory_page')
    def test_http_401_and_shared_key_never_render_secrets(self, fetch):
        fetch.side_effect = StatzWebHTTPError(
            status=401,
            request_url='https://inventory.example/api/inventory/v1/items/?page=1',
            method='GET',
            path='/api/inventory/v1/items/',
        )
        self.client.force_login(self.staff)
        response = self.client.get('/inventory/connection-check/')
        self.assertContains(response, 'STATZWeb rejected the signature')
        self.assertContains(response, 'INVENTORY_API_KEY is the same value as SUPPLIER_PORTAL_API_KEY')
        self.assertNotContains(response, 'super-secret-key-value')
        self.assertNotContains(response, 'super-secret-hmac-value')
        self.assertNotContains(response, 'other-supplier-secret')
