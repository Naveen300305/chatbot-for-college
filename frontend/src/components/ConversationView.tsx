"use client";

import { useState, useEffect, useRef } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
  agent?: string;
  confidence?: number;
  sources?: string[];
  timestamp?: string;
}

interface ConversationViewProps {
  onSwitchToVoice: () => void;
}

export const ConversationView = ({
  onSwitchToVoice,
}: ConversationViewProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [transcript, setTranscript] = useState("");
  const [currentAgent, setCurrentAgent] = useState("");
  const [agentConfidence, setAgentConfidence] = useState<number | null>(null);
  const [followupSuggestions, setFollowupSuggestions] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const transcriptRef = useRef("");

  // Helper function to generate follow-up suggestions
  const generateFollowups = (responseText: string): string[] => {
    const keywords = responseText.match(/\b[A-Z][a-z]+\b/g) || [];
    return [
      `Tell me more about ${keywords[0] || "that"}`,
      `What about ${keywords[1] || "other options"}?`,
      "How does this compare to others?",
    ];
  };

  useEffect(() => {
    wsRef.current = new WebSocket("ws://localhost:8000/ws/chat");

    wsRef.current.onmessage = (event: Event) => {
      if (!(event instanceof MessageEvent)) return;

      const data = JSON.parse(event.data as string);

      if (data.type === "text_chunk") {
        transcriptRef.current += data.content;
        setTranscript(transcriptRef.current);
      } else if (data.type === "agent_selected") {
        setCurrentAgent(data.agent);
        setAgentConfidence(data.confidence);
      } else if (data.type === "complete") {
        const responseContent = transcriptRef.current;

        // Add assistant message
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: responseContent,
            agent: data.agent || currentAgent,
            confidence:
              data.confidence !== undefined
                ? data.confidence
                : agentConfidence || 0,
            sources: data.sources,
            timestamp: new Date().toISOString(),
          },
        ]);

        // Generate follow-up suggestions
        const suggestions = generateFollowups(responseContent);
        setFollowupSuggestions(suggestions);

        // Reset for next message
        transcriptRef.current = "";
        setTranscript("");
        setIsProcessing(false);
      } else if (data.type === "error") {
        console.error("Error:", data.message);
        setIsProcessing(false);
        transcriptRef.current = "";
        setTranscript("");

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `❌ ${data.message}`,
            timestamp: new Date().toISOString(),
          },
        ]);
      }
    };

    wsRef.current.onerror = () => {
      // Suppress error on unmount / mode switch
      setIsProcessing(false);
    };

    wsRef.current.onopen = () => {
      console.log("WebSocket connected");
    };

    return () => wsRef.current?.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, transcript]);

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputText.trim() || isProcessing) return;

    const userMessage = inputText;
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: userMessage,
        timestamp: new Date().toISOString(),
      },
    ]);

    setIsProcessing(true);
    transcriptRef.current = "";
    setTranscript("");
    setInputText("");

    wsRef.current?.send(
      JSON.stringify({
        type: "text_query",
        content: userMessage,
      }),
    );
  };

  const handleFollowupClick = (question: string) => {
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: question,
        timestamp: new Date().toISOString(),
      },
    ]);

    setIsProcessing(true);
    transcriptRef.current = "";
    setTranscript("");

    wsRef.current?.send(
      JSON.stringify({
        type: "text_query",
        content: question,
      }),
    );
  };

  return (
    <div className="conversation-view">
      <div className="conversation-header">
        <div className="header-content">
          <h1>🎓 CIT College Assistant</h1>
          <p>Ask anything about admissions, careers, or placements</p>
        </div>
      </div>

      <div className="messages-container">
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            {msg.role === "assistant" && (
              <>
                <div className="agent-badge">
                  🤖 {msg.agent} ({msg.confidence?.toFixed(1)}% confidence)
                </div>
              </>
            )}
            <div className="message-content">
              {msg.content.split("\n").map((line, idx) => (
                <p key={idx}>{line.trim() || "\u00A0"}</p>
              ))}
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="sources">
                {msg.sources.map((source, j) => (
                  <span key={j} className="source-tag">
                    📎 {source}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {/* Streaming text — shown in both modes */}
        {transcript && (
          <div className="message assistant streaming">
            <div className="agent-badge">
              🤖 {currentAgent} ({agentConfidence?.toFixed(1)}%)
            </div>
            <div className="message-content">
              {transcript.split("\n").map((line, idx, arr) => (
                <p key={idx}>
                  {line.trim() || "\u00A0"}
                  {idx === arr.length - 1 ? "▌" : ""}
                </p>
              ))}
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {followupSuggestions.length > 0 && !isProcessing && (
        <div className="followup-suggestions">
          <p>💡 You might also want to ask:</p>
          {followupSuggestions.map((suggestion, i) => (
            <button
              key={i}
              className="followup-btn"
              onClick={() => handleFollowupClick(suggestion)}
            >
              ➤ {suggestion}
            </button>
          ))}
        </div>
      )}

      <div className="input-section">
        <form onSubmit={handleTextSubmit} className="input-form">
          <div className="input-wrapper">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Ask me anything about CIT..."
              disabled={isProcessing}
              className="text-input"
            />
            <button
              type="submit"
              disabled={isProcessing || !inputText.trim()}
              className="send-btn"
            >
              📤 Send
            </button>
            <button
              type="button"
              className="voice-mode-btn"
              onClick={onSwitchToVoice}
              title="Switch to Voice Assistant"
            >
              🎤
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
