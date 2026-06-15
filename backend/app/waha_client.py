from __future__ import annotations

import asyncio
from typing import Any, Callable
from urllib.parse import quote

import httpx

from backend.app.config import Settings


class WahaError(Exception):
    def __init__(self, message: str, status_code: int | None = None, detail: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class WahaClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.waha_base_url.rstrip("/")
        self.session = settings.waha_session

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.settings.waha_api_key:
            headers["X-Api-Key"] = self.settings.waha_api_key
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.request(
                method,
                url,
                headers=self._headers(),
                params=params,
                json=json,
            )

        if response.status_code >= 400:
            detail: Any
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise WahaError(
                f"WAHA request failed: {method} {path}",
                status_code=response.status_code,
                detail=detail,
            )

        if response.status_code == 204 or not response.content:
            return None
        try:
            return response.json()
        except Exception:
            return response.text

    async def get_session_me(self) -> dict[str, Any]:
        return await self._request("GET", f"/api/sessions/{self.session}/me")

    async def list_groups(self, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
        data = await self._request(
            "GET",
            f"/api/{self.session}/groups",
            params={
                "limit": limit,
                "offset": offset,
                "sortBy": "subject",
                "sortOrder": "asc",
            },
        )
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("groups", "data", "items"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

    async def get_participants(self, group_id: str) -> list[dict[str, Any]]:
        encoded_id = quote(group_id, safe="")
        data = await self._request(
            "GET",
            f"/api/{self.session}/groups/{encoded_id}/participants/v2",
        )
        if not isinstance(data, list):
            return []
        return data

    async def create_group(self, name: str, participants: list[dict[str, str]]) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/api/{self.session}/groups",
            json={"name": name, "participants": participants},
        )

    async def add_participants(
        self, group_id: str, participants: list[dict[str, str]]
    ) -> Any:
        encoded_id = quote(group_id, safe="")
        return await self._request(
            "POST",
            f"/api/{self.session}/groups/{encoded_id}/participants/add",
            json={"participants": participants},
        )

    async def add_participants_batched(
        self,
        group_id: str,
        participant_ids: list[str],
        *,
        batch_size: int,
        delay_ms: int,
        on_progress: Callable[[int, int, int], None] | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for i in range(0, len(participant_ids), batch_size):
            batch = participant_ids[i : i + batch_size]
            payload = [{"id": pid} for pid in batch]
            try:
                result = await self.add_participants(group_id, payload)
                results.append({"batch": i // batch_size + 1, "count": len(batch), "ok": True, "result": result})
            except WahaError as exc:
                results.append(
                    {
                        "batch": i // batch_size + 1,
                        "count": len(batch),
                        "ok": False,
                        "error": str(exc),
                        "detail": exc.detail,
                    }
                )
            if on_progress:
                on_progress(len(batch), i + len(batch), len(participant_ids))
            if i + batch_size < len(participant_ids) and delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000)
        return results
