"""Tiny synthetic OAuth/Core LMI upstream; reachable only on the test network."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs


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
            if parse_qs(body.decode()) != {
                "client_id": ["proxy-test-client"],
                "client_secret": ["proxy-test-secret"],
                "grant_type": ["client_credentials"],
                "scope": ["agnitio"],
            }:
                return self.respond(400, {"error": "Unexpected test credentials/scope"})
            return self.respond(
                200,
                {
                    "access_token": "synthetic-proxy-token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        if self.path == "/emsi.us.occupation/2026.4":
            if self.headers.get("Authorization") != "Bearer synthetic-proxy-token":
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
                        {"name": "Jobs.2025", "type": "Double", "rows": [42, None]}
                    ],
                    "errors": [],
                    "timings": [],
                    "totalRows": 2,
                },
            )
        self.respond(404, {"error": "No fixture for this path"})


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), FixtureHandler).serve_forever()
