"""Tiny synthetic OAuth/Core LMI upstream; reachable only on the test network."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

ACCOUNTS = {
    "proxy-test-client": ("proxy-test-secret", 42),
    "account-a": ("synthetic-secret-a", 101),
    "account-b": ("synthetic-secret-b", 202),
}


class FixtureHandler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/token":
            fields = parse_qs(body.decode())
            account = fields.get("client_id", [""])[0]
            if (
                account not in ACCOUNTS
                or fields.get("client_secret") != [ACCOUNTS[account][0]]
                or fields.get("grant_type") != ["client_credentials"]
                or fields.get("scope") not in (["agnitio"], ["emsi_open"])
            ):
                return self.respond(401, {"error": "Invalid synthetic credentials"})
            return self.respond(
                200,
                {
                    "access_token": f"synthetic-token-{account}",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        if self.path == "/emsi.us.occupation/2026.4":
            account = self.headers.get("Authorization", "").removeprefix(
                "Bearer synthetic-token-"
            )
            if account not in ACCOUNTS:
                return self.respond(401, {"error": "Missing synthetic token"})
            if json.loads(body) != {
                "metrics": [{"name": "Jobs.2025"}],
                "constraints": [],
                "offset": 0,
                "limit": 3,
            }:
                return self.respond(400, {"error": "Unexpected test query"})
            return self.respond(
                200,
                {
                    "data": [
                        {
                            "name": "Jobs.2025",
                            "type": "Double",
                            "rows": [ACCOUNTS[account][1], None],
                        }
                    ],
                    "errors": [],
                    "timings": [],
                    "totalRows": 2,
                },
            )
        self.respond(404, {"error": "No fixture for this path"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), FixtureHandler).serve_forever()
