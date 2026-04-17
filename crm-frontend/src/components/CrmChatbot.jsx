import React, { useState, useRef, useEffect } from 'react';

const CrmChatbot = () => {
  const defaultWelcomeMessage = { role: 'assistant', content: 'Hi there! Welcome to our website. Are you looking for Sales (Pricing/Features) or do you need Customer Support?' };
  
  const [messages, setMessages] = useState([defaultWelcomeMessage]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  const [sessionId, setSessionId] = useState(`session_${Math.random().toString(36).substring(2, 9)}`);
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  useEffect(() => scrollToBottom(), [messages]);

  const handleVoiceInput = (e) => {
    e.preventDefault();
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (event) => setInput((prev) => (prev + " " + event.results[0][0].transcript).trim());
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognition.start();
  };

  const sendMessage = async (text) => {
    if (!text.trim()) return;

    const userMessage = { role: 'user', content: text };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // 🚨 REPLACE THIS URL WITH YOUR LOCALTUNNEL PORT 8000 URL
      const response = await fetch('https://crm-backend-z5d9.onrender.com/chat', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Bypass-Tunnel-Reminder': 'true' // Bypasses Localtunnel security screen
        },
        body: JSON.stringify({ message: text, user_id: sessionId }) 
      });

      if (!response.ok) throw new Error('Network error');
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Our servers are currently busy. Please try again later.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleEndChat = () => {
    if (window.confirm("Are you sure you want to end this chat and clear your history?")) {
      setMessages([defaultWelcomeMessage]); 
      setSessionId(`session_${Math.random().toString(36).substring(2, 9)}`); 
      setInput(''); 
    }
  };

  return (
    <div className="flex flex-col h-[600px] w-full max-w-md border border-gray-200 rounded-2xl shadow-2xl bg-white font-sans overflow-hidden">
      <div className="bg-teal-600 text-white p-4 flex justify-between items-center shadow-md z-10">
        <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center text-xl shadow-inner">💬</div>
            <div>
                <h3 className="font-bold text-lg leading-tight">Customer Support</h3>
                <span className="text-xs text-teal-100 flex items-center gap-1">
                    <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
                    Online & Ready to Help
                </span>
            </div>
        </div>
        <button onClick={handleEndChat} className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-teal-700 text-teal-100 hover:text-white transition-colors" title="End Chat">✕</button>
      </div>

      <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
        {messages.map((msg, idx) => (
          <div key={idx} className={`mb-4 flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`p-3 rounded-2xl max-w-[85%] whitespace-pre-wrap text-sm shadow-sm ${msg.role === 'user' ? 'bg-teal-600 text-white rounded-br-none' : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none'}`}>
              {msg.content}
            </div>
            {idx === 0 && messages.length === 1 && (
              <div className="flex flex-wrap gap-2 mt-3 ml-1">
                {["💰 What is the pricing?", "🛠️ I need technical support", "🚀 Can I get a demo?"].map((suggestion, sIdx) => (
                  <button key={sIdx} onClick={() => sendMessage(suggestion)} className="text-xs bg-teal-50 text-teal-700 border border-teal-200 px-3 py-1.5 rounded-full hover:bg-teal-600 hover:text-white transition-colors shadow-sm font-medium">
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
        {isLoading && <div className="text-left text-gray-400 text-xs animate-pulse ml-2">Agent is typing...</div>}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="p-3 bg-white border-t border-gray-100 flex gap-2 items-center">
        <button type="button" onClick={handleVoiceInput} disabled={isListening || isLoading} className={`p-2 rounded-full transition-all flex-shrink-0 ${isListening ? 'bg-red-100 text-red-600 animate-pulse' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'}`} title="Speak to us">
          {isListening ? '🎙️' : '🎤'}
        </button>
        <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder={isListening ? "Listening..." : "Type your message..."} className="flex-1 p-3 bg-gray-100 border-none rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-none text-sm" disabled={isLoading || isListening} />
        <button type="submit" disabled={isLoading || !input.trim()} className="bg-teal-600 text-white px-5 py-2.5 rounded-xl hover:bg-teal-700 disabled:bg-teal-300 transition-colors flex-shrink-0 font-medium text-sm shadow-md">Send</button>
      </form>
    </div>
  );
};

export default CrmChatbot;