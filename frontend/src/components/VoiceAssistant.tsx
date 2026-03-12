"use client";

import { useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { useGeminiLive } from "@/hooks/useGeminiLive";

interface VoiceAssistantProps {
  onBack: () => void;
}

export const VoiceAssistant = ({ onBack }: VoiceAssistantProps) => {
  const {
    isConnected,
    isListening,
    isSpeaking,
    transcript,
    error,
    startListening,
    stopListening,
    stopPlayback,
    stopSession,
  } = useGeminiLive();

  const transcriptEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript, isSpeaking]);

  const handleOrbClick = async () => {
    if (isSpeaking) {
      stopPlayback();
    } else if (isListening) {
      stopListening();
    } else {
      await startListening();
    }
  };

  const handleBack = () => {
    stopSession();
    onBack();
  };

  const orbState = isListening ? "listening" : isSpeaking ? "speaking" : "idle";

  return (
    <div className="voice-panel">
      {/* Header */}
      <div className="voice-panel-header">
        <button className="voice-back-btn" onClick={handleBack}>
          ← Back to Chat
        </button>
        <h2>🎙️ Voice Assistant</h2>
        <div className="voice-connection-status">
          <span
            className={`status-dot ${isConnected ? "connected" : "disconnected"}`}
          />
          {isConnected ? "Connected" : "Disconnected"}
        </div>
      </div>

      {/* Compact Orb */}
      <div className="voice-orb-container">
        <div className="voice-orb-wrapper">
          {isListening && (
            <>
              <div className="voice-ripple voice-ripple-1" />
              <div className="voice-ripple voice-ripple-2" />
              <div className="voice-ripple voice-ripple-3" />
            </>
          )}
          {isSpeaking && (
            <>
              <div className="voice-speak-ring voice-speak-ring-1" />
              <div className="voice-speak-ring voice-speak-ring-2" />
            </>
          )}
          <button className={`voice-orb ${orbState}`} onClick={handleOrbClick}>
            <div className="voice-orb-inner">
              <div className="voice-orb-icon">
                {isListening ? (
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="6" y="6" width="12" height="12" rx="2" />
                  </svg>
                ) : (
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                    <line x1="12" x2="12" y1="19" y2="22" />
                  </svg>
                )}
              </div>
              <span className="voice-orb-label">
                {isListening
                  ? "Listening…"
                  : isSpeaking
                    ? "Tap to interrupt"
                    : "Click to speak"}
              </span>
            </div>
          </button>
        </div>
      </div>

      {error && <div className="voice-error">{error}</div>}

      {/* Conversation transcript */}
      <div className="voice-conversation">
        {transcript.length === 0 && !isSpeaking && !isListening && (
          <div className="voice-conversation-empty">
            <div className="voice-conversation-empty-icon">🎓</div>
            <p>Click the orb above to start a conversation</p>
            <p className="voice-conversation-empty-hint">
              Ask about admissions, placements, career guidance, and more
            </p>
          </div>
        )}

        {transcript.map((entry, i) => (
          <div key={i} className={`voice-bubble ${entry.role}`}>
            <div className="voice-bubble-avatar">
              {entry.role === "user" ? "🧑" : "🤖"}
            </div>
            <div className="voice-bubble-body">
              <div className="voice-bubble-label">
                {entry.role === "user" ? "You" : "CIT Assistant"}
              </div>
              <div className="voice-bubble-content">
                {entry.role === "assistant" ? (
                  <ReactMarkdown>{entry.text}</ReactMarkdown>
                ) : (
                  <p>{entry.text}</p>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Live speaking indicator */}
        {isSpeaking && (
          <div className="voice-bubble assistant">
            <div className="voice-bubble-avatar">🤖</div>
            <div className="voice-bubble-body">
              <div className="voice-bubble-label">CIT Assistant</div>
              <div className="voice-bubble-content">
                <div className="voice-typing-dots">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Live listening indicator */}
        {isListening && (
          <div className="voice-bubble user">
            <div className="voice-bubble-avatar">🧑</div>
            <div className="voice-bubble-body">
              <div className="voice-bubble-label">You</div>
              <div className="voice-bubble-content">
                <div className="voice-listening-bar">
                  <span />
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={transcriptEndRef} />
      </div>
    </div>
  );
};
