import React from 'react';
export default function FileAnalysis() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold text-textPrimary tracking-wide">Manual File Analysis</h2>
      <p className="text-xs text-textSecondary font-medium">Extract hashes, file size, type, and static indicators without execution.</p>
      <div className="bg-bgCard border border-borderDark rounded-lg p-8 text-center text-textSecondary text-xs">
        Phase 10 Feature: Static analysis file upload handler.
      </div>
    </div>
  );
}
