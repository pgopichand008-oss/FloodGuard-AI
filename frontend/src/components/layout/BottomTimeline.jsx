import React from 'react';
import { Clock } from 'lucide-react';

export default function BottomTimeline({ selectedTimeIndex, setSelectedTimeIndex }) {
  const steps = [
    { minutes: 0, label: "NOW", depth: "18 cm", peak: false },
    { minutes: 30, label: "+30m", depth: "27 cm", peak: false },
    { minutes: 60, label: "+60m", depth: "36 cm", peak: false },
    { minutes: 90, label: "+90m", depth: "47 cm", peak: true },
    { minutes: 120, label: "+120m", depth: "43 cm", peak: false },
    { minutes: 150, label: "+150m", depth: "32 cm", peak: false },
    { minutes: 180, label: "+180m", depth: "21 cm", peak: false }
  ];

  const currentStep = steps[selectedTimeIndex] || steps[0];

  return (
    <div className="bottom-timeline-strip">
      <div className="timeline-info-chip">
        <Clock size={13} style={{ color: 'var(--cyan-bright)' }} />
        <span>FORECAST HORIZON: <strong>{currentStep.label}</strong></span>
        <span className="chip-sep">|</span>
        <span>Predicted Max Depth: <strong>{currentStep.depth}</strong></span>
        {currentStep.peak && <span className="peak-badge">PEAK SURGE</span>}
      </div>

      <div className="timeline-control-track">
        <div className="track-bar"></div>
        <div className="step-chips-row">
          {steps.map((step, idx) => {
            const isSelected = idx === selectedTimeIndex;
            return (
              <div
                key={step.minutes}
                className={`time-chip ${isSelected ? 'selected' : ''} ${step.peak ? 'peak' : ''}`}
                onClick={() => setSelectedTimeIndex(idx)}
              >
                <span className="chip-time">{step.label}</span>
                <span className="chip-dot"></span>
                <span className="chip-depth">{step.depth}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
