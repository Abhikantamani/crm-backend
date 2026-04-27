import { useState, useRef, useEffect } from 'react';

const BACKEND_URL  = 'https://crm-backend-z5d9.onrender.com';
const COMPANY_NAME = 'Future Invo Solutions';

const TRANSLATIONS = {
  en: {
    welcome: "👋 Hello! I'm your AI Sales Assistant for NexCRM by Future Invo Solutions.\n\nHow can I help you today? I can assist with pricing, demos, features, lead management, support, and anything about NexCRM.\n\nWhat would you like to know?",
    placeholder: "Ask me anything about NexCRM...",
    listening: t.listening,
    newChat: "New Chat",
    online: t.online,
    feedbackQ: t.feedbackQ,
    feedbackOptional: t.feedbackOptional,
    submitFeedback: t.submitFeedback,
    thankYouFeedback: t.thankYouFeedback,
    helpImprove: t.helpImprove
  },
  hi: {
    welcome: "👋 नमस्ते! मैं Future Invo Solutions के NexCRM के लिए आपका AI सेल्स असिस्टेंट हूँ।\n\nमैं आपकी कैसे मदद कर सकता हूँ? मैं मूल्य निर्धारण, डेमो, सुविधाएं, लीड प्रबंधन, समर्थन और NexCRM के बारे में कुछ भी करने में मदद कर सकता हूँ।\n\nआप क्या जानना चाहते हैं?",
    placeholder: "NexCRM के बारे में कुछ भी पूछें...",
    listening: "🎙️ सुन रहा हूँ... अब बोलें",
    newChat: "नई बातचीत",
    online: "ऑनलाइन · Groq AI द्वारा संचालित",
    feedbackQ: "आपका अनुभव कैसा रहा? 😊",
    feedbackOptional: "कोई टिप्पणी? (वैकल्पिक)",
    submitFeedback: "प्रतिक्रिया सबमिट करें",
    thankYouFeedback: "आपकी प्रतिक्रिया के लिए धन्यवाद! 🙏",
    helpImprove: "यह हमें NexCRM में सुधार करने में मदद करता है।"
  },
  te: {
    welcome: "👋 నమస్కారం! నేను Future Invo Solutions కి చెందిన NexCRM కోసం మీ AI విక్రయ సహాయకుడిని.\n\nనేను మీకు ఎలా సహాయం చేయగలను? నేను ధర నిర్ణయం, డెమో, లక్షణాలు, లీడ్ నిర్వహణ, సపోర్టు మరియు NexCRM గురించి ఏదైనా సహాయం చేయవచ్చు.\n\nమీరు ఏమి తెలుసుకోవాలనుకుంటున్నారు?",
    placeholder: "NexCRM గురించి ఏదైనా అడగండి...",
    listening: "🎙️ వింటున్నాను... ఇప్పుడు మాట్లాడండి",
    newChat: "కొత్త సంభాషణ",
    online: "ఆన్‌లైన్ · Groq AI ద్వారా",
    feedbackQ: "మీ అనుభవం ఎలా ఉంది? 😊",
    feedbackOptional: "ఏదైనా వ్యాఖ్యలు? (ఐచ్ఛికం)",
    submitFeedback: "ప్రతిక్రియ సమర్పించండి",
    thankYouFeedback: "మీ ప్రతిక్రియ కోసం ధన్యవాదాలు! 🙏",
    helpImprove: "ఇది NexCRM లో సుధారించటానికి సహాయం చేస్తుంది."
  },
  ta: {
    welcome: "👋 வணக்கம்! நான் Future Invo Solutions இன் NexCRM க்கான உங்கள் AI விற்பனை உதவியாளர்.\n\nநான் உங்களுக்கு எவ்வாறு உதவ முடியும்? நான் விலை நிர்ణயம், டெமோ, அம்சங்கள், லீட் மேலாண்மை, ஆதரவு மற்றும் NexCRM பற்றி எதுவும் உதவ முடியும்.\n\nநீங்கள் எதை அறிய விரும்புகிறீர்கள்?",
    placeholder: "NexCRM பற்றி எதுவும் கேளுங்கள்...",
    listening: "🎙️ கேட்டுக்கொண்டிருக்கிறேன்... இப்போது பேசுங்கள்",
    newChat: "புதிய உரையாடல்",
    online: "ஆன்லைன் · Groq AI ஆல் இயக்கப்படுகிறது",
    feedbackQ: "உங்கள் அனுபவம் எப்படி இருந்தது? 😊",
    feedbackOptional: "ஏதாவது கருத்துகள்? (விருப்பத்தேர்வு)",
    submitFeedback: "கருத்தை சமர்ப்பிக்கவும்",
    thankYouFeedback: "உங்கள் கருத்துக்கு நன்றி! 🙏",
    helpImprove: "இது NexCRM ஐ மேம்படுத்த உதவுகிறது."
  }
};


const PRODUCT_NAME = 'NexCRM';

function generateSessionId() {
  return 'session_' + Math.random().toString(36).substring(2, 9);
}

// ── Pricing Card ──────────────────────────────────────────────
const PricingCard = () => (
  <div className="mt-3 w-full max-w-sm rounded-2xl border border-teal-100 bg-white shadow-lg overflow-hidden">
    <div className="bg-gradient-to-r from-teal-600 to-teal-500 px-4 py-2.5">
      <p className="text-xs font-bold text-white uppercase tracking-widest">{PRODUCT_NAME} Plans</p>
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
      const hasContent = line.split('|').filter(c => c.trim() !== '' && !/^[-: ]+$/.test(c)).some(c => c.trim().length > 0);
      if (!hasContent) return null;
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

  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} mb-4`}>
      {isBot && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-teal-700 flex items-center justify-center mr-2.5 mt-1 flex-shrink-0 shadow-md">
          <span className="text-white text-xs font-bold">F</span>
        </div>
      )}
      <div className="max-w-[82%]">
        <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isBot
            ? 'bg-white border border-slate-200 text-slate-800 rounded-tl-none shadow-sm'
            : 'bg-gradient-to-br from-teal-600 to-teal-700 text-white rounded-tr-none shadow-md'
        }`}>
          {isBot ? renderMarkdown(msg.text) : msg.text}
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
  'What are your pricing plans?',
  'I want a demo',
  'What is the next best action?',
  'I found a bug',
];

// ── Mic Icon ──────────────────────────────────────────────────
const MicIcon = ({ active }) => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3a3 3 0 013 3v6a3 3 0 11-6 0V6a3 3 0 013-3z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-14 0" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v3M8 21h8" />
  </svg>
);

// ── Main Component ────────────────────────────────────────────
export default function CrmChatbot() {
  const sessionId      = useRef(generateSessionId());
  const bottomRef      = useRef(null);
  const inputRef       = useRef(null);
  const recognitionRef = useRef(null);
  const transcriptRef  = useRef('');


  const [messages, setMessages] = useState([{ sender: 'bot', text: t.welcome }]);
  const [input,        setInput]        = useState('');
  const [isLoading,    setIsLoading]    = useState(false);
  const [convState,    setConvState]    = useState('IDLE');
  const [convData,     setConvData]     = useState({});
  const [convHistory,  setConvHistory]  = useState([]);
  const [isListening,  setIsListening]  = useState(false);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [speechError,  setSpeechError]  = useState('');
  const [showFeedback,  setShowFeedback]  = useState(false);
  const [fbRating,      setFbRating]      = useState(0);
  const [fbComment,     setFbComment]     = useState('');
  const [fbSubmitted,   setFbSubmitted]   = useState(false);
  const [language, setLanguage] = useState('en');  // Language state
  const t = TRANSLATIONS[language];  // Translation shortcut

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Setup Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = language === 'hi' ? 'hi-IN' : language === 'te' ? 'te-IN' : language === 'ta' ? 'ta-IN' : 'en-IN';
    recognition.continuous       = false;
    recognition.interimResults   = true;

    recognition.onstart = () => {
      transcriptRef.current = '';
      setSpeechError('');
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(r => r[0]?.transcript || '')
        .join(' ')
        .trim();
      transcriptRef.current = transcript;
      setInput(transcript);
    };

    recognition.onerror = (event) => {
      const errors = {
        'not-allowed':    'Microphone access blocked. Please allow permission and try again.',
        'no-speech':      'No speech detected. Please try again.',
        'audio-capture':  'No microphone found on this device.',
      };
      setSpeechError(errors[event.error] || 'Voice input failed. Please try again.');
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (transcriptRef.current) inputRef.current?.focus();
    };

    recognitionRef.current = recognition;
    setSpeechSupported(true);

    return () => recognition.stop();
  }, []);

  const toggleVoice = () => {
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

  const send = async (text) => {
    const trimmed = text.trim();
    if (!trimmed || isLoading) return;

    setMessages(prev => [...prev, { sender: 'user', text: trimmed }]);
    setInput('');
    setSpeechError('');
    setIsLoading(true);

    const updatedHistory = [...convHistory, { role: 'user', content: trimmed }];

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          user_id: sessionId.current,
          state:   convState,
          data:    convData,
          history: updatedHistory,
          language: language,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const result  = await res.json();
      const botReply = result.response || 'I am having trouble responding. Please try again.';

      setConvState(result.state || 'IDLE');
      setConvData(result.data   || {});
      setConvHistory([...updatedHistory, { role: 'assistant', content: botReply }]);
      setMessages(prev => [...prev, { sender: 'bot', text: botReply }]);

      // Show feedback form when conversation winds down
      const closeWords = ['thank you', 'thanks', 'goodbye', 'bye', 'ok bye', 'no thank', 'thats all', 'that's all', 'great', 'done', 'see you'];
      if (closeWords.some(w => trimmed.toLowerCase().includes(w)) && messages.length >= 6) {
        setTimeout(() => setShowFeedback(true), 1200);
      }

    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: '⚠️ I\'m having trouble connecting right now. Please try again in a moment.\n\n*(If this is the first message, Render may be waking up — wait 30 seconds and retry)*'
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
    setInput('');
    setSpeechError('');
    setIsListening(false);
    recognitionRef.current?.stop();
    setShowFeedback(false); setFbRating(0); setFbComment(""); setFbSubmitted(false); setMessages([{ sender: "bot", text: t.welcome }]);
  };

  const submitFeedback = async () => {
    if (!fbRating) return;
    try {
      await fetch(`${BACKEND_URL}/api/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: sessionId.current,
          rating: fbRating,
          comment: fbComment,
          name: convData.name || '',
          email: convData.email || '',
        }),
      });
    } catch (e) { console.error(e); }
    setFbSubmitted(true);
  };

  const showChips = messages.length <= 2 && !isLoading;

  return (
    <div className="flex flex-col h-[680px] bg-slate-50 rounded-3xl overflow-hidden shadow-2xl border border-slate-200">

      {/* ── Header ── */}
      <div className="bg-gradient-to-r from-teal-700 to-teal-500 px-5 py-3 shadow-md">
        {/* Company name bar */}
        <div className="flex items-center justify-between mb-2">
          <a href="https://futureinvo.com" target="_blank" rel="noreferrer"
            className="text-xs font-semibold text-teal-100 tracking-widest uppercase hover:text-white transition">
            🌐 {COMPANY_NAME}
          </a>
          <div className="flex items-center gap-1.5">
            {/* Language Toggle */}
            <div className="flex gap-0.5 bg-white/10 rounded-full p-0.5">
              {['en', 'hi', 'te', 'ta'].map(lang => {
                const labels = { en: '🇬🇧 EN', hi: '🇮🇳 HI', te: '🇮🇳 TE', ta: '🇮🇳 TA' };
                return (
                  <button key={lang} onClick={() => setLanguage(lang)}
                    className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full transition ${
                      language === lang
                        ? 'bg-white text-teal-700'
                        : 'text-teal-100 hover:text-white'
                    }`}>
                    {labels[lang]}
                  </button>
                );
              })}
            </div>
            <button onClick={handleReset}
              className="text-xs text-teal-200 hover:text-white transition px-2 py-1 rounded-full hover:bg-white/10 font-medium">
              {t.newChat}
            </button>
          </div>
        </div>
        {/* Bot identity row */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-white/20 border-2 border-white/40 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">F</span>
          </div>
          <div>
            <p className="text-sm font-bold text-white">{PRODUCT_NAME} Sales Assistant</p>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-green-300 rounded-full animate-pulse" />
              <p className="text-xs text-teal-100 font-medium">Online · Powered by Groq AI</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Messages ── */}
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
              <span className="text-white text-xs font-bold">F</span>
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


        {/* ── End-of-conversation Feedback ── */}
        {showFeedback && (
          <div className="mx-2 mb-4 rounded-2xl border border-teal-100 bg-white shadow-sm overflow-hidden">
            {!fbSubmitted ? (
              <div className="px-4 py-3">
                <p className="text-xs font-semibold text-slate-600 mb-2">How was your experience? 😊</p>
                <div className="flex gap-1 mb-2">
                  {[1,2,3,4,5].map(star => (
                    <button key={star} onClick={() => setFbRating(star)}
                      className={`text-lg transition ${fbRating >= star ? 'text-yellow-400' : 'text-slate-200 hover:text-yellow-300'}`}>
                      ★
                    </button>
                  ))}
                </div>
                <textarea value={fbComment} onChange={e => setFbComment(e.target.value)}
                  placeholder=t.feedbackOptional
                  rows={2}
                  className="w-full text-xs px-3 py-2 bg-slate-50 rounded-xl border border-slate-100 focus:outline-none focus:ring-1 focus:ring-teal-400 resize-none text-slate-700 placeholder-slate-300 mb-2" />
                <button onClick={submitFeedback} disabled={!fbRating}
                  className="w-full bg-teal-600 text-white text-xs font-semibold py-1.5 rounded-xl hover:bg-teal-700 transition disabled:opacity-40">
                  Submit Feedback
                </button>
              </div>
            ) : (
              <div className="px-4 py-3 text-center">
                <p className="text-sm font-semibold text-teal-600">Thank you for your feedback! 🙏</p>
                <p className="text-xs text-slate-400 mt-0.5">It helps us improve NexCRM.</p>
              </div>
            )}
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* ── Input ── */}
      <form onSubmit={handleSubmit} className="px-4 py-3 bg-white border-t border-slate-100">
        <div className="flex gap-2 items-center">
          <input ref={inputRef} type="text" value={input}
            onChange={e => setInput(e.target.value)}
            placeholder={isListening ? t.listening : t.placeholder.split('...')[0]} ${PRODUCT_NAME}...`}
            disabled={isLoading}
            className={`flex-1 px-4 py-2.5 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-teal-400 transition disabled:opacity-50 text-slate-800 placeholder-slate-400 ${
              isListening ? 'bg-red-50 border border-red-200 focus:bg-red-50' : 'bg-slate-100 focus:bg-white'
            }`}
          />

          {/* Voice button */}
          {speechSupported && (
            <button type="button" onClick={toggleVoice} disabled={isLoading}
              aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
              className={`w-10 h-10 flex-shrink-0 rounded-full flex items-center justify-center transition border ${
                isListening
                  ? 'bg-red-500 border-red-500 text-white animate-pulse'
                  : 'bg-white border-teal-200 text-teal-600 hover:bg-teal-50'
              } disabled:opacity-40`}>
              <MicIcon active={isListening} />
            </button>
          )}

          {/* Send button */}
          <button type="submit" disabled={isLoading || !input.trim()}
            className="w-10 h-10 bg-gradient-to-br from-teal-500 to-teal-700 rounded-full flex items-center justify-center hover:opacity-90 transition disabled:opacity-40 shadow-md flex-shrink-0">
            <svg className="w-4 h-4 text-white translate-x-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
            </svg>
          </button>
        </div>

        {/* Status bar */}
        <div className="mt-1.5 min-h-[14px] text-center text-[10px] text-slate-400">
          {speechError
            ? <span className="text-red-500">{speechError}</span>
            : isListening
              ? <span className="text-red-500 font-medium">🔴 Listening — speak now, your words will appear above</span>
              : speechSupported
                ? `Powered by Groq AI · ${COMPANY_NAME}`
                : `${PRODUCT_NAME} Sales Assistant · ${COMPANY_NAME}`
          }
        </div>
      </form>
    </div>
  );
}