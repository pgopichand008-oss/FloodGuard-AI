import React, { useState, useEffect } from 'react';
import { X, CloudRain } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { fetchForecastData } from '../../services/api';
import LoadingState from '../common/LoadingState';

export default function ForecastPanel({ onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadForecast() {
      setLoading(true);
      const res = await fetchForecastData(180);
      setData(res.data);
      setLoading(false);
    }
    loadForecast();
  }, []);

  const chartData = data?.time_series || [
    { minutes: 0, time: "NOW", rainfall_mm_hr: 86.4, depth_cm: 18.0 },
    { minutes: 30, time: "+30m", rainfall_mm_hr: 94.0, depth_cm: 27.5 },
    { minutes: 60, time: "+60m", rainfall_mm_hr: 101.2, depth_cm: 36.0 },
    { minutes: 90, time: "+90m", rainfall_mm_hr: 105.0, depth_cm: 47.5 },
    { minutes: 120, time: "+120m", rainfall_mm_hr: 82.0, depth_cm: 43.0 },
    { minutes: 150, time: "+150m", rainfall_mm_hr: 54.0, depth_cm: 32.0 },
    { minutes: 180, time: "+180m", rainfall_mm_hr: 28.0, depth_cm: 21.0 }
  ];

  return (
    <div className="workspace-overlay-backdrop" onClick={onClose}>
      <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-header">
          <div className="title-group">
            <CloudRain size={18} />
            <h3 className="workspace-title">0–3 HOUR RAINFALL & INUNDATION NOWCAST</h3>
          </div>
          <button className="workspace-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="workspace-body">
          {loading ? (
            <LoadingState message="Generating 0-3 hour nowcast forecast..." />
          ) : (
            <>
              <div className="forecast-summary-bar">
                <div className="summary-item">
                  <span className="lbl">Peak Forecast Rate</span>
                  <span className="val" style={{ color: 'var(--cyan-bright)' }}>{data?.peak_forecast_intensity_mm_hr || 105.0} mm/hr</span>
                </div>
                <div className="summary-item">
                  <span className="lbl">Peak Arrival Time</span>
                  <span className="val" style={{ color: 'var(--amber-bright)' }}>+{data?.peak_arrival_minutes || 90} mins</span>
                </div>
                <div className="summary-item">
                  <span className="lbl">Peak Surge Depth</span>
                  <span className="val" style={{ color: 'var(--crimson-bright)' }}>47.5 cm</span>
                </div>
              </div>

              <div className="recharts-container-box">
                <div className="chart-header-row">
                  <span>PRECIPITATION (mm/hr) vs INUNDATION DEPTH (cm)</span>
                  <span>180-MINUTE HORIZON</span>
                </div>
                <div style={{ width: '100%', height: 260 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                      <defs>
                        <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0}/>
                        </linearGradient>
                        <linearGradient id="depthGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                          <stop offset="95%" stopColor="#ef4444" stopOpacity={0.0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="time" stroke="var(--text-subtle)" fontSize={11} />
                      <YAxis stroke="var(--text-subtle)" fontSize={11} />
                      <Tooltip contentStyle={{ background: '#0d1420', border: '1px solid #2b3a5c', borderRadius: 6, fontSize: 12, color: '#fff' }} />
                      <Area type="monotone" dataKey="rainfall_mm_hr" name="Rainfall (mm/hr)" stroke="#38bdf8" fillOpacity={1} fill="url(#rainGrad)" />
                      <Area type="monotone" dataKey="depth_cm" name="Depth (cm)" stroke="#ef4444" fillOpacity={1} fill="url(#depthGrad)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
