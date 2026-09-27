# Expense Tracker API

Built with **core Python only** (`http.server`) — no Flask, no Django.

## Endpoints

| Method | Path             | Description       |
| ------ | ---------------- | ----------------- |
| GET    | `/`              | API info          |
| GET    | `/expenses`      | List all expenses |
| GET    | `/expenses/<id>` | Get one expense   |
| POST   | `/expenses`      | Add expense       |
| DELETE | `/expenses/<id>` | Delete expense    |
| GET    | `/total`         | Total amount      |

## Run Locally

```bash
python app.py
```
