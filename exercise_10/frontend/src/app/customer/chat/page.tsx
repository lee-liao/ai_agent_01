'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Phone, PhoneOff, MessageSquare, User, Send, Mic, MicOff, Volume2 } from 'lucide-react';
import { useAudioCall } from '@/lib/useAudioCall';
import { playAudioChunk } from '@/lib/audioUtils';
import useWebRTCAudio from '@/lib/useWebRTCAudio';

interface Message {
  id: string;
  speaker: 'customer' | 'agent' | 'system';
  text: string;
  timestamp: Date;
}

export default function CustomerChatPage() {
  const router = useRouter();
  const [customer, setCustomer] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [waitingForAgent, setWaitingForAgent] = useState(false);
  const [serverContext, setServerContext] = useState<any>(null);
  const [isTranscribing, setIsTranscribing] = useState(false); // Track when audio is being transcribed
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
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
      addMessage(speaker, `[Voice] ${text}`);
    }
  });

  // WebRTC audio (customer initiates)
  const rtc = useWebRTCAudio({ role: 'initiator', ws });

  // Check if customer is logged in
  useEffect(() => {
    const customerData = localStorage.getItem('customer');
    if (!customerData) {
      router.push('/customer');
      return;
    }
    const parsed = JSON.parse(customerData);
    setCustomer(parsed);
    
    // Fetch server-side context (public)
    import('@/lib/callApi').then(async (mod) => {
      try {
        const q = parsed.name || parsed.email || parsed.phone || parsed.accountNumber || '';
        if (q) {
          const info = await mod.customerAPI.publicSearch(q);
          if (info) {
            setCustomer((prev: any) => ({
              ...prev,
              name: info.name ?? prev?.name,
              email: info.email ?? prev?.email,
              phone: info.phone ?? prev?.phone,
              accountNumber: info.account_number ?? prev?.accountNumber,
              tier: info.tier ?? prev?.tier,
              status: info.status ?? prev?.status,
            }));
            setServerContext(info);
            console.log('Loaded server context:', info);
          }
        }
      } catch (e) {
        // Non-blocking if server has no match
        console.warn('Customer context lookup failed:', e);
      }
    });
  }, [router]);

  // Auto-scroll: only scroll if user is near bottom to avoid jumping when typing
  useEffect(() => {
    if (chatContainerRef.current) {
      const container = chatContainerRef.current;
      const threshold = 120; // px from bottom considered "near bottom"
      const nearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < threshold;
      if (nearBottom) {
        // Scroll to bottom of container
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [messages]);
  
  // Function to force scroll to bottom (used when customer sends a message)
  const scrollToBottom = () => {
    // Use requestAnimationFrame to ensure DOM has updated before scrolling
    requestAnimationFrame(() => {
      if (chatContainerRef.current) {
        // Scroll to bottom of container
        chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
      }
    });
  };

  const connectToAgent = async () => {
    setWaitingForAgent(true);

    try {
      // Step 1: Request connection to backend matching service
      const callApiModule = await import('@/lib/callApi');
      const response = await callApiModule.callAPI.startCall(
        'customer',
        customer?.name || 'Customer',
        { accountNumber: customer?.accountNumber }
      );

      console.log('📞 Call response:', response);

      // Step 2: Connect WebSocket with assigned call_id
      // Determine WebSocket backend URL based on environment variable
      // This ensures the WebSocket connects to the same backend server as API calls
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || `https://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:8600`;
      
      // Extract hostname and port from API URL to build WebSocket URL
      let wsUrl;
      if (apiBaseUrl.startsWith('http://')) {
        wsUrl = apiBaseUrl.replace('http://', 'ws://');
      } else if (apiBaseUrl.startsWith('https://')) {
        wsUrl = apiBaseUrl.replace('https://', 'wss://');
      } else {
        // Fallback for malformed URL
        wsUrl = `ws://${apiBaseUrl}`;
      }
      
      const websocket = new WebSocket(`${wsUrl}/ws/call/${response.call_id}`);

      websocket.onopen = () => {
        console.log('✅ WebSocket connected with call_id:', response.call_id);

        // Notify backend that customer is ready
        websocket.send(JSON.stringify({
          type: 'start_call',
          call_id: response.call_id,
          customer_name: customer?.name,
          timestamp: new Date().toISOString()
        }));

        // Show appropriate message based on match status
        if (response.matched && response.partner_name) {
          setConnected(true);
          setWaitingForAgent(false);
          addMessage('system', `Connected to ${response.partner_name}! How can we help you today?`);
        } else {
          setConnected(false);
          setWaitingForAgent(true);
          addMessage('system', `${response.message} You are in the queue.`);
          if (response.status === 'duplicate') {
            addMessage('system', `You already have a pending request. We will notify you when an agent joins.`);
          }
        }
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'transcript' && data.speaker === 'agent') {
            setIsTranscribing(true);
            setTimeout(() => setIsTranscribing(false), 2000); // Show active state for 2 seconds
            addMessage('agent', data.text);
          } else if (data.type === 'transcript' && data.speaker === 'customer') {
            setIsTranscribing(true);
            setTimeout(() => setIsTranscribing(false), 2000); // Show active state for 2 seconds
            addMessage('customer', data.text);
          } else if (data.type === 'conversation_ended') {
            addMessage('system', 'Conversation ended. Thank you for contacting us!');
            setConnected(false);
          } else if (data.type === 'conversation_started') {
            addMessage('system', 'Agent has joined the chat!');
            setConnected(true);
            setWaitingForAgent(false);
          }
          return;
        } catch (e) {
          // Legacy binary audio (not used with WebRTC)
          if (event.data instanceof Blob) {
            playAudioChunk(event.data);
            return;
          }
          if (event.data instanceof ArrayBuffer) {
            playAudioChunk(new Blob([event.data], { type: 'audio/webm;codecs=opus' }));
            return;
          }
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        addMessage('system', '❗ Connection error. Please try again.');
        setConnected(false);
        // Keep waitingForAgent as-is if we already sent a request
      };

      websocket.onclose = () => {
        console.log('WebSocket closed');
        setConnected(false);
        setWs(null);
      };

      setWs(websocket);
    } catch (error: any) {
      console.error('Failed to connect:', error);
      addMessage('system', `⚠️ Failed to connect: ${error.message || 'Please check if the server is running.'}`);
      setWaitingForAgent(false);
    }
  };

  const disconnectFromAgent = () => {
    if (ws) {
      ws.send(JSON.stringify({
        type: 'end_call',
        user_type: 'customer',
        timestamp: new Date().toISOString()
      }));
    }
    
    setConnected(false);
    addMessage('system', 'Disconnected from support');
  };

  const addMessage = (speaker: 'customer' | 'agent' | 'system', text: string) => {
    const message: Message = {
      id: `msg_${Date.now()}_${Math.random()}`,
      speaker,
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
        speaker: 'customer',
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

  // Quick message templates
  const quickMessages = [
    "I need help with my order",
    "I want to request a refund",
    "I have a billing question",
    "How do I upgrade my plan?"
  ];

  if (!customer) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-primary-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Phone className="w-6 h-6 text-primary-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Customer Support</h1>
                <p className="text-sm text-gray-600">Welcome, {customer.name}</p>
              </div>
            </div>
            <button
              onClick={() => {
                if (connected) {
                  disconnectFromAgent();
                }
                localStorage.removeItem('customer');
                router.push('/customer');
              }}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              Exit
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-xl overflow-hidden flex flex-col h-[600px]">
            {/* Status Bar */}
            <div className={`px-6 py-4 ${connected ? 'bg-green-50 border-b border-green-200' : 'bg-gray-50 border-b border-gray-200'}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {connected ? (
                    <>
                      <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-green-700 font-medium">Connected to Support</span>
                    </>
                  ) : waitingForAgent ? (
                    <>
                      <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse" />
                      <span className="text-yellow-700 font-medium">Request Sent</span>
                    </>
                  ) : (
                    <>
                      <div className="w-3 h-3 bg-gray-400 rounded-full" />
                      <span className="text-gray-600">Not Connected</span>
                    </>
                  )}
                </div>
                
                {!connected ? (
                  <button
                    onClick={!waitingForAgent ? connectToAgent : undefined}
                    disabled={waitingForAgent}
                    title={waitingForAgent ? 'Request Sent – awaiting agent' : 'Start a chat request'}
                    className={`flex items-center gap-2 px-6 py-2 rounded-lg transition ${
                      waitingForAgent
                        ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                        : 'bg-primary-600 text-white hover:bg-primary-700'
                    }`}
                  >
                    <Phone className="w-5 h-5" />
                    {waitingForAgent ? 'Request Sent' : 'Chat for Assistance'}
                  </button>
                ) : (
                  <button
                    onClick={disconnectFromAgent}
                    className="flex items-center gap-2 bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition"
                  >
                    <PhoneOff className="w-5 h-5" />
                    End Chat
                  </button>
                )}
              </div>
            </div>

            {/* Audio Controls - Only show when connected */}
            {connected && (
              <div className="px-6 py-3 bg-gradient-to-r from-primary-50 to-primary-100 border-b border-primary-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {/* Audio toggle button */}
                    {!rtc.isAudioEnabled ? (
                      <button
                        onClick={rtc.start}
                        className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition"
                      >
                        <Mic className="w-4 h-4" />
                        Enable Voice
                      </button>
                    ) : (
                      <button
                        onClick={rtc.stop}
                        className="flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
                      >
                        <PhoneOff className="w-4 h-4" />
                        End Voice Call
                      </button>
                    )}
                    
                    {/* Mute toggle */}
                    {rtc.isAudioEnabled && (
                      <button
                        onClick={rtc.toggleMute}
                        className={`p-2 rounded-lg transition ${
                          rtc.isMuted 
                            ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                        title={rtc.isMuted ? 'Unmute' : 'Mute'}
                      >
                        {rtc.isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                      </button>
                    )}
                    
                    {/* Audio level indicator */}
                    {rtc.isAudioEnabled && (
                      <div className="flex items-center gap-2">
                        <Volume2 className="w-4 h-4 text-gray-500" />
                        <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary-500 transition-all duration-100"
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
                      className="text-sm border border-gray-300 rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500"
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
                      <div className="mt-2 text-xs text-primary-600 flex items-center gap-2">
                        <div className="w-2 h-2 bg-primary-500 rounded-full animate-pulse" />
                        {isMuted ? 'Microphone muted' : isTranscribing ? 'Processing voice input...' : 'Voice call active - speak naturally'}
                      </div>
                    )}
              </div>
            )}

            {/* Messages */}
            <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-400 mt-20">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="mb-6">Click "Chat for Assistance" to start chatting</p>
                  
                  {/* Quick Messages */}
                  <div className="max-w-md mx-auto space-y-2">
                    <p className="text-sm text-gray-500 mb-3">Or select a quick message:</p>
                    {quickMessages.map((msg, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          if (!connected) {
                            setInputMessage(msg);
                          }
                        }}
                        className="block w-full bg-primary-50 hover:bg-primary-100 text-primary-700 px-4 py-2 rounded-lg text-sm transition"
                      >
                        {msg}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.speaker === 'customer' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[70%] rounded-lg px-4 py-3 ${
                        message.speaker === 'agent'
                          ? 'bg-primary-100 text-primary-900'
                          : message.speaker === 'customer'
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-100 text-gray-600 text-sm italic'
                      }`}
                    >
                      {message.speaker !== 'system' && (
                        <div className="flex items-center gap-2 mb-1">
                          {message.speaker === 'agent' && <User className="w-3 h-3" />}
                          <span className="text-xs font-semibold uppercase opacity-75">
                            {message.speaker === 'agent' ? 'Support Agent' : 'You'}
                          </span>
                          <span className="text-xs opacity-60">
                            {message.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                      )}
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
                  placeholder={connected ? "Type your message..." : "Connect to agent to send messages"}
                  disabled={!connected}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
                />
                <button
                  onClick={sendMessage}
                  disabled={!connected || !inputMessage.trim()}
                  className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              
              {/* Quick Messages when connected */}
              {connected && messages.length > 0 && (
                <div className="mt-3 flex gap-2 overflow-x-auto">
                  {quickMessages.map((msg, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputMessage(msg)}
                      className="flex-shrink-0 bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded-full text-xs transition"
                    >
                      {msg}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          

          {/* Customer Info Panel */}
          <div className="mt-6 bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-900 mb-3">Your Info (Loaded)</h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Name</span>
                <p className="font-medium">{(serverContext?.name ?? customer?.name) || '—'}</p>
              </div>
              <div>
                <span className="text-gray-600">Account</span>
                <p className="font-medium">{(serverContext?.account_number ?? customer?.accountNumber) || '—'}</p>
              </div>
              <div>
                <span className="text-gray-600">Tier</span>
                <p className="font-medium">{(serverContext?.tier ?? customer?.tier) || 'standard'}</p>
              </div>
              <div>
                <span className="text-gray-600">Email</span>
                <p className="font-medium">{(serverContext?.email ?? customer?.email) || '—'}</p>
              </div>
            </div>
            {!connected && (
              <p className="mt-3 text-xs text-gray-500">Connect to agent to receive tailored assistance.</p>
            )}
            {serverContext && (
              <div className="mt-4">
                <h4 className="font-semibold text-gray-900 mb-2">Recent Orders</h4>
                {serverContext.orders && serverContext.orders.length > 0 ? (
                  <ul className="text-sm text-gray-700 space-y-1">
                    {serverContext.orders.map((o: any) => (
                      <li key={o.order_number} className="flex justify-between">
                        <span>{o.product_name}</span>
                        <span className="text-gray-500">{o.order_number}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">No recent orders</p>
                )}
                <h4 className="font-semibold text-gray-900 mt-4 mb-2">Recent Tickets</h4>
                {serverContext.tickets && serverContext.tickets.length > 0 ? (
                  <ul className="text-sm text-gray-700 space-y-1">
                    {serverContext.tickets.map((t: any) => (
                      <li key={t.ticket_number} className="flex justify-between">
                        <span>{t.subject}</span>
                        <span className="text-gray-500">{t.ticket_number}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-gray-500">No recent tickets</p>
                )}
              </div>
            )}
          </div>

          {/* Info Card moved to end */}
          <div className="mt-6 bg-white rounded-lg shadow p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                <MessageSquare className="w-5 h-5 text-primary-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 mb-1">How it works</h3>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Click "Connect to Agent" to start a conversation</li>
                  <li>• Type your message and press Enter to send</li>
                  <li>• Our agents will respond in real-time</li>
                  <li>• Click "End Chat" when you're done</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
