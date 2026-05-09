import { useState } from "react";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await onLogin({ username, password });
    } catch (err) {
      setError(err.message || "Unable to login");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-wrap">
      <div className="login-hero">
        <span className="badge">Voice + SQL Agent</span>
        <h1>Conversational Data Copilot</h1>
        <p>
          Talk to your PostgreSQL data in natural language. It can fetch, add, and update records while
          automatically blocking destructive actions.
        </p>
      </div>

      <form className="login-card" onSubmit={handleSubmit}>
        <h2 className="title-sm">Login</h2>
        <p className="subtle">Use backend credentials from your `.env`.</p>

        <div>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="admin"
            autoComplete="username"
          />
        </div>

        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="admin123"
            autoComplete="current-password"
          />
        </div>

        {error && <div className="error">{error}</div>}

        <button className="primary-btn" type="submit" disabled={submitting}>
          {submitting ? "Signing in..." : "Enter Workspace"}
        </button>
      </form>
    </div>
  );
}
