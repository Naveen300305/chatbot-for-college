// pcm-processor.js — AudioWorklet processor for mic capture
// Resamples from browser's native sample rate (usually 48kHz) to 16kHz
// and converts Float32 samples to Int16 PCM for Gemini Live API

class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buffer = [];
    // Send a chunk every ~50ms worth of 16kHz samples = 800 samples
    this._chunkSize = 800;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const inputData = input[0]; // mono channel
    const inputSampleRate = sampleRate; // global in AudioWorklet scope
    const targetRate = 16000;
    const ratio = inputSampleRate / targetRate;

    // Simple linear interpolation downsampling
    for (let i = 0; i < inputData.length; i++) {
      const targetIndex = i / ratio;
      if (Math.floor(targetIndex) >= this._buffer.length || i % Math.round(ratio) === 0) {
        // Clamp to [-1, 1] and convert Float32 to Int16
        const sample = Math.max(-1, Math.min(1, inputData[i]));
        const int16 = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
        this._buffer.push(int16);
      }
    }

    // When buffer reaches chunk size, send to main thread
    while (this._buffer.length >= this._chunkSize) {
      const chunk = this._buffer.splice(0, this._chunkSize);
      const int16Array = new Int16Array(chunk);
      this.port.postMessage({
        type: "pcm_chunk",
        data: int16Array.buffer,
      }, [int16Array.buffer]);
    }

    return true;
  }
}

registerProcessor("pcm-processor", PCMProcessor);
