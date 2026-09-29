import json

from cardsmith import cli


class FakePingClient:
    def __init__(self, base_url, model):
        self.base_url = base_url
        self.model = model

    def ping(self):
        return False, "cannot reach ollama at http://localhost:11434: connection refused"


def test_build_parser_defaults():
    args = cli.build_parser().parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == 8420
    assert args.model == "qwen3:4b"
    assert args.ollama_url == "http://localhost:11434"


def test_check_flag_reports_unreachable_server_and_exits_nonzero(monkeypatch, capsys):
    monkeypatch.setattr(cli, "OllamaClient", FakePingClient)
    code = cli.main(["--check"])
    assert code == 1
    out = capsys.readouterr().out
    assert "unreachable" in out


def test_check_flag_json_output(monkeypatch, capsys):
    monkeypatch.setattr(cli, "OllamaClient", FakePingClient)
    cli.main(["--check", "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["ok"] is False
    assert "message" in data


def test_version_flag_exits_zero(capsys):
    try:
        cli.main(["--version"])
    except SystemExit as e:
        assert e.code == 0
    out = capsys.readouterr().out
    assert "cardsmith" in out
