from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from lf2x.config import LF2XSettings
from lf2x.ir import IntermediateRepresentation
from lf2x.parser import LangFlowDocument
from lf2x.rest_client import (
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
