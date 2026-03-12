import { useRef, useCallback } from "react";

/**
 * Hook for playing back 24kHz PCM Int16 audio chunks from Gemini Live API.
 * Supports gapless queued playback and instant stop for barge-in.
 */
export function useAudioPlayback() {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const nextStartTimeRef = useRef(0);
  const sourceNodesRef = useRef<AudioBufferSourceNode[]>([]);
  const isPlayingRef = useRef(false);

  const getContext = useCallback(() => {
    if (!audioCtxRef.current || audioCtxRef.current.state === "closed") {
      audioCtxRef.current = new AudioContext({ sampleRate: 24000 });
      nextStartTimeRef.current = 0;
    }
    return audioCtxRef.current;
  }, []);

  // Pre-warm: create AudioContext early so first audio chunk plays instantly
  const warmup = useCallback(() => {
    const ctx = getContext();
    if (ctx.state === "suspended") ctx.resume();
  }, [getContext]);

  const playChunk = useCallback(
    (base64PCM: string) => {
      const ctx = getContext();
      if (ctx.state === "suspended") {
        ctx.resume();
      }

      // Decode base64 → binary string → Uint8Array (no per-byte char loop)
      const binary = atob(base64PCM);
      const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
      const int16 = new Int16Array(bytes.buffer);

      // Convert Int16 to Float32 — single divisor, no per-sample conditional
      const float32 = new Float32Array(int16.length);
      for (let i = 0; i < int16.length; i++) {
        float32[i] = int16[i] / 32768;
      }

      // Create AudioBuffer
      const buffer = ctx.createBuffer(1, float32.length, 24000);
      buffer.getChannelData(0).set(float32);

      // Schedule for gapless playback
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.connect(ctx.destination);

      const now = ctx.currentTime;
      const startTime = Math.max(now, nextStartTimeRef.current);
      source.start(startTime);
      nextStartTimeRef.current = startTime + buffer.duration;
      isPlayingRef.current = true;

      sourceNodesRef.current.push(source);
      source.onended = () => {
        sourceNodesRef.current = sourceNodesRef.current.filter(
          (n) => n !== source,
        );
        if (sourceNodesRef.current.length === 0) {
          isPlayingRef.current = false;
        }
      };
    },
    [getContext],
  );

  const stop = useCallback(() => {
    // Immediately stop all scheduled audio (for barge-in)
    sourceNodesRef.current.forEach((node) => {
      try {
        node.stop();
      } catch {
        // already stopped
      }
    });
    sourceNodesRef.current = [];
    nextStartTimeRef.current = 0;
    isPlayingRef.current = false;
  }, []);

  const cleanup = useCallback(() => {
    stop();
    audioCtxRef.current?.close();
    audioCtxRef.current = null;
  }, [stop]);

  return { playChunk, stop, cleanup, warmup, isPlayingRef };
}
