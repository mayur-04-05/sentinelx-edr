import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL, useAuth, parseUTC } from '../context/AuthContext';
import { 
  FileWarning, Clock, ShieldAlert, CheckCircle2, 
  User, RefreshCw, Send, BrainCircuit, Activity, Cpu
} from 'lucide-react';

// Recursive Process Tree Node Component
function ProcessNode({ node, selectedPid, onSelect }) {
  if (!node) return null;
  const isSelected = selectedPid === node.pid;

  return (
    <div className="pl-4 border-l border-borderDark/60 relative mt-2 select-none">
      {/* Connector lines visual */}
      <div className="absolute top-4 left-0 w-3 border-t border-borderDark/60"></div>
      
      <div 
        onClick={() => onSelect(node)}
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded border text-xs font-semibold cursor-pointer transition duration-150 ${
          isSelected 
            ? 'bg-blue-500/15 border-accentBlue text-textPrimary' 
            : 'bg-bgInput/40 border-borderDark hover:bg-bgInput/70 text-textSecondary hover:text-textPrimary'
        }`}
      >
        <Cpu size={12} className={isSelected ? 'text-accentBlue' : 'text-textSecondary'} />
        <span>{node.name}</span>
        <span className="text-[10px] text-textSecondary font-mono font-normal">PID: {node.pid}</span>
      </div>

      {node.children && node.children.length > 0 && (
        <div className="mt-1 space-y-1">
          {node.children.map(child => (
            <ProcessNode 
              key={child.pid} 
              node={child} 
              selectedPid={selectedPid} 
              onSelect={onSelect} 
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function IncidentDetail() {
  const { id } = useParams();
  const { role, user } = useAuth();
  const [incident, setIncident] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [processTree, setProcessTree] = useState(null);
  const [selectedProcess, setSelectedProcess] = useState(null);
  
  // AI assist state
  const [aiReport, setAiReport] = useState(null);
  const [loadingAi, setLoadingAi] = useState(false);

  // Edit fields
  const [status, setStatus] = useState('');
  const [notes, setNotes] = useState('');
  const [updating, setUpdating] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchIncidentDetails = async () => {
    try {
      const incRes = await axios.get(`${API_URL}/incidents/${id}`);
      setIncident(incRes.data);
      setStatus(incRes.data.status);
      setNotes(incRes.data.analyst_notes || '');

      const timelineRes = await axios.get(`${API_URL}/incidents/${id}/timeline`);
      setTimeline(timelineRes.data);

      const treeRes = await axios.get(`${API_URL}/incidents/${id}/process-tree`);
      setProcessTree(treeRes.data);
      if (treeRes.data && !selectedProcess) {
        setSelectedProcess(treeRes.data);
      }
    } catch (err) {
      console.error("Failed to load incident detailed info", err);
    } finally {
      setLoading(false);
    }
  };

  const updateIncident = async (e) => {
    e.preventDefault();
    setUpdating(true);
    try {
      await axios.patch(`${API_URL}/incidents/${id}`, {
        status: status,
        analyst_notes: notes
      });
      fetchIncidentDetails();
    } catch (err) {
      console.error("Failed to update incident details", err);
    } finally {
      setUpdating(false);
    }
  };

  const getAiInvestigation = async () => {
    setLoadingAi(true);
    setAiReport(null);
    try {
      // In Phase 9 we will fetch from AI API, for now stub details
      const response = await axios.get(`${API_URL}/ai/investigate/${id}`);
      setAiReport(response.data);
    } catch (err) {
      // Offline fallback
      setAiReport({
        summary: "AI analysis unavailable — configure an AI provider.",
        suspicious_reasons: ["Provider key missing in environment variables."],
        recommendations: ["Check process arguments manually.", "Quarantine execution folder."]
      });
    } finally {
      setLoadingAi(false);
    }
  };

  useEffect(() => {
    fetchIncidentDetails();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
      </div>
    );
  }

  if (!incident) {
    return (
      <div className="bg-bgCard border border-borderDark p-8 rounded-lg text-center text-textSecondary text-xs">
        Incident not found.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex justify-between items-center">
        <div className="space-y-1">
          <Link to="/incidents" className="text-xs text-accentBlue hover:underline font-bold">&larr; Back to Incidents</Link>
          <h2 className="text-xl font-bold text-textPrimary tracking-wide flex items-center gap-2">
            Incident: INC-{incident.id}
            <span className={`text-[10px] px-2.5 py-0.5 rounded font-bold uppercase ${
              incident.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-500' :
              incident.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-500' :
              incident.severity === 'MEDIUM' ? 'bg-yellow-500/20 text-yellow-500' :
              'bg-blue-500/20 text-blue-400'
            }`}>
              {incident.severity} (Score: {incident.risk_score})
            </span>
          </h2>
        </div>
        <button 
          onClick={fetchIncidentDetails}
          className="bg-bgInput border border-borderDark p-2 rounded-lg text-textSecondary hover:text-textPrimary"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left column: Incident details, notes, updates */}
        <div className="space-y-6">
          
          {/* Metadata Card */}
          <div className="bg-bgCard border border-borderDark rounded-lg p-5 space-y-4">
            <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider border-b border-borderDark pb-2">Incident Meta</h3>
            
            <div className="space-y-3 text-xs leading-relaxed">
              <div>
                <strong className="text-textSecondary block uppercase text-[10px]">Affected Host</strong>
                <Link to={`/endpoints/${incident.agent_id}`} className="text-accentBlue hover:underline font-mono font-bold break-all">
                  {incident.agent_id}
                </Link>
              </div>
              <div>
                <strong className="text-textSecondary block uppercase text-[10px]">Detection Scope</strong>
                <p className="text-textPrimary font-semibold">{incident.title}</p>
              </div>
              <div className="flex justify-between">
                <div>
                  <strong className="text-textSecondary block uppercase text-[10px]">First Observed</strong>
                  <span className="text-textSecondary">{parseUTC(incident.first_seen).toLocaleString()}</span>
                </div>
                <div>
                  <strong className="text-textSecondary block uppercase text-[10px]">Last Check</strong>
                  <span className="text-textSecondary">{parseUTC(incident.last_seen).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Lifecycle & Status Update form */}
          <div className="bg-bgCard border border-borderDark rounded-lg p-5">
            <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider border-b border-borderDark pb-2 mb-4">Analyst Actions</h3>
            
            <form onSubmit={updateIncident} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-textSecondary uppercase mb-1.5">Lifecycle Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  disabled={role === 'Viewer'}
                  className="w-full bg-bgInput border border-borderDark rounded-lg py-2 px-3 text-xs text-textPrimary focus:outline-none"
                >
                  <option value="NEW">New Alert</option>
                  <option value="INVESTIGATING">Under Investigation</option>
                  <option value="CONTAINED">Threat Contained</option>
                  <option value="RESOLVED">Resolved / Closed</option>
                  <option value="FALSE_POSITIVE">False Positive</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-textSecondary uppercase mb-1.5">Analyst Notes</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  disabled={role === 'Viewer'}
                  rows={4}
                  className="w-full bg-bgInput border border-borderDark rounded-lg p-3 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
                  placeholder="Record investigation steps, findings, and remediation history..."
                />
              </div>

              {role !== 'Viewer' && (
                <button
                  type="submit"
                  disabled={updating}
                  className="w-full bg-accentBlue hover:bg-blue-600 text-white py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 cursor-pointer transition"
                >
                  <Send size={12} />
                  {updating ? 'Saving...' : 'Update Incident'}
                </button>
              )}
            </form>
          </div>

          {/* AI Co-Pilot investigation suggestions */}
          <div className="bg-bgCard border border-borderDark rounded-lg p-5 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider flex items-center gap-1.5">
                <BrainCircuit size={16} className="text-accentBlue" />
                AI Incident Assistant
              </h3>
              <button
                onClick={getAiInvestigation}
                disabled={loadingAi}
                className="bg-accentBlue/10 hover:bg-accentBlue/20 text-accentBlue border border-blue-500/20 text-[10px] px-2.5 py-1 rounded font-bold cursor-pointer transition"
              >
                Analyze
              </button>
            </div>

            {loadingAi ? (
              <div className="py-8 flex flex-col items-center justify-center gap-2">
                <span className="w-5 h-5 border-2 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
                <span className="text-[10px] text-textSecondary">Consulting LLM models...</span>
              </div>
            ) : aiReport ? (
              <div className="space-y-3 text-xs leading-relaxed bg-bgDark/40 border border-borderDark/40 p-4 rounded-lg">
                <div>
                  <h4 className="font-bold text-textPrimary uppercase text-[9px] mb-1">Threat Assessment:</h4>
                  <p className="text-textSecondary">{aiReport.summary}</p>
                </div>

                {aiReport.suspicious_reasons && (
                  <div>
                    <h4 className="font-bold text-accentRed uppercase text-[9px] mb-1">Risk Factors:</h4>
                    <ul className="list-disc pl-4 space-y-1 text-textSecondary text-[11px]">
                      {aiReport.suspicious_reasons.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}

                {aiReport.recommendations && (
                  <div>
                    <h4 className="font-bold text-accentGreen uppercase text-[9px] mb-1">Containment Steps:</h4>
                    <ul className="list-decimal pl-4 space-y-1 text-textSecondary text-[11px]">
                      {aiReport.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
                <span className="block text-[8px] text-textSecondary/40 mt-3 font-semibold uppercase">
                  AI-generated analysis — verify with telemetry.
                </span>
              </div>
            ) : (
              <div className="py-4 text-center text-textSecondary text-[11px]">
                Click "Analyze" to generate AI containment instructions.
              </div>
            )}
          </div>
        </div>

        {/* Right column: Timeline & Process Tree */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Reconstructed Process Tree Card */}
          <div className="bg-bgCard border border-borderDark rounded-lg p-5">
            <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider border-b border-borderDark pb-2 mb-4">Process Execution Graph</h3>
            
            {processTree ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-borderDark/40 bg-bgDark/20 p-4 rounded-lg min-h-[250px] overflow-auto">
                  <ProcessNode 
                    node={processTree} 
                    selectedPid={selectedProcess?.pid} 
                    onSelect={setSelectedProcess} 
                  />
                </div>
                
                {/* Node Details panel */}
                <div className="bg-bgInput/20 border border-borderDark p-4 rounded-lg flex flex-col justify-between">
                  {selectedProcess ? (
                    <div className="space-y-4 text-xs">
                      <div>
                        <h4 className="font-bold text-accentBlue text-sm">{selectedProcess.name}</h4>
                        <span className="text-[10px] text-textSecondary font-mono font-semibold">PID: {selectedProcess.pid} | Parent PID: {selectedProcess.ppid}</span>
                      </div>
                      
                      <div className="space-y-2">
                        <div>
                          <strong className="text-textSecondary text-[10px] block uppercase">Command Line</strong>
                          <pre className="bg-bgDark/80 p-2 rounded text-[10px] text-textPrimary font-mono break-all whitespace-pre-wrap">
                            {selectedProcess.cmdline.join(' ') || selectedProcess.name}
                          </pre>
                        </div>
                        <div>
                          <strong className="text-textSecondary text-[10px] block uppercase">Executable Exec Path</strong>
                          <span className="font-mono text-[10px] break-all">{selectedProcess.exe || "unknown"}</span>
                        </div>
                        <div>
                          <strong className="text-textSecondary text-[10px] block uppercase">SHA-256 Hash</strong>
                          <span className="font-mono text-[10px] break-all text-accentYellow">{selectedProcess.sha256 || "Locked / Non-accessible"}</span>
                        </div>
                        <div>
                          <strong className="text-textSecondary text-[10px] block uppercase">Process Owner</strong>
                          <span>{selectedProcess.username}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-textSecondary text-xs text-center my-auto">Select a process node to inspect arguments.</p>
                  )}
                  {selectedProcess && role !== 'Viewer' && (
                    <button
                      onClick={() => handleResponseAction('TERMINATE_PROCESS', { pid: selectedProcess.pid, process_name: selectedProcess.name })}
                      className="w-full bg-accentRed hover:bg-red-600 text-white font-bold text-xs py-2 rounded-lg mt-4 cursor-pointer"
                    >
                      Kill Process PID {selectedProcess.pid}
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-textSecondary text-xs">Process tree builder loading...</div>
            )}
          </div>

          {/* Chronological Timeline Card */}
          <div className="bg-bgCard border border-borderDark rounded-lg p-5">
            <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wider border-b border-borderDark pb-2 mb-6">Forensic Timeline</h3>
            
            {timeline.length === 0 ? (
              <div className="py-8 text-center text-textSecondary text-xs">No timeline events captured.</div>
            ) : (
              <div className="relative border-l border-borderDark/80 ml-4 space-y-6">
                {timeline.map((item, idx) => (
                  <div key={idx} className="relative pl-6">
                    {/* Circle icon */}
                    <span className={`absolute -left-2.5 top-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center text-[10px] ${
                      item.type === 'ALERT' ? 'bg-bgCard border-accentRed text-accentRed' :
                      item.type === 'PERSISTENCE' ? 'bg-bgCard border-accentYellow text-accentYellow' :
                      item.type.startsWith('PROCESS') ? 'bg-bgCard border-accentBlue text-accentBlue' :
                      'bg-bgCard border-textSecondary text-textSecondary'
                    }`}>
                      {item.type === 'ALERT' ? '!' : idx + 1}
                    </span>
                    
                    <div className="space-y-1">
                      <div className="flex justify-between items-center text-[10px] text-textSecondary font-mono">
                        <span className="font-bold uppercase tracking-wider">{item.type}</span>
                        <span>{parseUTC(item.timestamp).toLocaleString()}</span>
                      </div>
                      <h4 className="text-xs font-bold text-textPrimary">{item.title}</h4>
                      <p className="text-xs text-textSecondary">{item.description}</p>
                      
                      {item.details && Object.keys(item.details).length > 0 && (
                        <pre className="bg-bgDark/30 p-2 rounded text-[9px] font-mono text-textSecondary break-all whitespace-pre-wrap leading-tight mt-1">
                          {JSON.stringify(item.details)}
                        </pre>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
