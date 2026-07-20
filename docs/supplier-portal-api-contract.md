# Supplier Portal API Contract (STATZWeb → statzcorp-com)

Spec for the API that the STATZWeb/STATZCorp project (owner of the `Supplier`, `Contact`,
`SupplierCertification`, `SupplierClassification`, and `SupplierDocument` models) exposes to the
public site (`statzcorp-com`). `statzcorp-com` hosts supplier login and the portal UI; it holds no
supplier business data of its own and calls this API server-to-server on every portal page load
and edit.

**Status:** Not yet implemented on either side. This document is the spec to build against.

**Audience:** Whoever implements the API on the STATZWeb side, and whoever builds the
`statzcorp-com` API client against it.

---

## 1. Scope

| Phase | Direction | What it covers |
|-------|-----------|-----------------|
| Phase 1 | Read-only | Supplier profile, contacts, certifications, classifications, documents |
| Phase 2 | Read + write | Supplier can edit a defined subset of its own profile/contacts, upload documents |

Phase 2 endpoints are included below so the schema is stable across both phases, but STATZWeb can
implement Phase 1 first and stub/reject Phase 2 routes until ready.

**Out of scope entirely — never exposed by this API, in either direction:** `probation`,
`probation_on`, `probation_by`, `conditional`, `conditional_on`, `conditional_by`,
`special_terms`, `special_terms_on`, `notes`, `prime`, `ppi`, `iso`, `allows_gsi`, `archived*`,
`packhouse`, `files_url`, `supplier_type`, `cage_code` (identifying value, not editable), `dodaac`.
These are internal risk/compliance/classification fields on `Supplier` and must never be
readable or writable through this API. If a future supplier-portal need touches one of these,
that's a deliberate scope change to renegotiate — not an oversight to patch around.

---

## 2. Authentication

Every request is server-to-server (statzcorp-com backend → STATZWeb backend). No browser ever
calls this API directly, and no credential from it ever reaches a client response or template.

Two layers, both required:

### 2.1 API key

- Header: `X-API-Key: <key>`
- Identifies the calling application. STATZWeb should scope this key's permissions to exactly
  the endpoints in this document — not general internal-API access.
- Issued once, stored server-side only (Azure App Service application settings / Key Vault on
  the statzcorp-com side; equivalent secret store on the STATZWeb side to verify against).
- **Env var name (both sides, values must match exactly):** `SUPPLIER_PORTAL_API_KEY`

### 2.2 Request signature (HMAC)

Guards against a leaked API key alone being sufficient, and against replay.

- Shared secret, separate from the API key, known only to both servers.
- **Env var name (both sides, values must match exactly):** `SUPPLIER_PORTAL_HMAC_SECRET`
- Canonical string to sign: `{method}\n{path}\n{timestamp}\n{body}` (body = raw JSON, empty
  string for GET).
- `HMAC-SHA256(secret, canonical_string)`, hex-encoded.
- Headers sent with every request:
  - `X-Timestamp: <unix epoch seconds>`
  - `X-Signature: <hex hmac>`
- STATZWeb rejects the request (`401`) if:
  - the signature doesn't match, or
  - `X-Timestamp` is more than 5 minutes from server time (replay window).

### 2.4 Base URL

- **Env var name (statzcorp-com side only):** `SUPPLIER_PORTAL_API_BASE_URL` — e.g.
  `https://<statzweb-host>/api/supplier-portal/v1/`. STATZWeb doesn't need this value; it only
  needs to actually serve the API at whatever path this points to.
- Generate both shared secrets with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
  and copy the identical value into both projects' environment — never regenerate independently
  per side, or the handshake breaks.

### 2.3 Network layer (recommended, not required to start)

IP-allowlist the known outbound IP(s) of the statzcorp-com App Service on the STATZWeb API, in
addition to the above. Defense in depth — a leaked key+secret pair still doesn't work from an
arbitrary attacker's host.

### 2.4 Key rotation

Both the API key and HMAC secret should be independently rotatable without a code deploy on
either side (i.e., read from env/config, not hardcoded). No specific rotation cadence mandated
here — just don't make rotation require a release.

---

## 3. Conventions

- **Base URL (example):** `https://<statzweb-host>/api/supplier-portal/v1/`
- **Format:** JSON request/response bodies, `Content-Type: application/json`.
- **Versioning:** path-prefixed (`/v1/`). Breaking changes get a new version prefix, not an
  in-place change.
- **Dates:** ISO 8601 (`YYYY-MM-DD` for dates, `YYYY-MM-DDTHH:MM:SSZ` for datetimes, UTC).
- **Identifier in path:** `cage_code` (URL-encoded if it ever contains non-alphanumerics).
  Assumes `cage_code` is unique per `Supplier` — **confirm/enforce a unique constraint on
  `Supplier.cage_code` on the STATZWeb side before this ships**; the current model
  (`suppliers/models.py`) does not declare one.

### 3.1 Error envelope

All non-2xx responses return:

```json
{
  "error": {
    "code": "not_found",
    "message": "No supplier found for the given cage code."
  }
}
```

| HTTP status | `code` | When |
|---|---|---|
| 400 | `bad_request` | Malformed body / missing required field |
| 401 | `unauthorized` | Missing/invalid API key or signature, or stale timestamp |
| 403 | `forbidden` | Valid caller, but not permitted to touch this field/resource (e.g. write attempt on an excluded field) |
| 404 | `not_found` | Cage code doesn't exist (or is archived — see §3.2) |
| 409 | `conflict` | e.g. duplicate contact email within a supplier |
| 422 | `validation_error` | Field present but fails validation (bad email format, etc.) — include a `fields` map of field → message |
| 429 | `rate_limited` | Caller exceeded rate limit |
| 5xx | `server_error` | STATZWeb-side failure |

### 3.2 Archived suppliers

`Supplier.archived = True` suppliers should behave as `404` on every endpoint below — an
archived supplier has no active portal access, regardless of what `statzcorp-com`'s local
`SupplierPortalAccount` table thinks.

---

## 4. Phase 1 — Read endpoints

### 4.1 Verify supplier (account provisioning)

Used once, when staff provisions a `SupplierPortalAccount` on the statzcorp-com side, to confirm
the cage code is real and get the on-file email to send the initial set-password link to.

```
GET /suppliers/{cage_code}/verify/
```

Response `200`:
```json
{
  "cage_code": "3WGD1",
  "name": "Example Supplier LLC",
  "is_active": true,
  "contact_email": "ap@example-supplier.com"
}
```
`contact_email` — STATZWeb's choice of source field (suggest `Supplier.business_email`, falling
back to `primary_email`, falling back to the first `Contact` flagged as the primary/AP contact if
one exists). Document whichever rule is chosen.

Response `404` if cage code doesn't exist or supplier is archived.

### 4.2 Supplier profile (portal dashboard)

```
GET /suppliers/{cage_code}/
```

Response `200`:
```json
{
  "cage_code": "3WGD1",
  "name": "Example Supplier LLC",
  "business_phone": "608-555-0100",
  "business_fax": "608-555-0101",
  "business_email": "ap@example-supplier.com",
  "website_url": "https://example-supplier.com",
  "primary_phone": "608-555-0199",
  "primary_email": "owner@example-supplier.com",
  "addresses": {
    "billing": { "line1": "...", "line2": "...", "city": "...", "state": "...", "zip": "...", "country": "..." },
    "shipping": { "...": "..." },
    "physical": { "...": "..." }
  },
  "contacts": [
    {
      "id": 101,
      "salutation": "Mr.",
      "name": "Jane Doe",
      "title": "AP Manager",
      "phone": "608-555-0102",
      "email": "jane@example-supplier.com",
      "categories": ["Accounts Payable", "Sales"]
    }
  ],
  "certifications": [
    {
      "type": "ISO 9001",
      "certification_date": "2024-01-15",
      "certification_expiration": "2027-01-15",
      "compliance_status": "Compliant"
    }
  ],
  "classifications": [
    { "type": "Small Business", "classification_date": "2023-06-01", "classification_expiration": null }
  ],
  "documents": [
    {
      "id": 55,
      "doc_type": "CERT",
      "description": "ISO 9001 Certificate",
      "linked_certification": "ISO 9001",
      "uploaded_on": "2024-01-16T10:00:00Z"
    }
  ]
}
```

`addresses.*` shape depends on STATZWeb's `contracts.Address` model fields — fill in exact keys
when that model is available; the shape above is a placeholder for whatever fields it has.

`documents[]` deliberately omits a direct file URL here — see §4.3 for why.

### 4.3 Document download

```
GET /suppliers/{cage_code}/documents/{document_id}/download/
```

Response `200`:
```json
{ "url": "https://.../supplier-docs/....pdf?<sas-token>", "expires_at": "2026-07-20T18:30:00Z" }
```

Returns a short-lived signed URL (Azure Blob SAS token or equivalent) rather than proxying file
bytes through `statzcorp-com`. Keeps large-file bandwidth off the public site's server and avoids
statzcorp-com needing Blob credentials at all. `expires_at` should be short (minutes, not hours)
since the URL will typically be used immediately by the browser.

---

## 5. Phase 2 — Write endpoints

Writes apply directly to STATZWeb's live tables — no approval queue (decided 2026-07-20). To
keep that safe with no gate in front of it:

- **STATZWeb enforces the field allowlist below itself.** Do not trust that `statzcorp-com` only
  sends editable fields — reject/ignore (`403`) any attempt to set an excluded field, even if
  the caller is authenticated correctly. STATZWeb is system of record.
- **Log every write** with source = `"supplier-portal"`, the `cage_code`, old/new values, and
  timestamp — whatever audit mechanism STATZWeb already uses for staff edits (or a new simple
  audit table if it doesn't have one for these models yet).
- **Notify internal staff by email** on every accepted write, summarizing what changed. This is
  the substitute for a review gate — staff finds out immediately rather than never.

### 5.1 Editable fields on `Supplier`

| Field | Editable via portal? |
|---|---|
| `business_phone`, `business_fax`, `business_email`, `website_url` | Yes |
| `primary_phone`, `primary_email` | Yes |
| `billing_address`, `shipping_address`, `physical_address` | Yes |
| everything else on `Supplier` (see §1 exclusion list, plus `name`, `logo_url`, `last_enriched_at`) | No |

```
PATCH /suppliers/{cage_code}/
body: { any subset of the "Yes" fields above }
```

`200` with the updated profile (same shape as §4.2) on success. `403` with `fields` naming the
rejected keys if the body includes anything outside the allowlist — reject the whole request
rather than silently dropping fields, so the caller's UI can show what failed.

### 5.2 Contacts

```
POST   /suppliers/{cage_code}/contacts/            body: { salutation, name, title, phone, email, categories }
PATCH  /suppliers/{cage_code}/contacts/{id}/        body: subset of the above
DELETE /suppliers/{cage_code}/contacts/{id}/
```

All fields on `Contact` are supplier-editable except `id` and `supplier` (implicit from the URL).
`categories` — decide whether the portal can only pick from existing `SupplierContactCategory`
values (recommended) or create new ones (not recommended — category taxonomy should stay
staff-controlled).

### 5.3 Documents

```
POST /suppliers/{cage_code}/documents/
body: multipart/form-data — file, doc_type, description, linked certification/classification id (optional)
```

`201` with the created document's metadata (same shape as an entry in `documents[]` from §4.2).
`doc_type` restricted to the existing `SupplierDocument.DOC_TYPE_CHOICES` (`CERT`, `CLASS`,
`GENERAL`) — reject anything else with `422`.

Consider whether a document upload tied to a certification/classification should also *update*
that record's dates, or stay purely additive (new document, dates unchanged until staff reviews)
— flagging as an open decision, not specifying an answer, since it affects compliance workflows
STATZWeb owns.

---

## 6. Rate limiting

Recommend STATZWeb rate-limit this API per API key (not per cage code, since all traffic shares
one caller identity) — e.g. a generous ceiling like 60 req/min — mainly to contain a bug or
runaway retry loop on the statzcorp-com side, not to defend against the caller itself.

---

## 7. Open questions for the STATZWeb implementer

1. Does `Supplier.cage_code` need a unique constraint added? (Not currently declared in
   `suppliers/models.py`.)
2. What's the exact source/fallback rule for `verify/`'s `contact_email`?
3. Exact field names/shape for `contracts.Address` (used in `addresses.*` above).
4. Does STATZWeb already have an audit-log mechanism to hook into for §5's write logging, or does
   one need to be added for these models?
5. Should a document upload tied to a certification/classification touch that record's dates, or
   stay purely additive? (§5.3)
6. Confirm which `SupplierContactCategory` values, if any, should be hidden from the
   portal-facing category list (e.g. internal-only categories).

---

## 8. Change log

- 2026-07-20 — Initial draft. Auth model (API key + HMAC), Phase 1 read endpoints, Phase 2 direct
  write (no approval queue, staff notified per write), field allowlist/exclusion list.
