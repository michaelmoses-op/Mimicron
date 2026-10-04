from __future__ import annotations

from pathlib import Path

import yaml

from app.main import create_app

M1_PATHS: dict[str, set[str]] = {
    "/healthz": {"get"},
    "/readyz": {"get"},
    "/v1/auth/register": {"post"},
    "/v1/auth/login": {"post"},
    "/v1/auth/refresh": {"post"},
    "/v1/me": {"get"},
    "/v1/api-keys": {"get", "post"},
    "/v1/api-keys/{key_id}": {"delete"},
    "/internal/v1/keys/verify": {"post"},
}


def test_m1_paths_match_contract() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    contract_path = repo_root / "contracts" / "openapi" / "control-api.yaml"
    contract = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    live = create_app().openapi()

    for path, methods in M1_PATHS.items():
        assert path in contract["paths"], f"missing in contract: {path}"
        assert path in live["paths"], f"not implemented: {path}"
        for method in methods:
            assert method in contract["paths"][path], f"{path} missing {method} in contract"
            assert method in live["paths"][path], f"{path} missing {method} in app"
