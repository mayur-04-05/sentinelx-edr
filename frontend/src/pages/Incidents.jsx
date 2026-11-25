import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL, parseUTC } from '../context/AuthContext';
import { FileWarning, Search, Clock, ShieldAlert } from 'lucide-react';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchIncidents = async () => {
    try {
      const response = await axios.get(`${API_URL}/incidents`);
      setIncidents(response.data);
    } catch (err) {
      console.error("Failed to load incidents list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredIncidents = incidents.filter(inc => {
    const matchesSearch = inc.title.toLowerCase().includes(search.toLowerCase()) ||
                          inc.agent_id.toLowerCase().includes(search.toLowerCase());
                          
    const matchesStatus = statusFilter === 'ALL' || inc.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-textPrimary tracking-wide">Incident Detections</h2>
        <p className="text-xs text-textSecondary font-medium">Investigate aggregated and correlated behavioral alerts affecting endpoints.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between bg-bgCard border border-borderDark p-4 rounded-lg">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={16} />
          <input
            type="text"
            placeholder="Search by Title or Agent ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-bgInput border border-borderDark rounded-lg py-2 pl-10 pr-4 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-bgInput border border-borderDark rounded-lg px-3 py-2 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          >
            <option value="ALL">All Statuses</option>
            <option value="NEW">New</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="CONTAINED">Contained</option>
            <option value="RESOLVED">Resolved</option>
            <option value="FALSE_POSITIVE">False Positive</option>
          </select>
          <button 
            onClick={fetchIncidents}
            className="bg-bgInput hover:bg-borderDark border border-borderDark px-4 py-2 rounded-lg text-xs font-semibold text-textPrimary cursor-pointer"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Incidents Table list */}
      {loading ? (
        <div className="py-12 flex justify-center">
          <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
        </div>
      ) : filteredIncidents.length === 0 ? (
        <div className="bg-bgCard border border-borderDark rounded-lg p-12 text-center text-textSecondary text-xs">
          No security incidents recorded.
        </div>
      ) : (
        <div className="bg-bgCard border border-borderDark rounded-lg overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-borderDark text-[10px] text-textSecondary font-bold uppercase tracking-wider bg-bgDark/30">
                <th className="p-4">Incident ID</th>
                <th className="p-4">Incident Name</th>
                <th className="p-4">Affected Agent</th>
                <th className="p-4">Severity</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4">Last Activity</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderDark/40 text-xs font-medium text-textPrimary">
              {filteredIncidents.map(inc => (
                <tr key={inc.id} className="hover:bg-bgInput/20 transition duration-150">
                  <td className="p-4 text-accentBlue font-bold">INC-{inc.id}</td>
                  <td className="p-4 font-semibold text-textPrimary max-w-[280px] truncate">{inc.title}</td>
                  <td className="p-4">
                    <Link to={`/endpoints/${inc.agent_id}`} className="font-mono text-[10px] text-accentBlue hover:underline break-all">
                      {inc.agent_id.substring(0, 18)}...
                    </Link>
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                      inc.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-500' :
                      inc.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-500' :
                      inc.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {inc.severity}
                    </span>
                  </td>
                  <td className="p-4 font-bold text-textPrimary">{inc.risk_score}/100</td>
                  <td className="p-4 text-textSecondary flex items-center gap-1.5 pt-6">
                    <Clock size={12} /> {parseUTC(inc.last_seen).toLocaleString()}
                  </td>
                  <td className="p-4">
                    <span className={`px-2 py-0.5 rounded-[3px] text-[10px] uppercase font-bold tracking-wider ${
                      inc.status === 'NEW' ? 'bg-accentRed/10 text-accentRed border border-accentRed/20' :
                      inc.status === 'INVESTIGATING' ? 'bg-accentYellow/10 text-accentYellow border border-accentYellow/20' :
                      inc.status === 'CONTAINED' ? 'bg-accentBlue/10 text-accentBlue border border-accentBlue/20' :
                      inc.status === 'RESOLVED' ? 'bg-accentGreen/10 text-accentGreen border border-accentGreen/20' :
                      'bg-textSecondary/15 text-textSecondary'
                    }`}>
                      {inc.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <Link
                      to={`/incidents/${inc.id}`}
                      className="bg-accentBlue hover:bg-blue-600 text-white px-3 py-1.5 rounded text-xs font-semibold shadow transition duration-150 cursor-pointer"
                    >
                      Investigate
                    </Link>
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
