import React, { useState, useEffect } from 'react';
import { Waves, RefreshCw, Bell, User, CloudRain, HelpCircle, Network, Sliders, ListOrdered, Route } from 'lucide-react';

export default function TopBar({ floodState, onRefresh, onOpenSitRep, onNavClick, activeWorkspace }) {
  const isLive = floodState?.isLive;
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formattedDate = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  const formattedTime = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true });

  const navLinks = [
    { id: 'forecast', label: 'Predict', icon: CloudRain, color: 'cyan' },
    { id: 'analysis', label: 'Explain', icon: HelpCircle, color: 'purple' },
    { id: 'drainage', label: 'Diagnose', icon: Network, color: 'emerald' },
    { id: 'whatif', label: 'Simulate', icon: Sliders, color: 'amber' },
    { id: 'alerts', label: 'Prioritize', icon: ListOrdered, color: 'rose' },
    { id: 'routing', label: 'Reroute', icon: Route, color: 'blue' }
  ];

  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <div className="brand-icon">
          <Waves size={18} />
        </div>
        <div className="brand-text-group">
          <span className="brand-name">HydroPulse AI</span>
        </div>

        {/* Framed Header Navigation Links */}
        <nav className="top-bar-nav">
          {navLinks.map(link => {
            const isActive = activeWorkspace === link.id;
            const Icon = link.icon;
            return (
              <button
                key={link.id}
                className={`top-nav-link nav-${link.color} ${isActive ? 'active' : ''}`}
                onClick={() => onNavClick && onNavClick(link.id)}
              >
                {Icon && <Icon size={12} className="top-nav-icon" />}
                <span>{link.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="top-bar-right">
        {/* ONE Primary User-Facing Timestamp */}
        <div className="top-clock">
          <span className="clock-local">{formattedDate} | {formattedTime}</span>
        </div>

        <button className="top-icon-btn" onClick={onRefresh} title="Refresh Telemetry Data">
          <RefreshCw size={14} className={floodState?.loading ? 'spin' : ''} />
        </button>

        <button className="top-icon-btn" style={{ position: 'relative' }} title="Notifications">
          <Bell size={14} />
          <span style={{ position: 'absolute', top: '-2px', right: '-2px', background: 'var(--crimson)', color: '#fff', fontSize: '0.55rem', fontStyle: 'normal', fontWeight: 900, borderRadius: '50%', width: '12px', height: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>3</span>
        </button>

        <button className="top-icon-btn" title="User Account Profile">
          <User size={14} />
        </button>

        <button className="sitrep-btn" onClick={onOpenSitRep}>
          <span>Demo Mode</span>
        </button>
      </div>
    </header>
  );
}
