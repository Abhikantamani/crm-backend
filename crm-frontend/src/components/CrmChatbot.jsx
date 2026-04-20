import { useState } from 'react';

// --- The Minimalist Pricing Component ---
const MenuPricing = () => (
  <div className="flex flex-col gap-2 w-full max-w-sm mt-3 p-4 bg-white rounded-xl border border-gray-100 shadow-sm">
    <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Pricing List</h3>
    
    <div className="flex justify-between items-center py-2 border-b border-gray-50">
      <span className="text-sm text-gray-700">Initial Setup</span>
      <span className="text-sm font-medium text-gray-900">$100</span>
    </div>
    
    <div className="flex justify-between items-center py-2 border-b border-gray-50">
      <span className="text-sm text-gray-700">Basic Monthly</span>
      <span className="text-sm font-medium text-gray-900">$15 / mo</span>
    </div>
    
    <div className="flex justify-between items-center py-2">
      <span className="text-sm text-gray-700">Pro API Access</span>
      <span className="text-sm font-medium text-gray-900">$49 / mo</span>
    </div>
  </div>
);

// --- The Main Chatbot Component ---
export default function CrmChatbot() {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! I am your CRM assistant. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      // Your live Render backend URL
      const response = await fetch('https://crm-backend-z5d9.onrender.com/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Sending data as "text" to match the FastAPI backend perfectly
        body: JSON.stringify({ text: userMsg.text }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      setMessages((prev) => [
        ...prev,
        // Expecting the backend to return {"reply": "..."}
        { sender: 'bot', text: data.reply } 
      ]);
    } catch (error) {
      console.error("Fetch Error:", error);
      setMessages((prev) => [
        ...prev,
        { sender: 'bot', text: 'Sorry, I am having trouble connecting to the server. Please try again.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto bg-gray-50 font-sans">
      <div className="bg-white px-6 py-4 border-b border-gray-200 shadow-sm">
        <h1 className="text-xl font-semibold text-gray-800">CRM AI Assistant</h1>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.sender === 'user' 
                ? 'bg-blue-600 text-white rounded-br-none' 
                : 'bg-white border border-gray-200 text-gray-800 rounded-bl-none shadow-sm'
            }`}>
              
              {/* Trigger logic for the pricing UI */}
              {msg.sender === 'bot' && msg.text.includes('[SHOW_PRICING]') ? (
                <div>
                  <span className="whitespace-pre-wrap">
                    {msg.text.replace('[SHOW_PRICING]', '')}
                  </span>
                  <MenuPricing />
                </div>
              ) : (
                <span className="whitespace-pre-wrap">{msg.text}</span>
              )}

            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 text-gray-500 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm text-sm">
              Typing...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={sendMessage} className="p-4 bg-white border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about our pricing..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          />
          <button 
            type="submit" 
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white font-medium rounded-full hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}