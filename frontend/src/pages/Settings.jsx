import React from 'react';
export default function Settings() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-textPrimary tracking-wide">Platform Settings</h2>
      <p className="text-xs text-textSecondary font-medium">Configure rules, alert parameters, AI integrations, and EDR keys.</p>
      <div className="bg-bgCard border border-borderDark rounded-lg p-8 text-center text-textSecondary text-xs">
        Phase 9 & 10 Feature: Rules tuning and LLM API config panel.
      </div>
    </div>
  );
}
