"""Configuration is loaded before auth; stdout stays available for MCP JSON-RPC."""

from click.testing import CliRunner

from mcp_lightcast import main
from mcp_lightcast.auth.oauth import LightcastAuth


def test_env_file_applies_before_auth(tmp_path, monkeypatch):
    for key in ("LIGHTCAST_CLIENT_ID", "LIGHTCAST_CLIENT_SECRET"):
        monkeypatch.delenv(key, raising=False)
    env = tmp_path / "credentials.env"
    env.write_text(
        "LIGHTCAST_CLIENT_ID=from-file\nLIGHTCAST_CLIENT_SECRET=secret-from-file\n"
    )

    async def token(self, scope=None):
        assert self.config.client_id == "from-file"
        assert self.config.client_secret == "secret-from-file"
        return "test-token"

    monkeypatch.setattr(LightcastAuth, "get_access_token", token)
    result = CliRunner().invoke(main, ["--env-file", str(env), "--validate-config"])
    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert "verified" in result.stderr
    assert "secret-from-file" not in result.output


def test_stdio_default_has_no_stdout(monkeypatch):
    from mcp_lightcast.server import mcp

    calls = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    result = CliRunner().invoke(main, [])
    assert result.exit_code == 0, result.output
    assert result.stdout == ""
    assert calls[0]["transport"] == "stdio"


def test_explicit_http_transport(monkeypatch):
    from mcp_lightcast.server import mcp

    calls = []
    monkeypatch.setattr(mcp, "run", lambda **kwargs: calls.append(kwargs))
    result = CliRunner().invoke(
        main, ["--transport", "streamable-http", "--port", "3001"]
    )
    assert result.exit_code == 0
    assert calls[0]["host"] == "127.0.0.1" and calls[0]["port"] == 3001
