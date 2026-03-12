"use client";

import { useState, useEffect } from "react";
import { ConversationView } from "@/components/ConversationView";
import { VoiceAssistant } from "@/components/VoiceAssistant";
import { Sidebar } from "@/components/Sidebar";

export default function Home() {
  const [mode, setMode] = useState<"chat" | "voice">("chat");

  useEffect(() => {
    // Initialize theme from localStorage
    const theme = localStorage.getItem("theme") || "light";
    if (theme === "dark") {
      document.body.classList.add("dark");
    } else {
      document.body.classList.remove("dark");
    }
  }, []);

  return (
    <div className="app">
      <Sidebar />
      <main className="main-content">
        {mode === "chat" ? (
          <ConversationView onSwitchToVoice={() => setMode("voice")} />
        ) : (
          <VoiceAssistant onBack={() => setMode("chat")} />
        )}
      </main>
    </div>
  );
}
