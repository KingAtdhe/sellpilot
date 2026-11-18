"""In-memory fake of the Polar API endpoints SellPilot uses (for tests)."""
import io
import json
import re
import urllib.error
import uuid
from urllib.parse import urlparse, parse_qs


class Resp(io.BytesIO):
    def __init__(self, body: bytes, headers=None):
        super().__init__(body)
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakePolar:
    def __init__(self):
        self.files, self.benefits, self.products, self.links, self.discounts, self.orders = {}, {}, {}, {}, {}, []
        self.calls = []
        self.fail_next = []      # list of (method, path_regex, status)

    def _err(self, url, code, msg):
        raise urllib.error.HTTPError(url, code, msg, {}, io.BytesIO(json.dumps({"detail": msg}).encode()))

    def __call__(self, req, timeout=None):
        url, method = req.full_url, req.get_method()
        u = urlparse(url)
        path, q = u.path, parse_qs(u.query)
        self.calls.append((method, path))
        for i, (m, rx, code) in enumerate(self.fail_next):
            if m == method and re.search(rx, path):
                self.fail_next.pop(i)
                self._err(url, code, "injected")
        if u.netloc == "s3.fake":
            return Resp(b"", {"ETag": '"etag-%s"' % path[-6:]})
        body = json.loads(req.data) if req.data and method != "PUT" else None
        out = self.route(method, path, q, body, url)
        return Resp(json.dumps(out).encode())

    def _page(self, items, q):
        page, limit = int(q.get("page", ["1"])[0]), int(q.get("limit", ["10"])[0])
        mx = max(1, -(-len(items) // limit))
        return {"items": items[(page - 1) * limit: page * limit], "pagination": {"total_count": len(items), "max_page": mx}}

    def route(self, m, path, q, b, url):
        if m == "POST" and path == "/v1/files/":
            fid = str(uuid.uuid4())
            assert b["service"] in ("downloadable", "product_media")
            assert b["size"] > 0 and b["upload"]["parts"]
            if b["service"] == "product_media":
                assert b["mime_type"].startswith("image/") and b["size"] <= 10485760
            parts = [dict(p, url=f"https://s3.fake/up/{fid}/{p['number']}", expires_at="x", headers={}) for p in b["upload"]["parts"]]
            self.files[fid] = {"id": fid, "name": b["name"], "service": b["service"], "is_uploaded": False,
                               "public_url": f"https://cdn.fake/{fid}.png", "upload": {"id": "up" + fid, "path": "p/" + fid, "parts": parts}}
            return self.files[fid]
        mm = re.match(r"^/v1/files/([^/]+)/uploaded$", path)
        if m == "POST" and mm:
            f = self.files[mm.group(1)]
            assert b["id"] == f["upload"]["id"] and b["parts"] and all(p["checksum_etag"] for p in b["parts"])
            f["is_uploaded"] = True
            return f
        if m == "POST" and path == "/v1/benefits/":
            assert b["type"] == "downloadables" and 3 <= len(b["description"]) <= 42
            for fid in b["properties"]["files"]:
                assert self.files[fid]["is_uploaded"]
            bid = str(uuid.uuid4())
            self.benefits[bid] = dict(b, id=bid)
            return self.benefits[bid]
        if m == "POST" and path == "/v1/products/":
            for mid in b.get("medias") or []:
                assert self.files[mid]["service"] == "product_media" and self.files[mid]["is_uploaded"]
            for k, v in b["metadata"].items():
                assert len(k) <= 40 and (not isinstance(v, str) or len(v) <= 500), k
            assert len(b["metadata"]) <= 50
            pid = str(uuid.uuid4())
            p = {"id": pid, "name": b["name"], "description": b["description"], "visibility": b.get("visibility", "public"),
                 "is_archived": False, "metadata": b["metadata"], "created_at": "2026-11-18T08:00:00Z",
                 "prices": [dict(pr, id=str(uuid.uuid4()), is_archived=False) for pr in b["prices"]],
                 "benefits": [], "medias": [{"id": i, "public_url": self.files[i]["public_url"]} for i in b.get("medias") or []]}
            self.products[pid] = p
            return p
        mm = re.match(r"^/v1/products/([^/]+)/benefits$", path)
        if m == "POST" and mm:
            p = self.products[mm.group(1)]
            p["benefits"] = [self.benefits[x] for x in b["benefits"]]
            return p
        mm = re.match(r"^/v1/products/([^/]+)$", path)
        if m == "PATCH" and mm:
            p = self.products[mm.group(1)]
            for k, v in b.items():
                if k == "prices":
                    for pr in p["prices"]:
                        pr["is_archived"] = True
                    p["prices"] = [dict(pr, id=str(uuid.uuid4()), is_archived=False) for pr in v]
                else:
                    p[k] = v
            return p
        if m == "GET" and path == "/v1/products/":
            arch = q.get("is_archived", ["false"])[0] == "true"
            return self._page([p for p in self.products.values() if p["is_archived"] == arch], q)
        if m == "POST" and path == "/v1/checkout-links/":
            lid = str(uuid.uuid4())
            assert b["payment_processor"] == "stripe" and b["products"]
            self.links[lid] = dict(b, id=lid, url=f"https://buy.polar.sh/{lid}")
            return self.links[lid]
        if m == "GET" and path == "/v1/orders/":
            return self._page(self.orders, q)
        if m == "GET" and path == "/v1/discounts/":
            return self._page(list(self.discounts.values()), q)
        if m == "POST" and path == "/v1/discounts/":
            assert re.fullmatch(r"[A-Za-z0-9]{3,256}", b["code"])
            if any(d["code"] == b["code"] for d in self.discounts.values()):
                self._err(url, 422, "code exists")
            did = str(uuid.uuid4())
            self.discounts[did] = dict(b, id=did)
            return self.discounts[did]
        self._err(url, 404, f"no route {m} {path}")

    def sell(self, pid, cents, day, status="paid"):
        self.orders.append({"id": str(uuid.uuid4()), "product_id": pid, "status": status, "net_amount": cents,
                            "platform_fee_amount": int(cents * 0.05), "refunded_amount": 0, "currency": "usd",
                            "created_at": f"{day}T10:00:00Z"})
