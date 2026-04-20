import { useState, useRef, useEffect } from 'react';

const BACKEND_URL = 'https://crm-backend-z5d9.onrender.com';

function generateSessionId() {
  return 'session_' + Math.random().toString(36).substring(2, 9);
}

// ── Pricing Card ──────────────────────────────────────────────
const MenuPricing = () => (
  <div className="mt-3 w-full max-w-xs rounded-2xl border border-teal-100 bg-white shadow-md overflow-hidden">
    <div className="bg-teal-600 px-4 py-2">
      <p className="text-xs font-bold text-white uppercase tracking-widest">Our Plans</p>
    </div>
    <div className="divide-y divide-slate-100">
      {[
        { label: 'Initial Setup',  price: '$100', note: 'one-time fee' },
        { label: 'Basic Monthly',  price: '$15',  note: 'per month' },
        { label: 'Pro API Access', price: '$49',  note: 'per month' },
      ].map(({ label, price, note }) => (
        <div key={label} className="flex items-center justify-between px-4 py-3">
          <span className="text-sm text-slate-600">{label}</span>
          <div className="text-right">
            <span className="text-sm font-bold text-slate-900">{price}</span>
            <span className="block text-xs text-slate-400">{note}</span>
          </div>
        </div>
      ))}
    </div>
  </div>
);

// ── Markdown-lite renderer ────────────────────────────────────
function renderText(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**'))
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith('`') && part.endsWith('`'))
      return <code key={i} className="bg-slate-100 text-teal-700 px-1 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
    return <span key={i}>{part}</span>;
  });
}

// ── Message Bubble ────────────────────────────────────────────
function MessageBubble({ msg }) {
  const isBot = msg.sender === 'bot';
  const hasPricing = isBot && msg.text.includes('[SHOW_PRICING]');
  const cleanText = msg.text.replace('[SHOW_PRICING]', '').trim();

  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} mb-3`}>
      {isBot && (
        <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center mr-2 mt-1 flex-shrink-0 shadow-sm">
          <span className="text-white text-xs font-bold">C</span>
        </div>
      )}
      <div className="max-w-[80%]">
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isBot
            ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-sm'
            : 'bg-teal-600 text-white rounded-tr-none shadow-md'
        }`}>
          {isBot ? renderText(cleanText) : cleanText}
        </div>
        {hasPricing && <MenuPricing />}
      </div>
    </div>
  );
}

// ── Main Chatbot Component ────────────────────────────────────
export default function CrmChatbot() {
  const sessionId = useRef(generateSessionId());
  const bottomRef = useRef(null);

  const WELCOME_MSG = "👋 Welcome to CRM Assistant! I can help you with:\n\n• 💰 **Pricing & Plans** — ask about our costs\n• 🎯 **Demo Request** — get a live walkthrough\n• 🐛 **Bug Reports** — log a support ticket\n• 🔍 **Ticket Status** — look up a TICK-### ID\n\nWhat can I help you with today?";

  const [messages,  setMessages]  = useState([{ sender: 'bot', text: WELCOME_MSG }]);
  const [input,     setInput]     = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // Client-side FSM state — travels with every request to the backend
  const [convState, setConvState] = useState('IDLE');
  const [convData,  setConvData]  = useState({});

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const sendMessage = async (e) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || isLoading) return;

    setMessages(prev => [...prev, { sender: 'user', text }]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: sessionId.current,
          state:   convState,
          data:    convData,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const result = await res.json();

      // Save the new FSM state returned by the backend
      setConvState(result.state || 'IDLE');
      setConvData(result.data   || {});

      setMessages(prev => [...prev, { sender: 'bot', text: result.response }]);

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: "⚠️ Sorry, I'm having trouble connecting to the server. Please try again in a moment."
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    sessionId.current = generateSessionId();
    setConvState('IDLE');
    setConvData({});
    setMessages([{ sender: 'bot', text: WELCOME_MSG }]);
  };

  return (
    <div className="flex flex-col h-[600px] bg-slate-50 rounded-3xl overflow-hidden shadow-2xl border border-slate-200">

      {/* Header */}
      <div className="bg-white px-5 py-4 border-b border-slate-100 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-teal-600 flex items-center justify-center shadow">
            <span className="text-white font-bold text-sm">C</span>
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">CRM Assistant</p>
            <p className="text-xs text-teal-500 font-medium">● Online</p>
          </div>
        </div>
        <button
          onClick={handleReset}
          className="text-xs text-slate-400 hover:text-slate-600 transition px-3 py-1 rounded-full hover:bg-slate-100"
        >
          New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {isLoading && (
          <div className="flex justify-start mb-3">
            <div className="w-7 h-7 rounded-full bg-teal-600 flex items-center justify-center mr-2 mt-1 flex-shrink-0">
              <span className="text-white text-xs font-bold">C</span>
            </div>
            <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 shadow-sm">
              <div className="flex gap-1 items-center h-4">
                <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={sendMessage} className="px-4 py-3 bg-white border-t border-slate-100">
        <div className="flex gap-2 items-center">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 text-sm bg-slate-100 rounded-full focus:outline-none focus:ring-2 focus:ring-teal-400 disabled:opacity-50 text-slate-800 placeholder-slate-400"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="w-10 h-10 bg-teal-600 rounded-full flex items-center justify-center hover:bg-teal-700 transition disabled:opacity-40 shadow-sm flex-shrink-0"
          >
            <svg className="w-4 h-4 text-white translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>
      </form>

    </div>
  );
}