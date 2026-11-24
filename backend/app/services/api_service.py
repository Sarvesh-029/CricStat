"""CricAPI service layer.

All HTTP interaction with the external Cricket API lives here. The rest of the
application never calls the network directly, which keeps authentication,
pagination, retries, and rate-limit handling in one place.

CricAPI reference (https://www.cricapi.com/):
  Base URL: https://api.cricapi.com/v1
  Auth:     ?apikey=<KEY> on every request
  Common endpoints used by CricStat:
    /series          - list series (filter by name containing "IPL")
    /series_info     - matches & squads for a series (?id=<series_id>)
    /match_info      - single match metadata (?id=<match_id>)
    /match_scorecard - full scorecard for a match (?id=<match_id>)
    /players         - player search (?search=<name>, ?offset=)
    /player_info     - player profile (?id=<player_id>)
    /currentMatches  - live/recent matches
    /matches         - upcoming/past matches list

NOTE: CricAPI's free tier is heavily rate-limited (~100 calls/day) and does
not guarantee ball-by-ball data. Where an endpoint is unavailable or returns
insufficient data, CricStat marks the affected metric as unavailable rather
than fabricating values.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

import requests
from requests import Response

from ..config import settings

logger = logging.getLogger(__name__)

# HTTP status codes worth retrying.
_RETRYABLE = {429, 500, 502, 503, 504}


class CricAPIError(Exception):
    """Raised when the API returns an error or an unexpected payload."""


class CricAPIClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: int = 30):
        self.base_url = (base_url or settings.cricapi_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.cricapi_api_key
        self.timeout = timeout
        self._session = requests.Session()

    # ------------------------------------------------------------------ #
    # Low-level
    # ------------------------------------------------------------------ #
    def _request(self, endpoint: str, params: Optional[dict] = None, retries: int = 3) -> dict:
        if not settings.has_api_key and not self.api_key:
            raise CricAPIError(
                "No CricAPI key configured. Set CRICAPI_API_KEY in backend/.env. "
                "See backend/.env.example."
            )

        params = dict(params or {})
        params["apikey"] = self.api_key
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        last_exc: Optional[Exception] = None
        for attempt in range(1, retries + 1):
            try:
                resp: Response = self._session.get(url, params=params, timeout=self.timeout)
            except requests.RequestException as exc:  # network / timeout
                last_exc = exc
                logger.warning("Network error on %s (attempt %d/%d): %s", endpoint, attempt, retries, exc)
                time.sleep(min(2 ** attempt, 8))
                continue

            if resp.status_code in _RETRYABLE:
                # Respect Retry-After if present.
                retry_after = resp.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else min(2 ** attempt, 8)
                logger.warning("HTTP %s on %s (attempt %d/%d); retrying in %ss", resp.status_code, endpoint, attempt, retries, wait)
                time.sleep(wait)
                last_exc = CricAPIError(f"HTTP {resp.status_code}")
                continue

            if resp.status_code != 200:
                raise CricAPIError(f"HTTP {resp.status_code} for {endpoint}: {resp.text[:300]}")

            try:
                payload = resp.json()
            except ValueError as exc:
                raise CricAPIError(f"Invalid JSON from {endpoint}: {exc}") from exc

            if not isinstance(payload, dict):
                raise CricAPIError(f"Unexpected response shape from {endpoint}")

            status = str(payload.get("status", "")).lower()
            if status and status != "success":
                reason = payload.get("reason") or payload.get("message") or "unknown error"
                raise CricAPIError(f"CricAPI error on {endpoint}: {reason}")

            return payload

        raise CricAPIError(f"Failed to fetch {endpoint} after {retries} attempts: {last_exc}")

    # ------------------------------------------------------------------ #
    # Endpoints
    # ------------------------------------------------------------------ #
    def series_list(self, offset: int = 0, search: Optional[str] = None) -> dict:
        params = {"offset": offset}
        if search:
            params["search"] = search
        return self._request("series", params=params)

    def series_info(self, series_id: str, offset: int = 0) -> dict:
        return self._request("series_info", params={"id": series_id, "offset": offset})

    def match_info(self, match_id: str) -> dict:
        return self._request("match_info", params={"id": match_id})

    def match_scorecard(self, match_id: str) -> dict:
        return self._request("match_scorecard", params={"id": match_id})

    def players(self, search: Optional[str] = None, offset: int = 0) -> dict:
        params = {"offset": offset}
        if search:
            params["search"] = search
        return self._request("players", params=params)

    def player_info(self, player_id: str) -> dict:
        return self._request("player_info", params={"id": player_id})

    def current_matches(self, offset: int = 0) -> dict:
        return self._request("currentMatches", params={"offset": offset})

    def matches_list(self, offset: int = 0) -> dict:
        return self._request("matches", params={"offset": offset})

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def extract_data(payload: dict) -> Any:
        """Return the ``data`` field, tolerating list/dict shapes."""
        return payload.get("data", payload)

    def fetch_all_pages(self, fetcher, *args, **kwargs) -> list:
        """Generic paginator for endpoints that return {data:[...], ...}.

        Stops when an empty page is returned or a page smaller than the
        previous full page. Hard-capped to avoid runaway calls on free tier.
        """
        results: list = []
        offset = 0
        page_size = kwargs.pop("page_size", 50)
        for _ in range(200):  # safety cap
            kwargs["offset"] = offset
            payload = fetcher(*args, **kwargs)
            data = self.extract_data(payload)
            if isinstance(data, dict):
                # Some endpoints nest lists under a key.
                for key in ("list", "matches", "players", "series", "info"):
                    if isinstance(data.get(key), list):
                        data = data[key]
                        break
            if not isinstance(data, list) or not data:
                break
            results.extend(data)
            if len(data) < page_size:
                break
            offset += len(data)
        return results