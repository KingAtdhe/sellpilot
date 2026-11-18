"""Pinterest promotion (optional). Pinterest is the biggest free traffic source
for printables. Needs a Pinterest developer app + refresh token (see README)."""
from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request

API = "https://api.pinterest.com/v5"


class Pinterest:
    def __init__(self, app_id, app_secret, refresh_token, board_id, opener=None):
        self.app_id, self.secret, self.refresh, self.board = app_id, app_secret, refresh_token, board_id
        self.open = opener or urllib.request.urlopen
        self.token = None

    def _auth(self):
        basic = base64.b64encode(f"{self.app_id}:{self.secret}".encode()).decode()
        body = urllib.parse.urlencode({"grant_type": "refresh_token", "refresh_token": self.refresh}).encode()
        r = urllib.request.Request(API + "/oauth/token", data=body, method="POST", headers={
            "Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"})
        with self.open(r, timeout=30) as resp:
            self.token = json.loads(resp.read())["access_token"]

    def pin(self, title, description, link, image_url, alt=""):
        if not self.token:
            self._auth()
        body = {"board_id": self.board, "title": title[:100], "description": description[:500], "link": link,
                "alt_text": (alt or title)[:500], "media_source": {"source_type": "image_url", "url": image_url}}
        r = urllib.request.Request(API + "/pins", data=json.dumps(body).encode(), method="POST", headers={
            "Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        with self.open(r, timeout=60) as resp:
            return json.loads(resp.read())
