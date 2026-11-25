import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL, parseUTC } from '../context/AuthContext';
import { Laptop, Search, ShieldAlert, Wifi, WifiOff, Clock } from 'lucide-react';

export default function Endpoints() {
  const [agents, setAgents] = useState([]);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);

  const fetchEndpoints = async () => {
    try {
      const response = await axios.get(`${API_URL}/agents`);
      setAgents(response.data);
    } catch (err) {
      console.error("Failed to load agents list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEndpoints();
    const interval = setInterval(fetchEndpoints, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.hostname.toLowerCase().includes(search.toLowerCase()) || 
                          agent.id.toLowerCase().includes(search.toLowerCase()) ||
                          (agent.ip_address && agent.ip_address.includes(search));
                          
    const matchesStatus = statusFilter === 'ALL' || agent.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-textPrimary tracking-wide">Monitored Endpoints</h2>
        <p className="text-xs text-textSecondary font-medium">Verify system health, client versions, and endpoint risk profiles.</p>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between bg-bgCard border border-borderDark p-4 rounded-lg">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={16} />
          <input
            type="text"
            placeholder="Search by Hostname, IP address, or Agent ID..."
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
            <option value="ONLINE">Online Only</option>
            <option value="OFFLINE">Offline Only</option>
          </select>
          <button 
            onClick={fetchEndpoints}
            className="bg-bgInput hover:bg-borderDark border border-borderDark px-4 py-2 rounded-lg text-xs font-semibold text-textPrimary cursor-pointer"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Grid or Table list */}
      {loading ? (
        <div className="py-12 flex justify-center">
          <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="bg-bgCard border border-borderDark rounded-lg p-12 text-center text-textSecondary text-xs">
          No endpoints found matching search criteria.
        </div>
      ) : (
        <div className="bg-bgCard border border-borderDark rounded-lg overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-borderDark text-[10px] text-textSecondary font-bold uppercase tracking-wider bg-bgDark/30">
                <th className="p-4">Hostname</th>
                <th className="p-4">Agent ID</th>
                <th className="p-4">OS Version</th>
                <th className="p-4">IP Address</th>
                <th className="p-4">Risk Score</th>
                <th className="p-4">Last Check-in</th>
                <th className="p-4">Status</th>
                <th className="p-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-borderDark/40 text-xs font-medium text-textPrimary">
              {filteredAgents.map(agent => (
                <tr key={agent.id} className="hover:bg-bgInput/20 transition duration-150">
                  <td className="p-4 flex items-center gap-3">
                    <div className="p-2 bg-blue-500/10 border border-blue-500/20 rounded text-accentBlue">
                      <Laptop size={16} />
                    </div>
                    <span className="font-bold">{agent.hostname}</span>
                  </td>
                  <td className="p-4 font-mono text-[10px] text-textSecondary">{agent.id.substring(0, 18)}...</td>
                  <td className="p-4 text-textSecondary max-w-[150px] truncate">{agent.os}</td>
                  <td className="p-4 font-mono text-textSecondary">{agent.ip_address || "127.0.0.1"}</td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        agent.risk_score >= 76 ? 'bg-red-500/20 text-red-500' :
                        agent.risk_score >= 51 ? 'bg-orange-500/20 text-orange-500' :
                        agent.risk_score >= 26 ? 'bg-yellow-500/20 text-yellow-500' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {agent.risk_score}/100
                      </span>
                    </div>
                  </td>
                  <td className="p-4 text-textSecondary flex items-center gap-1.5 pt-6">
                    <Clock size={12} />
                    {parseUTC(agent.last_seen).toLocaleTimeString()}
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                      agent.status === 'ONLINE' ? 'bg-accentGreen/10 text-accentGreen' : 'bg-accentRed/10 text-accentRed'
                    }`}>
                      {agent.status === 'ONLINE' ? <Wifi size={10} /> : <WifiOff size={10} />}
                      {agent.status}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    <Link
                      to={`/endpoints/${agent.id}`}
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
