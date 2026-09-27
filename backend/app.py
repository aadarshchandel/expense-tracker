import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "expenses.json")

# ---------- Storage Helpers ----------
def load_expenses():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_expenses(expenses):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(expenses, f, indent=2)
    except IOError:
        pass  # Vercel read-only

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
        "created_at": datetime.utcnow().isoformat()
    }
    expenses.append(item)
    save_expenses(expenses)
    return {"status": "ok", "data": item}

def delete_expense(expense_id):
    expenses = load_expenses()
    filtered = [e for e in expenses if e["id"] != expense_id]
    if len(filtered) == len(expenses):
        return {"status": "error", "message": "Not found"}
    save_expenses(filtered)
    return {"status": "ok", "message": "Deleted"}

def total():
    expenses = load_expenses()
    return {
        "status": "ok",
        "total": sum(e["amount"] for e in expenses),
        "count": len(expenses)
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
            self._send(200, {"message": "Expense Tracker API", "status": "ok"})
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


def run_server(port=8000):
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"🚀 Backend running at http://localhost:{port}")
    print("Endpoints: GET/POST /api/expenses, DELETE /api/expenses/<id>, GET /api/total\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()