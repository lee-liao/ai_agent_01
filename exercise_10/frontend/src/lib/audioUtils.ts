/**
 * Audio utilities for WebRTC voice calls
 */

export interface AudioDevice {
  deviceId: string;
  label: string;
}

/**
 * Get available audio input devices (microphones)
 */
export async function getAudioDevices(): Promise<AudioDevice[]> {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices
      .filter(device => device.kind === 'audioinput')
      .map(device => ({
        deviceId: device.deviceId,
        label: device.label || `Microphone ${device.deviceId.substring(0, 5)}`
      }));
  } catch (error) {
    console.error('Error getting audio devices:', error);
    return [];
  }
}

/**
 * Request microphone access
 */
export async function requestMicrophoneAccess(deviceId?: string): Promise<MediaStream | null> {
  try {
    const constraints: MediaStreamConstraints = {
      audio: deviceId ? { deviceId: { exact: deviceId } } : true,
      video: false
    };
    
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    console.log('🎤 Microphone access granted');
    return stream;
  } catch (error: any) {
    console.error('Error accessing microphone:', error);
    
    if (error.name === 'NotAllowedError') {
      alert('Microphone access denied. Please allow microphone access in your browser settings.');
    } else if (error.name === 'NotFoundError') {
      alert('No microphone found. Please connect a microphone and try again.');
    } else {
      alert(`Microphone error: ${error.message}`);
    }
    
    return null;
  }
}

/**
 * Stop all tracks in a media stream
 */
export function stopMediaStream(stream: MediaStream | null) {
  if (stream) {
    stream.getTracks().forEach(track => {
      track.stop();
      console.log('🛑 Stopped track:', track.kind);
    });
  }
}

/**
 * Get audio level from audio stream (for visualization)
 */
export function getAudioLevel(stream: MediaStream): number {
  try {
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(stream);
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    
    microphone.connect(analyser);
    analyser.getByteFrequencyData(dataArray);
    
    // Calculate average level
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    return average / 255; // Normalize to 0-1
  } catch (error) {
    console.error('Error getting audio level:', error);
    return 0;
  }
}

/**
 * Create an audio recorder that sends chunks to WebSocket
 */
export class AudioRecorder {
  private mediaRecorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private onAudioChunk?: (chunk: Blob) => void;
  private onTranscript?: (text: string) => void;
  
  constructor(
    onAudioChunk?: (chunk: Blob) => void,
    onTranscript?: (text: string) => void
  ) {
    this.onAudioChunk = onAudioChunk;
    this.onTranscript = onTranscript;
  }
  
  async start(deviceId?: string): Promise<boolean> {
    this.stream = await requestMicrophoneAccess(deviceId);
    
    if (!this.stream) {
      return false;
    }
    
    try {
      // Try formats in order of Whisper API compatibility
      let mimeType = '';
      
      // Try various formats in order of preference
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        mimeType = 'audio/webm;codecs=opus';  // Best compression, widely supported
      } else if (MediaRecorder.isTypeSupported('audio/wav')) {
        mimeType = 'audio/wav';  // Direct compatibility with Whisper API
      } else if (MediaRecorder.isTypeSupported('audio/mpeg')) {
        mimeType = 'audio/mpeg';  // Alternative format
      } else {
        mimeType = 'audio/webm';  // Fallback
      }
      
      const options = {
        mimeType: mimeType,
        audioBitsPerSecond: 16000
      };
      
      this.mediaRecorder = new MediaRecorder(this.stream, options);
      
      // Send audio chunks every 1 second
      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && this.onAudioChunk) {
          this.onAudioChunk(event.data);
          
          // NOTE: Simulated transcription is DISABLED
          // In production, the backend would send real transcriptions via WebSocket
          // Students can implement this by:
          // 1. Sending audio to OpenAI Whisper API
          // 2. Returning transcript text via WebSocket
          // 3. Displaying it in the chat
          
          // Uncomment below to re-enable demo transcription:
          /*
          if (this.onTranscript && Math.random() > 0.7) {
            const phrases = [
              "I need help with my order",
              "Can you check my account?",
              "Thank you for your help",
              "What are your hours?",
              "I have a question about billing"
            ];
            const randomPhrase = phrases[Math.floor(Math.random() * phrases.length)];
            setTimeout(() => this.onTranscript?.(randomPhrase), 500);
          }
          */
        }
      };
      
      this.mediaRecorder.start(3000); // Capture in 3-second chunks (complete WebM files)
      console.log('🎙️ Recording started');
      return true;
      
    } catch (error) {
      console.error('Error starting recorder:', error);
      return false;
    }
  }
  
  stop() {
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
      console.log('🎙️ Recording stopped');
    }
    
    stopMediaStream(this.stream);
    this.stream = null;
    this.mediaRecorder = null;
  }
  
  isRecording(): boolean {
    return this.mediaRecorder?.state === 'recording';
  }
  
  getStream(): MediaStream | null {
    return this.stream;
  }
}

/**
 * Play audio received from WebSocket
 */
export function playAudioChunk(audioData: Blob) {
  try {
    const audio = new Audio();
    audio.src = URL.createObjectURL(audioData);
    audio.play();
  } catch (error) {
    console.error('Error playing audio:', error);
  }
}

/**
 * Audio visualization using Web Audio API
 */
export class AudioVisualizer {
  private audioContext: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private dataArray: Uint8Array | null = null;
  private animationId: number | null = null;
  
  constructor(private canvas: HTMLCanvasElement) {}
  
  start(stream: MediaStream) {
    this.audioContext = new AudioContext();
    this.analyser = this.audioContext.createAnalyser();
    this.analyser.fftSize = 256;
    
    const microphone = this.audioContext.createMediaStreamSource(stream);
    microphone.connect(this.analyser);
    
    const bufferLength = this.analyser.frequencyBinCount;
    this.dataArray = new Uint8Array(bufferLength);
    
    this.draw();
  }
  
  private draw() {
    if (!this.analyser || !this.dataArray) return;
    
    this.animationId = requestAnimationFrame(() => this.draw());
    
    this.analyser.getByteFrequencyData(this.dataArray);
    
    const ctx = this.canvas.getContext('2d');
    if (!ctx) return;
    
    const width = this.canvas.width;
    const height = this.canvas.height;
    
    ctx.fillStyle = 'rgb(15, 23, 42)'; // slate-900
    ctx.fillRect(0, 0, width, height);
    
    const barWidth = (width / this.dataArray.length) * 2.5;
    let x = 0;
    
    for (let i = 0; i < this.dataArray.length; i++) {
      const barHeight = (this.dataArray[i] / 255) * height;
      
      const gradient = ctx.createLinearGradient(0, height - barHeight, 0, height);
      gradient.addColorStop(0, 'rgb(59, 130, 246)'); // blue-500
      gradient.addColorStop(1, 'rgb(37, 99, 235)'); // blue-600
      
      ctx.fillStyle = gradient;
      ctx.fillRect(x, height - barHeight, barWidth, barHeight);
      
      x += barWidth + 1;
    }
  }
  
  stop() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
    }
    
    if (this.audioContext) {
      this.audioContext.close();
    }
    
    this.audioContext = null;
    this.analyser = null;
    this.dataArray = null;
  }
}

