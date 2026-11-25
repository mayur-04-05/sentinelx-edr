import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL, useAuth, parseUTC } from '../context/AuthContext';
import { History, Search, User, Clock, RefreshCw } from 'lucide-react';

export default function AuditLogs() {
  const { role } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('ALL');

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API_URL}/audit`);
      setLogs(response.data);
    } catch (err) {
      console.error("Failed to load audit logs list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.username.toLowerCase().includes(search.toLowerCase()) ||
                          log.action.toLowerCase().includes(search.toLowerCase()) ||
                          (log.target && log.target.toLowerCase().includes(search.toLowerCase()));
                          
    const matchesAction = actionFilter === 'ALL' || log.action === actionFilter;
    
    return matchesSearch && matchesAction;
  });

  // Extract unique actions for the filter dropdown
  const uniqueActions = ['ALL', ...new Set(logs.map(l => l.action))];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-textPrimary tracking-wide">SOC Activity Audit Trails</h2>
        <p className="text-xs text-textSecondary font-medium">Verify system administration activity, logins, and EDR response action history.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between bg-bgCard border border-borderDark p-4 rounded-lg">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={16} />
          <input
            type="text"
            placeholder="Search by User, Action, or Target details..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-bgInput border border-borderDark rounded-lg py-2 pl-10 pr-4 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="bg-bgInput border border-borderDark rounded-lg px-3 py-2 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          >
            {uniqueActions.map(act => (
              <option key={act} value={act}>
                {act.replace('_', ' ')}
              </option>
            ))}
          </select>
          <button 
            onClick={fetchLogs}
            className="bg-bgInput hover:bg-borderDark border border-borderDark px-4 py-2 rounded-lg text-xs font-semibold text-textPrimary cursor-pointer"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div className="py-12 flex justify-center">
          <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
        </div>
      ) : filteredLogs.length === 0 ? (
        <div className="bg-bgCard border border-borderDark rounded-lg p-12 text-center text-textSecondary text-xs">
          No audit logs recorded.
        </div>
      ) : (
        <div className="bg-bgCard border border-borderDark rounded-lg overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-borderDark text-[10px] text-textSecondary font-bold uppercase tracking-wider bg-bgDark/30">
                <th className="p-4">Timestamp</th>
                <th className="p-4">Analyst / Actor</th>
                <th className="p-4">Activity Action</th>
                <th className="p-4">Target Resource Details</th>
                <th className="p-4">Result Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderDark/40 text-xs font-medium text-textPrimary">
              {filteredLogs.map(log => (
                <tr key={log.id} className="hover:bg-bgInput/20 transition duration-150">
                  <td className="p-4 text-textSecondary flex items-center gap-1.5 pt-6">
                    <Clock size={12} /> {parseUTC(log.timestamp).toLocaleString()}
                  </td>
                  <td className="p-4 flex items-center gap-2">
                    <div className="p-1 bg-bgDark rounded border border-borderDark/40 text-textSecondary">
                      <User size={12} />
                    </div>
                    <span className="font-semibold">{log.username}</span>
                  </td>
                  <td className="p-4">
                    <span className="font-mono text-accentBlue font-bold text-[10px]">
                      {log.action}
                    </span>
                  </td>
                  <td className="p-4 font-mono text-[10px] text-textSecondary max-w-[320px] truncate" title={log.target}>
                    {log.target || 'N/A'}
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold tracking-wider ${
                      log.result === 'SUCCESS' ? 'bg-accentGreen/15 text-accentGreen' :
                      log.result === 'FAILED' ? 'bg-accentRed/15 text-accentRed' :
                      'bg-textSecondary/15 text-textSecondary'
                    }`}>
                      {log.result}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
