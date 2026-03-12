import { useRef, useCallback } from "react";

/**
 * Hook for capturing microphone audio as 16kHz PCM Int16 chunks.
 * Uses AudioWorklet for low-latency, non-blocking processing.
 */
export function useAudioCapture(onPCMChunk: (base64: string) => void) {
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);

  const start = useCallback(async () => {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
      },
    });
    streamRef.current = stream;

    const audioCtx = new AudioContext({ sampleRate: 16000 });
    audioCtxRef.current = audioCtx;

    await audioCtx.audioWorklet.addModule("/pcm-processor.js");

    const source = audioCtx.createMediaStreamSource(stream);
    const worklet = new AudioWorkletNode(audioCtx, "pcm-processor");
    workletRef.current = worklet;

    worklet.port.onmessage = (event) => {
      if (event.data.type === "pcm_chunk") {
        // Single native call — avoids N string allocations from a char loop
        const bytes = new Uint8Array(event.data.data as ArrayBuffer);
        const base64 = btoa(String.fromCharCode(...bytes));
        onPCMChunk(base64);
      }
    };

    source.connect(worklet);
    worklet.connect(audioCtx.destination); // required for worklet to process
  }, [onPCMChunk]);

  const stop = useCallback(() => {
    workletRef.current?.disconnect();
    workletRef.current = null;
    audioCtxRef.current?.close();
    audioCtxRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  return { start, stop };
}
