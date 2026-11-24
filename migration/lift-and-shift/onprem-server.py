import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler

class OnPremHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        conn = sqlite3.connect("onprem_legacy.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS legacy_records (id INTEGER PRIMARY KEY, name TEXT, value TEXT)")
        cursor.execute("SELECT id, name, value FROM legacy_records")
        rows = cursor.fetchall()
        conn.close()

        payload = [{"id": r[0], "name": r[1], "value": r[2]} for r in rows]
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))

def run_server(port=9000):
    server = HTTPServer(("0.0.0.0", port), OnPremHandler)
    server.serve_forever()

if __name__ == "__main__":
    run_server()
