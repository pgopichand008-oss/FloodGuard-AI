import React from 'react';

export default function StatusBadge({ status, size = 'md', className = '' }) {
  const normalized = (status || 'DEFAULT').toString().toUpperCase();

  let chipClass = 'chip-default';
  if (normalized === 'CRITICAL' || normalized === 'SEVERE') chipClass = 'chip-critical';
  else if (normalized === 'HIGH') chipClass = 'chip-high';
  else if (normalized === 'WARNING' || normalized === 'MODERATE') chipClass = 'chip-warning';
  else if (normalized === 'NOMINAL' || normalized === 'LOW' || normalized === 'NORMAL' || normalized === 'OK') chipClass = 'chip-nominal';
  else if (normalized === 'DEMO' || normalized === 'SIMULATED') chipClass = 'chip-demo';
  else if (normalized === 'LIVE') chipClass = 'chip-nominal';

  return (
    <span className={`status-chip ${chipClass} ${size} ${className}`}>
      <span className="chip-beacon"></span>
      <span>{normalized}</span>
    </span>
  );
}
