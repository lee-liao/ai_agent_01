'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

type Role = 'initiator' | 'responder';

interface UseWebRTCAudioOptions {
  role: Role;
  ws: WebSocket | null;
}

interface SignalMessage {
  type: 'rtc_offer' | 'rtc_answer' | 'ice_candidate';
  sdp?: any;
  candidate?: any;
}

const ICE_SERVERS: RTCIceServer[] = [
  { urls: 'stun:stun.l.google.com:19302' },
];

export function useWebRTCAudio({ role, ws }: UseWebRTCAudioOptions) {
  const [isAudioEnabled, setIsAudioEnabled] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const analyserIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const attachRemoteAudio = useCallback((stream: MediaStream) => {
    if (!remoteAudioRef.current) {
      const audio = document.createElement('audio');
      audio.autoplay = true;
      audio.playsInline = true;
      audio.muted = false;
      audio.style.display = 'none';
      document.body.appendChild(audio);
      remoteAudioRef.current = audio;
    }
    remoteAudioRef.current.srcObject = stream;
    // Best effort play
    remoteAudioRef.current
      .play()
      .catch(() => {});
  }, []);

  const startAnalyser = useCallback((stream: MediaStream) => {
    try {
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      source.connect(analyser);
      analyserIntervalRef.current = setInterval(() => {
        analyser.getByteFrequencyData(dataArray);
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length;
        setAudioLevel(avg / 255);
      }, 100);
    } catch {
      // ignore
    }
  }, []);

  const stopAnalyser = useCallback(() => {
    if (analyserIntervalRef.current) {
      clearInterval(analyserIntervalRef.current);
      analyserIntervalRef.current = null;
    }
  }, []);

  const sendSignal = useCallback(
    (msg: SignalMessage) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(msg));
      }
    },
    [ws]
  );

  const createPeer = useCallback(() => {
    const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
    pc.onicecandidate = (e) => {
      if (e.candidate) {
        sendSignal({ type: 'ice_candidate', candidate: e.candidate });
      }
    };
    pc.ontrack = (e) => {
      const [stream] = e.streams;
      if (stream) {
        remoteStreamRef.current = stream;
        attachRemoteAudio(stream);
      }
    };
    pcRef.current = pc;
    return pc;
  }, [attachRemoteAudio, sendSignal]);

  const start = useCallback(async () => {
    if (pcRef.current) return;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    localStreamRef.current = stream;
    startAnalyser(stream);

    const pc = createPeer();
    stream.getTracks().forEach((t) => pc.addTrack(t, stream));

    if (role === 'initiator') {
      const offer = await pc.createOffer({ offerToReceiveAudio: true });
      await pc.setLocalDescription(offer);
      sendSignal({ type: 'rtc_offer', sdp: offer });
    }
    setIsAudioEnabled(true);
  }, [createPeer, role, sendSignal, startAnalyser]);

  const stop = useCallback(() => {
    setIsAudioEnabled(false);
    stopAnalyser();
    if (pcRef.current) {
      pcRef.current.getSenders().forEach((s) => {
        try { s.track && s.track.stop(); } catch {}
      });
      pcRef.current.close();
    }
    pcRef.current = null;
    localStreamRef.current = null;
    remoteStreamRef.current = null;
  }, [stopAnalyser]);

  const toggleMute = useCallback(() => {
    const track = localStreamRef.current?.getAudioTracks()[0];
    if (track) {
      track.enabled = !track.enabled;
      setIsMuted(!track.enabled);
    }
  }, []);

  const handleSignal = useCallback(
    async (msg: SignalMessage) => {
      if (!pcRef.current && (msg.type === 'rtc_offer' || msg.type === 'rtc_answer' || msg.type === 'ice_candidate')) {
        // Create peer lazily if not started yet (for responder)
        if (!localStreamRef.current) {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
          localStreamRef.current = stream;
          startAnalyser(stream);
        }
        const pc = createPeer();
        localStreamRef.current!.getTracks().forEach((t) => pc.addTrack(t, localStreamRef.current!));
      }

      const pc = pcRef.current!;
      if (!pc) return;

      if (msg.type === 'rtc_offer') {
        await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        sendSignal({ type: 'rtc_answer', sdp: answer });
        setIsAudioEnabled(true);
      } else if (msg.type === 'rtc_answer') {
        await pc.setRemoteDescription(new RTCSessionDescription(msg.sdp));
      } else if (msg.type === 'ice_candidate' && msg.candidate) {
        try {
          await pc.addIceCandidate(new RTCIceCandidate(msg.candidate));
        } catch {}
      }
    },
    [createPeer, sendSignal, startAnalyser]
  );

  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    isAudioEnabled,
    isMuted,
    audioLevel,
    start,
    stop,
    toggleMute,
    handleSignal,
  };
}

export default useWebRTCAudio;


