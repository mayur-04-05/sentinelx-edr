import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth, API_URL, parseUTC } from '../context/AuthContext';
import { 
  Laptop, 
  AlertTriangle, 
  FileWarning, 
  Activity, 
  CheckCircle, 
  XCircle,
  Clock
} from 'lucide-react';

// Helper to build friendly display strings for raw events
const getEventSummary = (evt) => {
  const meta = evt.metadata_json;
  if (!meta) return 'No event details';
  
  switch (evt.event_type) {
    case 'PROCESS':
      const action = meta.action || 'SPAWN';
      return `${action === 'SPAWN' ? '🚀 Spawn' : '❌ Exit'} process: ${meta.name || 'unknown'} (PID: ${meta.pid})`;
    case 'NETWORK':
      return `🌐 Socket connection: ${meta.process_name || 'unknown'} (PID: ${meta.pid}) -> ${meta.remote_address}:${meta.remote_port}`;
    case 'FILE':
      return `📁 File FIM: ${meta.action || 'modified'} -> ${meta.path || 'unknown'}`;
    case 'AUTHENTICATION':
      return `🔑 Login logon: ${meta.status || 'unknown'} for user ${meta.username || 'unknown'}`;
    case 'STARTUP':
      return `⚙️ Startup persistence entry: ${meta.command || 'unknown'}`;
    default:
      return `${evt.event_type} event logged`;
  }
};

export default function Dashboard() {
  const { token } = useAuth();
  const [stats, setStats] = useState({
    endpoints: 0,
    onlineEndpoints: 0,
    alerts: 0,
    incidents: 0
  });
  const [health, setHealth] = useState({
    status: 'checking',
    database: 'checking'
  });
  const [recentIncidents, setRecentIncidents] = useState([]);
  const [recentTelemetry, setRecentTelemetry] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      // Health check
      try {
        const healthRes = await axios.get(`${API_URL.replace('/api', '')}/health`);
        setHealth({
          status: healthRes.data.status,
          database: healthRes.data.database
        });
      } catch (err) {
        setHealth({ status: 'offline', database: 'unknown' });
      }

      // Fetch Agents
      const agentsRes = await axios.get(`${API_URL}/agents`);
      const agents = agentsRes.data;
      const online = agents.filter(a => a.status === 'ONLINE').length;

      // Fetch Alerts
      const alertsRes = await axios.get(`${API_URL}/alerts?limit=5`);
      const alertsCount = alertsRes.data.length;

      // Fetch Incidents
      const incidentsRes = await axios.get(`${API_URL}/incidents?limit=5`);
      const incidents = incidentsRes.data;

      // Fetch Telemetry Events
      const telemetryRes = await axios.get(`${API_URL}/telemetry?limit=10`);
      const telemetry = telemetryRes.data;

      setStats({
        endpoints: agents.length,
        onlineEndpoints: online,
        alerts: alertsCount,
        incidents: incidents.filter(i => i.status !== 'RESOLVED').length
      });

      setRecentIncidents(incidents);
      setRecentTelemetry(telemetry);
    } catch (error) {
      console.error("Error loading dashboard data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 8000); // refresh every 8s for snappier feedback
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      {/* Title */}
      <div>
        <h2 className="text-xl font-bold text-textPrimary tracking-wide">SOC Overview</h2>
        <p className="text-xs text-textSecondary font-medium">Real-time enterprise endpoint security posture.</p>
      </div>

      {/* Health Indicator Banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={`p-4 rounded-lg border flex items-center justify-between ${
          health.status === 'healthy' 
            ? 'bg-accentGreen/15 border-accentGreen/30 text-accentGreen' 
            : 'bg-accentRed/15 border-accentRed/30 text-accentRed'
        }`}>
          <div className="flex items-center gap-3">
            {health.status === 'healthy' ? <CheckCircle size={20} /> : <XCircle size={20} />}
            <div>
              <p className="text-xs font-bold uppercase tracking-wider">EDR Core Engine Status</p>
              <p className="text-[10px] text-textSecondary font-semibold">
                Backend status: {health.status.toUpperCase()} | Database: {health.database.toUpperCase()}
              </p>
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-widest bg-bgDark px-2.5 py-1 rounded">
            {health.status === 'healthy' ? 'Active' : 'Offline'}
          </span>
        </div>

        <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30 text-accentBlue flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity size={20} className="animate-pulse" />
            <div>
              <p className="text-xs font-bold uppercase tracking-wider">WebSocket Alerts Channel</p>
              <p className="text-[10px] text-textSecondary font-semibold">Subscribed to real-time events feed.</p>
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold tracking-widest bg-bgDark px-2.5 py-1 rounded">
            Connected
          </span>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Endpoints */}
        <div className="bg-bgCard border border-borderDark p-5 rounded-lg flex items-center justify-between shadow-md relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-full translate-x-8 -translate-y-8"></div>
          <div>
            <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block">Total Endpoints</span>
            <span className="text-3xl font-extrabold text-textPrimary mt-2 block">{stats.endpoints}</span>
            <span className="text-[10px] text-accentGreen font-semibold mt-1 block">
              🟢 {stats.onlineEndpoints} online
            </span>
          </div>
          <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-accentBlue">
            <Laptop size={24} />
          </div>
        </div>

        {/* Active Incidents */}
        <div className="bg-bgCard border border-borderDark p-5 rounded-lg flex items-center justify-between shadow-md relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accentRed/5 rounded-full translate-x-8 -translate-y-8"></div>
          <div>
            <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block">Active Incidents</span>
            <span className="text-3xl font-extrabold text-accentRed mt-2 block">{stats.incidents}</span>
            <span className="text-[10px] text-textSecondary font-semibold mt-1 block">Requiring immediate response</span>
          </div>
          <div className="p-3 bg-accentRed/10 border border-accentRed/30 rounded-lg text-accentRed">
            <FileWarning size={24} />
          </div>
        </div>

        {/* Security Alerts */}
        <div className="bg-bgCard border border-borderDark p-5 rounded-lg flex items-center justify-between shadow-md relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accentYellow/5 rounded-full translate-x-8 -translate-y-8"></div>
          <div>
            <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block">Security Alerts</span>
            <span className="text-3xl font-extrabold text-accentYellow mt-2 block">{stats.alerts}</span>
            <span className="text-[10px] text-textSecondary font-semibold mt-1 block">Telemetry-triggered detections</span>
          </div>
          <div className="p-3 bg-accentYellow/10 border border-accentYellow/30 rounded-lg text-accentYellow">
            <AlertTriangle size={24} />
          </div>
        </div>

        {/* Heartbeat Status */}
        <div className="bg-bgCard border border-borderDark p-5 rounded-lg flex items-center justify-between shadow-md relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-accentGreen/5 rounded-full translate-x-8 -translate-y-8"></div>
          <div>
            <span className="text-xs text-textSecondary font-bold uppercase tracking-wider block">Endpoint Health</span>
            <span className="text-3xl font-extrabold text-accentGreen mt-2 block">
              {stats.endpoints > 0 ? Math.round((stats.onlineEndpoints / stats.endpoints) * 100) : 0}%
            </span>
            <span className="text-[10px] text-textSecondary font-semibold mt-1 block">Agent check-in success rate</span>
          </div>
          <div className="p-3 bg-accentGreen/10 border border-accentGreen/30 rounded-lg text-accentGreen">
            <Activity size={24} />
          </div>
        </div>
      </div>

      {/* Main Body Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Side: Recent Incidents & Live Telemetry Activity Stream */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Incidents Card */}
          <div className="bg-bgCard border border-borderDark rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-textPrimary tracking-wide uppercase">Recent Critical Incidents</h3>
              <span className="text-[10px] text-textSecondary flex items-center gap-1 font-semibold">
                <Clock size={12} /> Auto-refreshing
              </span>
            </div>

            {loading ? (
              <div className="py-8 flex justify-center">
                <span className="w-6 h-6 border-2 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
              </div>
            ) : recentIncidents.length === 0 ? (
              <div className="py-12 border border-dashed border-borderDark rounded-lg flex flex-col items-center justify-center text-textSecondary">
                <CheckCircle size={32} className="text-accentGreen/40 mb-2" />
                <p className="text-xs font-semibold">No active incidents detected.</p>
                <p className="text-[10px] text-textSecondary/60 mt-1">Ready for incoming agent telemetry.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-borderDark text-[10px] text-textSecondary font-bold uppercase tracking-wider">
                      <th className="pb-3">Incident ID</th>
                      <th className="pb-3">Title</th>
                      <th className="pb-3">Severity</th>
                      <th className="pb-3">Risk Score</th>
                      <th className="pb-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-borderDark/40 text-xs font-medium">
                    {recentIncidents.map((incident) => (
                      <tr key={incident.id} className="hover:bg-bgInput/40 transition duration-150">
                        <td className="py-3 text-accentBlue font-semibold">INC-{incident.id}</td>
                        <td className="py-3 text-textPrimary max-w-[200px] truncate">{incident.title}</td>
                        <td className="py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
                            incident.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-500' :
                            incident.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-500' :
                            incident.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' :
                            'bg-blue-500/20 text-blue-400'
                          }`}>
                            {incident.severity}
                          </span>
                        </td>
                        <td className="py-3 font-semibold text-textPrimary">{incident.risk_score}/100</td>
                        <td className="py-3">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-textSecondary">
                            {incident.status.replace('_', ' ')}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Live Telemetry Activity Feed */}
          <div className="bg-bgCard border border-borderDark rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-textPrimary tracking-wide uppercase">Real-Time Endpoint Activity Feed</h3>
              <span className="text-[10px] text-textSecondary flex items-center gap-1 font-semibold">
                <Clock size={12} /> Live stream
              </span>
            </div>
            
            {loading ? (
              <div className="py-8 flex justify-center">
                <span className="w-6 h-6 border-2 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
              </div>
            ) : recentTelemetry.length === 0 ? (
              <p className="text-xs text-textSecondary text-center py-6">No endpoint telemetry events logged yet.</p>
            ) : (
              <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
                {recentTelemetry.map((evt) => (
                  <div key={evt.id} className="p-2.5 bg-bgDark/30 border border-borderDark/40 rounded flex justify-between items-center text-xs">
                    <div className="space-y-1">
                      <span className={`text-[9px] font-extrabold uppercase px-2 py-0.5 rounded ${
                        evt.event_type === 'PROCESS' ? 'bg-blue-500/10 text-accentBlue' :
                        evt.event_type === 'NETWORK' ? 'bg-purple-500/10 text-purple-400' :
                        evt.event_type === 'FILE' ? 'bg-yellow-500/10 text-accentYellow' :
                        evt.event_type === 'AUTHENTICATION' ? 'bg-green-500/10 text-accentGreen' :
                        'bg-textSecondary/10 text-textSecondary'
                      }`}>
                        {evt.event_type}
                      </span>
                      <p className="text-textPrimary text-[11px] font-mono leading-tight mt-1">{getEventSummary(evt)}</p>
                    </div>
                    <span className="text-[10px] text-textSecondary font-mono shrink-0 font-semibold">
                      {parseUTC(evt.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
        
        {/* Right Side: Quick Simulator Instructions */}
        <div className="bg-bgCard border border-borderDark rounded-lg p-5 flex flex-col justify-between h-fit space-y-6">
          <div>
            <h3 className="text-sm font-bold text-textPrimary tracking-wide uppercase mb-3">Simulation Lab Mode</h3>
            <p className="text-xs text-textSecondary leading-relaxed">
              SentinelX EDR includes a harmless security-behavior simulator. To generate security telemetry, run the simulator scripts on your computer.
            </p>
            <div className="mt-4 space-y-3 bg-bgDark border border-borderDark p-3 rounded-lg text-[10px] font-mono text-accentBlue">
              <div>
                <p className="text-textSecondary"># Run process simulator</p>
                <p>python simulator/safe_process_test.py</p>
              </div>
              <div>
                <p className="text-textSecondary"># Run file integrity simulator</p>
                <p>python simulator/safe_file_activity_test.py</p>
              </div>
              <div>
                <p className="text-textSecondary"># Run network activity simulator</p>
                <p>python simulator/safe_network_test.py</p>
              </div>
            </div>
          </div>
          <div className="p-3 bg-blue-500/5 border border-blue-500/20 rounded text-[10px] text-textSecondary/80">
            Detections map automatically to <strong>MITRE ATT&CK</strong> techniques and populate the incident response workflow.
          </div>
        </div>

      </div>
    </div>
  );
}
