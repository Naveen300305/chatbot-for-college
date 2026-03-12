import { useState, useRef, useCallback } from "react";
import { useAudioCapture } from "./useAudioCapture";
import { useAudioPlayback } from "./useAudioPlayback";

export interface TranscriptEntry {
  role: "user" | "assistant";
  text: string;
}

const GEMINI_WS_URL =
  "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent";

const BACKEND_URL = "http://localhost:8000";

export function useGeminiLive() {
  const [isConnected, setIsConnected] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const setupCompleteRef = useRef(false);
  const startingRef = useRef(false); // prevent double starts
  const currentUserTextRef = useRef("");
  const currentAssistantTextRef = useRef("");

  const { playChunk, stop: stopPlayback, cleanup: cleanupPlayback, warmup: warmupPlayback, isPlayingRef } =
    useAudioPlayback();

  // Send audio chunks to Gemini when mic captures them
  const sendAudioChunk = useCallback((base64PCM: string) => {
    if (
      wsRef.current?.readyState === WebSocket.OPEN &&
      setupCompleteRef.current
    ) {
      wsRef.current.send(
        JSON.stringify({
          realtimeInput: {
            audio: {
              data: base64PCM,
              mimeType: "audio/pcm;rate=16000",
            },
          },
        }),
      );
    }
  }, []);

  const { start: startMic, stop: stopMic } = useAudioCapture(sendAudioChunk);

  // Handle function calls from Gemini (RAG queries)
  const handleToolCall = useCallback(
    async (toolCall: { functionCalls: Array<{ id: string; name: string; args: Record<string, string> }> }) => {
      console.log("[Gemini] Tool call received:", JSON.stringify(toolCall));
      const results = [];
      for (const fc of toolCall.functionCalls) {
        if (fc.name === "query_college_info") {
          try {
            const resp = await fetch(`${BACKEND_URL}/api/rag-query`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                query: fc.args.query,
                category: fc.args.category || null,
              }),
            });
            const data = await resp.json();
            console.log("[Gemini] RAG result:", data.agent, data.sources);
            results.push({
              id: fc.id,
              name: fc.name,
              response: { result: data.context || "No information found." },
            });
          } catch (e) {
            console.error("[Gemini] RAG query failed:", e);
            results.push({
              id: fc.id,
              name: fc.name,
              response: { result: "Failed to query the knowledge base." },
            });
          }
        }
      }

      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(
          JSON.stringify({
            toolResponse: {
              functionResponses: results,
            },
          }),
        );
        console.log("[Gemini] Tool response sent");
      }
    },
    [],
  );

  // Process incoming WebSocket messages from Gemini
  const handleMessage = useCallback(
    async (event: MessageEvent) => {
      try {
        // Gemini sends binary WebSocket frames — decode Blob to text first
        const rawData =
          event.data instanceof Blob
            ? await (event.data as Blob).text()
            : (event.data as string);
        const msg = JSON.parse(rawData);
        console.log("[Gemini] Message:", JSON.stringify(msg).slice(0, 300));

        // Setup complete — session is ready for audio
        if (msg.setupComplete) {
          console.log("[Gemini] ✅ Setup complete — ready for audio");
          setupCompleteRef.current = true;
          return;
        }

        // Audio data from model
        if (msg.serverContent?.modelTurn?.parts) {
          for (const part of msg.serverContent.modelTurn.parts) {
            if (part.inlineData?.data) {
              setIsSpeaking(true);
              playChunk(part.inlineData.data);
            }
          }
        }

        // Turn complete — model finished speaking
        if (msg.serverContent?.turnComplete) {
          setIsSpeaking(false);
          if (currentAssistantTextRef.current) {
            const text = currentAssistantTextRef.current;
            setTranscript((prev) => [...prev, { role: "assistant", text }]);
            currentAssistantTextRef.current = "";
          }
        }

        // Interrupted — user barged in
        if (msg.serverContent?.interrupted) {
          stopPlayback();
          setIsSpeaking(false);
        }

        // Input transcription (user's speech)
        if (msg.serverContent?.inputTranscription?.text) {
          currentUserTextRef.current +=
            msg.serverContent.inputTranscription.text;
        }

        // Input transcription complete
        if (msg.serverContent?.inputTranscription?.finished) {
          if (currentUserTextRef.current) {
            const text = currentUserTextRef.current;
            setTranscript((prev) => [...prev, { role: "user", text }]);
            currentUserTextRef.current = "";
          }
        }

        // Output transcription (model's speech as text)
        if (msg.serverContent?.outputTranscription?.text) {
          currentAssistantTextRef.current +=
            msg.serverContent.outputTranscription.text;
        }

        // Tool call from model
        if (msg.toolCall) {
          handleToolCall(msg.toolCall);
        }
      } catch (e) {
        console.error("[Gemini] Error processing message:", e);
      }
    },
    [playChunk, stopPlayback, handleToolCall],
  );

  const startSession = useCallback(async (): Promise<boolean> => {
    // Prevent double starts
    if (startingRef.current) {
      console.log("[Gemini] Session start already in progress, skipping");
      return false;
    }
    startingRef.current = true;

    setError(null);
    setTranscript([]);
    setupCompleteRef.current = false;
    currentUserTextRef.current = "";
    currentAssistantTextRef.current = "";

    try {
      // 1. Get ephemeral token from backend
      console.log("[Gemini] Fetching ephemeral token...");
      const tokenResp = await fetch(`${BACKEND_URL}/api/ephemeral-token`, {
        method: "POST",
      });
      const tokenData = await tokenResp.json();
      console.log("[Gemini] Token response:", tokenData.token ? "received" : "FAILED", tokenData.error || "");

      if (tokenData.error) {
        setError(`Token error: ${tokenData.error}`);
        startingRef.current = false;
        return false;
      }

      // 2. Open WebSocket to Gemini Live API with ephemeral token
      const wsUrl = `${GEMINI_WS_URL}?key=${tokenData.token}`;
      console.log("[Gemini] Opening WebSocket...");

      return new Promise<boolean>((resolve) => {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        const timeout = setTimeout(() => {
          console.error("[Gemini] Connection timeout after 15s");
          setError("Connection timeout. Please try again.");
          ws.close();
          startingRef.current = false;
          resolve(false);
        }, 15000);

        ws.onopen = () => {
          console.log("[Gemini] WebSocket opened, sending setup...");
          setIsConnected(true);
          // Pre-warm audio playback so first response plays instantly
          warmupPlayback();

          // Send session config as first message
          const setupMsg = { setup: tokenData.config };
          console.log("[Gemini] Setup message:", JSON.stringify(setupMsg).slice(0, 500));
          ws.send(JSON.stringify(setupMsg));
        };

        ws.onmessage = async (event) => {
          // Decode Blob to text first — Gemini sends binary WebSocket frames
          const rawData =
            event.data instanceof Blob
              ? await (event.data as Blob).text()
              : (event.data as string);

          // Check for setupComplete to resolve the promise
          try {
            const msg = JSON.parse(rawData);
            if (msg.setupComplete) {
              clearTimeout(timeout);
              startingRef.current = false;
              handleMessage(new MessageEvent("message", { data: rawData }));
              resolve(true);
              return;
            }
          } catch {
            // fall through
          }
          handleMessage(new MessageEvent("message", { data: rawData }));
        };

        ws.onerror = () => {
          console.error("[Gemini] WebSocket error event fired");
          setError("Connection error. Please try again.");
          setIsConnected(false);
          clearTimeout(timeout);
          startingRef.current = false;
          resolve(false);
        };

        ws.onclose = (event) => {
          console.log(
            `[Gemini] WebSocket closed: code=${event.code} reason="${event.reason}" clean=${event.wasClean}`,
          );
          if (event.code !== 1000 && event.code !== 1005) {
            setError(`Connection closed (code ${event.code}): ${event.reason || "unknown reason"}`);
          }
          setIsConnected(false);
          setIsListening(false);
          setIsSpeaking(false);
          setupCompleteRef.current = false;
          stopMic();
          clearTimeout(timeout);
          startingRef.current = false;
        };
      });
    } catch (e) {
      console.error("[Gemini] Failed to start session:", e);
      setError("Failed to connect. Check your backend.");
      startingRef.current = false;
      return false;
    }
  }, [handleMessage, stopMic, warmupPlayback]);

  const startListening = useCallback(async () => {
    // If not connected or setup not done, start a new session
    if (!setupCompleteRef.current) {
      const success = await startSession();
      if (!success) return;
    }

    // Stop any ongoing playback (barge-in)
    if (isPlayingRef.current) {
      stopPlayback();
    }

    console.log("[Gemini] Starting mic...");
    await startMic();
    setIsListening(true);
    console.log("[Gemini] ✅ Listening started");
  }, [startSession, startMic, stopPlayback, isPlayingRef]);

  const stopListening = useCallback(() => {
    stopMic();
    setIsListening(false);
    console.log("[Gemini] Mic stopped, still connected");
  }, [stopMic]);

  const stopSession = useCallback(() => {
    stopMic();
    stopPlayback();
    cleanupPlayback();
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
    setIsListening(false);
    setIsSpeaking(false);
    setupCompleteRef.current = false;
    startingRef.current = false;
  }, [stopMic, stopPlayback, cleanupPlayback]);

  return {
    isConnected,
    isListening,
    isSpeaking,
    transcript,
    error,
    startListening,
    stopListening,
    stopPlayback,
    stopSession,
  };
}
