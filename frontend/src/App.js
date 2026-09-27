import React, { useEffect, useState } from "react";
import { fetchExpenses, addExpense, deleteExpense } from "./api";

const CATEGORIES = ["general", "food", "transport", "shopping", "bills", "education", "entertainment"];

export default function App() {
  const [expenses, setExpenses] = useState([]);
  const [title, setTitle] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("general");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim() || !amount) return;
    await addExpense({ title: title.trim(), amount: parseFloat(amount), category });
    setTitle("");
    setAmount("");
    setCategory("general");
    loadData();
  };

  const handleDelete = async (id) => {
    await deleteExpense(id);
    loadData();
  };

  const total = expenses.reduce((sum, e) => sum + Number(e.amount), 0);

  return (
    <div className="app">
      <header className="header">
        <h1>💰 Expense Tracker</h1>
        <p className="subtitle">Track your spending with React + Core Python</p>
      </header>

      <div className="summary">
        <div className="summary-card">
          <span className="summary-label">Total Spent</span>
          <span className="summary-value">${total.toFixed(2)}</span>
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
          placeholder="Amount"
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
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        <button className="btn-primary" type="submit">+ Add</button>
      </form>

      {error && <div className="error">{error}</div>}

      {loading ? (
        <div className="empty">Loading...</div>
      ) : expenses.length === 0 ? (
        <div className="empty">No expenses yet. Add your first one above! 🎉</div>
      ) : (
        <ul className="list">
          {expenses.map((exp) => (
            <li key={exp.id} className="list-item">
              <div className="list-left">
                <span className="list-title">{exp.title}</span>
                <span className="badge">{exp.category}</span>
              </div>
              <div className="list-right">
                <span className="list-amount">${Number(exp.amount).toFixed(2)}</span>
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

      <footer className="footer">
        Built with React ⚛️ + Python 🐍
      </footer>
    </div>
  );
}