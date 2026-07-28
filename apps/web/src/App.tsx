import React, { useState } from 'react';

interface StatCardProps {
  title: string;
  value: string;
  change: string;
  isPositive: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, isPositive }) => (
  <div className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-teal-500/40 transition-all duration-300">
    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</p>
    <div className="mt-3 flex items-baseline justify-between">
      <h3 className="text-2xl font-extrabold text-white tracking-tight">{value}</h3>
      <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${isPositive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
        {change}
      </span>
    </div>
  </div>
);

export function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'parties' | 'inventory' | 'sales' | 'accounting'>('dashboard');

  return (
    <div className="flex h-screen bg-[#070a11] text-slate-100 font-sans overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900/80 backdrop-blur-xl border-r border-slate-800 flex flex-col justify-between p-4">
        <div>
          {/* Logo Header */}
          <div className="flex items-center gap-3 px-3 py-4 border-b border-slate-800/80 mb-6">
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-teal-500 to-blue-600 flex items-center justify-center font-black text-xl shadow-lg shadow-teal-500/20 text-white">
              A
            </div>
            <div>
              <h1 className="font-extrabold text-lg tracking-wider text-white leading-tight">ASTHA ERP</h1>
              <p className="text-[10px] text-teal-400 font-mono tracking-widest uppercase">Builders & Hardware</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: '📊' },
              { id: 'parties', label: 'Parties & Ledgers', icon: '👥' },
              { id: 'inventory', label: 'Inventory & Stock', icon: '📦' },
              { id: 'sales', label: 'Sales & GST Billing', icon: '🛒' },
              { id: 'accounting', label: 'Double Entry Accounting', icon: '⚖️' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as any)}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  activeTab === item.id
                    ? 'bg-teal-500/10 text-teal-300 border border-teal-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Footer info */}
        <div className="px-3 py-3 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs text-slate-400">
          <div className="flex items-center justify-between mb-1">
            <span className="font-mono text-[11px] text-teal-400">● Offline Sync Active</span>
            <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">v1.0.0</span>
          </div>
          <p className="text-[11px] text-slate-500">Local Node: POS-DESKTOP-01</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto bg-gradient-to-b from-[#090d16] to-[#05070c]">
        {/* Top bar */}
        <header className="h-16 border-b border-slate-800/80 px-8 flex items-center justify-between bg-slate-900/40 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <h2 className="text-lg font-bold text-white tracking-wide uppercase">
              {activeTab} Overview
            </h2>
            <div className="flex items-center gap-2 text-xs font-mono bg-slate-800/60 px-3 py-1 rounded-full border border-slate-700/50 text-slate-300">
              <kbd className="bg-slate-700 px-1.5 py-0.5 rounded text-white">F1</kbd> Search Item
              <kbd className="bg-slate-700 px-1.5 py-0.5 rounded text-white ml-2">F5</kbd> POS Billing
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button className="px-3.5 py-1.5 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-teal-600/20 transition-all flex items-center gap-2">
              <span>+ New Sales Invoice</span>
            </button>
            <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-xs text-teal-400">
              AD
            </div>
          </div>
        </header>

        {/* Content Body */}
        <div className="p-8 space-y-8">
          {activeTab === 'dashboard' && (
            <>
              {/* Stat Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
                <StatCard title="Today's Sales" value="₹ 1,48,500.00" change="+12.4%" isPositive={true} />
                <StatCard title="Today's Collections" value="₹ 92,000.00" change="+8.1%" isPositive={true} />
                <StatCard title="Outstanding Receivables" value="₹ 4,35,000.00" change="-2.5%" isPositive={true} />
                <StatCard title="Low Stock Alerts" value="8 Items" change="Action Needed" isPositive={false} />
              </div>

              {/* Quick Table Section */}
              <div className="glass-panel rounded-xl p-6 border border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-bold text-white">Recent Counter Transactions</h3>
                  <button className="text-xs text-teal-400 hover:text-teal-300 font-medium">View All →</button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-slate-300">
                    <thead className="bg-slate-900/80 text-slate-400 font-semibold uppercase tracking-wider text-[11px] border-b border-slate-800">
                      <tr>
                        <th className="py-3 px-4">Invoice No</th>
                        <th className="py-3 px-4">Party Name</th>
                        <th className="py-3 px-4">Items</th>
                        <th className="py-3 px-4">Total Amount</th>
                        <th className="py-3 px-4">Payment</th>
                        <th className="py-3 px-4">Sync Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      <tr className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-medium text-teal-300">AS-26-0042</td>
                        <td className="py-3.5 px-4 font-semibold text-white">Astha Builders Ltd</td>
                        <td className="py-3.5 px-4">Ultratech Cement (50 Bags)</td>
                        <td className="py-3.5 px-4 font-bold text-slate-100">₹ 21,500.00</td>
                        <td className="py-3.5 px-4"><span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">CASH</span></td>
                        <td className="py-3.5 px-4"><span className="text-teal-400 text-xs">Synced</span></td>
                      </tr>
                      <tr className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-3.5 px-4 font-mono font-medium text-teal-300">AS-26-0043</td>
                        <td className="py-3.5 px-4 font-semibold text-white">National Infrastructure</td>
                        <td className="py-3.5 px-4">TMT Steel Rods 12mm (2 Bundles)</td>
                        <td className="py-3.5 px-4 font-bold text-slate-100">₹ 38,400.00</td>
                        <td className="py-3.5 px-4"><span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">CREDIT</span></td>
                        <td className="py-3.5 px-4"><span className="text-slate-400 text-xs">Queued Offline</span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {activeTab === 'parties' && (
            <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">Party Directory & Outstanding Ledgers</h3>
                  <p className="text-xs text-slate-400">Unified master for Customers, Suppliers, and Dual Accounts.</p>
                </div>
                <button className="px-3.5 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-xs font-semibold shadow-md shadow-teal-600/20">
                  + Create New Party
                </button>
              </div>

              <div className="p-4 bg-slate-900/60 rounded-lg border border-slate-800 flex items-center justify-between text-xs text-slate-300">
                <span>Total Active Customers: <strong className="text-white">124</strong></span>
                <span>Total Active Suppliers: <strong className="text-white">42</strong></span>
                <span>Total Outstanding Balance: <strong className="text-teal-400">₹ 4,35,000.00</strong></span>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
