import React from 'react';
import { Loader2 } from 'lucide-react';

export default function LoadingState({ message = "Processing GIS calculations..." }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px', gap: '8px', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
      <Loader2 className="spin" size={24} style={{ color: 'var(--cyan-bright)' }} />
      <span>{message}</span>
    </div>
  );
}
