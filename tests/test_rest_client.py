from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest

from lf2x.config import LF2XSettings
from lf2x.ir import IntermediateRepresentation
from lf2x.parser import LangFlowDocument
from lf2x.rest_client import (
    FlowPage,
    FlowSummary,
    LangFlowAPIError,
    LangFlowAuthError,
    LangFlowClient,
    LangFlowNotFoundError,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "flows"
PAYLOAD = json.loads((FIXTURE_DIR / "simple_passthrough.json").read_text())


def test_fetch_flow_json_success() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=PAYLOAD))
    client = LangFlowClient("https://langflow.example", token="secret", transport=transport)

    data = client.fetch_flow_json("flow")

    assert data["id"] == PAYLOAD["id"]


def test_fetch_flow_document_returns_document(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=PAYLOAD))
    settings = LF2XSettings.from_sources(output_dir=tmp_path / "out")
    client = LangFlowClient("https://langflow.example", transport=transport)

    document = client.fetch_flow_document(PAYLOAD["id"], settings=settings)

    assert isinstance(document, LangFlowDocument)
    assert document.flow_id == PAYLOAD["id"]
    assert document.metadata.output_dir == settings.resolve_output_dir()


def test_fetch_ir_returns_intermediate_representation(tmp_path: Path) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=PAYLOAD))
    settings = LF2XSettings.from_sources(output_dir=tmp_path / "out")
    client = LangFlowClient("https://langflow.example", transport=transport)

    ir = client.fetch_ir(PAYLOAD["id"], settings=settings)

    assert isinstance(ir, IntermediateRepresentation)
    assert ir.flow_id == PAYLOAD["id"]


def test_fetch_flow_json_raises_for_auth_failure() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"detail": "invalid"}))
    client = LangFlowClient("https://langflow.example", transport=transport)

    with pytest.raises(LangFlowAuthError):
        client.fetch_flow_json("flow")


def test_fetch_flow_json_raises_for_not_found() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(404, json={"detail": "missing"}))
    client = LangFlowClient("https://langflow.example", transport=transport)

    with pytest.raises(LangFlowNotFoundError):
        client.fetch_flow_json("missing")


def test_fetch_flow_json_raises_for_other_errors() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(500, text="boom"))
    client = LangFlowClient("https://langflow.example", transport=transport)

    with pytest.raises(LangFlowAPIError):
        client.fetch_flow_json("flow")


def test_authorization_header_is_sent() -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        return httpx.Response(200, json=PAYLOAD)

    transport = httpx.MockTransport(handler)
    client = LangFlowClient("https://langflow.example", token="secret-token", transport=transport)

    client.fetch_flow_json("flow")

    assert captured_headers.get("authorization") == "Bearer secret-token"


def test_list_flows_returns_page() -> None:
    collection_payload = {
        "data": [
            {
                "id": "flow1",
                "name": "Sample Flow",
                "tags": ["demo"],
            }
        ],
        "pagination": {"total": 1, "offset": 0, "limit": 10},
    }
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=collection_payload))
    client = LangFlowClient("https://langflow.example", transport=transport)

    page = client.list_flows(limit=10)

    assert page.total == 1
    assert page.offset == 0
    assert len(page.flows) == 1
    summary = page.flows[0]
    assert summary.flow_id == "flow1"
    assert summary.tags == ("demo",)


def test_iter_flow_summaries_handles_pagination() -> None:
    responses = [
        {
            "data": [{"id": "one", "name": "One"}],
            "pagination": {"total": 2, "offset": 0, "limit": 1},
        },
        {
            "data": [{"id": "two", "name": "Two"}],
            "pagination": {"total": 2, "offset": 1, "limit": 1},
        },
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params)
        offset = int(params.get("offset", 0))
        index = offset if offset < len(responses) else len(responses) - 1
        return httpx.Response(200, json=responses[index])

    transport = httpx.MockTransport(handler)
    client = LangFlowClient("https://langflow.example", transport=transport)

    summaries = list(client.iter_flow_summaries(page_size=1))

    assert [summary.flow_id for summary in summaries] == ["one", "two"]


def test_client_from_settings_requires_base_url(tmp_path: Path) -> None:
    settings = LF2XSettings(output_dir=tmp_path / "dist")
    with pytest.raises(ValueError, match="api_base_url"):
        LangFlowClient.from_settings(settings)

    configured = LF2XSettings(
        output_dir=tmp_path / "dist",
        api_base_url="https://langflow.example",
        api_token="secret",
    )
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=PAYLOAD))
    client = LangFlowClient.from_settings(configured, transport=transport)

    client.fetch_flow_json("flow")


def test_flow_summary_requires_identifier() -> None:
    with pytest.raises(LangFlowAPIError, match="identifier"):
        FlowSummary.from_payload({})


def test_flow_page_has_more_property() -> None:
    page = FlowPage(
        flows=(FlowSummary(flow_id="one", name="One", tags=()),),
        total=2,
        offset=0,
        limit=1,
    )
    assert page.has_more
    assert not FlowPage(flows=(), total=0, offset=0, limit=1).has_more


def test_iter_irs_fetches_all_flows(tmp_path: Path) -> None:
    list_payload = {
        "data": [
            {"id": "flow1", "name": "One", "tags": {"main": "demo"}},
            {"id": "flow2", "name": "Two", "tags": ["prod"]},
        ],
        "pagination": {"total": 2, "offset": 0, "limit": 50},
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("flows"):
            if "tags" in request.url.params:
                assert request.url.params["tags"] == "demo"
            return httpx.Response(200, json=list_payload)
        return httpx.Response(200, json=PAYLOAD)

    settings = LF2XSettings(output_dir=tmp_path / "dist")
    transport = httpx.MockTransport(handler)
    client = LangFlowClient("https://langflow.example", transport=transport)

    irs = list(client.iter_irs(tags=["demo"], settings=settings))

    ids = [ir.flow_id for ir in irs]
    assert ids == [PAYLOAD["id"], PAYLOAD["id"]]


@pytest.mark.skipif(  # type: ignore[misc]
    "LF2X_LANGFLOW_BASE_URL" not in os.environ,
    reason="LF2X_LANGFLOW_BASE_URL not set; skipping integration test",
)
def test_live_langflow_iter_irs(tmp_path: Path) -> None:
    base_url = os.environ["LF2X_LANGFLOW_BASE_URL"]
    token = os.environ.get("LF2X_LANGFLOW_API_TOKEN")
    settings = LF2XSettings(
        output_dir=tmp_path / "dist",
        api_base_url=base_url,
        api_token=token,
    )
    client = LangFlowClient.from_settings(settings)

    try:
        ir_iterator = client.iter_irs(settings=settings)
        first = next(ir_iterator, None)
    except (LangFlowAPIError, httpx.HTTPError) as exc:
        pytest.skip(f"LangFlow API unavailable: {exc}")

    assert first is not None, "Expected at least one flow from live LangFlow instance"
    assert isinstance(first, IntermediateRepresentation)
