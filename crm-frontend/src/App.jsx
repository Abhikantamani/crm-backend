import React, { useState } from 'react'
import CrmChatbot from './components/CrmChatbot'
import AdminDashboard from './components/AdminDashboard' 

function App() {
  const [currentView, setCurrentView] = useState('chatbot');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-100 via-teal-50 to-slate-200 font-sans">
      <nav className="bg-white shadow-sm p-4 flex justify-center gap-4 mb-8">
        <button 
          onClick={() => setCurrentView('chatbot')}
          className={`px-6 py-2 rounded-full font-medium transition ${
            currentView === 'chatbot' ? 'bg-teal-600 text-white shadow-md' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          Customer View (Chatbot)
        </button>
        <button 
          onClick={() => setCurrentView('admin')}
          className={`px-6 py-2 rounded-full font-medium transition ${
            currentView === 'admin' ? 'bg-slate-800 text-white shadow-md' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          Admin Console
        </button>
      </nav>

      <div className="flex justify-center p-4">
        {currentView === 'chatbot' ? (
          <div className="w-full max-w-md drop-shadow-2xl">
             <CrmChatbot />
          </div>
        ) : (
          <AdminDashboard />
        )}
      </div>
    </div>
  )
}

export default App