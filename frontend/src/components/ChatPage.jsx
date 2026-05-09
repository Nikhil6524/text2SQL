import { useEffect, useMemo, useRef, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

function formatValue(value) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function formatNumber(value) {
  if (value === null || value === undefined) return "-";
  if (Number.isNaN(Number(value))) return "-";
  return Number(value).toFixed(2);
}

function buildLineSeries(histogram, label, color) {
  const bins = histogram?.bins || [];
  const counts = histogram?.counts || [];
  if (bins.length < 2 || counts.length === 0) {
    return {
      data: {
        labels: [],
        datasets: [],
      },
      options: {},
    };
  }

  const labels = bins.slice(0, -1).map((edge, idx) => {
    const next = bins[idx + 1];
    const midpoint = (edge + next) / 2;
    return midpoint.toFixed(1);
  });

  return {
    data: {
      labels,
      datasets: [
        {
          label,
          data: counts,
          borderColor: color,
          backgroundColor: "rgba(126, 246, 255, 0.2)",
          tension: 0.35,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: { color: "#cad8e8" },
          grid: { color: "rgba(255,255,255,0.08)" },
        },
        y: {
          ticks: { color: "#cad8e8" },
          grid: { color: "rgba(255,255,255,0.08)" },
        },
      },
    },
  };
}

function Heatmap({ heatmap }) {
  const labels = heatmap?.labels || [];
  const matrix = heatmap?.matrix || [];

  if (!labels.length || !matrix.length) {
    return <div className="stats-empty">No heatmap data yet.</div>;
  }

  const maxAbs = Math.max(
    0.01,
    ...matrix.flat().map((value) => Math.abs(value || 0))
  );

  return (
    <div className="heatmap">
      <div className="heatmap-grid" style={{ gridTemplateColumns: `120px repeat(${labels.length}, 1fr)` }}>
        <div className="heatmap-cell heatmap-header"></div>
        {labels.map((label) => (
          <div key={`col-${label}`} className="heatmap-cell heatmap-header">
            {label}
          </div>
        ))}

        {labels.map((rowLabel, rowIdx) => (
          <div key={`row-${rowLabel}`} className="heatmap-row">
            <div className="heatmap-cell heatmap-header">{rowLabel}</div>
            {matrix[rowIdx].map((value, colIdx) => {
              const intensity = Math.abs(value) / maxAbs;
              const hue = value >= 0 ? 180 : 12;
              const background = `hsla(${hue}, 85%, 55%, ${0.15 + intensity * 0.65})`;
              return (
                <div key={`cell-${rowIdx}-${colIdx}`} className="heatmap-cell" style={{ background }}>
                  {value.toFixed(2)}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}

function StatsPanel({ stats, loading, error, onLoadStats }) {
  const costSeries = useMemo(
    () => buildLineSeries(stats?.histograms?.cost, "Cost distribution", "#7ef6ff"),
    [stats]
  );
  const ratingSeries = useMemo(
    () => buildLineSeries(stats?.histograms?.rating, "Rating distribution", "#ffd166"),
    [stats]
  );

  return (
    <div className="stats-panel">
      <div className="stats-header">
        <div>
          <h3 className="stats-title">Product Analytics</h3>
          <p className="stats-subtitle">Distribution curves and correlations built from live product data.</p>
        </div>
        <button className="primary-btn" onClick={onLoadStats} disabled={loading}>
          {loading ? "Loading..." : "Refresh stats"}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {!stats && !loading && !error && (
        <div className="stats-empty">No stats loaded yet. Click refresh to load analytics.</div>
      )}

      {stats && (
        <div className="stats-grid">
          <div className="stats-card">
            <h4>Summary</h4>
            <div className="stats-metrics">
              <div>
                <span>Total products</span>
                <strong>{stats.summary?.count ?? 0}</strong>
              </div>
              <div>
                <span>Cost avg</span>
                <strong>{formatNumber(stats.summary?.cost?.avg)}</strong>
              </div>
              <div>
                <span>Rating avg</span>
                <strong>{formatNumber(stats.summary?.rating?.avg)}</strong>
              </div>
              <div>
                <span>Depreciation avg</span>
                <strong>{formatNumber(stats.summary?.depreciation_per_year?.avg)}</strong>
              </div>
            </div>
          </div>

          <div className="stats-card">
            <h4>Cost distribution</h4>
            <div className="chart-wrap">
              <Line data={costSeries.data} options={costSeries.options} />
            </div>
          </div>

          <div className="stats-card">
            <h4>Rating distribution</h4>
            <div className="chart-wrap">
              <Line data={ratingSeries.data} options={ratingSeries.options} />
            </div>
          </div>

          <div className="stats-card">
            <h4>Correlation heatmap</h4>
            <Heatmap heatmap={stats.heatmap} />
          </div>
        </div>
      )}
    </div>
  );
}

export default function ChatPage({
  messages,
  loading,
  stats,
  statsLoading,
  statsError,
  onLoadStats,
  onSendMessage,
  onLogout,
}) {
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [activeTab, setActiveTab] = useState("chat");

  const messageEndRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const sendMessage = async () => {
    const message = input.trim();
    if (!message || loading) return;
    setInput("");
    await onSendMessage(message);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const handleMic = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      window.alert("Speech recognition is not supported in this browser.");
      return;
    }

    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      setListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);
    recognition.onresult = (event) => {
      const transcript = event.results?.[0]?.[0]?.transcript || "";
      if (transcript) {
        setInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  return (
    <div className="chat-wrap">
      <aside className="sidebar">
        <span className="badge">Authenticated</span>
        <h2>Safe DB Controls</h2>
        <p>
          Allowed: SELECT, INSERT, UPDATE
          <br />
          Blocked: DELETE, DROP, ALTER, TRUNCATE and all schema changes
        </p>
        <p>
          Try:
          <br />
          "Add a new user named Asha with email asha@example.com"
          <br />
          "Update order 18 status to shipped"
        </p>
        <p>
          Analytics:
          <br />
          Open the Stats tab to view distribution curves and heatmaps.
        </p>
        <button className="ghost-btn" onClick={onLogout}>
          Logout
        </button>
      </aside>

      <section className="chat-main">
        <div className="chat-header">
          <h3 className="chat-title">Data Chat</h3>
          <div className="chat-tabs">
            <button
              className={`tab-btn ${activeTab === "chat" ? "active" : ""}`}
              type="button"
              onClick={() => setActiveTab("chat")}
            >
              Chat
            </button>
            <button
              className={`tab-btn ${activeTab === "stats" ? "active" : ""}`}
              type="button"
              onClick={() => setActiveTab("stats")}
            >
              Stats
            </button>
            <span className="badge">Model via Groq</span>
          </div>
        </div>

        {activeTab === "chat" ? (
          <>
            <div className="messages">
              {messages.map((messageItem, index) => (
                <article className={`msg ${messageItem.role}`} key={`${messageItem.role}-${index}`}>
                  {messageItem.content}

                  {messageItem.sql_executed && <div className="sql-chip">SQL: {messageItem.sql_executed}</div>}

                  {Array.isArray(messageItem.data) && messageItem.data.length > 0 && (
                    <table className="result-table">
                      <thead>
                        <tr>
                          {Object.keys(messageItem.data[0]).map((column) => (
                            <th key={column}>{column}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {messageItem.data.slice(0, 8).map((row, rowIndex) => (
                          <tr key={rowIndex}>
                            {Object.keys(messageItem.data[0]).map((column) => (
                              <td key={`${rowIndex}-${column}`}>{formatValue(row[column])}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </article>
              ))}

              {loading && <div className="loading">Thinking and preparing a safe SQL action...</div>}
              <div ref={messageEndRef} />
            </div>

            <div className="chat-input">
              <div className="input-row">
                <input
                  placeholder="Ask for data retrieval, insert, or update..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <button className="mic-btn" onClick={handleMic} type="button">
                  {listening ? "Stop" : "Mic"}
                </button>
                <button className="send-btn" onClick={sendMessage} type="button" disabled={loading}>
                  Send
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="stats-scroll">
            <StatsPanel
              stats={stats}
              loading={statsLoading}
              error={statsError}
              onLoadStats={onLoadStats}
            />
          </div>
        )}
      </section>
    </div>
  );
}
