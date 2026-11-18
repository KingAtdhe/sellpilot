"""Minimal Polar.sh API client (merchant of record: Polar charges the buyer,
handles EU VAT / sales tax, emails the download and pays you out).

Uses an Organization Access Token, so organization_id is never needed.
Docs: https://polar.sh/docs/api-reference
"""
from __future__ import annotations

import base64
import hashlib
import json
import time
import urllib.error
import urllib.request

SERVERS = {"production": "https://api.polar.sh", "sandbox": "https://sandbox-api.polar.sh"}
PART = 10 * 1024 * 1024


class PolarError(Exception):
    def __init__(self, status, body, where):
        super().__init__(f"Polar {status} on {where}: {str(body)[:400]}")
        self.status, self.body = status, body


class Polar:
    def __init__(self, token: str, server: str = "production", base_url: str | None = None, opener=None):
        self.token = token
        self.base = base_url or SERVERS[server]
        self.open = opener or urllib.request.urlopen

    # ------------------------------------------------------------ low level
    def req(self, method, path, body=None, query=None, retries=4):
        url = self.base + path
        if query:
            from urllib.parse import urlencode
            url += "?" + urlencode([(k, v) for k, v in query.items() if v is not None], doseq=True)
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(retries + 1):
            r = urllib.request.Request(url, data=data, method=method, headers={
                "Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
                "Accept": "application/json", "User-Agent": "SellPilot/1.0"})
            try:
                with self.open(r, timeout=60) as resp:
                    raw = resp.read()
                    return json.loads(raw) if raw else {}
            except urllib.error.HTTPError as e:
                txt = e.read().decode("utf-8", "replace")
                if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                    wait = float(e.headers.get("Retry-After") or 2 ** attempt * 2)
                    time.sleep(min(wait, 60))
                    continue
                raise PolarError(e.code, txt, f"{method} {path}") from None
            except urllib.error.URLError:
                if attempt < retries:
                    time.sleep(2 ** attempt * 2)
                    continue
                raise

    def paged(self, path, query=None):
        page, out = 1, []
        while True:
            q = dict(query or {}, page=page, limit=100)
            res = self.req("GET", path, query=q)
            out += res.get("items", [])
            mx = (res.get("pagination") or {}).get("max_page", 1)
            if page >= mx:
                return out
            page += 1

    # ------------------------------------------------------------ files
    def upload(self, name: str, data: bytes, mime: str, service: str) -> str:
        """Multipart upload to Polar's S3 and mark it complete. Returns file id."""
        parts = []
        for n, start in enumerate(range(0, len(data), PART), 1):
            chunk = data[start:start + PART]
            parts.append({"number": n, "chunk_start": start, "chunk_end": start + len(chunk),
                          "checksum_sha256_base64": base64.b64encode(hashlib.sha256(chunk).digest()).decode()})
        f = self.req("POST", "/v1/files/", {
            "name": name, "mime_type": mime, "size": len(data), "service": service,
            "checksum_sha256_base64": base64.b64encode(hashlib.sha256(data).digest()).decode(),
            "upload": {"parts": parts}})
        done = []
        for part in f["upload"]["parts"]:
            chunk = data[part["chunk_start"]:part["chunk_end"]]
            headers = dict(part.get("headers") or {})
            r = urllib.request.Request(part["url"], data=chunk, method="PUT", headers=headers)
            for attempt in range(4):
                try:
                    with self.open(r, timeout=120) as resp:
                        etag = (resp.headers.get("ETag") or "").strip()
                    break
                except (urllib.error.URLError, urllib.error.HTTPError):
                    if attempt == 3:
                        raise
                    time.sleep(3 * (attempt + 1))
            done.append({"number": part["number"], "checksum_etag": etag,
                         "checksum_sha256_base64": part.get("checksum_sha256_base64")})
        self.req("POST", f"/v1/files/{f['id']}/uploaded",
                 {"id": f["upload"]["id"], "path": f["upload"]["path"], "parts": done})
        return f["id"]

    # ------------------------------------------------------------ catalog
    def organization(self) -> dict:
        items = self.req("GET", "/v1/organizations/", query={"limit": 1}).get("items", [])
        return items[0] if items else {}

    def products(self, archived=False) -> list[dict]:
        return self.paged("/v1/products/", {"is_archived": str(archived).lower()})

    def create_benefit_files(self, description: str, file_ids: list[str], metadata=None) -> dict:
        return self.req("POST", "/v1/benefits/", {
            "type": "downloadables", "description": description[:42],
            "properties": {"files": file_ids}, "metadata": metadata or {}})

    def create_product(self, name, description, price_cents, currency, media_ids, metadata) -> dict:
        return self.req("POST", "/v1/products/", {
            "name": name, "description": description, "visibility": "public",
            "prices": [{"amount_type": "fixed", "price_amount": price_cents, "price_currency": currency}],
            "medias": media_ids, "metadata": metadata})

    def set_benefits(self, product_id, benefit_ids):
        return self.req("POST", f"/v1/products/{product_id}/benefits", {"benefits": benefit_ids})

    def update_product(self, product_id, **fields):
        return self.req("PATCH", f"/v1/products/{product_id}", fields)

    def checkout_link(self, product_id, label="", metadata=None) -> dict:
        return self.req("POST", "/v1/checkout-links/", {
            "payment_processor": "stripe", "products": [product_id], "label": label[:100] or None,
            "allow_discount_codes": True, "metadata": metadata or {}})

    # ------------------------------------------------------------ sales
    def orders(self, since_iso=None) -> list[dict]:
        q = {"sorting": "-created_at"}
        if since_iso:
            q["created_after"] = since_iso
        return self.paged("/v1/orders/", q)

    def discounts(self) -> list[dict]:
        return self.paged("/v1/discounts/")

    def create_discount(self, name, code, percent, starts_at=None, ends_at=None, products=None, metadata=None):
        return self.req("POST", "/v1/discounts/", {
            "name": name, "code": code, "type": "percentage", "basis_points": int(percent * 100),
            "duration": "once", "starts_at": starts_at, "ends_at": ends_at, "products": products,
            "metadata": metadata or {}})
