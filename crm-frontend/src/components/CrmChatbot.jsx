import { useEffect, useRef, useState } from 'react';

const BACKEND_URL = 'https://crm-backend-z5d9.onrender.com';
const COMPANY_NAME = 'Future Invo Solutions';
const ASSISTANT_NAME = 'CRM Bot';

function generateSessionId() {
  return 'session_' + Math.random().toString(36).substring(2, 9);
}

const PricingCard = () => (
  <div className="mt-3 w-full max-w-sm overflow-hidden rounded-2xl border border-teal-100 bg-white shadow-lg">
    <div className="bg-gradient-to-r from-teal-600 to-teal-500 px-4 py-2.5">
      <p className="text-xs font-bold uppercase tracking-widest text-white">Product Overview</p>
    </div>
    <div className="px-4 py-3 text-sm text-slate-700">
      For product details, a walkthrough, or a custom quote, ask for a demo and our team will assist you.
    </div>
    <div className="bg-slate-50 px-4 py-2 text-center text-xs text-slate-400">
      Demos, onboarding help, and support guidance are available here
    </div>
  </div>
);

function renderMarkdown(text) {
  return text
    .split('\n')
    .map((line, i, arr) => {
      const isLast = i === arr.length - 1;

      if (line.startsWith('|') && line.endsWith('|')) {
        const cells = line.split('|').filter((cell) => cell.trim() !== '');
        if (cells.every((cell) => /^[-: ]+$/.test(cell))) return null;
        return (
          <div key={i} className="flex rounded bg-slate-50 text-xs border-b border-slate-100 last:border-0">
            {cells.map((cell, j) => (
              <span key={j} className="flex-1 px-2 py-1.5 text-slate-700">
                {cell.trim()}
              </span>
            ))}
          </div>
        );
      }

      const parts = line.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
      const rendered = parts.map((part, j) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return (
            <strong key={j} className="font-semibold">
              {part.slice(2, -2)}
            </strong>
          );
        }

        if (part.startsWith('`') && part.endsWith('`')) {
          return (
            <code key={j} className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-xs text-teal-700">
              {part.slice(1, -1)}
            </code>
          );
        }

        if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={j}>{part.slice(1, -1)}</em>;
        }

        return <span key={j}>{part}</span>;
      });

      return (
        <span key={i}>
          {rendered}
          {!isLast ? '\n' : ''}
        </span>
      );
    })
    .filter(Boolean);
}

function MessageBubble({ msg }) {
  const isBot = msg.sender === 'bot';
  const hasPricing = isBot && /pricing|quote|plan|demo/i.test(msg.text);

  return (
    <div className={`mb-4 flex ${isBot ? 'justify-start' : 'justify-end'}`}>
      {isBot && (
        <div className="mt-1 mr-2.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-teal-700 shadow-md">
          <span className="text-xs font-bold text-white">F</span>
        </div>
      )}
      <div className="max-w-[82%]">
        <div
          className={`whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
            isBot
              ? 'rounded-tl-none border border-slate-200 bg-white text-slate-800 shadow-sm'
              : 'rounded-tr-none bg-gradient-to-br from-teal-600 to-teal-700 text-white shadow-md'
          }`}
        >
          {isBot ? renderMarkdown(msg.text) : msg.text}
        </div>
        {hasPricing && <PricingCard />}
        <p className={`mt-1 text-[10px] text-slate-400 ${isBot ? 'ml-1' : 'text-right'}`}>
          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      </div>
    </div>
  );
}

const CHIPS = [
  'Show your features',
  'I want a demo',
  'Create a support ticket',
  'How do you handle leads?',
];

export default function CrmChatbot() {
  const sessionId = useRef(generateSessionId());
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const transcriptRef = useRef('');

  const WELCOME = 'Hello! I am your CRM bot from Future Invo Solutions.';

  const [messages, setMessages] = useState([{ sender: 'bot', text: WELCOME }]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [convState, setConvState] = useState('IDLE');
  const [convData, setConvData] = useState({});
  const [convHistory, setConvHistory] = useState([]);
  const [isSpeechSupported, setIsSpeechSupported] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState('');

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSpeechSupported(false);
      return undefined;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      transcriptRef.current = '';
      setSpeechError('');
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript || '')
        .join(' ')
        .trim();

      transcriptRef.current = transcript;
      setInput(transcript);
    };

    recognition.onerror = (event) => {
      const errorMap = {
        'not-allowed': 'Microphone access was blocked. Please allow microphone permission and try again.',
        'no-speech': 'No speech was detected. Please try again.',
        'audio-capture': 'No microphone was found on this device.',
      };
      setSpeechError(errorMap[event.error] || 'Voice input could not start. Please try again.');
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (transcriptRef.current) {
        inputRef.current?.focus();
      }
    };

    recognitionRef.current = recognition;
    setIsSpeechSupported(true);

    return () => {
      recognition.stop();
    };
  }, []);

  const send = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    setMessages((prev) => [...prev, { sender: 'user', text: trimmed }]);
    setInput('');
    setSpeechError('');
    setIsLoading(true);

    const updatedHistory = [...convHistory, { role: 'user', content: trimmed }];

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          user_id: sessionId.current,
          state: convState,
          data: convData,
          history: updatedHistory,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result = await res.json();
      const botReply = result.response || 'I am having trouble responding right now. Please try again.';

      setConvState(result.state || 'IDLE');
      setConvData(result.data || {});
      setConvHistory([...updatedHistory, { role: 'assistant', content: botReply }]);
      setMessages((prev) => [...prev, { sender: 'bot', text: botReply }]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'bot',
          text: 'I am having trouble connecting right now. Please try again in a moment.',
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    send(input);
  };

  const handleReset = () => {
    sessionId.current = generateSessionId();
    setConvState('IDLE');
    setConvData({});
    setConvHistory([]);
    setInput('');
    setSpeechError('');
    setIsListening(false);
    recognitionRef.current?.stop();
    setMessages([{ sender: 'bot', text: WELCOME }]);
  };

  const toggleVoiceInput = () => {
    if (!recognitionRef.current || isLoading) return;

    if (isListening) {
      recognitionRef.current.stop();
      return;
    }

    transcriptRef.current = '';
    setInput('');
    setSpeechError('');
    recognitionRef.current.start();
  };

  const showChips = messages.length <= 2 && !isLoading;

  return (
    <div className="flex h-[680px] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-slate-50 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-100 bg-white px-5 py-3.5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-teal-700 shadow-md">
            <span className="font-bold text-white">F</span>
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">{ASSISTANT_NAME}</p>
            <div className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-green-500" />
              <p className="text-xs font-medium text-green-600">Online now</p>
            </div>
          </div>
        </div>
        <button
          onClick={handleReset}
          className="rounded-full px-3 py-1.5 text-xs font-medium text-slate-400 transition hover:bg-teal-50 hover:text-teal-600"
        >
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pt-4 pb-2">
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {showChips && (
          <div className="mb-3 ml-10 flex flex-wrap gap-2">
            {CHIPS.map((chip) => (
              <button
                key={chip}
                onClick={() => send(chip)}
                className="rounded-full border border-teal-200 bg-white px-3 py-1.5 text-xs font-medium text-teal-700 shadow-sm transition hover:border-teal-400 hover:bg-teal-50"
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        {isLoading && (
          <div className="mb-4 flex justify-start">
            <div className="mt-1 mr-2.5 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-teal-700">
              <span className="text-xs font-bold text-white">F</span>
            </div>
            <div className="rounded-2xl rounded-tl-none border border-slate-200 bg-white px-4 py-3 shadow-sm">
              <div className="flex h-4 items-center gap-1">
                {[0, 150, 300].map((delay) => (
                  <span
                    key={delay}
                    className="h-2 w-2 animate-bounce rounded-full bg-teal-400"
                    style={{ animationDelay: `${delay}ms` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-slate-100 bg-white px-4 py-3">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 rounded-full bg-slate-100 px-4 py-2.5 text-sm text-slate-800 transition placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-teal-400 disabled:opacity-50"
          />

          {isSpeechSupported && (
            <button
              type="button"
              onClick={toggleVoiceInput}
              disabled={isLoading}
              aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
              title={isListening ? 'Stop voice input' : 'Start voice input'}
              className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border transition ${
                isListening
                  ? 'border-red-200 bg-red-50 text-red-600'
                  : 'border-teal-200 bg-white text-teal-700 hover:bg-teal-50'
              } disabled:opacity-40`}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3a3 3 0 013 3v6a3 3 0 11-6 0V6a3 3 0 013-3z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-14 0" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v3" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M8 21h8" />
              </svg>
            </button>
          )}

          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-teal-700 shadow-md transition hover:opacity-90 disabled:opacity-40"
          >
            <svg className="h-4 w-4 translate-x-0.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>

        <div className="mt-1.5 min-h-[16px] text-center text-[10px] text-slate-400">
          {speechError
            ? speechError
            : isListening
              ? 'Listening now. Speak and your words will appear in the input box.'
              : isSpeechSupported
                ? 'Use the microphone button if you prefer speaking instead of typing.'
                : `${ASSISTANT_NAME} is ready to help.`}
        </div>
      </form>
    </div>
  );
}
