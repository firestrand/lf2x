from __future__ import annotations

from pathlib import Path

from lf2x.extractors import DetectedSecret, detect_secrets
from lf2x.ir import IntermediateRepresentation, IREdge, IRMetadata, IRNode


def _secret_ir() -> IntermediateRepresentation:
    nodes = (
        IRNode("provider", "SecretNode", {"api_key": "sk-live-123"}),
        IRNode("other", "OtherNode", {"name": "demo"}),
    )
    edges: tuple[IREdge, ...] = ()
    metadata = IRMetadata(Path("flow.json"), Path("dist"))
    return IntermediateRepresentation(
        flow_id="SecretFlow",
        name="Secrets",
        version="1.0.0",
        nodes=nodes,
        edges=edges,
        metadata=metadata,
    )


def test_detect_secrets_returns_expected_env_var() -> None:
    ir = _secret_ir()

    secrets = detect_secrets(ir)

    assert secrets
    secret = secrets[0]
    assert isinstance(secret, DetectedSecret)
    assert secret.env_var == "SECRETFLOW_PROVIDER_API_KEY"
    assert secret.attribute == "secretflow_provider_api_key"
    assert secret.source_node == "provider"
    assert secret.field == "api_key"


def test_detect_secrets_is_idempotent() -> None:
    ir = _secret_ir()
    first = detect_secrets(ir)
    second = detect_secrets(ir)
    assert first == second
