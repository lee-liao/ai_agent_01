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
  const [selectedCustomer, setSelectedCustomer] = useState<{ name?: string; account?: string; tier?: string; status?: string; lifetime_value?: number; orders?: any[]; tickets?: any[] } | null>(null);
  const [aiSuggestions, setAiSuggestions] = useState<Array<{ text: string; timestamp: Date }>>([]);
  const [nextTopSuggestionColor, setNextTopSuggestionColor] = useState<'yellow' | 'blue'>('yellow'); // Track color for next top suggestion
  const [isTranscribing, setIsTranscribing] = useState(false); // Track when audio is being transcribed
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const callTimerRef = useRef<NodeJS.Timeout | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const aiSuggestionsRef = useRef<HTMLDivElement>(null);
  
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

  // Auto-scroll to latest message - scroll to bottom when new messages arrive
  useEffect(() => {
    // Use requestAnimationFrame to ensure DOM is updated before scrolling
    const scrollToBottom = () => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      }
    };
    
    // Try immediate scroll first
    scrollToBottom();
    
    // Also try after a small delay to ensure DOM is fully updated
    const timer = setTimeout(scrollToBottom, 50);
    
    // Cleanup timer
    return () => clearTimeout(timer);
  }, [messages]);

  // Auto-scroll AI suggestions panel only if user is near bottom
  useEffect(() => {
    const suggestionsContainer = aiSuggestionsRef.current;
    if (!suggestionsContainer) return;
    
    // Only auto-scroll if user is within 20px of the bottom
    const isNearBottom = suggestionsContainer.scrollHeight - suggestionsContainer.scrollTop <= suggestionsContainer.clientHeight + 20;
    
    if (isNearBottom) {
      // Scroll to top since new suggestions are added at the beginning
      setTimeout(() => {
        suggestionsContainer.scrollTop = 0;
      }, 0);
    }
  }, [aiSuggestions]);

  // Auto-connect (monitor mode) to subscribe to queue on page load
  useEffect(() => {
    if (user && ws === null) {
      connectAgent();
    }
  }, [user, ws]);

  // WS heartbeat: send ping every 25s when connected
  useEffect(() => {
    if (!ws) return;
    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 25000);
    return () => clearInterval(interval);
  }, [ws]);

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

  // Initialize agent connection (monitoring mode only)
  const connectAgent = async () => {
    if (ws) return; // Already connected
    
    try {
      // Step 1: Request connection to backend matching service
      const callApiModule = await import('@/lib/callApi');
      const response = await callApiModule.callAPI.startCall(
        'agent',
        user?.username || 'Agent'
        // No availability parameter needed in simplified model
      );
      
      console.log('📞 Agent call response:', response);
      
      // Step 2: Connect WebSocket with assigned call_id
      // Determine WebSocket backend URL based on environment variable
      // This ensures the WebSocket connects to the same backend server as API calls
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || `http://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:8600`;
      
      // Extract hostname and port from API URL to build WebSocket URL
      let wsUrl;
      if (apiBaseUrl.startsWith('http://')) {
        wsUrl = apiBaseUrl.replace('http://', 'ws://');
      } else if (apiBaseUrl.startsWith('https://')) {
        wsUrl = apiBaseUrl.replace('https://', 'wss://');
      } else {
        // Fallback for malformed URL - check if it's already a WebSocket URL
        if (apiBaseUrl.startsWith('ws://') || apiBaseUrl.startsWith('wss://')) {
          wsUrl = apiBaseUrl;
        } else {
          // Default to secure WebSocket if HTTPS is likely being used
          wsUrl = `wss://${apiBaseUrl}`;
        }
      }
      
      const websocket = new WebSocket(`${wsUrl}/ws/call/${response.call_id}`);
      
      websocket.onopen = () => {
        console.log('✅ Agent WebSocket connected with call_id:', response.call_id);
        
        websocket.send(JSON.stringify({
          type: 'start_call',
          call_id: response.call_id,
          agent_name: user?.username,
          timestamp: new Date().toISOString()
        }));
        
        // Subscribe to queue updates (monitoring mode)
        websocket.send(JSON.stringify({ type: 'subscribe_queue' }));
        console.log('Agent subscribed to queue updates');
        
        addMessage('system', 'Agent connected. Use "Take Top" or "Pick Up" to manually select customers.');
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'transcript' && data.speaker === 'customer') {
            setIsTranscribing(true);
            setTimeout(() => setIsTranscribing(false), 2000); // Show active state for 2 seconds
            addMessage('customer', data.text);
          } else if (data.type === 'transcript' && data.speaker === 'agent') {
            setIsTranscribing(true);
            setTimeout(() => setIsTranscribing(false), 2000); // Show active state for 2 seconds
            addMessage('agent', data.text);
          } else if (data.type === 'ai_suggestion') {
            // Route AI suggestions to dedicated panel list (limit to 10)
            // Flip the color for the next top suggestion
            setNextTopSuggestionColor(prev => prev === 'yellow' ? 'blue' : 'yellow');
            setAiSuggestions(prev => [
              { text: `${data.suggestion}`, timestamp: new Date() },
              ...prev,
            ].slice(0, 10));
          } else if (data.type === 'conversation_ended') {
            addMessage('system', 'Conversation ended');
            setInCall(false);
            // Ensure queue panel remains visible after call ends
            setShowQueuePanel(true);
          } else if (data.type === 'conversation_started') {
            addMessage('system', 'Conversation started');
            setInCall(true);
            // Update customer info if provided in conversation_started message
            if (data.customer_name || data.account_number) {
              setSelectedCustomer(prev => ({
                ...prev,
                name: data.customer_name || prev?.name,
                account: data.account_number || prev?.account,
              }));
            }
          } else if (data.type === 'queue_update') {
            setQueueItems(Array.isArray(data.items) ? data.items : []);
            // Update queue panel visibility based on items
            setShowQueuePanel(Array.isArray(data.items) && data.items.length > 0);
          } else if (data.type === 'customer_context') {
            // Handle customer context data
            if (data.customer) {
              setSelectedCustomer({
                name: data.customer.name,
                account: data.customer.account_number,
                tier: data.customer.tier,
                status: data.customer.status,
                lifetime_value: data.customer.lifetime_value,
                orders: data.orders || [],
              });
            }
          } else if (data.type === 'pickup_result') {
            addMessage('system', `Pickup result: ${data.status || data.message}`);
          } else if (data.type === 'availability_ignored') {
            // In the simplified model, agents don't use availability states
            // They remain in monitoring mode and manually pick customers
          } else {
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('system', '⚠️ Connection error. Please check if backend is running.');
      };

      websocket.onclose = () => {
        console.log('DEBUG: WebSocket closed, clearing ws reference');
        setWs(null);
      };

      setWs(websocket);
      
    } catch (error: any) {
      console.error('Failed to connect agent:', error);
      addMessage('system', `⚠️ Failed to connect: ${error.message || 'Please check if the server is running on port 8600.'}`);
    }
  };

  const endCall = () => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'end_call',
        user_type: 'agent',
        timestamp: new Date().toISOString()
      }));
    }
    
    // Set inCall to false immediately for better UX feedback
    // But keep in mind that server confirmation via 'conversation_ended' is the authoritative state
    setInCall(false);
    
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

    // Send via WebSocket (the WebSocket response will add the message to UI)
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
                if (inCall) {
                  endCall();
                }
                localStorage.removeItem('user');
                router.push('/auth/signin');
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
                      // No button needed in idle state - agent is always ready to pick customers
                      <div className="text-gray-600">
                        <Phone className="w-5 h-5 inline mr-2" />
                        Monitoring Queue
                      </div>
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
                          {isMuted ? 'Microphone muted' : isTranscribing ? 'Processing voice input...' : 'Listening... Speak to the customer'}
                        </div>
                      )}
                </div>
              )}

              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4" ref={chatContainerRef}>
                {messages.length === 0 ? (
                  <div className="text-center text-gray-400 mt-20">
                    <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>No messages yet. Start a conversation to begin conversation.</p>
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
                  placeholder={inCall ? "Type your response..." : "Start a conversation to send messages"}
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

            {/* AI Suggestions (Under Chat) */}
            {aiSuggestions.length > 0 && (
              <div className="border-t border-gray-200 p-4 bg-gray-50">
                <h4 className="text-sm font-semibold text-gray-800 mb-2">AI Suggestions</h4>
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1" ref={aiSuggestionsRef}>
                  {aiSuggestions.map((s, idx) => {
                    // Determine color based on position and the color of the top suggestion
                    // If this is the top suggestion (idx === 0), use the tracked color
                    // Otherwise, alternate based on distance from top
                    const isTopSuggestion = idx === 0;
                    let bgColor = '';
                    let borderColor = '';
                    
                    if (isTopSuggestion) {
                      bgColor = nextTopSuggestionColor === 'yellow' ? 'bg-yellow-100' : 'bg-blue-50';
                      borderColor = nextTopSuggestionColor === 'yellow' ? 'border-yellow-300' : 'border-blue-200';
                    } else {
                      // For non-top items, alternate based on distance from top
                      const distanceFromTop = idx;
                      const colorForThisItem = (nextTopSuggestionColor === 'yellow') ? 
                        (distanceFromTop % 2 === 1 ? 'blue' : 'yellow') :  // If top is yellow: blue, yellow, blue...
                        (distanceFromTop % 2 === 1 ? 'yellow' : 'blue');   // If top is blue: yellow, blue, yellow...
                      
                      bgColor = colorForThisItem === 'yellow' ? 'bg-yellow-100' : 'bg-blue-50';
                      borderColor = colorForThisItem === 'yellow' ? 'border-yellow-300' : 'border-blue-200';
                    }
                    
                    return (
                      <button
                        key={s.timestamp.getTime()}
                        type="button"
                        onClick={() => setInputMessage(s.text)}
                        className={`w-full text-left rounded-lg p-2 border transition hover:opacity-90 ${bgColor} ${borderColor}`}
                        title="Click to copy into chat input"
                      >
                        <p className="text-sm text-gray-900">{s.text}</p>
                        <div className="text-[10px] text-gray-600 mt-1">{s.timestamp.toLocaleTimeString()}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <User className="w-5 h-5" />
                  Waiting Customers
                </h3>
                <button
                  onClick={() => {
                    if (ws && ws.readyState === WebSocket.OPEN && !inCall) {
                      ws.send(JSON.stringify({ type: 'pickup' }));
                    }
                  }}
                  disabled={!ws || ws.readyState !== WebSocket.OPEN || queueItems.length === 0 || inCall}
                  className="text-sm bg-blue-600 text-white px-3 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  Take Top
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
                          if (ws && ws.readyState === WebSocket.OPEN && !inCall) {
                            ws.send(JSON.stringify({ 
                              type: 'pickup', 
                              account_number: item.account_number 
                            }));
                          }
                        }}
                        disabled={!ws || ws.readyState !== WebSocket.OPEN || inCall}
                        className="text-sm bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 disabled:opacity-50"
                      >
                        Pick Up
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
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
                  {selectedCustomer?.lifetime_value !== undefined && (
                    <div>
                      <span className="text-gray-600">Lifetime Value:</span>
                      <p className="font-medium">${selectedCustomer.lifetime_value.toFixed(2)}</p>
                    </div>
                  )}
                  {selectedCustomer?.orders && selectedCustomer.orders.length > 0 ? (
                    <div className="mt-3">
                      <span className="text-gray-600">Recent Orders</span>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {selectedCustomer.orders.map((o: any) => (
                          <li key={o.order_number} className="flex justify-between">
                            <span>{o.product_name}</span>
                            <span className="text-gray-500">{o.order_number}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 mt-2">No recent orders</p>
                  )}
                  {selectedCustomer?.tickets && selectedCustomer.tickets.length > 0 ? (
                    <div className="mt-3">
                      <span className="text-gray-600">Recent Tickets</span>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {selectedCustomer.tickets.map((t: any) => (
                          <li key={t.ticket_number} className="flex justify-between">
                            <span>{t.subject}</span>
                            <span className="text-gray-500">{t.ticket_number}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 mt-2">No recent tickets</p>
                  )}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">Start a conversation to see customer information</p>
              )}
            </div>

            {/* AI Suggestions moved under chat */}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Quick Actions
              </h3>
              <div className="space-y-2">
                <button className="w-full bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm transition">
                  Transfer conversation
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
