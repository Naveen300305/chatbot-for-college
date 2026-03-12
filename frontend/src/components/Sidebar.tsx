"use client";

import { useState, useEffect } from "react";

interface SidebarProps {
  sessionStats?: { totalQuestions: number; agentsUsed: Record<string, number> };
}

export const Sidebar = ({ sessionStats }: SidebarProps) => {
  const [isOpen, setIsOpen] = useState(true);
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Check if dark mode is already set
    const isDarkMode = document.body.classList.contains("dark");
    setIsDark(isDarkMode);
  }, []);

  const toggleDarkMode = () => {
    setIsDark(!isDark);
    document.body.classList.toggle("dark");
    localStorage.setItem("theme", !isDark ? "dark" : "light");
  };

  return (
    <aside className={`sidebar ${isOpen ? "open" : "closed"}`}>
      <div className="sidebar-header">
        <h2>🎓 CIT Bot</h2>
        <div className="header-controls">
          <button
            className="theme-toggle-btn"
            onClick={toggleDarkMode}
            title={isDark ? "Light mode" : "Dark mode"}
          >
            {isDark ? "☀️" : "🌙"}
          </button>
          <button className="toggle-btn" onClick={() => setIsOpen(!isOpen)}>
            {isOpen ? "◄" : "►"}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="sidebar-content">
          <div className="session-stats">
            <h3>Session Stats</h3>
            <div className="stat">
              <span>Questions Asked:</span>
              <strong>{sessionStats?.totalQuestions || 0}</strong>
            </div>

            {sessionStats?.agentsUsed &&
              Object.entries(sessionStats.agentsUsed).length > 0 && (
                <div className="agents-used">
                  <h4>Agents Used:</h4>
                  <ul>
                    {Object.entries(sessionStats.agentsUsed).map(
                      ([agent, count]) => (
                        <li key={agent}>
                          <span className="agent-name">{agent}:</span>
                          <span className="agent-count">{count}</span>
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              )}
          </div>

          <div className="divider"></div>

          <div className="agents-info">
            <h3>🤖 Available Agents</h3>
            <ul>
              <li>📚 Admissions</li>
              <li>💼 Career Guidance</li>
              <li>📊 Placements</li>
            </ul>
          </div>

          <div className="sidebar-footer">
            <button className="new-chat-btn">+ New Chat</button>
            <p className="sidebar-version">v1.0 • Powered by AI</p>
          </div>
        </div>
      )}
    </aside>
  );
};
