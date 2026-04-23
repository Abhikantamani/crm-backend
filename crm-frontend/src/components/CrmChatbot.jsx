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
        { label: 'Basic',      price: '₹8,000',  note: '/month · up to 5 users',   tag: null      },
        { label: 'Pro',        price: '₹20,000', note: '/month · up to 20 users',  tag: 'Popular' },
        { label: 'Enterprise', price: '₹45,000', note: '/month · unlimited users', tag: null      },
      ].map(({ label, price, note, tag }) => (
        <div key={label} className={`flex items-center justify-between px-4 py-3 ${tag ? 'bg-teal-50' : ''}`}>
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-700">{label}</span>
            {tag && <span className="text-[10px] bg-teal-600 text-white px-1.5 py-0.5 rounded-full font-semibold">{tag}</span>}
          </div>
          <div className="text-right">
            <span className="text-sm font-bold text-slate-900">{price}</span>
            <span className="block text-xs text-slate-400">{note}</span>
          </div>
        </div>
      ))}
    </div>
    <div className="px-4 py-2 bg-slate-50 text-xs text-slate-400 text-center">
      All plans include 30-day free trial · No credit card required
    </div>
  </div>
);

// ── Markdown renderer ─────────────────────────────────────────
function renderMarkdown(text) {
  return text.split('\n').map((line, i, arr) => {
    const isLast = i === arr.length - 1;

    // Table rows
    if (line.startsWith('|') && line.endsWith('|')) {
      const cells = line.split('|').filter(c => c.trim() !== '');
      if (cells.every(c => /^[-: ]+$/.test(c))) return null;
      return (
        <div key={i} className="flex text-xs border-b border-slate-100 last:border-0 bg-slate-50 rounded">
          {cells.map((cell, j) => (
            <span key={j} className="flex-1 px-2 py-1.5 text-slate-700">{cell.trim()}</span>
          ))}
        </div>
      );
    }

    const parts = line.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
    const rendered = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**'))
        return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>;
      if (part.startsWith('`') && part.endsWith('`'))
        return <code key={j} className="bg-slate-100 text-teal-700 px-1.5 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
      if (part.startsWith('*') && part.endsWith('*'))
        return <em key={j}>{part.slice(1, -1)}</em>;
      return <span key={j}>{part}</span>;
    });

    return <span key={i}>{rendered}{!isLast ? '\n' : ''}</span>;
  }).filter(Boolean);
}

// ── Message Bubble ────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isBot      = msg.sender === 'bot';
  const hasPricing = isBot && msg.text.toLowerCase().includes('pricing plans') &&
                     msg.text.includes('₹8,000');
  const cleanText  = msg.text;

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
        <p className={`text-[10px] mt-1 text-slate-400 ${isBot ? 'ml-1' : 'text-right'}`}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}

// ── Quick Chips ───────────────────────────────────────────────
const CHIPS = [
  "What is your pricing?",
  "I want a demo",
  "What is the next best action?",
  "I found a bug",
];

// ── Main Component ────────────────────────────────────────────
export default function CrmChatbot() {
  const sessionId = useRef(generateSessionId());
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  const WELCOME = "👋 Hello! I'm your **AI Sales Assistant** for NexCRM.\n\nHow can I help you today? I can help you with pricing, demos, features, support, or anything else about NexCRM.\n\nWhat would you like to know?";

  const [messages,   setMessages]   = useState([{ sender: 'bot', text: WELCOME }]);
  const [input,      setInput]      = useState('');
  const [isLoading,  setIsLoading]  = useState(false);
  const [convState,  setConvState]  = useState('IDLE');
  const [convData,   setConvData]   = useState({});
  // Full conversation history sent to Grok for context
  const [convHistory, setConvHistory] = useState([]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const send = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    // Add to visible messages
    setMessages(prev => [...prev, { sender: 'user', text: trimmed }]);
    setInput('');
    setIsLoading(true);

    // Build updated history to send
    const updatedHistory = [
      ...convHistory,
      { role: 'user', content: trimmed }
    ];

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message:  trimmed,
          user_id:  sessionId.current,
          state:    convState,
          data:     convData,
          history:  updatedHistory,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = await res.json();

      const botReply = result.response || "I'm having trouble responding. Please try again.";

      // Update state
      setConvState(result.state || 'IDLE');
      setConvData(result.data   || {});

      // Append bot reply to history
      setConvHistory([
        ...updatedHistory,
        { role: 'assistant', content: botReply }
      ]);

      setMessages(prev => [...prev, { sender: 'bot', text: botReply }]);

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: "⚠️ I'm having trouble connecting right now. Please try again in a moment.\n\n*(If this is the first message, Render may be waking up — please wait 30 seconds)*"
      }]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e) => { e.preventDefault(); send(input); };

  const handleReset = () => {
    sessionId.current = generateSessionId();
    setConvState('IDLE');
    setConvData({});
    setConvHistory([]);
    setMessages([{ sender: 'bot', text: WELCOME }]);
  };

  const showChips = messages.length <= 2 && !isLoading;

  return (
    <div className="flex flex-col h-[640px] bg-slate-50 rounded-3xl overflow-hidden shadow-2xl border border-slate-200">

      {/* Header */}
      <div className="bg-white px-5 py-3.5 border-b border-slate-100 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center shadow-md">
            <span className="text-white font-bold">N</span>
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">NexCRM Assistant</p>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
              <p className="text-xs text-green-600 font-medium">Online · Powered by Grok AI</p>
            </div>
          </div>
        </div>
        <button onClick={handleReset}
          className="text-xs text-slate-400 hover:text-teal-600 transition px-3 py-1.5 rounded-full hover:bg-teal-50 font-medium">
          New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2">
        {messages.map((msg, i) => <MessageBubble key={i} msg={msg} />)}

        {showChips && (
          <div className="flex flex-wrap gap-2 mb-3 ml-10">
            {CHIPS.map(chip => (
              <button key={chip} onClick={() => send(chip)}
                className="text-xs bg-white border border-teal-200 text-teal-700 px-3 py-1.5 rounded-full hover:bg-teal-50 hover:border-teal-400 transition font-medium shadow-sm">
                {chip}
              </button>
            ))}
          </div>
        )}

        {isLoading && (
          <div className="flex justify-start mb-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center mr-2.5 mt-1 flex-shrink-0">
              <span className="text-white text-xs font-bold">N</span>
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
              <div className="flex gap-1 items-center h-4">
                {[0, 150, 300].map(d => (
                  <span key={d} className="w-2 h-2 bg-teal-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${d}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="px-4 py-3 bg-white border-t border-slate-100">
        <div className="flex gap-2 items-center">
          <input ref={inputRef} type="text" value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask me anything about NexCRM..."
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
        <p className="text-[10px] text-slate-300 text-center mt-1.5">Powered by Grok AI · NexCRM Sales Assistant</p>
      </form>
    </div>
  );
}