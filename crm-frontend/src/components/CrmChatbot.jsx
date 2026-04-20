import { useState, useRef, useEffect } from 'react';

const BACKEND_URL = 'https://crm-backend-z5d9.onrender.com';

function generateSessionId() {
  return 'session_' + Math.random().toString(36).substring(2, 9);
}

// ── Pricing Card ──────────────────────────────────────────────
const PricingCard = () => (
  <div className="mt-3 w-full max-w-sm rounded-2xl border border-teal-100 bg-white shadow-lg overflow-hidden">
    <div className="bg-gradient-to-r from-teal-600 to-teal-500 px-4 py-2.5">
      <p className="text-xs font-bold text-white uppercase tracking-widest">NexCRM Plans</p>
    </div>
    <div className="divide-y divide-slate-100">
      {[
        { label: 'Basic',      price: '₹8,000',  note: '/month · up to 5 users',      highlight: false },
        { label: 'Pro',        price: '₹20,000', note: '/month · up to 20 users',     highlight: true  },
        { label: 'Enterprise', price: '₹45,000', note: '/month · unlimited users',    highlight: false },
      ].map(({ label, price, note, highlight }) => (
        <div key={label} className={`flex items-center justify-between px-4 py-3 ${highlight ? 'bg-teal-50' : ''}`}>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-700">{label}</span>
            {highlight && <span className="text-[10px] bg-teal-600 text-white px-1.5 py-0.5 rounded-full font-semibold">Popular</span>}
          </div>
          <div className="text-right">
            <span className="text-sm font-bold text-slate-900">{price}</span>
            <span className="block text-xs text-slate-400">{note}</span>
          </div>
        </div>
      ))}
    </div>
    <div className="px-4 py-2 bg-slate-50 text-xs text-slate-500 text-center">
      All plans include 30-day free trial
    </div>
  </div>
);

// ── Markdown renderer ─────────────────────────────────────────
function renderMarkdown(text) {
  return text.split('\n').map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
    const rendered = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**'))
        return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>;
      if (part.startsWith('`') && part.endsWith('`'))
        return <code key={j} className="bg-slate-100 text-teal-700 px-1.5 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
      if (part.startsWith('*') && part.endsWith('*'))
        return <em key={j}>{part.slice(1, -1)}</em>;
      // Render | table rows as formatted text
      if (line.startsWith('|') && line.endsWith('|')) {
        return <span key={j} className="font-mono text-xs">{part}</span>;
      }
      return <span key={j}>{part}</span>;
    });
    return <span key={i}>{rendered}{i < text.split('\n').length - 1 ? '\n' : ''}</span>;
  });
}

// ── Message Bubble ────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isBot     = msg.sender === 'bot';
  const hasPricing = isBot && msg.text.includes('[SHOW_PRICING]');
  const cleanText  = msg.text.replace('[SHOW_PRICING]', '').trim();

  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} mb-4`}>
      {isBot && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center mr-2.5 mt-1 flex-shrink-0 shadow-md">
          <span className="text-white text-xs font-bold">N</span>
        </div>
      )}
      <div className="max-w-[82%]">
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isBot
            ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-sm'
            : 'bg-gradient-to-br from-teal-600 to-teal-700 text-white rounded-tr-none shadow-md'
        }`}>
          {isBot ? renderMarkdown(cleanText) : cleanText}
        </div>
        {hasPricing && <PricingCard />}
        <p className={`text-[10px] mt-1 ${isBot ? 'text-slate-400 ml-1' : 'text-slate-400 text-right'}`}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}

// ── Quick Reply Chips ─────────────────────────────────────────
const QUICK_REPLIES = [
  "What is your pricing?",
  "I want a demo",
  "I found a bug",
  "Show dashboard",
];

// ── Main Component ────────────────────────────────────────────
export default function CrmChatbot() {
  const sessionId = useRef(generateSessionId());
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  const WELCOME_MSG = "👋 Hello! I'm your **AI Sales Assistant** for NexCRM.\n\nI can help you with:\n• 💰 Pricing & Plans\n• 🎯 Book a Demo\n• 📋 Create a Deal or Proposal\n• 🐛 Raise a Support Ticket\n• 📊 View Dashboard & Pipeline *(say 'show dashboard')*\n\nWhat can I help you with today?";

  const [messages,  setMessages]  = useState([{ sender: 'bot', text: WELCOME_MSG }]);
  const [input,     setInput]     = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [convState, setConvState] = useState('IDLE');
  const [convData,  setConvData]  = useState({});

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const send = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    setMessages(prev => [...prev, { sender: 'user', text: trimmed }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message:  trimmed,
          user_id:  sessionId.current,
          state:    convState,
          data:     convData,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = await res.json();

      setConvState(result.state || 'IDLE');
      setConvData(result.data   || {});
      setMessages(prev => [...prev, { sender: 'bot', text: result.response }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: "⚠️ I'm having trouble connecting right now. Please try again in a moment."
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => { e.preventDefault(); send(input); };
  const handleChip   = (chip) => send(chip);

  const handleReset = () => {
    sessionId.current = generateSessionId();
    setConvState('IDLE');
    setConvData({});
    setMessages([{ sender: 'bot', text: WELCOME_MSG }]);
  };

  const showChips = messages.length <= 2 && !isLoading;

  return (
    <div className="flex flex-col h-[640px] bg-slate-50 rounded-3xl overflow-hidden shadow-2xl border border-slate-200">

      {/* ── Header ── */}
      <div className="bg-white px-5 py-3.5 border-b border-slate-100 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center shadow-md">
            <span className="text-white font-bold">N</span>
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">NexCRM Assistant</p>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              <p className="text-xs text-green-600 font-medium">Online · AI Sales Bot</p>
            </div>
          </div>
        </div>
        <button onClick={handleReset}
          className="text-xs text-slate-400 hover:text-teal-600 transition-colors px-3 py-1.5 rounded-full hover:bg-teal-50 font-medium">
          New Chat
        </button>
      </div>

      {/* ── Messages ── */}
      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2">
        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}

        {/* Quick reply chips */}
        {showChips && (
          <div className="flex flex-wrap gap-2 mb-3 ml-10">
            {QUICK_REPLIES.map(chip => (
              <button key={chip} onClick={() => handleChip(chip)}
                className="text-xs bg-white border border-teal-200 text-teal-700 px-3 py-1.5 rounded-full hover:bg-teal-50 hover:border-teal-400 transition font-medium shadow-sm">
                {chip}
              </button>
            ))}
          </div>
        )}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center mr-2.5 mt-1 flex-shrink-0">
              <span className="text-white text-xs font-bold">N</span>
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
              <div className="flex gap-1 items-center h-4">
                {[0,150,300].map(d => (
                  <span key={d} className="w-2 h-2 bg-teal-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${d}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input ── */}
      <form onSubmit={handleSubmit} className="px-4 py-3 bg-white border-t border-slate-100">
        <div className="flex gap-2 items-center">
          <input ref={inputRef} type="text" value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about pricing, demo, support..."
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 text-sm bg-slate-100 rounded-full focus:outline-none focus:ring-2 focus:ring-teal-400 focus:bg-white transition disabled:opacity-50 text-slate-800 placeholder-slate-400"
          />
          <button type="submit" disabled={isLoading || !input.trim()}
            className="w-10 h-10 bg-gradient-to-br from-teal-500 to-teal-700 rounded-full flex items-center justify-center hover:opacity-90 transition disabled:opacity-40 shadow-md flex-shrink-0">
            <svg className="w-4 h-4 text-white translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}