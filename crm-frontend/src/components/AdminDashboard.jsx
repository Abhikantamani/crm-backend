import { useState, useEffect } from 'react';

const BACKEND_URL = 'https://crm-backend-z5d9.onrender.com';

const fmt = (n) => !n ? '₹0' : n >= 100000 ? `₹${(n / 100000).toFixed(1)}L` : `₹${n.toLocaleString('en-IN')}`;

const StatCard = ({ label, value, color, icon }) => (
  <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
    <div className="flex items-center justify-between mb-2">
      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{label}</p>
      <span className="text-xl">{icon}</span>
    </div>
    <p className={`text-3xl font-bold ${color}`}>{value}</p>
  </div>
);

const Badge = ({ children, color = 'blue' }) => {
  const map = {
    green:  'bg-green-100 text-green-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    blue:   'bg-blue-100 text-blue-700',
    red:    'bg-red-100 text-red-700',
    teal:   'bg-teal-100 text-teal-700',
  };
  return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${map[color]}`}>{children}</span>;
};

const EmptyRow = ({ cols, msg }) => (
  <tr><td colSpan={cols} className="px-5 py-10 text-center text-slate-400 text-xs">{msg}</td></tr>
);

export default function AdminDashboard() {
  const [data, setData] = useState({
    leads: [], support_tickets: [], deals: [],
    appointments: [], communication_log: [], activities: [],
    stats: { total_leads: 0, total_tickets: 0, total_deals: 0, pipeline_value: 0, total_comms: 0 }
  });
  const [isLoading,    setIsLoading]    = useState(true);
  const [tab,          setTab]          = useState('leads');
  const [lastUpdated,  setLastUpdated]  = useState(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const res    = await fetch(`${BACKEND_URL}/api/admin`, { cache: 'no-store' });
      const result = await res.json();
      setData(result);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Admin fetch failed', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const TABS = [
    { id: 'leads',    label: '📋 Leads'    },
    { id: 'deals',    label: '💼 Deals'    },
    { id: 'tickets',  label: '🎫 Tickets'  },
    { id: 'comms',    label: '💬 Comms'    },
    { id: 'activity', label: '⚡ Activity' },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto font-sans">

      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Admin Console</h1>
          <p className="text-xs text-slate-400 mt-0.5">
            {lastUpdated ? `Last updated: ${lastUpdated}` : 'Loading...'}
          </p>
        </div>
        <button onClick={fetchData} disabled={isLoading}
          className="flex items-center gap-2 bg-teal-600 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-teal-700 transition shadow-sm disabled:opacity-50">
          <svg className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Leads"    value={data.stats.total_leads}                      color="text-teal-600"    icon="📋" />
        <StatCard label="Active Deals"   value={data.stats.total_deals}                      color="text-blue-600"   icon="💼" />
        <StatCard label="Open Tickets"   value={data.stats.total_tickets}                    color="text-red-500"    icon="🎫" />
        <StatCard label="Pipeline Value" value={fmt(data.stats.pipeline_value)}              color="text-emerald-600" icon="💰" />
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="flex border-b border-slate-100 overflow-x-auto">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex-1 min-w-[80px] px-3 py-3 text-xs font-medium transition whitespace-nowrap ${
                tab === t.id
                  ? 'text-teal-600 border-b-2 border-teal-600 bg-teal-50'
                  : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
              }`}>
              {t.label}
            </button>
          ))}
        </div>

        {/* LEADS */}
        {tab === 'leads' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  <th className="px-5 py-3">Lead ID</th>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Email</th>
                  <th className="px-5 py-3">Company</th>
                  <th className="px-5 py-3">Score</th>
                  <th className="px-5 py-3">Stage</th>
                  <th className="px-5 py-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {data.leads.length === 0
                  ? <EmptyRow cols={7} msg="No leads yet — start a conversation in the chatbot!" />
                  : data.leads.map((l, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition">
                      <td className="px-5 py-3.5"><code className="text-xs text-teal-600 bg-teal-50 px-2 py-0.5 rounded">{l.lead_id}</code></td>
                      <td className="px-5 py-3.5 font-medium text-slate-800">{l.name}</td>
                      <td className="px-5 py-3.5 text-slate-500">{l.email || '—'}</td>
                      <td className="px-5 py-3.5 text-slate-500">{l.company || '—'}</td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <div className="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${l.lead_score >= 80 ? 'bg-green-500' : l.lead_score >= 60 ? 'bg-yellow-400' : 'bg-blue-400'}`}
                              style={{ width: `${l.lead_score}%` }} />
                          </div>
                          <span className="text-xs font-semibold text-slate-700">{l.lead_score}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5"><Badge color="blue">{l.stage}</Badge></td>
                      <td className="px-5 py-3.5 text-xs text-slate-400">{l.created}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {/* DEALS */}
        {tab === 'deals' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  <th className="px-5 py-3">Deal ID</th>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Company</th>
                  <th className="px-5 py-3">Value</th>
                  <th className="px-5 py-3">Stage</th>
                  <th className="px-5 py-3">Probability</th>
                  <th className="px-5 py-3">Created</th>
                </tr>
              </thead>
              <tbody>
                {data.deals.length === 0
                  ? <EmptyRow cols={7} msg="No deals yet" />
                  : data.deals.map((d, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition">
                      <td className="px-5 py-3.5"><code className="text-xs text-blue-600 bg-blue-50 px-2 py-0.5 rounded">{d.deal_id}</code></td>
                      <td className="px-5 py-3.5 font-medium text-slate-800">{d.name}</td>
                      <td className="px-5 py-3.5 text-slate-500">{d.company || '—'}</td>
                      <td className="px-5 py-3.5 font-semibold text-emerald-600">₹{d.value.toLocaleString('en-IN')}/mo</td>
                      <td className="px-5 py-3.5"><Badge color="yellow">{d.stage}</Badge></td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <div className="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div className="h-full bg-yellow-400 rounded-full" style={{ width: `${d.probability}%` }} />
                          </div>
                          <span className="text-xs font-semibold text-slate-600">{d.probability}%</span>
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-xs text-slate-400">{d.created}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {/* TICKETS */}
        {tab === 'tickets' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  <th className="px-5 py-3">Ticket ID</th>
                  <th className="px-5 py-3">Customer</th>
                  <th className="px-5 py-3">Issue</th>
                  <th className="px-5 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {data.support_tickets.length === 0
                  ? <EmptyRow cols={4} msg="No tickets yet" />
                  : data.support_tickets.map((t, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition">
                      <td className="px-5 py-3.5"><code className="text-xs text-red-600 bg-red-50 px-2 py-0.5 rounded">{t.ticket}</code></td>
                      <td className="px-5 py-3.5">
                        <p className="font-medium text-slate-800">{t.name}</p>
                        <p className="text-xs text-slate-400">{t.email}</p>
                      </td>
                      <td className="px-5 py-3.5 text-slate-600 max-w-xs truncate" title={t.issue}>{t.issue}</td>
                      <td className="px-5 py-3.5"><Badge color="yellow">{t.status}</Badge></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {/* COMMS */}
        {tab === 'comms' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  <th className="px-5 py-3">Time</th>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Channel</th>
                  <th className="px-5 py-3">Note</th>
                </tr>
              </thead>
              <tbody>
                {data.communication_log.length === 0
                  ? <EmptyRow cols={4} msg="No communications logged yet" />
                  : [...data.communication_log].reverse().map((c, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition">
                      <td className="px-5 py-3.5 text-xs text-slate-400 whitespace-nowrap">{c.time}</td>
                      <td className="px-5 py-3.5 font-medium text-slate-800">{c.name}</td>
                      <td className="px-5 py-3.5">
                        <Badge color={c.channel === 'WhatsApp' ? 'green' : c.channel === 'Email' ? 'blue' : c.channel === 'Automation' ? 'teal' : 'yellow'}>
                          {c.channel}
                        </Badge>
                      </td>
                      <td className="px-5 py-3.5 text-slate-600">{c.note}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}

        {/* ACTIVITY */}
        {tab === 'activity' && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead>
                <tr className="bg-slate-50 text-xs text-slate-400 uppercase tracking-wider border-b border-slate-100">
                  <th className="px-5 py-3">Time</th>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Action</th>
                </tr>
              </thead>
              <tbody>
                {(data.activities || []).length === 0
                  ? <EmptyRow cols={3} msg="No activity yet" />
                  : [...(data.activities || [])].reverse().map((a, i) => (
                    <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition">
                      <td className="px-5 py-3.5 text-xs text-slate-400 whitespace-nowrap">{a.time}</td>
                      <td className="px-5 py-3.5 font-medium text-slate-800">{a.name}</td>
                      <td className="px-5 py-3.5 text-slate-600">{a.action}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}