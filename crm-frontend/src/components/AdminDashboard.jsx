import React, { useState, useEffect } from 'react';

const AdminDashboard = () => {
  const [data, setData] = useState({ leads: [], support_tickets: [], stats: { total_leads: 0, total_tickets: 0 } });
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // 🚨 REPLACE THIS URL WITH YOUR LOCALTUNNEL PORT 8000 URL
      const response = await fetch('http://127.0.0.1:8000/api/admin', {
        headers: {
            'Bypass-Tunnel-Reminder': 'true' // Bypasses Localtunnel security screen
        },
        cache: 'no-store' // Prevents browser caching
      });
      const result = await response.json();
      setData(result);
    } catch (error) {
      console.error("Failed to fetch admin data", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="w-full max-w-6xl mx-auto p-6 bg-slate-50 min-h-screen font-sans">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-slate-800">CRM Admin Console</h1>
        <button onClick={fetchData} className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition shadow-sm">
          ↻ Refresh Data
        </button>
      </div>

      <div className="grid grid-cols-2 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col items-center justify-center">
            <h3 className="text-slate-500 text-sm font-semibold uppercase tracking-wider">Total Sales Leads</h3>
            <span className="text-4xl font-bold text-teal-600 mt-2">{data.stats.total_leads}</span>
        </div>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 flex flex-col items-center justify-center">
            <h3 className="text-slate-500 text-sm font-semibold uppercase tracking-wider">Open Support Tickets</h3>
            <span className="text-4xl font-bold text-red-500 mt-2">{data.stats.total_tickets}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* LEADS TABLE */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="bg-teal-600 px-6 py-4">
            <h2 className="text-lg font-bold text-white">Recent Sales Leads</h2>
          </div>
          <div className="p-0 overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-sm border-b border-slate-200">
                  <th className="px-6 py-3 font-medium">Name</th>
                  <th className="px-6 py-3 font-medium">Email Address</th>
                </tr>
              </thead>
              <tbody>
                {data.leads.length === 0 ? (
                  <tr><td colSpan="2" className="px-6 py-8 text-center text-slate-400">No leads captured yet.</td></tr>
                ) : (
                  data.leads.map((lead, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-800">{lead.name}</td>
                      <td className="px-6 py-4 text-slate-600">{lead.email}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* TICKETS TABLE */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="bg-slate-800 px-6 py-4">
            <h2 className="text-lg font-bold text-white">Active Support Tickets</h2>
          </div>
          <div className="p-0 overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-500 text-sm border-b border-slate-200">
                  <th className="px-6 py-3 font-medium">Ticket ID</th>
                  <th className="px-6 py-3 font-medium">Customer</th>
                  <th className="px-6 py-3 font-medium">Reported Issue</th>
                </tr>
              </thead>
              <tbody>
                {data.support_tickets.length === 0 ? (
                  <tr><td colSpan="3" className="px-6 py-8 text-center text-slate-400">No open tickets.</td></tr>
                ) : (
                  data.support_tickets.map((ticket, idx) => (
                    <tr key={idx} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="px-6 py-4 font-mono text-sm font-bold text-blue-600">{ticket.ticket}</td>
                      <td className="px-6 py-4">
                        <div className="font-medium text-slate-800">{ticket.name}</div>
                        <div className="text-xs text-slate-500">{ticket.email}</div>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-600 max-w-xs truncate" title={ticket.issue}>{ticket.issue}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;