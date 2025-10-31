'use client';

import { useEffect, useRef, useState } from 'react';
import coachAPI from '@/lib/coachApi';
import { Send, Sparkles, User, Bot, Loader2, CheckCircle2, Shield, Zap, Heart, Star, TrendingUp } from 'lucide-react';

interface Msg { id: string; role: 'parent' | 'coach' | 'system'; text: string; at: Date }

export default function CoachChatPage() {
  const [parent, setParent] = useState<{ name: string } | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [sessionId, setSessionId] = useState('');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Msg[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const endRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const p = localStorage.getItem('parent');
    if (p) setParent(JSON.parse(p));
  }, []);

  useEffect(() => { 
    endRef.current?.scrollIntoView({ behavior: 'smooth' }); 
  }, [messages]);

  const start = async () => {
    if (!parent) return;
    setConnectionStatus('connecting');
    try {
      const { session_id, message } = await coachAPI.startSession(parent.name);
      setSessionId(session_id);
      setMessages((m) => [...m, { 
        id: crypto.randomUUID(), 
        role: 'system', 
        text: message, 
        at: new Date() 
      }]);
      
      const socket = new WebSocket(`ws://localhost:8011/ws/coach/${session_id}`);
      
      socket.onopen = () => {
        setWs(socket);
        setConnectionStatus('connected');
        inputRef.current?.focus();
      };
      
      socket.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          if (data.type === 'advice') {
            setIsTyping(true);
            setTimeout(() => {
              setMessages((m) => [
                ...m,
                { id: crypto.randomUUID(), role: 'coach', text: data.text, at: new Date() },
              ]);
              setIsTyping(false);
            }, 1000);
          } else if (data.type === 'session_started') {
            setMessages((m) => [...m, { 
              id: crypto.randomUUID(), 
              role: 'system', 
              text: '✨ Session ready! How can I help you today?', 
              at: new Date() 
            }]);
          }
        } catch {
          // ignore malformed messages
        }
      };
      
      socket.onclose = () => {
        setWs(null);
        setConnectionStatus('disconnected');
      };
      
      socket.onerror = () => {
        setConnectionStatus('disconnected');
      };
    } catch (error) {
      setConnectionStatus('disconnected');
      setMessages((m) => [...m, { 
        id: crypto.randomUUID(), 
        role: 'system', 
        text: '❌ Failed to connect. Please try again.', 
        at: new Date() 
      }]);
    }
  };

  const send = () => {
    if (!input.trim() || !ws) return;
    ws.send(JSON.stringify({ type: 'text', text: input.trim() }));
    setMessages((m) => [...m, { 
      id: crypto.randomUUID(), 
      role: 'parent', 
      text: input.trim(), 
      at: new Date() 
    }]);
    setInput('');
    inputRef.current?.focus();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-orange-50/40 to-amber-50/60 flex items-center py-8">
      <div className="container mx-auto px-4 md:px-6 max-w-6xl w-full">
        {/* Header Card */}
        <div className="bg-gradient-to-r from-orange-500 via-amber-500 to-orange-500 backdrop-blur-xl rounded-[2.5rem] shadow-2xl border-3 border-orange-300/50 p-8 mb-8 animate-slide-up relative overflow-hidden">
          {/* Animated Background */}
          <div className="absolute inset-0 bg-gradient-to-r from-orange-400/20 to-amber-400/20 animate-pulse" />
          
          <div className="relative z-10 flex items-center justify-between flex-wrap gap-6">
            <div className="flex items-center gap-5">
              <div className="w-20 h-20 bg-white rounded-3xl flex items-center justify-center shadow-2xl">
                <Sparkles className="w-10 h-10 text-orange-500 animate-pulse" />
              </div>
              <div>
                <h1 className="text-3xl md:text-4xl font-black text-white drop-shadow-lg flex items-center gap-2">
                  Child Growth Assistant
                  <Star className="w-6 h-6 fill-white animate-pulse" />
                </h1>
                <div className="flex items-center gap-3 mt-1">
                  <span className="text-lg font-black text-orange-100">👋 {parent?.name || 'Loading...'}</span>
                  {connectionStatus === 'connected' && (
                    <>
                      <span className="text-orange-200">•</span>
                      <div className="flex items-center gap-2 bg-green-400/30 px-3 py-1 rounded-full border border-green-300/50">
                        <div className="w-2.5 h-2.5 bg-green-300 rounded-full animate-pulse shadow-lg" />
                        <span className="text-sm font-black text-white">Live</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
            
            {connectionStatus === 'disconnected' ? (
              <button 
                onClick={start} 
                className="bg-white text-orange-700 rounded-2xl px-10 py-4 font-black text-lg hover:shadow-2xl hover:scale-110 transition-all duration-200 flex items-center gap-3 border-3 border-orange-300/50 shadow-xl"
              >
                <Zap className="w-6 h-6 fill-orange-600 animate-pulse" />
                Start Session
              </button>
            ) : connectionStatus === 'connecting' ? (
              <div className="flex items-center gap-3 bg-white/20 px-6 py-3 rounded-2xl backdrop-blur-sm border border-white/30">
                <Loader2 className="w-6 h-6 animate-spin text-white" />
                <span className="font-black text-white">Connecting...</span>
              </div>
            ) : (
              <div className="flex items-center gap-3 bg-green-500 px-6 py-3 rounded-2xl shadow-xl border-2 border-green-300">
                <CheckCircle2 className="w-6 h-6 text-white" />
                <span className="font-black text-white">Active Session</span>
              </div>
            )}
          </div>
        </div>

        {/* Chat Container */}
        <div className="bg-white backdrop-blur-xl rounded-[2.5rem] shadow-2xl border-2 border-slate-100 overflow-hidden animate-scale-in">
          {/* Messages Area */}
          <div className="h-[650px] overflow-y-auto p-8 md:p-10 space-y-8 bg-gradient-to-br from-slate-50/30 via-orange-50/20 to-amber-50/30">
            {messages.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center max-w-2xl">
                  <div className="inline-flex items-center justify-center w-32 h-32 bg-gradient-to-br from-orange-500 to-amber-500 rounded-[2rem] mb-8 shadow-2xl shadow-orange-500/50 relative">
                    <Heart className="w-16 h-16 text-white fill-white animate-pulse" />
                    <div className="absolute -top-4 -right-4 w-16 h-16 bg-gradient-to-br from-rose-500 to-pink-500 rounded-full flex items-center justify-center shadow-xl animate-bounce">
                      <Sparkles className="w-8 h-8 text-white" />
                    </div>
                  </div>
                  
                  <h3 className="text-4xl font-black mb-4">
                    <span className="bg-gradient-to-r from-orange-600 to-amber-600 bg-clip-text text-transparent">
                      Ready to Start?
                    </span>
                  </h3>
                  <p className="text-slate-600 mb-10 text-xl font-semibold">
                    Click <span className="text-orange-600 font-black">"Start Session"</span> above to begin your personalized coaching
                  </p>
                  
                  <div className="flex flex-wrap gap-4 justify-center">
                    {[
                      { text: '😴 Sleep routines', gradient: 'from-blue-500 to-indigo-600' },
                      { text: '🤝 Sibling conflicts', gradient: 'from-purple-500 to-pink-600' },
                      { text: '📱 Screen time', gradient: 'from-orange-500 to-red-600' },
                      { text: '😢 Tantrums', gradient: 'from-rose-500 to-pink-600' }
                    ].map((topic) => (
                      <div 
                        key={topic.text} 
                        className={`px-6 py-3 bg-gradient-to-r ${topic.gradient} text-white rounded-full text-base font-bold shadow-lg hover:scale-110 transition-transform cursor-pointer`}
                      >
                        {topic.text}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <>
                {messages.map((m, idx) => (
                  <div 
                    key={m.id} 
                    className={`flex ${m.role === 'parent' ? 'justify-end' : 'justify-start'} animate-slide-up`}
                    style={{ animationDelay: `${idx * 30}ms` }}
                  >
                    <div className={`flex gap-4 max-w-[80%] ${m.role === 'parent' ? 'flex-row-reverse' : 'flex-row'}`}>
                      {/* Avatar */}
                      {m.role !== 'system' && (
                        <div className={`flex-shrink-0 w-14 h-14 rounded-2xl flex items-center justify-center shadow-xl border-3 ${
                          m.role === 'coach'
                            ? 'bg-gradient-to-br from-amber-400 via-orange-500 to-amber-600 border-orange-300'
                            : 'bg-gradient-to-br from-orange-600 via-orange-500 to-amber-600 border-orange-400'
                        }`}>
                          {m.role === 'coach' ? (
                            <Bot className="w-7 h-7 text-white" />
                          ) : (
                            <User className="w-7 h-7 text-white" />
                          )}
                        </div>
                      )}
                      
                      {/* Message Bubble */}
                      <div className={`rounded-3xl px-7 py-5 shadow-xl border-3 ${
                        m.role === 'parent'
                          ? 'bg-gradient-to-br from-orange-600 via-orange-500 to-amber-600 text-white border-orange-400'
                          : m.role === 'coach'
                          ? 'bg-gradient-to-br from-amber-50 via-orange-50 to-amber-50 text-slate-900 border-orange-300'
                          : 'bg-gradient-to-br from-blue-50 to-cyan-50 text-slate-700 border-blue-300'
                      }`}>
                        <p className={`leading-relaxed whitespace-pre-wrap font-semibold text-lg ${
                          m.role === 'coach' ? 'text-slate-800' : ''
                        }`}>
                          {m.text}
                        </p>
                        <div className={`text-xs mt-3 font-bold flex items-center gap-2 ${
                          m.role === 'parent' ? 'text-white/80' : 'text-slate-600'
                        }`}>
                          <span>{m.at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                          {m.role === 'parent' && <CheckCircle2 className="w-3.5 h-3.5" />}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Typing Indicator */}
                {isTyping && (
                  <div className="flex gap-4 animate-slide-up">
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center bg-gradient-to-br from-amber-400 to-orange-500 shadow-xl border-3 border-orange-300">
                      <Bot className="w-7 h-7 text-white" />
                    </div>
                    <div className="bg-gradient-to-br from-amber-50 to-orange-100 border-3 border-orange-300 rounded-3xl px-7 py-5 shadow-xl">
                      <div className="flex gap-2">
                        <div className="w-4 h-4 bg-gradient-to-r from-orange-500 to-amber-500 rounded-full animate-bounce shadow-lg" />
                        <div className="w-4 h-4 bg-gradient-to-r from-orange-500 to-amber-500 rounded-full animate-bounce shadow-lg" style={{ animationDelay: '0.2s' }} />
                        <div className="w-4 h-4 bg-gradient-to-r from-orange-500 to-amber-500 rounded-full animate-bounce shadow-lg" style={{ animationDelay: '0.4s' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={endRef} />
              </>
            )}
          </div>

          {/* Input Area */}
          <div className="border-t-3 border-slate-200 p-8 bg-gradient-to-r from-orange-50/50 via-amber-50/50 to-orange-50/50 backdrop-blur-sm">
            <div className="flex gap-4">
              <input
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { 
                  if (e.key === 'Enter' && !e.shiftKey) { 
                    e.preventDefault(); 
                    send(); 
                  } 
                }}
                placeholder={ws ? 'Ask about routines, conflicts, screen time…' : 'Start session to begin chatting'}
                disabled={!ws}
                className="flex-1 border-3 border-orange-300 rounded-2xl px-7 py-5 focus:ring-4 focus:ring-orange-500/40 focus:border-orange-500 disabled:bg-slate-100 disabled:cursor-not-allowed outline-none transition-all text-slate-900 text-lg font-semibold placeholder:text-slate-500 hover:border-orange-400 bg-white shadow-inner"
              />
              <button
                onClick={send}
                disabled={!ws || !input.trim()}
                className="bg-gradient-to-r from-orange-600 via-orange-500 to-amber-600 text-white rounded-2xl px-10 py-5 font-black disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-2xl hover:shadow-orange-500/50 hover:scale-110 transition-all duration-200 flex items-center gap-3 group border-3 border-orange-400/50 shadow-xl"
              >
                <Send className="w-7 h-7 group-hover:translate-x-1 transition-transform" />
                <span className="hidden sm:inline text-xl">Send</span>
              </button>
            </div>
            
            {/* Quick Tips */}
            {ws && messages.length < 2 && (
              <div className="mt-6 flex flex-wrap gap-3 items-center justify-center">
                <TrendingUp className="w-5 h-5 text-slate-500" />
                <span className="text-sm text-slate-600 font-black uppercase tracking-wide">Popular Topics:</span>
                {[
                  { text: 'Bedtime resistance', gradient: 'from-blue-500 to-cyan-600' },
                  { text: 'Picky eating', gradient: 'from-green-500 to-emerald-600' },
                  { text: 'Homework battles', gradient: 'from-purple-500 to-violet-600' }
                ].map((tip) => (
                  <button
                    key={tip.text}
                    onClick={() => setInput(tip.text)}
                    className={`text-sm px-5 py-2.5 bg-gradient-to-r ${tip.gradient} text-white rounded-full font-bold shadow-lg hover:scale-110 hover:shadow-xl transition-all border-2 border-white/50`}
                  >
                    {tip.text}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <div className="inline-flex items-center gap-3 bg-white px-7 py-4 rounded-full border-2 border-slate-200 shadow-lg">
            <Shield className="w-5 h-5 text-orange-600" />
            <p className="text-sm text-slate-700 font-bold">
              <span className="text-orange-700 font-black">General guidance</span> · For urgent concerns, consult a professional
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
