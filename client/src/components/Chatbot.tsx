import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, X, Send, Bot, User, Trash2, Sparkles } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface Message {
  role: 'user' | 'model';
  content: string;
}

export const Chatbot: React.FC = () => {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of message list on updates
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
    }
  }, [history, isOpen, loading]);

  // Initial welcome message
  useEffect(() => {
    if (history.length === 0) {
      setHistory([
        {
          role: 'model',
          content: "Hello Operator! I am your AI Operations Assistant. Ask me anything about the furnace live telemetry, safety limits, or active alarms in the plant."
        }
      ]);
    }
  }, []);

  const handleSend = async (textToSend?: string) => {
    const rawPrompt = textToSend || message;
    if (!rawPrompt.trim()) return;

    // Clear input
    if (!textToSend) setMessage('');

    // Append user message to history
    const updatedHistory = [...history, { role: 'user', content: rawPrompt } as Message];
    setHistory(updatedHistory);
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: rawPrompt,
          history: updatedHistory.slice(0, -1).map(h => ({
            role: h.role,
            content: h.content
          }))
        })
      });

      if (res.ok) {
        const data = await res.json();
        setHistory(prev => [...prev, { role: 'model', content: data.response }]);
        if (data.offline) {
          setIsOffline(true);
        } else {
          setIsOffline(false);
        }
      } else {
        throw new Error('Connection failed');
      }
    } catch (e) {
      console.error(e);
      setHistory(prev => [
        ...prev,
        {
          role: 'model',
          content: "**Chat Connection Error**\n\nUnable to reach the AI engine. Please verify the FastAPI backend server is running and healthy."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const clearHistory = () => {
    setHistory([
      {
        role: 'model',
        content: "Chat history cleared. How can I assist you with the live furnace analytics now?"
      }
    ]);
  };

  // Custom markdown formatting parser for sleek cyan/text rendering
  const formatMessageContent = (text: string) => {
    if (!text) return "";
    
    const lines = text.split('\n');
    return (
      <div className="space-y-1.5 font-sans">
        {lines.map((line, idx) => {
          let trimmed = line.trim();
          let isBullet = false;
          let isNumbered = false;
          let numPrefix = "";
          
          if (trimmed.startsWith('- ')) {
            isBullet = true;
            trimmed = trimmed.substring(2);
          } else if (trimmed.startsWith('* ')) {
            isBullet = true;
            trimmed = trimmed.substring(2);
          } else {
            const numMatch = trimmed.match(/^(\d+)\.\s(.*)/);
            if (numMatch) {
              isNumbered = true;
              numPrefix = numMatch[1];
              trimmed = numMatch[2];
            }
          }
          
          // Parse **bold** tags
          const boldRegex = /\*\*(.*?)\*\*/g;
          const parts = [];
          let lastIndex = 0;
          let match;
          
          while ((match = boldRegex.exec(trimmed)) !== null) {
            if (match.index > lastIndex) {
              parts.push(trimmed.substring(lastIndex, match.index));
            }
            parts.push(<strong key={match.index} className="font-extrabold text-cyan-400">{match[1]}</strong>);
            lastIndex = boldRegex.lastIndex;
          }
          
          if (lastIndex < trimmed.length) {
            parts.push(trimmed.substring(lastIndex));
          }
          
          const content = parts.length > 0 ? parts : trimmed;
          
          if (line.trim() === '') {
            return <div key={idx} className="h-1.5" />;
          }
          
          if (isBullet) {
            return (
              <div key={idx} className="flex items-start gap-2 ml-2">
                <span className="text-cyan-400 mt-2 h-1.5 w-1.5 rounded-full bg-cyan-400 flex-shrink-0 shadow-[0_0_4px_#22d3ee]" />
                <span className="text-slate-300 text-[13px] leading-relaxed">{content}</span>
              </div>
            );
          }
          
          if (isNumbered) {
            return (
              <div key={idx} className="flex items-start gap-2 ml-2">
                <span className="text-cyan-400 font-mono text-xs mt-0.5 font-bold">{numPrefix}.</span>
                <span className="text-slate-300 text-[13px] leading-relaxed">{content}</span>
              </div>
            );
          }
          
          return <p key={idx} className="text-slate-300 text-[13px] leading-relaxed">{content}</p>;
        })}
      </div>
    );
  };

  const suggestionPills = [
    "Are there active alarms?",
    "Status of SMS-1 furnace",
    "List key sensors",
    "What is this platform?"
  ];

  return (
    <>
      {/* FLOATING ACTION BUTTON */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 text-white flex items-center justify-center shadow-[0_0_20px_rgba(79,70,229,0.5)] hover:shadow-[0_0_25px_rgba(34,211,238,0.7)] transition-all duration-300 hover:scale-105 z-40 border border-white/10 group"
        title="Open AI Operations Assistant"
      >
        {isOpen ? (
          <X className="h-6 w-6 transition-transform duration-300 rotate-90" />
        ) : (
          <div className="relative">
            <MessageSquare className="h-6 w-6 transition-transform duration-300 group-hover:rotate-12" />
            <span className="absolute -top-1.5 -right-1.5 h-3 w-3 bg-cyan-400 rounded-full border border-[#070913] animate-ping" />
            <span className="absolute -top-1.5 -right-1.5 h-3 w-3 bg-cyan-400 rounded-full border border-[#070913]" />
          </div>
        )}
      </button>

      {/* CHAT DRAWER */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[500px] bg-[#0E1326]/95 backdrop-blur-md border border-[#222F54] rounded-2xl shadow-2xl flex flex-col overflow-hidden z-40 transition-all duration-300 animate-in fade-in slide-in-from-bottom-5">
          {/* HEADER */}
          <div className="p-4 border-b border-[#222F54] bg-[#141C38] flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-indigo-500/20 text-indigo-400 relative">
                <Bot className="h-5 w-5" />
                <span className={`absolute bottom-0 right-0 h-2 w-2 rounded-full ring-2 ring-[#141C38] ${isOffline ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500 animate-pulse'}`} />
              </div>
              <div>
                <h3 className="font-bold text-xs text-white uppercase tracking-wider flex items-center gap-1">
                  AI Operations Copilot
                  <Sparkles className="h-3 w-3 text-cyan-400 animate-pulse" />
                </h3>
                <p className="text-[9px] text-cyan-400/90 font-mono tracking-widest uppercase">
                  {isOffline ? 'Offline Fallback Snapshot' : 'Live SCADA Core Engine'}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={clearHistory}
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-[#202B52]/40 transition-all"
                title="Clear Chat History"
              >
                <Trash2 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#202B52]/40 transition-all"
                title="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* MESSAGES LIST */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
            {history.map((msg, i) => (
              <div
                key={i}
                className={`flex gap-3 items-start ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role === 'model' && (
                  <div className="p-1.5 rounded-lg bg-[#202B52] border border-[#2B3A6C] text-cyan-400 mt-1">
                    <Bot className="h-4.5 w-4.5" />
                  </div>
                )}
                
                <div
                  className={`max-w-[78%] rounded-2xl px-4 py-3 text-sm shadow-md transition-all ${
                    msg.role === 'user'
                      ? 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-tr-none border border-indigo-500/20'
                      : 'bg-[#18203E]/80 border border-[#2B3A6C] text-slate-200 rounded-tl-none'
                  }`}
                >
                  {formatMessageContent(msg.content)}
                </div>

                {msg.role === 'user' && (
                  <div className="p-1.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30 text-indigo-400 mt-1">
                    <User className="h-4.5 w-4.5" />
                  </div>
                )}
              </div>
            ))}

            {/* TYPING INDICATOR */}
            {loading && (
              <div className="flex gap-3 items-start justify-start">
                <div className="p-1.5 rounded-lg bg-[#202B52] border border-[#2B3A6C] text-cyan-400 mt-1">
                  <Bot className="h-4.5 w-4.5" />
                </div>
                <div className="bg-[#18203E]/80 border border-[#2B3A6C] rounded-2xl rounded-tl-none px-4 py-3 flex items-center gap-1 shadow-md">
                  <span className="h-2 w-2 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 bg-cyan-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 bg-cyan-400 rounded-full animate-bounce" />
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* DYNAMIC SUGGESTIONS */}
          {history.length < 5 && (
            <div className="px-4 py-2 bg-[#121933]/50 border-t border-[#222F54]/40 flex flex-wrap gap-2">
              {suggestionPills.map((pill, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(pill)}
                  className="text-[10px] text-cyan-400 font-semibold bg-[#182245] hover:bg-[#202D5C] border border-[#2B3B70] px-2.5 py-1.5 rounded-full transition-all duration-200 hover:border-cyan-400/50 hover:shadow-[0_0_8px_rgba(34,211,238,0.2)]"
                >
                  {pill}
                </button>
              ))}
            </div>
          )}

          {/* INPUT AREA */}
          <div className="p-4 border-t border-[#222F54] bg-[#10162E] flex gap-2.5 items-center">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={isOffline ? "Ask local questions (Alarms, Sensors)..." : "Ask Copilot about sensors or active alarms..."}

              className="flex-1 bg-[#151D3B] text-slate-100 placeholder-slate-500 text-xs px-3.5 py-2.5 rounded-xl border border-[#263566] focus:outline-none focus:border-cyan-500 focus:shadow-[0_0_8px_rgba(34,211,238,0.3)] transition-all"
              disabled={loading}
            />
            <button
              onClick={() => handleSend()}
              disabled={loading || !message.trim()}
              className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-[#1C2340] disabled:text-slate-500 text-white transition-all hover:scale-105 duration-200 cursor-pointer shadow-lg flex items-center justify-center flex-shrink-0"
              title="Send Message"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
