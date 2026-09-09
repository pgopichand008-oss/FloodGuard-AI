import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default function ErrorState({ title = "Data Unavailable", message = "Unable to connect to service.", onRetry }) {
  return (
    <div style={{ background: 'var(--amber-dim)', border: '1px solid rgba(245,158,11,0.3)', borderRadius: 'var(--radius-md)', padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px', color: 'var(--amber-bright)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '0.8rem' }}>
        <AlertTriangle size={16} />
        <span>{title}</span>
      </div>
      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', lineHeight: 1.4 }}>
        {message}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 10px', background: 'var(--bg)', border: '1px solid var(--amber)', borderRadius: 'var(--radius-sm)', color: 'var(--amber-bright)', fontSize: '0.68rem', cursor: 'pointer' }}
        >
          <RefreshCw size={12} /> Retry Connection
        </button>
      )}
    </div>
  );
}
