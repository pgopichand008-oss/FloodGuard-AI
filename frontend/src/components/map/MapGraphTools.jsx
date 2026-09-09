import React, { useState } from 'react';
import { X, LineChart, BarChart2, Activity, Download, Layers } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, LineChart as ReLineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function MapGraphTools({ zones = [], onClose }) {
  const [activeTab, setActiveTab] = useState('depth'); // 'depth', 'risk', 'capacity'
  const [selectedZoneId, setSelectedZoneId] = useState('ALL');

  // Sample 24h/180m forecast curve data
  const depthCurveData = [
    { time: 'NOW', Z01: 15.0, Z03: 20.0, Z05: 5.0, Z08: 12.0, avg: 13.0 },
    { time: '+30m', Z01: 28.0, Z03: 34.0, Z05: 8.0, Z08: 22.0, avg: 23.0 },
    { time: '+60m', Z01: 38.0, Z03: 45.0, Z05: 10.5, Z08: 31.0, avg: 31.1 },
    { time: '+90m', Z01: 40.4, Z03: 47.5, Z05: 11.1, Z08: 34.2, avg: 33.3 },
    { time: '+120m', Z01: 35.0, Z03: 42.0, Z05: 9.0, Z08: 28.0, avg: 28.5 },
    { time: '+150m', Z01: 26.0, Z03: 31.0, Z05: 6.5, Z08: 20.0, avg: 20.9 },
    { time: '+180m', Z01: 18.0, Z03: 22.0, Z05: 4.0, Z08: 14.0, avg: 14.5 }
  ];

  // Risk breakdown data
  const riskDistributionData = [
    { category: 'Critical Risk (>45cm)', count: zones.filter(z => z.risk === 'CRITICAL').length || 2, color: '#ef4444' },
    { category: 'High Risk (30-45cm)', count: zones.filter(z => z.risk === 'HIGH').length || 3, color: '#f97316' },
    { category: 'Moderate Risk (15-30cm)', count: zones.filter(z => z.risk === 'MODERATE').length || 2, color: '#eab308' },
    { category: 'Low Risk (<15cm)', count: zones.filter(z => z.risk === 'LOW').length || 1, color: '#22c55e' }
  ];

  // Capacity vs Runoff data
  const capacityData = [
    { time: '00:00', runoff_m3s: 12.5, capacity_m3s: 25.0, surcharge_risk: 'LOW' },
    { time: '00:30', runoff_m3s: 28.4, capacity_m3s: 25.0, surcharge_risk: 'MODERATE' },
    { time: '01:00', runoff_m3s: 42.1, capacity_m3s: 25.0, surcharge_risk: 'HIGH' },
    { time: '01:30', runoff_m3s: 55.8, capacity_m3s: 25.0, surcharge_risk: 'CRITICAL' },
    { time: '02:00', runoff_m3s: 48.0, capacity_m3s: 25.0, surcharge_risk: 'HIGH' },
    { time: '02:30', runoff_m3s: 32.2, capacity_m3s: 25.0, surcharge_risk: 'MODERATE' },
    { time: '03:00', runoff_m3s: 18.6, capacity_m3s: 25.0, surcharge_risk: 'LOW' }
  ];

  const handleExportCSV = () => {
    let csvContent = 'data:text/csv;charset=utf-8,';
    if (activeTab === 'depth') {
      csvContent += 'Time,Z01_Commercial_cm,Z03_Station_cm,Z05_Hospital_cm,Avg_Catchment_cm\n';
      depthCurveData.forEach(row => {
        csvContent += `${row.time},${row.Z01},${row.Z03},${row.Z05},${row.avg}\n`;
      });
    } else if (activeTab === 'risk') {
      csvContent += 'Risk_Category,Zone_Count\n';
      riskDistributionData.forEach(row => {
        csvContent += `"${row.category}",${row.count}\n`;
      });
    } else {
      csvContent += 'Time,Surface_Runoff_m3s,Pipe_Capacity_m3s\n';
      capacityData.forEach(row => {
        csvContent += `${row.time},${row.runoff_m3s},${row.capacity_m3s}\n`;
      });
    }

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `floodguard_${activeTab}_analytics.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{
      position: 'absolute',
      top: '56px',
      right: '16px',
      width: '420px',
      maxHeight: 'calc(100% - 90px)',
      background: 'rgba(10, 15, 26, 0.92)',
      backdropFilter: 'blur(12px)',
      border: '1px solid var(--border)',
      borderRadius: '8px',
      zIndex: 25,
      display: 'flex',
      flexDirection: 'column',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(15, 23, 42, 0.6)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <LineChart size={15} style={{ color: 'var(--cyan-bright)' }} />
          <span style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--text-bright)', letterSpacing: '0.03em' }}>
            GIS GRAPH & ANALYTICS TOOLKIT
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={handleExportCSV}
            title="Export Graph Data (CSV)"
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              color: 'var(--cyan-bright)',
              cursor: 'pointer',
              padding: '3px 6px',
              fontSize: '0.66rem',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}
          >
            <Download size={12} />
            <span>CSV</span>
          </button>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '2px'
            }}
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border)',
        background: 'rgba(6, 10, 18, 0.4)',
        padding: '4px'
      }}>
        <button
          onClick={() => setActiveTab('depth')}
          style={{
            flex: 1,
            padding: '6px',
            fontSize: '0.68rem',
            fontWeight: 700,
            border: 'none',
            borderRadius: '4px',
            background: activeTab === 'depth' ? 'rgba(6, 182, 212, 0.2)' : 'transparent',
            color: activeTab === 'depth' ? 'var(--cyan-bright)' : 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px'
          }}
        >
          <Activity size={12} />
          <span>Depth Curve</span>
        </button>

        <button
          onClick={() => setActiveTab('risk')}
          style={{
            flex: 1,
            padding: '6px',
            fontSize: '0.68rem',
            fontWeight: 700,
            border: 'none',
            borderRadius: '4px',
            background: activeTab === 'risk' ? 'rgba(168, 85, 247, 0.2)' : 'transparent',
            color: activeTab === 'risk' ? '#c084fc' : 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px'
          }}
        >
          <BarChart2 size={12} />
          <span>Risk Distribution</span>
        </button>

        <button
          onClick={() => setActiveTab('capacity')}
          style={{
            flex: 1,
            padding: '6px',
            fontSize: '0.68rem',
            fontWeight: 700,
            border: 'none',
            borderRadius: '4px',
            background: activeTab === 'capacity' ? 'rgba(234, 179, 8, 0.2)' : 'transparent',
            color: activeTab === 'capacity' ? '#fde047' : 'var(--text-muted)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px'
          }}
        >
          <Layers size={12} />
          <span>Runoff vs Capacity</span>
        </button>
      </div>

      {/* Chart Canvas Area */}
      <div style={{ padding: '12px', flex: 1, overflowY: 'auto' }}>
        {activeTab === 'depth' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>0–180 MINUTE INUNDATION DEPTH (CM)</span>
              <select
                value={selectedZoneId}
                onChange={(e) => setSelectedZoneId(e.target.value)}
                style={{
                  background: 'var(--card-bg)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-bright)',
                  fontSize: '0.65rem',
                  borderRadius: '4px',
                  padding: '2px 6px'
                }}
              >
                <option value="ALL">All Zones (Overlay)</option>
                <option value="Z01">Z01 - Commercial</option>
                <option value="Z03">Z03 - Station Sump</option>
                <option value="Z05">Z05 - General Hospital</option>
              </select>
            </div>

            <div style={{ width: '100%', height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={depthCurveData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="time" stroke="var(--text-subtle)" fontSize={10} />
                  <YAxis stroke="var(--text-subtle)" fontSize={10} unit="cm" />
                  <Tooltip
                    contentStyle={{ background: '#0b1329', borderColor: 'var(--border)', borderRadius: '6px', fontSize: '0.72rem' }}
                    itemStyle={{ color: 'var(--cyan-bright)' }}
                  />
                  {(selectedZoneId === 'ALL' || selectedZoneId === 'Z03') && (
                    <Area type="monotone" dataKey="Z03" name="Z03 Station Corridor" stroke="#ef4444" fill="rgba(239, 68, 68, 0.2)" strokeWidth={2} />
                  )}
                  {(selectedZoneId === 'ALL' || selectedZoneId === 'Z01') && (
                    <Area type="monotone" dataKey="Z01" name="Z01 Commercial" stroke="#f97316" fill="rgba(249, 115, 22, 0.2)" strokeWidth={2} />
                  )}
                  {(selectedZoneId === 'ALL' || selectedZoneId === 'Z05') && (
                    <Area type="monotone" dataKey="Z05" name="Z05 Hospital Hub" stroke="#22c55e" fill="rgba(34, 197, 94, 0.2)" strokeWidth={2} />
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'risk' && (
          <div>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CATCHMENT ZONE RISK BREAKDOWN</span>
            </div>

            <div style={{ width: '100%', height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={riskDistributionData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="category" stroke="var(--text-subtle)" fontSize={8} interval={0} tick={{ fontSize: 9 }} />
                  <YAxis stroke="var(--text-subtle)" fontSize={10} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ background: '#0b1329', borderColor: 'var(--border)', borderRadius: '6px', fontSize: '0.72rem' }}
                  />
                  <Bar dataKey="count" name="Zone Count" fill="#a855f7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {activeTab === 'capacity' && (
          <div>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>RUNOFF INFLOW VS STORM DRAIN CAPACITY (M³/S)</span>
            </div>

            <div style={{ width: '100%', height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <ReLineChart data={capacityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                  <XAxis dataKey="time" stroke="var(--text-subtle)" fontSize={10} />
                  <YAxis stroke="var(--text-subtle)" fontSize={10} unit=" m³/s" />
                  <Tooltip
                    contentStyle={{ background: '#0b1329', borderColor: 'var(--border)', borderRadius: '6px', fontSize: '0.72rem' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '0.65rem', paddingTop: '4px' }} />
                  <Line type="monotone" dataKey="runoff_m3s" name="Surface Runoff Inflow" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="dash" dataKey="capacity_m3s" name="Max Pipe Capacity" stroke="#22c55e" strokeWidth={2} strokeDasharray="4 4" dot={false} />
                </ReLineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Footer Metrics */}
      <div style={{
        padding: '8px 12px',
        borderTop: '1px solid var(--border)',
        background: 'rgba(6, 10, 18, 0.8)',
        display: 'flex',
        justifyContent: 'space-between',
        fontSize: '0.66rem',
        color: 'var(--text-muted)'
      }}>
        <span>MAX PEAK DEPTH: <strong style={{ color: '#ef4444' }}>47.5 cm (Z03)</strong></span>
        <span>SURCHARGE STATUS: <strong style={{ color: '#f97316' }}>OVER CAPACITY (+123%)</strong></span>
      </div>
    </div>
  );
}
