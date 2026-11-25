import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL, parseUTC } from '../context/AuthContext';
import { AlertTriangle, Clock, Shield, Search } from 'lucide-react';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API_URL}/alerts`);
      setAlerts(response.data);
    } catch (err) {
      console.error("Failed to fetch alerts list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.title.toLowerCase().includes(search.toLowerCase()) ||
                          alert.agent_id.toLowerCase().includes(search.toLowerCase()) ||
                          alert.rule_name.toLowerCase().includes(search.toLowerCase());
                          
    const matchesSeverity = severityFilter === 'ALL' || alert.severity === severityFilter;
    
    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-textPrimary tracking-wide">Security Alerts</h2>
        <p className="text-xs text-textSecondary font-medium">Real-time alert telemetry triggered by behavioral detection rules.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between bg-bgCard border border-borderDark p-4 rounded-lg">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={16} />
          <input
            type="text"
            placeholder="Search by Title, Rule Name, or Agent ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-bgInput border border-borderDark rounded-lg py-2 pl-10 pr-4 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-bgInput border border-borderDark rounded-lg px-3 py-2 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
          <button 
            onClick={fetchAlerts}
            className="bg-bgInput hover:bg-borderDark border border-borderDark px-4 py-2 rounded-lg text-xs font-semibold text-textPrimary cursor-pointer"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Alert Feed List */}
      {loading ? (
        <div className="py-12 flex justify-center">
          <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
        </div>
      ) : filteredAlerts.length === 0 ? (
        <div className="bg-bgCard border border-borderDark rounded-lg p-12 text-center text-textSecondary text-xs">
          No security alerts generated yet.
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAlerts.map(alert => (
            <div key={alert.id} className="bg-bgCard border border-borderDark rounded-lg p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-md">
              <div className="flex items-start gap-4">
                <div className={`p-3 border rounded-lg mt-0.5 ${
                  alert.severity === 'CRITICAL' ? 'bg-red-500/10 border-red-500/30 text-red-500' :
                  alert.severity === 'HIGH' ? 'bg-orange-500/10 border-orange-500/30 text-orange-500' :
                  alert.severity === 'MEDIUM' ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500' :
                  'bg-blue-500/10 border-blue-500/30 text-blue-400'
                }`}>
                  <AlertTriangle size={20} />
                </div>
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`text-[9px] font-extrabold uppercase px-2 py-0.5 rounded ${
                      alert.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-500' :
                      alert.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-500' :
                      alert.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {alert.severity} (Score: {alert.risk_score})
                    </span>
                    {alert.mitre_technique && (
                      <span className="bg-blue-500/10 text-accentBlue border border-blue-500/20 text-[9px] font-mono px-2 py-0.5 rounded font-semibold uppercase">
                        MITRE: {alert.mitre_technique}
                      </span>
                    )}
                    <span className="text-[10px] text-textSecondary font-mono uppercase">Rule: {alert.rule_name}</span>
                  </div>
                  <h3 className="text-sm font-bold text-textPrimary">{alert.title}</h3>
                  <p className="text-xs text-textSecondary leading-relaxed">{alert.description}</p>
                  
                  {/* Evidence Display */}
                  <div className="bg-bgDark/40 border border-borderDark/30 p-2.5 rounded text-[10px] font-mono text-textSecondary max-w-xl overflow-x-auto mt-2 leading-tight">
                    <span className="text-accentBlue font-semibold uppercase block mb-1">Evidence Summary:</span>
                    {Object.entries(alert.evidence).map(([key, val]) => (
                      <div key={key}>
                        <strong className="text-textPrimary">{key}:</strong> {JSON.stringify(val)}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex flex-row md:flex-col items-center md:items-end justify-between md:justify-center gap-3 border-t border-borderDark/40 md:border-t-0 pt-3 md:pt-0">
                <div className="text-left md:text-right space-y-1">
                  <span className="text-[10px] text-textSecondary font-bold uppercase block">ENDPOINT UUID</span>
                  <Link to={`/endpoints/${alert.agent_id}`} className="text-xs font-mono font-semibold text-accentBlue hover:underline break-all">
                    {alert.agent_id.substring(0, 18)}...
                  </Link>
                  <span className="text-[10px] text-textSecondary flex items-center gap-1.5 md:justify-end mt-1.5 font-semibold">
                    <Clock size={12} /> {parseUTC(alert.timestamp).toLocaleString()}
                  </span>
                </div>
                
                {alert.incident_id ? (
                  <Link
                    to={`/incidents/${alert.incident_id}`}
                    className="bg-bgInput hover:bg-borderDark border border-borderDark text-accentBlue px-4 py-2 rounded text-xs font-bold transition duration-150 cursor-pointer shadow"
                  >
                    View Incident INC-{alert.incident_id}
                  </Link>
                ) : (
                  <span className="text-[10px] text-textSecondary font-semibold">No Incident Linked</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
