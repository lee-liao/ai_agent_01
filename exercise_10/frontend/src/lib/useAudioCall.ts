import { useState, useEffect, useRef, useCallback } from 'react';
import { AudioRecorder, stopMediaStream } from './audioUtils';

interface UseAudioCallOptions {
  onTranscript?: (text: string, speaker: 'agent' | 'customer') => void;
  onAudioLevel?: (level: number) => void;
  autoSendAudio?: boolean;
}

export function useAudioCall(ws: WebSocket | null, options: UseAudioCallOptions = {}) {
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [audioDevices, setAudioDevices] = useState<{ deviceId: string; label: string }[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [audioLevel, setAudioLevel] = useState(0);
  
  const recorderRef = useRef<AudioRecorder | null>(null);
  const audioLevelIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Load available audio devices
  useEffect(() => {
    loadAudioDevices();
  }, []);
  
  const loadAudioDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices
        .filter(device => device.kind === 'audioinput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || `Microphone ${device.deviceId.substring(0, 5)}`
        }));
      
      setAudioDevices(audioInputs);
      if (audioInputs.length > 0 && !selectedDevice) {
        setSelectedDevice(audioInputs[0].deviceId);
      }
    } catch (error) {
      console.error('Error loading audio devices:', error);
    }
  };
  
  const startAudio = useCallback(async () => {
    if (recorderRef.current) {
      return; // Already started
    }
    
    const recorder = new AudioRecorder(
      // onAudioChunk
      (chunk) => {
        if (ws && ws.readyState === WebSocket.OPEN && !isMuted) {
          // Send audio chunk to backend
          ws.send(chunk);
          console.log('📤 Sent audio chunk:', chunk.size, 'bytes');
        }
      },
      // onTranscript (simulated)
      (text) => {
        if (options.onTranscript) {
          options.onTranscript(text, 'customer');
        }
      }
    );
    
    const started = await recorder.start(selectedDevice);
    
    if (started) {
      recorderRef.current = recorder;
      setIsAudioEnabled(true);
      
      // Start monitoring audio level
      audioLevelIntervalRef.current = setInterval(() => {
        const stream = recorder.getStream();
        if (stream) {
          const level = getStreamAudioLevel(stream);
          setAudioLevel(level);
          if (options.onAudioLevel) {
            options.onAudioLevel(level);
          }
        }
      }, 100);
      
      console.log('🎙️ Audio started');
    }
  }, [ws, selectedDevice, isMuted, options]);
  
  const stopAudio = useCallback(() => {
    if (recorderRef.current) {
      recorderRef.current.stop();
      recorderRef.current = null;
      setIsAudioEnabled(false);
      setAudioLevel(0);
      
      if (audioLevelIntervalRef.current) {
        clearInterval(audioLevelIntervalRef.current);
        audioLevelIntervalRef.current = null;
      }
      
      console.log('🛑 Audio stopped');
    }
  }, []);
  
  const toggleMute = useCallback(() => {
    setIsMuted(prev => !prev);
  }, []);
  
  const changeDevice = useCallback((deviceId: string) => {
    setSelectedDevice(deviceId);
    
    // If audio is currently enabled, restart with new device
    if (isAudioEnabled) {
      stopAudio();
      setTimeout(() => startAudio(), 100);
    }
  }, [isAudioEnabled, stopAudio, startAudio]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAudio();
    };
  }, [stopAudio]);
  
  return {
    isAudioEnabled,
    isMuted,
    audioLevel,
    audioDevices,
    selectedDevice,
    startAudio,
    stopAudio,
    toggleMute,
    changeDevice
  };
}

// Helper function to get audio level from stream
function getStreamAudioLevel(stream: MediaStream): number {
  try {
    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const microphone = audioContext.createMediaStreamSource(stream);
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    
    microphone.connect(analyser);
    analyser.getByteFrequencyData(dataArray);
    
    // Calculate average level
    const average = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
    
    // Close context to avoid memory leak
    audioContext.close();
    
    return average / 255; // Normalize to 0-1
  } catch (error) {
    return 0;
  }
}

