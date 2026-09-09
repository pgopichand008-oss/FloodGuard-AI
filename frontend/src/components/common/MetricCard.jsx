import React from 'react';

export default function MetricCard({ label, value, unit, subtext, icon: Icon, color = 'cyan', onClick }) {
  return (
    <div className={`metric-box ${onClick ? 'interactive' : ''}`} onClick={onClick}>
      <div className="box-lbl">
        {Icon && <Icon size={12} style={{ display: 'inline', marginRight: 4, color: `var(--${color}-bright, var(--cyan-bright))` }} />}
        {label}
      </div>
      <div className="box-val">
        {value} {unit && <span style={{ fontSize: '0.65rem', fontWeight: 400, color: 'var(--text-subtle)' }}>{unit}</span>}
      </div>
      {subtext && <div className="box-sub">{subtext}</div>}
    </div>
  );
}
