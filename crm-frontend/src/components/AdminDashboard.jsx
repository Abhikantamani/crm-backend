import { useState, useEffect } from 'react';

const BACKEND_URL = 'https://crm-backend-z5d9.onrender.com';

const AdminDashboard = () => {
  const [data, setData] = useState({
    leads: [],
    support_tickets: [],
    stats: { total_leads: 0, total_tickets: 0 }
  });
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin`, {
        headers: { 'Bypass-Tunnel-Reminder': 'true' },
        cache: 'no-store'
      });
      const result = await res.json();
      setData(result);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Failed to fetch admin data', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  return (
    <div className="w-full max-w-5xl mx-auto font-sans">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Admin Console</h1>
          {lastUpdated && (
            <p className="text-xs text-slate-400 mt-0.5">Last updated: {lastUpdated}</p>
          )}
        </div>
        <button
          onClick={fetchData}
          disabled={isLoading}
          className="flex items-center gap-2 bg-teal-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-teal-700 transition disabled:opacity-50 shadow-sm"
        >
          <svg className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Total Sales Leads</p>
          <p className="text-4xl font-bold text-teal-600">{data.stats.total_leads}</p>
        </div>
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Open Support Tickets</p>
          <p className="text-4xl font-bold text-red-500">{data.stats.total_tickets}</p>
        </div>
      </div>

      {/* Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Leads */}
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="bg-teal-600 px-5 py-3.5">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Recent Sales Leads</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs text-slate-400 uppercase tracking-wider">
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Email</th>
                </tr>
              </thead>
              <tbody>
                {data.leads.length === 0 ? (
                  <tr>
                    <td colSpan="2" className="px-5 py-10 text-center text-slate-400 text-xs">
                      No leads captured yet
                    </td>
                  </tr>
                ) : (
                  data.leads.map((lead, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition">
                      <td className="px-5 py-3.5 font-medium text-slate-800">{lead.name}</td>
                      <td className="px-5 py-3.5 text-slate-500">{lead.email}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Tickets */}
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="bg-slate-800 px-5 py-3.5">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider">Support Tickets</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs text-slate-400 uppercase tracking-wider">
                  <th className="px-5 py-3 font-medium">Ticket</th>
                  <th className="px-5 py-3 font-medium">Customer</th>
                  <th className="px-5 py-3 font-medium">Issue</th>
                </tr>
              </thead>
              <tbody>
                {data.support_tickets.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="px-5 py-10 text-center text-slate-400 text-xs">
                      No open tickets
                    </td>
                  </tr>
                ) : (
                  data.support_tickets.map((ticket, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition">
                      <td className="px-5 py-3.5">
                        <span className="font-mono text-xs font-bold text-teal-600 bg-teal-50 px-2 py-1 rounded-lg">
                          {ticket.ticket}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <p className="font-medium text-slate-800">{ticket.name}</p>
                        <p className="text-xs text-slate-400">{ticket.email}</p>
                      </td>
                      <td className="px-5 py-3.5 text-slate-500 max-w-[150px] truncate" title={ticket.issue}>
                        {ticket.issue}
                      </td>
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
