'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Phone, PhoneOff, Mic, MicOff, User, Clock, MessageSquare } from 'lucide-react';

interface Message {
  id: string;
  speaker: 'customer' | 'agent';
  text: string;
  timestamp: Date;
}

export default function CallsPage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [inCall, setInCall] = useState(false);
  const [muted, setMuted] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [callDuration, setCallDuration] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const callTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Check authentication
  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      router.push('/auth/signin');
      return;
    }
    setUser(JSON.parse(userData));
  }, [router]);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Call timer
  useEffect(() => {
    if (inCall) {
      callTimerRef.current = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
    } else {
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current);
      }
      setCallDuration(0);
    }

    return () => {
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current);
      }
    };
  }, [inCall]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startCall = () => {
    setInCall(true);
    
    // Connect WebSocket
    const callId = `call_${Date.now()}`;
    const websocket = new WebSocket(`ws://localhost:8000/ws/call/${callId}`);
    
    websocket.onopen = () => {
      console.log('✅ Connected to call');
      websocket.send(JSON.stringify({
        type: 'start_call',
        call_id: callId,
        agent_name: user?.username,
        timestamp: new Date().toISOString()
      }));
      
      addMessage('system', 'Call started. Waiting for customer...');
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'transcript' && data.speaker === 'customer') {
          addMessage('customer', data.text);
        } else if (data.type === 'call_ended') {
          addMessage('system', 'Customer ended the call');
          endCall();
        }
      } catch (e) {
        console.error('Error parsing message:', e);
      }
    };

    websocket.onerror = () => {
      addMessage('system', '⚠️ Connection error. Using demo mode.');
    };

    websocket.onclose = () => {
      console.log('WebSocket closed');
    };

    setWs(websocket);
  };

  const endCall = () => {
    if (ws) {
      ws.send(JSON.stringify({
        type: 'end_call',
        timestamp: new Date().toISOString()
      }));
      ws.close();
    }
    
    setInCall(false);
    setWs(null);
    addMessage('system', 'Call ended');
  };

  const addMessage = (speaker: 'customer' | 'agent' | 'system', text: string) => {
    const message: Message = {
      id: `msg_${Date.now()}_${Math.random()}`,
      speaker: speaker as any,
      text,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const sendMessage = () => {
    if (!inputMessage.trim()) return;

    // Add to UI
    addMessage('agent', inputMessage);

    // Send via WebSocket
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'transcript',
        speaker: 'agent',
        text: inputMessage,
        timestamp: new Date().toISOString()
      }));
    }

    setInputMessage('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Phone className="w-6 h-6 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Call Center</h1>
                <p className="text-sm text-gray-600">Agent: {user.fullName}</p>
              </div>
            </div>
            <button
              onClick={() => {
                localStorage.removeItem('user');
                router.push('/');
              }}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Sign Out
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Chat Area */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden flex flex-col h-[600px]">
              {/* Call Status Bar */}
              <div className={`px-6 py-4 ${inCall ? 'bg-green-50 border-b border-green-200' : 'bg-gray-50 border-b border-gray-200'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {inCall ? (
                      <>
                        <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                        <span className="text-green-700 font-medium">In Call</span>
                        <Clock className="w-4 h-4 text-green-600 ml-2" />
                        <span className="text-green-700 font-mono">{formatDuration(callDuration)}</span>
                      </>
                    ) : (
                      <>
                        <div className="w-3 h-3 bg-gray-400 rounded-full" />
                        <span className="text-gray-600">Idle - Ready to take calls</span>
                      </>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {inCall && (
                      <button
                        onClick={() => setMuted(!muted)}
                        className={`p-2 rounded-lg transition ${muted ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                      >
                        {muted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                      </button>
                    )}
                    
                    {!inCall ? (
                      <button
                        onClick={startCall}
                        className="flex items-center gap-2 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition"
                      >
                        <Phone className="w-5 h-5" />
                        Start Call
                      </button>
                    ) : (
                      <button
                        onClick={endCall}
                        className="flex items-center gap-2 bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition"
                      >
                        <PhoneOff className="w-5 h-5" />
                        End Call
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="text-center text-gray-400 mt-20">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No messages yet. Start a call to begin conversation.</p>
                  </div>
                ) : (
                  messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.speaker === 'agent' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] rounded-lg px-4 py-3 ${
                          message.speaker === 'customer'
                            ? 'bg-blue-100 text-blue-900'
                            : message.speaker === 'agent'
                            ? 'bg-green-100 text-green-900'
                            : 'bg-gray-100 text-gray-600 text-sm italic'
                        }`}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold uppercase">
                            {message.speaker}
                          </span>
                          <span className="text-xs opacity-60">
                            {message.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                        <p>{message.text}</p>
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Area */}
              <div className="border-t border-gray-200 p-4">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={inCall ? "Type your response..." : "Start a call to send messages"}
                    disabled={!inCall}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!inCall || !inputMessage.trim()}
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Customer Info */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <User className="w-5 h-5" />
                Customer Info
              </h3>
              {inCall ? (
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-600">Name:</span>
                    <p className="font-medium">John Doe</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Account:</span>
                    <p className="font-medium">#ACC00001</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Tier:</span>
                    <p className="font-medium">🥇 Gold</p>
                  </div>
                  <div>
                    <span className="text-gray-600">LTV:</span>
                    <p className="font-medium">$2,340</p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-400 text-sm">Start a call to see customer information</p>
              )}
            </div>

            {/* AI Suggestions */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                🤖 AI Suggestions
              </h3>
              {inCall ? (
                <div className="space-y-3">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <p className="text-sm text-blue-900">
                      💡 Customer seems satisfied with the service
                    </p>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <p className="text-sm text-green-900">
                      ✅ Consider offering premium upgrade
                    </p>
                  </div>
                </div>
              ) : (
                <p className="text-gray-400 text-sm">AI suggestions will appear during calls</p>
              )}
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Quick Actions
              </h3>
              <div className="space-y-2">
                <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm transition">
                  Transfer Call
                </button>
                <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm transition">
                  Create Ticket
                </button>
                <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm transition">
                  Schedule Callback
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

