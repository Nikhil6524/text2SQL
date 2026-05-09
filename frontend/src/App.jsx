import { useMemo, useState } from "react";

import ChatPage from "./components/ChatPage";
import LoginPage from "./components/LoginPage";
import { chatRequest, loginRequest, productStatsRequest } from "./api/client";

const initialAssistantMessage = {
  role: "assistant",
  content:
    "Hi. Ask me to fetch, insert, or update records in your PostgreSQL database. I will refuse delete and schema-change requests for safety.",
};

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("chatbot_token") || "");
  const [messages, setMessages] = useState([initialAssistantMessage]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [statsError, setStatsError] = useState("");

  const chatHistory = useMemo(
    () =>
      messages.map((msg) => {
        if (msg.role === "assistant" && msg.sql_executed) {
          return {
            role: msg.role,
            content: `${msg.content}\nSQL: ${msg.sql_executed}`,
          };
        }
        return { role: msg.role, content: msg.content };
      }),
    [messages]
  );

  const handleLogin = async ({ username, password }) => {
    const data = await loginRequest({ username, password });
    setToken(data.access_token);
    localStorage.setItem("chatbot_token", data.access_token);
  };

  const handleLogout = () => {
    setToken("");
    localStorage.removeItem("chatbot_token");
    setMessages([initialAssistantMessage]);
    setStats(null);
    setStatsError("");
  };

  const handleLoadStats = async () => {
    setStatsLoading(true);
    setStatsError("");
    try {
      const data = await productStatsRequest({ token });
      setStats(data);
    } catch (error) {
      setStatsError(error.message || "Stats request failed");
    } finally {
      setStatsLoading(false);
    }
  };

  const handleSendMessage = async (message) => {
    const userMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const data = await chatRequest({
        token,
        message,
        history: [...chatHistory, userMessage].slice(-16),
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.reply,
          sql_executed: data.sql_executed,
          data: data.data,
        },
      ]);

      if ("speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(data.reply);
        utterance.rate = 1;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
      }
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: `I hit an error: ${error.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <div className="panel">
        {!token ? (
          <LoginPage onLogin={handleLogin} />
        ) : (
          <ChatPage
            messages={messages}
            loading={loading}
            stats={stats}
            statsLoading={statsLoading}
            statsError={statsError}
            onLoadStats={handleLoadStats}
            onSendMessage={handleSendMessage}
            onLogout={handleLogout}
          />
        )}
      </div>
    </div>
  );
}
