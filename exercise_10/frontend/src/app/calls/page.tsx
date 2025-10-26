'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Phone, PhoneOff, Mic, MicOff, User, Clock, MessageSquare, Volume2 } from 'lucide-react';
import { useAudioCall } from '@/lib/useAudioCall';

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
  // Removed manual target account input; rely on WS queue
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [queueItems, setQueueItems] = useState<Array<{ customer_name?: string; account_number?: string; waiting_since?: string }>>([]);
  const [callDuration, setCallDuration] = useState(0);
  const [showQueuePanel, setShowQueuePanel] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState<{ name?: string; account?: string; tier?: string; status?: string } | null>(null);
  const [aiSuggestions, setAiSuggestions] = useState<Array<{ text: string; timestamp: Date }>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const callTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Audio call hook
  const {
    isAudioEnabled,
    isMuted,
    audioLevel,
    audioDevices,
    selectedDevice,
    startAudio,
    stopAudio,
    toggleMute,
    changeDevice
  } = useAudioCall(ws, {
    onTranscript: (text, speaker) => {
      addMessage(speaker === 'agent' ? 'agent' : 'customer', `[Voice] ${text}`);
    }
  });

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

  // Auto-connect (monitor mode) to subscribe to queue on page load
  useEffect(() => {
    if (user && !ws) {
      startCall();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

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

  const startCall = async () => {
    // Do not set inCall until matched or call_started; keeps queue visible
    
    try {
      // Step 1: Request connection to backend matching service
      const callApiModule = await import('@/lib/callApi');
      const response = await callApiModule.callAPI.startCall(
        'agent',
        user?.username || 'Agent',
        { available: false }
      );
      
      console.log('📞 Agent call response:', response);
      
      // Step 2: Connect WebSocket with assigned call_id
      const websocket = new WebSocket(`ws://localhost:8000/ws/call/${response.call_id}`);
      
      websocket.onopen = () => {
        console.log('✅ Agent WebSocket connected with call_id:', response.call_id);
        
        websocket.send(JSON.stringify({
          type: 'start_call',
          call_id: response.call_id,
          agent_name: user?.username,
          timestamp: new Date().toISOString()
        }));
        
        // Show appropriate message based on match status
        if (response.matched && response.partner_name) {
          addMessage('system', `Connected to customer: ${response.partner_name}`);
          setInCall(true);
        } else {
          addMessage('system', `${response.message} Waiting for incoming calls... (subscribed)`);
          websocket.send(JSON.stringify({ type: 'subscribe_queue' }));
          console.log('Agent subscribed to queue updates');
        }
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'transcript' && data.speaker === 'customer') {
            addMessage('customer', data.text);
          } else if (data.type === 'ai_suggestion') {
            // Route AI suggestions to dedicated panel list (limit to 10)
            setAiSuggestions(prev => [
              { text: `${data.suggestion}`, timestamp: new Date() },
              ...prev,
            ].slice(0, 10));
          } else if (data.type === 'conversation_ended') {
            addMessage('system', 'Conversation ended');
            endCall();
          } else if (data.type === 'conversation_started') {
            addMessage('system', 'Conversation started');
            setInCall(true);
          } else if (data.type === 'queue_update') {
            console.log('Agent received queue_update:', data.items);
            setQueueItems(Array.isArray(data.items) ? data.items : []);
          } else if (data.type === 'pickup_result') {
            if (data.status === 'success') {
              addMessage('system', `Picked up ${data.customer_name || ''}`);
              setMessages([]);
              setInCall(true);
              setSelectedCustomer({ name: data.customer_name, account: data.account_number });
              if (data.account_number) {
                import('@/lib/callApi').then(async (mod) => {
                  try {
                    const info = await mod.customerAPI.publicSearch(data.account_number);
                    if (info) {
                      setSelectedCustomer({
                        name: info.name ?? data.customer_name,
                        account: info.account_number ?? data.account_number,
                        tier: info.tier,
                        status: info.status,
                      });
                    }
                  } catch (e) {
                    console.warn('Agent: customer context lookup failed:', e);
                  }
                });
              }
            } else {
              addMessage('system', `Pickup failed: ${data.status}`);
            }
          }
        } catch (e) {
          console.error('Error parsing message:', e);
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('system', '⚠️ Connection error. Please check if backend is running.');
      };

      websocket.onclose = () => {
        console.log('WebSocket closed');
      };

      setWs(websocket);
      
    } catch (error: any) {
      console.error('Failed to start chat:', error);
      addMessage('system', `⚠️ Failed to connect: ${error.message || 'Please check if the server is running on port 8000.'}`);
      setInCall(false);
    }
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
    // Keep queue panel visible (collapsed with count)
    setShowQueuePanel(true);
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
                        Start Chat
                      </button>
                    ) : (
                      <button
                        onClick={endCall}
                        className="flex items-center gap-2 bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition"
                      >
                        <PhoneOff className="w-5 h-5" />
                        End Chat
                      </button>
                    )}
                  </div>
                </div>
              </div>
              {/* Removed manual target account input */}

              {/* Audio Controls - Only show when in call */}
              {inCall && (
                <div className="px-6 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Audio toggle button */}
                      {!isAudioEnabled ? (
                        <button
                          onClick={startAudio}
                          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                        >
                          <Mic className="w-4 h-4" />
                          Enable Voice
                        </button>
                      ) : (
                        <button
                          onClick={stopAudio}
                          className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
                        >
                          <PhoneOff className="w-4 h-4" />
                          Disable Voice
                        </button>
                      )}
                      
                      {/* Mute toggle (using audio hook's mute) */}
                      {isAudioEnabled && (
                        <button
                          onClick={toggleMute}
                          className={`p-2 rounded-lg transition ${
                            isMuted 
                              ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                          title={isMuted ? 'Unmute' : 'Mute'}
                        >
                          {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                        </button>
                      )}
                      
                      {/* Audio level indicator */}
                      {isAudioEnabled && (
                        <div className="flex items-center gap-2">
                          <Volume2 className="w-4 h-4 text-gray-500" />
                          <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-blue-500 transition-all duration-100"
                              style={{ width: `${Math.min(audioLevel * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Device selector */}
                    {isAudioEnabled && audioDevices.length > 1 && (
                      <select
                        value={selectedDevice}
                        onChange={(e) => changeDevice(e.target.value)}
                        className="text-sm border border-gray-300 rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        {audioDevices.map((device) => (
                          <option key={device.deviceId} value={device.deviceId}>
                            {device.label}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>
                  
                  {/* Status message */}
                  {isAudioEnabled && (
                    <div className="mt-2 text-xs text-blue-600 flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                      {isMuted ? 'Microphone muted' : 'Listening... Speak to the customer'}
                    </div>
                  )}
                </div>
              )}

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
            {!inCall ? (
              <div className="bg-white rounded-lg shadow-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <User className="w-5 h-5" />
                    Waiting Customers
                  </h3>
                  <button
                    onClick={() => {
                      if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({ type: 'pickup' }));
                      }
                    }}
                    disabled={!ws || ws.readyState !== WebSocket.OPEN || queueItems.length === 0}
                    className="text-sm bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    Start Chat (Top)
                  </button>
                </div>
                {queueItems.length === 0 ? (
                  <p className="text-gray-400 text-sm">No customers waiting</p>
                ) : (
                  <div className="space-y-3">
                    {queueItems.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between border border-gray-200 rounded-lg p-3">
                        <div>
                          <p className="text-sm font-medium text-gray-900">{item.customer_name || 'Customer'}</p>
                          <p className="text-xs text-gray-600">{item.account_number || '—'} · since {item.waiting_since?.split('T')[0]}</p>
                        </div>
                        <button
                          onClick={() => {
                            if (ws && ws.readyState === WebSocket.OPEN && item.account_number) {
                              ws.send(JSON.stringify({ type: 'pickup', account_number: item.account_number }));
                            }
                          }}
                          className="bg-blue-600 text-white px-3 py-2 rounded-lg text-sm hover:bg-blue-700"
                        >
                          Pick Up
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">Waiting Customers</div>
                  <div className="text-xs text-gray-500">{queueItems.length} waiting</div>
                </div>
              </div>
            )}
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
                    <p className="font-medium">{selectedCustomer?.name || '—'}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Account:</span>
                    <p className="font-medium">{selectedCustomer?.account || '—'}</p>
                  </div>
                  {selectedCustomer?.tier && (<div><span className="text-gray-600">Tier:</span><p className="font-medium">{selectedCustomer.tier}</p></div>)}
                  {selectedCustomer?.status && (<div><span className="text-gray-600">Status:</span><p className="font-medium">{selectedCustomer.status}</p></div>)}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">Start a call to see customer information</p>
              )}
            </div>

            {/* AI Suggestions */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">AI Suggestions</h3>
              {inCall ? (
                aiSuggestions.length > 0 ? (
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                    {aiSuggestions.map((s, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => setInputMessage(s.text)}
                        className={`w-full text-left rounded-lg p-3 border transition hover:opacity-90 ${idx % 2 === 0 ? 'bg-yellow-100 border-yellow-300' : 'bg-blue-50 border-blue-200'}`}
                        title="Click to copy into chat input"
                      >
                        <p className="text-sm text-gray-900">{s.text}</p>
                        <div className="text-[10px] text-gray-600 mt-1">{s.timestamp.toLocaleTimeString()}</div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400 text-sm">Suggestions will appear during calls</p>
                )
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
