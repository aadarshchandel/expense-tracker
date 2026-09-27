import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "expenses.json")

UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
USE_REDIS = bool(UPSTASH_URL and UPSTASH_TOKEN)

REDIS_KEY = "expenses_list"


# ---------- Upstash Redis Helpers ----------
def redis_command(*args):
    """Send a command to Upstash Redis REST API."""
    url = f"{UPSTASH_URL}/{'/'.join(str(a) for a in args)}"
    req = Request(url, headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"})
    with urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def redis_get_expenses():
    try:
        result = redis_command("GET", REDIS_KEY)
        raw = result.get("result")
        if not raw:
            return []
        return json.loads(raw)
    except (URLError, json.JSONDecodeError, KeyError):
        return []


def redis_set_expenses(expenses):
    try:
        payload = json.dumps(expenses)
        url = UPSTASH_URL
        body = json.dumps(["SET", REDIS_KEY, payload]).encode("utf-8")
        req = Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {UPSTASH_TOKEN}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except URLError:
        return False


# ---------- Storage Helpers (Redis if available, else JSON file) ----------
def load_expenses():
    if USE_REDIS:
        return redis_get_expenses()
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_expenses(expenses):
    if USE_REDIS:
        return redis_set_expenses(expenses)
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(expenses, f, indent=2)
        return True
    except IOError:
        return False


# ---------- Core Handlers ----------
def get_all():
    return {"status": "ok", "data": load_expenses()}


def get_one(expense_id):
    item = next((e for e in load_expenses() if e["id"] == expense_id), None)
    if item:
        return {"status": "ok", "data": item}
    return {"status": "error", "message": "Not found"}


def add_expense(payload):
    if not payload.get("title") or payload.get("amount") is None:
        return {"status": "error", "message": "title and amount required"}
    expenses = load_expenses()
    new_id = max([e["id"] for e in expenses], default=0) + 1
    item = {
        "id": new_id,
        "title": payload["title"],
        "amount": float(payload["amount"]),
        "category": payload.get("category", "general"),
        "created_at": datetime.utcnow().isoformat(),
    }
    expenses.append(item)
    ok = save_expenses(expenses)
    if not ok and USE_REDIS:
        return {"status": "error", "message": "Failed to save to Redis"}
    return {"status": "ok", "data": item}


def delete_expense(expense_id):
    expenses = load_expenses()
    filtered = [e for e in expenses if e["id"] != expense_id]
    if len(filtered) == len(expenses):
        return {"status": "error", "message": "Not found"}
    ok = save_expenses(filtered)
    if not ok and USE_REDIS:
        return {"status": "error", "message": "Failed to save to Redis"}
    return {"status": "ok", "message": "Deleted"}


def total():
    expenses = load_expenses()
    return {
        "status": "ok",
        "total": sum(e["amount"] for e in expenses),
        "count": len(expenses),
    }


# ---------- HTTP Handler ----------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode("utf-8"))

    def do_OPTIONS(self):
        self._send(200, {"status": "ok"})

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        if path in ("", "/", "/api"):
            self._send(200, {
                "message": "Expense Tracker API",
                "storage": "redis" if USE_REDIS else "file",
                "status": "ok",
            })
        elif path == "/api/expenses":
            self._send(200, get_all())
        elif path.startswith("/api/expenses/"):
            try:
                self._send(200, get_one(int(path.split("/")[-1])))
            except ValueError:
                self._send(400, {"status": "error", "message": "Invalid id"})
        elif path == "/api/total":
            self._send(200, total())
        else:
            self._send(404, {"status": "error", "message": "Route not found"})

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path != "/api/expenses":
            self._send(404, {"status": "error", "message": "Route not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self._send(400, {"status": "error", "message": "Invalid JSON"})
            return
        self._send(201, add_expense(payload))

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/")
        if path.startswith("/api/expenses/"):
            try:
                result = delete_expense(int(path.split("/")[-1]))
                self._send(200 if result["status"] == "ok" else 404, result)
            except ValueError:
                self._send(400, {"status": "error", "message": "Invalid id"})
        else:
            self._send(404, {"status": "error", "message": "Route not found"})

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


# ---------- Local Entry Point ----------
def run_server(port=8000):
    server = HTTPServer(("0.0.0.0", port), Handler)
    storage = "Redis ☁️" if USE_REDIS else "Local JSON 📁"
    print(f"🚀 Backend running at http://localhost:{port}")
    print(f"💾 Storage: {storage}\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()