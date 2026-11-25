import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { API_URL, useAuth } from '../context/AuthContext';
import { Database, Search, ShieldCheck, ShieldAlert, ShieldX, Clock } from 'lucide-react';

export default function IOCs() {
  const { role } = useAuth();
  const [iocs, setIocs] = useState([]);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  
  // Update state
  const [updatingId, setUpdatingId] = useState(null);
  const [newStatus, setNewStatus] = useState('');

  const fetchIocs = async () => {
    try {
      const response = await axios.get(`${API_URL}/iocs`);
      setIocs(response.data);
    } catch (err) {
      console.error("Failed to load IOC list", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIocs();
  }, []);

  const handleUpdateStatus = async (iocId) => {
    try {
      await axios.patch(`${API_URL}/iocs/${iocId}`, {
        status: newStatus
      });
      setUpdatingId(null);
      fetchIocs();
    } catch (err) {
      console.error("Failed to update IOC status", err);
    }
  };

  const filteredIocs = iocs.filter(ioc => {
    const matchesSearch = ioc.value.toLowerCase().includes(search.toLowerCase()) ||
                          (ioc.description && ioc.description.toLowerCase().includes(search.toLowerCase()));
                          
    const matchesType = typeFilter === 'ALL' || ioc.type === typeFilter;
    
    return matchesSearch && matchesType;
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-textPrimary tracking-wide">Threat Indicators of Compromise (IOC)</h2>
        <p className="text-xs text-textSecondary font-medium">Manage and review malicious IPs, domains, files, and executable hashes gathered from endpoints.</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between bg-bgCard border border-borderDark p-4 rounded-lg">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary" size={16} />
          <input
            type="text"
            placeholder="Search by IOC value or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-bgInput border border-borderDark rounded-lg py-2 pl-10 pr-4 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="bg-bgInput border border-borderDark rounded-lg px-3 py-2 text-xs text-textPrimary focus:outline-none focus:border-accentBlue"
          >
            <option value="ALL">All Types</option>
            <option value="IP">IP Address</option>
            <option value="HASH">SHA-256 Hash</option>
            <option value="FILE_PATH">File Path</option>
          </select>
          <button 
            onClick={fetchIocs}
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
      ) : filteredIocs.length === 0 ? (
        <div className="bg-bgCard border border-borderDark rounded-lg p-12 text-center text-textSecondary text-xs">
          No IOCs recorded in database.
        </div>
      ) : (
        <div className="bg-bgCard border border-borderDark rounded-lg overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-borderDark text-[10px] text-textSecondary font-bold uppercase tracking-wider bg-bgDark/30">
                <th className="p-4">Indicator Value</th>
                <th className="p-4">Type</th>
                <th className="p-4">Description</th>
                <th className="p-4">Created Date</th>
                <th className="p-4">Threat Status</th>
                {role !== 'Viewer' && <th className="p-4 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-borderDark/40 text-xs font-medium text-textPrimary">
              {filteredIocs.map(ioc => (
                <tr key={ioc.id} className="hover:bg-bgInput/20 transition duration-150">
                  <td className="p-4 font-mono text-accentBlue max-w-[250px] truncate" title={ioc.value}>
                    {ioc.value}
                  </td>
                  <td className="p-4">
                    <span className="bg-bgInput px-2.5 py-1 rounded text-[10px] uppercase font-bold tracking-wider text-textSecondary">
                      {ioc.type}
                    </span>
                  </td>
                  <td className="p-4 text-textSecondary max-w-[200px] truncate">{ioc.description || 'No description'}</td>
                  <td className="p-4 text-textSecondary flex items-center gap-1.5 pt-6">
                    <Clock size={12} /> {new Date(ioc.added_at).toLocaleString()}
                  </td>
                  <td className="p-4">
                    {updatingId === ioc.id ? (
                      <div className="flex gap-2">
                        <select
                          value={newStatus}
                          onChange={(e) => setNewStatus(e.target.value)}
                          className="bg-bgDark border border-borderDark rounded text-[11px] px-2 py-1 text-textPrimary"
                        >
                          <option value="SUSPICIOUS">Suspicious</option>
                          <option value="CONFIRMED">Confirmed</option>
                          <option value="UNKNOWN">False Alarm</option>
                        </select>
                        <button
                          onClick={() => handleUpdateStatus(ioc.id)}
                          className="bg-accentGreen text-black font-bold text-[10px] px-2 py-1 rounded"
                        >
                          OK
                        </button>
                      </div>
                    ) : (
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        ioc.status === 'CONFIRMED' ? 'bg-red-500/10 text-red-500' :
                        ioc.status === 'SUSPICIOUS' ? 'bg-yellow-500/10 text-yellow-500' :
                        'bg-blue-500/10 text-blue-400'
                      }`}>
                        {ioc.status === 'CONFIRMED' ? <ShieldAlert size={10} /> :
                         ioc.status === 'SUSPICIOUS' ? <ShieldAlert size={10} /> :
                         <ShieldCheck size={10} />}
                        {ioc.status}
                      </span>
                    )}
                  </td>
                  {role !== 'Viewer' && (
                    <td className="p-4 text-right">
                      {updatingId === ioc.id ? (
                        <button
                          onClick={() => setUpdatingId(null)}
                          className="text-[10px] text-textSecondary hover:underline"
                        >
                          Cancel
                        </button>
                      ) : (
                        <button
                          onClick={() => {
                            setUpdatingId(ioc.id);
                            setNewStatus(ioc.status);
                          }}
                          className="bg-bgInput hover:bg-borderDark border border-borderDark text-textPrimary px-2.5 py-1 rounded text-[11px] font-semibold"
                        >
                          Edit Status
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
