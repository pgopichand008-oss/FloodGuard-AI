import React, { useState } from 'react';
import {
  Map,
  CloudRain,
  Network,
  HelpCircle,
  Route,
  Sliders,
  AlertTriangle,
  Radio,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

export default function LeftToolRail({ activeWorkspace, setActiveWorkspace }) {
  const [collapsed, setCollapsed] = useState(false);

  const tools = [
    { id: null, label: 'Map', icon: Map },
    { id: 'forecast', label: 'Forecast', icon: CloudRain },
    { id: 'drainage', label: 'Drainage', icon: Network },
    { id: 'analysis', label: 'Analysis', icon: HelpCircle },
    { id: 'routing', label: 'Routing', icon: Route },
    { id: 'whatif', label: 'What-If', icon: Sliders },
    { id: 'alerts', label: 'Priority', icon: AlertTriangle },
    { id: 'propagation', label: 'Propagation', icon: Radio },
    { id: 'feed', label: 'Alerts', icon: Bell, badge: 3 }
  ];

  const handleToolClick = (toolId) => {
    setActiveWorkspace(toolId);
  };

  return (
    <aside className={`tool-rail ${collapsed ? 'collapsed' : 'expanded'}`}>
      <div className="rail-header">
        <button
          className="rail-toggle-btn"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? "Expand Tool Rail" : "Collapse Tool Rail"}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          {!collapsed && <span className="rail-header-title">NAVIGATION</span>}
        </button>
      </div>

      <div className="rail-scroll-container">
        <div className="rail-group">
          <div className="rail-group-items">
            {tools.map((tool) => {
              const Icon = tool.icon;
              const isActive = activeWorkspace === tool.id || (tool.id === null && !activeWorkspace);
              return (
                <button
                  key={tool.label}
                  className={`rail-btn ${isActive ? 'active' : ''}`}
                  onClick={() => handleToolClick(tool.id)}
                >
                  <div className="rail-btn-icon">
                    <Icon size={16} />
                  </div>
                  {!collapsed && <span className="rail-label">{tool.label}</span>}
                  {tool.badge && <span className="rail-badge">{tool.badge}</span>}
                  {collapsed && <div className="rail-tooltip">{tool.label}</div>}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="rail-footer" style={{ padding: '8px', borderTop: '1px solid var(--border)' }}>
        <button
          className="rail-btn"
          onClick={() => setActiveWorkspace(null)}
          title="Settings"
        >
          <div className="rail-btn-icon">
            <Settings size={16} />
          </div>
          {!collapsed && <span className="rail-label">Settings</span>}
          {collapsed && <div className="rail-tooltip">Settings</div>}
        </button>
      </div>
    </aside>
  );
}
