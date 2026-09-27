import React, { useEffect, useState } from "react";
import { fetchExpenses, addExpense, deleteExpense } from "./api";

const CATEGORIES = [
  "general",
  "food",
  "transport",
  "shopping",
  "bills",
  "education",
  "entertainment",
];

// Currencies + fallback rates (1 USD = X)
const CURRENCIES = {
  USD: { symbol: "$", label: "USD", flag: "🇺🇸", fallbackRate: 1 },
  INR: { symbol: "₹", label: "INR", flag: "🇮🇳", fallbackRate: 83.5 },
};

// Exchange rate API (free, no key required)
const RATES_API = "https://open.er-api.com/v6/latest/USD";

export default function App() {
  const [expenses, setExpenses] = useState([]);
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("general");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [rates, setRates] = useState({
    USD: CURRENCIES.USD.fallbackRate,
    INR: CURRENCIES.INR.fallbackRate,
  });

  // ---------- Load expenses ----------
  const loadData = async () => {
    try {
      setLoading(true);
      const data = await fetchExpenses();
      setExpenses(data);
      setError("");
    } catch (e) {
      setError("Failed to load expenses");
    } finally {
      setLoading(false);
    }
  };

  // ---------- Fetch live exchange rates ----------
  const loadRates = async () => {
    try {
      const res = await fetch(RATES_API);
      const json = await res.json();
      if (json && json.rates) {
        setRates({
          USD: 1,
          INR: json.rates.INR || CURRENCIES.INR.fallbackRate,
        });
      }
    } catch (e) {
      console.warn("Using fallback exchange rates", e);
    }
  };

  useEffect(() => {
    loadData();
    loadRates();
  }, []);

  // ---------- Add expense ----------
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !amount) return;

    // Store amount in the CURRENTLY SELECTED currency
    // (we'll convert to USD as the base for storage)
    const amountInSelectedCurrency = parseFloat(amount);
    const amountInUSD = amountInSelectedCurrency / rates[currency];

    await addExpense({
      title: title.trim(),
      amount: amountInUSD, // always store in USD as base
      category,
    });

    setTitle("");
    setAmount("");
    setCategory("general");
    loadData();
  };

  // ---------- Delete expense ----------
  const handleDelete = async (id) => {
    await deleteExpense(id);
    loadData();
  };

  // ---------- Convert amount from USD base to selected currency ----------
  const convert = (amountInUSD) => amountInUSD * rates[currency];

  // ---------- Format money ----------
  const format = (amountInUSD) => {
    const converted = convert(amountInUSD);
    return `${CURRENCIES[currency].symbol}${converted.toFixed(2)}`;
  };

  const totalUSD = expenses.reduce((sum, e) => sum + Number(e.amount), 0);

  return (
    <div className="app">
      <header className="header">
        <h1>💰 Expense Tracker</h1>
        <p className="subtitle">Track your spending with React + Core Python</p>

        {/* Currency switcher */}
        <div className="currency-switcher">
          {Object.keys(CURRENCIES).map((key) => (
            <button
              key={key}
              className={`currency-btn ${currency === key ? "active" : ""}`}
              onClick={() => setCurrency(key)}
            >
              {CURRENCIES[key].flag} {CURRENCIES[key].label}
            </button>
          ))}
        </div>

        {/* Live rate info */}
        <p className="rate-info">
          1 USD = {rates.INR.toFixed(2)} INR
        </p>
      </header>

      <div className="summary">
        <div className="summary-card">
          <span className="summary-label">Total Spent</span>
          <span className="summary-value">{format(totalUSD)}</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">Transactions</span>
          <span className="summary-value">{expenses.length}</span>
        </div>
      </div>

      <form className="form" onSubmit={handleSubmit}>
        <input
          className="input"
          type="text"
          placeholder="What did you buy?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <input
          className="input"
          type="number"
          step="0.01"
          min="0"
          placeholder={`Amount (${CURRENCIES[currency].symbol})`}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
        <select
          className="input"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <button className="btn-primary" type="submit">
          + Add
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="empty">Loading...</div>
      ) : expenses.length === 0 ? (
        <div className="empty">
          No expenses yet. Add your first one above! 🎉
        </div>
      ) : (
        <ul className="list">
          {expenses.map((exp) => (
            <li key={exp.id} className="list-item">
              <div className="list-left">
                <span className="list-title">{exp.title}</span>
                <span className="badge">{exp.category}</span>
              </div>
              <div className="list-right">
                <span className="list-amount">{format(Number(exp.amount))}</span>
                <button
                  className="btn-delete"
                  onClick={() => handleDelete(exp.id)}
                  aria-label="Delete"
                >
                  ✕
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <footer className="footer">Built with React ⚛️ + Python 🐍</footer>
    </div>
  );
}