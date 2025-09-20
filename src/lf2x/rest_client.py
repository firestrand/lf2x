"""LangFlow REST API client skeleton."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import httpx

from .config import LF2XSettings
from .ir import IntermediateRepresentation, build_intermediate_representation
from .parser import LangFlowDocument, parse_langflow_dict

DEFAULT_TIMEOUT_SECONDS = 10.0
API_PREFIX = "/api/v1/flows"


class LangFlowAPIError(RuntimeError):
    """Base exception for LangFlow client errors."""


class LangFlowAuthError(LangFlowAPIError):
    """Raised when authentication fails (HTTP 401/403)."""


class LangFlowNotFoundError(LangFlowAPIError):
    """Raised when the requested flow does not exist (HTTP 404)."""


@dataclass(slots=True)
class LangFlowClient:
    """Minimal REST client for retrieving LangFlow flows."""

    base_url: str
    token: str | None = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    verify: bool | str = True
    transport: httpx.BaseTransport | None = None

    def fetch_flow_json(self, flow_id: str) -> Mapping[str, Any]:
        """Return the raw JSON payload for a LangFlow flow."""

        response = self._request(flow_id)
        payload = response.json()
        if not isinstance(payload, Mapping):
            raise LangFlowAPIError("Unexpected response payload from LangFlow API")
        return cast(Mapping[str, Any], payload)

    def fetch_flow_document(
        self,
        flow_id: str,
        *,
        settings: LF2XSettings | None = None,
    ) -> LangFlowDocument:
        """Return a parsed LangFlow document for the given flow."""

        payload = self.fetch_flow_json(flow_id)
        return parse_langflow_dict(
            payload,
            settings=settings,
            source_path=self._source_path(flow_id),
        )

    def fetch_ir(
        self,
        flow_id: str,
        *,
        settings: LF2XSettings | None = None,
    ) -> IntermediateRepresentation:
        """Return the Intermediate Representation for the given flow."""

        document = self.fetch_flow_document(flow_id, settings=settings)
        return build_intermediate_representation(document)

    def _request(self, flow_id: str) -> httpx.Response:
        url = f"{self._base_url}{API_PREFIX}/{flow_id}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        with httpx.Client(
            timeout=self.timeout,
            verify=self.verify,
            transport=self.transport,
        ) as client:
            response = client.get(url, headers=headers)

        if response.status_code in {401, 403}:
            raise LangFlowAuthError("Authentication failed for LangFlow API request")
        if response.status_code == 404:
            raise LangFlowNotFoundError(f"Flow '{flow_id}' was not found")
        if response.status_code >= 400:
            raise LangFlowAPIError(
                f"LangFlow API request failed with status {response.status_code}: {response.text}"
            )
        return response

    @property
    def _base_url(self) -> str:
        return self.base_url.rstrip("/")

    @staticmethod
    def _source_path(flow_id: str) -> Path:
        return Path(f"{flow_id}.json")


__all__ = [
    "LangFlowAPIError",
    "LangFlowAuthError",
    "LangFlowClient",
    "LangFlowNotFoundError",
]
