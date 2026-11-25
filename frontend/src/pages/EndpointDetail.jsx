import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL, useAuth, parseUTC } from '../context/AuthContext';
import { 
  Laptop, ShieldAlert, Cpu, Network, FileText, Lock, 
  RefreshCw, Terminal, CheckCircle2, AlertTriangle, Play
} from 'lucide-react';

export default function EndpointDetail() {
  const { id } = useParams();
  const { role } = useAuth();
  const [agent, setAgent] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ALERTS'); // ALERTS, TELEMETRY, CONTAINMENT
  
  // Containment inputs
  const [killPid, setKillPid] = useState('');
  const [killProcName, setKillProcName] = useState('');
  const [quarantinePath, setQuarantinePath] = useState('');
  const [actionMessage, setActionMessage] = useState('');
  const [actionError, setActionError] = useState('');
  const [submittingAction, setSubmittingAction] = useState(false);

  const fetchAgentDetails = async () => {
    try {
      const agentRes = await axios.get(`${API_URL}/agents/${id}`);
      setAgent(agentRes.data);

      const alertsRes = await axios.get(`${API_URL}/alerts?agent_id=${id}`);
      setAlerts(alertsRes.data);

      const telemetryRes = await axios.get(`${API_URL}/telemetry?agent_id=${id}&limit=50`);
      setEvents(telemetryRes.data);
    } catch (err) {
      console.error("Failed to load agent details", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgentDetails();
    const interval = setInterval(fetchAgentDetails, 8000);
    return () => clearInterval(interval);
  }, [id]);

  const handleResponseAction = async (actionType, details) => {
    setActionMessage('');
    setActionError('');
    setSubmittingAction(true);
    try {
      const response = await axios.post(`${API_URL}/response`, {
        agent_id: id,
        action_type: actionType,
        details: details
      });
      setActionMessage(`Response Action requested successfully! Status: ${response.data.status}`);
      // Clear inputs
      setKillPid('');
      setKillProcName('');
      setQuarantinePath('');
      fetchAgentDetails();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Failed to trigger response action");
    } finally {
      setSubmittingAction(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="bg-bgCard border border-borderDark p-8 rounded-lg text-center text-textSecondary text-xs">
        Agent details not found. Verify the agent is registered.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Back button & Title */}
      <div className="flex justify-between items-center">
        <div className="space-y-1">
          <Link to="/endpoints" className="text-xs text-accentBlue hover:underline font-bold">&larr; Back to Endpoints</Link>
          <h2 className="text-xl font-bold text-textPrimary tracking-wide flex items-center gap-2">
            Endpoint: {agent.hostname}
            <span className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase tracking-wider ${
              agent.status === 'ONLINE' ? 'bg-accentGreen/20 text-accentGreen' : 'bg-accentRed/20 text-accentRed'
            }`}>
              {agent.status}
            </span>
          </h2>
        </div>
        <button 
          onClick={fetchAgentDetails}
          className="bg-bgInput border border-borderDark p-2 rounded-lg text-textSecondary hover:text-textPrimary"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      {/* Grid containing Agent Details Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Host Details */}
        <div className="bg-bgCard border border-borderDark rounded-lg p-5 space-y-4">
          <h3 className="text-sm font-bold text-textPrimary uppercase tracking-wider border-b border-borderDark pb-2">Host Metadata</h3>
          
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-textSecondary font-semibold block uppercase text-[10px]">Agent UUID</span>
              <span className="font-mono text-textPrimary break-all">{agent.id}</span>
            </div>
            <div>
              <span className="text-textSecondary font-semibold block uppercase text-[10px]">OS Version</span>
              <span className="text-textPrimary">{agent.os}</span>
            </div>
            <div>
              <span className="text-textSecondary font-semibold block uppercase text-[10px]">Primary IP</span>
              <span className="font-mono text-textPrimary">{agent.ip_address || "127.0.0.1"}</span>
            </div>
            <div>
              <span className="text-textSecondary font-semibold block uppercase text-[10px]">Active User</span>
              <span className="text-textPrimary font-semibold">{agent.username || "unknown"}</span>
            </div>
            <div>
              <span className="text-textSecondary font-semibold block uppercase text-[10px]">Overall Risk score</span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                agent.risk_score >= 76 ? 'bg-red-500/20 text-red-500' :
                agent.risk_score >= 51 ? 'bg-orange-500/20 text-orange-500' :
                agent.risk_score >= 26 ? 'bg-yellow-500/20 text-yellow-500' :
                'bg-blue-500/20 text-blue-400'
              }`}>
                {agent.risk_score}/100 Risk Score
              </span>
            </div>
            <div>
              <span className="text-textSecondary font-semibold block uppercase text-[10px]">Last Heartbeat</span>
              <span className="text-textPrimary">{parseUTC(agent.last_seen).toLocaleString()}</span>
            </div>
            <div>
              <span className="text-textSecondary font-semibold block uppercase text-[10px]">Agent Version</span>
              <span className="font-mono text-textPrimary">v{agent.agent_version}</span>
            </div>
          </div>
        </div>

        {/* Tab content panel */}
        <div className="lg:col-span-2 bg-bgCard border border-borderDark rounded-lg overflow-hidden flex flex-col">
          {/* Tab buttons */}
          <div className="flex border-b border-borderDark bg-bgDark/40">
            <button
              onClick={() => setActiveTab('ALERTS')}
              className={`px-5 py-3 text-xs font-bold uppercase tracking-wider ${
                activeTab === 'ALERTS' 
                  ? 'border-b-2 border-accentBlue text-textPrimary bg-bgCard' 
                  : 'text-textSecondary hover:text-textPrimary'
              }`}
            >
              Detections ({alerts.length})
            </button>
            <button
              onClick={() => setActiveTab('TELEMETRY')}
              className={`px-5 py-3 text-xs font-bold uppercase tracking-wider ${
                activeTab === 'TELEMETRY' 
                  ? 'border-b-2 border-accentBlue text-textPrimary bg-bgCard' 
                  : 'text-textSecondary hover:text-textPrimary'
              }`}
            >
              Raw Telemetry ({events.length})
            </button>
            <button
              onClick={() => setActiveTab('CONTAINMENT')}
              className={`px-5 py-3 text-xs font-bold uppercase tracking-wider ${
                activeTab === 'CONTAINMENT' 
                  ? 'border-b-2 border-accentBlue text-textPrimary bg-bgCard' 
                  : 'text-textSecondary hover:text-textPrimary'
              }`}
            >
              Containment Controls
            </button>
          </div>

          <div className="p-6 flex-1 overflow-y-auto max-h-[450px]">
            {/* ALERTS TAB */}
            {activeTab === 'ALERTS' && (
              alerts.length === 0 ? (
                <div className="py-12 text-center text-textSecondary text-xs">
                  No alerts triggered for this agent.
                </div>
              ) : (
                <div className="space-y-4">
                  {alerts.map(alert => (
                    <div key={alert.id} className="p-4 bg-bgDark border border-borderDark rounded-lg flex items-start gap-4 justify-between">
                      <div className="space-y-1">
                        <span className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase ${
                          alert.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-500' :
                          alert.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-500' :
                          alert.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' :
                          'bg-blue-500/20 text-blue-400'
                        }`}>
                          {alert.severity} (Score: {alert.risk_score})
                        </span>
                        <h4 className="text-xs font-bold text-textPrimary">{alert.title}</h4>
                        <p className="text-[11px] text-textSecondary">{alert.description}</p>
                        {alert.mitre_technique && (
                          <span className="inline-block text-[9px] font-mono font-bold text-accentBlue uppercase mt-1">
                            MITRE: {alert.mitre_technique}
                          </span>
                        )}
                      </div>
                      {alert.incident_id && (
                        <Link 
                          to={`/incidents/${alert.incident_id}`}
                          className="bg-bgInput border border-borderDark text-[10px] text-accentBlue px-2.5 py-1 rounded font-bold hover:underline"
                        >
                          INC-{alert.incident_id}
                        </Link>
                      )}
                    </div>
                  ))}
                </div>
              )
            )}

            {/* TELEMETRY TAB */}
            {activeTab === 'TELEMETRY' && (
              events.length === 0 ? (
                <div className="py-12 text-center text-textSecondary text-xs">
                  No telemetry logged. Make sure agent is running and sending data.
                </div>
              ) : (
                <div className="space-y-3">
                  {events.map(evt => (
                    <div key={evt.id} className="p-3 bg-bgDark/50 border border-borderDark/40 rounded text-xs space-y-1 font-mono">
                      <div className="flex justify-between text-[10px] text-textSecondary">
                        <span>{evt.event_type} | Severity: {evt.severity}</span>
                        <span>{parseUTC(evt.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="text-textPrimary overflow-x-auto">
                        <pre className="text-[10px] leading-tight">{JSON.stringify(evt.metadata_json, null, 2)}</pre>
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}

            {/* CONTAINMENT TAB */}
            {activeTab === 'CONTAINMENT' && (
              <div className="space-y-6">
                {actionMessage && (
                  <div className="p-3 bg-accentGreen/15 border border-accentGreen/30 text-accentGreen rounded text-xs">
                    {actionMessage}
                  </div>
                )}
                {actionError && (
                  <div className="p-3 bg-accentRed/15 border border-accentRed/30 text-accentRed rounded text-xs">
                    {actionError}
                  </div>
                )}

                {role === 'Viewer' ? (
                  <p className="text-xs text-accentRed">Containment actions are locked in Viewer (read-only) mode.</p>
                ) : (
                  <div className="space-y-6 divide-y divide-borderDark/50">
                    {/* Terminate Process */}
                    <div className="space-y-4 pt-1">
                      <h4 className="text-xs font-bold text-accentRed flex items-center gap-2">
                        <Cpu size={14} /> Terminate Suspect Process
                      </h4>
                      <p className="text-[11px] text-textSecondary">Request immediate process termination on the endpoint by specifying the Process ID (PID).</p>
                      
                      <div className="flex flex-col sm:flex-row gap-3">
                        <input
                          type="number"
                          placeholder="Process PID (e.g. 5678)"
                          value={killPid}
                          onChange={(e) => setKillPid(e.target.value)}
                          className="bg-bgInput border border-borderDark rounded-lg px-3 py-2 text-xs text-textPrimary focus:outline-none"
                        />
                        <input
                          type="text"
                          placeholder="Process Name (e.g. mal.exe)"
                          value={killProcName}
                          onChange={(e) => setKillProcName(e.target.value)}
                          className="bg-bgInput border border-borderDark rounded-lg px-3 py-2 text-xs text-textPrimary focus:outline-none"
                        />
                        <button
                          onClick={() => handleResponseAction('TERMINATE_PROCESS', { pid: parseInt(killPid), process_name: killProcName })}
                          disabled={submittingAction || !killPid}
                          className="bg-accentRed hover:bg-red-600 text-white px-4 py-2 rounded-lg text-xs font-bold cursor-pointer"
                        >
                          Execute Kill
                        </button>
                      </div>
                    </div>

                    {/* Quarantine File */}
                    <div className="space-y-4 pt-5">
                      <h4 className="text-xs font-bold text-accentYellow flex items-center gap-2">
                        <FileText size={14} /> Quarantine Suspicious File
                      </h4>
                      <p className="text-[11px] text-textSecondary">Move files from monitored test directory to a secure containment folder.</p>
                      
                      <div className="flex flex-col sm:flex-row gap-3">
                        <input
                          type="text"
                          placeholder="Monitored File Path..."
                          value={quarantinePath}
                          onChange={(e) => setQuarantinePath(e.target.value)}
                          className="bg-bgInput border border-borderDark rounded-lg px-3 py-2 text-xs text-textPrimary focus:outline-none flex-1"
                        />
                        <button
                          onClick={() => handleResponseAction('QUARANTINE_FILE', { file_path: quarantinePath })}
                          disabled={submittingAction || !quarantinePath}
                          className="bg-accentYellow hover:bg-yellow-600 text-black px-4 py-2 rounded-lg text-xs font-bold cursor-pointer"
                        >
                          Quarantine File
                        </button>
                      </div>
                    </div>

                    {/* Isolate Endpoint Simulation */}
                    <div className="space-y-4 pt-5">
                      <h4 className="text-xs font-bold text-accentBlue flex items-center gap-2">
                        <Lock size={14} /> Simulate Network Isolation
                      </h4>
                      <p className="text-[11px] text-textSecondary">Simulate blocking all outbound endpoint network connections to isolate the agent in the local lab env.</p>
                      
                      <button
                        onClick={() => handleResponseAction('ISOLATE_AGENT', {})}
                        disabled={submittingAction}
                        className="bg-accentBlue hover:bg-blue-600 text-white px-4 py-2.5 rounded-lg text-xs font-bold cursor-pointer flex items-center gap-2"
                      >
                        <Play size={14} /> Initiate Host Isolation
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
