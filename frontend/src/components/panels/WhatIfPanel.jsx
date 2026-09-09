import React, { useState } from 'react';
import { X, Sliders, RefreshCw } from 'lucide-react';
import { executeSimulation } from '../../services/api';
import LoadingState from '../common/LoadingState';
import StatusBadge from '../common/StatusBadge';

export default function WhatIfPanel({ onClose }) {
  const [rainfallOverride, setRainfallOverride] = useState(86.4);
  const [blockagePct, setBlockagePct] = useState(35);
  const [clearedNodeN21, setClearedNodeN21] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleRunSimulation = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);

    const payload = {
      baseline_rainfall_mm_hr: 86.4,
      scenario_rainfall_mm_hr: Number(rainfallOverride),
      drainage_blockage_pct: Number(blockagePct),
      cleared_nodes: clearedNodeN21 ? ["N21"] : []
    };

    const res = await executeSimulation(payload);
    setResult(res.data);
    setLoading(false);
  };

  const handleApplyPreset = (rain, block, cleared) => {
    setRainfallOverride(rain);
    setBlockagePct(block);
    setClearedNodeN21(cleared);
  };

  return (
    <div className="workspace-overlay-backdrop" onClick={onClose}>
      <div className="workspace-modal" onClick={(e) => e.stopPropagation()}>
        <div className="workspace-header">
          <div className="title-group">
            <Sliders size={18} />
            <h3 className="workspace-title">WHAT-IF HYDRAULIC FLOOD SIMULATOR</h3>
          </div>
          <button className="workspace-close-btn" onClick={onClose}><X size={18} /></button>
        </div>

        <div className="workspace-body">
          <div className="sim-notice-banner">
            <Sliders size={16} />
            <span>Simulate zone inundation depth deltas and risk transitions under custom rainfall intensity, drain blockage, or pump clearing scenarios.</span>
          </div>

          {/* Preset Buttons */}
          <div className="presets-row">
            <span className="presets-label">SCENARIO PRESETS:</span>
            <button className="preset-btn" onClick={() => handleApplyPreset(86.4, 0, false)}>Normal Drainage (0% Blockage)</button>
            <button className="preset-btn" onClick={() => handleApplyPreset(120.0, 50, false)}>Storm Surge (120mm/hr + 50% Blocked)</button>
            <button className="preset-btn" onClick={() => handleApplyPreset(86.4, 0, true)}>Cleared Node N21 (Intervention)</button>
          </div>

          {/* Simulation Controls Form */}
          <form onSubmit={handleRunSimulation} className="simulation-controls-grid">
            <div className="sim-control-card">
              <div className="control-label-row">
                <span>RAINFALL SCENARIO</span>
                <strong style={{ color: 'var(--cyan-bright)' }}>{rainfallOverride} mm/hr</strong>
              </div>
              <input
                type="range"
                className="sim-slider"
                min="0"
                max="200"
                step="5"
                value={rainfallOverride}
                onChange={(e) => setRainfallOverride(e.target.value)}
              />
              <span className="control-desc">Current live baseline is 86.4 mm/hr</span>
            </div>

            <div className="sim-control-card">
              <div className="control-label-row">
                <span>DRAINAGE BLOCKAGE</span>
                <strong style={{ color: blockagePct > 25 ? 'var(--crimson-bright)' : 'var(--emerald-bright)' }}>{blockagePct}% Blocked</strong>
              </div>
              <input
                type="range"
                className="sim-slider"
                min="0"
                max="100"
                step="5"
                value={blockagePct}
                onChange={(e) => setBlockagePct(e.target.value)}
              />
              <span className="control-desc">Effective conduit cross-section reduction</span>
            </div>

            <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="checkbox-item" style={{ margin: 0 }}>
                <input
                  type="checkbox"
                  checked={clearedNodeN21}
                  onChange={(e) => setClearedNodeN21(e.target.checked)}
                />
                <span>Simulate Emergency Debris Clearing at Sump Node N21</span>
              </label>

              <button className="inspector-btn" type="submit" style={{ width: 'auto', padding: '6px 16px', display: 'flex', alignItems: 'center', gap: 6 }}>
                <RefreshCw size={13} className={loading ? 'spin' : ''} />
                <span>Run Scenario Simulation</span>
              </button>
            </div>
          </form>

          {loading && <LoadingState message="Executing scenario simulation against hydrodynamic model..." />}

          {/* Simulation Results Output */}
          {result && !loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div className="sim-output-card">
                <div className="output-metric">
                  <span className="lbl">Baseline Rainfall</span>
                  <span className="val">{result.baseline_rainfall_mm_hr} mm/hr</span>
                </div>
                <span className="output-divider">➔</span>
                <div className="output-metric">
                  <span className="lbl">Simulated Scenario</span>
                  <span className="val" style={{ color: 'var(--cyan-bright)' }}>{result.scenario_rainfall_mm_hr} mm/hr</span>
                </div>
                <span className="output-divider">|</span>
                <div className="output-metric">
                  <span className="lbl">Worsened Zones</span>
                  <span className="val" style={{ color: 'var(--crimson-bright)' }}>{result.overall_summary?.zones_worsened || 0}</span>
                </div>
                <div className="output-metric">
                  <span className="lbl">Improved Zones</span>
                  <span className="val" style={{ color: 'var(--emerald-bright)' }}>{result.overall_summary?.zones_improved || 0}</span>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {result.zone_simulations.map((z) => (
                  <div key={z.zone_id} className="priority-card" style={{ padding: '8px 12px' }}>
                    <div className="priority-card-main">
                      <div className="priority-top-row">
                        <span className="priority-target">Zone {z.zone_id}: {z.zone_name}</span>
                        <StatusBadge status={z.simulated_risk} />
                      </div>
                      <div className="priority-issue">
                        Baseline: <strong>{z.baseline_depth_cm} cm</strong> ➔ Simulated: <strong>{z.simulated_depth_cm} cm</strong> (Delta: <strong style={{ color: z.depth_delta_cm > 0 ? 'var(--crimson-bright)' : 'var(--emerald-bright)' }}>{z.depth_delta_cm > 0 ? `+${z.depth_delta_cm}` : z.depth_delta_cm} cm</strong>)
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
