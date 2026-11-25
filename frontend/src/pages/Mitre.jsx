import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL } from '../context/AuthContext';
import { Shield, Search, AlertCircle, RefreshCw } from 'lucide-react';

export default function Mitre() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTechnique, setSelectedTechnique] = useState(null);

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API_URL}/alerts`);
      setAlerts(response.data);
    } catch (err) {
      console.error("Failed to load alerts for MITRE map", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  // Standard MITRE ATT&CK tactics & techniques mapping configuration
  const tactics = [
    {
      name: "Execution",
      description: "Tactics to execute adversary-controlled code.",
      techniques: [
        { id: "T1059", name: "Command and Scripting Interpreter", desc: "Executing shell scripts/utilities." },
        { id: "T1059.001", name: "PowerShell Commands", desc: "Obfuscated or encoded PowerShell arguments." }
      ]
    },
    {
      name: "Persistence",
      description: "Tactics to maintain access across restarts.",
      techniques: [
        { id: "T1547.001", name: "Registry Run Keys Startup", desc: "Registry run key startup configuration changes." }
      ]
    },
    {
      name: "Defense Evasion",
      description: "Tactics to avoid signature-based detection.",
      techniques: [
        { id: "T1036", name: "Masquerading / Path Anomaly", desc: "Executing from sandbox/temp locations." }
      ]
    },
    {
      name: "Credential Access",
      description: "Tactics to steal account logons and secrets.",
      techniques: [
        { id: "T1110", name: "Brute Force Logins", desc: "Repeated logon attempts on the endpoint." }
      ]
    },
    {
      name: "Command & Control",
      description: "Tactics to communicate with external hosts.",
      techniques: [
        { id: "T1043", name: "Commonly Used Port Network", desc: "Sockets initiated by system shells." }
      ]
    },
    {
      name: "Impact",
      description: "Tactics to disrupt host operations.",
      techniques: [
        { id: "T1486", name: "Ransomware Encrypt / Mass Writes", desc: "Rapid mass writes and file modification loops." },
        { id: "T1496", name: "File Integrity Modification (FIM)", desc: "Cryptographic hash changes on monitored files." }
      ]
    }
  ];

  // Helper to count alerts mapping to a technique
  const getAlertsForTechnique = (techId) => {
    return alerts.filter(a => a.mitre_technique === techId);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-textPrimary tracking-wide">MITRE ATT&CK Matrix Mapping</h2>
          <p className="text-xs text-textSecondary font-medium">Potential MITRE tactics and techniques mapped directly from active behavioral rules.</p>
        </div>
        <button 
          onClick={fetchAlerts}
          className="bg-bgInput border border-borderDark p-2 rounded-lg text-textSecondary hover:text-textPrimary"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      {loading ? (
        <div className="py-12 flex justify-center">
          <span className="w-8 h-8 border-4 border-accentBlue border-t-transparent rounded-full animate-spin"></span>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {tactics.map((tactic, idx) => (
            <div key={idx} className="bg-bgCard border border-borderDark rounded-lg overflow-hidden flex flex-col h-full shadow-md">
              {/* Tactic Title */}
              <div className="p-3 bg-bgDark/60 border-b border-borderDark">
                <span className="text-[10px] text-accentBlue font-bold uppercase tracking-wider block">Tactic</span>
                <h3 className="text-xs font-bold text-textPrimary uppercase tracking-wide truncate">{tactic.name}</h3>
              </div>

              {/* Techniques list */}
              <div className="p-3 space-y-3 flex-1">
                {tactic.techniques.map(tech => {
                  const techAlerts = getAlertsForTechnique(tech.id);
                  const isTriggered = techAlerts.length > 0;
                  
                  return (
                    <div
                      key={tech.id}
                      onClick={() => isTriggered && setSelectedTechnique({ id: tech.id, name: tech.name, alerts: techAlerts })}
                      className={`p-3 rounded border text-left transition duration-150 flex flex-col justify-between min-h-[100px] ${
                        isTriggered
                          ? 'bg-accentRed/10 border-accentRed/40 hover:bg-accentRed/15 cursor-pointer'
                          : 'bg-bgInput/20 border-borderDark/40 cursor-default opacity-60'
                      }`}
                    >
                      <div>
                        <span className="text-[9px] font-mono font-bold text-textSecondary">{tech.id}</span>
                        <h4 className="text-xs font-bold text-textPrimary leading-snug mt-0.5">{tech.name}</h4>
                      </div>
                      
                      {isTriggered ? (
                        <span className="mt-2 text-[9px] font-bold uppercase text-accentRed flex items-center gap-1">
                          <AlertCircle size={10} />
                          {techAlerts.length} Active Alert{techAlerts.length > 1 ? 's' : ''}
                        </span>
                      ) : (
                        <span className="mt-2 text-[9px] text-textSecondary font-semibold uppercase">0 Detections</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Drill-down Detail Modal/Panel */}
      {selectedTechnique && (
        <div className="bg-bgCard border border-accentRed/30 rounded-lg p-5 mt-6 space-y-4">
          <div className="flex justify-between items-center border-b border-borderDark pb-2">
            <div>
              <span className="text-[10px] font-mono text-accentRed font-bold">DETECTION TRIAGE &bull; {selectedTechnique.id}</span>
              <h3 className="text-sm font-bold text-textPrimary">Evidence for Technique: {selectedTechnique.name}</h3>
            </div>
            <button 
              onClick={() => setSelectedTechnique(null)}
              className="text-textSecondary hover:text-textPrimary text-xs font-bold"
            >
              Close
            </button>
          </div>

          <div className="space-y-4 max-h-[350px] overflow-y-auto">
            {selectedTechnique.alerts.map(alert => (
              <div key={alert.id} className="p-4 bg-bgDark border border-borderDark rounded-lg flex flex-col sm:flex-row justify-between items-start gap-4">
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-textPrimary">{alert.title}</h4>
                  <p className="text-xs text-textSecondary">{alert.description}</p>
                  
                  <div className="bg-bgCard border border-borderDark p-2.5 rounded text-[10px] font-mono text-textSecondary max-w-2xl overflow-x-auto mt-2 leading-tight">
                    {Object.entries(alert.evidence).map(([key, val]) => (
                      <div key={key}>
                        <strong className="text-textPrimary">{key}:</strong> {JSON.stringify(val)}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="text-left sm:text-right space-y-2 shrink-0">
                  <div>
                    <span className="text-[9px] text-textSecondary block uppercase font-bold">Affected Host</span>
                    <Link to={`/endpoints/${alert.agent_id}`} className="text-xs font-mono font-semibold text-accentBlue hover:underline">
                      {alert.agent_id.substring(0, 18)}...
                    </Link>
                  </div>
                  <div>
                    <span className="text-[9px] text-textSecondary block uppercase font-bold">Incident Association</span>
                    {alert.incident_id ? (
                      <Link to={`/incidents/${alert.incident_id}`} className="text-xs text-accentBlue font-bold hover:underline">
                        INC-{alert.incident_id}
                      </Link>
                    ) : (
                      <span className="text-xs text-textSecondary">None</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
