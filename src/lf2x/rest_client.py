"""LangFlow REST API client skeleton."""

from __future__ import annotations

from collections.abc import Generator, Iterable, Mapping
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


@dataclass(frozen=True, slots=True)
class FlowSummary:
    """Summary information about a LangFlow flow."""

    flow_id: str
    name: str
    tags: tuple[str, ...]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> FlowSummary:
        raw_id = payload.get("id") or payload.get("flow_id")
        if not raw_id:
            raise LangFlowAPIError("Flow summary is missing an identifier")
        flow_id = str(raw_id)
        name = str(payload.get("name") or flow_id)
        tags_value = payload.get("tags", [])
        if isinstance(tags_value, Mapping):
            tags_iter: Iterable[str] = tags_value.values()
        elif isinstance(tags_value, list | tuple | set):
            tags_iter = (str(tag) for tag in tags_value)
        else:
            tags_iter = ()
        return cls(flow_id=flow_id, name=name, tags=tuple(tags_iter))


@dataclass(frozen=True, slots=True)
class FlowPage:
    """A paginated collection of flow summaries."""

    flows: tuple[FlowSummary, ...]
    total: int
    offset: int
    limit: int

    @property
    def has_more(self) -> bool:
        return self.offset + len(self.flows) < self.total


@dataclass(slots=True)
class LangFlowClient:
    """Minimal REST client for retrieving LangFlow flows."""

    base_url: str
    token: str | None = None
    timeout: float = DEFAULT_TIMEOUT_SECONDS
    verify: bool | str = True
    transport: httpx.BaseTransport | None = None

    @classmethod
    def from_settings(
        cls,
        settings: LF2XSettings,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        verify: bool | str = True,
        transport: httpx.BaseTransport | None = None,
    ) -> LangFlowClient:
        """Build a client from LF2X settings."""

        if not settings.api_base_url:
            raise ValueError("api_base_url must be configured to use the LangFlow client")
        return cls(
            base_url=settings.api_base_url,
            token=settings.api_token,
            timeout=timeout,
            verify=verify,
            transport=transport,
        )

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

    def list_flows(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        tags: Iterable[str] | None = None,
    ) -> FlowPage:
        """Return a page of flow summaries."""

        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if tags:
            params["tags"] = ",".join(tags)
        response = self._request_collection(params)
        data = response.json()
        if not isinstance(data, Mapping):
            raise LangFlowAPIError("Unexpected response payload for list_flows")
        items = data.get("data")
        if not isinstance(items, list):
            raise LangFlowAPIError("LangFlow list response missing 'data' array")
        summaries = tuple(FlowSummary.from_payload(item) for item in items)
        pagination = data.get("pagination")
        if isinstance(pagination, Mapping):
            total = int(pagination.get("total", len(summaries)))
            page_limit = int(pagination.get("limit", limit))
            page_offset = int(pagination.get("offset", offset))
        else:
            total = len(summaries)
            page_limit = limit
            page_offset = offset
        return FlowPage(flows=summaries, total=total, offset=page_offset, limit=page_limit)

    def iter_flow_summaries(
        self,
        *,
        page_size: int = 50,
        tags: Iterable[str] | None = None,
    ) -> Generator[FlowSummary, None, None]:
        """Yield summaries for all flows, handling pagination."""

        offset = 0
        while True:
            page = self.list_flows(limit=page_size, offset=offset, tags=tags)
            if not page.flows:
                break
            yield from page.flows
            offset = page.offset + len(page.flows)
            if offset >= page.total:
                break

    def iter_flow_documents(
        self,
        *,
        page_size: int = 50,
        tags: Iterable[str] | None = None,
        settings: LF2XSettings | None = None,
    ) -> Generator[LangFlowDocument, None, None]:
        """Iterate over LangFlow documents for all flows."""

        for summary in self.iter_flow_summaries(page_size=page_size, tags=tags):
            yield self.fetch_flow_document(summary.flow_id, settings=settings)

    def iter_irs(
        self,
        *,
        page_size: int = 50,
        tags: Iterable[str] | None = None,
        settings: LF2XSettings | None = None,
    ) -> Generator[IntermediateRepresentation, None, None]:
        """Iterate over Intermediate Representations for all flows."""

        for document in self.iter_flow_documents(page_size=page_size, tags=tags, settings=settings):
            yield build_intermediate_representation(document)

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

    def _request_collection(self, params: Mapping[str, Any]) -> httpx.Response:
        url = f"{self._base_url}{API_PREFIX}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        with httpx.Client(
            timeout=self.timeout,
            verify=self.verify,
            transport=self.transport,
        ) as client:
            response = client.get(url, headers=headers, params=params)

        if response.status_code in {401, 403}:
            raise LangFlowAuthError("Authentication failed for LangFlow API request")
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
    "FlowSummary",
    "FlowPage",
]
