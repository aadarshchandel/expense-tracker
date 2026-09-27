const BASE_URL =
  process.env.NODE_ENV === "production" ? "/api" : "http://localhost:8000/api";

export async function fetchExpenses() {
  const res = await fetch(`${BASE_URL}/expenses`);
  const json = await res.json();
  return json.data || [];
}

export async function addExpense(expense) {
  const res = await fetch(`${BASE_URL}/expenses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(expense),
  });
  return res.json();
}

export async function deleteExpense(id) {
  const res = await fetch(`${BASE_URL}/expenses/${id}`, { method: "DELETE" });
  return res.json();
}

export async function fetchTotal() {
  const res = await fetch(`${BASE_URL}/total`);
  return res.json();
}