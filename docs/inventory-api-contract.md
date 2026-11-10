# STATZWeb Inventory API Contract (statzcorp-com)

Public, view-only inventory listing. STATZWeb's `inventory/INVENTORY_API.md` is the source of truth.

This site never stores inventory rows. Staff opt an item in on STATZWeb (`is_public=True`). The public page reads a cached snapshot of those items.

## Settings

Azure App Service application settings (statzcorp-com only). Leave them empty until the values exist in STATZWeb. Do not copy the Supplier Portal key or secret.

| App Setting | Role |
|---|---|
| `INVENTORY_API_BASE_URL` | Full base including the path, e.g. `https://<statzweb-host>/api/inventory/v1/` |
| `INVENTORY_API_KEY` | `X-API-Key` |
| `INVENTORY_API_HMAC_SECRET` | HMAC secret for `X-Signature` |

`INVENTORY_API_BASE_URL` is independent of `SUPPLIER_PORTAL_API_BASE_URL`. Never derive one STATZWeb API's base URL from another's setting. The client rejects a base whose path is not exactly `/api/inventory/v1` before any network call, so a Supplier Portal prefix cannot be signed by mistake.

## Request

`GET {INVENTORY_API_BASE_URL}/items/?page=<int>&page_size=<int>`

- `page_size` defaults to 50 on STATZWeb and maxes at 200. This site requests `page_size=200`.
- Signed path: `/api/inventory/v1/items/` (trailing slash, no query string).
- `GET /api/inventory/v1/items/<pk>/` exists on STATZWeb and is not used here.

## Authentication

Same canonical string as the Supplier Portal API, with the inventory key and secret:

`METHOD\npath\ntimestamp\nbody`

- `path` excludes the query string.
- A GET signs an empty body.
- Headers: `X-API-Key`, `X-Timestamp`, `X-Signature`.
- Timestamp window ±300 seconds.
- Signature is hex HMAC-SHA256.

The helpers live in `apps/supplier_portal/statzweb_client.py` (`_canonical_string`, `_sign`). `fetch_public_inventory_page` calls them with the inventory credentials. It does not go through `_request`, which is bound to the Supplier Portal settings.

## 200 body

```json
{"count": 0, "page": 1, "page_size": 200, "num_pages": 1, "results": []}
```

Item keys, exact and complete:

| Key | Type | Null becomes |
|---|---|---|
| `id` | int | item is dropped |
| `nsn` | str | `""` |
| `description` | str | `""` |
| `part_number` | str | `""` |
| `manufacturer` | str | `""` |
| `quantity` | int | `0` (then dropped from the public snapshot) |

Any other key (`purchaseprice`, `totalcost`, `itemlocation`, and anything added later) is ignored. The presenter is an allowlist.

## Errors

| Status | Body |
|---|---|
| 401 | `{"error": {"code": "unauthorized", "message": ...}}` |
| 400 | `{"error": "invalid_parameter"}` |
| 404 | `{"error": "not_found"}` |
| 405 | `{"error": "method_not_allowed"}` |

Every response carries `Cache-Control: no-store`. There is no CORS. The browser never calls this API.

## Snapshot

`apps/public/inventory_service.py` pages until `num_pages` or 25 pages, whichever is smaller. Presenter output is cached under:

| Key | TTL |
|---|---|
| `public_inventory:fresh:v1` | 900 seconds |
| `public_inventory:last_good:v1` | 86400 seconds |

`PublicInventoryListView` reads that snapshot only. Search, filtering, and pagination happen in memory. A failed refresh serves the last-good snapshot with a staleness notice, or an unavailable message when nothing has ever been cached. Partial pages are not cached.
