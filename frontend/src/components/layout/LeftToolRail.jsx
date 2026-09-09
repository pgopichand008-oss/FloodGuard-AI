import React, { useState } from 'react';
import {
  Layers,
  CloudRain,
  Network,
  HelpCircle,
  Route,
  Sliders,
  Bell,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

export default function LeftToolRail({ activeWorkspace, setActiveWorkspace }) {
  const [collapsed, setCollapsed] = useState(false);

  const tools = [
    { id: 'layers', label: 'GIS Layers', icon: Layers, group: 'VIEWPORT' },
    { id: 'forecast', label: 'Rain Nowcast', icon: CloudRain, group: 'HYDROLOGY' },
    { id: 'drainage', label: 'Drainage Net', icon: Network, group: 'HYDROLOGY' },
    { id: 'analysis', label: 'WHY-FLOOD', icon: HelpCircle, group: 'INTELLIGENCE' },
    { id: 'routing', label: 'Safe Routing', icon: Route, group: 'INTELLIGENCE' },
    { id: 'whatif', label: 'WHAT-IF Sim', icon: Sliders, group: 'INTELLIGENCE' },
    { id: 'alerts', label: 'Alert Feed', icon: Bell, group: 'OPERATIONS', badge: 2 }
  ];

  const handleToolClick = (toolId) => {
    if (activeWorkspace === toolId) {
      setActiveWorkspace(null); // toggle off
    } else {
      setActiveWorkspace(toolId);
    }
  };

  return (
    <aside className={`tool-rail ${collapsed ? 'collapsed' : 'expanded'}`}>
      <div className="rail-header">
        <button
          className="rail-toggle-btn"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? "Expand Tools" : "Collapse Tools"}
        >
          {collapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
          {!collapsed && <span className="rail-header-title">TOOLS</span>}
        </button>
      </div>

      <div className="rail-scroll-container">
        <div className="rail-group">
          <div className="rail-group-items">
            {tools.map((tool) => {
              const Icon = tool.icon;
              const isActive = activeWorkspace === tool.id;
              return (
                <button
                  key={tool.id}
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
    </aside>
  );
}
